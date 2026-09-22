"""Cenários de falha da camada de parsing — ver ADR-002.

O enunciado exige tratar arquivo indisponível e informação incompleta.
A regra é nunca mascarar o problema com dado parcial.
"""

import zipfile

import pytest

from app.parsing.consolidado import ler_consolidado
from app.parsing.leitor_zip import ParsingError
from app.parsing.uf import ler_uf


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ParsingError, match="não existe"):
        ler_consolidado(tmp_path / "ausente.zip")


def test_zip_corrompido(tmp_path):
    corrompido = tmp_path / "corrompido.zip"
    corrompido.write_bytes(b"isto nao e um zip")
    with pytest.raises(ParsingError, match="não é um ZIP válido"):
        ler_consolidado(corrompido)


def test_zip_sem_o_csv_esperado(tmp_path):
    """Acontece ao passar o ZIP de UF para o parser do consolidado."""
    vazio = tmp_path / "vazio.zip"
    with zipfile.ZipFile(vazio, "w") as z:
        z.writestr("leiame.txt", "sem csv aqui")

    with pytest.raises(ParsingError, match="Segmentos_Consolidados.csv"):
        ler_consolidado(vazio)


def test_parser_errado_para_o_arquivo_certo(zip_uf):
    with pytest.raises(ParsingError, match="Segmentos_Consolidados.csv"):
        ler_consolidado(zip_uf)


def test_parser_errado_para_o_outro_arquivo(zip_consolidado):
    with pytest.raises(ParsingError, match="Consorcios_UF.csv"):
        ler_uf(zip_consolidado)
