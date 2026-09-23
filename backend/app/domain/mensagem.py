"""Composição da mensagem de WhatsApp no template do relatório.

Negrito e itálico com * e _, que o WhatsApp renderiza. Métricas que o BCB só
divulga para o país inteiro levam 🇧🇷, para ninguém ler um número nacional
como se fosse das UFs escolhidas.
"""

from app.domain.analise import Alerta, Movimento, PerfilAdministradora, PosicaoUF
from app.domain.formatacao import (
    com_preposicao,
    formatar_inteiro,
    formatar_mes_curto,
    formatar_percentual,
    formatar_pontos,
    formatar_trimestre,
    nome_curto,
    nome_da_uf,
)
from app.domain.relatorio import Relatorio

MAX_LINHAS = 50  # acima disso ninguém lê no celular
MAX_UFS_EM_LINHA = 5  # acima disso, só os extremos de share
EXTREMOS = 3
MAX_UFS_COM_DETALHE = 3  # share da administradora UF a UF...
MAX_ADMS_COM_DETALHE = 3  # ...só quando cabe

TITULOS = {
    1: ("🏠", "IMÓVEIS"),
    2: ("🚚", "VEÍCULOS PESADOS"),
    3: ("🚗", "AUTOMÓVEIS"),
    4: ("🏍️", "MOTOS"),
    5: ("📦", "BENS MÓVEIS"),
    6: ("✈️", "SERVIÇOS TURÍSTICOS"),
}


def compor_mensagem(relatorio: Relatorio) -> str:
    if not relatorio.tem_resultado:
        raise ValueError("relatório sem resultado não gera mensagem")

    blocos = [_cabecalho(relatorio)]
    if relatorio.recorte is None:
        blocos.append(
            "⚠️ Sem recorte por UF até esta data-base: o BCB publica esse dado "
            "apenas trimestralmente."
        )
    else:
        blocos.append(_recorte(relatorio))
        if len(relatorio.posicoes_uf) > 1:
            blocos.append(_por_uf(relatorio))
    blocos.append(_administradoras(relatorio))
    if relatorio.alertas:
        blocos.append("⚠️ *ALERTAS*\n" + "\n".join(_alerta(a) for a in relatorio.alertas))
    if relatorio.data_base_nacional and any(a.nacional for a in relatorio.administradoras):
        mes = formatar_mes_curto(relatorio.data_base_nacional)
        blocos.append(f"_🇧🇷 = dado nacional de {mes}, o BCB não divulga por UF_")

    return "\n\n".join(blocos)


def _cabecalho(r: Relatorio) -> str:
    emoji, titulo = TITULOS.get(r.segmento, ("📊", "SEGMENTO"))
    data_base = r.data_base_uf or r.data_base_nacional or ""
    ufs = ", ".join(r.ufs) if r.ufs else "Brasil"
    adms = ", ".join(nome_curto(a.nome_administradora) for a in r.administradoras)
    return "\n".join(
        [
            f"{emoji} *CONSÓRCIO {titulo} – SEGMENTO {r.segmento}*",
            f"📅 {formatar_mes_curto(data_base)} | Fonte: BCB",
            f"🔎 UFs: *{ufs}*",
            f"🏢 Adms: *{adms}*",
        ]
    )


def _recorte(r: Relatorio) -> str:
    assert r.recorte is not None
    m = r.recorte
    if not r.ufs:
        titulo = "BRASIL"
    elif len(r.ufs) == 1:
        titulo = nome_da_uf(r.ufs[0]).upper()
    else:
        titulo = f"UFs SELECIONADAS: {', '.join(r.ufs)}"
    periodo = formatar_trimestre(r.data_base_uf) if r.data_base_uf else "trimestre"
    return "\n".join(
        [
            f"📍 *{titulo}* _({periodo})_",
            f"- Consorciados ativos: *{formatar_inteiro(m.ativos)}*",
            f"- Adesões: *{formatar_inteiro(m.adesoes)}*",
            f"- Contemplações: {formatar_inteiro(m.contemplados)} "
            f"({formatar_percentual(m.percentual_lance)} por lance)",
            f"- Taxa de exclusão: {formatar_percentual(m.taxa_exclusao)}",
            f"- Administradoras atuando: {m.administradoras}",
        ]
    )


def _por_uf(r: Relatorio) -> str:
    posicoes = list(r.posicoes_uf)
    ocultas = 0
    if len(posicoes) > MAX_UFS_EM_LINHA:
        por_share = sorted(posicoes, key=lambda p: p.alvo.share_carteira, reverse=True)
        posicoes = por_share[:EXTREMOS] + por_share[-EXTREMOS:]
        ocultas = len(por_share) - len(posicoes)

    alvo = nome_curto(r.alvo.nome_administradora)
    linhas = [_linha_uf(p, alvo) for p in posicoes]
    if ocultas:
        linhas.append(f"- _+{ocultas} UFs no total_")
    return "\n".join(linhas)


def _linha_uf(p: PosicaoUF, alvo: str) -> str:
    return (
        f"- *{p.uf}*: {formatar_inteiro(p.ativos)} ativos | "
        f"{formatar_inteiro(p.adesoes)} adesões | "
        f"{alvo} {_seta(p.alvo.share_carteira, p.alvo.share_adesoes)}"
    )


def _administradoras(r: Relatorio) -> str:
    detalhar = (
        1 < len(r.ufs) <= MAX_UFS_COM_DETALHE and len(r.administradoras) <= MAX_ADMS_COM_DETALHE
    )
    blocos = [_administradora(a, r, detalhar) for a in r.administradoras]
    return "🏢 *ADMINISTRADORAS*\n" + "\n\n".join(blocos)


def _administradora(a: PerfilAdministradora, r: Relatorio, detalhar: bool) -> str:
    linhas = [f"*{nome_curto(a.nome_administradora)}*"]
    if r.recorte is not None:
        linhas.append(
            f"  {_onde(r.ufs)}: share {formatar_percentual(a.recorte.share_carteira)} carteira / "
            f"{formatar_percentual(a.recorte.share_adesoes)} adesões "
            f"({formatar_inteiro(a.recorte.adesoes)} adesões)"
        )
        if detalhar:
            linhas.append(
                "  "
                + " | ".join(f"{u.uf} {_seta(u.share_carteira, u.share_adesoes)}" for u in a.por_uf)
            )
    if a.nacional:
        n = a.nacional
        linhas.append(
            f"  🇧🇷 Taxa {formatar_percentual(n.taxa_administracao)} | "
            f"Inad. {formatar_percentual(n.inadimplencia)} | "
            f"Contemp./mês {formatar_percentual(n.contemplacao_mes)}"
        )
        linhas.append(
            f"  🇧🇷 Vendas mês {formatar_inteiro(n.vendas_mes)} | "
            f"Crédito pendente {formatar_inteiro(n.credito_pendente)}"
        )
    return "\n".join(linhas)


def _onde(ufs: tuple[str, ...]) -> str:
    if not ufs:
        return "No Brasil"
    if len(ufs) == 1:
        local = com_preposicao(ufs[0])
        return local[0].upper() + local[1:]
    return "Nas UFs"


def _alerta(a: Alerta) -> str:
    nome = nome_curto(a.nome_administradora)
    if a.tipo == "inadimplencia":
        assert a.inadimplencia is not None
        return f"- 🔴 {nome} com inadimplência de {formatar_percentual(a.inadimplencia)}"
    emoji, verbo = ("📈", "ganhando") if a.tipo == "ganho" else ("📉", "perdendo")
    return f"- {emoji} {nome} {verbo} share {_movimentos(a.movimentos)}"


def _movimentos(movimentos: tuple[Movimento, ...]) -> str:
    """Um lugar: antes → depois. Vários: a variação de cada um, para caber na linha."""
    if len(movimentos) == 1:
        m = movimentos[0]
        return f"{_local(m.uf)} ({_seta(m.antes, m.depois)})"
    partes = [f"{m.uf} ({_variacao(m)})" for m in movimentos]
    partes[0] = f"{_local(movimentos[0].uf)} ({_variacao(movimentos[0])})"
    return ", ".join(partes[:-1]) + " e " + partes[-1]


def _variacao(m: Movimento) -> str:
    # From the rounded shares: the reader sees 63,8% → 75,1% elsewhere, so it must read +11,3.
    return formatar_pontos(round(m.depois, 1) - round(m.antes, 1))


def _local(uf: str | None) -> str:
    return com_preposicao(uf) if uf else "no Brasil"


def _seta(antes: float, depois: float) -> str:
    return f"{formatar_percentual(antes)} → {formatar_percentual(depois)}"
