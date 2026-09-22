"""Montagem do relatório e composição da mensagem — PRD, seções 6 e 7."""

from datetime import datetime

import pytest

from app.domain.mensagem import compor_mensagem
from app.domain.relatorio import montar_relatorio

HONDA = "45441789"
MOTOS = 4
GERADO_EM = datetime(2026, 9, 22, 15, 12)


@pytest.fixture(scope="module")
def relatorio(registros_consolidado, registros_uf):
    return montar_relatorio(registros_consolidado, registros_uf, MOTOS, ["PI", "MA"], HONDA)


@pytest.fixture(scope="module")
def mensagem(relatorio):
    return compor_mensagem(relatorio, GERADO_EM)


class TestMontagem:
    def test_uma_praca_por_uf_na_ordem_pedida(self, relatorio):
        assert [p.uf for p in relatorio.pracas] == ["PI", "MA"]

    def test_contemplados_somados_entre_pracas(self, relatorio):
        assert relatorio.contemplados_no_trimestre == 10_305 + 13_402

    def test_inclui_o_contexto_nacional(self, relatorio):
        assert relatorio.nacional.cotas_ativas == 2_565_256

    def test_tem_resultado(self, relatorio):
        assert relatorio.tem_resultado

    def test_uf_onde_a_administradora_nao_opera(self, registros_consolidado, registros_uf):
        """A UF entra na lista de ausências em vez de derrubar o relatório."""
        rel = montar_relatorio(registros_consolidado, registros_uf, MOTOS, ["PI", "XX"], HONDA)
        assert [p.uf for p in rel.pracas] == ["PI"]
        assert rel.ufs_sem_resultado == ("XX",)

    def test_sem_arquivo_de_uf(self, registros_consolidado):
        """PRD §7: mês não trimestral — emite só o bloco nacional e avisa."""
        rel = montar_relatorio(registros_consolidado, None, MOTOS, ["PI"], HONDA)
        assert rel.pracas == ()
        assert rel.recorte_uf_indisponivel
        assert rel.tem_resultado

    def test_administradora_inexistente_nao_tem_resultado(
        self, registros_consolidado, registros_uf
    ):
        """Desfecho SEM_RESULTADO: não há o que enviar."""
        rel = montar_relatorio(registros_consolidado, registros_uf, MOTOS, ["PI"], "99999999")
        assert not rel.tem_resultado


class TestMensagem:
    def test_cabecalho_informa_segmento(self, mensagem):
        assert "RADAR DE CONSÓRCIO" in mensagem
        assert "motocicletas e motonetas" in mensagem

    def test_informa_a_data_base_de_cada_bloco(self, mensagem):
        """Consolidado e UF têm periodicidades diferentes — não assumir uma só."""
        assert "Junho/2026" in mensagem
        assert "Julho/2026" in mensagem

    @pytest.mark.parametrize(
        "trecho",
        ["PIAUÍ", "155.648", "148.962", "95,7%", "19.340", "10.305", "9.354", "951"],
    )
    def test_bloco_do_piaui(self, mensagem, trecho):
        assert trecho in mensagem

    @pytest.mark.parametrize("trecho", ["MARANHÃO", "249.533", "228.238", "91,5%", "13.402"])
    def test_bloco_do_maranhao(self, mensagem, trecho):
        assert trecho in mensagem

    def test_concorrencia_da_praca(self, mensagem):
        assert "BB CONSÓRCIOS 1,8%" in mensagem

    def test_oportunidade_soma_as_pracas(self, mensagem):
        assert "23.707" in mensagem
        assert "2 praças" in mensagem

    def test_contexto_nacional(self, mensagem):
        assert "77,3%" in mensagem
        assert "23,2%" in mensagem

    def test_rodape_com_fonte_e_horario(self, mensagem):
        assert "Banco Central do Brasil" in mensagem
        assert "22/09/2026 15:12" in mensagem

    def test_sem_tabelas_que_quebram_no_whatsapp(self, mensagem):
        assert "|" not in mensagem

    def test_uma_praca_so_usa_singular(self, registros_consolidado, registros_uf):
        rel = montar_relatorio(registros_consolidado, registros_uf, MOTOS, ["PI"], HONDA)
        texto = compor_mensagem(rel, GERADO_EM)
        assert "na praça" in texto
        assert "praças" not in texto.split("OPORTUNIDADE")[1]

    def test_avisa_quando_falta_o_recorte_por_uf(self, registros_consolidado):
        rel = montar_relatorio(registros_consolidado, None, MOTOS, ["PI"], HONDA)
        texto = compor_mensagem(rel, GERADO_EM)
        assert "recorte por UF" in texto
        assert "PIAUÍ" not in texto

    def test_avisa_uf_sem_atuacao(self, registros_consolidado, registros_uf):
        rel = montar_relatorio(registros_consolidado, registros_uf, MOTOS, ["PI", "XX"], HONDA)
        assert "sem atuação" in compor_mensagem(rel, GERADO_EM)

    def test_recusa_compor_sem_resultado(self, registros_consolidado, registros_uf):
        """Nunca enviar mensagem vazia: o chamador deve checar tem_resultado."""
        rel = montar_relatorio(registros_consolidado, registros_uf, MOTOS, ["PI"], "99999999")
        with pytest.raises(ValueError, match="sem resultado"):
            compor_mensagem(rel, GERADO_EM)
