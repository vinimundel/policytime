"""Small boundaries implemented by production adapters and test doubles."""

from collections.abc import Sequence
from decimal import Decimal
from typing import Protocol

from policytime.application.contracts import AnswerResponse, Generation, Hit
from policytime.domain.models import Clause, Context, Corpus


class CorpusRepository(Protocol):
    def snapshot(self) -> Corpus: ...


class Retriever(Protocol):
    @property
    def identity(self) -> str: ...

    def search(
        self,
        corpus: Corpus,
        question: str,
        context: Context | None,
        *,
        vector_only: bool = False,
    ) -> tuple[Hit, ...]: ...


class Reranker(Protocol):
    @property
    def identity(self) -> str: ...

    def rank(self, question: str, clauses: tuple[Clause, ...]) -> tuple[Clause, ...]: ...


class AnswerGenerator(Protocol):
    @property
    def identity(self) -> str: ...

    def generate(
        self, question: str, context: Context, clauses: tuple[Clause, ...]
    ) -> Generation: ...


class Embedder(Protocol):
    @property
    def identity(self) -> str: ...

    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class AnswerCache(Protocol):
    def get(self, key: str) -> AnswerResponse | None: ...
    def put(self, key: str, response: AnswerResponse) -> None: ...


class BudgetLedger(Protocol):
    def reserve(self, maximum_cost: Decimal) -> str: ...
    def settle(self, reservation_id: str, actual_cost: Decimal | None) -> None: ...
