"""Parser dos dados consolidados (administradora x segmento)."""

from pathlib import Path

from app.domain.modelos import RegistroConsolidado
from app.parsing.leitor_zip import ler_csv_do_zip
from app.parsing.normalizacao import para_decimal, para_inteiro, para_texto, raiz_cnpj

SUFIXO = "Segmentos_Consolidados.csv"


def ler_consolidado(caminho_zip: Path) -> list[RegistroConsolidado]:
    return [_converter(linha) for linha in ler_csv_do_zip(caminho_zip, SUFIXO)]


def _converter(linha: dict[str, str]) -> RegistroConsolidado:
    return RegistroConsolidado(
        nome_administradora=para_texto(linha.get("Nome_da_Administradora")),
        cnpj_raiz=raiz_cnpj(linha.get("CNPJ_da_Administradora")),
        data_base=para_texto(linha.get("Data_base")),
        segmento=para_inteiro(linha.get("Código_do_segmento")),
        taxa_administracao=para_decimal(linha.get("Taxa_de_administração")),
        grupos_ativos=para_inteiro(linha.get("Quantidade_de_grupos_ativos")),
        cotas_ativas_contempladas=para_inteiro(
            linha.get("Quantidade_acumulada_de_cotas_ativas_contempladas")
        ),
        cotas_ativas_nao_contempladas=para_inteiro(
            linha.get("Quantidade_de_cotas_ativas_não_contempladas")
        ),
        cotas_ativas_contempladas_inadimplentes=para_inteiro(
            linha.get("Quantidade_de_cotas_ativas_contempladas_inadimplentes")
        ),
        cotas_ativas_nao_contempladas_inadimplentes=para_inteiro(
            linha.get("Quantidade_de_cotas_ativas_não_contempladas_inadimplentes")
        ),
    )
