# SpecQL Installation Guide

**Time**: 15-30 minutes
**Goal**: Install SpecQL and verify everything works correctly

This guide covers installation on all major platforms with detailed troubleshooting for common issues.

## Prerequisites

Before installing SpecQL, ensure you have:

### Required
- **Python 3.11 or higher** - SpecQL requires modern Python features
- **uv package manager** - Fast, reliable Python package management
- **Git** - For cloning the repository

### Optional (but recommended)
- **PostgreSQL 14+** - For testing generated schemas locally
- **Docker** - For isolated testing environments
- **Visual Studio Code** - Recommended editor with YAML support

### Quick Prerequisites Check

```bash
# Check Python version (must be 3.11+)
python --version

# Check if uv is installed
uv --version

# Check Git
git --version

# Optional: Check PostgreSQL (if installed)
psql --version
```

---

## Installation Methods

### Method 1: Quick Install (Recommended)

#### Step 1: Install uv

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**:
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**Manual Installation**:
Visit https://github.com/astral-sh/uv and download the appropriate binary for your platform.

#### Step 2: Verify uv Installation

```bash
uv --version
# Should show: uv 0.x.x
```

#### Step 3: Clone and Install SpecQL

```bash
# Clone the repository
git clone https://github.com/fraiseql/specql.git
cd specql

# Install dependencies and SpecQL
uv sync
uv pip install -e .
```

#### Step 4: Verify Installation

```bash
# Check SpecQL CLI
specql --version

# Test basic functionality
specql generate entities/examples/contact_lightweight.yaml --dry-run
```

**✅ Success**: If you see generation output without errors, SpecQL is installed correctly!

---

### Method 2: Docker Installation

If you prefer containerized installation:

```bash
# Clone repository
git clone https://github.com/fraiseql/specql.git
cd specql

# Build Docker image
docker build -t specql .

# Run SpecQL in container
docker run -v $(pwd):/app specql generate entities/examples/contact_lightweight.yaml --dry-run
```

---

### Method 3: Development Installation

For contributors or advanced users:

```bash
# Clone with submodules
git clone --recursive https://github.com/fraiseql/specql.git
cd specql

# Install in development mode
uv sync --dev
uv pip install -e ".[dev]"

# Run tests to verify
uv run pytest tests/unit/ -v
```

---

## Platform-Specific Instructions

### macOS

#### Prerequisites
```bash
# Install Xcode Command Line Tools (if not already installed)
xcode-select --install

# Install Homebrew (optional, but recommended)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Installation
```bash
# Install uv via Homebrew (alternative to curl method)
brew install uv

# Then follow Method 1 steps above
```

#### Common Issues
- **"command not found: uv"**: Add uv to PATH: `export PATH="$HOME/.local/bin:$PATH"`
- **Python version issues**: Use `pyenv` to manage Python versions

---

### Linux (Ubuntu/Debian)

#### Prerequisites
```bash
# Update package list
sudo apt update

# Install Python 3.11+ if needed
sudo apt install python3.11 python3.11-venv python3-pip

# Install Git if needed
sudo apt install git
```

#### Installation
Follow Method 1 (Quick Install) above.

#### Common Issues
- **Permission denied**: Use `sudo` for system-wide installation, or install to user directory
- **Python path issues**: Ensure `python3.11` is available in PATH

---

### Linux (CentOS/RHEL/Fedora)

#### Prerequisites
```bash
# CentOS/RHEL
sudo yum install python311 python311-pip git

# Fedora
sudo dnf install python311 python311-pip git
```

#### Installation
Follow Method 1 (Quick Install) above.

---

### Windows

#### Prerequisites
- Windows 10 or 11
- Windows Terminal or PowerShell 7+ recommended

#### Installation
```powershell
# Install uv (PowerShell method from Method 1)
irm https://astral.sh/uv/install.ps1 | iex

# Clone repository (use Git Bash or WSL for better experience)
git clone https://github.com/fraiseql/specql.git
cd specql

# Install (use uv run for Windows compatibility)
uv sync
uv pip install -e .
```

#### Common Issues
- **Execution policy**: Run PowerShell as Administrator and set: `Set-ExecutionPolicy RemoteSigned`
- **PATH issues**: Restart terminal after uv installation
- **Python conflicts**: Use `py` launcher or specify full path to python.exe

---

### WSL (Windows Subsystem for Linux)

Recommended for Windows users who want full Linux compatibility:

```bash
# Install WSL2
wsl --install

# Install Ubuntu distribution
wsl --install -d Ubuntu

# Then follow Linux installation instructions
```

---

## Post-Installation Verification

### Basic Verification

```bash
# Check SpecQL version
specql --version

# List available commands
specql --help

# Test YAML parsing
specql generate entities/examples/contact_lightweight.yaml --dry-run
```

### Advanced Verification

```bash
# Test full generation pipeline
specql generate entities/examples/contact_lightweight.yaml --output /tmp/test_output

# Check generated files exist
ls -la /tmp/test_output/

# Test with PostgreSQL (if available)
# Create test database
createdb specql_test

# Apply generated schema
psql specql_test < /tmp/test_output/postgresql/crm/01_tables.sql

# Verify tables created
psql specql_test -c "\dt crm.*"
```

---

## Configuration

### Environment Variables

SpecQL respects these environment variables:

```bash
# Database connection (for testing)
export DATABASE_URL="postgresql://user:pass@localhost:5432/specql_test"

# Custom Python path
export PYTHONPATH="/path/to/custom/modules:$PYTHONPATH"

# SpecQL configuration directory
export SPECQL_CONFIG_DIR="$HOME/.config/specql"
```

### Configuration Files

SpecQL looks for configuration in:
1. `./specql.yaml` (project-specific)
2. `~/.config/specql/config.yaml` (user-specific)
3. Environment variables

Example `specql.yaml`:
```yaml
# Default database for testing
database:
  url: "postgresql://localhost:5432/specql_dev"

# Default output directory
output:
  directory: "./generated"

# Generator settings
generators:
  postgresql:
    schema: "public"
  java:
    package: "com.example"
```

---

## Troubleshooting Installation

### "uv command not found"

**Problem**: uv is not in PATH after installation.

**Solutions**:
```bash
# macOS/Linux
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Windows
# Add %USERPROFILE%\.local\bin to PATH environment variable
```

### "Python version too old"

**Problem**: System Python is older than 3.11.

**Solutions**:
```bash
# Install Python 3.11+ using pyenv
curl https://pyenv.run | bash
pyenv install 3.11.5
pyenv global 3.11.5

# Or use uv's Python management
uv python install 3.11
```

### "Permission denied" errors

**Problem**: Cannot write to installation directories.

**Solutions**:
```bash
# Install to user directory instead of system
uv pip install --user -e .

# Or use virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows
uv pip install -e .
```

### "specql command not found"

**Problem**: SpecQL CLI not available after installation.

**Solutions**:
```bash
# Check installation
uv pip list | grep specql

# Reinstall
uv pip uninstall specql
uv pip install -e .

# Check PATH includes uv's bin directory
which specql
```

---

## Updating SpecQL

To update to the latest version:

```bash
# Pull latest changes
cd specql
git pull origin main

# Update dependencies
uv sync

# Reinstall SpecQL
uv pip install -e .
```

---

## Uninstalling SpecQL

To remove SpecQL:

```bash
# Uninstall package
uv pip uninstall specql

# Remove repository (optional)
rm -rf specql

# Remove configuration (optional)
rm -rf ~/.config/specql
```

---

## Next Steps

Once installed, you're ready to:

1. **[Quick Start Guide](QUICKSTART.md)** - Generate your first schema
2. **[Getting Started Tutorial](../01_tutorials/GETTING_STARTED_TUTORIAL.md)** - Build a complete application
3. **[Examples](../06_examples/)** - Study real-world implementations

---

**Need help?** Check the [Troubleshooting Guide](TROUBLESHOOTING.md) or open an issue on [GitHub](https://github.com/fraiseql/specql/issues).