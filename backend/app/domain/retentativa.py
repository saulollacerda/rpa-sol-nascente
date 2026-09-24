"""Política de retentativa para falhas transitórias da coleta."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PoliticaDeRetentativa:
    """Quantas vezes tentar e quanto esperar entre as tentativas (backoff exponencial).

    Com os padrões: 3 tentativas, esperando 5 s e depois 15 s.
    """

    tentativas: int = 3
    espera_inicial: float = 5.0
    fator: float = 3.0

    def __post_init__(self) -> None:
        if self.tentativas < 1:
            raise ValueError("é preciso ao menos uma tentativa")
        if self.espera_inicial < 0:
            raise ValueError("a espera não pode ser negativa")
        if self.fator < 1:
            raise ValueError("o fator não pode encurtar as esperas")

    def esperas(self) -> list[float]:
        """Esperas antes da 2ª, 3ª… tentativa. Não há espera depois da última."""
        return [self.espera_inicial * self.fator**i for i in range(self.tentativas - 1)]
