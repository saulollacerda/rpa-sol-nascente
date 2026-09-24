"""Implementações falsas das portas do domínio, para testar o fluxo sem rede."""

from app.domain.erros import ColetaError, ColetaIndisponivel
from app.domain.portas import DadosColetados


class FonteFalsa:
    """Devolve os registros das fixtures reais, ou falha sob demanda."""

    def __init__(self, consolidado, uf, data_base_uf="202606", falhar_com=None, indisponivel_por=0):
        self._dados = DadosColetados(
            data_base_consolidado="202607",
            consolidado=tuple(consolidado),
            data_base_uf=data_base_uf,
            uf=tuple(uf) if uf is not None else None,
        )
        self.falhar_com = falhar_com
        self.indisponivel_por = indisponivel_por  # chamadas que falham antes de responder
        self.chamadas = 0

    def obter(self, data_base: str) -> DadosColetados:
        self.chamadas += 1
        if self.chamadas <= self.indisponivel_por:
            raise ColetaIndisponivel("site do BCB indisponível ou lento demais: timeout")
        if self.falhar_com:
            raise ColetaError(self.falhar_com)
        return self._dados
