"""Análise de mercado — regras de negócio da seção 7 do PRD.

Casos sintéticos documentam cada regra isoladamente; os casos com fixture
amarram o resultado aos números de referência do CLAUDE.md.
"""

import pytest

from app.domain.analise import analisar_nacional, analisar_praca, calcular_share
from app.domain.modelos import RegistroUF

HONDA = "45441789"
MOTOS = 4


def uf_(cnpj: str, uf: str, ativos: int, segmento: int = MOTOS, adesoes: int = 0) -> RegistroUF:
    return RegistroUF(
        nome_administradora=f"ADM {cnpj}",
        cnpj_raiz=cnpj,
        data_base="202606",
        segmento=segmento,
        uf=uf,
        contemplados_lance=0,
        contemplados_sorteio=0,
        nao_contemplados=ativos,
        contemplados_lance_no_trimestre=0,
        contemplados_sorteio_no_trimestre=0,
        adesoes_no_trimestre=adesoes,
    )


class TestShare:
    def test_percentual(self):
        assert calcular_share(25, 200) == pytest.approx(12.5)

    def test_praca_vazia_nao_divide_por_zero(self):
        assert calcular_share(0, 0) == 0.0


class TestRegrasDaPraca:
    def test_share_e_calculado_sobre_a_praca_inteira(self):
        """PRD §7: calcular depois de filtrar a administradora daria sempre 100%."""
        registros = [uf_("A", "PI", 300), uf_("B", "PI", 100)]
        assert analisar_praca(registros, "PI", MOTOS, "A").share == pytest.approx(75.0)

    def test_ignora_outras_ufs(self):
        registros = [uf_("A", "PI", 100), uf_("B", "MA", 900)]
        posicao = analisar_praca(registros, "PI", MOTOS, "A")
        assert posicao.ativos_praca == 100
        assert posicao.share == pytest.approx(100.0)

    def test_ignora_outros_segmentos(self):
        registros = [uf_("A", "PI", 100), uf_("B", "PI", 900, segmento=1)]
        assert analisar_praca(registros, "PI", MOTOS, "A").ativos_praca == 100

    def test_administradora_ausente_na_praca_devolve_none(self):
        """PRD §7: consulta sem resultado é desfecho legítimo, não erro."""
        assert analisar_praca([uf_("B", "PI", 100)], "PI", MOTOS, "A") is None

    def test_concorrentes_excluem_o_alvo_e_vem_ordenados(self):
        registros = [
            uf_("A", "PI", 500),
            uf_("B", "PI", 100),
            uf_("C", "PI", 300),
            uf_("D", "PI", 200),
        ]
        posicao = analisar_praca(registros, "PI", MOTOS, "A", top_concorrentes=2)
        assert [c.cnpj_raiz for c in posicao.concorrentes] == ["C", "D"]


class TestPracasReais:
    @pytest.mark.parametrize(
        ("uf", "ativos_praca", "administradoras", "ativos", "share"),
        [("PI", 155_648, 40, 148_962, 95.7), ("MA", 249_533, 45, 228_238, 91.5)],
    )
    def test_posicao_da_honda(self, registros_uf, uf, ativos_praca, administradoras, ativos, share):
        posicao = analisar_praca(registros_uf, uf, MOTOS, HONDA)
        assert posicao.ativos_praca == ativos_praca
        assert posicao.administradoras_na_praca == administradoras
        assert posicao.ativos == ativos
        assert posicao.share == pytest.approx(share, abs=0.05)

    def test_contemplacao_no_trimestre_no_piaui(self, registros_uf):
        posicao = analisar_praca(registros_uf, "PI", MOTOS, HONDA)
        assert posicao.adesoes_no_trimestre == 19_340
        assert posicao.contemplados_lance_no_trimestre == 9_354
        assert posicao.contemplados_sorteio_no_trimestre == 951
        assert posicao.contemplados_no_trimestre == 10_305

    @pytest.mark.parametrize(
        ("uf", "esperado"),
        [
            ("PI", [("BB CONSÓRCIOS", 1.8), ("YAMAHA ADM CONS LTDA", 0.9)]),
            ("MA", [("YAMAHA ADM CONS LTDA", 3.3), ("BB CONSÓRCIOS", 1.9)]),
        ],
    )
    def test_principais_concorrentes(self, registros_uf, uf, esperado):
        posicao = analisar_praca(registros_uf, uf, MOTOS, HONDA, top_concorrentes=2)
        obtido = [(c.nome_administradora, round(c.share, 1)) for c in posicao.concorrentes]
        assert obtido == esperado


class TestNacional:
    def test_posicao_da_honda(self, registros_consolidado):
        posicao = analisar_nacional(registros_consolidado, MOTOS, HONDA)
        assert posicao.cotas_ativas == 2_565_256
        assert posicao.cotas_ativas_mercado == 3_319_425
        assert posicao.administradoras_no_segmento == 125
        assert posicao.share == pytest.approx(77.3, abs=0.05)
        assert posicao.taxa_administracao == pytest.approx(23.2, abs=0.05)
        assert posicao.grupos_ativos == 3_760

    def test_lideres_depois_da_honda(self, registros_consolidado):
        posicao = analisar_nacional(registros_consolidado, MOTOS, HONDA, top_concorrentes=3)
        assert [round(c.share, 1) for c in posicao.concorrentes] == [4.4, 3.9, 1.9]

    def test_administradora_ausente_devolve_none(self, registros_consolidado):
        assert analisar_nacional(registros_consolidado, MOTOS, "99999999") is None
