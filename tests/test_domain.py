from datetime import date

import pytest
from pydantic import ValidationError

from policytime.domain.models import (
    Answered,
    Conflict,
    Context,
    Corpus,
    Country,
    EffectivePeriod,
    Employment,
    MoneyLimit,
    Relationship,
    Scope,
    Topic,
)
from policytime.domain.resolution import resolve, validate_corpus


def context(day="2026-07-15", country=Country.BR, employment=Employment.EMPLOYEE):
    return Context(
        expense_date=date.fromisoformat(day), country=country, employment_type=employment
    )


@pytest.mark.parametrize(
    "day,expected",
    [
        ("2025-12-31", False),
        ("2026-01-01", True),
        ("2026-06-30", True),
        ("2026-07-01", False),
    ],
)
def test_effective_interval_is_start_inclusive_end_exclusive(day, expected):
    period = EffectivePeriod(start=date(2026, 1, 1), end=date(2026, 7, 1))
    assert period.contains(date.fromisoformat(day)) is expected


@pytest.mark.parametrize("end", [date(2026, 1, 1), date(2025, 12, 31)])
def test_invalid_period_cannot_be_constructed(end):
    with pytest.raises(ValidationError):
        EffectivePeriod(start=date(2026, 1, 1), end=end)


def test_empty_scope_and_answer_without_evidence_are_invalid():
    with pytest.raises(ValidationError):
        Scope(countries=(), employment_types=(Employment.EMPLOYEE,))
    with pytest.raises(ValidationError):
        MoneyLimit(amount=-10, currency="BRL", unit="per_night")
    with pytest.raises(ValidationError):
        Answered(answer="Approved", context=context(), citations=(), selection=())
    with pytest.raises(ValidationError):
        Conflict(
            context=context(),
            message="Conflict",
            rule_keys=("lodging.main",),
            citations=(),
            selection=(),
        )


def test_domain_values_are_immutable():
    period = EffectivePeriod(start=date(2026, 1, 1))
    with pytest.raises(ValidationError):
        period.start = date(2027, 1, 1)


def test_contractor_override_changes_only_the_limit(corpus):
    clauses = tuple(clause for clause in corpus.clauses if clause.topic == Topic.LODGING)
    decision = resolve(clauses, context(employment=Employment.CONTRACTOR))
    assert {clause.id for clause in decision.selected} == {
        "lodging-br-v2.contractor",
        "lodging-br-v2.documentation",
    }
    assert any(
        step.clause_id == "lodging-br-v2.main" and step.decision == "overridden"
        for step in decision.steps
    )
    assert not decision.conflicts


def test_future_publication_does_not_change_current_applicability(corpus):
    clauses = tuple(clause for clause in corpus.clauses if clause.topic == Topic.LODGING)
    decision = resolve(clauses, context("2026-06-20"))
    assert {clause.id for clause in decision.selected} == {
        "lodging-br-v1.main",
        "lodging-br-v1.documentation",
    }


def test_unresolved_conflict_is_not_resolved_by_newness(corpus):
    clauses = tuple(clause for clause in corpus.clauses if clause.topic == Topic.MEALS)
    decision = resolve(clauses, context("2026-09-01", Country.US))
    assert len(decision.conflicts) == 1
    assert {clause.id for clause in decision.conflicts[0]} == {
        "meals-us-v2.main",
        "meals-us-v2.unresolved-bulletin",
    }


def test_an_employee_conflict_does_not_leak_to_contractors(corpus):
    clauses = tuple(clause for clause in corpus.clauses if clause.topic == Topic.MEALS)
    decision = resolve(clauses, context("2026-09-01", Country.US, Employment.CONTRACTOR))
    assert not decision.conflicts
    assert "meals-us-v2.contractor" in {clause.id for clause in decision.selected}


def replace_clauses(corpus, replacements):
    documents = tuple(
        document.model_copy(
            update={
                "clauses": tuple(
                    replacements.get(clause.id, clause) for clause in document.clauses
                ),
            }
        )
        for document in corpus.documents
    )
    return Corpus(version=corpus.version, documents=documents)


def test_dangling_relationship_is_rejected(corpus):
    first = corpus.clauses[0]
    changed = first.model_copy(
        update={"relationships": (Relationship(kind="overrides", target_id="missing"),)}
    )
    with pytest.raises(ValueError, match="Unknown relationship"):
        validate_corpus(replace_clauses(corpus, {first.id: changed}))


def test_precedence_cycle_is_rejected(corpus):
    first = next(c for c in corpus.clauses if c.id == "lodging-br-v2.main")
    second = next(c for c in corpus.clauses if c.id == "lodging-br-v2.contractor")
    changed = first.model_copy(
        update={"relationships": (Relationship(kind="overrides", target_id=second.id),)}
    )
    with pytest.raises(ValueError, match="cycle"):
        validate_corpus(replace_clauses(corpus, {first.id: changed}))


def test_relationship_cannot_replace_an_unrelated_rule(corpus):
    first = corpus.clauses[0]
    target = next(clause for clause in corpus.clauses if clause.topic != first.topic)
    changed = first.model_copy(
        update={"relationships": (Relationship(kind="overrides", target_id=target.id),)}
    )
    with pytest.raises(ValueError, match="same rule"):
        validate_corpus(replace_clauses(corpus, {first.id: changed}))
