# Contributing

PolicyTime favors clarity, explicit contracts, and testable policy decisions.

## Coding conventions

- Write straightforward code with descriptive names and focused functions.
- Use guard clauses to handle invalid input and edge cases early.
- Validate immutable domain objects at construction; represent outcomes as distinct types.
- Put third-party APIs, databases, and model libraries behind application protocols.
- Compute policy decisions first, then execute side effects in the application layer.
- Domain code has no filesystem, database, network, environment, or clock access.
- Keep dependencies pointing inward: delivery/adapters → application → domain.

## Development

Use Python 3.12 and uv. Run `uv sync --locked` for the lightweight environment or
`uv sync --locked --extra neural` for CPU model inference.

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -m 'not browser and not neural'
```

Integration tests use an explicitly configured disposable database whose name ends
in `_test`. Browser and model test prerequisites are documented in the README.

Never label fixture references as human ratings or extractive responses as LLM
results. Preserve failed benchmark runs and their provenance when improving code.
