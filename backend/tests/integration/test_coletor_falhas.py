"""Falhas de infraestrutura na coleta.

Módulo separado de propósito: a API síncrona do Playwright não admite duas
sessões abertas na mesma thread, e a fixture de test_coletor_bcb.py mantém
uma aberta durante todo aquele módulo.
"""

import pytest

from app.rpa.coletor import ColetaError, ColetorBCB

pytestmark = pytest.mark.integration


def test_site_inacessivel_vira_coleta_error():
    """Exceção do Playwright não pode vazar: vira erro de domínio com contexto."""
    with ColetorBCB("http://127.0.0.1:9/inexistente", timeout_ms=5_000) as coletor:
        with pytest.raises(ColetaError, match="indisponível"):
            coletor.ler_catalogo()


def test_uso_fora_do_bloco_with_e_erro_de_programacao():
    with pytest.raises(RuntimeError, match="with"):
        ColetorBCB("http://127.0.0.1:9/").ler_catalogo()
