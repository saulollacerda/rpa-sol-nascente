"""Entidades do domínio. Sem dependência de I/O — ver ADR-001."""

from dataclasses import dataclass

SEGMENTOS = {
    1: "bens imóveis",
    2: "veículos de carga e transporte coletivo",
    3: "veículos automotores",
    4: "motocicletas e motonetas",
    5: "outros bens móveis duráveis",
    6: "serviços turísticos",
}


@dataclass(frozen=True, slots=True)
class RegistroConsolidado:
    """Uma administradora em um segmento, numa data-base. Periodicidade mensal."""

    nome_administradora: str
    cnpj_raiz: str
    data_base: str
    segmento: int
    taxa_administracao: float
    grupos_ativos: int
    cotas_ativas_contempladas: int
    cotas_ativas_nao_contempladas: int
    cotas_ativas_contempladas_inadimplentes: int
    cotas_ativas_nao_contempladas_inadimplentes: int
    cotas_comercializadas_no_mes: int = 0
    cotas_contempladas_no_mes: int = 0
    cotas_credito_pendente: int = 0

    @property
    def cotas_ativas(self) -> int:
        return self.cotas_ativas_contempladas + self.cotas_ativas_nao_contempladas

    @property
    def cotas_inadimplentes(self) -> int:
        return (
            self.cotas_ativas_contempladas_inadimplentes
            + self.cotas_ativas_nao_contempladas_inadimplentes
        )


@dataclass(frozen=True, slots=True)
class RegistroUF:
    """Uma administradora, num segmento e numa UF. Periodicidade trimestral."""

    nome_administradora: str
    cnpj_raiz: str
    data_base: str
    segmento: int
    uf: str
    contemplados_lance: int
    contemplados_sorteio: int
    nao_contemplados: int
    contemplados_lance_no_trimestre: int
    contemplados_sorteio_no_trimestre: int
    adesoes_no_trimestre: int
    excluidos_contemplados: int = 0
    excluidos_nao_contemplados: int = 0

    @property
    def consorciados_ativos(self) -> int:
        return self.contemplados_lance + self.contemplados_sorteio + self.nao_contemplados

    @property
    def contemplados_no_trimestre(self) -> int:
        return self.contemplados_lance_no_trimestre + self.contemplados_sorteio_no_trimestre

    @property
    def excluidos(self) -> int:
        return self.excluidos_contemplados + self.excluidos_nao_contemplados
