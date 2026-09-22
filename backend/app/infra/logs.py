"""Logging estruturado em JSON — padrão do CLAUDE.md.

Toda linha de uma execução carrega o execucao_id (via LoggerAdapter no
serviço). Tokens são mascarados na formatação, e não em cada chamada: o risco
real é um log.debug da configuração inteira, não imprimir o token de propósito.
"""

import json
import logging
import re
import sys
from datetime import UTC, datetime

PADROES_SENSIVEIS = (
    (re.compile(r"(Bearer\s+)\S+"), r"\1***"),
    (re.compile(r"\bEAA[A-Za-z0-9]{6,}"), "***"),  # tokens de acesso da Meta
)


def mascarar(texto: str) -> str:
    for padrao, substituto in PADROES_SENSIVEIS:
        texto = padrao.sub(substituto, texto)
    return texto


class FormatadorJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        linha: dict[str, object] = {
            "momento": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "nivel": record.levelname,
            "logger": record.name,
            "mensagem": mascarar(record.getMessage()),
        }
        if hasattr(record, "execucao_id"):
            linha["execucao_id"] = record.execucao_id
        if record.exc_info:
            linha["excecao"] = mascarar(self.formatException(record.exc_info))
        return json.dumps(linha, ensure_ascii=False)


def configurar_logs(nivel: str = "INFO") -> None:
    saida = logging.StreamHandler(sys.stdout)
    saida.setFormatter(FormatadorJson())
    raiz = logging.getLogger()
    raiz.handlers[:] = [saida]
    raiz.setLevel(nivel)
