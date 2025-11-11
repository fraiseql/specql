.PHONY: help install test test-unit test-integration lint typecheck format clean clean-generated clean-test clean-all version

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
	@echo "  make clean           Clean all artifacts"
	@echo "  make clean-generated Clean generated files only"
	@echo "  make clean-test      Clean test artifacts only"
	@echo "  make clean-all       Clean everything"
	@echo "  make repo-size       Show repository size"
	@echo "  make coverage        Generate coverage report"
	@echo ""
	@echo "Version Management:"
	@echo "  make version         Show current version"
	@echo "  make version-patch   Bump patch version (0.1.0 -> 0.1.1)"
	@echo "  make version-minor   Bump minor version (0.1.0 -> 0.2.0)"
	@echo "  make version-major   Bump major version (0.1.0 -> 1.0.0)"

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

# Clean generated files
clean-generated:
	@echo "Cleaning generated files..."
	find generated -type f -not -name '.gitkeep' -not -name 'README.md' -delete
	@echo "Generated files cleaned."

# Clean test artifacts
clean-test:
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache/ htmlcov/ .coverage .mypy_cache/ .ruff_cache/
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	@echo "Test artifacts cleaned."

# Clean all temporary files
clean-all: clean-generated clean-test
	@echo "Cleaning all temporary files..."
	rm -rf tmp/ temp/ test_output/ *.db *.log
	@echo "All temporary files cleaned."

# Show repository size
repo-size:
	@echo "Repository size:"
	@du -sh .
	@echo "\nGit object size:"
	@du -sh .git/
	@echo "\nLargest directories:"
	@du -h --max-depth=1 . | sort -rh | head -10

# Legacy clean target (for backward compatibility)
clean: clean-all

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

# Version management
version:
	@python scripts/version.py

version-patch:
	@python scripts/version.py bump patch

version-minor:
	@python scripts/version.py bump minor

version-major:
	@python scripts/version.py bump major
