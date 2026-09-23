"""Adapters de envio por WhatsApp — ver ADR-009.

WahaSender envia pelo WAHA (WhatsApp HTTP API), que conecta um número comum
por QR code. Não é oficial: serve à demonstração, não à produção. O caminho
de produção está descrito no ADR-009.
"""

import itertools
import logging
from typing import Any

import httpx

from app.config import Settings, WhatsAppProvider
from app.domain.erros import EnvioError
from app.domain.portas import EstadoConexao, ResultadoEnvio, SituacaoConexao

logger = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 20

# Status do WAHA traduzidos para o que o gestor precisa fazer.
ERROS_CONHECIDOS = {
    401: "API key do WAHA inválida: a WAHA_API_KEY do backend/.env não é a do container; "
    "rode `docker compose up -d --force-recreate waha backend`",
    404: "sessão do WAHA não está conectada; escaneie o QR code no painel do WAHA "
    "(http://localhost:3000)",
    422: "sessão do WAHA não está conectada; escaneie o QR code no painel do WAHA "
    "(http://localhost:3000)",
}


# Sem key, o WAHA gera uma aleatória ao subir, e o backend não tem como conhecê-la.
SEM_API_KEY = (
    "o backend está sem WAHA_API_KEY; preencha no backend/.env e rode "
    "`docker compose up -d --force-recreate waha backend`"
)


class FakeSender:
    """Registra em memória e no log, sem tocar a rede. Para testes e para ensaiar sem celular."""

    def __init__(self, falhar_com: str | None = None) -> None:
        self.enviadas: list[tuple[str, str]] = []
        self._falhar_com = falhar_com
        self._sequencia = itertools.count(1)

    def enviar(self, destinatario: str, mensagem: str) -> ResultadoEnvio:
        if self._falhar_com:
            raise EnvioError(self._falhar_com)
        self.enviadas.append((destinatario, mensagem))
        id_mensagem = f"fake-{next(self._sequencia)}"
        logger.info("envio simulado %s para %s", id_mensagem, destinatario)
        return ResultadoEnvio(id_mensagem=id_mensagem)

    def estado(self) -> EstadoConexao:
        return EstadoConexao(SituacaoConexao.CONECTADO, conta="envio simulado")

    def reconectar(self) -> None:
        pass


class WahaSender:
    def __init__(
        self,
        url: str,
        api_key: str | None,
        sessao: str,
        cliente: httpx.Client | None = None,
    ) -> None:
        self._url = url.rstrip("/")
        self._sessao = sessao
        self._headers = {"X-Api-Key": api_key} if api_key else {}
        self._cliente = cliente or httpx.Client(timeout=TIMEOUT_SEGUNDOS)

    def __repr__(self) -> str:
        return f"WahaSender(url={self._url!r}, sessao={self._sessao!r}, api_key=***)"

    def enviar(self, destinatario: str, mensagem: str) -> ResultadoEnvio:
        chat_id = self._resolver_chat_id(destinatario)
        corpo = {"session": self._sessao, "chatId": chat_id, "text": mensagem}
        resposta = self._chamar("POST", "/api/sendText", json=corpo)
        id_mensagem = _extrair_id(resposta)
        if not id_mensagem:
            raise EnvioError("o WAHA respondeu sem o id da mensagem")
        return ResultadoEnvio(id_mensagem=id_mensagem)

    def estado(self) -> EstadoConexao:
        try:
            sessao = self._chamar("GET", f"/api/sessions/{self._sessao}")
        except SessaoInexistente:
            return EstadoConexao(SituacaoConexao.DESCONECTADO)

        status = sessao.get("status")
        if status == "WORKING":
            return EstadoConexao(SituacaoConexao.CONECTADO, conta=_descrever_conta(sessao))
        if status == "SCAN_QR_CODE":
            qr_code = self._qr_code()
            if qr_code is None:
                return EstadoConexao(SituacaoConexao.INICIANDO)
            return EstadoConexao(SituacaoConexao.AGUARDANDO_QR, qr_code=qr_code)
        if status == "STARTING":
            return EstadoConexao(SituacaoConexao.INICIANDO)
        # FAILED: o QR code venceu sem ser lido, ou o celular desconectou.
        return EstadoConexao(SituacaoConexao.DESCONECTADO)

    def reconectar(self) -> None:
        try:
            self._chamar("POST", f"/api/sessions/{self._sessao}/restart")
        except SessaoInexistente:
            self._chamar("POST", "/api/sessions", json={"name": self._sessao, "start": True})

    def _qr_code(self) -> str | None:
        """None quando a sessão saiu de SCAN_QR_CODE entre as duas chamadas."""
        try:
            qr = self._chamar(
                "GET",
                f"/api/{self._sessao}/auth/qr",
                params={"format": "image"},
                headers={"Accept": "application/json"},
            )
        except EnvioError:
            return None
        if not qr.get("data"):
            return None
        return f"data:{qr.get('mimetype', 'image/png')};base64,{qr['data']}"

    def _resolver_chat_id(self, destinatario: str) -> str:
        """O WhatsApp sabe se o número existe com ou sem o 9º dígito; nós não."""
        resposta = self._chamar(
            "GET",
            "/api/contacts/check-exists",
            params={"phone": destinatario, "session": self._sessao},
        )
        if not resposta.get("numberExists") or not resposta.get("chatId"):
            raise EnvioError(f"o número {destinatario} não tem WhatsApp")
        return str(resposta["chatId"])

    def _chamar(
        self,
        metodo: str,
        caminho: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            resposta = self._cliente.request(
                metodo,
                f"{self._url}{caminho}",
                headers={**self._headers, **(headers or {})},
                **kwargs,
            )
        except httpx.ConnectError as erro:
            raise EnvioError(
                f"WAHA não está acessível em {self._url}; "
                "confira se o container subiu com `docker compose up`"
            ) from erro
        except httpx.HTTPError as erro:
            raise EnvioError(f"falha de rede ao chamar o WAHA: {type(erro).__name__}") from erro

        if resposta.status_code == 404 and caminho.startswith("/api/sessions/"):
            raise SessaoInexistente(f"a sessão {self._sessao} não existe no WAHA")
        if resposta.is_error:
            # Sem o corpo da resposta, que pode conter credenciais (ADR-005).
            base = f"o WAHA recusou o envio (HTTP {resposta.status_code})"
            explicacao = ERROS_CONHECIDOS.get(resposta.status_code)
            if resposta.status_code == 401 and not self._headers:
                explicacao = SEM_API_KEY
            raise EnvioError(f"{base}: {explicacao}" if explicacao else base)

        try:
            corpo = resposta.json()
        except ValueError as erro:
            raise EnvioError("o WAHA respondeu com um corpo que não é JSON") from erro
        return corpo if isinstance(corpo, dict) else {}


class SessaoInexistente(EnvioError):
    pass


def _descrever_conta(sessao: dict[str, Any]) -> str | None:
    me = sessao.get("me")
    if not isinstance(me, dict):
        return None
    numero = str(me.get("id", "")).split("@")[0] or None
    nome = me.get("pushName")
    if nome and numero:
        return f"{nome} ({numero})"
    return nome or numero


def _extrair_id(resposta: dict[str, Any]) -> str | None:
    """O formato do id muda conforme a engine do WAHA (WEBJS, NOWEB, GOWS)."""
    id_ = resposta.get("id")
    if isinstance(id_, str):
        return id_
    if isinstance(id_, dict) and isinstance(id_.get("_serialized"), str):
        return id_["_serialized"]
    chave = resposta.get("key")
    if isinstance(chave, dict) and isinstance(chave.get("id"), str):
        return chave["id"]
    return None


def criar_sender(settings: Settings) -> WahaSender | FakeSender:
    """Os dois adapters implementam WhatsAppSender e ConexaoWhatsApp."""
    if settings.whatsapp_provider is WhatsAppProvider.WAHA:
        return WahaSender(
            url=settings.waha_url,
            api_key=settings.waha_api_key,
            sessao=settings.waha_session,
        )
    return FakeSender()
