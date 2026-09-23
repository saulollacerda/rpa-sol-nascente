"""Envio por WhatsApp — ADR-009.

O adapter real é testado sem rede: o MockTransport do httpx responde como o
WAHA responderia.
"""

import json

import httpx
import pytest

from app.domain.erros import EnvioError
from app.domain.portas import SituacaoConexao
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


# Respostas capturadas do WAHA 2026.9.1 (engine GOWS), com o número mascarado.
SESSAO_AGUARDANDO_QR = {"name": "default", "status": "SCAN_QR_CODE", "me": None}
SESSAO_CONECTADA = {
    "name": "default",
    "status": "WORKING",
    "me": {"id": "558699990000@c.us", "pushName": "Sol Nascente Demo"},
}
QR_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAASQAAAEk"


def waha_conexao(sessao: dict | None, qr_status: int = 200):
    """Responde às rotas de sessão e de QR code como o WAHA."""

    def responder(request: httpx.Request) -> httpx.Response:
        caminho = request.url.path
        if caminho == "/api/sessions/default":
            if sessao is None:
                return httpx.Response(404, json={"error": "Session not found"})
            return httpx.Response(200, json=sessao)
        if caminho == "/api/default/auth/qr":
            if qr_status != 200:
                return httpx.Response(qr_status, json={"error": "not in SCAN_QR_CODE"})
            return httpx.Response(200, json={"mimetype": "image/png", "data": QR_PNG_BASE64})
        if caminho == "/api/sessions/default/restart":
            return httpx.Response(201, json={**SESSAO_AGUARDANDO_QR, "status": "STARTING"})
        if caminho == "/api/sessions":
            return httpx.Response(201, json={**SESSAO_AGUARDANDO_QR, "status": "STARTING"})
        return httpx.Response(500)

    return responder


class TestConexaoWaha:
    def test_conectado_mostra_a_conta_e_nenhum_qr_code(self):
        sender, recebidas = sender_com(waha_conexao(SESSAO_CONECTADA))
        estado = sender.estado()
        assert estado.situacao is SituacaoConexao.CONECTADO
        assert estado.conta == "Sol Nascente Demo (558699990000)"
        assert estado.qr_code is None
        assert len(recebidas) == 1, "conectado não precisa buscar QR code"

    def test_aguardando_leitura_traz_o_qr_code_como_imagem(self):
        sender, _ = sender_com(waha_conexao(SESSAO_AGUARDANDO_QR))
        estado = sender.estado()
        assert estado.situacao is SituacaoConexao.AGUARDANDO_QR
        assert estado.qr_code == f"data:image/png;base64,{QR_PNG_BASE64}"

    def test_pede_o_qr_code_em_json(self):
        sender, recebidas = sender_com(waha_conexao(SESSAO_AGUARDANDO_QR))
        sender.estado()
        _, qr = recebidas
        assert qr.url.params["format"] == "image"
        assert qr.headers["Accept"] == "application/json"
        assert qr.headers["X-Api-Key"] == API_KEY

    def test_qr_code_some_entre_as_duas_chamadas(self):
        """A sessão conectou ou reiniciou entre ler o status e pedir o QR: não é erro."""
        sender, _ = sender_com(waha_conexao(SESSAO_AGUARDANDO_QR, qr_status=422))
        assert sender.estado().situacao is SituacaoConexao.INICIANDO

    def test_iniciando(self):
        sender, _ = sender_com(waha_conexao({**SESSAO_AGUARDANDO_QR, "status": "STARTING"}))
        estado = sender.estado()
        assert estado.situacao is SituacaoConexao.INICIANDO
        assert estado.qr_code is None

    @pytest.mark.parametrize("status", ["FAILED", "STOPPED"])
    def test_sessao_parada_fica_desconectada(self, status):
        """FAILED é o que o WAHA faz quando o QR code vence sem ser lido."""
        sender, _ = sender_com(waha_conexao({**SESSAO_AGUARDANDO_QR, "status": status}))
        assert sender.estado().situacao is SituacaoConexao.DESCONECTADO

    def test_sessao_inexistente_fica_desconectada(self):
        sender, _ = sender_com(waha_conexao(None))
        assert sender.estado().situacao is SituacaoConexao.DESCONECTADO

    def test_waha_fora_do_ar_levanta_envio_error(self):
        def cair(request):
            raise httpx.ConnectError("sem conexão", request=request)

        sender, _ = sender_com(cair)
        with pytest.raises(EnvioError, match="não está acessível"):
            sender.estado()

    def test_reconectar_reinicia_a_sessao(self):
        sender, recebidas = sender_com(waha_conexao(SESSAO_AGUARDANDO_QR))
        sender.reconectar()
        [req] = recebidas
        assert req.method == "POST"
        assert req.url.path == "/api/sessions/default/restart"

    def test_reconectar_cria_a_sessao_que_nao_existe(self):
        def responder(request):
            if request.url.path == "/api/sessions/default/restart":
                return httpx.Response(404, json={"error": "Session not found"})
            return waha_conexao(None)(request)

        sender, recebidas = sender_com(responder)
        sender.reconectar()
        _, criar = recebidas
        assert criar.method == "POST"
        assert criar.url.path == "/api/sessions"
        assert json.loads(criar.content) == {"name": "default", "start": True}


class TestConexaoFake:
    def test_fake_se_declara_conectado(self):
        estado = FakeSender().estado()
        assert estado.situacao is SituacaoConexao.CONECTADO
        assert "simulado" in (estado.conta or "")

    def test_reconectar_no_fake_nao_faz_nada(self):
        FakeSender().reconectar()
