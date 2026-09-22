"""Opções oferecidas pelo painel — PRD, seção 5."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.modelos import RegistroConsolidado


@dataclass(frozen=True, slots=True)
class Administradora:
    cnpj: str
    nome: str
    segmentos: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Opcoes:
    data_bases: tuple[str, ...]
    """Data-bases do consolidado, da mais recente para a mais antiga."""
    data_base_administradoras: str
    """Data-base de onde saiu a lista de administradoras."""
    administradoras: tuple[Administradora, ...]


def listar_administradoras(registros: Sequence[RegistroConsolidado]) -> tuple[Administradora, ...]:
    """Uma entrada por CNPJ, com os segmentos em que atua, ordenada pelo nome."""
    nomes: dict[str, str] = {}
    segmentos: dict[str, set[int]] = {}
    for r in registros:
        nomes.setdefault(r.cnpj_raiz, r.nome_administradora)
        segmentos.setdefault(r.cnpj_raiz, set()).add(r.segmento)
    return tuple(
        sorted(
            (
                Administradora(cnpj=c, nome=nomes[c], segmentos=tuple(sorted(segmentos[c])))
                for c in nomes
            ),
            key=lambda a: a.nome,
        )
    )
