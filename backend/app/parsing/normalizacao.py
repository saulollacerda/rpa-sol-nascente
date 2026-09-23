"""Normalização dos campos dos CSV do BCB.

Os arquivos vêm em windows-1252, com separador ponto e vírgula, decimal por
vírgula, nomes preenchidos com espaços e CNPJ apenas com a raiz. Ver ADR-002.
"""


def para_texto(valor: str | None) -> str:
    """Remove o padding de espaços herdado do formato de largura fixa."""
    return valor.strip() if valor else ""


def para_inteiro(valor: str | None) -> int:
    """Campo ausente ou ilegível vira zero — informação incompleta é prevista."""
    if not valor:
        return 0
    try:
        return int(valor.strip())
    except ValueError:
        return 0


def para_decimal(valor: str | None) -> float:
    """O BCB usa vírgula como separador decimal."""
    if not valor:
        return 0.0
    try:
        return float(valor.strip().replace(",", "."))
    except ValueError:
        return 0.0


def raiz_cnpj(valor: str | None) -> str:
    """Mantém como texto: converter para inteiro perderia os zeros à esquerda."""
    digitos = "".join(c for c in (valor or "") if c.isdigit())
    return digitos.zfill(8)
