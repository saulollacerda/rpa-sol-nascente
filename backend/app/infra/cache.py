"""Cache em memória com validade — camada de catálogo do ADR-006.

Falha não é guardada: se o site estava fora do ar, a próxima chamada tenta
de novo em vez de repetir o erro até o fim da validade.
"""

import threading
from collections.abc import Callable
from datetime import datetime, timedelta


class CacheComValidade[T]:
    def __init__(
        self,
        carregar: Callable[[], T],
        validade: timedelta,
        relogio: Callable[[], datetime],
    ) -> None:
        self._carregar = carregar
        self._validade = validade
        self._agora = relogio
        self._valor: T | None = None
        self._carregado_em: datetime | None = None
        # Dois acessos simultâneos com o cache vencido não disparam duas coletas.
        self._trava = threading.Lock()

    @property
    def carregado_em(self) -> datetime | None:
        return self._carregado_em

    def obter(self) -> T:
        with self._trava:
            if self._vencido():
                self._valor = self._carregar()
                self._carregado_em = self._agora()
            return self._valor  # type: ignore[return-value]

    def invalidar(self) -> None:
        with self._trava:
            self._carregado_em = None

    def _vencido(self) -> bool:
        return self._carregado_em is None or self._agora() - self._carregado_em >= self._validade
