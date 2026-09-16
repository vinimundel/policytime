"""Explicit operator commands; no downloads, migrations, or ingestion at HTTP startup."""

import argparse
import json
from dataclasses import replace
from pathlib import Path

from policytime.adapters.benchmark import run_benchmark
from policytime.adapters.corpus import load_corpus
from policytime.adapters.database import connect_database, publish_corpus
from policytime.adapters.offline import NullCache
from policytime.application.service import Strategy
from policytime.bootstrap import build_neural_runtime, build_runtime, model_revision
from policytime.settings import Settings


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="policytime", description="Operate and evaluate PolicyTime."
    )
    commands = root.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Serve the configured demo or live application")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    commands.add_parser("validate-corpus", help="Validate metadata, references, and precedence")
    commands.add_parser("download-models", help="Download and record immutable model revisions")
    commands.add_parser("ingest", help="Publish the validated corpus transactionally to PostgreSQL")
    commands.add_parser("budget", help="Inspect this month's persistent model spending")
    benchmark = commands.add_parser(
        "benchmark", help="Run fixture reference checks, not human ratings"
    )
    benchmark.add_argument("--cases", type=Path, default=Path("evaluation/cases.jsonl"))
    benchmark.add_argument("--output", type=Path, required=True)
    benchmark.add_argument(
        "--neural", action="store_true", help="Use PostgreSQL and real CPU models"
    )
    judge = commands.add_parser(
        "judge", help="Prepare author ratings or run a calibrated offline judge"
    )
    judge.add_argument("action", choices=("prepare", "run"))
    judge.add_argument("--results", type=Path, required=True)
    judge.add_argument("--ratings", type=Path, required=True)
    judge.add_argument("--cases", type=Path, default=Path("evaluation/cases.jsonl"))
    judge.add_argument("--output", type=Path, default=Path("artifacts/judge"))
    return root


def main() -> None:
    args = parser().parse_args()
    settings = Settings()
    if args.command == "serve":
        import uvicorn

        uvicorn.run("policytime.delivery.web:app", host=args.host, port=args.port, access_log=False)
        return
    if args.command == "validate-corpus":
        corpus = load_corpus(settings.corpus_dir)
        print(
            json.dumps(
                {
                    "version": corpus.version,
                    "documents": len(corpus.documents),
                    "clauses": len(corpus.clauses),
                },
                indent=2,
            )
        )
        return
    if args.command == "download-models":
        from policytime.adapters.model_files import download_models

        print(json.dumps(download_models(settings.model_cache), indent=2))
        return
    if args.command == "ingest":
        _ingest(settings)
        return
    if args.command == "benchmark":
        _benchmark(settings, args.cases, args.output, neural=args.neural)
        return
    if args.command == "judge":
        from policytime.adapters.judging import prepare_ratings, run_judge

        if args.action == "prepare":
            prepare_ratings(args.results, args.ratings)
            return
        run_judge(settings, args.results, args.cases, args.ratings, args.output)
        return
    if args.command == "budget":
        from policytime.adapters.operations import PostgresBudgetLedger

        engine = connect_database(settings.database_url)
        try:
            print(json.dumps(PostgresBudgetLedger(engine, settings.monthly_budget_usd).summary()))
        finally:
            engine.dispose()


def _ingest(settings: Settings) -> None:
    from policytime.adapters.retrieval import MiniLMEmbedder

    corpus = load_corpus(settings.corpus_dir)
    embedder = MiniLMEmbedder(
        settings.model_cache / "embedding", model_revision(settings.model_cache, "embedding")
    )
    engine = connect_database(settings.database_url)
    try:
        publish_corpus(engine, corpus, embedder)
    finally:
        engine.dispose()
    print(json.dumps({"published": corpus.version, "embedding": embedder.identity}))


def _benchmark(settings: Settings, cases: Path, output: Path, *, neural: bool) -> None:
    runtime = (
        build_neural_runtime(settings)
        if neural and settings.mode == "demo"
        else build_runtime(settings)
    )
    runtime.service.dependencies = replace(runtime.service.dependencies, cache=NullCache())
    strategies: tuple[Strategy, ...] = (
        ("vector", "filtered", "complete", "without_reranker")
        if neural or settings.mode == "live"
        else ("complete",)
    )
    try:
        summary = run_benchmark(runtime.service, cases, output, strategies)
        print(json.dumps(summary, indent=2))
    finally:
        runtime.close()


if __name__ == "__main__":
    main()
