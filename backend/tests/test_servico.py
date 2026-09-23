"""Serviço de execução — orquestra coleta, análise, mensagem, envio e histórico.

Fonte e envio falsos; repositório real em SQLite em memória, porque o que se
quer verificar aqui é justamente o encadeamento dos estados gravados.
"""

from datetime import UTC, datetime

import pytest

from app.domain.execucao import Decisao, ParametrosConsulta, StatusExecucao
from app.domain.servico import ServicoExecucao
from app.infra.db import RepositorioSQL, criar_engine, criar_tabelas
from app.infra.whatsapp import FakeSender
from tests.fakes import FonteFalsa

S = StatusExecucao
AGORA = datetime(2026, 9, 22, 15, 12, tzinfo=UTC)
HONDA = "45441789"


def params(**kw) -> ParametrosConsulta:
    base = dict(
        data_base="202607",
        segmento=4,
        ufs=("PI", "MA"),
        cnpj_administradora=HONDA,
        top_concorrentes=3,
        destinatario="5586999990000",
    )
    return ParametrosConsulta(**{**base, **kw})


@pytest.fixture
def repo():
    engine = criar_engine("sqlite:///:memory:")
    criar_tabelas(engine)
    return RepositorioSQL(engine)


@pytest.fixture
def fonte(registros_consolidado, registros_uf):
    return FonteFalsa(registros_consolidado, registros_uf)


@pytest.fixture
def sender():
    return FakeSender()


@pytest.fixture
def servico(repo, fonte, sender):
    return ServicoExecucao(repo, fonte, sender, relogio=lambda: AGORA)


def executar(servico, **kw):
    solicitacao = servico.solicitar(params(**kw))
    return servico.processar(solicitacao.execucao.id)


class TestCaminhoFeliz:
    def test_termina_enviado(self, servico):
        assert executar(servico).status is S.ENVIADO

    def test_envia_a_mensagem_gerada_ao_destinatario(self, servico, sender):
        execucao = executar(servico)
        [(destino, texto)] = sender.enviadas
        assert destino == "5586999990000"
        assert texto == execucao.mensagem_gerada
        assert "- *PI*:" in texto and "- *MA*:" in texto

    def test_registra_id_do_provedor_e_horario(self, servico):
        execucao = executar(servico)
        assert execucao.provider_message_id == "fake-1"
        assert execucao.enviado_em == AGORA

    def test_guarda_os_numeros_separados_do_texto(self, servico):
        """ADR-004: auditar qual número originou cada mensagem."""
        dados = executar(servico).dados_encontrados
        assert dados["data_base_consolidado"] == "202607"
        assert dados["data_base_uf"] == "202606"
        pi = next(p for p in dados["relatorio"]["posicoes_uf"] if p["uf"] == "PI")
        assert pi["alvo"]["ativos"] == 148_962


class TestIdempotencia:
    def test_primeira_solicitacao_cria_e_manda_processar(self, servico):
        solicitacao = servico.solicitar(params())
        assert solicitacao.decisao is Decisao.CRIAR
        assert solicitacao.processar

    def test_mesmo_pedido_depois_do_envio_reenvia_sem_coletar(self, servico, sender, fonte):
        """ADR-010: cada clique envia; os dados da consulta anterior são reaproveitados."""
        primeira = executar(servico)
        de_novo = servico.solicitar(params(ufs=("MA", "PI")))  # ordem diferente, mesma consulta
        assert de_novo.decisao is Decisao.REENVIAR
        assert de_novo.processar
        assert de_novo.execucao.id != primeira.id

        reenviada = servico.processar(de_novo.execucao.id)

        assert reenviada.status is S.ENVIADO
        assert reenviada.origem_id == primeira.id
        assert reenviada.mensagem_gerada == primeira.mensagem_gerada
        assert reenviada.dados_encontrados == primeira.dados_encontrados
        assert [texto for _, texto in sender.enviadas] == [primeira.mensagem_gerada] * 2
        assert fonte.chamadas == 1, "o reenvio não abre o site do BCB"

    def test_reenvio_registra_o_proprio_envio(self, servico):
        executar(servico)
        reenviada = executar(servico)
        assert reenviada.provider_message_id == "fake-2"
        assert reenviada.enviado_em == AGORA

    def test_dois_cliques_seguidos_nao_disparam_duas_coletas(self, servico):
        primeira = servico.solicitar(params())
        segunda = servico.solicitar(params())
        assert segunda.execucao.id == primeira.execucao.id
        assert not segunda.processar

    def test_outro_destinatario_e_outra_execucao(self, servico, sender):
        executar(servico)
        executar(servico, destinatario="5586888880000")
        assert len(sender.enviadas) == 2


class TestFalhas:
    def test_falha_de_coleta(self, servico, fonte, sender):
        fonte.falhar_com = "site do BCB indisponível"
        execucao = executar(servico)
        assert execucao.status is S.FALHA_COLETA
        assert execucao.erro_tipo == "ColetaError"
        assert execucao.erro_descricao == "site do BCB indisponível"
        assert sender.enviadas == []

    def test_retentar_falha_de_envio_nao_coleta_de_novo(self, repo, fonte):
        sender = FakeSender(falhar_com="WAHA fora do ar")
        servico = ServicoExecucao(repo, fonte, sender, relogio=lambda: AGORA)
        falhou = executar(servico)
        assert falhou.status is S.FALHA_ENVIO

        sender._falhar_com = None
        retentada = executar(servico)

        assert retentada.id == falhou.id
        assert retentada.status is S.ENVIADO
        assert retentada.tentativas == 2
        assert fonte.chamadas == 1

    def test_falha_de_envio_guarda_a_mensagem(self, repo, fonte):
        servico = ServicoExecucao(
            repo, fonte, FakeSender(falhar_com="fora da janela"), relogio=lambda: AGORA
        )
        execucao = executar(servico)
        assert execucao.status is S.FALHA_ENVIO
        assert execucao.mensagem_gerada  # gerada, só não entregue
        assert execucao.erro_descricao == "fora da janela"

    def test_erro_inesperado_nao_escapa(self, servico, fonte):
        """processar roda em segundo plano: ninguém capturaria a exceção."""

        def explodir(_):
            raise RuntimeError("bug")

        fonte.obter = explodir
        execucao = executar(servico)
        assert execucao.status is S.FALHA_COLETA
        assert execucao.erro_tipo == "RuntimeError"

    def test_falha_pode_ser_retentada(self, servico, fonte, sender):
        fonte.falhar_com = "fora do ar"
        executar(servico)

        fonte.falhar_com = None
        solicitacao = servico.solicitar(params())
        assert solicitacao.decisao is Decisao.RETENTAR
        assert solicitacao.processar

        execucao = servico.processar(solicitacao.execucao.id)
        assert execucao.status is S.ENVIADO
        assert execucao.tentativas == 2
        assert execucao.erro_tipo is None


class TestSemResultado:
    def test_administradora_ausente_nao_envia(self, servico, sender):
        execucao = executar(servico, cnpj_administradora="99999999")
        assert execucao.status is S.SEM_RESULTADO
        assert execucao.mensagem_gerada is None
        assert sender.enviadas == []

    def test_sem_arquivo_de_uf_envia_so_o_nacional(self, repo, sender, registros_consolidado):
        fonte = FonteFalsa(registros_consolidado, None, data_base_uf=None)
        servico = ServicoExecucao(repo, fonte, sender, relogio=lambda: AGORA)
        execucao = executar(servico)
        assert execucao.status is S.ENVIADO
        assert "recorte por UF" in execucao.mensagem_gerada
