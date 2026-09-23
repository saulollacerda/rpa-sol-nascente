from pathlib import Path

import pytest

from app.parsing.consolidado import ler_consolidado
from app.parsing.uf import ler_uf

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def zip_consolidado() -> Path:
    """Dados consolidados de Julho/2026, baixados da fonte real."""
    return FIXTURES / "202607Consorcios.zip"


@pytest.fixture(scope="session")
def zip_uf() -> Path:
    """Dados por UF de Junho/2026, baixados da fonte real."""
    return FIXTURES / "202606Consorcios_UF.zip"


@pytest.fixture(scope="session")
def registros_consolidado(zip_consolidado):
    return ler_consolidado(zip_consolidado)


@pytest.fixture(scope="session")
def registros_uf(zip_uf):
    return ler_uf(zip_uf)
