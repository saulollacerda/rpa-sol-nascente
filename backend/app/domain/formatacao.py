"""Formatação em convenção brasileira, para leitura no WhatsApp.

Sem locale do sistema operacional: o resultado não pode variar conforme a
máquina (ou o container) onde a aplicação roda.
"""

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
