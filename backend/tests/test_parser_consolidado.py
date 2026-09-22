"""Parser dos dados consolidados.

As assertivas usam os números de referência do CLAUDE.md, apurados da fonte.
"""

import pytest

from app.parsing.consolidado import ler_consolidado

SEGMENTO_MOTOS = 4


@pytest.fixture(scope="module")
def registros(zip_consolidado):
    return ler_consolidado(zip_consolidado)


def test_le_todas_as_linhas(registros):
    assert len(registros) == 750


def test_decodifica_acentos_do_windows_1252(registros):
    """Ler como UTF-8 quebraria em CONSÓRCIO."""
    nomes = {r.nome_administradora for r in registros}
    assert "ITAÚ ADM DE CONSÓRCIOS LTDA" in nomes


def test_nome_vem_sem_padding(registros):
    assert all(r.nome_administradora == r.nome_administradora.strip() for r in registros)


def test_cnpj_preserva_zeros_a_esquerda(registros):
    itau = next(r for r in registros if r.nome_administradora.startswith("ITAÚ"))
    assert itau.cnpj_raiz == "00000776"


def test_data_base_vem_do_arquivo_e_nao_da_documentacao(registros):
    """O dicionário declara AAAA-MM, mas o arquivo traz AAAAMM."""
    assert {r.data_base for r in registros} == {"202607"}


@pytest.fixture(scope="module")
def motos(registros):
    return [r for r in registros if r.segmento == SEGMENTO_MOTOS]


class TestSegmentoDeMotos:
    def test_quantidade_de_administradoras(self, motos):
        assert len(motos) == 125

    def test_total_de_cotas_ativas_do_mercado(self, motos):
        assert sum(r.cotas_ativas for r in motos) == 3_319_425

    def test_numeros_da_honda(self, motos):
        honda = next(r for r in motos if "HONDA" in r.nome_administradora)
        assert honda.cotas_ativas == 2_565_256
        assert honda.grupos_ativos == 3_760
        assert honda.taxa_administracao == pytest.approx(23.2, abs=0.1)


def test_soma_inadimplentes_contemplados_e_nao_contemplados(motos):
    honda = next(r for r in motos if "HONDA" in r.nome_administradora)
    assert honda.cotas_inadimplentes == (
        honda.cotas_ativas_contempladas_inadimplentes
        + honda.cotas_ativas_nao_contempladas_inadimplentes
    )
    assert honda.cotas_inadimplentes > 0
