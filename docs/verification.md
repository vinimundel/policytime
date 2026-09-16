# Local verification — 2026-09-16

- Python 3.12; Ruff checks and formatting passed; strict mypy passed across 26 source files.
- 52 application/domain/evaluation/PostgreSQL/browser tests passed together. Two additional release rollback tests passed after correcting restoration of the previous corpus pointer.
- Chromium checked desktop and 390px mobile workflows, date comparison, source navigation and conflict examples.
- Docker image built successfully; read-only non-root runtime (`10001:10001`) became healthy.
- Live dependency wiring loaded both pinned CPU models, PostgreSQL and the LangChain Mistral adapter and passed readiness with a dummy API key. No hosted generation call was made; this does not validate provider credentials or model output quality.
- Production Compose and Caddy configuration validation passed.
- PostgreSQL custom-format backup restored into a separate database with the same corpus fingerprint and 53 clauses.
- Real neural retrieval benchmark: 240 runs across four configurations, no operational errors. Raw results are committed under `evaluation/results/`.
- A two-minute captioned walkthrough was recorded against the local extractive demo.

Known dependency warning: Starlette's test client uses a deprecated AnyIO `BlockingPortal` alias; tests still pass.

Cloud deployment, hosted-provider evaluation, author ratings and real production load/uptime remain unverified. See `deployment.md` for release gates.
