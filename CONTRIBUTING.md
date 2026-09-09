# Contributing

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

Use Python 3.12 or newer.

## Checks

All of the following must succeed before you send a change:

```bash
pytest
pytest --cov=app --cov-report=term-missing
ruff check .
mypy app/
```

Add tests for new behavior. Bug fixes need a regression test.

## Code style

- Type hints on functions and methods
- Constructor-style dependencies, no field injection
- Keep modules focused and under 300 lines
- Do not log secrets or upload contents
- New files use lowercase names; Python modules stay importable (snake_case)

## Changelog

Update `CHANGELOG.md` for user-facing changes. Follow [Common Changelog](https://common-changelog.org/).
