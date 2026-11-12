# Contributing to SmartENV

Thanks for your interest in improving SmartENV. This guide covers the local
workflow, the quality gates, and what a good contribution looks like.

## Ground rules

- SmartENV has **zero runtime dependencies** on Python 3.11+. Do not add one.
  On Python 3.10 the only dependency is `tomli`, used because `tomllib` is not
  yet in the standard library.
- Public API changes need tests and a `README.md` update.
- Every change must pass the same gates CI runs.

## Setting up

```bash
git clone https://github.com/sc8134/SmartENV.git
cd SmartENV
python -m venv .venv
```

Activate the virtual environment, then:

```bash
pip install -e ".[dev]"
pre-commit install
```

On Windows (PowerShell) activation is `.venv\Scripts\Activate.ps1`; on macOS
and Linux it is `source .venv/bin/activate`.

## Quality gates

The `Makefile` wraps every command:

| Command | What it runs |
|---------|--------------|
| `make test` | Full test suite |
| `make test-cov` | Tests with branch coverage (fails under 95%) |
| `make lint` | `ruff check` |
| `make format` | `ruff format` (rewrites files) |
| `make format-check` | `ruff format --check` |
| `make typecheck` | `mypy smartenv` |
| `make check` | lint + format check + typecheck + coverage |
| `make build` | Build sdist and wheel |

Run `make check` before opening a pull request. On Windows without `make`, run
the underlying commands directly:

```bash
ruff check smartenv tests examples
ruff format --check smartenv tests examples
mypy smartenv
pytest --cov=smartenv --cov-branch --cov-report=term-missing
```

## Tests

- Tests live in `tests/` and use plain `pytest` (no plugins beyond
  `pytest-cov`).
- Every bug fix needs a regression test that fails before the fix.
- Prefer asserting on observable behavior (`config.get(...)`) over internals.
- Tests must pass on Python 3.10 through 3.14 and on Linux, macOS, and Windows.

## Code style

- Formatting and import order are enforced by `ruff`; do not hand-format.
- Type hints are required on all public functions; `mypy` runs in strict-ish
  mode over the package.
- Keep comments for non-obvious *why* only. Names should explain *what*.
- No `from __future__ import annotations`: quoted annotations that must work at
  runtime are deliberate, because the package supports 3.10.

## Commits and pull requests

- Keep commits focused. A bug fix should not also refactor unrelated code.
- Write the commit subject in the imperative mood, e.g.
  `fix: preserve stored None values in get()`.
- Link issues in the pull request description (`Closes #123`).
- Add an entry under `Unreleased` in `CHANGELOG.md` for user-facing changes.
- Fill in the pull request template checklist.

## Reporting bugs

Use the bug report issue template and include a minimal reproduction, the
SmartENV version, and your Python version. Security issues must not be filed
publicly — see [SECURITY.md](SECURITY.md).

## License

By contributing you agree that your contributions are licensed under the MIT
License, as described in [LICENSE](LICENSE).
