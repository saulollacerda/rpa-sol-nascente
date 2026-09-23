"""Ciclo de vida de uma execução — ADR-004."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.domain.erros import TransicaoInvalida

# Changes when the key fields change, or when the same parameters start producing
# a different report (v2: WhatsApp template) — otherwise the old one is reused.
VERSAO_DA_CHAVE = 2


class StatusExecucao(StrEnum):
    PENDENTE = "PENDENTE"
    COLETANDO = "COLETANDO"
    PROCESSANDO = "PROCESSANDO"
    MENSAGEM_GERADA = "MENSAGEM_GERADA"
    ENVIANDO = "ENVIANDO"
    ENVIADO = "ENVIADO"
    SEM_RESULTADO = "SEM_RESULTADO"
    FALHA_COLETA = "FALHA_COLETA"
    FALHA_PROCESSAMENTO = "FALHA_PROCESSAMENTO"
    FALHA_ENVIO = "FALHA_ENVIO"


S = StatusExecucao

FALHAS = frozenset({S.FALHA_COLETA, S.FALHA_PROCESSAMENTO, S.FALHA_ENVIO})
CONCLUIDAS = frozenset({S.ENVIADO, S.SEM_RESULTADO})

TRANSICOES: dict[StatusExecucao, frozenset[StatusExecucao]] = {
    S.PENDENTE: frozenset({S.COLETANDO}),
    S.COLETANDO: frozenset({S.PROCESSANDO, S.FALHA_COLETA}),
    S.PROCESSANDO: frozenset({S.MENSAGEM_GERADA, S.SEM_RESULTADO, S.FALHA_PROCESSAMENTO}),
    S.MENSAGEM_GERADA: frozenset({S.ENVIANDO}),
    S.ENVIANDO: frozenset({S.ENVIADO, S.FALHA_ENVIO}),
    S.ENVIADO: frozenset(),
    S.SEM_RESULTADO: frozenset(),
    **{falha: frozenset({S.PENDENTE}) for falha in FALHAS},
}


def validar_transicao(de: StatusExecucao, para: StatusExecucao) -> None:
    if para not in TRANSICOES[de]:
        raise TransicaoInvalida(f"{de} → {para} não é permitido")


class Decisao(StrEnum):
    CRIAR = "CRIAR"
    REUSAR = "REUSAR"
    RETENTAR = "RETENTAR"


def decidir(status_anterior: StatusExecucao | None) -> Decisao:
    """O que fazer diante de uma execução anterior com a mesma chave.

    Concluída não se repete (anti-duplicidade); em andamento não se duplica
    (dois cliques seguidos); só falha pode ser tentada de novo.
    """
    if status_anterior is None:
        return Decisao.CRIAR
    if status_anterior in FALHAS:
        return Decisao.RETENTAR
    return Decisao.REUSAR


@dataclass(frozen=True, slots=True)
class ParametrosConsulta:
    """Parâmetros escolhidos no painel, já normalizados."""

    data_base: str
    segmento: int
    ufs: tuple[str, ...]
    cnpj_administradora: str
    top_concorrentes: int
    destinatario: str

    def __post_init__(self) -> None:
        normalizar = object.__setattr__
        normalizar(self, "ufs", tuple(sorted({u.strip().upper() for u in self.ufs})))
        normalizar(self, "destinatario", _digitos(self.destinatario))
        normalizar(self, "cnpj_administradora", _digitos(self.cnpj_administradora).zfill(8))

    def como_dict(self) -> dict[str, Any]:
        dados = asdict(self)
        dados["ufs"] = list(self.ufs)
        return dados

    @classmethod
    def de_dict(cls, dados: dict[str, Any]) -> "ParametrosConsulta":
        return cls(**{**dados, "ufs": tuple(dados["ufs"])})


def chave_idempotencia(parametros: ParametrosConsulta) -> str:
    """SHA-256 da forma canônica dos parâmetros — ADR-004.

    Normalização acontece antes: ordem das UFs e formatação do telefone não
    produzem chaves diferentes para a mesma consulta.
    """
    canonico = json.dumps(
        {"v": VERSAO_DA_CHAVE, **parametros.como_dict()},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonico.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Execucao:
    id: int
    chave: str
    parametros: ParametrosConsulta
    status: StatusExecucao
    tentativas: int
    criado_em: datetime
    atualizado_em: datetime
    dados_encontrados: dict[str, Any] | None = None
    mensagem_gerada: str | None = None
    enviado_em: datetime | None = None
    provider_message_id: str | None = None
    erro_tipo: str | None = None
    erro_descricao: str | None = None


def _digitos(valor: str) -> str:
    return "".join(c for c in valor if c.isdigit())
