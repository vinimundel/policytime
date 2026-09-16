"""Credential-free demonstrations. These adapters do not simulate neural or LLM results."""

import re
import threading
from collections import OrderedDict

from policytime.application.contracts import (
    AnswerResponse,
    DraftAnswer,
    DraftCitation,
    Generation,
    Hit,
    Usage,
)
from policytime.domain.models import Clause, Context, Corpus

STOP_WORDS = {
    "the",
    "a",
    "an",
    "on",
    "in",
    "for",
    "is",
    "my",
    "i",
    "what",
    "how",
    "can",
    "of",
    "to",
    "and",
    "was",
    "are",
    "do",
    "with",
    "this",
    "policy",
    "expense",
    "expenses",
}
SYNONYMS = {
    "hotel": "lodging",
    "hotels": "lodging",
    "accommodation": "lodging",
    "stay": "lodging",
    "food": "meals",
    "lunch": "meals",
    "dinner": "meals",
    "breakfast": "meals",
    "taxi": "transport",
    "rideshare": "transport",
    "ground": "transport",
    "flight": "airfare",
    "flights": "airfare",
    "plane": "airfare",
    "flying": "airfare",
    "approval": "approvals",
    "approve": "approvals",
    "permission": "approvals",
    "submit": "submission",
    "deadline": "submission",
    "filing": "submission",
}


def tokens(text: str) -> set[str]:
    words = set(re.findall(r"[a-z]+", text.lower())) - STOP_WORDS
    return {SYNONYMS.get(word, word) for word in words}


class LexicalRetriever:
    identity = "offline-lexical-v1"

    def search(
        self,
        corpus: Corpus,
        question: str,
        context: Context | None,
        *,
        vector_only: bool = False,
    ) -> tuple[Hit, ...]:
        query = tokens(question)
        hits: list[Hit] = []
        for clause in corpus.clauses:
            if context is not None and not clause.applies_to(context):
                continue
            overlap = query & tokens(f"{clause.topic} {clause.text}")
            topic_match = clause.topic.value in query
            if not overlap or (not topic_match and len(overlap) < 2):
                continue
            score = len(overlap) + (10 if topic_match else 0)
            hits.append(Hit(clause_id=clause.id, score=score))
        return tuple(sorted(hits, key=lambda item: (-item.score, item.clause_id))[:12])


class IdentityReranker:
    identity = "offline-no-reranker"

    def rank(self, question: str, clauses: tuple[Clause, ...]) -> tuple[Clause, ...]:
        return clauses


class ExtractiveGenerator:
    identity = "offline-exact-passages-v1"

    def generate(self, question: str, context: Context, clauses: tuple[Clause, ...]) -> Generation:
        return Generation(
            draft=DraftAnswer(
                answer="\n\n".join(clause.text for clause in clauses),
                citations=tuple(
                    DraftCitation(clause_id=clause.id, quote=clause.text) for clause in clauses
                ),
            ),
            usage=Usage(),
        )


class MemoryCache:
    def __init__(self, capacity: int = 256) -> None:
        self.capacity = capacity
        self._items: OrderedDict[str, AnswerResponse] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> AnswerResponse | None:
        with self._lock:
            result = self._items.get(key)
            if result is not None:
                self._items.move_to_end(key)
            return result

    def put(self, key: str, response: AnswerResponse) -> None:
        with self._lock:
            self._items[key] = response
            self._items.move_to_end(key)
            while len(self._items) > self.capacity:
                self._items.popitem(last=False)


class NullCache:
    def get(self, key: str) -> AnswerResponse | None:
        return None

    def put(self, key: str, response: AnswerResponse) -> None:
        return None
