"""Contratos de entrada e saída da API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.execucao import Execucao
from app.domain.formatacao import UFS

HONDA = "45441789"


class SolicitacaoIn(BaseModel):
    """Parâmetros do painel — PRD, seção 5. Defaults para a Sol Nascente Motos."""

    data_base: str = Field(pattern=r"^\d{6}$", examples=["202607"])
    segmento: int = Field(4, ge=1, le=6)
    ufs: list[str] = Field(default_factory=lambda: ["PI", "MA"], min_length=1)
    cnpj_administradora: str = Field(HONDA, pattern=r"^\d{1,8}$")
    top_concorrentes: int = Field(3, ge=0, le=10)
    destinatario: str | None = Field(None, examples=["+55 86 99999-0000"])

    @field_validator("data_base")
    @classmethod
    def mes_valido(cls, valor: str) -> str:
        if not 1 <= int(valor[4:]) <= 12:
            raise ValueError("mês fora de 01 a 12")
        return valor

    @field_validator("ufs")
    @classmethod
    def ufs_validas(cls, valor: list[str]) -> list[str]:
        normalizadas = [u.strip().upper() for u in valor]
        invalidas = sorted(set(normalizadas) - set(UFS))
        if invalidas:
            raise ValueError(f"UF inválida: {', '.join(invalidas)}")
        return normalizadas

    @field_validator("destinatario")
    @classmethod
    def telefone_valido(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        digitos = "".join(c for c in valor if c.isdigit())
        if not 10 <= len(digitos) <= 15:
            raise ValueError("telefone deve ter de 10 a 15 dígitos, com DDI")
        return digitos


class ExecucaoOut(BaseModel):
    id: int
    status: str
    tentativas: int
    parametros: dict[str, Any]
    destinatario: str
    criado_em: datetime
    atualizado_em: datetime
    dados_encontrados: dict[str, Any] | None
    mensagem_gerada: str | None
    enviado_em: datetime | None
    provider_message_id: str | None
    erro_tipo: str | None
    erro_descricao: str | None

    @classmethod
    def de_dominio(cls, e: Execucao) -> "ExecucaoOut":
        return cls(
            id=e.id,
            status=e.status.value,
            tentativas=e.tentativas,
            parametros=e.parametros.como_dict(),
            destinatario=e.parametros.destinatario,
            criado_em=e.criado_em,
            atualizado_em=e.atualizado_em,
            dados_encontrados=e.dados_encontrados,
            mensagem_gerada=e.mensagem_gerada,
            enviado_em=e.enviado_em,
            provider_message_id=e.provider_message_id,
            erro_tipo=e.erro_tipo,
            erro_descricao=e.erro_descricao,
        )


class SolicitacaoOut(BaseModel):
    decisao: str
    execucao: ExecucaoOut
