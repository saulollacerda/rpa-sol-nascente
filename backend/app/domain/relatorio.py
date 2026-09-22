"""Montagem do relatório a partir dos dois datasets."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.analise import (
    TOP_CONCORRENTES_PADRAO,
    PosicaoNacional,
    PosicaoNaPraca,
    analisar_nacional,
    analisar_praca,
)
from app.domain.modelos import RegistroConsolidado, RegistroUF


@dataclass(frozen=True, slots=True)
class Relatorio:
    segmento: int
    pracas: tuple[PosicaoNaPraca, ...]
    nacional: PosicaoNacional | None
    ufs_sem_resultado: tuple[str, ...]
    recorte_uf_indisponivel: bool

    @property
    def tem_resultado(self) -> bool:
        """Falso é o desfecho SEM_RESULTADO do ADR-004: não há o que enviar."""
        return bool(self.pracas) or self.nacional is not None

    @property
    def contemplados_no_trimestre(self) -> int:
        return sum(p.contemplados_no_trimestre for p in self.pracas)


def montar_relatorio(
    consolidado: Sequence[RegistroConsolidado],
    por_uf: Sequence[RegistroUF] | None,
    segmento: int,
    ufs: Sequence[str],
    cnpj_alvo: str,
    top_concorrentes: int = TOP_CONCORRENTES_PADRAO,
) -> Relatorio:
    """`por_uf` é None quando a data-base não tem arquivo trimestral de UF."""
    pracas: list[PosicaoNaPraca] = []
    ausentes: list[str] = []

    if por_uf is not None:
        for uf in ufs:
            posicao = analisar_praca(por_uf, uf, segmento, cnpj_alvo, top_concorrentes)
            if posicao is None:
                ausentes.append(uf)
            else:
                pracas.append(posicao)

    return Relatorio(
        segmento=segmento,
        pracas=tuple(pracas),
        nacional=analisar_nacional(consolidado, segmento, cnpj_alvo, top_concorrentes),
        ufs_sem_resultado=tuple(ausentes),
        recorte_uf_indisponivel=por_uf is None,
    )
