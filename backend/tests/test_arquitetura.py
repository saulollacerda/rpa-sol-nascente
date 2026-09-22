"""Regra de dependência do ADR-001, verificada em vez de apenas documentada.

domain/ é puro: não pode importar nada que toque rede, disco, banco ou
browser, nem as camadas externas. Se este teste falhar, a lógica de
negócio deixou de ser testável sem infraestrutura.
"""

import ast
from pathlib import Path

import pytest

DOMINIO = Path(__file__).parents[1] / "app" / "domain"

PROIBIDOS = {
    "playwright", "sqlalchemy", "httpx", "requests", "fastapi", "uvicorn",
    "zipfile", "csv", "sqlite3", "socket", "urllib",
    "app.api", "app.infra", "app.parsing", "app.rpa", "app.config",
}  # fmt: skip


def _importados(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.add(no.module)
    return nomes


def _viola(modulo: str) -> bool:
    return any(modulo == p or modulo.startswith(p + ".") for p in PROIBIDOS)


@pytest.mark.parametrize("arquivo", sorted(DOMINIO.glob("*.py")), ids=lambda p: p.name)
def test_dominio_nao_importa_io_nem_camadas_externas(arquivo):
    violacoes = sorted(m for m in _importados(arquivo) if _viola(m))
    assert not violacoes, f"{arquivo.name} importa {violacoes}"
