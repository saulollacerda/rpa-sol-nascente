"""Persistência das execuções em SQLite via SQLAlchemy — ver ADR-004."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Engine,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    inspect,
    make_url,
    select,
    text,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from app.domain.erros import ExecucaoDuplicada
from app.domain.execucao import (
    EM_ANDAMENTO,
    Execucao,
    ParametrosConsulta,
    StatusExecucao,
    validar_transicao,
)

CAMPOS_ATUALIZAVEIS = frozenset(
    {
        "dados_encontrados",
        "mensagem_gerada",
        "enviado_em",
        "provider_message_id",
        "erro_tipo",
        "erro_descricao",
    }
)


class Base(DeclarativeBase):
    pass


_EM_ANDAMENTO_SQL = text(
    "status IN (" + ", ".join(f"'{s.value}'" for s in sorted(EM_ANDAMENTO)) + ")"
)


class ExecucaoRow(Base):
    __tablename__ = "execucoes"
    __table_args__ = (
        # Unique só entre as execuções em andamento (ADR-010): é o banco, e não a
        # disciplina do código, que barra o clique duplo — e o reenvio vira linha nova.
        Index(
            "uq_execucoes_chave_em_andamento",
            "parametros_hash",
            unique=True,
            sqlite_where=_EM_ANDAMENTO_SQL,
            postgresql_where=_EM_ANDAMENTO_SQL,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parametros_hash: Mapped[str] = mapped_column(String(64), index=True)
    parametros: Mapped[dict[str, Any]] = mapped_column(JSON)
    destinatario: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(24), index=True)
    tentativas: Mapped[int] = mapped_column(Integer, default=1)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dados_encontrados: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    mensagem_gerada: Mapped[str | None] = mapped_column(Text, nullable=True)
    enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    erro_tipo: Mapped[str | None] = mapped_column(String(64), nullable=True)
    erro_descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    origem_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


def criar_engine(url: str) -> Engine:
    """Engine SQLite utilizável a partir das threads do BackgroundTasks."""
    argumentos: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
    banco = make_url(url).database
    if banco in (None, "", ":memory:"):
        argumentos["poolclass"] = StaticPool  # mesma conexão, senão cada uma vê um banco vazio
    else:
        Path(banco).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, **argumentos)


def criar_tabelas(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    _migrar(engine)


def _migrar(engine: Engine) -> None:
    """Leva bancos anteriores ao ADR-010 ao esquema atual. Idempotente."""
    inspetor = inspect(engine)
    with engine.begin() as conexao:
        colunas = {c["name"] for c in inspetor.get_columns("execucoes")}
        if "origem_id" not in colunas:
            conexao.execute(text("ALTER TABLE execucoes ADD COLUMN origem_id INTEGER"))
        for indice in inspetor.get_indexes("execucoes"):
            if indice["name"] == "ix_execucoes_parametros_hash" and indice["unique"]:
                conexao.execute(text("DROP INDEX ix_execucoes_parametros_hash"))
    for indice in ExecucaoRow.__table__.indexes:
        indice.create(engine, checkfirst=True)


class RepositorioSQL:
    def __init__(self, engine: Engine) -> None:
        self._sessoes = sessionmaker(engine, expire_on_commit=False)

    def criar(
        self,
        parametros: ParametrosConsulta,
        chave: str,
        agora: datetime,
        origem: Execucao | None = None,
    ) -> Execucao:
        row = ExecucaoRow(
            parametros_hash=chave,
            parametros=parametros.como_dict(),
            destinatario=parametros.destinatario,
            status=StatusExecucao.PENDENTE.value,
            tentativas=1,
            criado_em=agora,
            atualizado_em=agora,
            dados_encontrados=origem.dados_encontrados if origem else None,
            mensagem_gerada=origem.mensagem_gerada if origem else None,
            origem_id=origem.id if origem else None,
        )
        try:
            with self._sessoes.begin() as sessao:
                sessao.add(row)
        except IntegrityError as erro:
            existente = self.buscar_por_chave(chave)
            if existente is None:
                raise
            raise ExecucaoDuplicada(existente.id) from erro
        return _para_dominio(row)

    def obter(self, execucao_id: int) -> Execucao | None:
        with self._sessoes() as sessao:
            row = sessao.get(ExecucaoRow, execucao_id)
            return _para_dominio(row) if row else None

    def buscar_por_chave(self, chave: str) -> Execucao | None:
        with self._sessoes() as sessao:
            row = sessao.scalar(
                select(ExecucaoRow)
                .where(ExecucaoRow.parametros_hash == chave)
                .order_by(ExecucaoRow.id.desc())
                .limit(1)
            )
            return _para_dominio(row) if row else None

    def listar(self, limite: int) -> list[Execucao]:
        with self._sessoes() as sessao:
            consulta = select(ExecucaoRow).order_by(ExecucaoRow.id.desc()).limit(limite)
            return [_para_dominio(row) for row in sessao.scalars(consulta)]

    def atualizar(
        self, execucao_id: int, status: StatusExecucao, agora: datetime, **campos: Any
    ) -> Execucao:
        desconhecidos = set(campos) - CAMPOS_ATUALIZAVEIS
        if desconhecidos:
            raise TypeError(f"campos não atualizáveis: {sorted(desconhecidos)}")

        with self._sessoes.begin() as sessao:
            row = _exigir(sessao, execucao_id)
            validar_transicao(StatusExecucao(row.status), status)
            row.status = status.value
            row.atualizado_em = agora
            for campo, valor in campos.items():
                setattr(row, campo, valor)
        return _para_dominio(row)

    def retentar(self, execucao_id: int, agora: datetime) -> Execucao:
        """Reabre uma execução que falhou, na mesma linha.

        Dados e mensagem ficam: numa falha de envio, a retentativa só reenvia.
        """
        with self._sessoes.begin() as sessao:
            row = _exigir(sessao, execucao_id)
            validar_transicao(StatusExecucao(row.status), StatusExecucao.PENDENTE)
            row.status = StatusExecucao.PENDENTE.value
            row.tentativas += 1
            row.atualizado_em = agora
            row.erro_tipo = None
            row.erro_descricao = None
        return _para_dominio(row)


def _exigir(sessao: Session, execucao_id: int) -> ExecucaoRow:
    row = sessao.get(ExecucaoRow, execucao_id)
    if row is None:
        raise LookupError(f"execução {execucao_id} não existe")
    return row


def _utc(valor: datetime | None) -> datetime | None:
    """SQLite não guarda fuso: o que sai sem fuso foi gravado em UTC."""
    if valor is None or valor.tzinfo is not None:
        return valor
    return valor.replace(tzinfo=UTC)


def _para_dominio(row: ExecucaoRow) -> Execucao:
    return Execucao(
        id=row.id,
        chave=row.parametros_hash,
        parametros=ParametrosConsulta.de_dict(row.parametros),
        status=StatusExecucao(row.status),
        tentativas=row.tentativas,
        criado_em=_utc(row.criado_em),
        atualizado_em=_utc(row.atualizado_em),
        dados_encontrados=row.dados_encontrados,
        mensagem_gerada=row.mensagem_gerada,
        enviado_em=_utc(row.enviado_em),
        provider_message_id=row.provider_message_id,
        erro_tipo=row.erro_tipo,
        erro_descricao=row.erro_descricao,
        origem_id=row.origem_id,
    )
