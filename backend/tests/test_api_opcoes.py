"""GET /opcoes — o que o painel oferece para escolha."""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencias import get_opcoes
from app.domain.erros import ColetaError
from app.domain.opcoes import Administradora, Opcoes
from app.main import app

OPCOES = Opcoes(
    data_bases=("202607", "202606", "202605"),
    data_base_administradoras="202607",
    administradoras=(
        Administradora(cnpj="45441789", nome="ADM CONS NAC HONDA LTDA", segmentos=(3, 4)),
        Administradora(cnpj="00000776", nome="ITAÚ ADM DE CONSÓRCIOS LTDA", segmentos=(1, 4)),
    ),
)


class FonteDeOpcoes:
    def __init__(self, falhar=False):
        self.falhar = falhar

    def obter(self):
        if self.falhar:
            raise ColetaError("site do BCB indisponível")
        return OPCOES


@pytest.fixture
def cliente():
    fonte = FonteDeOpcoes()
    app.dependency_overrides[get_opcoes] = lambda: fonte
    yield TestClient(app), fonte
    app.dependency_overrides.clear()


def test_data_bases_da_mais_recente_para_a_mais_antiga(cliente):
    http, _ = cliente
    assert http.get("/opcoes").json()["data_bases"] == ["202607", "202606", "202605"]


def test_administradoras_com_segmentos(cliente):
    http, _ = cliente
    [honda, itau] = http.get("/opcoes").json()["administradoras"]
    assert honda == {"cnpj": "45441789", "nome": "ADM CONS NAC HONDA LTDA", "segmentos": [3, 4]}


def test_segmentos_e_ufs_por_extenso(cliente):
    http, _ = cliente
    corpo = http.get("/opcoes").json()
    assert {"codigo": 4, "nome": "motocicletas e motonetas"} in corpo["segmentos"]
    assert {"sigla": "PI", "nome": "Piauí"} in corpo["ufs"]
    assert len(corpo["ufs"]) == 27


def test_padroes_da_sol_nascente(cliente):
    http, _ = cliente
    padrao = http.get("/opcoes").json()["padrao"]
    assert padrao == {
        "data_base": "202607",
        "segmento": 4,
        "ufs": ["PI", "MA"],
        "cnpj_administradora": "45441789",
        "top_concorrentes": 3,
    }


def test_site_fora_do_ar_responde_503_com_o_motivo(cliente):
    http, fonte = cliente
    fonte.falhar = True
    resposta = http.get("/opcoes")
    assert resposta.status_code == 503
    assert "indisponível" in resposta.json()["detail"]
