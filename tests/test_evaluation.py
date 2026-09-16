import csv
import json
from pathlib import Path

import pytest

from policytime.adapters.benchmark import load_cases, run_benchmark, summarize
from policytime.adapters.judging import _read_ratings, agreement_report, prepare_ratings


def test_benchmark_has_separate_scenario_families():
    cases = load_cases(Path("evaluation/cases.jsonl"))
    assert len(cases) == 60
    assert sum(case.split == "development" for case in cases) == 20
    assert sum(case.split == "test" for case in cases) == 40


def test_reference_runner_persists_provenance_without_overwriting(service, tmp_path):
    output = tmp_path / "run"
    summary = run_benchmark(service, Path("evaluation/cases.jsonl"), output, ("complete",))
    assert summary["provenance"]["generator"] == "offline-exact-passages-v1"
    assert len((output / "results.jsonl").read_text().splitlines()) == 60
    with pytest.raises(ValueError, match="never overwritten"):
        run_benchmark(service, Path("evaluation/cases.jsonl"), output, ("complete",))


def test_errors_remain_in_evaluation_denominators():
    summary = summarize(
        [
            {
                "case_id": "broken",
                "split": "test",
                "strategy": "complete",
                "error_type": "ProviderUnavailable",
            }
        ]
    )
    assert summary["groups"]["complete/test"]["reference_check_pass_rate"] == 0
    assert summary["groups"]["complete/test"]["operational_errors"] == 1


def test_prepared_ratings_are_blank_and_cannot_be_claimed_as_human_scores(tmp_path):
    results = tmp_path / "results.jsonl"
    results.write_text(
        json.dumps(
            {"case_id": "case-001", "split": "development", "strategy": "complete", "response": {}}
        )
        + "\n"
    )
    path = tmp_path / "ratings.csv"
    prepare_ratings(results, path)
    with path.open() as handle:
        assert next(csv.DictReader(handle))["correctness"] == ""
    with pytest.raises(ValueError, match="incomplete"):
        _read_ratings(path)
    with pytest.raises(ValueError, match="overwrite"):
        prepare_ratings(results, path)


def test_judge_agreement_metrics_measure_disagreement():
    report = agreement_report(
        [
            {
                "judge": {"correctness": 3, "grounding": 4, "applicability": 5},
                "author": {"correctness": 5, "grounding": 4, "applicability": 4},
            }
        ]
    )
    assert report["dimensions"]["correctness"]["mean_absolute_error"] == 2
    assert report["dimensions"]["grounding"]["exact_agreement"] == 1
    assert report["dimensions"]["applicability"]["within_one_point"] == 1
