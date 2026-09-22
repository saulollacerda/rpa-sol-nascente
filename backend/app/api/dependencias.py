"""Dependências da API. Os testes as substituem por implementações falsas."""

from functools import lru_cache

from fastapi import Request

from app.config import Settings
from app.domain.servico import ServicoExecucao


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_servico(request: Request) -> ServicoExecucao:
    return request.app.state.servico


def get_opcoes(request: Request):  # noqa: ANN201 — CacheComValidade[Opcoes]
    return request.app.state.opcoes
