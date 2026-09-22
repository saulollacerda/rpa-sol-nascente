"""Persistência das execuções — ADR-004. SQLite em memória, sem arquivo."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.erros import ExecucaoDuplicada, TransicaoInvalida
from app.domain.execucao import ParametrosConsulta, StatusExecucao, chave_idempotencia
from app.infra.db import RepositorioSQL, criar_engine, criar_tabelas

S = StatusExecucao
AGORA = datetime(2026, 9, 22, 15, 12, tzinfo=UTC)


def params(**kw) -> ParametrosConsulta:
    base = dict(
        data_base="202607",
        segmento=4,
        ufs=("PI", "MA"),
        cnpj_administradora="45441789",
        top_concorrentes=3,
        destinatario="5586999990000",
    )
    return ParametrosConsulta(**{**base, **kw})


@pytest.fixture
def repo():
    engine = criar_engine("sqlite:///:memory:")
    criar_tabelas(engine)
    return RepositorioSQL(engine)


def criar(repo, **kw):
    p = params(**kw)
    return repo.criar(p, chave_idempotencia(p), AGORA)


def avancar(repo, execucao_id, *passos):
    for status in passos:
        repo.atualizar(execucao_id, status, AGORA)


class TestCriacao:
    def test_nasce_pendente_na_primeira_tentativa(self, repo):
        execucao = criar(repo)
        assert execucao.id > 0
        assert execucao.status is S.PENDENTE
        assert execucao.tentativas == 1
        assert execucao.criado_em == AGORA

    def test_parametros_voltam_iguais(self, repo):
        execucao = criar(repo)
        assert repo.obter(execucao.id).parametros == params()

    def test_chave_repetida_e_barrada_pelo_banco(self, repo):
        """A unique constraint é o mecanismo anti-duplicidade do ADR-004."""
        primeira = criar(repo)
        with pytest.raises(ExecucaoDuplicada) as erro:
            criar(repo)
        assert erro.value.execucao_id == primeira.id

    def test_repositorio_continua_utilizavel_depois_da_duplicata(self, repo):
        criar(repo)
        with pytest.raises(ExecucaoDuplicada):
            criar(repo)
        assert criar(repo, ufs=("PI",)).id > 0


class TestConsulta:
    def test_buscar_por_chave(self, repo):
        execucao = criar(repo)
        assert repo.buscar_por_chave(execucao.chave).id == execucao.id

    def test_inexistentes(self, repo):
        assert repo.obter(999) is None
        assert repo.buscar_por_chave("0" * 64) is None

    def test_listar_da_mais_recente_para_a_mais_antiga(self, repo):
        ids = [criar(repo, top_concorrentes=n).id for n in (1, 2, 3)]
        assert [e.id for e in repo.listar(limite=10)] == ids[::-1]

    def test_listar_respeita_o_limite(self, repo):
        for n in range(5):
            criar(repo, top_concorrentes=n + 1)
        assert len(repo.listar(limite=2)) == 2


class TestAtualizacao:
    def test_percorre_o_caminho_feliz(self, repo):
        execucao = criar(repo)
        avancar(repo, execucao.id, S.COLETANDO, S.PROCESSANDO)
        repo.atualizar(
            execucao.id,
            S.MENSAGEM_GERADA,
            AGORA,
            mensagem_gerada="📊 RADAR",
            dados_encontrados={"pracas": [{"uf": "PI", "share": 95.7}]},
        )
        avancar(repo, execucao.id, S.ENVIANDO)
        enviado = repo.atualizar(
            execucao.id, S.ENVIADO, AGORA, enviado_em=AGORA, provider_message_id="wamid.X"
        )

        assert enviado.status is S.ENVIADO
        assert enviado.mensagem_gerada == "📊 RADAR"
        assert enviado.dados_encontrados["pracas"][0]["share"] == 95.7
        assert enviado.provider_message_id == "wamid.X"
        assert enviado.enviado_em == AGORA

    def test_atualizado_em_avanca(self, repo):
        execucao = criar(repo)
        depois = AGORA + timedelta(seconds=30)
        assert repo.atualizar(execucao.id, S.COLETANDO, depois).atualizado_em == depois

    def test_transicao_invalida_e_recusada_e_nada_muda(self, repo):
        """Pular direto para ENVIADO seria enviar sem ter coletado."""
        execucao = criar(repo)
        with pytest.raises(TransicaoInvalida):
            repo.atualizar(execucao.id, S.ENVIADO, AGORA)
        assert repo.obter(execucao.id).status is S.PENDENTE

    def test_falha_registra_tipo_e_descricao(self, repo):
        execucao = criar(repo)
        avancar(repo, execucao.id, S.COLETANDO)
        falha = repo.atualizar(
            execucao.id,
            S.FALHA_COLETA,
            AGORA,
            erro_tipo="ColetaError",
            erro_descricao="site do BCB indisponível",
        )
        assert (falha.erro_tipo, falha.erro_descricao) == (
            "ColetaError",
            "site do BCB indisponível",
        )

    def test_campo_desconhecido_e_erro_de_programacao(self, repo):
        execucao = criar(repo)
        with pytest.raises(TypeError, match="campo_inventado"):
            repo.atualizar(execucao.id, S.COLETANDO, AGORA, campo_inventado=1)

    def test_execucao_inexistente(self, repo):
        with pytest.raises(LookupError):
            repo.atualizar(999, S.COLETANDO, AGORA)


class TestRetentativa:
    def test_reabre_a_falha_limpando_o_erro(self, repo):
        execucao = criar(repo)
        avancar(repo, execucao.id, S.COLETANDO)
        repo.atualizar(
            execucao.id, S.FALHA_COLETA, AGORA, erro_tipo="ColetaError", erro_descricao="x"
        )

        reaberta = repo.retentar(execucao.id, AGORA)

        assert reaberta.status is S.PENDENTE
        assert reaberta.tentativas == 2
        assert reaberta.erro_tipo is None and reaberta.erro_descricao is None

    def test_nao_reabre_o_que_foi_enviado(self, repo):
        execucao = criar(repo)
        avancar(repo, execucao.id, S.COLETANDO, S.PROCESSANDO, S.MENSAGEM_GERADA, S.ENVIANDO)
        avancar(repo, execucao.id, S.ENVIADO)
        with pytest.raises(TransicaoInvalida):
            repo.retentar(execucao.id, AGORA)


def test_banco_em_arquivo(tmp_path):
    """O caminho real: arquivo em disco, que sobrevive ao processo."""
    url = f"sqlite:///{tmp_path / 'execucoes.db'}"
    engine = criar_engine(url)
    criar_tabelas(engine)
    execucao = criar(RepositorioSQL(engine))

    outro = RepositorioSQL(criar_engine(url))
    assert outro.obter(execucao.id).parametros == params()
