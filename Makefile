.PHONY: help install test test-unit test-integration lint format clean version db-up db-down db-restart db-logs db-status test-all

help:
	@echo "SpecQL Generator - Development Commands"
	@echo ""
	@echo "  make install          Install dependencies"
	@echo "  make test            Run all tests (unit only, no DB)"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-all        Run ALL tests including database tests"
	@echo "  make lint            Run linting (ruff)"
	@echo "  make format          Format code (black)"
	@echo "  make clean           Clean generated files"
	@echo "  make coverage        Generate coverage report"
	@echo ""
	@echo "Database Management:"
	@echo "  make db-up           Start PostgreSQL test database"
	@echo "  make db-down         Stop and remove test database"
	@echo "  make db-restart      Restart test database"
	@echo "  make db-logs         Show database logs"
	@echo "  make db-status       Check database status"
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

# Version management
version:
	@python scripts/version.py

version-patch:
	@python scripts/version.py bump patch

version-minor:
	@python scripts/version.py bump minor

version-major:
	@python scripts/version.py bump major

# Database management
db-up:
	@echo "Starting PostgreSQL test database..."
	docker-compose -f docker-compose.test.yml up -d
	@echo "Waiting for database to be ready..."
	@sleep 3
	@docker-compose -f docker-compose.test.yml exec -T postgres pg_isready -U postgres || echo "Database starting..."
	@echo "✅ Database ready on port 5433"

db-down:
	@echo "Stopping PostgreSQL test database..."
	docker-compose -f docker-compose.test.yml down

db-restart:
	@echo "Restarting PostgreSQL test database..."
	docker-compose -f docker-compose.test.yml restart
	@sleep 2
	@echo "✅ Database restarted"

db-logs:
	docker-compose -f docker-compose.test.yml logs -f postgres

db-status:
	@echo "Database Status:"
	@docker-compose -f docker-compose.test.yml ps
	@echo ""
	@docker-compose -f docker-compose.test.yml exec -T postgres pg_isready -U postgres 2>/dev/null && echo "✅ Database is READY" || echo "❌ Database is NOT ready"

# Test with database
test-all: db-up
	@echo "Running ALL tests (including database integration tests)..."
	TEST_DB_HOST=localhost TEST_DB_PORT=5433 TEST_DB_NAME=test_specql TEST_DB_USER=postgres TEST_DB_PASSWORD=postgres uv run pytest tests/ -v
