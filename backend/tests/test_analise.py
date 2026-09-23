"""Análise de mercado — regras do template do relatório.

Casos sintéticos documentam cada regra isoladamente; os casos com fixture
amarram o resultado aos números de referência do CLAUDE.md e ao exemplo
preenchido do template (SP, MG e PR em Junho/2026).
"""

import pytest

from app.domain.analise import (
    CNPJ_HONDA,
    Alerta,
    Movimento,
    ParticipacaoNaUF,
    PerfilAdministradora,
    calcular_share,
    detectar_alertas,
    escolher_administradoras,
    indicadores_nacionais,
    participacao,
    perfil_da_administradora,
    recortar,
    resumir,
)
from app.domain.modelos import RegistroUF

MOTOS = 4
YAMAHA = "47458153"
SICREDI = "07808907"
SUDESTE_SUL = ["SP", "MG", "PR"]


def uf_(
    cnpj: str,
    uf: str,
    ativos: int,
    adesoes: int = 0,
    segmento: int = MOTOS,
) -> RegistroUF:
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
        assert calcular_share(25, 100) == 25.0

    def test_total_zero_nao_divide_por_zero(self):
        assert calcular_share(0, 0) == 0.0


class TestRecorte:
    def test_filtra_segmento_e_ufs(self):
        registros = [
            uf_("1", "PI", 10),
            uf_("1", "MA", 20),
            uf_("1", "SP", 30),
            uf_("1", "PI", 5, segmento=3),
        ]
        assert [r.uf for r in recortar(registros, MOTOS, ["PI", "MA"])] == ["PI", "MA"]

    def test_sem_uf_e_o_brasil_inteiro(self):
        registros = [uf_("1", "PI", 10), uf_("1", "SP", 30)]
        assert len(recortar(registros, MOTOS, [])) == 2

    def test_share_e_sobre_o_recorte_e_nao_sobre_o_pais(self):
        registros = [
            uf_("A", "PI", 60, adesoes=9),
            uf_("B", "PI", 40, adesoes=1),
            uf_("B", "SP", 900),
        ]
        p = participacao(recortar(registros, MOTOS, ["PI"]), "A")
        assert (p.share_carteira, p.share_adesoes) == (60.0, 90.0)
        assert p.variacao == pytest.approx(30.0)


@pytest.fixture(scope="module")
def recorte(registros_uf):
    return recortar(registros_uf, MOTOS, SUDESTE_SUL)


class TestRecorteReal:
    """Os números do exemplo preenchido do template, calculados da fixture."""

    def test_bloco_das_ufs(self, recorte):
        r = resumir(recorte)
        assert r.ativos == 722_444
        assert r.adesoes == 70_535
        assert r.contemplados == 33_651
        assert r.percentual_lance == pytest.approx(72.4, abs=0.05)
        assert r.taxa_exclusao == pytest.approx(49.0, abs=0.05)
        assert r.administradoras == 67

    @pytest.mark.parametrize(
        ("cnpj", "carteira", "adesoes", "quantas"),
        [(CNPJ_HONDA, 55.9, 64.7, 45_619), (YAMAHA, 3.4, 3.6, 2_562), (SICREDI, 2.3, 1.5, 1_075)],
    )
    def test_share_nas_ufs(self, recorte, cnpj, carteira, adesoes, quantas):
        p = participacao(recorte, cnpj)
        assert p.share_carteira == pytest.approx(carteira, abs=0.05)
        assert p.share_adesoes == pytest.approx(adesoes, abs=0.05)
        assert p.adesoes == quantas

    @pytest.mark.parametrize(("uf", "share"), [("PI", 95.7), ("MA", 91.5)])
    def test_referencia_das_pracas_da_sol_nascente(self, registros_uf, uf, share):
        p = participacao(recortar(registros_uf, MOTOS, [uf]), CNPJ_HONDA)
        assert p.share_carteira == pytest.approx(share, abs=0.05)


class TestIndicadoresNacionais:
    def test_honda(self, registros_consolidado):
        n = indicadores_nacionais(registros_consolidado, MOTOS, CNPJ_HONDA)
        assert n is not None
        assert n.data_base == "202607"
        assert n.taxa_administracao == pytest.approx(23.2, abs=0.05)
        assert n.inadimplencia == pytest.approx(10.6, abs=0.05)
        assert n.contemplacao_mes == pytest.approx(4.3, abs=0.05)  # sobre as não contempladas
        assert n.vendas_mes == 105_315
        assert n.credito_pendente == 142_436

    def test_administradora_ausente(self, registros_consolidado):
        assert indicadores_nacionais(registros_consolidado, MOTOS, "99999999") is None


class TestEscolhaDasAdministradoras:
    REGISTROS = [
        uf_("ALVO", "PI", 10, adesoes=5),
        uf_(CNPJ_HONDA, "PI", 80, adesoes=50),
        uf_("C1", "PI", 1, adesoes=40),
        uf_("C2", "PI", 90, adesoes=30),
        uf_("C3", "PI", 5, adesoes=20),
        uf_("C4", "PI", 5, adesoes=10),
    ]

    def test_concorrentes_por_adesoes_no_recorte(self):
        assert escolher_administradoras(self.REGISTROS, CNPJ_HONDA, 2) == (CNPJ_HONDA, "C1", "C2")

    def test_honda_sempre_aparece_como_referencia(self):
        assert escolher_administradoras(self.REGISTROS, "ALVO", 1) == ("ALVO", CNPJ_HONDA, "C1")

    def test_no_maximo_quatro_administradoras(self):
        assert escolher_administradoras(self.REGISTROS, "ALVO", 3) == (
            "ALVO",
            CNPJ_HONDA,
            "C1",
            "C2",
        )

    def test_sem_concorrentes(self):
        assert escolher_administradoras(self.REGISTROS, CNPJ_HONDA, 0) == (CNPJ_HONDA,)


class TestAlertas:
    def test_exemplo_do_template(self, registros_uf, registros_consolidado):
        """Honda ganha em MG e PR, Sicredi perde no PR, Yamaha com inadimplência alta."""
        recorte = recortar(registros_uf, MOTOS, SUDESTE_SUL)
        perfis = [
            perfil_da_administradora(recorte, registros_consolidado, MOTOS, SUDESTE_SUL, cnpj)
            for cnpj in (CNPJ_HONDA, YAMAHA, SICREDI)
        ]
        alertas = detectar_alertas(perfis)

        assert [(a.tipo, a.nome_administradora) for a in alertas] == [
            ("ganho", "ADM CONS NAC HONDA LTDA"),
            ("perda", "ADM CONS SICREDI LTDA"),
            ("inadimplencia", "YAMAHA ADM CONS LTDA"),
        ]
        assert [m.uf for m in alertas[0].movimentos] == ["MG", "PR"]
        assert alertas[1].movimentos[0].antes == pytest.approx(10.2, abs=0.05)
        assert alertas[1].movimentos[0].depois == pytest.approx(6.0, abs=0.05)
        assert alertas[2].inadimplencia == pytest.approx(18.5, abs=0.05)

    def test_variacao_pequena_nao_alerta(self):
        """SP da Honda no exemplo: +4,1 p.p. sobre 49,9% é oscilação, não movimento."""
        honda = PerfilAdministradora(
            cnpj_raiz=CNPJ_HONDA,
            nome_administradora="Honda",
            recorte=participacao([uf_(CNPJ_HONDA, "SP", 1)], CNPJ_HONDA),
            por_uf=(ParticipacaoNaUF("SP", 49.9, 54.0),),
            nacional=None,
        )
        assert detectar_alertas([honda]) == ()

    def test_sem_uf_compara_o_brasil(self):
        a = PerfilAdministradora(
            cnpj_raiz="A",
            nome_administradora="A",
            recorte=participacao(
                [uf_("A", "PI", 20, adesoes=1), uf_("B", "PI", 80, adesoes=9)], "A"
            ),
            por_uf=(),
            nacional=None,
        )
        assert detectar_alertas([a]) == (
            Alerta(
                tipo="perda",
                nome_administradora="A",
                movimentos=(Movimento(uf=None, antes=20.0, depois=10.0),),
            ),
        )
