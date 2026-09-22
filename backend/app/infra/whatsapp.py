"""Adapters de envio por WhatsApp — ver ADR-003.

CloudApiSender envia mensagem de texto pela Graph API da Meta. Texto, e não
template: parâmetros de template não aceitam quebra de linha, e o relatório
tem várias. A contrapartida é a janela de 24 horas — o destinatário precisa
ter escrito para o número da empresa no último dia.
"""

import itertools
import logging

import httpx

from app.config import Settings, WhatsAppProvider
from app.domain.erros import EnvioError
from app.domain.portas import ResultadoEnvio, WhatsAppSender

logger = logging.getLogger(__name__)

LIMITE_DE_CARACTERES = 4096  # corpo de mensagem de texto na Cloud API
TIMEOUT_SEGUNDOS = 20

# Códigos da Meta traduzidos para o que o gestor precisa fazer.
ERROS_CONHECIDOS = {
    131047: "fora da janela de 24 horas: o destinatário precisa ter enviado uma mensagem "
    "ao número da empresa nas últimas 24 horas",
    131030: "destinatário fora da lista de números de teste cadastrados no app da Meta",
    190: "token de acesso inválido ou expirado",
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


class CloudApiSender:
    def __init__(
        self,
        token: str,
        phone_number_id: str,
        versao_api: str,
        cliente: httpx.Client | None = None,
    ) -> None:
        self._token = token
        self._url = f"https://graph.facebook.com/{versao_api}/{phone_number_id}/messages"
        self._cliente = cliente or httpx.Client(timeout=TIMEOUT_SEGUNDOS)

    def __repr__(self) -> str:
        return f"CloudApiSender(url={self._url!r}, token=***)"

    def enviar(self, destinatario: str, mensagem: str) -> ResultadoEnvio:
        if len(mensagem) > LIMITE_DE_CARACTERES:
            raise EnvioError(
                f"mensagem com {len(mensagem)} caracteres excede o limite de "
                f"{LIMITE_DE_CARACTERES} da Cloud API"
            )

        corpo = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": destinatario,
            "type": "text",
            "text": {"preview_url": False, "body": mensagem},
        }
        try:
            resposta = self._cliente.post(
                self._url, json=corpo, headers={"Authorization": f"Bearer {self._token}"}
            )
        except httpx.HTTPError as erro:
            raise EnvioError(
                f"falha de rede ao chamar a API do WhatsApp: {type(erro).__name__}"
            ) from erro

        if resposta.is_error:
            raise EnvioError(_explicar(resposta))

        try:
            return ResultadoEnvio(id_mensagem=resposta.json()["messages"][0]["id"])
        except (ValueError, KeyError, IndexError, TypeError) as erro:
            raise EnvioError("a API do WhatsApp respondeu sem o id da mensagem") from erro


def _explicar(resposta: httpx.Response) -> str:
    """Mensagem de erro sem o corpo da resposta, que pode conter credenciais (ADR-005)."""
    try:
        codigo = resposta.json()["error"]["code"]
    except (ValueError, KeyError, TypeError):
        codigo = None
    base = f"a API do WhatsApp recusou o envio (HTTP {resposta.status_code}"
    base += f", código {codigo})" if codigo is not None else ")"
    explicacao = ERROS_CONHECIDOS.get(codigo) if codigo is not None else None
    return f"{base}: {explicacao}" if explicacao else base


def criar_sender(settings: Settings) -> WhatsAppSender:
    if settings.whatsapp_provider is WhatsAppProvider.CLOUD_API:
        return CloudApiSender(
            token=settings.whatsapp_token or "",
            phone_number_id=settings.whatsapp_phone_number_id or "",
            versao_api=settings.whatsapp_api_version,
        )
    return FakeSender()
