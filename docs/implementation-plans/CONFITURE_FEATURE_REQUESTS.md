# Confiture Feature Requests for SpecQL Integration

**Context**: We're integrating Confiture with SpecQL's hexadecimal registry system and need to assess if Confiture's current features support our architecture or if we need additional capabilities.

**Date**: 2025-11-09
**Current Confiture Version**: v0.1.0 (Beta, Production-Ready)

---

## 🔍 Current Integration Challenges

### **Challenge 1: Hexadecimal File Naming**
**Our Need**: Files named with hexadecimal codes (e.g., `012A31_tb_contact.sql`)

**Question**: Does Confiture's deterministic ordering work with hexadecimal prefixes?

**Current Confiture Behavior** (from documentation):
- Orders files deterministically within each `schema_dirs` path
- Typically expects numeric prefixes or alphabetic ordering

**Potential Issue**:
```
db/schema/10_tables/
├── 012311_tb_contact.sql      # Hex: 74513 decimal
├── 012A31_tb_company.sql      # Hex: 76337 decimal
└── 01F231_tb_account.sql      # Hex: 127537 decimal
```

**Question for Confiture Team**:
- Does Confiture sort `012A31` correctly as hexadecimal (or as string)?
- If string sorting, would it handle `01F` before `012`? (Wrong order!)

**Workaround** (if needed):
- Convert hex to decimal for filenames: `076337_tb_company.sql`
- Keep hex in table codes, decimal in filenames

---

### **Challenge 2: Multi-Level Directory Hierarchies**

**Our Architecture**:
```
db/schema/
├── 01_write_side/              # Layer 1
│   └── 012_crm/                # Layer 2 (domain)
│       └── 0123_customer/      # Layer 3 (subdomain)
│           └── 01231_group/    # Layer 4 (entity group)
│               └── 012311_tb_contact.sql  # Layer 5 (file)
```

**Current Confiture Support**:
```yaml
# confiture.yaml
schema_dirs:
  - path: db/schema/01_write_side
    order: 10
  - path: db/schema/02_read_side
    order: 20
```

**Issue**: Confiture expects **flat directory lists**, not nested hierarchies.

**Options**:

#### **Option A: Flatten for Confiture**
```yaml
# List all leaf directories explicitly
schema_dirs:
  - path: db/schema/01_write_side/012_crm/0123_customer/01231_group
    order: 10123110
  - path: db/schema/01_write_side/012_crm/0123_customer/01232_group
    order: 10123120
  # ... (would need 100s of entries for many entities!)
```
❌ **Unscalable**: Need to update config for every new entity

#### **Option B: Use Flat Directories (Current Plan)**
```yaml
# Confiture-compatible flat structure
schema_dirs:
  - path: db/schema/10_tables
    order: 10
  - path: db/schema/30_functions
    order: 30
```
✅ **Works but loses hierarchy benefits**

#### **Option C: Request Recursive Directory Support**
```yaml
# PROPOSED FEATURE
schema_dirs:
  - path: db/schema/01_write_side
    order: 10
    recursive: true          # NEW: Scan all subdirectories
    sort_by: path            # Sort by full path (preserves hierarchy)
```

**Feature Request**:
- **Recursive directory scanning** with `recursive: true`
- Maintains file order by full path (naturally preserves hierarchy)
- No need to list every subdirectory explicitly

---

### **Challenge 3: Dynamic Schema Discovery**

**Our Use Case**: Generate entities dynamically, Confiture should auto-discover new files

**Current Confiture Behavior**:
- Reads `confiture.yaml` for explicit directory list
- Requires config update when adding new `schema_dirs`

**Problem**:
```bash
# Day 1: Generate Contact
python -m src.cli.generate entities contact.yaml
# Creates: db/schema/01_write_side/012_crm/.../contact.sql

# Day 2: Generate Company
python -m src.cli.generate entities company.yaml
# Creates: db/schema/01_write_side/013_finance/.../company.sql

# Confiture build
confiture build --env local
# ❌ Won't find company.sql if db/schema/01_write_side/013_finance not in config!
```

**Feature Request**:
```yaml
# PROPOSED FEATURE
schema_dirs:
  - path: db/schema
    recursive: true
    exclude:                 # NEW: Exclude patterns
      - "**/*.bak"
      - "**/temp/**"
    include:                 # NEW: Include patterns
      - "**/*.sql"
    auto_discover: true      # NEW: Don't require pre-listing
```

**Benefit**: Add entities without updating `confiture.yaml`

---

### **Challenge 4: Metadata Comments Preservation**

**Our Use Case**: FraiseQL `@fraiseql:*` comments must be preserved exactly

**Current Confiture Behavior** (need to verify):
- Does Confiture strip/modify SQL comments during build?
- Are `COMMENT ON` statements preserved?

**Example**:
```sql
-- File: db/schema/40_metadata/contact_fraiseql.sql
COMMENT ON TABLE crm.tb_contact IS
  '@fraiseql:type name=Contact,schema=crm';

COMMENT ON COLUMN crm.tb_contact.email IS
  '@fraiseql:field name=email,type=String!';
```

**Question for Confiture Team**:
- Are all SQL comments preserved byte-for-byte?
- Are `COMMENT ON` statements preserved in build output?
- Any comment preprocessing or formatting?

**If Not Preserved**:
- This would be a **blocking issue** for FraiseQL integration
- FraiseQL depends on these comments for GraphQL schema generation

---

### **Challenge 5: Build Output with Hierarchical Context**

**Our Need**: Debug which file contributed which SQL in the final migration

**Current Confiture Behavior**:
```sql
-- migrations/001_schema.sql (concatenated output)
CREATE TABLE crm.tb_contact (...);
CREATE TABLE finance.tb_invoice (...);
CREATE FUNCTION crm.qualify_lead (...);
```

**Problem**: No indication of **which file** each statement came from

**Feature Request**: Add source file markers
```sql
-- migrations/001_schema.sql (with source markers)

-- SOURCE: db/schema/10_tables/contact.sql (012311)
CREATE TABLE crm.tb_contact (...);

-- SOURCE: db/schema/10_tables/invoice.sql (013A21)
CREATE TABLE finance.tb_invoice (...);

-- SOURCE: db/schema/30_functions/contact_actions.sql (032311)
CREATE FUNCTION crm.qualify_lead (...);
```

**Benefit**:
- Easy debugging (which file has syntax error?)
- Audit trail (what came from where?)
- Helps with conflict resolution

**Implementation Suggestion**:
```yaml
# confiture.yaml
build:
  add_source_markers: true   # NEW: Add -- SOURCE: comments
  marker_format: "-- SOURCE: {path} ({table_code})"  # Configurable format
```

---

### **Challenge 6: Split Output by Component Type**

**Our Need**: Generate separate migration files for different components

**Use Case**:
```bash
# Generate 3 separate migrations instead of 1 combined
confiture build --env local --split-by layer

# Output:
migrations/001_tables.sql      # All from 10_tables/
migrations/002_functions.sql   # All from 30_functions/
migrations/003_metadata.sql    # All from 40_metadata/
```

**Why Needed**:
- Tables must be created before functions (dependency order)
- Can apply tables first, test, then apply functions
- Metadata can be applied last (optional for some deployments)

**Current Workaround**:
```yaml
# Define separate environments for each layer
environments:
  tables_only:
    schema_dirs:
      - path: db/schema/10_tables
  functions_only:
    schema_dirs:
      - path: db/schema/30_functions
```

Then:
```bash
confiture build --env tables_only --output migrations/001_tables.sql
confiture build --env functions_only --output migrations/002_functions.sql
```

**Feature Request**:
```yaml
# PROPOSED FEATURE
build:
  split_output: true
  split_strategy: by_directory  # or 'by_layer', 'by_domain'
  output_template: "migrations/{order:03d}_{dir_name}.sql"
```

```bash
confiture build --env local --split

# Auto-generates:
migrations/010_tables.sql
migrations/030_functions.sql
migrations/040_metadata.sql
```

---

### **Challenge 7: Registry Integration Hooks**

**Our Need**: Call custom Python code during Confiture build

**Use Case**: Update `domain_registry.yaml` after successful build

**Current Confiture Behavior**:
- No hooks for custom code execution
- Pure SQL concatenation + migration tracking

**Feature Request**: Build lifecycle hooks
```yaml
# confiture.yaml
hooks:
  pre_build:
    - command: "python scripts/validate_registry.py"
      description: "Validate registry consistency"

  post_build:
    - command: "python scripts/update_registry_timestamps.py"
      description: "Update last_built timestamps"

  pre_migrate:
    - command: "python scripts/backup_database.py"
      description: "Backup before migration"

  post_migrate:
    - command: "python scripts/notify_team.py"
      description: "Notify deployment complete"
```

**Benefit**:
- Integrate with SpecQL registry system
- Custom validation before build
- Notifications, backups, cleanup

---

### **Challenge 8: Table Code Validation**

**Our Need**: Ensure generated SQL matches registry table codes

**Problem**:
```sql
-- File: db/schema/10_tables/contact.sql
-- Registry says: tb_contact should have code 012311
-- But file contains: CREATE TABLE crm.tb_contact_old (...)
```

**Feature Request**: Pre-build validation
```yaml
# confiture.yaml
validation:
  enabled: true
  rules:
    - type: table_name_pattern
      pattern: "^tb_[a-z_]+$"
      message: "Table names must start with tb_"

    - type: custom_validator
      script: "python scripts/validate_table_codes.py"
      args: ["--registry", "registry/domain_registry.yaml"]
```

**Validation Script**:
```python
# scripts/validate_table_codes.py
import sys
from src.generators.schema.naming_conventions import NamingConventions

def validate_sql_file(filepath, registry):
    """Ensure SQL file matches registry table code"""
    # Extract table name from SQL
    # Look up in registry
    # Validate code matches filename
    # Return errors if mismatch
```

---

### **Challenge 9: Incremental Builds**

**Our Need**: Only rebuild changed files (performance optimization)

**Current Confiture Behavior** (need to verify):
- Rebuild entire schema every time?
- Or track file checksums for incremental builds?

**Use Case**:
```bash
# Day 1: Generate 100 entities
confiture build --env local
# Takes 5 seconds (100 files × 50ms)

# Day 2: Change 1 entity
python -m src.cli.generate entities contact.yaml --use-registry
confiture build --env local --incremental
# Takes 50ms (only rebuild changed file)
```

**Feature Request** (if not already supported):
```yaml
# confiture.yaml
build:
  incremental: true
  cache_dir: .confiture/cache
  hash_algorithm: sha256
```

**Benefit**:
- Faster iteration during development
- Only rebuild what changed
- Crucial for large projects (100+ entities)

---

### **Challenge 10: Environment-Specific Directory Overrides**

**Our Need**: Different directory structures for local vs production

**Use Case**:
```yaml
# Local: Use hierarchical structure for debugging
environments:
  local:
    schema_dirs:
      - path: generated/migrations/01_write_side
        recursive: true

# Production: Use flat structure for simplicity
  production:
    schema_dirs:
      - path: db/schema/10_tables
      - path: db/schema/30_functions
```

**Current Support**: ✅ Already works!

**Enhancement Request**: Directory path variables
```yaml
# PROPOSED FEATURE
variables:
  schema_root: ${SCHEMA_ROOT:-db/schema}

environments:
  local:
    schema_dirs:
      - path: ${schema_root}/10_tables
      - path: ${schema_root}/30_functions
```

**Benefit**: Easier CI/CD configuration

---

## 📋 Summary: Feature Request Priority

### **P0 (Critical - Blockers)**

1. **Comment Preservation** (Challenge 4)
   - **Why**: FraiseQL integration depends on `@fraiseql:*` comments
   - **Question**: Are SQL comments preserved exactly?
   - **If Not Supported**: We cannot use Confiture

2. **Hexadecimal File Ordering** (Challenge 1)
   - **Why**: Our entire naming system uses hex codes
   - **Question**: Does Confiture sort hex prefixes correctly?
   - **Workaround**: Convert to decimal filenames (loses elegance)

---

### **P1 (High - Major Quality of Life)**

3. **Recursive Directory Support** (Challenge 2)
   - **Why**: Enables full hierarchical registry structure
   - **Current**: Must use flat directories
   - **Request**: `recursive: true` option

4. **Source File Markers in Output** (Challenge 5)
   - **Why**: Debugging, audit trail, conflict resolution
   - **Request**: `add_source_markers: true` option

5. **Build Lifecycle Hooks** (Challenge 7)
   - **Why**: Registry integration, validation, notifications
   - **Request**: `hooks: { pre_build, post_build }` config

---

### **P2 (Medium - Nice to Have)**

6. **Split Output by Component** (Challenge 6)
   - **Why**: Separate migrations for tables/functions/metadata
   - **Workaround**: Multiple environments
   - **Request**: `split_output: true` option

7. **Pre-Build Validation** (Challenge 8)
   - **Why**: Catch errors before build
   - **Request**: `validation.rules` config

8. **Incremental Builds** (Challenge 9)
   - **Why**: Performance with large projects
   - **Question**: Already supported via Rust hashing?

---

### **P3 (Low - Future Enhancement)**

9. **Dynamic Schema Discovery** (Challenge 3)
   - **Why**: Auto-discover new entities without config updates
   - **Workaround**: Update `confiture.yaml` manually
   - **Request**: `auto_discover: true` option

10. **Environment Variables in Config** (Challenge 10)
    - **Why**: Easier CI/CD configuration
    - **Request**: `${VAR}` substitution in YAML

---

## 🎯 Recommended Approach

### **Before Requesting Features**

1. **Test Current Confiture Capabilities**
   ```bash
   # Test hex file ordering
   mkdir -p test_confiture/schema
   echo "CREATE TABLE t1 (id INT);" > test_confiture/schema/012A31_test.sql
   echo "CREATE TABLE t2 (id INT);" > test_confiture/schema/01F231_test.sql
   confiture build --env test --output test.sql
   # Check: Is order correct? (012A31 before 01F231)
   ```

2. **Test Comment Preservation**
   ```bash
   echo "COMMENT ON TABLE t IS '@fraiseql:type name=T';" > test_confiture/schema/comments.sql
   confiture build --env test --output test.sql
   grep "@fraiseql" test.sql
   # Check: Are comments preserved exactly?
   ```

3. **Test Recursive Directories**
   ```bash
   mkdir -p test_confiture/schema/sub1/sub2
   echo "CREATE TABLE t (id INT);" > test_confiture/schema/sub1/sub2/test.sql
   # Can Confiture discover this with current config?
   ```

---

### **If Features Are Missing**

#### **Option A: Open GitHub Issues**
Create issues in Confiture repository:
- **Title**: "[Feature Request] Recursive Directory Scanning"
- **Labels**: enhancement
- **Provide**:
  - Use case (SpecQL integration)
  - Proposed YAML syntax
  - Why existing workarounds are insufficient

#### **Option B: Contribute Pull Requests**
If Confiture is open-source:
- Fork repository
- Implement feature (e.g., `recursive: true`)
- Submit PR with tests
- Benefit: Faster integration, community contribution

#### **Option C: Wrapper Script**
If features take time to implement:
```python
# scripts/confiture_wrapper.py
"""
Wrapper around Confiture that adds:
- Recursive directory scanning
- Source file markers
- Registry validation hooks
"""

def build_with_hierarchy(base_dir, output):
    # 1. Recursively find all .sql files
    # 2. Sort by full path (preserves hierarchy)
    # 3. Add source markers
    # 4. Concatenate
    # 5. Call Confiture migrate (not build)
```

---

## 📧 Draft Feature Request Email/Issue

**Subject**: Feature Requests for SpecQL Integration

**Body**:

```
Hi Confiture Team,

We're integrating Confiture with SpecQL, a business DSL → PostgreSQL + GraphQL
code generator, and would love to discuss a few features that would make the
integration smoother.

**Context**:
- SpecQL generates hexadecimal table codes (e.g., 012A31)
- Uses hierarchical directory structure (5 levels deep)
- Generates FraiseQL metadata comments for GraphQL auto-discovery
- Targets 100+ entities in production

**Critical Questions**:

1. **Comment Preservation** (BLOCKER):
   Are SQL comments (including `COMMENT ON` statements) preserved exactly
   in build output? FraiseQL depends on `@fraiseql:*` comments.

2. **Hexadecimal File Ordering**:
   Does Confiture sort files with hex prefixes correctly?
   Example: 012A31, 01F231 (should be in hex order, not string order)

**Feature Requests** (in priority order):

1. **Recursive Directory Scanning** (P1):
   ```yaml
   schema_dirs:
     - path: db/schema/01_write_side
       recursive: true  # Scan all subdirectories
   ```
   Why: Enables full hierarchical structure without listing every subdirectory

2. **Source File Markers** (P1):
   ```yaml
   build:
     add_source_markers: true
   ```
   Output: `-- SOURCE: db/schema/10_tables/contact.sql`
   Why: Debugging, audit trail

3. **Build Lifecycle Hooks** (P1):
   ```yaml
   hooks:
     pre_build: ["python validate.py"]
     post_build: ["python update_registry.py"]
   ```
   Why: Integration with registry system

Happy to discuss implementation details or contribute PRs if helpful!

Thanks,
[Your Name]
SpecQL Team
```

---

## 🔗 Next Steps

1. **Day 1**: Test Confiture capabilities (hex ordering, comments, recursion)
2. **Day 2**: Document test results in this file
3. **Day 3**: If blockers found, open issues immediately
4. **Day 4**: If features missing, decide: wait, contribute, or workaround
5. **Week 2**: Proceed with integration (with or without features)

---

**Status**: 📋 DRAFT - Needs Testing & Validation
**Owner**: SpecQL Team
**Reviewers**: Confiture maintainers
**Last Updated**: 2025-11-09
