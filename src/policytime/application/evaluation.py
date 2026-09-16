"""Reference checks measure known fixture facts, not independent human correctness."""

import re
from typing import Literal

from policytime.application.contracts import AnswerResponse, AskCommand
from policytime.domain.models import Answered, Context, Corpus, ValueObject


class EvaluationCase(ValueObject):
    id: str
    label_source: Literal["synthetic-specification"]
    split: Literal["development", "test"]
    scenario_family: str
    input: AskCommand
    expected_status: Literal["answered", "needs_context", "conflict", "no_evidence"]
    required_clause_ids: tuple[str, ...]
    forbidden_clause_ids: tuple[str, ...] = ()
    expected_facts: tuple[str, ...]


class CaseScore(ValueObject):
    outcome_correct: bool
    reference_checks_pass: bool
    expected_fact_match: bool
    source_recall: float | None
    fabricated_citations: int
    inapplicable_citations: int
    forbidden_citations: int


def score_response(case: EvaluationCase, response: AnswerResponse, corpus: Corpus) -> CaseScore:
    result = response.result
    citations = getattr(result, "citations", ())
    identifiers = {citation.clause_id for citation in citations}
    known = {clause.id: clause for clause in corpus.clauses}
    context = getattr(result, "context", None)
    fabricated = len(identifiers - known.keys())
    inapplicable = sum(
        1
        for identifier in identifiers
        if identifier in known
        and isinstance(context, Context)
        and not known[identifier].applies_to(context)
    )
    forbidden = len(identifiers & set(case.forbidden_clause_ids))
    required = set(case.required_clause_ids)
    recall = len(required & identifiers) / len(required) if required else None
    answer = result.answer if isinstance(result, Answered) else ""
    facts_match = all(_contains_fact(answer, fact) for fact in case.expected_facts)
    outcome_correct = result.status == case.expected_status
    return CaseScore(
        outcome_correct=outcome_correct,
        expected_fact_match=facts_match,
        source_recall=recall,
        fabricated_citations=fabricated,
        inapplicable_citations=inapplicable,
        forbidden_citations=forbidden,
        reference_checks_pass=outcome_correct
        and facts_match
        and (recall is None or recall == 1)
        and fabricated == 0
        and inapplicable == 0
        and forbidden == 0,
    )


def _contains_fact(answer: str, fact: str) -> bool:
    return (
        re.search(r"(?<!\w)" + re.escape(fact) + r"(?!\w)", answer, flags=re.IGNORECASE) is not None
    )
