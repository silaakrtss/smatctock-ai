.PHONY: install test lint format typecheck imports check run clean

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

typecheck:
	mypy src/

imports:
	lint-imports

check: lint format-check typecheck imports test

run:
	uvicorn src.presentation.main:app --reload

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
