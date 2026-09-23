"""Serviço de execução: do pedido ao envio, com o histórico em cada passo.

Depende só das portas do domínio. `processar` roda em segundo plano, então
nunca deixa uma exceção escapar: toda falha vira status gravado.
"""

import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from app.domain.erros import ErroDeDominio, ExecucaoDuplicada
from app.domain.execucao import (
    Decisao,
    Execucao,
    ParametrosConsulta,
    StatusExecucao,
    chave_idempotencia,
    decidir,
)
from app.domain.mensagem import compor_mensagem
from app.domain.portas import DadosColetados, FonteDeDados, RepositorioExecucoes, WhatsAppSender
from app.domain.relatorio import Relatorio, montar_relatorio

logger = logging.getLogger(__name__)
S = StatusExecucao


@dataclass(frozen=True, slots=True)
class Solicitacao:
    execucao: Execucao
    decisao: Decisao

    @property
    def processar(self) -> bool:
        """Se o chamador deve agendar o processamento."""
        return self.decisao is not Decisao.REUSAR


class ServicoExecucao:
    def __init__(
        self,
        repositorio: RepositorioExecucoes,
        fonte: FonteDeDados,
        sender: WhatsAppSender,
        relogio: Callable[[], datetime],
    ) -> None:
        self._repo = repositorio
        self._fonte = fonte
        self._sender = sender
        self._agora = relogio

    def solicitar(self, parametros: ParametrosConsulta) -> Solicitacao:
        """Cria, reaproveita ou reabre a execução — ADR-004."""
        chave = chave_idempotencia(parametros)
        existente = self._repo.buscar_por_chave(chave)
        decisao = decidir(existente.status if existente else None)

        if existente is None:
            try:
                return Solicitacao(self._repo.criar(parametros, chave, self._agora()), decisao)
            except ExecucaoDuplicada as corrida:
                # Outro pedido idêntico criou a linha entre a busca e a criação.
                # A unique constraint resolveu; aqui só se reaproveita.
                vencedora = self._repo.obter(corrida.execucao_id)
                assert vencedora is not None
                return Solicitacao(vencedora, Decisao.REUSAR)

        if decisao is Decisao.RETENTAR:
            return Solicitacao(self._repo.retentar(existente.id, self._agora()), decisao)
        return Solicitacao(existente, decisao)

    def obter(self, execucao_id: int) -> Execucao | None:
        return self._repo.obter(execucao_id)

    def listar(self, limite: int) -> list[Execucao]:
        return self._repo.listar(limite)

    def processar(self, execucao_id: int) -> Execucao:
        execucao = self._repo.obter(execucao_id)
        if execucao is None:
            raise LookupError(f"execução {execucao_id} não existe")
        log = logging.LoggerAdapter(logger, {"execucao_id": execucao_id})
        p = execucao.parametros

        self._avancar(execucao_id, S.COLETANDO)
        log.info("coletando data-base %s", p.data_base)
        try:
            dados = self._fonte.obter(p.data_base)
        except Exception as erro:  # noqa: BLE001 — segundo plano: nada pode escapar
            return self._falhar(execucao_id, S.FALHA_COLETA, erro, log)

        self._avancar(execucao_id, S.PROCESSANDO)
        try:
            relatorio = montar_relatorio(
                dados.consolidado,
                dados.uf,
                p.segmento,
                p.ufs,
                p.cnpj_administradora,
                p.top_concorrentes,
            )
            encontrados = _resumo(dados, relatorio)
            if not relatorio.tem_resultado:
                log.info("sem resultado para os parâmetros; nada a enviar")
                return self._avancar(execucao_id, S.SEM_RESULTADO, dados_encontrados=encontrados)
            mensagem = compor_mensagem(relatorio)
        except Exception as erro:  # noqa: BLE001
            return self._falhar(execucao_id, S.FALHA_PROCESSAMENTO, erro, log)

        self._avancar(
            execucao_id,
            S.MENSAGEM_GERADA,
            dados_encontrados=encontrados,
            mensagem_gerada=mensagem,
        )
        self._avancar(execucao_id, S.ENVIANDO)
        try:
            resultado = self._sender.enviar(p.destinatario, mensagem)
        except Exception as erro:  # noqa: BLE001
            return self._falhar(execucao_id, S.FALHA_ENVIO, erro, log)

        log.info("enviado: %s", resultado.id_mensagem)
        return self._avancar(
            execucao_id,
            S.ENVIADO,
            enviado_em=self._agora(),
            provider_message_id=resultado.id_mensagem,
        )

    def _avancar(self, execucao_id: int, status: StatusExecucao, **campos: Any) -> Execucao:
        return self._repo.atualizar(execucao_id, status, self._agora(), **campos)

    def _falhar(
        self,
        execucao_id: int,
        status: StatusExecucao,
        erro: Exception,
        log: logging.LoggerAdapter,
    ) -> Execucao:
        esperado = isinstance(erro, ErroDeDominio)
        if esperado:
            log.warning("%s: %s", status, erro)
        else:
            log.exception("%s por erro inesperado", status)
        return self._avancar(
            execucao_id,
            status,
            erro_tipo=type(erro).__name__,
            # Erro inesperado pode carregar detalhe interno: vai para o log, não para a API.
            erro_descricao=str(erro) if esperado else "erro inesperado; ver o log da execução",
        )


def _resumo(dados: DadosColetados, relatorio: Relatorio) -> dict[str, Any]:
    return {
        "data_base_consolidado": dados.data_base_consolidado,
        "data_base_uf": dados.data_base_uf,
        "relatorio": asdict(relatorio),
    }
