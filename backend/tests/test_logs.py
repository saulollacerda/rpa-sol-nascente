"""Logging estruturado — CLAUDE.md: execucao_id em toda linha, segredos mascarados."""

import json
import logging

from app.infra.logs import FormatadorJson, mascarar


def formatar(mensagem, *args, extra=None, exc_info=None):
    registro = logging.LogRecord("app.teste", logging.INFO, __file__, 1, mensagem, args, exc_info)
    for chave, valor in (extra or {}).items():
        setattr(registro, chave, valor)
    return json.loads(FormatadorJson().format(registro))


def test_linha_em_json_com_os_campos_basicos():
    linha = formatar("coletando data-base %s", "202607")
    assert linha["mensagem"] == "coletando data-base 202607"
    assert linha["nivel"] == "INFO"
    assert linha["logger"] == "app.teste"
    assert "momento" in linha


def test_inclui_o_execucao_id():
    assert formatar("x", extra={"execucao_id": 42})["execucao_id"] == 42


def test_sem_execucao_id_o_campo_nao_aparece():
    assert "execucao_id" not in formatar("x")


def test_excecao_vira_campo_proprio():
    try:
        raise ValueError("quebrou")
    except ValueError:
        import sys

        linha = formatar("falhou", exc_info=sys.exc_info())
    assert "ValueError: quebrou" in linha["excecao"]


def test_mascara_bearer_token():
    assert mascarar("Authorization: Bearer EAAGabc123") == "Authorization: Bearer ***"


def test_mascara_token_da_meta_solto():
    assert "EAAGabc123xyz" not in mascarar("token=EAAGabc123xyz no texto")


def test_mascara_dentro_da_linha_formatada():
    """O risco real não é imprimir o token de propósito — é um log.debug da config inteira."""
    linha = formatar("config: %s", "whatsapp_token='EAAGsegredo999'")
    assert "EAAGsegredo999" not in json.dumps(linha)


def test_texto_comum_fica_intacto():
    assert mascarar("EAAG não é token quando curto") == "EAAG não é token quando curto"
