PYTHON ?= python

.PHONY: help install test test-cov lint format format-check typecheck check build clean

help:
	@echo "install      Install the package with development dependencies"
	@echo "test         Run the test suite"
	@echo "test-cov     Run tests with branch coverage (fails under the configured threshold)"
	@echo "lint         Run ruff lint checks"
	@echo "format       Format code and apply safe ruff fixes"
	@echo "format-check Verify formatting without modifying files"
	@echo "typecheck    Run mypy on the package"
	@echo "check        Run every CI gate locally"
	@echo "build        Build sdist and wheel into dist/"
	@echo "clean        Remove build artefacts and caches"

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

test-cov:
	$(PYTHON) -m pytest --cov=smartenv --cov-report=term-missing --cov-report=xml

lint:
	ruff check smartenv tests examples

format:
	ruff check --fix smartenv tests examples
	ruff format smartenv tests examples

format-check:
	ruff format --check smartenv tests examples

typecheck:
	mypy smartenv

check: lint format-check typecheck test-cov

build: clean
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

clean:
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
