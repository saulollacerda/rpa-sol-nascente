"""Ponto de entrada da aplicação."""

from fastapi import FastAPI

from app.config import Settings

VERSAO = "0.1.0"

app = FastAPI(title="Radar de Consórcio de Motos", version=VERSAO)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "versao": VERSAO}


def get_settings() -> Settings:
    return Settings()
