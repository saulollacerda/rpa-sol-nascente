"""Leitura dos ZIPs do BCB.

Os arquivos vêm compactados, com CSV em windows-1252 e separador ponto e
vírgula. O cabeçalho começa com '#', que precisa sair do nome da coluna.
"""

import csv
import zipfile
from collections.abc import Iterator
from pathlib import Path

from app.domain.erros import ParsingError

ENCODING = "cp1252"
SEPARADOR = ";"


def ler_csv_do_zip(caminho_zip: Path, sufixo: str) -> Iterator[dict[str, str]]:
    """Devolve as linhas do primeiro CSV cujo nome termina em `sufixo`."""
    try:
        with zipfile.ZipFile(caminho_zip) as arquivo:
            nome = _localizar(arquivo, sufixo, caminho_zip)
            with arquivo.open(nome) as bruto:
                texto = bruto.read().decode(ENCODING)
    except zipfile.BadZipFile as erro:
        raise ParsingError(f"{caminho_zip.name} não é um ZIP válido") from erro
    except FileNotFoundError as erro:
        raise ParsingError(f"{caminho_zip} não existe") from erro

    leitor = csv.DictReader(texto.splitlines(), delimiter=SEPARADOR)
    if leitor.fieldnames:
        leitor.fieldnames = [campo.lstrip("#") for campo in leitor.fieldnames]
    yield from leitor


def _localizar(arquivo: zipfile.ZipFile, sufixo: str, caminho: Path) -> str:
    candidatos = [n for n in arquivo.namelist() if n.endswith(sufixo)]
    if not candidatos:
        raise ParsingError(f"{caminho.name} não contém arquivo terminado em '{sufixo}'")
    return candidatos[0]
