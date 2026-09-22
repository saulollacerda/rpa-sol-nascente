"""Fonte de dados real: robô no site do BCB + parsers.

Implementa a porta FonteDeDados. Não é TDD (depende do site); coberta por
teste de integração. Ainda baixa os arquivos a cada consulta: o cache do
ADR-006 é o próximo passo.
"""

from pathlib import Path

from app.domain.erros import ColetaError
from app.domain.periodos import data_base_uf_para
from app.domain.portas import DadosColetados
from app.parsing.consolidado import ler_consolidado
from app.parsing.uf import ler_uf
from app.rpa.catalogo import Dataset
from app.rpa.coletor import ColetorBCB


class FonteBCB:
    def __init__(self, url_pagina: str, diretorio: Path, headless: bool = True) -> None:
        self._url = url_pagina
        self._diretorio = diretorio
        self._headless = headless

    def obter(self, data_base: str) -> DadosColetados:
        with ColetorBCB(self._url, headless=self._headless) as coletor:
            catalogo = coletor.ler_catalogo()

            item_consolidado = catalogo.buscar(Dataset.CONSOLIDADO, data_base)
            if item_consolidado is None:
                recente = catalogo.mais_recente(Dataset.CONSOLIDADO)
                raise ColetaError(
                    f"data-base {data_base} não publicada; a mais recente é "
                    f"{recente.data_base if recente else 'nenhuma'}"
                )

            data_base_uf = data_base_uf_para(data_base, catalogo.data_bases(Dataset.UF))
            item_uf = catalogo.buscar(Dataset.UF, data_base_uf) if data_base_uf else None

            zip_consolidado = coletor.baixar(item_consolidado, self._diretorio)
            zip_uf = coletor.baixar(item_uf, self._diretorio) if item_uf else None

        return DadosColetados(
            data_base_consolidado=data_base,
            consolidado=tuple(ler_consolidado(zip_consolidado)),
            data_base_uf=data_base_uf if zip_uf else None,
            uf=tuple(ler_uf(zip_uf)) if zip_uf else None,
        )
