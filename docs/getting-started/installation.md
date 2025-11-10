# Installation Guide

This guide will help you install SpecQL and set up your development environment.

## 📋 Prerequisites

Before installing SpecQL, ensure you have:

- **Python 3.8 or higher**
- **PostgreSQL 12 or higher**
- **Command-line access** (Terminal, PowerShell, etc.)

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.8 | 3.11+ |
| **PostgreSQL** | 12 | 15+ |
| **RAM** | 2GB | 4GB+ |
| **Disk** | 500MB | 1GB+ |

## 🚀 Quick Install (2 minutes)

### Option 1: Install from PyPI (Recommended)

```bash
# Install SpecQL
pip install specql

# Verify installation
specql --version
```

**Expected output:**
```
SpecQL v1.0.0
```

### Option 2: Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/your-org/specql
cd specql

# Install in development mode
pip install -e .

# Verify installation
specql --version
```

## 🗄️ Database Setup

SpecQL requires PostgreSQL for storing your generated schemas and running tests.

### Option A: Docker (Easiest - Recommended)

```bash
# Start PostgreSQL container
docker run --name specql-postgres \
  -e POSTGRES_DB=specql_dev \
  -e POSTGRES_USER=specql \
  -e POSTGRES_PASSWORD=specql123 \
  -p 5432:5432 \
  -d postgres:15

# Wait for PostgreSQL to start
sleep 5

# Test connection
psql postgresql://specql:specql123@localhost:5432/specql_dev -c "SELECT version();"
```

### Option B: Local PostgreSQL

#### macOS (Homebrew)
```bash
# Install PostgreSQL
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create database
createdb specql_dev
```

#### Ubuntu/Debian
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql

# Create database as postgres user
sudo -u postgres createdb specql_dev
```

#### Windows
```powershell
# Using Chocolatey
choco install postgresql

# Or download from postgresql.org
# Follow installer instructions
# Create database via pgAdmin or psql
```

### Option C: Cloud Database

You can also use cloud-hosted PostgreSQL:

- **AWS RDS PostgreSQL**
- **Google Cloud SQL**
- **Azure Database for PostgreSQL**
- **Supabase**
- **Neon**

Just ensure you have the connection URL.

## ⚙️ Configuration

### Environment Variables

Set up your database connection:

```bash
# For local Docker setup
export DATABASE_URL="postgresql://specql:specql123@localhost:5432/specql_dev"

# For local PostgreSQL
export DATABASE_URL="postgresql://localhost/specql_dev"

# For cloud database
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

### Optional: Confiture Configuration

For advanced setups, create a `confiture.yaml`:

```yaml
# confiture.yaml
schema_dirs:
  - path: db/schema/00_foundation
    order: 0
  - path: db/schema/10_tables
    order: 10
  - path: db/schema/20_constraints
    order: 20
  - path: db/schema/30_indexes
    order: 30
  - path: db/schema/40_functions
    order: 40

environments:
  local:
    database_url: ${DATABASE_URL}
  production:
    database_url: ${PROD_DATABASE_URL}
```

## ✅ Verification

Test that everything is working:

```bash
# 1. Check SpecQL version
specql --version

# 2. Test database connection
psql $DATABASE_URL -c "SELECT version();"

# 3. Test SpecQL database connection
specql validate connection

# 4. Optional: Test Confiture (if using)
confiture validate confiture.yaml
```

**Expected output:**
```
SpecQL v1.0.0
                                                 version
---------------------------------------------------------------------------------------------------------
 PostgreSQL 15.3 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 9.4.0, 64-bit
(1 row)

✅ Database connection successful
✅ All configurations valid
```

## 🐛 Troubleshooting

### Common Installation Issues

#### "specql command not found"
```bash
# Check if pip installed to user directory
pip install --user specql

# Or use pipx
pipx install specql

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

#### "psql command not found"
```bash
# Install PostgreSQL client
# macOS
brew install libpq

# Ubuntu
sudo apt install postgresql-client

# Add to PATH
export PATH="/usr/local/opt/libpq/bin:$PATH"
```

#### Database Connection Failed
```bash
# Check if PostgreSQL is running
# Docker
docker ps | grep postgres

# Local service
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS

# Test connection manually
psql $DATABASE_URL -c "SELECT 1;"
```

#### Permission Denied
```bash
# For Docker on Linux
sudo chmod 666 /var/run/docker.sock

# Or add user to docker group
sudo usermod -aG docker $USER
# Then logout and login again
```

## 🎯 Next Steps

Now that SpecQL is installed:

1. **[Create Your First Entity](first-entity.md)** - Learn the basics
2. **[Use Your First Pattern](first-pattern.md)** - Add business logic
3. **[Generate Tests](first-tests.md)** - Set up automated testing

## 📚 Additional Resources

- **[CLI Reference](../reference/cli-reference.md)** - All commands
- **[Troubleshooting](../troubleshooting/common-issues.md)** - Common problems
- **[Community](https://discord.gg/specql)** - Get help

## 💡 Pro Tips

- **Use Docker for development** - Consistent environment
- **Set environment variables** in your shell profile (`.bashrc`, `.zshrc`)
- **Use virtual environments** - `python -m venv specql-env`
- **Keep PostgreSQL updated** - Latest version for best performance

**Ready to create your first entity? Let's go! 🚀**