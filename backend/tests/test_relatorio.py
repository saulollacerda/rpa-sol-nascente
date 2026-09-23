"""Montagem do relatório e composição da mensagem no template do WhatsApp.

O cenário SP, MG e PR reproduz o exemplo preenchido do template: os números
por UF vêm da fixture de Junho/2026; os nacionais (🇧🇷), da de Julho/2026.
"""

import pytest

from app.domain.analise import CNPJ_HONDA
from app.domain.mensagem import MAX_LINHAS, compor_mensagem
from app.domain.relatorio import montar_relatorio

MOTOS = 4
YAMAHA = "47458153"
SUDESTE_SUL = ["PR", "MG", "SP"]


@pytest.fixture(scope="module")
def relatorio(registros_consolidado, registros_uf):
    return montar_relatorio(registros_consolidado, registros_uf, MOTOS, SUDESTE_SUL, CNPJ_HONDA, 2)


@pytest.fixture(scope="module")
def linhas(relatorio):
    return compor_mensagem(relatorio).splitlines()


def montar(registros_consolidado, registros_uf, ufs, cnpj=CNPJ_HONDA, top=3):
    return montar_relatorio(registros_consolidado, registros_uf, MOTOS, ufs, cnpj, top)


class TestMontagem:
    def test_ufs_ordenadas_pelo_tamanho_do_mercado(self, relatorio):
        assert relatorio.ufs == ("SP", "MG", "PR")
        assert [p.uf for p in relatorio.posicoes_uf] == ["SP", "MG", "PR"]

    def test_escolhida_e_maiores_concorrentes_em_adesoes(self, relatorio):
        nomes = [a.nome_administradora for a in relatorio.administradoras]
        assert nomes == [
            "ADM CONS NAC HONDA LTDA",
            "SPERTA ADM CONSORCIO NAC LTDA",
            "YAMAHA ADM CONS LTDA",
        ]

    def test_honda_entra_mesmo_quando_a_escolhida_e_outra(
        self, registros_consolidado, registros_uf
    ):
        rel = montar(registros_consolidado, registros_uf, SUDESTE_SUL, YAMAHA, 1)
        assert [a.cnpj_raiz for a in rel.administradoras][:2] == [YAMAHA, CNPJ_HONDA]
        assert len(rel.administradoras) == 3

    def test_data_bases_de_cada_dataset(self, relatorio):
        assert (relatorio.data_base_uf, relatorio.data_base_nacional) == ("202606", "202607")

    def test_tem_resultado(self, relatorio):
        assert relatorio.tem_resultado

    def test_sem_uf_o_recorte_e_o_brasil(self, registros_consolidado, registros_uf):
        rel = montar(registros_consolidado, registros_uf, [])
        assert rel.posicoes_uf == ()
        assert rel.recorte.administradoras == 69  # no trimestral por UF; o mensal lista 125

    def test_sem_arquivo_de_uf(self, registros_consolidado):
        """Data-base anterior ao primeiro trimestral: só os dados nacionais."""
        rel = montar_relatorio(registros_consolidado, None, MOTOS, ["PI"], CNPJ_HONDA)
        assert rel.recorte is None
        assert [a.cnpj_raiz for a in rel.administradoras] == [CNPJ_HONDA]
        assert rel.tem_resultado

    def test_administradora_inexistente_nao_tem_resultado(
        self, registros_consolidado, registros_uf
    ):
        """Desfecho SEM_RESULTADO: não há o que enviar."""
        rel = montar(registros_consolidado, registros_uf, ["PI"], "99999999", 0)
        assert not rel.tem_resultado


class TestMensagem:
    def test_cabecalho(self, linhas):
        assert linhas[:4] == [
            "🏍️ *CONSÓRCIO MOTOS – SEGMENTO 4*",
            "📅 Jun/2026 | Fonte: BCB",
            "🔎 UFs: *SP, MG, PR*",
            "🏢 Adms: *Honda, Sperta, Yamaha*",
        ]

    def test_bloco_das_ufs_selecionadas(self, linhas):
        inicio = linhas.index("📍 *UFs SELECIONADAS: SP, MG, PR* _(2º trimestre/2026)_")
        assert linhas[inicio + 1 : inicio + 6] == [
            "- Consorciados ativos: *722.444*",
            "- Adesões: *70.535*",
            "- Contemplações: 33.651 (72,4% por lance)",
            "- Taxa de exclusão: 49,0%",
            "- Administradoras atuando: 67",
        ]

    def test_uma_linha_por_uf(self, linhas):
        assert "- *SP*: 317.669 ativos | 30.317 adesões | Honda 49,9% → 54,0%" in linhas
        assert "- *MG*: 298.149 ativos | 32.359 adesões | Honda 63,8% → 75,1%" in linhas
        assert "- *PR*: 106.626 ativos | 7.859 adesões | Honda 51,6% → 63,0%" in linhas

    def test_bloco_da_honda(self, linhas):
        inicio = linhas.index("*Honda*")
        assert linhas[inicio + 1 : inicio + 5] == [
            "  Nas UFs: share 55,9% carteira / 64,7% adesões (45.619 adesões)",
            "  SP 49,9% → 54,0% | MG 63,8% → 75,1% | PR 51,6% → 63,0%",
            "  🇧🇷 Taxa 23,2% | Inad. 10,6% | Contemp./mês 4,3%",
            "  🇧🇷 Vendas mês 105.315 | Crédito pendente 142.436",
        ]

    def test_alertas(self, linhas):
        inicio = linhas.index("⚠️ *ALERTAS*")
        assert (
            linhas[inicio + 1] == "- 📈 Honda ganhando share em MG (+11,3 p.p.) e PR (+11,4 p.p.)"
        )
        assert "- 🔴 Yamaha com inadimplência de 18,5%" in linhas[inicio:]

    def test_rodape_explica_a_bandeira(self, linhas):
        assert linhas[-1] == "_🇧🇷 = dado nacional de Jul/2026, o BCB não divulga por UF_"

    def test_perda_numa_uf_mostra_antes_e_depois(self, registros_consolidado, registros_uf):
        sicredi = "07808907"
        texto = compor_mensagem(
            montar(registros_consolidado, registros_uf, SUDESTE_SUL, sicredi, 0)
        )
        assert "- 📉 Sicredi perdendo share no PR (10,2% → 6,0%)" in texto

    def test_sem_uf_vira_brasil(self, registros_consolidado, registros_uf):
        texto = compor_mensagem(montar(registros_consolidado, registros_uf, [], top=1))
        assert "🔎 UFs: *Brasil*" in texto
        assert "📍 *BRASIL* _(2º trimestre/2026)_" in texto
        assert "  No Brasil: share " in texto
        assert "- *" not in texto.split("🏢 *ADMINISTRADORAS*")[0].split("_(2º trimestre/2026)_")[1]

    def test_uma_uf_usa_o_nome_do_estado(self, registros_consolidado, registros_uf):
        texto = compor_mensagem(montar(registros_consolidado, registros_uf, ["PI"]))
        assert "📍 *PIAUÍ* _(2º trimestre/2026)_" in texto
        assert "  No PI: share 95,7% carteira" in texto
        assert "- *PI*:" not in texto  # repetiria o bloco de cima

    def test_mais_de_5_ufs_mostra_extremos(self, registros_consolidado, registros_uf):
        ufs = ["PI", "MA", "CE", "BA", "PE", "PB", "RN", "AL"]
        texto = compor_mensagem(montar(registros_consolidado, registros_uf, ufs))
        assert sum(linha.startswith("- *") for linha in texto.splitlines()) == 6
        assert "- _+2 UFs no total_" in texto

    def test_detalhe_por_uf_so_com_ate_3_administradoras(self, registros_consolidado, registros_uf):
        texto = compor_mensagem(montar(registros_consolidado, registros_uf, ["PI", "MA"], top=3))
        assert "  PI " not in texto and "  MA " not in texto

    @pytest.mark.parametrize(
        "ufs", [["PI", "MA"], SUDESTE_SUL, [], ["PI", "MA", "CE", "BA", "PE", "PB"]]
    )
    def test_cabe_no_limite_de_linhas(self, registros_consolidado, registros_uf, ufs):
        texto = compor_mensagem(montar(registros_consolidado, registros_uf, ufs))
        assert len(texto.splitlines()) <= MAX_LINHAS

    def test_avisa_quando_falta_o_recorte_por_uf(self, registros_consolidado):
        rel = montar_relatorio(registros_consolidado, None, MOTOS, ["PI"], CNPJ_HONDA)
        texto = compor_mensagem(rel)
        assert "recorte por UF" in texto
        assert "📍" not in texto
        assert "🇧🇷 Taxa 23,2%" in texto

    def test_recusa_compor_sem_resultado(self, registros_consolidado, registros_uf):
        """Nunca enviar mensagem vazia: o chamador deve checar tem_resultado."""
        rel = montar(registros_consolidado, registros_uf, ["PI"], "99999999", 0)
        with pytest.raises(ValueError, match="sem resultado"):
            compor_mensagem(rel)
