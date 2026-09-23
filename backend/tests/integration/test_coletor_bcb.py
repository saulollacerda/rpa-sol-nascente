"""Coleta contra o site real do BCB.

Fora da suíte padrão: rodar com `pytest -m integration`. Depende de rede e da
disponibilidade do site — por isso não é TDD (ver CLAUDE.md).
"""

import pytest

from app.config import Settings
from app.parsing.consolidado import ler_consolidado
from app.parsing.uf import ler_uf
from app.rpa.catalogo import Dataset, ItemCatalogo
from app.rpa.coletor import ColetaError, ColetorBCB

pytestmark = pytest.mark.integration

URL = Settings().bcb_base_url


@pytest.fixture(scope="module")
def coletor():
    with ColetorBCB(URL) as sessao:
        yield sessao


def test_catalogo_do_site_real(coletor):
    catalogo = coletor.ler_catalogo()
    assert len(catalogo.do_dataset(Dataset.CONSOLIDADO)) >= 355
    assert len(catalogo.do_dataset(Dataset.UF)) >= 72
    assert catalogo.mais_recente(Dataset.UF).data_base >= "202606"


@pytest.mark.parametrize(
    ("dataset", "parser", "linhas_minimas"),
    [(Dataset.UF, ler_uf, 7_000), (Dataset.CONSOLIDADO, ler_consolidado, 700)],
)
def test_baixa_e_parseia_o_mais_recente(coletor, tmp_path, dataset, parser, linhas_minimas):
    item = coletor.ler_catalogo().mais_recente(dataset)
    caminho = coletor.baixar(item, tmp_path)

    assert caminho.name == item.nome
    assert caminho.stat().st_size == item.tamanho
    assert len(parser(caminho)) >= linhas_minimas


def test_opcao_inexistente_falha_explicitamente(coletor, tmp_path):
    fantasma = ItemCatalogo(
        dataset=Dataset.UF,
        data_base="190001",
        nome="190001Consorcios_UF.zip",
        url=URL,
        tamanho=0,
        publicado_em=None,
    )
    with pytest.raises(ColetaError, match="não está no dropdown"):
        coletor.baixar(fantasma, tmp_path)
