"""Montagem do relatório a partir dos dois datasets."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.analise import (
    TOP_CONCORRENTES_PADRAO,
    Alerta,
    PerfilAdministradora,
    PosicaoUF,
    Recorte,
    detectar_alertas,
    escolher_administradoras,
    participacao,
    perfil_da_administradora,
    recortar,
    resumir,
)
from app.domain.modelos import RegistroConsolidado, RegistroUF


@dataclass(frozen=True, slots=True)
class Relatorio:
    segmento: int
    ufs: tuple[str, ...]  # vazio: o recorte é o Brasil inteiro
    data_base_uf: str | None
    data_base_nacional: str | None
    recorte: Recorte | None  # None: não há arquivo por UF até a data-base
    posicoes_uf: tuple[PosicaoUF, ...]
    administradoras: tuple[PerfilAdministradora, ...]  # a escolhida vem primeiro
    alertas: tuple[Alerta, ...]

    @property
    def alvo(self) -> PerfilAdministradora:
        return self.administradoras[0]

    @property
    def tem_resultado(self) -> bool:
        """Falso é o desfecho SEM_RESULTADO do ADR-004: não há o que enviar."""
        atua_no_recorte = self.alvo.recorte.ativos > 0 or self.alvo.recorte.adesoes > 0
        return atua_no_recorte or self.alvo.nacional is not None


def montar_relatorio(
    consolidado: Sequence[RegistroConsolidado],
    por_uf: Sequence[RegistroUF] | None,
    segmento: int,
    ufs: Sequence[str],
    cnpj_alvo: str,
    top_concorrentes: int = TOP_CONCORRENTES_PADRAO,
) -> Relatorio:
    """`por_uf` é None quando a data-base não tem arquivo trimestral de UF."""
    ufs = list(dict.fromkeys(ufs))
    registros = recortar(por_uf, segmento, ufs) if por_uf is not None else []
    recorte = resumir(registros) if por_uf is not None else None

    posicoes = sorted(
        (_posicao(registros, uf, cnpj_alvo) for uf in ufs) if recorte else (),
        key=lambda p: p.ativos,
        reverse=True,
    )
    ordem = tuple(p.uf for p in posicoes) if recorte else tuple(sorted(ufs))

    perfis = tuple(
        perfil_da_administradora(registros, consolidado, segmento, ordem if recorte else (), c)
        for c in escolher_administradoras(registros, cnpj_alvo, top_concorrentes)
    )
    return Relatorio(
        segmento=segmento,
        ufs=ordem,
        data_base_uf=por_uf[0].data_base if por_uf else None,
        data_base_nacional=next((r.data_base for r in consolidado if r.segmento == segmento), None),
        recorte=recorte,
        posicoes_uf=tuple(posicoes),
        administradoras=perfis,
        alertas=detectar_alertas(perfis),
    )


def _posicao(registros: Sequence[RegistroUF], uf: str, cnpj_alvo: str) -> PosicaoUF:
    da_uf = [r for r in registros if r.uf == uf]
    mercado = resumir(da_uf)
    return PosicaoUF(uf, mercado.ativos, mercado.adesoes, participacao(da_uf, cnpj_alvo))
