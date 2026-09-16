"""The composition root: concrete adapters are selected only here."""

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.engine import Engine

from policytime.adapters.corpus import FileCorpusRepository
from policytime.adapters.database import PostgresCorpusRepository, connect_database
from policytime.adapters.offline import (
    ExtractiveGenerator,
    IdentityReranker,
    LexicalRetriever,
    MemoryCache,
)
from policytime.application.service import AnswerService, Dependencies
from policytime.settings import Settings


@dataclass
class Runtime:
    service: AnswerService
    engine: Engine | None = None

    def close(self) -> None:
        if self.engine is not None:
            self.engine.dispose()


def build_runtime(settings: Settings) -> Runtime:
    if settings.mode == "demo":
        return Runtime(
            AnswerService(
                Dependencies(
                    repository=FileCorpusRepository(settings.corpus_dir),
                    retriever=LexicalRetriever(),
                    reranker=IdentityReranker(),
                    generator=ExtractiveGenerator(),
                    cache=MemoryCache(),
                ),
                mode="demo",
                concurrency=settings.concurrency,
            )
        )
    return build_neural_runtime(settings, use_provider=True)


def model_revision(cache: Path, name: str) -> str:
    manifest = json.loads((cache / "manifest.json").read_text())
    revision: str = manifest[name]["revision"]
    return revision


def build_neural_runtime(settings: Settings, *, use_provider: bool = False) -> Runtime:
    from policytime.adapters.generation import MistralGenerator
    from policytime.adapters.operations import PostgresBudgetLedger, PostgresCache
    from policytime.adapters.retrieval import MiniLMEmbedder, MiniLMReranker, PostgresRetriever

    engine = connect_database(settings.database_url)
    try:
        embedder = MiniLMEmbedder(
            settings.model_cache / "embedding", model_revision(settings.model_cache, "embedding")
        )
        reranker = MiniLMReranker(
            settings.model_cache / "reranker", model_revision(settings.model_cache, "reranker")
        )
        repository = PostgresCorpusRepository(engine)
        repository.snapshot()
        generator = (
            MistralGenerator(
                settings.mistral_api_key,
                PostgresBudgetLedger(engine, settings.monthly_budget_usd),
                timeout_seconds=settings.provider_timeout_seconds,
            )
            if use_provider
            else ExtractiveGenerator()
        )
        service = AnswerService(
            Dependencies(
                repository=repository,
                retriever=PostgresRetriever(engine, embedder),
                reranker=reranker,
                generator=generator,
                cache=PostgresCache(engine),
            ),
            mode="live" if use_provider else "demo",
            concurrency=settings.concurrency,
        )
        return Runtime(service, engine)
    except Exception:
        engine.dispose()
        raise
