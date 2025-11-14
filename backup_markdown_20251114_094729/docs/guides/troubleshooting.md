# Troubleshooting Guide

Quick solutions to common SpecQL issues.

**Can't find your issue?** Search existing issues or create a new one: https://github.com/fraiseql/specql/issues

---

## Table of Contents

1. [Parse Errors](#parse-errors)
2. [Validation Errors](#validation-errors)
3. [Generation Errors](#generation-errors)
4. [Database Errors](#database-errors)
5. [CLI Issues](#cli-issues)
6. [Performance Issues](#performance-issues)
7. [Getting Help](#getting-help)

---

## Parse Errors

### "Missing 'entity' key"

**Error**:
```
Failed to parse entities/contact.yaml: Missing required key 'entity'
```

**Cause**: File uses `import:` instead of `entity:` (import-only file).

**Solution**: Import files reference stdlib and don't generate directly.

```yaml
# ❌ Import-only (doesn't generate)
import: stdlib/crm/contact

# ✅ Full entity (generates SQL)
entity: Contact
schema: crm
fields:
  email: text
```

**When to use imports**: Extending stdlib entities with custom fields.

---

### "Unknown field type"

**Error**:
```
Parse Error: Unknown field type 'string' at line 5
```

**Cause**: SpecQL uses different type names than some SQL dialects.

**Solution**: Use SpecQL type names

| ❌ Don't Use | ✅ Use Instead |
|-------------|---------------|
| `string` | `text` |
| `int` | `integer` |
| `bool` | `boolean` |
| `varchar` | `text` |
| `numeric` | `decimal` |

**Reference**: `docs/reference/yaml-reference.md#scalar-types`

---

### "Invalid YAML syntax"

**Error**:
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Cause**: YAML indentation or syntax error.

**Solution**: Check YAML formatting

```yaml
# ❌ Invalid (missing colon)
entity Contact
schema crm

# ✅ Valid
entity: Contact
schema: crm

# ❌ Invalid (inconsistent indentation)
fields:
 email: text
   name: text

# ✅ Valid (2-space indentation)
fields:
  email: text
  name: text
```

**Tools**: Use YAML linter (e.g., `yamllint`)

```bash
uv add --dev yamllint
yamllint entities/contact.yaml
```

---

### "Duplicate key"

**Error**:
```
yaml.constructor.ConstructorError: found duplicate key 'email'
```

**Cause**: Same field name appears twice.

**Solution**: Remove duplicate or rename one field

```yaml
# ❌ Duplicate
fields:
  email: text
  email: email  # Duplicate key

# ✅ Fixed
fields:
  email: text
  alternate_email: email
```

---

## Validation Errors

### "Table code already assigned"

**Error**:
```
ValueError: Table code '012311' already assigned to Contact
```

**Cause**: Multiple entities have the same `organization.table_code`.

**Solution**: Check uniqueness

```bash
specql check-codes entities/**/*.yaml
```

**Output**:
```
❌ Duplicate table codes found

⚠️  Code 012311 assigned to:
  • Contact (entities/crm/contact.yaml)
  • Customer (entities/crm/customer.yaml)
```

**Fix**: Assign unique codes or remove `table_code` if not needed.

---

### "Referenced entity not found"

**Error**:
```
Validation Error: Field 'company' references undefined entity 'Company'
```

**Cause**: `ref(Company)` but no `Company` entity exists.

**Solution**:
1. Create referenced entity first
2. Or fix typo in reference name

```yaml
# ❌ References missing entity
entity: Contact
fields:
  company: ref(Company)  # Company.yaml doesn't exist

# ✅ Option 1: Create Company.yaml
# entities/company.yaml
entity: Company
schema: crm
fields:
  name: text

# ✅ Option 2: Fix typo
entity: Contact
fields:
  company: ref(Organization)  # Correct entity name
```

---

### "Invalid enum value"

**Error**:
```
Validation Error: Enum must have at least 2 values
```

**Cause**: `enum()` with 0 or 1 value.

**Solution**: Enums need 2+ values

```yaml
# ❌ Invalid
status: enum(active)  # Only 1 value

# ✅ Valid
status: enum(active, inactive)  # 2+ values

# ✅ Alternative: Use boolean
active: boolean
```

---

### "Circular reference detected"

**Error**:
```
Validation Error: Circular reference: Contact → Company → Contact
```

**Cause**: Entities reference each other in a loop.

**Solution**: Break circle with nullable reference

```yaml
# ❌ Circular
# Contact → Company
entity: Contact
fields:
  company: ref(Company)

# Company → Contact
entity: Company
fields:
  primary_contact: ref(Contact)  # Circular!

# ✅ Fixed: Make one nullable
entity: Company
fields:
  primary_contact: ref(Contact)?  # Optional breaks circle
```

---

## Generation Errors

### "No such file or directory"

**Error**:
```
Error: Invalid value for 'ENTITY_FILES': Path 'entities/contact.yaml' does not exist
```

**Cause**: File path is wrong or command run from wrong directory.

**Solution**: Use absolute paths or run from project root

```bash
# ❌ Wrong directory
cd /tmp
specql generate entities/contact.yaml  # Fails

# ✅ Run from project root
cd /path/to/project
specql generate entities/contact.yaml

# ✅ Or use absolute path
specql generate /path/to/project/entities/contact.yaml
```

---

### "Confiture build failed"

**Error**:
```
❌ Confiture build failed: No such file 'confiture.yaml'
```

**Cause**: Confiture not configured or not installed.

**Solution**:

```bash
# 1. Install Confiture
uv add fraiseql-confiture

# 2. Create confiture.yaml
cat > confiture.yaml << 'EOF'
schema_dirs:
  - path: db/schema/10_tables
    order: 10

environments:
  local:
    database_url: postgresql://localhost/mydb
EOF

# 3. Verify
specql generate entities/contact.yaml
```

---

### "Schema not in domain registry"

**Error**:
```
ValueError: Schema 'crm' not found in domain registry
```

**Cause**: Schema not registered in `registry/domain_registry.yaml`.

**Solution**: Add schema to registry

```yaml
# registry/domain_registry.yaml
domains:
  crm:
    type: multi_tenant
    description: "Customer relationship management"
```

---

### "Output directory not found"

**Error**:
```
FileNotFoundError: Directory 'db/schema/10_tables' does not exist
```

**Cause**: Output directories not created.

**Solution**: Create directory structure

```bash
mkdir -p db/schema/{00_foundation,10_tables,20_helpers,30_functions,40_metadata}
```

---

## Database Errors

### "relation does not exist"

**Error**:
```sql
psql: ERROR: relation "crm.tb_contact" does not exist
```

**Cause**: Schema not applied to database.

**Solution**: Apply generated SQL files

```bash
# Apply foundation first
psql mydb -f db/schema/00_foundation/000_app_foundation.sql

# Apply tables
psql mydb -f db/schema/10_tables/*.sql

# Or use Confiture
confiture migrate up --env local
```

---

### "constraint violation"

**Error**:
```sql
ERROR: insert or update on table "tb_contact" violates foreign key constraint "fk_tb_contact_company"
DETAIL: Key (company)=(999) is not present in table "tb_company".
```

**Cause**: Referenced record doesn't exist.

**Solution**: Insert parent records first

```sql
-- Insert in dependency order
INSERT INTO crm.tb_company (name) VALUES ('Acme Corp');
INSERT INTO crm.tb_contact (email, company) VALUES ('john@acme.com', 1);
```

---

### "column does not exist"

**Error**:
```sql
ERROR: column "company_id" does not exist
```

**Cause**: SpecQL uses different column naming (no `_id` suffix for ref fields).

**Solution**: Use correct column name

```sql
# ❌ Wrong (old naming)
SELECT * FROM crm.tb_contact WHERE company_id = 1;

# ✅ Correct (SpecQL naming)
SELECT * FROM crm.tb_contact WHERE company = 1;
```

**YAML**:
```yaml
fields:
  company: ref(Company)  # Column name is 'company' (NOT 'company_id')
```

---

### "permission denied"

**Error**:
```sql
ERROR: permission denied for schema crm
```

**Cause**: Database user lacks permissions.

**Solution**: Grant permissions

```sql
-- As superuser
GRANT USAGE ON SCHEMA crm TO myapp_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA crm TO myapp_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA crm TO myapp_user;
```

---

## CLI Issues

### "Command not found: specql"

**Error**:
```bash
$ specql
command not found: specql
```

**Cause**: SpecQL not installed or UV environment not activated.

**Solution**:

```bash
# Option 1: Use uv run
uv run specql --version

# Option 2: Install globally
uv add specql-generator
specql --version

# Option 3: Check PATH
which specql
echo $PATH
```

---

### "Permission denied"

**Error**:
```bash
$ specql generate entities/contact.yaml
Permission denied: db/schema/10_tables/contact.sql
```

**Cause**: File permissions issue.

**Solution**:

```bash
# Check permissions
ls -la db/schema/10_tables/

# Fix permissions
chmod 644 db/schema/10_tables/*.sql
chmod 755 db/schema/10_tables/
```

---

### "Timeout during generation"

**Error**:
```
TimeoutError: Generation took longer than 30 seconds
```

**Cause**: Very large number of entities or complex actions.

**Solution**: Generate in batches

```bash
# ❌ All at once (slow)
specql generate entities/**/*.yaml

# ✅ By schema (faster)
specql generate entities/crm/*.yaml
specql generate entities/commerce/*.yaml

# ✅ Parallel generation
find entities -name '*.yaml' | xargs -P 4 -n 1 specql generate
```

---

## Performance Issues

### "Generation is slow"

**Symptom**: `specql generate` takes >10 seconds for small number of entities.

**Causes & Solutions**:

1. **Too many glob patterns**
   ```bash
   # ❌ Slow
   specql generate entities/*/*.yaml

   # ✅ Faster
   specql generate entities/**/*.yaml
   ```

2. **Confiture rebuilding**
   ```bash
   # Skip Confiture if not needed
   specql generate entities/contact.yaml --skip-confiture
   ```

3. **Large number of actions**
   - Profile generation: `specql generate --profile`
   - Split complex actions into smaller ones

---

### "Database queries are slow"

**Symptom**: Queries on generated tables are slow.

**Causes & Solutions**:

1. **Missing indexes**
   ```sql
   -- Add custom index
   CREATE INDEX idx_tb_contact_email ON crm.tb_contact(email);
   ```

2. **Large JSON columns**
   ```sql
   -- Add GIN index (auto-generated for json fields, but verify)
   CREATE INDEX idx_tb_contact_metadata ON crm.tb_contact USING GIN (metadata);
   ```

3. **Soft-deleted records**
   ```sql
   -- Filter deleted records
   SELECT * FROM crm.tb_contact WHERE deleted_at IS NULL;
   ```

---

## Getting Help

### Before Creating an Issue

1. **Search existing issues**: https://github.com/fraiseql/specql/issues
2. **Check documentation**:
   - YAML Reference: `docs/reference/yaml-reference.md`
   - CLI Reference: `docs/reference/cli-reference.md`
   - Migration Guide: `docs/guides/migration-guide.md`
3. **Run validation**: `specql validate entities/**/*.yaml --verbose`

### Creating a Good Issue

Include:

1. **SpecQL version**:
   ```bash
   specql --version
   # Or: git rev-parse HEAD
   ```

2. **Minimal YAML example**:
   ```yaml
   entity: Contact
   schema: crm
   fields:
     email: text
   ```

3. **Complete error message**:
   ```
   [Copy full error output]
   ```

4. **Steps to reproduce**:
   ```bash
   1. Create entities/contact.yaml with above content
   2. Run: specql generate entities/contact.yaml
   3. Error occurs
   ```

5. **Expected vs actual behavior**:
   - Expected: Should generate table
   - Actual: Parse error

### Community Resources

- **GitHub Issues**: https://github.com/fraiseql/specql/issues
- **Documentation**: `docs/`
- **Examples**: `examples/entities/`
- **Stdlib**: `stdlib/` (reference implementations)

---

## Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set log level
export SPECQL_LOG_LEVEL=DEBUG

# Run with verbose output
specql generate entities/contact.yaml --verbose

# Check logs
tail -f /tmp/specql.log
```

---

## Common Gotchas

### 1. Auto-Generated Fields
❌ **Don't include** in YAML: `id`, `created_at`, `updated_at`, `tenant_id`
✅ **These are automatic** - SpecQL adds them

### 2. Field Names vs Column Names
```yaml
company: ref(Company)  # Field name is 'company'
# Column name is also 'company' (NOT 'company_id')
```

### 3. Enum Values Are Case-Sensitive
```yaml
status: enum(Active, Inactive)  # Capital A, I
# ❌ INSERT: status = 'active'  (lowercase fails)
# ✅ INSERT: status = 'Active'
```

### 4. Nullable References
```yaml
# ❌ Circular reference
company: ref(Company)
# Company also refs Contact

# ✅ Break circle
company: ref(Company)?  # Nullable
```

### 5. Import vs Entity
```yaml
# Import = reference only (doesn't generate)
import: stdlib/crm/contact

# Entity = full definition (generates SQL)
entity: Contact
```

---

## Diagnostic Commands

### Check Entity Validity
```bash
specql validate entities/contact.yaml --verbose
```

### Check Table Codes
```bash
specql check-codes entities/**/*.yaml
```

### Compare Generated vs Existing
```bash
specql diff entities/contact.yaml --compare db/schema/10_tables/contact.sql
```

### Test Database Connection
```bash
psql $DATABASE_URL -c "SELECT version();"
```

### Check Confiture Config
```bash
confiture validate confiture.yaml
```

---

**Still stuck?** Create a detailed issue: https://github.com/fraiseql/specql/issues/new