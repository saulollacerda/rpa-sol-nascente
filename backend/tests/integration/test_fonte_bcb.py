"""Fonte real: robô + parsers, contra o site do BCB. Rodar com `pytest -m integration`."""

import pytest

from app.config import Settings
from app.domain.erros import ColetaError
from app.infra.fonte_bcb import FonteBCB

pytestmark = pytest.mark.integration


def test_consolidado_mensal_com_o_trimestre_de_uf_correspondente(tmp_path):
    dados = FonteBCB(Settings().bcb_base_url, tmp_path).obter("202607")

    assert dados.data_base_consolidado == "202607"
    assert dados.data_base_uf == "202606"  # trimestre mais recente até julho
    assert len(dados.consolidado) >= 700
    assert len(dados.uf) >= 7_000


def test_data_base_nao_publicada(tmp_path):
    with pytest.raises(ColetaError, match="não publicada"):
        FonteBCB(Settings().bcb_base_url, tmp_path).obter("209912")


def test_opcoes_do_painel(tmp_path):
    opcoes = FonteBCB(Settings().bcb_base_url, tmp_path).opcoes()

    assert opcoes.data_bases[0] >= "202607"
    assert opcoes.data_base_administradoras == opcoes.data_bases[0]
    honda = next(a for a in opcoes.administradoras if a.cnpj == "45441789")
    assert 4 in honda.segmentos
