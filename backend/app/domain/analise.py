"""Análise de mercado — regras do template do relatório.

Funções puras: recebem registros já parseados e não tocam rede, disco nem
banco. A administradora é identificada pela raiz do CNPJ, não pelo nome, que
o BCB abrevia e pode mudar entre data-bases.

O share é sempre calculado dentro do recorte de UFs escolhido, não sobre o
Brasil: é o mercado em que a concessionária disputa.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

from app.domain.modelos import RegistroConsolidado, RegistroUF

CNPJ_HONDA = "45441789"
TOP_CONCORRENTES_PADRAO = 3
MAX_ADMINISTRADORAS = 4  # acima disso a mensagem passa de 50 linhas e ninguém lê

# Movimento de share vira alerta quando é relevante nas duas escalas: em pontos
# (descarta ruído de quem tem 0,5%) e relativo ao próprio share (descarta +4 p.p.
# sobre 50%, que é oscilação normal de trimestre).
VARIACAO_MINIMA_PP = 1.0
VARIACAO_MINIMA_RELATIVA = 0.15
LIMIAR_INADIMPLENCIA = 15.0


@dataclass(frozen=True, slots=True)
class Recorte:
    """O mercado nas UFs escolhidas (ou no Brasil). Vem do dataset trimestral."""

    ativos: int
    adesoes: int
    contemplados_lance: int
    contemplados_sorteio: int
    excluidos: int
    administradoras: int

    @property
    def contemplados(self) -> int:
        return self.contemplados_lance + self.contemplados_sorteio

    @property
    def percentual_lance(self) -> float:
        return calcular_share(self.contemplados_lance, self.contemplados)

    @property
    def taxa_exclusao(self) -> float:
        """Excluídos sobre todos que já entraram: ativos + excluídos."""
        return calcular_share(self.excluidos, self.ativos + self.excluidos)


@dataclass(frozen=True, slots=True)
class Participacao:
    """Share de uma administradora na carteira ativa e nas vendas do trimestre."""

    ativos: int
    adesoes: int
    share_carteira: float
    share_adesoes: float

    @property
    def variacao(self) -> float:
        """Positiva: vende mais do que o tamanho da carteira — está ganhando espaço."""
        return self.share_adesoes - self.share_carteira


@dataclass(frozen=True, slots=True)
class ParticipacaoNaUF:
    uf: str
    share_carteira: float
    share_adesoes: float


@dataclass(frozen=True, slots=True)
class PosicaoUF:
    """Uma linha do bloco por UF: o mercado da UF e a administradora escolhida nele."""

    uf: str
    ativos: int
    adesoes: int
    alvo: Participacao


@dataclass(frozen=True, slots=True)
class IndicadoresNacionais:
    """O BCB não divulga por UF: estes vêm do dataset mensal, do país inteiro."""

    data_base: str
    taxa_administracao: float
    inadimplencia: float
    contemplacao_mes: float
    vendas_mes: int
    credito_pendente: int


@dataclass(frozen=True, slots=True)
class PerfilAdministradora:
    cnpj_raiz: str
    nome_administradora: str
    recorte: Participacao
    por_uf: tuple[ParticipacaoNaUF, ...]
    nacional: IndicadoresNacionais | None


@dataclass(frozen=True, slots=True)
class Movimento:
    """`uf` None: a comparação é no Brasil inteiro."""

    uf: str | None
    antes: float
    depois: float


@dataclass(frozen=True, slots=True)
class Alerta:
    tipo: Literal["ganho", "perda", "inadimplencia"]
    nome_administradora: str
    movimentos: tuple[Movimento, ...] = ()
    inadimplencia: float | None = None


def calcular_share(parte: int, total: int) -> float:
    """Percentual de `parte` em `total`. Total zero dá zero, não erro."""
    return parte / total * 100 if total else 0.0


def recortar(
    registros: Sequence[RegistroUF], segmento: int, ufs: Sequence[str]
) -> list[RegistroUF]:
    """Registros do segmento nas UFs pedidas. Sem UF, o Brasil inteiro."""
    return [r for r in registros if r.segmento == segmento and (not ufs or r.uf in ufs)]


def resumir(registros: Sequence[RegistroUF]) -> Recorte:
    return Recorte(
        ativos=sum(r.consorciados_ativos for r in registros),
        adesoes=sum(r.adesoes_no_trimestre for r in registros),
        contemplados_lance=sum(r.contemplados_lance_no_trimestre for r in registros),
        contemplados_sorteio=sum(r.contemplados_sorteio_no_trimestre for r in registros),
        excluidos=sum(r.excluidos for r in registros),
        administradoras=len({r.cnpj_raiz for r in registros}),
    )


def participacao(registros: Sequence[RegistroUF], cnpj: str) -> Participacao:
    # Os totais são do recorte inteiro: calculados antes de isolar a
    # administradora, senão o share sairia sempre 100%.
    mercado = resumir(registros)
    proprios = resumir([r for r in registros if r.cnpj_raiz == cnpj])
    return Participacao(
        ativos=proprios.ativos,
        adesoes=proprios.adesoes,
        share_carteira=calcular_share(proprios.ativos, mercado.ativos),
        share_adesoes=calcular_share(proprios.adesoes, mercado.adesoes),
    )


def indicadores_nacionais(
    registros: Sequence[RegistroConsolidado], segmento: int, cnpj: str
) -> IndicadoresNacionais | None:
    r = next((r for r in registros if r.segmento == segmento and r.cnpj_raiz == cnpj), None)
    if r is None:
        return None
    return IndicadoresNacionais(
        data_base=r.data_base,
        taxa_administracao=r.taxa_administracao,
        inadimplencia=calcular_share(r.cotas_inadimplentes, r.cotas_ativas),
        # Sobre quem ainda espera a carta: é a chance mensal de ser contemplado.
        contemplacao_mes=calcular_share(
            r.cotas_contempladas_no_mes, r.cotas_ativas_nao_contempladas
        ),
        vendas_mes=r.cotas_comercializadas_no_mes,
        credito_pendente=r.cotas_credito_pendente,
    )


def escolher_administradoras(
    recorte: Sequence[RegistroUF], cnpj_alvo: str, top_concorrentes: int
) -> tuple[str, ...]:
    """A escolhida, a Honda como referência e as maiores concorrentes em adesões."""
    fixas = [cnpj_alvo] if cnpj_alvo == CNPJ_HONDA else [cnpj_alvo, CNPJ_HONDA]
    vagas = max(0, min(top_concorrentes, MAX_ADMINISTRADORAS - len(fixas)))

    adesoes: dict[str, int] = {}
    ativos: dict[str, int] = {}
    for r in recorte:
        adesoes[r.cnpj_raiz] = adesoes.get(r.cnpj_raiz, 0) + r.adesoes_no_trimestre
        ativos[r.cnpj_raiz] = ativos.get(r.cnpj_raiz, 0) + r.consorciados_ativos
    concorrentes = sorted(
        (c for c in adesoes if c not in fixas),
        key=lambda c: (adesoes[c], ativos[c]),
        reverse=True,
    )
    return (*fixas, *concorrentes[:vagas])


def perfil_da_administradora(
    recorte: Sequence[RegistroUF],
    consolidado: Sequence[RegistroConsolidado],
    segmento: int,
    ufs: Sequence[str],
    cnpj: str,
) -> PerfilAdministradora:
    return PerfilAdministradora(
        cnpj_raiz=cnpj,
        nome_administradora=_nome(cnpj, recorte, consolidado),
        recorte=participacao(recorte, cnpj),
        por_uf=tuple(_participacao_na_uf(recorte, uf, cnpj) for uf in ufs),
        nacional=indicadores_nacionais(consolidado, segmento, cnpj),
    )


def detectar_alertas(perfis: Iterable[PerfilAdministradora]) -> tuple[Alerta, ...]:
    """Movimentos de share primeiro, na ordem das administradoras; inadimplência depois."""
    perfis = list(perfis)
    alertas: list[Alerta] = []
    for p in perfis:
        movimentos = [m for m in _movimentos(p) if _relevante(m)]
        ganhos = tuple(m for m in movimentos if m.depois > m.antes)
        perdas = tuple(m for m in movimentos if m.depois < m.antes)
        if ganhos:
            alertas.append(Alerta("ganho", p.nome_administradora, ganhos))
        if perdas:
            alertas.append(Alerta("perda", p.nome_administradora, perdas))
    alertas.extend(
        Alerta("inadimplencia", p.nome_administradora, inadimplencia=p.nacional.inadimplencia)
        for p in perfis
        if p.nacional and p.nacional.inadimplencia >= LIMIAR_INADIMPLENCIA
    )
    return tuple(alertas)


def _participacao_na_uf(recorte: Sequence[RegistroUF], uf: str, cnpj: str) -> ParticipacaoNaUF:
    p = participacao([r for r in recorte if r.uf == uf], cnpj)
    return ParticipacaoNaUF(uf, p.share_carteira, p.share_adesoes)


def _movimentos(p: PerfilAdministradora) -> list[Movimento]:
    if p.por_uf:
        return [Movimento(u.uf, u.share_carteira, u.share_adesoes) for u in p.por_uf]
    return [Movimento(None, p.recorte.share_carteira, p.recorte.share_adesoes)]


def _relevante(m: Movimento) -> bool:
    variacao = abs(m.depois - m.antes)
    return variacao >= VARIACAO_MINIMA_PP and variacao >= VARIACAO_MINIMA_RELATIVA * m.antes


def _nome(
    cnpj: str, recorte: Sequence[RegistroUF], consolidado: Sequence[RegistroConsolidado]
) -> str:
    for r in (*recorte, *consolidado):
        if r.cnpj_raiz == cnpj:
            return r.nome_administradora
    return cnpj
