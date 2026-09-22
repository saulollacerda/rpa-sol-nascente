"""Configuração — regras definidas no ADR-005."""

import pytest
from pydantic import ValidationError

from app.config import Settings, WhatsAppProvider


def test_usa_adapter_fake_por_padrao():
    """A demonstração não pode depender de credencial da Meta."""
    assert Settings().whatsapp_provider is WhatsAppProvider.FAKE


def test_adapter_fake_nao_exige_token():
    settings = Settings(whatsapp_provider="fake")
    assert settings.whatsapp_token is None


def test_cloud_api_sem_token_falha_na_inicializacao():
    """ADR-005: falhar cedo vale mais que descobrir a credencial faltando
    no meio da execução, depois de já ter baixado os arquivos."""
    with pytest.raises(ValidationError, match="WHATSAPP_TOKEN"):
        Settings(whatsapp_provider="cloud_api", whatsapp_token=None)


def test_cloud_api_com_token_e_valida():
    settings = Settings(whatsapp_provider="cloud_api", whatsapp_token="EAAG...")
    assert settings.whatsapp_provider is WhatsAppProvider.CLOUD_API
