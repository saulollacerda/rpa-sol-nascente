"""Política de retentativa da coleta — esperas crescentes entre as tentativas."""

import pytest

from app.domain.retentativa import PoliticaDeRetentativa


def test_esperas_crescem_pelo_fator():
    politica = PoliticaDeRetentativa(tentativas=4, espera_inicial=5, fator=3)
    assert politica.esperas() == [5, 15, 45]


def test_uma_tentativa_nao_espera():
    assert PoliticaDeRetentativa(tentativas=1).esperas() == []


def test_padrao_sao_tres_tentativas():
    assert len(PoliticaDeRetentativa().esperas()) == 2


@pytest.mark.parametrize("campos", [{"tentativas": 0}, {"espera_inicial": -1}, {"fator": 0.5}])
def test_valores_sem_sentido_sao_recusados(campos):
    with pytest.raises(ValueError):
        PoliticaDeRetentativa(**campos)
