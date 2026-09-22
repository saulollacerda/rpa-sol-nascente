"""Envio por WhatsApp — ADR-003.

O adapter real é testado sem rede: o MockTransport do httpx responde como a
Graph API da Meta responderia.
"""

import json

import httpx
import pytest

from app.domain.erros import EnvioError
from app.infra.whatsapp import LIMITE_DE_CARACTERES, CloudApiSender, FakeSender

DESTINO = "5586999990000"
TOKEN = "EAAG-segredo-que-nao-pode-vazar"


class TestFakeSender:
    def test_registra_o_envio_sem_tocar_a_rede(self):
        sender = FakeSender()
        resultado = sender.enviar(DESTINO, "olá")
        assert sender.enviadas == [(DESTINO, "olá")]
        assert resultado.id_mensagem.startswith("fake-")

    def test_ids_distintos(self):
        sender = FakeSender()
        ids = {sender.enviar(DESTINO, "a").id_mensagem, sender.enviar(DESTINO, "b").id_mensagem}
        assert len(ids) == 2

    def test_simula_falha(self):
        """Para demonstrar o caminho de erro sem depender da Meta."""
        with pytest.raises(EnvioError, match="simulada"):
            FakeSender(falhar_com="falha simulada").enviar(DESTINO, "olá")


def sender_com(responder) -> tuple[CloudApiSender, list[httpx.Request]]:
    recebidas: list[httpx.Request] = []

    def transporte(request: httpx.Request) -> httpx.Response:
        recebidas.append(request)
        return responder(request)

    cliente = httpx.Client(transport=httpx.MockTransport(transporte))
    sender = CloudApiSender(
        token=TOKEN, phone_number_id="1234567890", versao_api="v23.0", cliente=cliente
    )
    return sender, recebidas


def ok(_request):
    return httpx.Response(200, json={"messages": [{"id": "wamid.ABC123"}]})


def erro_da_meta(status: int, codigo: int):
    def responder(_request):
        corpo = {"error": {"code": codigo, "message": f"detalhe com {TOKEN}"}}
        return httpx.Response(status, json=corpo)

    return responder


class TestCloudApiSender:
    def test_devolve_o_id_da_mensagem(self):
        sender, _ = sender_com(ok)
        assert sender.enviar(DESTINO, "📊 RADAR").id_mensagem == "wamid.ABC123"

    def test_monta_a_requisicao_da_graph_api(self):
        sender, recebidas = sender_com(ok)
        sender.enviar(DESTINO, "📊 RADAR\nlinha 2")

        [req] = recebidas
        assert req.method == "POST"
        assert str(req.url) == "https://graph.facebook.com/v23.0/1234567890/messages"
        assert req.headers["Authorization"] == f"Bearer {TOKEN}"
        corpo = json.loads(req.content)
        assert corpo["messaging_product"] == "whatsapp"
        assert corpo["to"] == DESTINO
        assert corpo["type"] == "text"
        assert corpo["text"]["body"] == "📊 RADAR\nlinha 2"

    def test_quebras_de_linha_sao_preservadas(self):
        """Motivo de usar texto e não template: template não aceita quebra de linha."""
        sender, recebidas = sender_com(ok)
        sender.enviar(DESTINO, "a\nb\nc")
        assert json.loads(recebidas[0].content)["text"]["body"].count("\n") == 2

    @pytest.mark.parametrize(
        ("status", "codigo", "trecho"),
        [
            (400, 131047, "24 horas"),
            (400, 131030, "números de teste"),
            (401, 190, "token"),
            (500, 1, "HTTP 500"),
        ],
    )
    def test_erros_da_meta_viram_envio_error_explicado(self, status, codigo, trecho):
        sender, _ = sender_com(erro_da_meta(status, codigo))
        with pytest.raises(EnvioError, match=trecho):
            sender.enviar(DESTINO, "olá")

    def test_erro_nao_vaza_o_corpo_da_resposta(self):
        """ADR-005: o corpo da Meta pode conter fragmentos de credencial."""
        sender, _ = sender_com(erro_da_meta(400, 131047))
        with pytest.raises(EnvioError) as erro:
            sender.enviar(DESTINO, "olá")
        assert TOKEN not in str(erro.value)

    def test_falha_de_rede(self):
        def cair(request):
            raise httpx.ConnectError("sem conexão", request=request)

        sender, _ = sender_com(cair)
        with pytest.raises(EnvioError, match="rede"):
            sender.enviar(DESTINO, "olá")

    def test_resposta_sem_id_de_mensagem(self):
        sender, _ = sender_com(lambda r: httpx.Response(200, json={"inesperado": True}))
        with pytest.raises(EnvioError, match="id"):
            sender.enviar(DESTINO, "olá")

    def test_resposta_de_erro_sem_json(self):
        sender, _ = sender_com(lambda r: httpx.Response(502, text="<html>bad gateway</html>"))
        with pytest.raises(EnvioError, match="HTTP 502"):
            sender.enviar(DESTINO, "olá")

    def test_mensagem_acima_do_limite_nem_chega_a_ser_enviada(self):
        sender, recebidas = sender_com(ok)
        with pytest.raises(EnvioError, match="caracteres"):
            sender.enviar(DESTINO, "x" * (LIMITE_DE_CARACTERES + 1))
        assert recebidas == []

    def test_token_nao_aparece_na_representacao(self):
        """Um log da configuração não pode imprimir o token."""
        sender, _ = sender_com(ok)
        assert TOKEN not in repr(sender)
