"""Portas do domínio: o que ele precisa do mundo externo, sem saber quem fornece.

As implementações ficam em infra/ (ver ADR-001 e ADR-009). Os testes do
serviço usam implementações falsas destas mesmas interfaces.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

from app.domain.execucao import Execucao, ParametrosConsulta, StatusExecucao
from app.domain.modelos import RegistroConsolidado, RegistroUF
from app.domain.opcoes import Opcoes


class RepositorioExecucoes(Protocol):
    def criar(
        self,
        parametros: ParametrosConsulta,
        chave: str,
        agora: datetime,
        origem: Execucao | None = None,
    ) -> Execucao:
        """Com `origem`, herda dados e mensagem dela.

        Levanta ExecucaoDuplicada se já houver execução da chave em andamento.
        """
        ...

    def obter(self, execucao_id: int) -> Execucao | None: ...

    def buscar_por_chave(self, chave: str) -> Execucao | None:
        """A mais recente com essa chave."""
        ...

    def listar(self, limite: int) -> list[Execucao]: ...

    def listar_em_andamento(self) -> list[Execucao]:
        """Da mais antiga para a mais recente."""
        ...

    def atualizar(
        self, execucao_id: int, status: StatusExecucao, agora: datetime, **campos: Any
    ) -> Execucao:
        """Levanta TransicaoInvalida se a máquina de estados não permitir."""
        ...

    def retentar(self, execucao_id: int, agora: datetime) -> Execucao: ...


@dataclass(frozen=True, slots=True)
class ResultadoEnvio:
    id_mensagem: str


class WhatsAppSender(Protocol):
    """Entrega de mensagens. Implementações: WahaSender e FakeSender (ADR-009)."""

    def enviar(self, destinatario: str, mensagem: str) -> ResultadoEnvio:
        """Levanta EnvioError quando a entrega falha."""
        ...


class SituacaoConexao(StrEnum):
    CONECTADO = "CONECTADO"
    AGUARDANDO_QR = "AGUARDANDO_QR"
    INICIANDO = "INICIANDO"
    DESCONECTADO = "DESCONECTADO"
    INDISPONIVEL = "INDISPONIVEL"  # o provedor não respondeu


@dataclass(frozen=True, slots=True)
class EstadoConexao:
    situacao: SituacaoConexao
    conta: str | None = None
    qr_code: str | None = None  # data URI da imagem, só em AGUARDANDO_QR
    mensagem: str | None = None


class ConexaoWhatsApp(Protocol):
    """O número que envia está conectado? Quem mostra o QR code é o painel (ADR-009)."""

    def estado(self) -> EstadoConexao:
        """Levanta EnvioError quando o provedor não responde."""
        ...

    def reconectar(self) -> None:
        """Pede um QR code novo. Levanta EnvioError."""
        ...


@dataclass(frozen=True, slots=True)
class DadosColetados:
    """Os dois datasets de uma consulta. `uf` é None quando não há trimestre publicado."""

    data_base_consolidado: str
    consolidado: tuple[RegistroConsolidado, ...]
    data_base_uf: str | None
    uf: tuple[RegistroUF, ...] | None


class FonteDeDados(Protocol):
    def obter(self, data_base: str) -> DadosColetados:
        """Levanta ColetaError ou ParsingError."""
        ...


class FonteDeOpcoes(Protocol):
    def opcoes(self) -> Opcoes:
        """Data-bases publicadas e administradoras da mais recente. Levanta ColetaError."""
        ...
