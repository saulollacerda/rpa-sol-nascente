"""Configuração centralizada — ver ADR-005."""

from enum import StrEnum
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class WhatsAppProvider(StrEnum):
    CLOUD_API = "cloud_api"
    FAKE = "fake"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    whatsapp_provider: WhatsAppProvider = WhatsAppProvider.FAKE
    whatsapp_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_destinatario: str | None = None
    whatsapp_template_name: str = "radar_consorcio"

    bcb_base_url: str = "https://www.bcb.gov.br/estabilidadefinanceira/consorciobd"
    database_url: str = "sqlite:///./data/execucoes.db"
    data_dir: Path = Path("data")
    catalogo_ttl_horas: int = 6

    playwright_headless: bool = True
    log_level: str = "INFO"

    @model_validator(mode="after")
    def exige_token_para_cloud_api(self) -> "Settings":
        """ADR-005: falha na inicialização em vez de no meio da execução."""
        if self.whatsapp_provider is WhatsAppProvider.CLOUD_API and not self.whatsapp_token:
            raise ValueError("WHATSAPP_TOKEN é obrigatório quando WHATSAPP_PROVIDER=cloud_api")
        return self
