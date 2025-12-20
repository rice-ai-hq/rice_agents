.PHONY: install test lint format build clean check

install:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check src tests examples
	# If ty is available as a command, un-comment below
	# uv run ty check

format:
	uv run ruff format src tests examples

check: format lint test

build:
	uv build

clean:
	rm -rf dist
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
