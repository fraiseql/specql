# Installation

## Prerequisites

- **Python 3.8+**
- **PostgreSQL 12+**
- **UV package manager** (recommended)

## Quick Install

### Via UV (Recommended)

```bash
# Install SpecQL generator
uv add specql-generator

# Verify installation
specql --version
```

### Via Git (Development)

```bash
# Clone the repository
git clone https://github.com/fraiseql/specql
cd specql

# Install dependencies
uv sync

# Verify installation
uv run specql --version
```

## Database Setup

SpecQL requires PostgreSQL. You can use:

- **Local PostgreSQL**: Install on your machine
- **Docker**: Quick development setup
- **Cloud**: AWS RDS, Google Cloud SQL, etc.

### Docker Setup (Recommended for Development)

```bash
# Start PostgreSQL in Docker
docker run --name specql-postgres \
  -e POSTGRES_DB=specql_dev \
  -e POSTGRES_USER=specql \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -d postgres:15

# Set connection environment variable
export DATABASE_URL="postgresql://specql:password@localhost:5432/specql_dev"
```

### Local PostgreSQL

```bash
# macOS with Homebrew
brew install postgresql
brew services start postgresql
createdb specql_dev

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo -u postgres createdb specql_dev

# Set connection
export DATABASE_URL="postgresql://localhost/specql_dev"
```

## Configuration

### Confiture Setup

SpecQL uses Confiture for configuration management:

```bash
# Install Confiture
uv add fraiseql-confiture

# Create basic configuration
cat > confiture.yaml << 'EOF'
schema_dirs:
  - path: db/schema/00_foundation
    order: 0
  - path: db/schema/10_tables
    order: 10
  - path: db/schema/20_helpers
    order: 20
  - path: db/schema/30_functions
    order: 30

environments:
  local:
    database_url: ${DATABASE_URL}
EOF
```

### Domain Registry

For multi-tenant applications, create a domain registry:

```yaml
# registry/domain_registry.yaml
domains:
  crm:
    type: multi_tenant
    description: "Customer relationship management"

  catalog:
    type: shared
    description: "Product catalog"
```

## Verification

Test your installation:

```bash
# Check SpecQL version
specql --version

# Test database connection
psql $DATABASE_URL -c "SELECT version();"

# Test Confiture
confiture validate confiture.yaml
```

## Next Steps

- [Create your first entity](your-first-entity.md)
- [Learn about YAML syntax](../../reference/yaml-reference.md)
- [Set up your development workflow](../../reference/cli-reference.md)