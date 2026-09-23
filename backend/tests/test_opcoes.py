"""Opções do painel: data-bases e administradoras disponíveis — PRD, seção 5."""

from app.domain.opcoes import listar_administradoras

HONDA = "45441789"


def test_uma_entrada_por_administradora(registros_consolidado):
    administradoras = listar_administradoras(registros_consolidado)
    cnpjs = [a.cnpj for a in administradoras]
    assert len(cnpjs) == len(set(cnpjs))
    assert set(cnpjs) == {r.cnpj_raiz for r in registros_consolidado}


def test_segmentos_em_que_cada_uma_atua(registros_consolidado):
    honda = next(a for a in listar_administradoras(registros_consolidado) if a.cnpj == HONDA)
    assert honda.nome == "ADM CONS NAC HONDA LTDA"
    assert 4 in honda.segmentos
    assert list(honda.segmentos) == sorted(honda.segmentos)


def test_ordenadas_pelo_nome(registros_consolidado):
    nomes = [a.nome for a in listar_administradoras(registros_consolidado)]
    assert nomes == sorted(nomes)


def test_lista_vazia():
    assert listar_administradoras([]) == ()
