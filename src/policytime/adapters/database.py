"""PostgreSQL schema and transactional corpus publication."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from policytime.application.ports import Embedder
from policytime.domain.models import Corpus
from policytime.domain.resolution import validate_corpus


class Base(DeclarativeBase):
    pass


class CorpusRow(Base):
    __tablename__ = "corpora"
    version: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    embedding_identity: Mapped[str] = mapped_column(String(250))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ActiveCorpusRow(Base):
    __tablename__ = "active_corpus"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(ForeignKey("corpora.version"))
    __table_args__ = (CheckConstraint("id = 1", name="single_active_corpus"),)


class ClauseRow(Base):
    __tablename__ = "clauses"
    corpus_version: Mapped[str] = mapped_column(ForeignKey("corpora.version"), primary_key=True)
    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(96))
    topic: Mapped[str] = mapped_column(String(30))
    rule_key: Mapped[str] = mapped_column(String(96))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    countries: Mapped[list[str]] = mapped_column(ARRAY(String(2)))
    employment_types: Mapped[list[str]] = mapped_column(ARRAY(String(20)))
    passage: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))
    __table_args__ = (
        CheckConstraint("ends_on IS NULL OR ends_on > starts_on", name="valid_effective_period"),
    )


class RelationshipRow(Base):
    __tablename__ = "relationships"
    corpus_version: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    target_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    __table_args__ = (
        ForeignKeyConstraint(
            ["corpus_version", "source_id"], ["clauses.corpus_version", "clauses.id"]
        ),
        ForeignKeyConstraint(
            ["corpus_version", "target_id"], ["clauses.corpus_version", "clauses.id"]
        ),
        CheckConstraint("kind IN ('supersedes', 'overrides')", name="valid_relationship_kind"),
        CheckConstraint("source_id <> target_id", name="no_self_relationship"),
    )


class CacheRow(Base):
    __tablename__ = "answer_cache"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class BudgetMonthRow(Base):
    __tablename__ = "budget_months"
    month: Mapped[str] = mapped_column(String(7), primary_key=True)
    spent: Mapped[Decimal] = mapped_column(Numeric(14, 8), default=Decimal(0))
    reserved: Mapped[Decimal] = mapped_column(Numeric(14, 8), default=Decimal(0))
    __table_args__ = (CheckConstraint("spent >= 0 AND reserved >= 0", name="nonnegative_budget"),)


class ReservationRow(Base):
    __tablename__ = "budget_reservations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    month: Mapped[str] = mapped_column(ForeignKey("budget_months.month"))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 8))
    settled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def connect_database(url: str) -> Engine:
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=4,
        max_overflow=0,
        connect_args={"connect_timeout": 5, "options": "-c statement_timeout=10000"},
    )


class PostgresCorpusRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def snapshot(self) -> Corpus:
        with Session(self.engine) as session:
            payload = session.scalar(
                select(CorpusRow.payload).join(
                    ActiveCorpusRow,
                    ActiveCorpusRow.version == CorpusRow.version,
                )
            )
        if payload is None:
            raise RuntimeError("No active corpus. Run policytime ingest first.")
        return Corpus.model_validate(payload)


def publish_corpus(engine: Engine, corpus: Corpus, embedder: Embedder) -> None:
    validate_corpus(corpus)
    embeddings = embedder.encode([f"{clause.topic}: {clause.text}" for clause in corpus.clauses])
    if len(embeddings) != len(corpus.clauses) or any(len(vector) != 384 for vector in embeddings):
        raise ValueError("Expected one 384-dimensional embedding per clause.")
    with Session(engine) as session, session.begin():
        session.execute(text("SELECT pg_advisory_xact_lock(730017)"))
        existing = session.get(CorpusRow, corpus.version)
        if existing is not None and existing.embedding_identity != embedder.identity:
            raise ValueError("This corpus fingerprint already uses a different embedding model.")
        if existing is None:
            _insert_corpus(session, corpus, embedder.identity, embeddings)
        session.execute(
            insert(ActiveCorpusRow)
            .values(id=1, version=corpus.version)
            .on_conflict_do_update(index_elements=["id"], set_={"version": corpus.version})
        )


def _insert_corpus(
    session: Session,
    corpus: Corpus,
    embedding_identity: str,
    embeddings: list[list[float]],
) -> None:
    session.add(
        CorpusRow(
            version=corpus.version,
            payload=corpus.model_dump(mode="json"),
            embedding_identity=embedding_identity,
            created_at=datetime.now(UTC),
        )
    )
    session.flush()
    for clause, vector in zip(corpus.clauses, embeddings, strict=True):
        session.add(
            ClauseRow(
                corpus_version=corpus.version,
                id=clause.id,
                document_id=clause.document_id,
                topic=clause.topic.value,
                rule_key=clause.rule_key,
                starts_on=clause.period.start,
                ends_on=clause.period.end,
                countries=[item.value for item in clause.scope.countries],
                employment_types=[item.value for item in clause.scope.employment_types],
                passage=clause.text,
                embedding=vector,
            )
        )
    session.flush()
    for clause in corpus.clauses:
        for relationship in clause.relationships:
            session.add(
                RelationshipRow(
                    corpus_version=corpus.version,
                    source_id=clause.id,
                    target_id=relationship.target_id,
                    kind=relationship.kind,
                )
            )
    session.flush()
