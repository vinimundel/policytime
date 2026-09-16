"""Resolve explicit policy authority. Relevance scores never establish precedence."""

from collections import defaultdict

from policytime.domain.models import Clause, Context, Corpus, SelectionStep, ValueObject


class Resolution(ValueObject):
    selected: tuple[Clause, ...]
    conflicts: tuple[tuple[Clause, ...], ...]
    steps: tuple[SelectionStep, ...]


def validate_corpus(corpus: Corpus) -> None:
    documents = [document.id for document in corpus.documents]
    if len(documents) != len(set(documents)):
        raise ValueError("Document identifiers must be unique.")
    clauses = {clause.id: clause for clause in corpus.clauses}
    if len(clauses) != len(corpus.clauses):
        raise ValueError("Clause identifiers must be unique.")
    for clause in clauses.values():
        for relationship in clause.relationships:
            target = clauses.get(relationship.target_id)
            if target is None:
                raise ValueError(f"Unknown relationship target: {relationship.target_id}")
            if target.rule_key != clause.rule_key or target.topic != clause.topic:
                raise ValueError("Relationships must connect the same rule and topic.")
            if relationship.kind == "supersedes" and target.period.start >= clause.period.start:
                raise ValueError("A superseding clause must start after its predecessor.")
    _reject_cycles(clauses)


def _reject_cycles(clauses: dict[str, Clause]) -> None:
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise ValueError(f"Policy precedence cycle at {identifier}")
        if identifier in visited:
            return
        visiting.add(identifier)
        for relationship in clauses[identifier].relationships:
            visit(relationship.target_id)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in clauses:
        visit(identifier)


def resolve(clauses: tuple[Clause, ...], context: Context) -> Resolution:
    eligible: dict[str, Clause] = {}
    steps: list[SelectionStep] = []
    for clause in clauses:
        exclusion = _exclusion(clause, context)
        if exclusion is not None:
            steps.append(exclusion)
            continue
        eligible[clause.id] = clause

    displaced = _displaced_clauses(eligible)
    selected: list[Clause] = []
    for clause in eligible.values():
        winner = displaced.get(clause.id)
        if winner is not None:
            steps.append(
                SelectionStep(
                    clause_id=clause.id,
                    decision="overridden",
                    related_clause_id=winner,
                    reason=f"An applicable clause explicitly takes precedence: {winner}.",
                )
            )
            continue
        selected.append(clause)
        steps.append(
            SelectionStep(
                clause_id=clause.id,
                decision="applies",
                reason=(
                    "The expense date and audience match; no applicable clause replaces this rule."
                ),
            )
        )
    groups: dict[str, list[Clause]] = defaultdict(list)
    for clause in selected:
        groups[clause.rule_key].append(clause)
    conflicts = tuple(
        tuple(group)
        for group in groups.values()
        if len({clause.value.model_dump_json() for clause in group}) > 1
    )
    return Resolution(selected=tuple(selected), conflicts=conflicts, steps=tuple(steps))


def _exclusion(clause: Clause, context: Context) -> SelectionStep | None:
    if not clause.period.contains(context.expense_date):
        return SelectionStep(
            clause_id=clause.id,
            decision="outside_date",
            reason="This version was not effective on the expense date.",
        )
    if not clause.applies_to(context):
        return SelectionStep(
            clause_id=clause.id,
            decision="outside_audience",
            reason="This clause covers a different country or employment type.",
        )
    return None


def _displaced_clauses(eligible: dict[str, Clause]) -> dict[str, str]:
    displaced: dict[str, str] = {}
    for clause in eligible.values():
        pending = [relationship.target_id for relationship in clause.relationships]
        seen: set[str] = set()
        while pending:
            target_id = pending.pop()
            if target_id in seen or target_id not in eligible:
                continue
            seen.add(target_id)
            displaced[target_id] = clause.id
            pending.extend(link.target_id for link in eligible[target_id].relationships)
    return displaced
