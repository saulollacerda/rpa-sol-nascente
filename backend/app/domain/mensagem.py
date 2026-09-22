"""Composição da mensagem de WhatsApp — PRD, seção 6.

Texto puro com emojis: tabelas e markdown quebram no aplicativo.
"""

from datetime import datetime

from app.domain.analise import Concorrente, PosicaoNacional, PosicaoNaPraca
from app.domain.formatacao import (
    formatar_compacto,
    formatar_data_base,
    formatar_inteiro,
    formatar_percentual,
    nome_da_uf,
)
from app.domain.modelos import SEGMENTOS
from app.domain.relatorio import Relatorio


def compor_mensagem(relatorio: Relatorio, gerado_em: datetime) -> str:
    """Recebe o horário por argumento para continuar sendo função pura."""
    if not relatorio.tem_resultado:
        raise ValueError("relatório sem resultado não gera mensagem")

    blocos = [_cabecalho(relatorio)]
    if relatorio.pracas:
        blocos.append(_pracas(relatorio.pracas))
        blocos.append(_oportunidade(relatorio))
    if relatorio.recorte_uf_indisponivel:
        blocos.append(
            "⚠️ Esta data-base não tem recorte por UF — o BCB publica esse "
            "dado apenas trimestralmente."
        )
    if relatorio.ufs_sem_resultado:
        siglas = ", ".join(relatorio.ufs_sem_resultado)
        blocos.append(f"ℹ️ Administradora sem atuação neste segmento em: {siglas}")
    if relatorio.nacional:
        blocos.append(_nacional(relatorio.nacional))
    blocos.append(f"Fonte: Banco Central do Brasil · gerado em {gerado_em:%d/%m/%Y %H:%M}")

    return "\n\n".join(blocos)


def _cabecalho(relatorio: Relatorio) -> str:
    linhas = [
        "📊 RADAR DE CONSÓRCIO",
        f"Segmento {relatorio.segmento} ({SEGMENTOS.get(relatorio.segmento, '—')})",
    ]
    datas = []
    if relatorio.pracas:
        datas.append(f"Praças: {formatar_data_base(relatorio.pracas[0].data_base)}")
    if relatorio.nacional:
        datas.append(f"Nacional: {formatar_data_base(relatorio.nacional.data_base)}")
    if datas:
        linhas.append("Data-base · " + " · ".join(datas))
    return "\n".join(linhas)


def _pracas(pracas: tuple[PosicaoNaPraca, ...]) -> str:
    return "🏍️ SUAS PRAÇAS\n\n" + "\n\n".join(_praca(p) for p in pracas)


def _praca(p: PosicaoNaPraca) -> str:
    linhas = [
        f"{nome_da_uf(p.uf).upper()} — {formatar_inteiro(p.ativos_praca)} consorciados "
        f"ativos · {p.administradoras_na_praca} administradoras",
        f"  {p.nome_administradora}",
        f"    Ativos: {formatar_inteiro(p.ativos)} ({formatar_percentual(p.share)} da praça)",
        f"    Adesões no trimestre: {formatar_inteiro(p.adesoes_no_trimestre)}",
        f"    Contemplados: {formatar_inteiro(p.contemplados_no_trimestre)} "
        f"({formatar_inteiro(p.contemplados_lance_no_trimestre)} lance · "
        f"{formatar_inteiro(p.contemplados_sorteio_no_trimestre)} sorteio)",
    ]
    if p.concorrentes:
        linhas.append(f"  Concorrência: {_lista(p.concorrentes)}")
    return "\n".join(linhas)


def _oportunidade(relatorio: Relatorio) -> str:
    quantidade = len(relatorio.pracas)
    onde = "na praça" if quantidade == 1 else f"nas {quantidade} praças"
    return (
        "🎯 OPORTUNIDADE\n"
        f"{formatar_inteiro(relatorio.contemplados_no_trimestre)} consumidores contemplados "
        f"{onde} neste trimestre — carta de crédito disponível para aquisição."
    )


def _nacional(n: PosicaoNacional) -> str:
    linhas = [
        "🇧🇷 CONTEXTO NACIONAL",
        f"{n.nome_administradora}: {formatar_percentual(n.share)} do mercado "
        f"({formatar_compacto(n.cotas_ativas)} de {formatar_compacto(n.cotas_ativas_mercado)} "
        f"cotas ativas · {n.administradoras_no_segmento} administradoras)",
        f"Taxa de administração: {formatar_percentual(n.taxa_administracao)} · "
        f"{formatar_inteiro(n.grupos_ativos)} grupos ativos",
    ]
    if n.concorrentes:
        linhas.append(f"Seguida por {_lista(n.concorrentes)}")
    return "\n".join(linhas)


def _lista(concorrentes: tuple[Concorrente, ...]) -> str:
    return " · ".join(
        f"{c.nome_administradora} {formatar_percentual(c.share)}" for c in concorrentes
    )
