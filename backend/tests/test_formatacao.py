"""Formatação para leitura no WhatsApp, em convenção brasileira."""

import pytest

from app.domain.formatacao import (
    formatar_compacto,
    formatar_data_base,
    formatar_inteiro,
    formatar_percentual,
    nome_da_uf,
)


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(0, "0"), (951, "951"), (19_340, "19.340"), (3_319_425, "3.319.425")],
)
def test_inteiro_com_ponto_de_milhar(valor, esperado):
    assert formatar_inteiro(valor) == esperado


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(95.7, "95,7%"), (95.70437, "95,7%"), (0.0, "0,0%"), (100.0, "100,0%")],
)
def test_percentual_com_virgula(valor, esperado):
    assert formatar_percentual(valor) == esperado


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(2_565_256, "2,57 mi"), (3_319_425, "3,32 mi"), (148_962, "149 mil"), (951, "951")],
)
def test_compacto(valor, esperado):
    assert formatar_compacto(valor) == esperado


@pytest.mark.parametrize(
    ("data_base", "esperado"),
    [("202606", "Junho/2026"), ("202607", "Julho/2026"), ("202412", "Dezembro/2024")],
)
def test_data_base_por_extenso(data_base, esperado):
    assert formatar_data_base(data_base) == esperado


@pytest.mark.parametrize("invalida", ["2026-06", "202613", "202600", ""])
def test_data_base_invalida_volta_como_veio(invalida):
    """Nunca derrubar a mensagem por um rótulo."""
    assert formatar_data_base(invalida) == invalida


@pytest.mark.parametrize(
    ("sigla", "nome"), [("PI", "Piauí"), ("MA", "Maranhão"), ("SP", "São Paulo")]
)
def test_nome_da_uf(sigla, nome):
    assert nome_da_uf(sigla) == nome


def test_cobre_as_27_ufs():
    from app.domain.formatacao import UFS

    assert len(UFS) == 27


def test_uf_desconhecida_volta_a_sigla():
    assert nome_da_uf("XX") == "XX"
