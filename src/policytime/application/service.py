"""Answer a question while keeping decisions separate from external actions."""

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

from policytime.application.contracts import (
    AnswerResponse,
    AskCommand,
    CapacityExceeded,
    RunInfo,
    Usage,
)
from policytime.application.evidence import citation_for, validate_citations
from policytime.application.ports import (
    AnswerCache,
    AnswerGenerator,
    CorpusRepository,
    Reranker,
    Retriever,
)
from policytime.domain.models import (
    Answered,
    Clause,
    Conflict,
    Context,
    Corpus,
    NeedsContext,
    NoEvidence,
    Outcome,
    SelectionStep,
)
from policytime.domain.resolution import Resolution, resolve

PROMPT_VERSION = "policy-answer-v1"
Strategy = Literal["vector", "filtered", "complete", "without_reranker"]
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Dependencies:
    repository: CorpusRepository
    retriever: Retriever
    reranker: Reranker
    generator: AnswerGenerator
    cache: AnswerCache


class AnswerService:
    def __init__(
        self,
        dependencies: Dependencies,
        mode: Literal["demo", "live"],
        concurrency: int = 2,
    ) -> None:
        self.dependencies = dependencies
        self.mode = mode
        self._slots = threading.BoundedSemaphore(concurrency)

    def ask(self, command: AskCommand, strategy: Strategy = "complete") -> AnswerResponse:
        if not self._slots.acquire(blocking=False):
            raise CapacityExceeded("All answer slots are busy. Please retry shortly.")
        try:
            return self._answer(command, strategy)
        finally:
            self._slots.release()

    def _answer(self, command: AskCommand, strategy: Strategy) -> AnswerResponse:
        started = time.perf_counter()
        corpus = self.dependencies.repository.snapshot()
        cache_key = self._cache_key(command, corpus.version, strategy)
        cached = self.dependencies.cache.get(cache_key)
        if cached is not None:
            run = cached.run.model_copy(
                update={
                    "request_id": str(uuid4()),
                    "cached": True,
                    "usage": Usage(),
                    "elapsed_ms": (time.perf_counter() - started) * 1000,
                }
            )
            return AnswerResponse(result=cached.result, run=run)
        result, usage = self._execute(command, corpus, strategy)
        response = AnswerResponse(
            result=result,
            run=RunInfo(
                request_id=str(uuid4()),
                corpus_version=corpus.version,
                mode=self.mode,
                strategy=strategy,
                generator=self.dependencies.generator.identity,
                retriever=self.dependencies.retriever.identity,
                reranker=self.dependencies.reranker.identity
                if strategy == "complete"
                else "disabled",
                prompt_version=PROMPT_VERSION,
                elapsed_ms=(time.perf_counter() - started) * 1000,
                usage=usage,
            ),
        )
        self.dependencies.cache.put(cache_key, response)
        return response

    def _execute(
        self,
        command: AskCommand,
        corpus: Corpus,
        strategy: Strategy,
    ) -> tuple[Outcome, Usage]:
        context = _context_or_question(command)
        if isinstance(context, NeedsContext):
            return context, Usage()
        hits = self.dependencies.retriever.search(
            corpus,
            command.question,
            None if strategy == "vector" else context,
            vector_only=strategy == "vector",
        )
        if not hits:
            return NoEvidence(
                context=context, message="No relevant policy evidence was found."
            ), Usage()
        by_id = {clause.id: clause for clause in corpus.clauses}
        candidates = tuple(by_id[hit.clause_id] for hit in hits if hit.clause_id in by_id)
        if strategy in {"vector", "filtered"}:
            return self._generate(command, context, candidates[:8], corpus, ())

        # Resolve the whole retrieved topic, including clauses omitted by top-k retrieval.
        topics = {clause.topic for clause in candidates[:3]}
        related = tuple(clause for clause in corpus.clauses if clause.topic in topics)
        decision = resolve(related, context)
        early_result = _decision_outcome(decision, context, corpus)
        if early_result is not None:
            return early_result, Usage()
        evidence = decision.selected
        if strategy == "complete":
            evidence = self.dependencies.reranker.rank(command.question, evidence)
        return self._generate(command, context, evidence, corpus, decision.steps)

    def _generate(
        self,
        command: AskCommand,
        context: Context,
        evidence: tuple[Clause, ...],
        corpus: Corpus,
        selection: tuple[SelectionStep, ...],
    ) -> tuple[Outcome, Usage]:
        generated = self.dependencies.generator.generate(command.question, context, evidence)
        citations = validate_citations(generated.draft, evidence, corpus)
        return Answered(
            answer=generated.draft.answer,
            context=context,
            citations=citations,
            selection=selection,
        ), generated.usage

    def _cache_key(self, command: AskCommand, version: str, strategy: Strategy) -> str:
        data = {
            "command": command.model_dump(mode="json"),
            "corpus": version,
            "strategy": strategy,
            "generator": self.dependencies.generator.identity,
            "retriever": self.dependencies.retriever.identity,
            "reranker": self.dependencies.reranker.identity,
            "prompt": PROMPT_VERSION,
            "mode": self.mode,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _context_or_question(command: AskCommand) -> Context | NeedsContext:
    fields: list[Literal["expense_date", "country", "employment_type"]] = []
    if command.expense_date is None:
        fields.append("expense_date")
    if command.country is None:
        fields.append("country")
    if command.employment_type is None:
        fields.append("employment_type")
    if fields:
        return NeedsContext(
            missing_fields=tuple(fields),
            message="Choose the expense date, country, and worker type.",
        )
    assert command.expense_date is not None
    assert command.country is not None
    assert command.employment_type is not None
    return Context(
        expense_date=command.expense_date,
        country=command.country,
        employment_type=command.employment_type,
    )


def _decision_outcome(
    decision: Resolution,
    context: Context,
    corpus: Corpus,
) -> Conflict | NoEvidence | None:
    if not decision.selected:
        return NoEvidence(
            context=context,
            message="No policy covers this date and audience.",
            selection=decision.steps,
        )
    if not decision.conflicts:
        return None
    clauses = tuple(clause for group in decision.conflicts for clause in group)
    return Conflict(
        context=context,
        message="Applicable policies disagree without an explicit precedence rule. "
        "A policy owner must resolve this before a definitive answer is possible.",
        rule_keys=tuple(sorted({clause.rule_key for clause in clauses})),
        citations=tuple(citation_for(clause, corpus) for clause in clauses),
        selection=decision.steps,
    )
