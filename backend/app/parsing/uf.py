"""Parser dos dados por unidade da federação (administradora x segmento x UF)."""

from pathlib import Path

from app.domain.modelos import RegistroUF
from app.parsing.leitor_zip import ler_csv_do_zip
from app.parsing.normalizacao import para_inteiro, para_texto, raiz_cnpj

SUFIXO = "Consorcios_UF.csv"


def ler_uf(caminho_zip: Path) -> list[RegistroUF]:
    return [_converter(linha) for linha in ler_csv_do_zip(caminho_zip, SUFIXO)]


def _converter(linha: dict[str, str]) -> RegistroUF:
    return RegistroUF(
        nome_administradora=para_texto(linha.get("Nome_da_Administradora")),
        cnpj_raiz=raiz_cnpj(linha.get("CNPJ_da_Administradora")),
        data_base=para_texto(linha.get("Data_base")),
        segmento=para_inteiro(linha.get("Código_do_segmento")),
        uf=para_texto(linha.get("Unidade_da_Federação_do_consorciado")),
        contemplados_lance=para_inteiro(
            linha.get("Quantidade_de_consorciados_ativos_contemplados_por_lance")
        ),
        contemplados_sorteio=para_inteiro(
            linha.get("Quantidade_de_consorciados_ativos_contemplados_por_sorteio")
        ),
        nao_contemplados=para_inteiro(
            linha.get("Quantidade_de_consorciados_ativos_não_contemplados")
        ),
        contemplados_lance_no_trimestre=para_inteiro(
            linha.get("Quantidade_de_consorciados_ativos_contemplados_por_lance_no_trimestre")
        ),
        contemplados_sorteio_no_trimestre=para_inteiro(
            linha.get("Quantidade_de_consorciados_ativos_contemplados_por_sorteio_no_trimestre")
        ),
        adesoes_no_trimestre=para_inteiro(linha.get("Quantidade_de_adesões_no_trimestre")),
    )
