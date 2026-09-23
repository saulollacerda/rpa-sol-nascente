"""Correspondência entre as periodicidades dos dois datasets."""

from collections.abc import Iterable


def data_base_uf_para(data_base: str, disponiveis: Iterable[str]) -> str | None:
    """Trimestre de UF mais recente até a data-base escolhida.

    O consolidado é mensal e o de UF é trimestral: para Julho/2026 usa-se
    Junho/2026. None quando a data é anterior a todos os trimestres publicados.
    """
    anteriores = [d for d in disponiveis if d <= data_base]
    return max(anteriores) if anteriores else None
