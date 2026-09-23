"""Formatação em convenção brasileira, para leitura no WhatsApp.

Sem locale do sistema operacional: o resultado não pode variar conforme a
máquina (ou o container) onde a aplicação roda.
"""

import re
import unicodedata

MESES = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)  # fmt: skip

UFS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia",
    "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe",
    "TO": "Tocantins",
}  # fmt: skip

# "no Paraná", "em Minas", "na Bahia": o artigo acompanha o nome do estado.
_PREPOSICAO = {sigla: "no" for sigla in UFS} | {
    "BA": "na", "PB": "na",
    "AL": "em", "GO": "em", "MG": "em", "PE": "em", "RO": "em",
    "RR": "em", "SC": "em", "SE": "em", "SP": "em",
}  # fmt: skip

# Tokens that only say "consortium administrator, Ltd." in the BCB's abbreviations.
_RUIDO_NO_NOME = {
    "ADM", "ADMINISTRADORA", "ADMINISTRACAO", "CONS", "CONSORCIO", "CONSORCIOS",
    "NAC", "NACIONAL", "LTDA", "LTD", "SA", "S/A", "S", "A", "DE",
}  # fmt: skip


def formatar_inteiro(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def formatar_percentual(valor: float) -> str:
    return f"{valor:.1f}%".replace(".", ",")


def formatar_compacto(valor: int) -> str:
    if valor >= 1_000_000:
        return f"{valor / 1_000_000:.2f} mi".replace(".", ",")
    if valor >= 1_000:
        return f"{valor / 1_000:.0f} mil"
    return str(valor)


def formatar_pontos(valor: float) -> str:
    """Diferença entre dois percentuais, com sinal: '+11,3 p.p.'."""
    return f"{valor:+.1f} p.p.".replace(".", ",", 1)


def formatar_data_base(data_base: str) -> str:
    """'202606' -> 'Junho/2026'. Formato inesperado volta como veio."""
    if len(data_base) != 6 or not data_base.isdigit():
        return data_base
    ano, mes = data_base[:4], int(data_base[4:])
    if not 1 <= mes <= 12:
        return data_base
    return f"{MESES[mes - 1]}/{ano}"


def nome_da_uf(sigla: str) -> str:
    return UFS.get(sigla, sigla)


def formatar_mes_curto(data_base: str) -> str:
    """'202606' -> 'Jun/2026'. Formato inesperado volta como veio."""
    completo = formatar_data_base(data_base)
    if completo == data_base:
        return data_base
    mes, ano = completo.split("/")
    return f"{mes[:3]}/{ano}"


def formatar_trimestre(data_base: str) -> str:
    """'202606' -> '2º trimestre/2026'. Formato inesperado volta como veio."""
    completo = formatar_data_base(data_base)
    if completo == data_base:
        return data_base
    return f"{(int(data_base[4:]) - 1) // 3 + 1}º trimestre/{data_base[:4]}"


def com_preposicao(sigla: str) -> str:
    return f"{_PREPOSICAO.get(sigla, 'em')} {sigla}"


def nome_curto(nome: str) -> str:
    """'ADM CONS NAC HONDA LTDA' -> 'Honda'. Nome só de ruído volta como veio."""
    tokens = [t for t in re.split(r"[\s.]+", nome) if t and _sem_acento(t) not in _RUIDO_NO_NOME]
    if not tokens:
        return nome
    return " ".join(_capitalizar(t) for t in tokens)


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.upper())
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def _capitalizar(token: str) -> str:
    # Short unaccented tokens are acronyms: BB, RCI, XS5.
    if len(token) <= 3 and _sem_acento(token) == token.upper():
        return token.upper()
    return token.capitalize()
