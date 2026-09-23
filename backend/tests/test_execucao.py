"""Ciclo de vida de uma execução — ADR-004.

Regras puras: estados, chave de idempotência e decisão diante de uma
execução anterior com os mesmos parâmetros.
"""

import pytest

from app.domain.erros import TransicaoInvalida
from app.domain.execucao import (
    Decisao,
    ParametrosConsulta,
    StatusExecucao,
    chave_idempotencia,
    decidir,
    validar_transicao,
)
from app.domain.periodos import data_base_uf_para

S = StatusExecucao


def params(**kw) -> ParametrosConsulta:
    base = dict(
        data_base="202607",
        segmento=4,
        ufs=("PI", "MA"),
        cnpj_administradora="45441789",
        top_concorrentes=3,
        destinatario="5586999990000",
    )
    return ParametrosConsulta(**{**base, **kw})


class TestNormalizacao:
    def test_ufs_em_maiusculas_ordenadas_e_sem_repeticao(self):
        assert params(ufs=("ma", "PI", "pi")).ufs == ("MA", "PI")

    def test_destinatario_so_com_digitos(self):
        assert params(destinatario="+55 (86) 99999-0000").destinatario == "5586999990000"

    def test_cnpj_com_zeros_a_esquerda(self):
        assert params(cnpj_administradora="776").cnpj_administradora == "00000776"


class TestChaveDeIdempotencia:
    def test_mesmos_parametros_mesma_chave(self):
        assert chave_idempotencia(params()) == chave_idempotencia(params())

    def test_ordem_das_ufs_nao_importa(self):
        """ADR-004: [PI, MA] e [MA, PI] são a mesma consulta."""
        assert chave_idempotencia(params(ufs=("PI", "MA"))) == chave_idempotencia(
            params(ufs=("MA", "PI"))
        )

    def test_formatacao_do_telefone_nao_importa(self):
        assert chave_idempotencia(params(destinatario="+55 86 99999-0000")) == chave_idempotencia(
            params(destinatario="5586999990000")
        )

    @pytest.mark.parametrize(
        "diferente",
        [
            {"data_base": "202606"},
            {"segmento": 3},
            {"ufs": ("PI",)},
            {"cnpj_administradora": "00000776"},
            {"top_concorrentes": 5},
            {"destinatario": "5586888880000"},
        ],
    )
    def test_qualquer_parametro_diferente_muda_a_chave(self, diferente):
        """O destinatário entra na chave: mesmo relatório para outra pessoa não é duplicata."""
        assert chave_idempotencia(params(**diferente)) != chave_idempotencia(params())

    def test_formato_sha256(self):
        chave = chave_idempotencia(params())
        assert len(chave) == 64 and all(c in "0123456789abcdef" for c in chave)


class TestVersaoDaChave:
    def test_pedido_anterior_ao_template_atual_nao_e_reaproveitado(self):
        """Mesmos parâmetros, mensagem diferente: a execução antiga não serve mais."""
        import hashlib
        import json

        p = params()
        chave_v1 = hashlib.sha256(
            json.dumps({"v": 1, **p.como_dict()}, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        assert chave_idempotencia(p) != chave_v1


class TestTransicoes:
    @pytest.mark.parametrize(
        ("de", "para"),
        [
            (S.PENDENTE, S.COLETANDO),
            (S.COLETANDO, S.PROCESSANDO),
            (S.COLETANDO, S.FALHA_COLETA),
            (S.PROCESSANDO, S.MENSAGEM_GERADA),
            (S.PROCESSANDO, S.SEM_RESULTADO),
            (S.PROCESSANDO, S.FALHA_PROCESSAMENTO),
            (S.MENSAGEM_GERADA, S.ENVIANDO),
            (S.ENVIANDO, S.ENVIADO),
            (S.ENVIANDO, S.FALHA_ENVIO),
            (S.FALHA_COLETA, S.PENDENTE),
            (S.FALHA_PROCESSAMENTO, S.PENDENTE),
            (S.FALHA_ENVIO, S.PENDENTE),
        ],
    )
    def test_transicoes_validas(self, de, para):
        validar_transicao(de, para)

    @pytest.mark.parametrize(
        ("de", "para"),
        [
            (S.PENDENTE, S.ENVIADO),
            (S.COLETANDO, S.ENVIANDO),
            (S.ENVIADO, S.PENDENTE),
            (S.SEM_RESULTADO, S.PENDENTE),
            (S.MENSAGEM_GERADA, S.ENVIADO),
        ],
    )
    def test_transicoes_invalidas(self, de, para):
        """Enviar sem passar pela coleta, ou reabrir o que já foi enviado, é bug."""
        with pytest.raises(TransicaoInvalida):
            validar_transicao(de, para)


class TestDecisaoDiantedeExecucaoAnterior:
    def test_sem_anterior_cria(self):
        assert decidir(None) is Decisao.CRIAR

    @pytest.mark.parametrize("status", [S.ENVIADO, S.SEM_RESULTADO])
    def test_concluida_nao_repete(self, status):
        """ADR-004: o mesmo relatório não é reenviado."""
        assert decidir(status) is Decisao.REUSAR

    @pytest.mark.parametrize(
        "status", [S.PENDENTE, S.COLETANDO, S.PROCESSANDO, S.MENSAGEM_GERADA, S.ENVIANDO]
    )
    def test_em_andamento_nao_duplica(self, status):
        """Dois cliques seguidos não disparam duas coletas."""
        assert decidir(status) is Decisao.REUSAR

    @pytest.mark.parametrize("status", [S.FALHA_COLETA, S.FALHA_PROCESSAMENTO, S.FALHA_ENVIO])
    def test_falha_pode_ser_retentada(self, status):
        assert decidir(status) is Decisao.RETENTAR


class TestDataBaseDoRecortePorUF:
    """Consolidado é mensal e UF é trimestral: vale o trimestre mais recente até a data."""

    DISPONIVEIS = ["202606", "202603", "202512"]

    @pytest.mark.parametrize(
        ("escolhida", "esperada"),
        [("202607", "202606"), ("202606", "202606"), ("202605", "202603"), ("202601", "202512")],
    )
    def test_trimestre_mais_recente_ate_a_data(self, escolhida, esperada):
        assert data_base_uf_para(escolhida, self.DISPONIVEIS) == esperada

    def test_anterior_a_todos_os_trimestres(self):
        assert data_base_uf_para("202011", self.DISPONIVEIS) is None

    def test_ordem_da_lista_nao_importa(self):
        assert data_base_uf_para("202605", ["202512", "202606", "202603"]) == "202603"
