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
    settings = Settings(
        whatsapp_provider="cloud_api", whatsapp_token="EAAG...", whatsapp_phone_number_id="123"
    )
    assert settings.whatsapp_provider is WhatsAppProvider.CLOUD_API


def test_cloud_api_sem_phone_number_id_falha_na_inicializacao():
    with pytest.raises(ValidationError, match="WHATSAPP_PHONE_NUMBER_ID"):
        Settings(whatsapp_provider="cloud_api", whatsapp_token="EAAG...")


def test_fabrica_escolhe_o_adapter_pelo_provider():
    from app.infra.whatsapp import CloudApiSender, FakeSender, criar_sender

    assert isinstance(criar_sender(Settings(whatsapp_provider="fake")), FakeSender)
    real = Settings(
        whatsapp_provider="cloud_api", whatsapp_token="EAAG...", whatsapp_phone_number_id="123"
    )
    assert isinstance(criar_sender(real), CloudApiSender)
