"""Conexão do WhatsApp — o painel mostra o QR code e o status (ADR-009)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencias import get_conexao
from app.domain.erros import EnvioError
from app.domain.portas import ConexaoWhatsApp, SituacaoConexao

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


class ConexaoOut(BaseModel):
    situacao: SituacaoConexao
    conta: str | None
    qr_code: str | None
    mensagem: str | None


@router.get("/conexao", response_model=ConexaoOut)
def conexao(servico: Annotated[ConexaoWhatsApp, Depends(get_conexao)]) -> ConexaoOut:
    """Consultado em loop pelo painel: provedor fora do ar é uma situação, não um 5xx."""
    try:
        e = servico.estado()
    except EnvioError as erro:
        return ConexaoOut(
            situacao=SituacaoConexao.INDISPONIVEL, conta=None, qr_code=None, mensagem=str(erro)
        )
    return ConexaoOut(situacao=e.situacao, conta=e.conta, qr_code=e.qr_code, mensagem=e.mensagem)


@router.post("/conexao/reconectar", status_code=202)
def reconectar(servico: Annotated[ConexaoWhatsApp, Depends(get_conexao)]) -> None:
    """Gera um QR code novo — o anterior vence em cerca de um minuto sem leitura."""
    try:
        servico.reconectar()
    except EnvioError as erro:
        raise HTTPException(503, str(erro)) from erro
