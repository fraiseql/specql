.PHONY: help install test test-unit test-integration lint typecheck format clean

help:
	@echo "SpecQL Generator - Development Commands"
	@echo ""
	@echo "  make install          Install dependencies"
	@echo "  make test            Run all tests"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make lint            Run linting (ruff)"
	@echo "  make typecheck       Run type checking (mypy)"
	@echo "  make format          Format code (black)"
	@echo "  make clean           Clean generated files"
	@echo "  make coverage        Generate coverage report"

install:
	uv pip install -e ".[dev]"

test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v -m unit

test-integration:
	uv run pytest tests/integration/ -v -m integration

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run mypy src/

format:
	uv run black src/ tests/

coverage:
	uv run pytest tests/ --cov=src --cov-report=html --cov-report=term

clean:
	rm -rf generated/*
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development shortcuts
dev-setup: install
	@echo "Development environment ready!"

watch-tests:
	uv run pytest-watch tests/unit/

# Team-specific commands
teamA-test:
	uv run pytest tests/unit/core/ -v

teamB-test:
	uv run pytest tests/unit/generators/ -v

teamC-test:
	uv run pytest tests/unit/numbering/ -v

teamD-test:
	uv run pytest tests/unit/integration/ -v

teamE-test:
	uv run pytest tests/unit/cli/ -v
