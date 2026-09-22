"""Normalização dos campos do BCB.

Cada teste aqui corresponde a uma armadilha real observada nos arquivos,
documentada no CLAUDE.md e no ADR-002.
"""

import pytest

from app.parsing.normalizacao import para_decimal, para_inteiro, para_texto, raiz_cnpj


class TestDecimalComVirgula:
    def test_converte_virgula_para_ponto(self):
        assert para_decimal("24,02186") == pytest.approx(24.02186)

    def test_aceita_ponto_tambem(self):
        assert para_decimal("23.2") == pytest.approx(23.2)

    def test_vazio_vira_zero(self):
        assert para_decimal("") == 0.0
        assert para_decimal(None) == 0.0

    def test_valor_invalido_vira_zero(self):
        assert para_decimal("n/d") == 0.0


class TestInteiro:
    def test_converte(self):
        assert para_inteiro("492484") == 492484

    def test_vazio_vira_zero(self):
        """Informação incompleta é cenário previsto no enunciado."""
        assert para_inteiro("") == 0
        assert para_inteiro(None) == 0

    def test_valor_invalido_vira_zero(self):
        assert para_inteiro("n/d") == 0


class TestTexto:
    def test_remove_padding_de_espacos(self):
        """Resquício de largura fixa: sem strip o agrupamento duplica registros."""
        bruto = "ITAÚ ADM DE CONSÓRCIOS LTDA                                 "
        assert para_texto(bruto) == "ITAÚ ADM DE CONSÓRCIOS LTDA"

    def test_nulo_vira_string_vazia(self):
        assert para_texto(None) == ""


class TestRaizCnpj:
    def test_preserva_zeros_a_esquerda(self):
        """Converter para int perderia os zeros — CNPJ é identificador, não número."""
        assert raiz_cnpj("00000776") == "00000776"

    def test_completa_com_zeros_ate_oito_digitos(self):
        assert raiz_cnpj("776") == "00000776"

    def test_remove_pontuacao(self):
        assert raiz_cnpj("00.000.776") == "00000776"
