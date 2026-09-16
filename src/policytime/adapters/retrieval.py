"""Neural inference and PostgreSQL retrieval are isolated from policy decisions."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from sqlalchemy import any_, func, or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from policytime.adapters.database import ClauseRow, CorpusRow
from policytime.application.contracts import Hit
from policytime.application.ports import Embedder
from policytime.domain.models import Clause, Context, Corpus

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


class MiniLMEmbedder:
    def __init__(self, model_path: Path, revision: str = "local-snapshot") -> None:
        from sentence_transformers import SentenceTransformer

        self.identity = f"{EMBEDDING_MODEL}@{revision}"
        self._model = SentenceTransformer(str(model_path), device="cpu", local_files_only=True)

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        # Fail explicitly rather than silently truncate an authoritative clause.
        for text in texts:
            token_ids = self._model.tokenizer.encode(text, add_special_tokens=True)
            if len(token_ids) > 256:
                raise ValueError("A clause exceeds the embedding model's 256-token limit.")
        encoded: Any = self._model.encode(list(texts), normalize_embeddings=True, batch_size=16)
        return [[float(value) for value in row] for row in encoded]


class MiniLMReranker:
    def __init__(self, model_path: Path, revision: str = "local-snapshot") -> None:
        from sentence_transformers import CrossEncoder

        self.identity = f"{RERANKER_MODEL}@{revision}"
        self._model = CrossEncoder(
            str(model_path), device="cpu", local_files_only=True, max_length=512
        )

    def rank(self, question: str, clauses: tuple[Clause, ...]) -> tuple[Clause, ...]:
        if not clauses:
            return ()
        scores = self._model.predict([(question, clause.text) for clause in clauses], batch_size=8)
        ranked = sorted(
            zip(clauses, scores, strict=True), key=lambda pair: float(pair[1]), reverse=True
        )
        return tuple(clause for clause, _ in ranked)


class PostgresRetriever:
    def __init__(self, engine: Engine, embedder: Embedder) -> None:
        self.engine = engine
        self.embedder = embedder
        self.identity = f"postgres-hybrid-rrf-v1:{embedder.identity}"

    def search(
        self,
        corpus: Corpus,
        question: str,
        context: Context | None,
        *,
        vector_only: bool = False,
    ) -> tuple[Hit, ...]:
        vector = self.embedder.encode([question])[0]
        filters = [ClauseRow.corpus_version == corpus.version]
        if context is not None:
            filters.extend(
                [
                    ClauseRow.starts_on <= context.expense_date,
                    or_(ClauseRow.ends_on.is_(None), ClauseRow.ends_on > context.expense_date),
                    any_(ClauseRow.countries) == context.country.value,
                    any_(ClauseRow.employment_types) == context.employment_type.value,
                ]
            )
        distance = ClauseRow.embedding.cosine_distance(vector)
        search_vector = func.to_tsvector("english", ClauseRow.passage)
        search_query = func.plainto_tsquery("english", question)
        lexical_score = func.ts_rank_cd(search_vector, search_query)
        with Session(self.engine) as session:
            identity = session.scalar(
                select(CorpusRow.embedding_identity).where(CorpusRow.version == corpus.version)
            )
            if identity != self.embedder.identity:
                raise RuntimeError("The query encoder does not match the corpus encoder.")
            dense = session.execute(
                select(ClauseRow.id, distance.label("distance"))
                .where(*filters)
                .order_by(distance)
                .limit(12)
            ).all()
            lexical = (
                []
                if vector_only
                else session.execute(
                    select(ClauseRow.id, lexical_score.label("score"))
                    .where(*filters, search_vector.op("@@")(search_query))
                    .order_by(lexical_score.desc())
                    .limit(12),
                ).all()
            )
        relevant_dense = [str(row.id) for row in dense if float(row.distance) <= 0.75]
        if vector_only:
            return tuple(
                Hit(clause_id=identifier, score=1 / (index + 1))
                for index, identifier in enumerate(relevant_dense)
            )
        scores: dict[str, float] = {}
        for ranking in (relevant_dense, [str(row.id) for row in lexical]):
            for rank, identifier in enumerate(ranking, start=1):
                scores[identifier] = scores.get(identifier, 0) + 1 / (60 + rank)
        return tuple(
            Hit(clause_id=identifier, score=score)
            for identifier, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[
                :12
            ]
        )
