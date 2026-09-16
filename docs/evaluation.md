# Evaluation: reference checks first, live quality still pending

## Frozen data and protocol

`evaluation/cases.jsonl` contains 60 synthetic specification cases: 20 development and 40 held-out, with disjoint scenario families. Cases include boundary dates, missing context, contractor exceptions, conflicts, unsupported questions and prompt injection. References were authored from the fictional specification; they have **not received independent human review**. “Held-out” describes the split, not an independently administered study.

Published raw responses and summaries are in `evaluation/results/`. The neural run used actual CPU MiniLM models and PostgreSQL. Generation was exact extraction, not a hosted LLM. Corpus fingerprint: `82d154e1ccd254e05376ef9c281fc7c8fbb787b8169ae8febdc8e67d58c0efe2`. Model revisions are in `models.lock.json`; dependency versions are in `uv.lock`.

| Held-out configuration | Reference pass | Outcome accuracy | Inapplicable citations | Forbidden citations | p95 ms |
|---|---:|---:|---:|---:|---:|
| Vector only | 5% | 75% | 238 | 6 | 25.96 |
| Filtered hybrid | 77.5% | 92.5% | 0 | 6 | 18.59 |
| Complete | 97.5% | 97.5% | 0 | 0 | 51.39 |
| Without reranker | 97.5% | 97.5% | 0 | 0 | 18.10 |

The summaries also publish source recall, fabricated citations, costs and development-set results. No operational failures occurred; no hosted tokens were purchased. The vector baseline deliberately omits context filtering. It is an evaluation baseline, not an API setting.

Reference success requires the expected outcome, required sources and expected fact snippets, without forbidden or inapplicable citations. It is not a semantic human accuracy measurement. p95 is a sequential local run with caches disabled; these timings do not establish warm production p95 under two concurrent requests.

## Findings and failure

Filtering eliminates wrong-date and wrong-audience citations. Explicit precedence eliminates contractor-base citations and surfaces the conflicting meals bulletin. On this tiny corpus, reranking changed ordering without improving reference results; its added latency is measurable.

Case 055 asks about parental leave. The neural retriever selects lodging evidence and returns an answer instead of `no_evidence`. This remains a documented beta failure. No threshold was tuned against this observed held-out case. A future abstention change needs development data and a fresh holdout.

## Reproduce

```sh
uv run policytime benchmark --cases evaluation/cases.jsonl --output artifacts/offline-new
# Start PostgreSQL, migrate, download models and ingest first:
uv run policytime benchmark --neural --cases evaluation/cases.jsonl --output artifacts/neural-new
```

Set `POLICYTIME_MODE=live` with a funded Mistral key for the hosted-generation comparison. The persistent model ledger still applies. Output directories cannot be overwritten, protecting prior measurements.

## Author-rating calibration (not yet performed)

```sh
uv run policytime judge prepare --results artifacts/neural-new/results.jsonl --ratings artifacts/ratings.csv
# Read the cases and sources, then fill the ratings personally.
uv run policytime judge run --results artifacts/neural-new/results.jsonl --ratings artifacts/ratings.csv --cases evaluation/cases.jsonl --output artifacts/judge.json
```

Check `policytime judge --help` for required arguments. The offline judge is Mistral Large 3. Development ratings calibrate the rubric; held-out author ratings assess agreement. Missing ratings fail closed. Report exact agreement, within-one-point agreement and MAE. Author ratings are one person's judgment; the generator and judge share a vendor/model family. Neither is independent ground truth. No ratings or agreement results have been fabricated.

## Launch gates

Deterministic and browser tests pass locally; container build and database recovery are separately documented. Hosted answer correctness, zero invalid hosted citations, two-concurrent-request warm p95 below 15 seconds, author-rating calibration, and public uptime remain pending. Keep beta labeling until these are measured.

For a small HTTP concurrency sample against the deployed service:

```sh
uv run python scripts/load_check.py --url https://YOUR_DOMAIN --output artifacts/load.json
```

It sends two requests together, spaces pairs to respect the public rate limit, and reports cache hits and failures separately. Use a warm service and inspect uncached answered requests before making any generation-latency claim. This script has been syntax/lint checked; a hosted run is still pending.
