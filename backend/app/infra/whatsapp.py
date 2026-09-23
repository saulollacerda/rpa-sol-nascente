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
from app.domain.portas import ResultadoEnvio, WhatsAppSender

logger = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 20

# Status do WAHA traduzidos para o que o gestor precisa fazer.
ERROS_CONHECIDOS = {
    401: "API key do WAHA inválida",
    404: "sessão do WAHA não está conectada; escaneie o QR code no painel do WAHA "
    "(http://localhost:3000)",
    422: "sessão do WAHA não está conectada; escaneie o QR code no painel do WAHA "
    "(http://localhost:3000)",
}


class FakeSender:
    """Registra em memória e no log, sem tocar a rede. Padrão da demonstração."""

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

    def _chamar(self, metodo: str, caminho: str, **kwargs: Any) -> dict[str, Any]:
        try:
            resposta = self._cliente.request(
                metodo, f"{self._url}{caminho}", headers=self._headers, **kwargs
            )
        except httpx.ConnectError as erro:
            raise EnvioError(
                f"WAHA não está acessível em {self._url}; "
                "suba com `docker compose --profile waha up`"
            ) from erro
        except httpx.HTTPError as erro:
            raise EnvioError(f"falha de rede ao chamar o WAHA: {type(erro).__name__}") from erro

        if resposta.is_error:
            # Sem o corpo da resposta, que pode conter credenciais (ADR-005).
            base = f"o WAHA recusou o envio (HTTP {resposta.status_code})"
            explicacao = ERROS_CONHECIDOS.get(resposta.status_code)
            raise EnvioError(f"{base}: {explicacao}" if explicacao else base)

        try:
            corpo = resposta.json()
        except ValueError as erro:
            raise EnvioError("o WAHA respondeu com um corpo que não é JSON") from erro
        return corpo if isinstance(corpo, dict) else {}


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


def criar_sender(settings: Settings) -> WhatsAppSender:
    if settings.whatsapp_provider is WhatsAppProvider.WAHA:
        return WahaSender(
            url=settings.waha_url,
            api_key=settings.waha_api_key,
            sessao=settings.waha_session,
        )
    return FakeSender()
