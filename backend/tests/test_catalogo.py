"""Catálogo de arquivos do BCB — ADR-008.

A conversão do JSON que a página requisita é função pura: testável com as
respostas reais capturadas, sem navegador.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.rpa.catalogo import Dataset, extrair_itens, montar_catalogo

FIXTURES = Path(__file__).parent / "fixtures"
ORIGEM = "https://www.bcb.gov.br"


def carregar(nome: str) -> dict:
    return json.loads((FIXTURES / nome).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def catalogo():
    corpos = [carregar("catalogo_consolidado.json"), carregar("catalogo_uf.json")]
    return montar_catalogo(corpos, ORIGEM)


class TestRespostasReais:
    def test_quantidade_de_itens_por_dataset(self, catalogo):
        assert len(catalogo.do_dataset(Dataset.CONSOLIDADO)) == 355
        assert len(catalogo.do_dataset(Dataset.UF)) == 72

    def test_mais_recentes(self, catalogo):
        assert catalogo.mais_recente(Dataset.CONSOLIDADO).data_base == "202607"
        assert catalogo.mais_recente(Dataset.UF).data_base == "202606"

    def test_url_absoluta_do_arquivo(self, catalogo):
        """A informação que o texto do dropdown não tinha — motivo do ADR-008."""
        item = catalogo.buscar(Dataset.UF, "202606")
        assert item.url == (
            "https://www.bcb.gov.br/content/estabilidadefinanceira/consorcio-banco-de-dados"
            "/dados-por-unidade-da-federacao/202606Consorcios_UF.zip"
        )

    def test_tamanho_bate_com_o_arquivo_verificado_no_spike(self, catalogo):
        assert catalogo.buscar(Dataset.UF, "202606").tamanho == 105_859

    def test_data_de_publicacao(self, catalogo):
        item = catalogo.buscar(Dataset.UF, "202606")
        assert item.publicado_em == datetime(2026, 8, 28, 13, 19, tzinfo=UTC)

    def test_rotulo_usado_para_achar_a_opcao_no_dropdown(self, catalogo):
        assert catalogo.buscar(Dataset.UF, "202606").rotulo == "202606Consorcios_UF"

    def test_data_bases_em_ordem_decrescente(self, catalogo):
        datas = catalogo.data_bases(Dataset.UF)
        assert datas[:3] == ["202606", "202603", "202512"]
        assert datas == sorted(datas, reverse=True)

    def test_data_base_inexistente(self, catalogo):
        assert catalogo.buscar(Dataset.UF, "202607") is None


def item_(nome: str, url: str | None = "/x/y.zip", **extra) -> dict:
    base = {"Nome": nome, "Url": url, "Tamanho": "100", "DataPublicacao": "2026-08-28T13:19:00Z"}
    return {**base, **extra}


class TestRegrasDeClassificacao:
    def test_classifica_pelo_nome_do_arquivo(self):
        corpo = {"conteudo": [item_("202607Consorcios.zip"), item_("202606Consorcios_UF.zip")]}
        datasets = {i.dataset for i in extrair_itens(corpo, ORIGEM)}
        assert datasets == {Dataset.CONSOLIDADO, Dataset.UF}

    def test_ignora_arquivos_fora_dos_padroes(self):
        """Os contábeis descontinuados vêm na mesma API e não interessam."""
        corpo = {"conteudo": [item_("ConsorciosAdministradoras_4110.zip")]}
        assert extrair_itens(corpo, ORIGEM) == []

    def test_aceita_lista_sem_envelope(self):
        assert len(extrair_itens([item_("202607Consorcios.zip")], ORIGEM)) == 1

    @pytest.mark.parametrize("corpo", [None, "texto", 42, {"outra": "coisa"}, {"conteudo": "x"}])
    def test_outras_respostas_da_pagina_nao_quebram(self, corpo):
        """A página faz dezenas de requisições; só algumas são o catálogo."""
        assert extrair_itens(corpo, ORIGEM) == []

    def test_item_sem_url_e_descartado(self):
        """Informação incompleta: sem URL não há o que baixar."""
        assert extrair_itens([item_("202607Consorcios.zip", url=None)], ORIGEM) == []

    def test_url_ja_absoluta_e_preservada(self):
        url = "https://outro.host/a/202607Consorcios.zip"
        [item] = extrair_itens([item_("202607Consorcios.zip", url=url)], ORIGEM)
        assert item.url == url

    def test_campos_opcionais_invalidos_nao_descartam_o_item(self):
        corpo = [item_("202607Consorcios.zip", Tamanho="?", DataPublicacao="ontem")]
        [item] = extrair_itens(corpo, ORIGEM)
        assert item.tamanho == 0
        assert item.publicado_em is None

    def test_duplicatas_entre_respostas_viram_um_item(self):
        """A página pode pedir a mesma lista mais de uma vez."""
        corpo = [item_("202607Consorcios.zip")]
        catalogo = montar_catalogo([corpo, corpo], ORIGEM)
        assert len(catalogo.do_dataset(Dataset.CONSOLIDADO)) == 1

    def test_catalogo_vazio(self):
        catalogo = montar_catalogo([], ORIGEM)
        assert catalogo.mais_recente(Dataset.UF) is None
        assert catalogo.vazio
