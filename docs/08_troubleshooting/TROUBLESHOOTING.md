# SpecQL Troubleshooting Guide

## Table of Contents
- [Quick Start Issues](#quick-start-issues)
- [CLI Usage Issues](#cli-usage-issues)
- [Installation Issues](#installation-issues)
- [Generation Errors](#generation-errors)
- [Runtime Errors](#runtime-errors)
- [Platform-Specific Issues](#platform-specific-issues)
- [Performance Issues](#performance-issues)
- [Integration Issues](#integration-issues)

## Quick Start Issues

### "specql: command not found"

**Symptoms**: Command not recognized in terminal

**Solutions**:
1. **Check if installed**: `pip show specql-generator`
2. **Find installation location**: `python -m site --user-base`
3. **Add to PATH**: Add `~/.local/bin` to your PATH
4. **Reinstall**: `pip install --force-reinstall specql-generator`

**Verify**:
```bash
which specql
specql --version
```

### First Generation Fails

**Symptoms**: Error on first `specql generate` command

**Solutions**:
1. **Check entity file exists**: `ls entities/*.yaml`
2. **Validate YAML syntax**: `python -c "import yaml; yaml.safe_load(open('entities/contact.yaml'))"`
3. **Use examples**: `specql examples simple-entity`
4. **Check file permissions**: `ls -la entities/`

### Examples Command Not Working

**Symptoms**: `specql examples` shows no output or errors

**Solutions**:
1. **List examples**: `specql examples --list`
2. **Check specific example**: `specql examples simple-entity`
3. **Update SpecQL**: `pip install --upgrade specql-generator`

## CLI Usage Issues

### "Invalid field type" Error

**Symptoms**:
```
❌ Invalid field type: 'string'
   File: contact.yaml | Entity: Contact | Field: name
   💡 Suggestion: Valid types: text, integer, decimal, boolean, ...
```

**Cause**: Using incorrect field type name

**Solution**: Use `text` instead of `string`. Valid types:
- `text` (instead of string/varchar)
- `integer` (instead of int)
- `decimal` (instead of float/double)
- `boolean` (instead of bool)
- `timestamp` (instead of datetime)
- `json` (for JSON data)

### Interactive Mode Issues

**Symptoms**: Interactive mode doesn't show previews or hangs

**Solutions**:
1. **Check entity files**: Ensure YAML files are valid
2. **Use non-interactive**: `specql generate entities/*.yaml`
3. **Check terminal**: Some terminals don't support interactive features

### Dry Run Shows Nothing

**Symptoms**: `--dry-run` produces no output

**Cause**: No entity files found or invalid paths

**Solutions**:
1. **Check file paths**: `ls entities/**/*.yaml`
2. **Use correct glob**: `entities/*.yaml` or `entities/**/*.yaml`
3. **Check permissions**: `ls -la entities/`

### Progress Bars Not Showing

**Symptoms**: No progress indicators during generation

**Cause**: Rich library not available or terminal limitations

**Solutions**:
1. **Check Rich installation**: `python -c "import rich; print('OK')"`
2. **Use verbose mode**: `specql generate --verbose entities/*.yaml`
3. **Check terminal**: Some terminals don't support rich formatting

## Installation Issues

### Python Version Errors

**Error**: `Python 3.11 or higher is required`

**Cause**: Incompatible Python version

**Solution**:
```bash
# Check current version
python --version

# Install Python 3.11+
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# Fedora/RHEL
sudo dnf install python3.11

# Windows
# Download from https://www.python.org/downloads/
```

**Verify**:
```bash
python3.11 --version
```

### uv Installation Fails

**Error**: `curl: command not found` or download errors

**Solution**:
```bash
# Linux - install curl first
sudo apt-get install curl  # Ubuntu/Debian
sudo yum install curl      # RHEL/CentOS

# Then install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alternative: use pip
pip install uv
```

### Command Not Found After Installation

**Error**: `specql: command not found`

**Cause**: Not in PATH

**Solution**:
```bash
# Find where uv installed specql
which specql
python -m site --user-base

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Or run directly
python -m specql generate entities/**/*.yaml
```

**Windows**:
```powershell
# Add to PATH
$env:Path += ";$env:USERPROFILE\.local\bin"
```

### Permission Denied Errors

**Error**: `Permission denied` during installation

**Solution**:
```bash
# Don't use sudo with uv/pip
# Install in user directory instead
uv pip install -e . --user

# If you must use system-wide:
sudo uv pip install -e .
```

---

## Generation Errors

### Invalid Field Type

**Error**: `Invalid field type: 'string'`

**Cause**: Using incorrect type name

**Solution**:
Use `text` instead of `string`:
```yaml
# ❌ Wrong
fields:
  name: string

# ✅ Correct
fields:
  name: text
```

**Valid types**: `text`, `integer`, `decimal`, `boolean`, `timestamp`, `date`, `time`, `json`, `uuid`, `email`, `url`, `phone`, `ref(Entity)`, `enum(...)`

[Complete type reference](../03_reference/yaml/complete_reference.md#field-types)

### Entity Not Found

**Error**: `Entity 'Company' not found`

**Cause**: Referenced entity doesn't exist or wrong name

**Solution**:
1. Check entity name matches exactly (case-sensitive)
2. Ensure entity file exists
3. Check entity is in same schema or specify full path

```yaml
# If entities are in different schemas
fields:
  company: ref(sales.Company)  # Specify schema
```

### Circular Dependency Warning

**Error**: `Circular dependency detected: Contact -> Company -> Contact`

**Cause**: Entities reference each other

**Solution**: This is **not an error**! SpecQL supports circular references.

Make sure:
- Both entities exist
- Syntax is correct: `ref(EntityName)`
- Names match exactly

SpecQL will handle the circular reference correctly in generated code.

### YAML Syntax Error

**Error**: `YAML syntax error at line 12`

**Cause**: Invalid YAML formatting

**Solution**:
```yaml
# Common issues:

# ❌ Tabs instead of spaces
fields:
→→name: text  # Tab character

# ✅ Use spaces
fields:
  name: text  # 2 spaces

# ❌ Missing colon
fields
  name: text

# ✅ Add colon
fields:
  name: text

# ❌ Wrong indentation
fields:
  name: text
    email: email  # 3 spaces

# ✅ Consistent indentation
fields:
  name: text
  email: email  # 2 spaces
```

**Tip**: Use a YAML validator or IDE with YAML support (VS Code, PyCharm)

### Template Rendering Error

**Error**: `Template rendering failed`

**Cause**: Bug in SpecQL or corrupted template

**Solution**:
1. Check SpecQL version: `specql --version`
2. Update to latest:
   ```bash
   cd ~/code/specql
   git pull origin main
   uv sync
   ```
3. Report issue with your YAML file

---

## Runtime Errors

### Generated SQL Doesn't Execute

**Error**: SQL syntax errors when loading generated schema

**Cause**: Incompatible PostgreSQL version or missing extensions

**Solution**:
```bash
# Check PostgreSQL version
psql --version  # Need 12+

# Install required extensions
psql -d your_database -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
psql -d your_database -c "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";"

# Load schema
psql -d your_database -f output/postgresql/01_schema.sql
```

### Generated Java Doesn't Compile

**Error**: Java compilation errors

**Cause**: Missing dependencies or wrong Java version

**Solution**:
```bash
# Check Java version
java -version  # Need Java 11+

# Ensure dependencies in pom.xml or build.gradle
# Spring Boot
# Lombok
# PostgreSQL driver
```

**Common fixes**:
```java
// Add Lombok to pom.xml
<dependency>
    <groupId>org.projectlombok</groupId>
    <artifactId>lombok</artifactId>
    <version>1.18.30</version>
</dependency>

// Enable annotation processing in IDE
// IntelliJ: Settings → Build → Compiler → Annotation Processors → Enable
```

### Generated Rust Doesn't Compile

**Error**: Rust compilation errors

**Cause**: Missing Diesel dependencies

**Solution**:
```bash
# Install Diesel CLI
cargo install diesel_cli --no-default-features --features postgres

# Add to Cargo.toml
[dependencies]
diesel = { version = "2.1", features = ["postgres", "uuid", "chrono"] }
diesel_migrations = "2.1"
chrono = "0.4"
uuid = { version = "1.0", features = ["v4"] }
```

---

## Platform-Specific Issues

### macOS Issues

**Issue**: `xcrun: error: invalid active developer path`

**Cause**: Xcode command line tools not installed

**Solution**:
```bash
xcode-select --install
```

**Issue**: SSL certificate errors

**Solution**:
```bash
# Update certificates
/Applications/Python\ 3.11/Install\ Certificates.command
```

### Linux Issues

**Issue**: `_sqlite3` module not found

**Cause**: Missing SQLite development libraries

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install libsqlite3-dev

# Fedora/RHEL
sudo dnf install sqlite-devel

# Rebuild Python or reinstall
```

**Issue**: Permission errors on `/usr/local`

**Solution**:
```bash
# Don't use sudo - install in user directory
uv pip install -e . --user
```

### Windows Issues

**Issue**: Long path errors

**Cause**: Windows 260 character path limit

**Solution**:
```powershell
# Enable long paths (requires admin)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or clone to shorter path
cd C:\
git clone https://github.com/fraiseql/specql.git
```

**Issue**: `'uv' is not recognized`

**Solution**:
```powershell
# Install via pip instead
pip install uv

# Or add to PATH
$env:Path += ";$env:USERPROFILE\.local\bin"
```

---

## Performance Issues

### Generation is Slow

**Symptom**: Takes >10 seconds for small entities

**Possible causes**:
1. Debug mode enabled
2. Old Python version
3. Large number of entities

**Solution**:
```bash
# Disable debug mode
unset SPECQL_LOG_LEVEL

# Check Python version
python --version  # Upgrade to 3.11+ for better performance

# Profile generation
time specql generate entities/**/*.yaml
```

### High Memory Usage

**Symptom**: >2GB RAM for small project

**Cause**: Parsing many files at once

**Solution**:
```bash
# Generate in batches
specql generate entities/crm/*.yaml
specql generate entities/sales/*.yaml

# Or limit concurrency (future feature)
```

---

## Integration Issues

### PostgreSQL Connection Issues

**Error**: `could not connect to server`

**Solution**:
```bash
# Check PostgreSQL is running
pg_isready

# Start PostgreSQL
# macOS
brew services start postgresql@14

# Linux
sudo systemctl start postgresql

# Check connection
psql -h localhost -U postgres
```

### FraiseQL Integration Issues

**Error**: FraiseQL can't find tables

**Cause**: Schema comments missing or wrong format

**Solution**:
```bash
# Verify comments exist
psql -d your_database -c "
  SELECT obj_description('crm.tb_contact'::regclass, 'pg_class');
"

# Regenerate with SpecQL to ensure comments are correct
specql generate entities/**/*.yaml --target postgresql
```

---

## Debug Mode

### Enable Detailed Logging

```bash
# Set environment variable
export SPECQL_LOG_LEVEL=DEBUG

# Run with verbose flag
specql generate entities/**/*.yaml --verbose

# Python logging
export PYTHONPATH=.
python -m specql.cli generate entities/**/*.yaml
```

### Collect Debug Information

When reporting issues, include:

```bash
# System info
uname -a
python --version
specql --version

# Error output
specql generate problematic.yaml 2>&1 | tee error.log

# YAML file (sanitized)
cat problematic.yaml
```

---

## Getting Help

### Before Asking for Help

1. ✅ Check this troubleshooting guide
2. ✅ Read the [FAQ](FAQ.md)
3. ✅ Search [existing issues](https://github.com/fraiseql/specql/issues)
4. ✅ Try with minimal example
5. ✅ Update to latest version

### How to Ask for Help

**GitHub Issues**: https://github.com/fraiseql/specql/issues

**Include**:
- SpecQL version (`specql --version`)
- Python version (`python --version`)
- Operating system
- Full error message
- Minimal YAML that reproduces issue
- What you've tried

**Example**:
```
**Environment**:
- SpecQL: 0.4.0-alpha
- Python: 3.11.5
- OS: Ubuntu 22.04

**Issue**: Generated SQL has syntax error

**YAML**:
```yaml
entity: Contact
schema: crm
fields:
  name: text
```

**Error**:
```
ERROR: syntax error at or near "INTEGER"
LINE 5:   pk_contact INTEGER PRIMARY KEY AUTO_INCREMENT,
                                           ^
```

**What I tried**:
- Updated to latest SpecQL
- Checked PostgreSQL version (14.2)
- Tested with simple entity
```

---

## Common Fixes Summary

| Issue | Quick Fix |
|-------|-----------|
| Command not found | Add to PATH or use `python -m specql` |
| Python version error | Install Python 3.11+ |
| Invalid field type | Use `text` not `string` |
| Permission denied | Don't use sudo, install with `--user` |
| SQL syntax error | Check PostgreSQL version 12+ |
| Slow generation | Disable debug mode |
| Missing entity | Check name case-sensitivity |
| YAML syntax error | Use 2 spaces, no tabs |

---

**Last updated**: 2024-11-15