"""Configuração — regras definidas no ADR-005 e no ADR-009."""

from app.config import Settings, WhatsAppProvider


def test_usa_adapter_fake_por_padrao():
    """A demonstração não pode depender de um número conectado."""
    assert Settings().whatsapp_provider is WhatsAppProvider.FAKE


def test_waha_funciona_com_os_defaults():
    settings = Settings(whatsapp_provider="waha")
    assert settings.whatsapp_provider is WhatsAppProvider.WAHA
    assert settings.waha_url == "http://localhost:3000"
    assert settings.waha_session == "default"
    assert settings.waha_api_key is None


def test_fabrica_escolhe_o_adapter_pelo_provider():
    from app.infra.whatsapp import FakeSender, WahaSender, criar_sender

    assert isinstance(criar_sender(Settings(whatsapp_provider="fake")), FakeSender)
    assert isinstance(criar_sender(Settings(whatsapp_provider="waha")), WahaSender)
