import hashlib
import math
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from policytime.adapters.database import (
    BudgetMonthRow,
    CacheRow,
    ClauseRow,
    PostgresCorpusRepository,
    ReservationRow,
    connect_database,
    publish_corpus,
)
from policytime.adapters.operations import PostgresBudgetLedger, PostgresCache
from policytime.adapters.retrieval import PostgresRetriever
from policytime.application.contracts import AskCommand, BudgetExceeded
from policytime.domain.models import Context, Country, Employment

pytestmark = pytest.mark.integration


class FixtureEmbedder:
    """Deterministic test vectors; not used in benchmarks or production."""

    identity = "integration-test-hash-v1"

    def encode(self, texts):
        result = []
        for text in texts:
            vector = [0.0] * 384
            for word in text.lower().split():
                position = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % 384
                vector[position] += 1
            norm = math.sqrt(sum(value * value for value in vector))
            result.append([value / norm for value in vector])
        return result


@pytest.fixture(scope="module")
def engine():
    url = os.environ.get("POLICYTIME_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set POLICYTIME_TEST_DATABASE_URL to run real PostgreSQL tests.")
    if not url.rsplit("/", 1)[-1].endswith("_test"):
        pytest.fail("Integration database name must end with _test.")
    old = os.environ.get("POLICYTIME_DATABASE_URL")
    os.environ["POLICYTIME_DATABASE_URL"] = url
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    if old is None:
        os.environ.pop("POLICYTIME_DATABASE_URL")
    else:
        os.environ["POLICYTIME_DATABASE_URL"] = old
    engine = connect_database(url)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clear_operational_tables(engine):
    with Session(engine) as session, session.begin():
        for model in (ReservationRow, BudgetMonthRow, CacheRow):
            session.execute(delete(model))


def test_idempotent_publication_and_filtered_search(engine, corpus):
    encoder = FixtureEmbedder()
    publish_corpus(engine, corpus, encoder)
    publish_corpus(engine, corpus, encoder)
    assert PostgresCorpusRepository(engine).snapshot() == corpus
    with Session(engine) as session:
        rows = session.scalars(
            select(ClauseRow).where(ClauseRow.corpus_version == corpus.version)
        ).all()
        assert len(rows) == len(corpus.clauses)
    context = Context(
        expense_date=date(2026, 7, 15), country=Country.BR, employment_type=Employment.CONTRACTOR
    )
    hits = PostgresRetriever(engine, encoder).search(corpus, "lodging hotel reimbursement", context)
    assert hits
    by_id = {clause.id: clause for clause in corpus.clauses}
    assert all(by_id[hit.clause_id].applies_to(context) for hit in hits)


def test_failed_publication_keeps_the_previous_snapshot(engine, corpus):
    publish_corpus(engine, corpus, FixtureEmbedder())

    class BrokenEmbedder:
        identity = "broken-test"

        def encode(self, texts):
            raise RuntimeError("Encoder unavailable")

    with pytest.raises(RuntimeError):
        publish_corpus(engine, corpus.model_copy(update={"version": "b" * 64}), BrokenEmbedder())
    assert PostgresCorpusRepository(engine).snapshot().version == corpus.version


def test_budget_reservations_are_atomic_and_persist_across_instances(engine):
    ledger = PostgresBudgetLedger(engine, Decimal("0.10"))

    def reserve(_):
        try:
            return ledger.reserve(Decimal("0.04"))
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=6) as executor:
        identifiers = [value for value in executor.map(reserve, range(6)) if value is not None]
    assert len(identifiers) == 2
    second = PostgresBudgetLedger(engine, Decimal("0.10"))
    with pytest.raises(BudgetExceeded):
        second.reserve(Decimal("0.04"))
    second.settle(identifiers[0], Decimal("0.005"))
    second.settle(identifiers[0], Decimal("0.005"))
    second.settle(identifiers[1], None)
    assert Decimal(second.summary()["spent_usd"]) == Decimal("0.045")
    assert Decimal(second.summary()["reserved_usd"]) == 0


def test_persistent_response_cache(engine, service):
    response = service.ask(
        AskCommand(
            question="What is the hotel limit?",
            expense_date=date(2026, 7, 1),
            country=Country.BR,
            employment_type=Employment.EMPLOYEE,
        )
    )
    cache = PostgresCache(engine)
    cache.put("a" * 64, response)
    assert PostgresCache(engine).get("a" * 64) == response
    assert cache.get("b" * 64) is None
    PostgresCache(engine, ttl_seconds=-1).put("c" * 64, response)
    assert cache.get("c" * 64) is None
