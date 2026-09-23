"""Formatação para leitura no WhatsApp, em convenção brasileira."""

import pytest

from app.domain.formatacao import (
    com_preposicao,
    formatar_compacto,
    formatar_data_base,
    formatar_inteiro,
    formatar_mes_curto,
    formatar_percentual,
    formatar_pontos,
    formatar_trimestre,
    nome_curto,
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


class TestTemplateDoRelatorio:
    @pytest.mark.parametrize(
        ("completo", "curto"),
        [
            ("ADM CONS NAC HONDA LTDA", "Honda"),
            ("YAMAHA ADM CONS LTDA", "Yamaha"),
            ("ADM CONS SICREDI LTDA", "Sicredi"),
            ("ÂNCORA ADM CONS S.A.", "Âncora"),
            ("SPERTA ADM CONSORCIO NAC LTDA", "Sperta"),
            ("TRADIÇÃO ADM CONS. LTDA.", "Tradição"),
            ("CONS. NACIONAL VOLKSWAGEN LTDA.", "Volkswagen"),
            ("ITAÚ ADM DE CONSÓRCIOS LTDA", "Itaú"),
            ("BB CONSÓRCIOS", "BB"),
            ("ADM CONS RCI BRASIL LTDA", "RCI Brasil"),
            ("SUZUKI MOTOS ADM. CONS. LTDA", "Suzuki Motos"),
            ("SANTA FÉ ADM CONS LTDA", "Santa Fé"),
            ("APEC ADM CONSORCIO S/A", "Apec"),
        ],
    )
    def test_nome_curto_da_administradora(self, completo, curto):
        assert nome_curto(completo) == curto

    def test_nome_so_de_ruido_volta_como_veio(self):
        assert nome_curto("CONSÓRCIO NACIONAL") == "CONSÓRCIO NACIONAL"

    @pytest.mark.parametrize(
        ("data_base", "trimestre"),
        [
            ("202603", "1º trimestre/2026"),
            ("202606", "2º trimestre/2026"),
            ("202612", "4º trimestre/2026"),
        ],
    )
    def test_trimestre_da_data_base(self, data_base, trimestre):
        assert formatar_trimestre(data_base) == trimestre

    def test_mes_abreviado(self):
        assert formatar_mes_curto("202606") == "Jun/2026"
        assert formatar_mes_curto("2026") == "2026"

    def test_pontos_percentuais_com_sinal(self):
        assert formatar_pontos(11.34) == "+11,3 p.p."
        assert formatar_pontos(-4.2) == "-4,2 p.p."

    @pytest.mark.parametrize(("sigla", "com"), [("PR", "no PR"), ("MG", "em MG"), ("BA", "na BA")])
    def test_preposicao_da_uf(self, sigla, com):
        assert com_preposicao(sigla) == com
