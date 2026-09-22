"""API de execuções — o painel dispara a consulta e acompanha o status.

As dependências de produção são trocadas por fonte e envio falsos: o fluxo
inteiro roda sem navegador e sem rede. O TestClient executa as BackgroundTasks
ao fim da requisição, então o status já está final no GET seguinte.
"""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.dependencias import get_servico, get_settings
from app.config import Settings
from app.domain.servico import ServicoExecucao
from app.infra.db import RepositorioSQL, criar_engine, criar_tabelas
from app.infra.whatsapp import FakeSender
from app.main import app
from tests.fakes import FonteFalsa

CORPO = {"data_base": "202607", "ufs": ["PI", "MA"], "destinatario": "5586999990000"}


@pytest.fixture
def sender():
    return FakeSender()


@pytest.fixture
def fonte(registros_consolidado, registros_uf):
    return FonteFalsa(registros_consolidado, registros_uf)


@pytest.fixture
def cliente(fonte, sender):
    engine = criar_engine("sqlite:///:memory:")
    criar_tabelas(engine)
    servico = ServicoExecucao(
        RepositorioSQL(engine), fonte, sender, relogio=lambda: datetime.now(UTC)
    )
    app.dependency_overrides[get_servico] = lambda: servico
    app.dependency_overrides[get_settings] = lambda: Settings(whatsapp_destinatario="5586777770000")
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestSolicitar:
    def test_aceita_e_processa_em_segundo_plano(self, cliente):
        resposta = cliente.post("/execucoes", json=CORPO)
        assert resposta.status_code == 202
        assert resposta.json()["decisao"] == "CRIAR"

        execucao_id = resposta.json()["execucao"]["id"]
        final = cliente.get(f"/execucoes/{execucao_id}").json()
        assert final["status"] == "ENVIADO"
        assert "PIAUÍ" in final["mensagem_gerada"]

    def test_repetir_o_pedido_nao_reenvia(self, cliente, sender):
        cliente.post("/execucoes", json=CORPO)
        de_novo = cliente.post("/execucoes", json={**CORPO, "ufs": ["MA", "PI"]})
        assert de_novo.status_code == 200
        assert de_novo.json()["decisao"] == "REUSAR"
        assert len(sender.enviadas) == 1

    def test_defaults_do_painel(self, cliente, sender):
        """Segmento 4, PI e MA, Honda e destinatário do .env — PRD, seção 5."""
        cliente.post("/execucoes", json={"data_base": "202607"})
        [(destino, _)] = sender.enviadas
        assert destino == "5586777770000"

    def test_sem_destinatario_e_sem_default(self, cliente):
        app.dependency_overrides[get_settings] = lambda: Settings(whatsapp_destinatario=None)
        resposta = cliente.post("/execucoes", json={"data_base": "202607"})
        assert resposta.status_code == 422
        assert "destinatário" in resposta.json()["detail"]

    def test_falha_de_coleta_fica_registrada(self, cliente, fonte):
        fonte.falhar_com = "site do BCB indisponível"
        execucao_id = cliente.post("/execucoes", json=CORPO).json()["execucao"]["id"]
        final = cliente.get(f"/execucoes/{execucao_id}").json()
        assert final["status"] == "FALHA_COLETA"
        assert final["erro_descricao"] == "site do BCB indisponível"

    def test_retentar_depois_da_falha(self, cliente, fonte):
        fonte.falhar_com = "fora do ar"
        cliente.post("/execucoes", json=CORPO)
        fonte.falhar_com = None
        resposta = cliente.post("/execucoes", json=CORPO)
        assert resposta.status_code == 202
        assert resposta.json()["decisao"] == "RETENTAR"
        final = cliente.get(f"/execucoes/{resposta.json()['execucao']['id']}").json()
        assert final["status"] == "ENVIADO"
        assert final["tentativas"] == 2


class TestValidacao:
    @pytest.mark.parametrize(
        "invalido",
        [
            {"data_base": "2026-07"},
            {"data_base": "202613"},
            {"ufs": ["XX"]},
            {"ufs": []},
            {"segmento": 9},
            {"top_concorrentes": -1},
            {"destinatario": "123"},
            {"cnpj_administradora": "abc"},
        ],
    )
    def test_parametros_invalidos_sao_recusados(self, cliente, invalido, sender):
        assert cliente.post("/execucoes", json={**CORPO, **invalido}).status_code == 422
        assert sender.enviadas == []


class TestConsultar:
    def test_execucao_inexistente(self, cliente):
        assert cliente.get("/execucoes/999").status_code == 404

    def test_historico_da_mais_recente_para_a_mais_antiga(self, cliente):
        primeira = cliente.post("/execucoes", json=CORPO).json()["execucao"]["id"]
        segunda = cliente.post("/execucoes", json={**CORPO, "ufs": ["PI"]}).json()["execucao"]["id"]
        historico = cliente.get("/execucoes").json()
        assert [e["id"] for e in historico] == [segunda, primeira]

    def test_historico_com_limite(self, cliente):
        cliente.post("/execucoes", json=CORPO)
        cliente.post("/execucoes", json={**CORPO, "ufs": ["PI"]})
        assert len(cliente.get("/execucoes?limite=1").json()) == 1

    def test_historico_traz_os_campos_do_enunciado(self, cliente):
        """Consulta, dados, data e hora, destinatário, mensagem, status e erro."""
        cliente.post("/execucoes", json=CORPO)
        [execucao] = cliente.get("/execucoes").json()
        for campo in (
            "parametros",
            "dados_encontrados",
            "criado_em",
            "destinatario",
            "mensagem_gerada",
            "status",
            "erro_descricao",
        ):
            assert campo in execucao
