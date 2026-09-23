"""Parser dos dados por UF.

Assertivas ancoradas nos números de referência do CLAUDE.md (Junho/2026).
"""

import pytest

from app.parsing.uf import ler_uf

SEGMENTO_MOTOS = 4


@pytest.fixture(scope="module")
def registros(zip_uf):
    return ler_uf(zip_uf)


@pytest.fixture(scope="module")
def motos(registros):
    return [r for r in registros if r.segmento == SEGMENTO_MOTOS]


def test_le_todas_as_linhas(registros):
    assert len(registros) == 7_667


def test_cobre_as_27_unidades_da_federacao(registros):
    assert len({r.uf for r in registros}) == 27


def test_data_base_do_arquivo(registros):
    assert {r.data_base for r in registros} == {"202606"}


def test_nome_vem_sem_padding(registros):
    assert all(r.nome_administradora == r.nome_administradora.strip() for r in registros)


@pytest.mark.parametrize(
    (
        "uf",
        "ativos_praca",
        "administradoras",
        "ativos_honda",
        "adesoes_honda",
        "contemplados_honda",
    ),
    [
        ("PI", 155_648, 40, 148_962, 19_340, 10_305),
        ("MA", 249_533, 45, 228_238, 27_261, 13_402),
    ],
)
def test_pracas_da_sol_nascente(
    motos, uf, ativos_praca, administradoras, ativos_honda, adesoes_honda, contemplados_honda
):
    praca = [r for r in motos if r.uf == uf]
    assert len(praca) == administradoras
    assert sum(r.consorciados_ativos for r in praca) == ativos_praca

    honda = next(r for r in praca if "HONDA" in r.nome_administradora)
    assert honda.consorciados_ativos == ativos_honda
    assert honda.adesoes_no_trimestre == adesoes_honda
    assert honda.contemplados_no_trimestre == contemplados_honda


def test_separa_contemplacao_por_lance_e_sorteio(motos):
    """Distinção que só existe no dataset de UF."""
    honda_pi = next(r for r in motos if r.uf == "PI" and "HONDA" in r.nome_administradora)
    assert honda_pi.contemplados_lance_no_trimestre == 9_354
    assert honda_pi.contemplados_sorteio_no_trimestre == 951


def test_le_os_excluidos(motos):
    """Base da taxa de exclusão do template."""
    honda_pi = next(r for r in motos if r.uf == "PI" and "HONDA" in r.nome_administradora)
    assert honda_pi.excluidos_contemplados == 22_695
    assert honda_pi.excluidos_nao_contemplados == 82_088
    assert honda_pi.excluidos == 104_783
