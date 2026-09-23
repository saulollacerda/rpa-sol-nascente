"""Envio por WhatsApp — ADR-009.

O adapter real é testado sem rede: o MockTransport do httpx responde como o
WAHA responderia.
"""

import json

import httpx
import pytest

from app.domain.erros import EnvioError
from app.infra.whatsapp import FakeSender, WahaSender

DESTINO = "5586999990000"
CHAT_ID = "558699990000@c.us"  # WhatsApp antigo, sem o 9º dígito
API_KEY = "chave-secreta-que-nao-pode-vazar"
WAHA_URL = "http://waha:3000"


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
        """Para demonstrar o caminho de erro sem depender do WAHA."""
        with pytest.raises(EnvioError, match="simulada"):
            FakeSender(falhar_com="falha simulada").enviar(DESTINO, "olá")


def sender_com(responder, api_key: str | None = API_KEY) -> tuple[WahaSender, list[httpx.Request]]:
    recebidas: list[httpx.Request] = []

    def transporte(request: httpx.Request) -> httpx.Response:
        recebidas.append(request)
        return responder(request)

    cliente = httpx.Client(transport=httpx.MockTransport(transporte))
    sender = WahaSender(url=WAHA_URL, api_key=api_key, sessao="default", cliente=cliente)
    return sender, recebidas


def waha(envio: httpx.Response | None = None, existe: bool = True):
    """Responde ao check-exists e ao sendText como o WAHA."""

    def responder(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/contacts/check-exists":
            return httpx.Response(200, json={"numberExists": existe, "chatId": CHAT_ID})
        return envio or httpx.Response(201, json={"id": "true_558699990000@c.us_3EB0ABC"})

    return responder


class TestWahaSender:
    def test_devolve_o_id_da_mensagem(self):
        sender, _ = sender_com(waha())
        assert sender.enviar(DESTINO, "📊 RADAR").id_mensagem == "true_558699990000@c.us_3EB0ABC"

    def test_consulta_o_numero_antes_de_enviar(self):
        sender, recebidas = sender_com(waha())
        sender.enviar(DESTINO, "olá")

        consulta, _ = recebidas
        assert consulta.method == "GET"
        assert consulta.url.path == "/api/contacts/check-exists"
        assert consulta.url.params["phone"] == DESTINO
        assert consulta.url.params["session"] == "default"

    def test_envia_para_o_chat_id_que_o_waha_devolveu(self):
        """Números brasileiros antigos existem sem o 9º dígito — quem sabe é o WhatsApp."""
        sender, recebidas = sender_com(waha())
        sender.enviar(DESTINO, "📊 RADAR\nlinha 2")

        _, envio = recebidas
        assert envio.method == "POST"
        assert str(envio.url) == f"{WAHA_URL}/api/sendText"
        assert json.loads(envio.content) == {
            "session": "default",
            "chatId": CHAT_ID,
            "text": "📊 RADAR\nlinha 2",
        }

    def test_manda_a_api_key_quando_configurada(self):
        sender, recebidas = sender_com(waha())
        sender.enviar(DESTINO, "olá")
        assert all(r.headers["X-Api-Key"] == API_KEY for r in recebidas)

    def test_sem_api_key_nao_manda_o_header(self):
        sender, recebidas = sender_com(waha(), api_key=None)
        sender.enviar(DESTINO, "olá")
        assert all("X-Api-Key" not in r.headers for r in recebidas)

    @pytest.mark.parametrize(
        "corpo",
        [
            {"id": "id-texto"},
            {"id": {"fromMe": True, "_serialized": "id-texto"}},
            {"key": {"id": "id-texto"}},
        ],
        ids=["string", "serialized", "key"],
    )
    def test_formatos_de_id_das_engines(self, corpo):
        sender, _ = sender_com(waha(httpx.Response(201, json=corpo)))
        assert sender.enviar(DESTINO, "olá").id_mensagem == "id-texto"

    def test_resposta_sem_id_de_mensagem(self):
        sender, _ = sender_com(waha(httpx.Response(201, json={"inesperado": True})))
        with pytest.raises(EnvioError, match="id"):
            sender.enviar(DESTINO, "olá")

    def test_numero_sem_whatsapp_nem_chega_a_enviar(self):
        sender, recebidas = sender_com(waha(existe=False))
        with pytest.raises(EnvioError, match="não tem WhatsApp"):
            sender.enviar(DESTINO, "olá")
        assert len(recebidas) == 1

    @pytest.mark.parametrize(
        ("status", "trecho"),
        [
            (401, "API key"),
            (404, "QR code"),
            (422, "QR code"),
            (500, "HTTP 500"),
        ],
    )
    def test_erros_do_waha_viram_envio_error_explicado(self, status, trecho):
        sender, _ = sender_com(lambda r: httpx.Response(status, json={"key": API_KEY}))
        with pytest.raises(EnvioError, match=trecho):
            sender.enviar(DESTINO, "olá")

    def test_erro_nao_vaza_o_corpo_da_resposta(self):
        sender, _ = sender_com(lambda r: httpx.Response(400, text=f"detalhe com {API_KEY}"))
        with pytest.raises(EnvioError) as erro:
            sender.enviar(DESTINO, "olá")
        assert API_KEY not in str(erro.value)

    def test_waha_fora_do_ar(self):
        def cair(request):
            raise httpx.ConnectError("sem conexão", request=request)

        sender, _ = sender_com(cair)
        with pytest.raises(EnvioError, match="não está acessível"):
            sender.enviar(DESTINO, "olá")

    def test_falha_de_rede(self):
        def estourar(request):
            raise httpx.ReadTimeout("demorou", request=request)

        sender, _ = sender_com(estourar)
        with pytest.raises(EnvioError, match="rede"):
            sender.enviar(DESTINO, "olá")

    def test_api_key_nao_aparece_na_representacao(self):
        """Um log da configuração não pode imprimir a key."""
        sender, _ = sender_com(waha())
        assert API_KEY not in repr(sender)
