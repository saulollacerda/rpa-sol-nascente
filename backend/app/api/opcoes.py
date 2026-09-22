"""Rota de opções do painel."""

from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencias import get_opcoes
from app.api.schemas import HONDA
from app.domain.erros import ColetaError, ParsingError
from app.domain.formatacao import UFS
from app.domain.modelos import SEGMENTOS
from app.domain.opcoes import Opcoes

router = APIRouter(prefix="/opcoes", tags=["opções"])

UFS_DA_SOL_NASCENTE = ["PI", "MA"]


class FonteDeOpcoes(Protocol):
    def obter(self) -> Opcoes: ...


class AdministradoraOut(BaseModel):
    cnpj: str
    nome: str
    segmentos: list[int]


class SegmentoOut(BaseModel):
    codigo: int
    nome: str


class UfOut(BaseModel):
    sigla: str
    nome: str


class PadraoOut(BaseModel):
    data_base: str | None
    segmento: int
    ufs: list[str]
    cnpj_administradora: str
    top_concorrentes: int


class OpcoesOut(BaseModel):
    data_bases: list[str]
    data_base_administradoras: str
    administradoras: list[AdministradoraOut]
    segmentos: list[SegmentoOut]
    ufs: list[UfOut]
    padrao: PadraoOut


@router.get("", response_model=OpcoesOut)
def opcoes(fonte: Annotated[FonteDeOpcoes, Depends(get_opcoes)]) -> OpcoesOut:
    """A primeira chamada abre o site do BCB (~10s); as seguintes vêm do cache (ADR-006)."""
    try:
        o = fonte.obter()
    except (ColetaError, ParsingError) as erro:
        raise HTTPException(503, f"não foi possível ler o catálogo do BCB: {erro}") from erro

    return OpcoesOut(
        data_bases=list(o.data_bases),
        data_base_administradoras=o.data_base_administradoras,
        administradoras=[
            AdministradoraOut(cnpj=a.cnpj, nome=a.nome, segmentos=list(a.segmentos))
            for a in o.administradoras
        ],
        segmentos=[SegmentoOut(codigo=c, nome=n) for c, n in SEGMENTOS.items()],
        ufs=[UfOut(sigla=s, nome=n) for s, n in sorted(UFS.items(), key=lambda i: i[1])],
        padrao=PadraoOut(
            data_base=o.data_bases[0] if o.data_bases else None,
            segmento=4,
            ufs=UFS_DA_SOL_NASCENTE,
            cnpj_administradora=HONDA,
            top_concorrentes=3,
        ),
    )
