"""Portas do domínio: o que ele precisa do mundo externo, sem saber quem fornece.

As implementações ficam em infra/ (ver ADR-001 e ADR-003). Os testes do
serviço usam implementações falsas destas mesmas interfaces.
"""

from datetime import datetime
from typing import Any, Protocol

from app.domain.execucao import Execucao, ParametrosConsulta, StatusExecucao


class RepositorioExecucoes(Protocol):
    def criar(self, parametros: ParametrosConsulta, chave: str, agora: datetime) -> Execucao:
        """Levanta ExecucaoDuplicada se a chave já existir."""
        ...

    def obter(self, execucao_id: int) -> Execucao | None: ...

    def buscar_por_chave(self, chave: str) -> Execucao | None: ...

    def listar(self, limite: int) -> list[Execucao]: ...

    def atualizar(
        self, execucao_id: int, status: StatusExecucao, agora: datetime, **campos: Any
    ) -> Execucao:
        """Levanta TransicaoInvalida se a máquina de estados não permitir."""
        ...

    def retentar(self, execucao_id: int, agora: datetime) -> Execucao: ...
