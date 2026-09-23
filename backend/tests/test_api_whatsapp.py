"""GET /whatsapp/conexao — o painel mostra se o WhatsApp está conectado."""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencias import get_conexao
from app.domain.erros import EnvioError
from app.domain.portas import EstadoConexao, SituacaoConexao
from app.main import app


class ConexaoFalsa:
    def __init__(self, estado: EstadoConexao | None = None, falhar: str | None = None):
        self._estado = estado
        self._falhar = falhar
        self.reconexoes = 0

    def estado(self) -> EstadoConexao:
        if self._falhar:
            raise EnvioError(self._falhar)
        assert self._estado is not None
        return self._estado

    def reconectar(self) -> None:
        if self._falhar:
            raise EnvioError(self._falhar)
        self.reconexoes += 1


@pytest.fixture
def usar():
    def instalar(conexao: ConexaoFalsa) -> TestClient:
        app.dependency_overrides[get_conexao] = lambda: conexao
        return TestClient(app)

    yield instalar
    app.dependency_overrides.clear()


def test_conectado(usar):
    http = usar(ConexaoFalsa(EstadoConexao(SituacaoConexao.CONECTADO, conta="Demo (5586)")))
    assert http.get("/whatsapp/conexao").json() == {
        "situacao": "CONECTADO",
        "conta": "Demo (5586)",
        "qr_code": None,
        "mensagem": None,
    }


def test_aguardando_qr_code(usar):
    estado = EstadoConexao(SituacaoConexao.AGUARDANDO_QR, qr_code="data:image/png;base64,AAA")
    corpo = usar(ConexaoFalsa(estado)).get("/whatsapp/conexao").json()
    assert corpo["situacao"] == "AGUARDANDO_QR"
    assert corpo["qr_code"] == "data:image/png;base64,AAA"


def test_waha_fora_do_ar_vira_situacao_e_nao_erro(usar):
    """O painel consulta em loop: um 5xx viraria ruído; a situação explica o problema."""
    http = usar(ConexaoFalsa(falhar="WAHA não está acessível em http://waha:3000"))
    resposta = http.get("/whatsapp/conexao")
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "INDISPONIVEL"
    assert "não está acessível" in resposta.json()["mensagem"]


def test_reconectar_pede_um_qr_code_novo(usar):
    conexao = ConexaoFalsa(EstadoConexao(SituacaoConexao.DESCONECTADO))
    resposta = usar(conexao).post("/whatsapp/conexao/reconectar")
    assert resposta.status_code == 202
    assert conexao.reconexoes == 1


def test_reconectar_com_waha_fora_do_ar(usar):
    http = usar(ConexaoFalsa(falhar="WAHA não está acessível"))
    resposta = http.post("/whatsapp/conexao/reconectar")
    assert resposta.status_code == 503
    assert "não está acessível" in resposta.json()["detail"]
