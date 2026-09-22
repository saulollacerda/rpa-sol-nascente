"""Cache com validade — camada de catálogo do ADR-006."""

from datetime import UTC, datetime, timedelta

import pytest

from app.infra.cache import CacheComValidade

INICIO = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)


class Relogio:
    def __init__(self):
        self.agora = INICIO

    def __call__(self):
        return self.agora


@pytest.fixture
def relogio():
    return Relogio()


def contador():
    chamadas = []

    def carregar():
        chamadas.append(1)
        return len(chamadas)

    return carregar, chamadas


def test_carrega_uma_vez_dentro_da_validade(relogio):
    carregar, chamadas = contador()
    cache = CacheComValidade(carregar, timedelta(hours=6), relogio)
    assert cache.obter() == 1
    relogio.agora += timedelta(hours=5, minutes=59)
    assert cache.obter() == 1
    assert len(chamadas) == 1


def test_recarrega_depois_da_validade(relogio):
    carregar, _ = contador()
    cache = CacheComValidade(carregar, timedelta(hours=6), relogio)
    cache.obter()
    relogio.agora += timedelta(hours=6)
    assert cache.obter() == 2


def test_falha_nao_fica_em_cache(relogio):
    """Se o site estava fora do ar, a próxima tentativa tem que ir ao site de novo."""
    tentativas = []

    def carregar():
        tentativas.append(1)
        if len(tentativas) == 1:
            raise RuntimeError("fora do ar")
        return "ok"

    cache = CacheComValidade(carregar, timedelta(hours=6), relogio)
    with pytest.raises(RuntimeError):
        cache.obter()
    assert cache.obter() == "ok"


def test_invalidar_forca_recarga(relogio):
    carregar, _ = contador()
    cache = CacheComValidade(carregar, timedelta(hours=6), relogio)
    cache.obter()
    cache.invalidar()
    assert cache.obter() == 2


def test_informa_quando_foi_carregado(relogio):
    carregar, _ = contador()
    cache = CacheComValidade(carregar, timedelta(hours=6), relogio)
    assert cache.carregado_em is None
    cache.obter()
    assert cache.carregado_em == INICIO
