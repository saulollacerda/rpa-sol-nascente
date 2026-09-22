"""Análise de mercado — regras de negócio do PRD, seção 7.

Funções puras: recebem registros já parseados e não tocam rede, disco nem
banco. A administradora é identificada pela raiz do CNPJ, não pelo nome, que
o BCB abrevia e pode mudar entre data-bases.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.domain.modelos import RegistroConsolidado, RegistroUF

TOP_CONCORRENTES_PADRAO = 3


@dataclass(frozen=True, slots=True)
class Concorrente:
    nome_administradora: str
    cnpj_raiz: str
    ativos: int
    share: float


@dataclass(frozen=True, slots=True)
class PosicaoNaPraca:
    """Posição de uma administradora numa UF. Vem do dataset trimestral."""

    uf: str
    data_base: str
    nome_administradora: str
    ativos_praca: int
    administradoras_na_praca: int
    ativos: int
    share: float
    adesoes_no_trimestre: int
    contemplados_lance_no_trimestre: int
    contemplados_sorteio_no_trimestre: int
    concorrentes: tuple[Concorrente, ...]

    @property
    def contemplados_no_trimestre(self) -> int:
        return self.contemplados_lance_no_trimestre + self.contemplados_sorteio_no_trimestre


@dataclass(frozen=True, slots=True)
class PosicaoNacional:
    """Posição de uma administradora no país. Vem do dataset mensal."""

    data_base: str
    nome_administradora: str
    cotas_ativas: int
    cotas_ativas_mercado: int
    administradoras_no_segmento: int
    share: float
    taxa_administracao: float
    grupos_ativos: int
    concorrentes: tuple[Concorrente, ...]


def calcular_share(parte: int, total: int) -> float:
    """Percentual de `parte` em `total`. Praça vazia dá zero, não erro."""
    return parte / total * 100 if total else 0.0


def analisar_praca(
    registros: Sequence[RegistroUF],
    uf: str,
    segmento: int,
    cnpj_alvo: str,
    top_concorrentes: int = TOP_CONCORRENTES_PADRAO,
) -> PosicaoNaPraca | None:
    """Posição da administradora na UF, ou None se ela não opera ali."""
    praca = [r for r in registros if r.uf == uf and r.segmento == segmento]
    alvo = _localizar(praca, cnpj_alvo)
    if alvo is None:
        return None

    # O total é da praça inteira: calculado antes de isolar a administradora,
    # senão o share sairia sempre 100%.
    total = sum(r.consorciados_ativos for r in praca)

    return PosicaoNaPraca(
        uf=uf,
        data_base=alvo.data_base,
        nome_administradora=alvo.nome_administradora,
        ativos_praca=total,
        administradoras_na_praca=len(praca),
        ativos=alvo.consorciados_ativos,
        share=calcular_share(alvo.consorciados_ativos, total),
        adesoes_no_trimestre=alvo.adesoes_no_trimestre,
        contemplados_lance_no_trimestre=alvo.contemplados_lance_no_trimestre,
        contemplados_sorteio_no_trimestre=alvo.contemplados_sorteio_no_trimestre,
        concorrentes=_ranking(
            praca, cnpj_alvo, total, lambda r: r.consorciados_ativos, top_concorrentes
        ),
    )


def analisar_nacional(
    registros: Sequence[RegistroConsolidado],
    segmento: int,
    cnpj_alvo: str,
    top_concorrentes: int = TOP_CONCORRENTES_PADRAO,
) -> PosicaoNacional | None:
    """Posição da administradora no segmento em todo o país, ou None se ausente."""
    mercado = [r for r in registros if r.segmento == segmento]
    alvo = _localizar(mercado, cnpj_alvo)
    if alvo is None:
        return None

    total = sum(r.cotas_ativas for r in mercado)

    return PosicaoNacional(
        data_base=alvo.data_base,
        nome_administradora=alvo.nome_administradora,
        cotas_ativas=alvo.cotas_ativas,
        cotas_ativas_mercado=total,
        administradoras_no_segmento=len(mercado),
        share=calcular_share(alvo.cotas_ativas, total),
        taxa_administracao=alvo.taxa_administracao,
        grupos_ativos=alvo.grupos_ativos,
        concorrentes=_ranking(
            mercado, cnpj_alvo, total, lambda r: r.cotas_ativas, top_concorrentes
        ),
    )


def _localizar[R: (RegistroConsolidado, RegistroUF)](registros: Sequence[R], cnpj: str) -> R | None:
    return next((r for r in registros if r.cnpj_raiz == cnpj), None)


def _ranking[R: (RegistroConsolidado, RegistroUF)](
    registros: Sequence[R],
    cnpj_alvo: str,
    total: int,
    medida: Callable[[R], int],
    limite: int,
) -> tuple[Concorrente, ...]:
    outros = sorted((r for r in registros if r.cnpj_raiz != cnpj_alvo), key=medida, reverse=True)
    return tuple(
        Concorrente(
            nome_administradora=r.nome_administradora,
            cnpj_raiz=r.cnpj_raiz,
            ativos=medida(r),
            share=calcular_share(medida(r), total),
        )
        for r in outros[:limite]
    )
