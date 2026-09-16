"""Use-case inputs, operational metadata, and provider-independent generation data."""

from datetime import date
from typing import Annotated, Literal

from pydantic import Field

from policytime.domain.models import (
    Country,
    Employment,
    Identifier,
    NonEmptyText,
    Outcome,
    ValueObject,
)


class AskCommand(ValueObject):
    question: Annotated[str, Field(min_length=3, max_length=800)]
    expense_date: date | None = None
    country: Country | None = None
    employment_type: Employment | None = None


class Hit(ValueObject):
    clause_id: Identifier
    score: float


class DraftCitation(ValueObject):
    clause_id: Identifier
    quote: NonEmptyText


class DraftAnswer(ValueObject):
    answer: NonEmptyText
    citations: Annotated[tuple[DraftCitation, ...], Field(min_length=1)]


class Usage(ValueObject):
    input_tokens: Annotated[int, Field(ge=0)] = 0
    output_tokens: Annotated[int, Field(ge=0)] = 0
    cost_usd: Annotated[float, Field(ge=0)] = 0


class Generation(ValueObject):
    draft: DraftAnswer
    usage: Usage


class RunInfo(ValueObject):
    request_id: str
    corpus_version: str
    mode: Literal["demo", "live"]
    strategy: str
    generator: str
    retriever: str
    reranker: str
    prompt_version: str
    elapsed_ms: float
    usage: Usage = Usage()
    cached: bool = False


class AnswerResponse(ValueObject):
    result: Outcome
    run: RunInfo


class OperationalError(Exception):
    """An infrastructure failure, never a scientific or policy abstention."""


class ProviderUnavailable(OperationalError):
    pass


class InvalidGeneration(OperationalError):
    pass


class BudgetExceeded(OperationalError):
    pass


class CapacityExceeded(OperationalError):
    pass
