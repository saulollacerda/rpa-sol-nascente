from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def zip_consolidado() -> Path:
    """Dados consolidados de Julho/2026, baixados da fonte real."""
    return FIXTURES / "202607Consorcios.zip"


@pytest.fixture(scope="session")
def zip_uf() -> Path:
    """Dados por UF de Junho/2026, baixados da fonte real."""
    return FIXTURES / "202606Consorcios_UF.zip"
