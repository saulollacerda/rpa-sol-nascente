"""Configuração centralizada — ver ADR-005."""

from enum import StrEnum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WhatsAppProvider(StrEnum):
    WAHA = "waha"
    FAKE = "fake"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    whatsapp_provider: WhatsAppProvider = WhatsAppProvider.WAHA
    whatsapp_destinatario: str | None = None

    # WAHA — ver ADR-009. A key é opcional: depende de como o container subiu.
    waha_url: str = "http://localhost:3000"
    waha_api_key: str | None = None
    waha_session: str = "default"

    bcb_base_url: str = "https://www.bcb.gov.br/estabilidadefinanceira/consorciobd"
    database_url: str = "sqlite:///./data/execucoes.db"
    data_dir: Path = Path("data")
    catalogo_ttl_horas: int = 6
    # Retentativa da coleta quando o BCB está fora do ar ou lento: esperas de 5 s e 15 s.
    coleta_tentativas: int = Field(default=3, ge=1)
    coleta_espera_inicial_segundos: float = Field(default=5, ge=0)

    playwright_headless: bool = True
    log_level: str = "INFO"
