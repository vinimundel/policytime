"""Versioned corpus, clause graph, response cache, and conservative cost ledger."""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "corpora",
        sa.Column("version", sa.String(64), primary_key=True),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("embedding_identity", sa.String(250), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "active_corpus",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("version", sa.String(64), sa.ForeignKey("corpora.version"), nullable=False),
        sa.CheckConstraint("id = 1", name="single_active_corpus"),
    )
    op.create_table(
        "clauses",
        sa.Column(
            "corpus_version", sa.String(64), sa.ForeignKey("corpora.version"), primary_key=True
        ),
        sa.Column("id", sa.String(96), primary_key=True),
        sa.Column("document_id", sa.String(96), nullable=False),
        sa.Column("topic", sa.String(30), nullable=False),
        sa.Column("rule_key", sa.String(96), nullable=False),
        sa.Column("starts_on", sa.Date, nullable=False),
        sa.Column("ends_on", sa.Date),
        sa.Column("countries", postgresql.ARRAY(sa.String(2)), nullable=False),
        sa.Column("employment_types", postgresql.ARRAY(sa.String(20)), nullable=False),
        sa.Column("passage", sa.Text, nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.CheckConstraint("ends_on IS NULL OR ends_on > starts_on", name="valid_effective_period"),
    )
    op.execute(
        "CREATE INDEX clauses_lexical ON clauses USING gin (to_tsvector('english', passage))"
    )
    op.create_table(
        "relationships",
        sa.Column("corpus_version", sa.String(64), primary_key=True),
        sa.Column("source_id", sa.String(96), primary_key=True),
        sa.Column("target_id", sa.String(96), primary_key=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(
            ["corpus_version", "source_id"], ["clauses.corpus_version", "clauses.id"]
        ),
        sa.ForeignKeyConstraint(
            ["corpus_version", "target_id"], ["clauses.corpus_version", "clauses.id"]
        ),
        sa.CheckConstraint("kind IN ('supersedes', 'overrides')", name="valid_relationship_kind"),
        sa.CheckConstraint("source_id <> target_id", name="no_self_relationship"),
    )
    op.create_table(
        "answer_cache",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_answer_cache_expires_at", "answer_cache", ["expires_at"])
    op.create_table(
        "budget_months",
        sa.Column("month", sa.String(7), primary_key=True),
        sa.Column("spent", sa.Numeric(14, 8), nullable=False),
        sa.Column("reserved", sa.Numeric(14, 8), nullable=False),
        sa.CheckConstraint("spent >= 0 AND reserved >= 0", name="nonnegative_budget"),
    )
    op.create_table(
        "budget_reservations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("month", sa.String(7), sa.ForeignKey("budget_months.month"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 8), nullable=False),
        sa.Column("settled", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in (
        "budget_reservations",
        "budget_months",
        "answer_cache",
        "relationships",
        "clauses",
        "active_corpus",
        "corpora",
    ):
        op.drop_table(table)
