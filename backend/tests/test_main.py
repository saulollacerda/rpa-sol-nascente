"""Aplicação FastAPI."""

from fastapi.testclient import TestClient

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
