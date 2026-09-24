"""Aplicação FastAPI."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencias import get_settings
from app.domain.execucao import ParametrosConsulta, StatusExecucao, chave_idempotencia
from app.infra.db import RepositorioSQL, criar_engine, criar_tabelas
from app.main import app

client = TestClient(app)


def test_health_responde_ok():
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_health_informa_a_versao():
    assert resposta_versao() == "0.1.0"


def resposta_versao() -> str:
    return client.get("/health").json()["versao"]


def test_subida_recupera_execucoes_interrompidas(tmp_path, monkeypatch):
    """Um restart no meio da coleta não pode deixar a consulta travada para sempre."""
    url = f"sqlite:///{tmp_path / 'execucoes.db'}"
    engine = criar_engine(url)
    criar_tabelas(engine)
    repo = RepositorioSQL(engine)
    p = ParametrosConsulta(
        data_base="202607",
        segmento=4,
        ufs=("PI", "MA"),
        cnpj_administradora="45441789",
        top_concorrentes=3,
        destinatario="5586999990000",
    )
    agora = datetime(2026, 9, 22, tzinfo=UTC)
    parada = repo.criar(p, chave_idempotencia(p), agora)
    repo.atualizar(parada.id, StatusExecucao.COLETANDO, agora)

    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("WHATSAPP_PROVIDER", "fake")
    get_settings.cache_clear()
    try:
        with TestClient(app) as cliente:
            execucao = cliente.get(f"/execucoes/{parada.id}").json()
    finally:
        get_settings.cache_clear()

    assert execucao["status"] == "FALHA_COLETA"
