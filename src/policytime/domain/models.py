"""Validated values shared by policy decisions and their callers."""

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{1,95}$")]
NonEmptyText = Annotated[str, Field(min_length=1, max_length=6000)]


class ValueObject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class Country(StrEnum):
    BR = "BR"
    US = "US"


class Employment(StrEnum):
    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"


class Topic(StrEnum):
    LODGING = "lodging"
    MEALS = "meals"
    TRANSPORT = "transport"
    AIRFARE = "airfare"
    APPROVALS = "approvals"
    SUBMISSION = "submission"


class EffectivePeriod(ValueObject):
    start: date
    end: date | None = None

    @model_validator(mode="after")
    def require_ordered_dates(self) -> Self:
        if self.end is not None and self.end <= self.start:
            raise ValueError("The exclusive end must be after the inclusive start.")
        return self

    def contains(self, day: date) -> bool:
        return self.start <= day and (self.end is None or day < self.end)


class Scope(ValueObject):
    countries: Annotated[tuple[Country, ...], Field(min_length=1)]
    employment_types: Annotated[tuple[Employment, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def require_unique_members(self) -> Self:
        if len(set(self.countries)) != len(self.countries):
            raise ValueError("Duplicate country in scope.")
        if len(set(self.employment_types)) != len(self.employment_types):
            raise ValueError("Duplicate employment type in scope.")
        return self


class Context(ValueObject):
    expense_date: date
    country: Country
    employment_type: Employment


class Relationship(ValueObject):
    kind: Literal["supersedes", "overrides"]
    target_id: Identifier


class MoneyLimit(ValueObject):
    kind: Literal["money"] = "money"
    amount: Annotated[int, Field(gt=0)]
    currency: Literal["BRL", "USD"]
    unit: Literal["per_night", "per_day", "per_trip"]


class DayLimit(ValueObject):
    kind: Literal["days"] = "days"
    days: Annotated[int, Field(gt=0)]


class Requirement(ValueObject):
    kind: Literal["requirement"] = "requirement"
    value: NonEmptyText


RuleValue = Annotated[MoneyLimit | DayLimit | Requirement, Field(discriminator="kind")]


class Clause(ValueObject):
    id: Identifier
    document_id: Identifier
    rule_key: Identifier
    topic: Topic
    period: EffectivePeriod
    scope: Scope
    value: RuleValue
    text: Annotated[str, Field(min_length=1, max_length=1600)]
    relationships: tuple[Relationship, ...] = ()

    def applies_to(self, context: Context) -> bool:
        return (
            self.period.contains(context.expense_date)
            and context.country in self.scope.countries
            and context.employment_type in self.scope.employment_types
        )


class PolicyDocument(ValueObject):
    id: Identifier
    title: NonEmptyText
    version: Identifier
    published_on: date
    topic: Topic
    clauses: Annotated[tuple[Clause, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def require_owned_clauses(self) -> Self:
        for clause in self.clauses:
            if clause.document_id != self.id or clause.topic != self.topic:
                raise ValueError("Clauses must belong to their document and topic.")
        return self


class Corpus(ValueObject):
    version: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    documents: Annotated[tuple[PolicyDocument, ...], Field(min_length=1)]

    @property
    def clauses(self) -> tuple[Clause, ...]:
        return tuple(clause for document in self.documents for clause in document.clauses)


class Citation(ValueObject):
    clause_id: Identifier
    document_id: Identifier
    document_title: NonEmptyText
    quote: NonEmptyText
    effective_period: EffectivePeriod


class SelectionStep(ValueObject):
    clause_id: Identifier
    decision: Literal["applies", "outside_date", "outside_audience", "overridden"]
    reason: NonEmptyText
    related_clause_id: Identifier | None = None


class Answered(ValueObject):
    status: Literal["answered"] = "answered"
    answer: NonEmptyText
    context: Context
    citations: Annotated[tuple[Citation, ...], Field(min_length=1)]
    selection: tuple[SelectionStep, ...]


class NeedsContext(ValueObject):
    status: Literal["needs_context"] = "needs_context"
    missing_fields: Annotated[
        tuple[Literal["expense_date", "country", "employment_type"], ...], Field(min_length=1)
    ]
    message: NonEmptyText


class Conflict(ValueObject):
    status: Literal["conflict"] = "conflict"
    context: Context
    message: NonEmptyText
    rule_keys: Annotated[tuple[str, ...], Field(min_length=1)]
    citations: Annotated[tuple[Citation, ...], Field(min_length=2)]
    selection: tuple[SelectionStep, ...]

    @model_validator(mode="after")
    def require_distinct_evidence(self) -> Self:
        if len({citation.clause_id for citation in self.citations}) < 2:
            raise ValueError("A conflict requires distinct competing clauses.")
        return self


class NoEvidence(ValueObject):
    status: Literal["no_evidence"] = "no_evidence"
    context: Context
    message: NonEmptyText
    selection: tuple[SelectionStep, ...] = ()


Outcome = Annotated[Answered | NeedsContext | Conflict | NoEvidence, Field(discriminator="status")]
