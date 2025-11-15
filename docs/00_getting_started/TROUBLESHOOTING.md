# SpecQL Troubleshooting Guide

**Common issues and their solutions** - When things go wrong, start here.

This guide covers the most frequent problems users encounter with SpecQL, organized by category.

## Quick Diagnosis

Before diving into specific issues, run this diagnostic script:

```bash
#!/bin/bash
echo "=== SpecQL Diagnostic Report ==="
echo "Date: $(date)"
echo ""

echo "1. System Information:"
echo "   OS: $(uname -s) $(uname -r)"
echo "   Python: $(python --version 2>&1)"
echo "   uv: $(uv --version 2>&1 || echo 'NOT INSTALLED')"
echo ""

echo "2. SpecQL Installation:"
echo "   SpecQL command: $(which specql 2>/dev/null || echo 'NOT FOUND')"
if command -v specql >/dev/null 2>&1; then
    echo "   Version: $(specql --version 2>&1)"
fi
echo ""

echo "3. Dependencies:"
echo "   Git: $(git --version 2>&1 | head -1)"
echo "   PostgreSQL: $(psql --version 2>&1 | head -1 || echo 'NOT INSTALLED')"
echo ""

echo "4. Test Generation:"
echo "   Testing basic YAML parsing..."
if specql generate entities/examples/contact_lightweight.yaml --dry-run >/dev/null 2>&1; then
    echo "   ✓ YAML parsing works"
else
    echo "   ✗ YAML parsing failed"
fi
echo ""

echo "=== End Diagnostic Report ==="
```

Save as `diagnose.sh`, run with `bash diagnose.sh`, and include the output when asking for help.

---

## Installation Issues

### "uv command not found"

**Symptoms**: `uv: command not found` after installation.

**Solutions**:

1. **Check PATH**:
   ```bash
   # macOS/Linux
   echo $PATH | grep -q "\.local/bin" && echo "PATH OK" || echo "PATH missing .local/bin"

   # Add to PATH if missing
   export PATH="$HOME/.local/bin:$PATH"
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

2. **Reinstall uv**:
   ```bash
   # Remove old installation
   rm -rf ~/.local/bin/uv ~/.local/share/uv

   # Reinstall
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Windows PATH**:
   - Open System Properties → Advanced → Environment Variables
   - Add `%USERPROFILE%\.local\bin` to PATH
   - Restart terminal

### "Python version 3.11+ required"

**Symptoms**: `RuntimeError: Python 3.11+ required, found 3.10.2`

**Solutions**:

1. **Install Python 3.11+**:
   ```bash
   # Using pyenv (recommended)
   curl https://pyenv.run | bash
   echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   pyenv install 3.11.5
   pyenv global 3.11.5

   # Verify
   python --version  # Should show 3.11.x
   ```

2. **Use uv's Python management**:
   ```bash
   uv python install 3.11
   uv python pin 3.11
   ```

3. **Check active Python**:
   ```bash
   which python
   python --version
   ```

### "Permission denied" during installation

**Symptoms**: `PermissionError: [Errno 13] Permission denied`

**Solutions**:

1. **Install to user directory**:
   ```bash
   uv pip install --user -e .
   ```

2. **Use virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate   # Windows
   uv pip install -e .
   ```

3. **Fix permissions** (not recommended):
   ```bash
   sudo chown -R $USER ~/.local
   ```

### "specql command not found" after installation

**Symptoms**: Installation succeeds but `specql` command unavailable.

**Solutions**:

1. **Check installation**:
   ```bash
   uv pip list | grep specql
   which specql
   ```

2. **Reinstall**:
   ```bash
   uv pip uninstall specql
   uv pip install -e .
   ```

3. **Check shell profile**:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"
   ```

---

## Generation Issues

### "No such file or directory" for entity YAML

**Symptoms**: `FileNotFoundError: [Errno 2] No such file or directory: 'entities/contact.yaml'`

**Solutions**:

1. **Check file path**:
   ```bash
   ls -la entities/
   find . -name "*.yaml" -type f
   ```

2. **Use absolute path**:
   ```bash
   specql generate /full/path/to/entities/contact.yaml
   ```

3. **Check working directory**:
   ```bash
   pwd
   ls -la
   ```

### YAML parsing errors

**Symptoms**: `yaml.YAMLError: mapping values are not allowed here`

**Common causes**:

1. **Indentation issues**:
   ```yaml
   # Wrong
   entity: Contact
     fields:  # Wrong indentation
       name: text

   # Correct
   entity: Contact
   fields:
     name: text
   ```

2. **Invalid field types**:
   ```yaml
   # Wrong
   fields:
     age: integer  # Should be 'integer' not 'int'

   # Correct
   fields:
     age: integer
   ```

3. **Missing colons**:
   ```yaml
   # Wrong
   entity Contact  # Missing colon

   # Correct
   entity: Contact
   ```

**Debug YAML**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('entities/contact.yaml'))"

# Check with yamllint
yamllint entities/contact.yaml
```

### "Unknown field type" errors

**Symptoms**: `ValueError: Unknown field type 'varchar'`

**Solutions**:

Supported field types:
- `text` - Variable length string
- `integer` - Whole numbers
- `decimal` - Fixed precision numbers
- `boolean` - True/false
- `timestamp` - Date and time
- `date` - Date only
- `uuid` - Universally unique identifier
- `json` - JSON data
- `enum(value1, value2, value3)` - Predefined choices

```yaml
# Correct usage
fields:
  status: enum(active, inactive, pending)
  metadata: json
  created_at: timestamp
```

### Action syntax errors

**Symptoms**: `SyntaxError: invalid syntax in action definition`

**Common issues**:

1. **Invalid step types**:
   ```yaml
   # Wrong
   actions:
     - name: update_status
       steps:
         - sql: UPDATE table SET...  # 'sql' not supported

   # Correct
   actions:
     - name: update_status
       steps:
         - update: Contact SET status = 'active'
   ```

2. **Missing required fields**:
   ```yaml
   # Wrong
   actions:
     - name: publish  # Missing 'steps'

   # Correct
   actions:
     - name: publish
       steps:
         - update: Post SET published = true
   ```

---

## Database Issues

### PostgreSQL connection errors

**Symptoms**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:

1. **Check PostgreSQL status**:
   ```bash
   # Linux/macOS
   sudo systemctl status postgresql

   # macOS with Homebrew
   brew services list | grep postgres

   # Start if stopped
   sudo systemctl start postgresql
   ```

2. **Check connection details**:
   ```bash
   # Test connection
   psql -h localhost -U postgres -d postgres

   # Check port
   ss -tlnp | grep 5432
   ```

3. **Create database**:
   ```bash
   createdb myapp_dev
   psql -c "CREATE USER myapp WITH PASSWORD 'secret';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE myapp_dev TO myapp;"
   ```

### Schema creation fails

**Symptoms**: `ERROR: schema "myschema" does not exist`

**Solutions**:

1. **Create schema first**:
   ```sql
   CREATE SCHEMA IF NOT EXISTS myschema;
   GRANT USAGE ON SCHEMA myschema TO myapp_user;
   ```

2. **Check permissions**:
   ```sql
   -- Grant schema permissions
   GRANT ALL ON SCHEMA myschema TO myapp_user;

   -- Grant table permissions
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA myschema TO myapp_user;
   ```

### Function execution errors

**Symptoms**: `ERROR: function my_action(uuid) does not exist`

**Solutions**:

1. **Check function exists**:
   ```sql
   SELECT * FROM pg_proc WHERE proname LIKE 'fn_%';
   ```

2. **Check search path**:
   ```sql
   SHOW search_path;
   SET search_path TO myschema, public;
   ```

3. **Reapply functions**:
   ```bash
   psql mydb < generated/postgresql/myschema/02_functions.sql
   ```

---

## Platform-Specific Issues

### macOS Issues

**Homebrew conflicts**:
```bash
# If Homebrew Python conflicts
export PATH="/usr/local/bin:/usr/bin:/bin"
```

**Xcode Command Line Tools**:
```bash
xcode-select --install
```

### Windows Issues

**Path separators**:
```powershell
# Use forward slashes in YAML paths
entity: Contact
# Wrong: C:\path\to\file.yaml
# Correct: C:/path/to/file.yaml
```

**Execution policy**:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**WSL recommendations**:
- Use WSL2 with Ubuntu for best compatibility
- Avoid mixing Windows and WSL file paths

### Linux Issues

**Package manager conflicts**:
```bash
# Ubuntu/Debian
sudo apt install python3.11 python3.11-venv

# CentOS/RHEL
sudo yum install python311 python311-pip
```

**Permission issues**:
```bash
# Add user to relevant groups
sudo usermod -a -G dialout $USER  # For serial devices
```

---

## Code Generation Issues

### Java generation fails

**Symptoms**: Errors during Java code generation.

**Solutions**:

1. **Check Java version**:
   ```bash
   java -version  # Should be 11+
   ```

2. **Validate package structure**:
   ```yaml
   # Correct package declaration
   entity: Contact
   schema: crm
   # Generates: com.example.crm.Contact
   ```

### Rust generation fails

**Symptoms**: Compilation errors in generated Rust code.

**Solutions**:

1. **Check Rust version**:
   ```bash
   rustc --version  # Should be 1.70+
   cargo --version
   ```

2. **Add dependencies**:
   ```toml
   [dependencies]
   diesel = { version = "2.0", features = ["postgres", "uuid"] }
   uuid = { version = "1.0", features = ["v4"] }
   ```

### TypeScript generation fails

**Symptoms**: Type errors in generated TypeScript.

**Solutions**:

1. **Check Node.js version**:
   ```bash
   node --version  # Should be 16+
   npm --version
   ```

2. **Install dependencies**:
   ```bash
   npm install prisma @prisma/client
   npm install typescript @types/node
   ```

---

## Reverse Engineering Issues

### PostgreSQL reverse engineering fails

**Symptoms**: `ERROR: permission denied for table pg_class`

**Solutions**:

1. **Grant permissions**:
   ```sql
   -- Connect as superuser
   GRANT SELECT ON pg_class TO myuser;
   GRANT SELECT ON pg_namespace TO myuser;
   GRANT SELECT ON pg_attribute TO myuser;
   GRANT SELECT ON pg_type TO myuser;
   ```

2. **Use superuser**:
   ```bash
   specql reverse postgresql --user postgres --password secret mydb
   ```

### Python reverse engineering fails

**Symptoms**: Import errors or parsing failures.

**Solutions**:

1. **Check Python file syntax**:
   ```bash
   python -m py_compile mymodel.py
   ```

2. **Install dependencies**:
   ```bash
   pip install dataclasses-json pydantic
   ```

3. **Supported formats**:
   ```python
   # Supported
   from dataclasses import dataclass
   @dataclass
   class Contact:
       name: str
       email: str

   # Also supported
   from pydantic import BaseModel
   class Contact(BaseModel):
       name: str
       email: str
   ```

---

## Performance Issues

### Generation is slow

**Symptoms**: Code generation takes more than 30 seconds.

**Solutions**:

1. **Check system resources**:
   ```bash
   # CPU and memory usage
   top -l 1 | head -10
   ```

2. **Use dry-run for testing**:
   ```bash
   specql generate entity.yaml --dry-run  # Faster testing
   ```

3. **Profile performance**:
   ```bash
   time specql generate entity.yaml
   ```

### Large schema issues

**Symptoms**: Out of memory errors with large schemas.

**Solutions**:

1. **Increase memory limits**:
   ```bash
   # Linux
   ulimit -v unlimited

   # Or set specific limit
   export PYTHON_MAX_MEM=4GB
   ```

2. **Split large schemas**:
   ```yaml
   # Instead of one huge file, split into multiple
   # entities/user.yaml
   # entities/product.yaml
   # entities/order.yaml
   ```

---

## Getting Help

### Before asking for help:

1. **Run diagnostics**: Use the diagnostic script at the top of this guide
2. **Check existing issues**: Search [GitHub Issues](https://github.com/fraiseql/specql/issues)
3. **Try minimal reproduction**: Create the smallest possible example that fails

### How to ask for help:

**Good issue report**:
```
**Title**: PostgreSQL generation fails with "permission denied"

**Environment**:
- OS: Ubuntu 22.04
- Python: 3.11.2
- SpecQL: 0.4.0-alpha
- PostgreSQL: 15.2

**Steps to reproduce**:
1. Created entity YAML...
2. Ran `specql generate entity.yaml`
3. Got error: `permission denied for table pg_class`

**Expected behavior**:
Schema should generate successfully

**Additional context**:
- Database user has CREATEDB privilege
- Can connect to database manually
- Diagnostic output: [paste here]
```

**Bad issue report**:
```
"SpecQL doesn't work" - please help!
```

### Community resources:

- **GitHub Issues**: https://github.com/fraiseql/specql/issues
- **Discussions**: https://github.com/fraiseql/specql/discussions
- **Documentation**: https://specql.dev/docs

---

## Advanced Troubleshooting

### Debug mode

Enable verbose logging:
```bash
export SPECQL_DEBUG=1
specql generate entity.yaml --verbose
```

### Manual testing

Test components individually:
```bash
# Test YAML parsing only
python -c "
import yaml
from specql.core.parser import SpecQLParser
data = yaml.safe_load(open('entity.yaml'))
parser = SpecQLParser()
ast = parser.parse(data)
print('YAML parsing successful')
"

# Test database connection
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://user:pass@localhost/db')
print('Database connection successful')
conn.close()
"
```

### Reset installation

Complete reset for testing:
```bash
# Remove all SpecQL files
rm -rf ~/.local/lib/python*/site-packages/specql*
rm -rf ~/.local/bin/specql

# Clean repository
cd specql
git clean -fdx
git reset --hard HEAD

# Reinstall fresh
uv sync
uv pip install -e .
```

---

**Still stuck?** Open a detailed issue on [GitHub](https://github.com/fraiseql/specql/issues) with your diagnostic output.