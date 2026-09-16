"""Persist each benchmark result immediately and keep operational errors in denominators."""

import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from policytime.application.evaluation import EvaluationCase, score_response
from policytime.application.service import AnswerService, Strategy


def load_cases(path: Path) -> tuple[EvaluationCase, ...]:
    cases = tuple(
        EvaluationCase.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    )
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Evaluation case identifiers must be unique.")
    development = {case.scenario_family for case in cases if case.split == "development"}
    test = {case.scenario_family for case in cases if case.split == "test"}
    if development & test:
        raise ValueError("Scenario families must not cross the development/test split.")
    return cases


def run_benchmark(
    service: AnswerService,
    cases_path: Path,
    output: Path,
    strategies: tuple[Strategy, ...],
) -> dict[str, Any]:
    cases = load_cases(cases_path)
    corpus = service.dependencies.repository.snapshot()
    output.mkdir(parents=True, exist_ok=True)
    path = output / "results.jsonl"
    if path.exists():
        raise ValueError("Use a new output directory; benchmark evidence is never overwritten.")
    rows: list[dict[str, Any]] = []
    with path.open("w") as handle:
        for strategy in strategies:
            for case in cases:
                row: dict[str, Any] = {
                    "case_id": case.id,
                    "split": case.split,
                    "strategy": strategy,
                    "scenario_family": case.scenario_family,
                }
                try:
                    response = service.ask(case.input, strategy)
                    row.update(
                        response=response.model_dump(mode="json"),
                        score=score_response(case, response, corpus).model_dump(),
                    )
                except Exception as error:
                    row["error_type"] = type(error).__name__
                handle.write(json.dumps(row) + "\n")
                handle.flush()
                rows.append(row)
    summary = summarize(rows)
    summary["provenance"] = {
        "corpus_version": corpus.version,
        "generator": service.dependencies.generator.identity,
        "retriever": service.dependencies.retriever.identity,
        "reranker": service.dependencies.reranker.identity,
        "labels": "Synthetic specification facts; no independent human correctness ratings.",
        "limitations": (
            "Reference checks do not establish semantic entailment or real-company quality."
        ),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[f"{row['strategy']}/{row['split']}"].append(row)
    summaries: dict[str, Any] = {}
    for name, group in groups.items():
        successes = [row for row in group if "score" in row]
        latencies = sorted(row["response"]["run"]["elapsed_ms"] for row in successes)
        recalls = [
            row["score"]["source_recall"]
            for row in successes
            if row["score"]["source_recall"] is not None
        ]
        summaries[name] = {
            "cases": len(group),
            "operational_errors": len(group) - len(successes),
            "reference_check_pass_rate": sum(
                row["score"]["reference_checks_pass"] for row in successes
            )
            / len(group),
            "outcome_accuracy": sum(row["score"]["outcome_correct"] for row in successes)
            / len(group),
            "source_recall": mean(recalls) if recalls else None,
            "fabricated_citations": sum(row["score"]["fabricated_citations"] for row in successes),
            "inapplicable_citations": sum(
                row["score"]["inapplicable_citations"] for row in successes
            ),
            "forbidden_citations": sum(row["score"]["forbidden_citations"] for row in successes),
            "p95_ms_sequential": latencies[max(0, math.ceil(len(latencies) * 0.95) - 1)]
            if latencies
            else None,
            "total_cost_usd": sum(row["response"]["run"]["usage"]["cost_usd"] for row in successes),
        }
    return {"groups": summaries}
