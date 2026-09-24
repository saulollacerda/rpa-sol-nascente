"""Configuração — regras definidas no ADR-005 e no ADR-009."""

import pytest

from app.config import Settings, WhatsAppProvider


@pytest.fixture
def sem_env_local(monkeypatch):
    """Defaults de verdade: nem o backend/.env da máquina nem variáveis do shell."""
    for nome in ("WHATSAPP_PROVIDER", "WAHA_URL", "WAHA_API_KEY", "WAHA_SESSION"):
        monkeypatch.delenv(nome, raising=False)
    return lambda **campos: Settings(_env_file=None, **campos)


def test_envia_de_verdade_por_padrao(sem_env_local):
    """O produto é o relatório chegando no celular; o fake é opt-in."""
    assert sem_env_local().whatsapp_provider is WhatsAppProvider.WAHA


def test_waha_funciona_com_os_defaults(sem_env_local):
    settings = sem_env_local()
    assert settings.whatsapp_provider is WhatsAppProvider.WAHA
    assert settings.waha_url == "http://localhost:3000"
    assert settings.waha_session == "default"
    assert settings.waha_api_key is None


def test_coleta_tenta_tres_vezes_por_padrao(sem_env_local):
    settings = sem_env_local()
    assert settings.coleta_tentativas == 3
    assert settings.coleta_espera_inicial_segundos == 5


def test_coleta_precisa_de_ao_menos_uma_tentativa(sem_env_local):
    with pytest.raises(ValueError):
        sem_env_local(coleta_tentativas=0)


def test_fabrica_escolhe_o_adapter_pelo_provider():
    from app.infra.whatsapp import FakeSender, WahaSender, criar_sender

    assert isinstance(criar_sender(Settings(whatsapp_provider="fake")), FakeSender)
    assert isinstance(criar_sender(Settings(whatsapp_provider="waha")), WahaSender)
