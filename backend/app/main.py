"""Ponto de entrada da aplicação."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI

from app.api.dependencias import get_settings
from app.api.execucoes import router as execucoes
from app.api.opcoes import router as opcoes
from app.api.whatsapp import router as whatsapp
from app.domain.servico import ServicoExecucao
from app.infra.cache import CacheComValidade
from app.infra.db import RepositorioSQL, criar_engine, criar_tabelas
from app.infra.fonte_bcb import FonteBCB
from app.infra.logs import configurar_logs
from app.infra.whatsapp import criar_sender

VERSAO = "0.1.0"


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    """Monta as dependências reais. Nos testes elas são substituídas."""
    settings = get_settings()
    configurar_logs(settings.log_level)
    engine = criar_engine(settings.database_url)
    criar_tabelas(engine)
    fonte = FonteBCB(settings.bcb_base_url, settings.data_dir, settings.playwright_headless)
    relogio = lambda: datetime.now(UTC)  # noqa: E731
    sender = criar_sender(settings)
    app.state.servico = ServicoExecucao(RepositorioSQL(engine), fonte, sender, relogio=relogio)
    app.state.conexao = sender
    app.state.opcoes = CacheComValidade(
        fonte.opcoes, timedelta(hours=settings.catalogo_ttl_horas), relogio
    )
    yield


app = FastAPI(title="Radar de Consórcio de Motos", version=VERSAO, lifespan=ciclo_de_vida)
app.include_router(execucoes)
app.include_router(opcoes)
app.include_router(whatsapp)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "versao": VERSAO}
