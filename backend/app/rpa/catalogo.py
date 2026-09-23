"""Catálogo de arquivos publicados pelo BCB — ver ADR-008.

A página de consórcios pede a lista de arquivos a uma API JSON interna. O
robô escuta essas respostas; este módulo só converte o JSON em itens. Não
conhece o endereço da API: classifica cada item pelo padrão do nome do
arquivo.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from urllib.parse import urljoin


class Dataset(StrEnum):
    CONSOLIDADO = "consolidado"
    UF = "uf"


PADROES = {
    Dataset.CONSOLIDADO: re.compile(r"^(\d{6})Consorcios\.zip$"),
    Dataset.UF: re.compile(r"^(\d{6})Consorcios_UF\.zip$"),
}


@dataclass(frozen=True, slots=True)
class ItemCatalogo:
    dataset: Dataset
    data_base: str
    nome: str
    url: str
    tamanho: int
    publicado_em: datetime | None

    @property
    def rotulo(self) -> str:
        """Início do texto da opção no dropdown: '202606Consorcios_UF (103.4 Kb)'."""
        return self.nome.removesuffix(".zip")


@dataclass(frozen=True, slots=True)
class Catalogo:
    itens: tuple[ItemCatalogo, ...]

    @property
    def vazio(self) -> bool:
        return not self.itens

    def do_dataset(self, dataset: Dataset) -> tuple[ItemCatalogo, ...]:
        """Itens do dataset, da data-base mais recente para a mais antiga."""
        return tuple(
            sorted(
                (i for i in self.itens if i.dataset is dataset),
                key=lambda i: i.data_base,
                reverse=True,
            )
        )

    def data_bases(self, dataset: Dataset) -> list[str]:
        return [i.data_base for i in self.do_dataset(dataset)]

    def mais_recente(self, dataset: Dataset) -> ItemCatalogo | None:
        itens = self.do_dataset(dataset)
        return itens[0] if itens else None

    def buscar(self, dataset: Dataset, data_base: str) -> ItemCatalogo | None:
        return next((i for i in self.do_dataset(dataset) if i.data_base == data_base), None)


def extrair_itens(corpo: object, origem: str) -> list[ItemCatalogo]:
    """Itens de catálogo contidos numa resposta JSON qualquer da página.

    Respostas que não têm o formato do catálogo devolvem lista vazia: a página
    faz dezenas de requisições e só algumas interessam.
    """
    if isinstance(corpo, dict):
        corpo = corpo.get("conteudo")
    if not isinstance(corpo, list):
        return []
    return [item for bruto in corpo if (item := _converter(bruto, origem)) is not None]


def montar_catalogo(corpos: Iterable[object], origem: str) -> Catalogo:
    unicos: dict[tuple[Dataset, str], ItemCatalogo] = {}
    for corpo in corpos:
        for item in extrair_itens(corpo, origem):
            unicos.setdefault((item.dataset, item.data_base), item)
    return Catalogo(itens=tuple(unicos.values()))


def _converter(bruto: object, origem: str) -> ItemCatalogo | None:
    if not isinstance(bruto, dict):
        return None
    nome, url = bruto.get("Nome"), bruto.get("Url")
    if not isinstance(nome, str) or not isinstance(url, str) or not url:
        return None

    for dataset, padrao in PADROES.items():
        if casamento := padrao.match(nome):
            return ItemCatalogo(
                dataset=dataset,
                data_base=casamento.group(1),
                nome=nome,
                url=urljoin(origem, url),
                tamanho=_inteiro(bruto.get("Tamanho")),
                publicado_em=_data(bruto.get("DataPublicacao")),
            )
    return None


def _inteiro(valor: object) -> int:
    try:
        return int(str(valor))
    except ValueError:
        return 0


def _data(valor: object) -> datetime | None:
    if not isinstance(valor, str):
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None
