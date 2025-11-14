# PrintOptim Reverse Engineering & Migration Preparation - Agent Prompt

## Mission
You are a database migration specialist tasked with preparing the PrintOptim repository for reverse engineering and setting up Confiture-based migration from the legacy `printoptim_production_old` database to a new SpecQL-generated schema.

## Context

### Project Location
**Working Directory**: `../printoptim_migration` (relative to `/home/lionel/code/specql`)

### Current State
- ✅ Production database dump restored to `printoptim_production_old`
- ✅ Confiture v0.3.0 installed at `/home/lionel/.local/share/../bin/confiture`
- ✅ Existing schema in `db/0_schema/` (566 SQL files)
- ✅ Environment configurations in `db/environments/`:
  - `old_production.yaml` - Points to `printoptim_production_old` (source)
  - `new_local.yaml` - Points to `printoptim_local` (target)
  - `local.yaml` - Local development environment

### Database Structure
```
db/
├── 0_schema/
│   ├── 00_common/          # Extensions, types, functions
│   ├── 01_write_side/      # Write-side tables
│   ├── 02_query_side/      # Query-side tables/views
│   ├── 03_functions/       # PostgreSQL functions
│   ├── 04_turbo_router/    # Routing logic
│   └── 05_lazy_caching/    # Caching layer
├── 1_seed_common/          # Common seed data
├── 2_seed_backend/         # Backend seeds
├── 3_seed_frontend/        # Frontend seeds
├── environments/           # Confiture environments
└── migrations/             # Migration scripts (to be created)
```

### Goals
1. **Prepare repository structure** for reverse engineering
2. **Assess schema differences** between old production and new schema using Confiture
3. **Generate migration scripts** using Confiture's migration generation capabilities
4. **Document findings** for SpecQL reverse engineering

---

## Phase 1: Repository Preparation (2-3 hours)

### Task 1.1: Create Migration Workspace Structure

**Objective**: Organize the repository for systematic reverse engineering

**Commands**:
```bash
cd ../printoptim_migration

# Create reverse engineering workspace
mkdir -p reverse_engineering/{assessments,mappings,patterns,issues}
mkdir -p reverse_engineering/sql_inventory/{tables,functions,views,types}
mkdir -p reverse_engineering/python_inventory/{models,services,validators}
mkdir -p reverse_engineering/specql_output/{entities,actions}

# Create Confiture migration workspace
mkdir -p db/migrations/schema_migration
mkdir -p db/migrations/data_migration
mkdir -p db/migrations/validation

# Create documentation structure
mkdir -p docs/migration/{assessments,strategies,mappings}
```

**Expected Output**:
```
reverse_engineering/
├── assessments/           # Analysis reports
├── mappings/             # Old → New mappings
├── patterns/             # Detected patterns
├── issues/               # Problems found
├── sql_inventory/        # Cataloged SQL objects
├── python_inventory/     # Cataloged Python code
└── specql_output/        # Generated SpecQL YAML

db/migrations/
├── schema_migration/     # DDL migrations
├── data_migration/       # DML migrations
└── validation/           # Validation scripts

docs/migration/
├── assessments/          # Detailed assessments
├── strategies/           # Migration strategies
└── mappings/            # Field/table mappings
```

**Deliverable**: `reverse_engineering/WORKSPACE_SETUP.md`
- Directory structure created
- Purpose of each directory
- Naming conventions

---

### Task 1.2: Inventory Existing Schema Objects

**Objective**: Create comprehensive inventory of all database objects in the old production database

**Commands**:
```bash
cd ../printoptim_migration

# Connect to old production database and extract inventory
psql printoptim_production_old << 'EOF' > reverse_engineering/assessments/database_inventory.txt

-- Header
\echo '=== PrintOptim Production Database Inventory ==='
\echo ''
\echo 'Date:' `date`
\echo 'Database:' printoptim_production_old
\echo ''

-- Tables
\echo '=== TABLES ==='
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;

\echo ''
\echo '=== TABLE COUNT BY SCHEMA ==='
SELECT
    schemaname,
    COUNT(*) as table_count
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
GROUP BY schemaname
ORDER BY schemaname;

-- Views
\echo ''
\echo '=== VIEWS ==='
SELECT
    schemaname,
    viewname,
    definition
FROM pg_views
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, viewname;

-- Functions
\echo ''
\echo '=== FUNCTIONS ==='
SELECT
    n.nspname as schema,
    p.proname as function_name,
    pg_get_function_arguments(p.oid) as arguments,
    pg_get_function_result(p.oid) as return_type
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY n.nspname, p.proname;

-- Types
\echo ''
\echo '=== CUSTOM TYPES ==='
SELECT
    n.nspname as schema,
    t.typname as type_name,
    t.typtype as type_kind
FROM pg_type t
JOIN pg_namespace n ON t.typnamespace = n.oid
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND t.typtype IN ('e', 'c')  -- enums and composite types
ORDER BY n.nspname, t.typname;

-- Sequences
\echo ''
\echo '=== SEQUENCES ==='
SELECT
    schemaname,
    sequencename,
    last_value,
    increment_by
FROM pg_sequences
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, sequencename;

-- Indexes
\echo ''
\echo '=== INDEXES ==='
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename, indexname;

-- Foreign Keys
\echo ''
\echo '=== FOREIGN KEYS ==='
SELECT
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY tc.table_schema, tc.table_name, kcu.column_name;

EOF

# Extract detailed table schemas
psql printoptim_production_old -c "\d+" > reverse_engineering/assessments/table_definitions.txt

# Extract function definitions
psql printoptim_production_old << 'EOF' > reverse_engineering/sql_inventory/functions/all_functions.sql
SELECT
    n.nspname || '.' || p.proname as full_name,
    pg_get_functiondef(p.oid) as definition
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY n.nspname, p.proname;
EOF
```

**Expected Output**:
- `reverse_engineering/assessments/database_inventory.txt` - Complete object inventory
- `reverse_engineering/assessments/table_definitions.txt` - Detailed table schemas
- `reverse_engineering/sql_inventory/functions/all_functions.sql` - All function definitions

**Deliverable**: `reverse_engineering/assessments/INVENTORY_SUMMARY.md`
```markdown
# Database Inventory Summary

## Statistics
- Total Tables: XXX
- Total Views: XXX
- Total Functions: XXX
- Total Types: XXX
- Total Sequences: XXX
- Total Indexes: XXX
- Total Foreign Keys: XXX

## Schema Breakdown
- public: XXX tables, XXX functions
- app: XXX tables, XXX functions
- catalog: XXX tables, XXX functions
...

## Notable Patterns
- Trinity pattern usage: Yes/No
- FraiseQL metadata: Yes/No
- Audit fields: Yes/No
- Naming conventions: ...
```

---

### Task 1.3: Extract Schema DDL from Old Production

**Objective**: Generate clean DDL from the old production database for comparison

**Commands**:
```bash
cd ../printoptim_migration

# Generate complete schema DDL
pg_dump printoptim_production_old \
    --schema-only \
    --no-owner \
    --no-privileges \
    --no-tablespaces \
    --no-security-labels \
    --no-comments \
    > reverse_engineering/assessments/old_production_schema.sql

# Generate DDL with comments (for FraiseQL analysis)
pg_dump printoptim_production_old \
    --schema-only \
    --no-owner \
    --no-privileges \
    > reverse_engineering/assessments/old_production_schema_with_comments.sql

# Extract just the table definitions (ordered)
psql printoptim_production_old << 'EOF' > reverse_engineering/sql_inventory/tables/table_ddl.sql
SELECT
    'CREATE TABLE ' || schemaname || '.' || tablename || ' (' ||
    string_agg(
        column_name || ' ' || data_type ||
        CASE WHEN character_maximum_length IS NOT NULL
             THEN '(' || character_maximum_length || ')'
             ELSE '' END,
        ', '
    ) || ');'
FROM (
    SELECT
        t.schemaname,
        t.tablename,
        c.column_name,
        c.data_type,
        c.character_maximum_length,
        c.ordinal_position
    FROM pg_tables t
    JOIN information_schema.columns c
        ON t.tablename = c.table_name
        AND t.schemaname = c.table_schema
    WHERE t.schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY t.schemaname, t.tablename, c.ordinal_position
) sub
GROUP BY schemaname, tablename
ORDER BY schemaname, tablename;
EOF
```

**Expected Output**:
- `reverse_engineering/assessments/old_production_schema.sql` - Clean DDL
- `reverse_engineering/assessments/old_production_schema_with_comments.sql` - DDL with comments
- `reverse_engineering/sql_inventory/tables/table_ddl.sql` - Table-only DDL

**Deliverable**: `reverse_engineering/assessments/OLD_SCHEMA_ANALYSIS.md`
- Schema size and complexity
- Identified conventions
- FraiseQL usage analysis
- Migration challenges

---

## Phase 2: Confiture Schema Comparison (3-4 hours)

### Task 2.1: Build New Schema from Current DDL Files

**Objective**: Create a fresh database from the current DDL files in `db/0_schema/`

**Commands**:
```bash
cd ../printoptim_migration

# Drop and recreate the new local database
dropdb --if-exists printoptim_local
createdb printoptim_local

# Use Confiture to build the schema
confiture build --env new_local

# Verify the build
psql printoptim_local -c "\dt" | wc -l
psql printoptim_local -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"

# Extract new schema DDL for comparison
pg_dump printoptim_local \
    --schema-only \
    --no-owner \
    --no-privileges \
    > reverse_engineering/assessments/new_schema.sql
```

**Expected Output**:
- `printoptim_local` database created and populated
- `reverse_engineering/assessments/new_schema.sql` - New schema DDL

**Success Criteria**:
- Database builds without errors
- All expected schemas present
- All tables created

**Deliverable**: `reverse_engineering/assessments/NEW_SCHEMA_BUILD_REPORT.md`
- Build status
- Schema statistics
- Warnings or errors encountered

---

### Task 2.2: Generate Schema Diff with Confiture

**Objective**: Use Confiture to compare old production schema vs new schema

**Commands**:
```bash
cd ../printoptim_migration

# Generate comprehensive diff report
confiture diff \
    --source printoptim_production_old \
    --target printoptim_local \
    --output reverse_engineering/assessments/schema_diff.sql \
    --format sql

# Generate human-readable diff report
confiture diff \
    --source printoptim_production_old \
    --target printoptim_local \
    --output reverse_engineering/assessments/schema_diff.md \
    --format markdown

# Generate JSON diff for programmatic processing
confiture diff \
    --source printoptim_production_old \
    --target printoptim_local \
    --output reverse_engineering/assessments/schema_diff.json \
    --format json
```

**Expected Output**:
- `schema_diff.sql` - SQL statements to migrate old → new
- `schema_diff.md` - Human-readable diff report
- `schema_diff.json` - Machine-readable diff data

**Deliverable**: `reverse_engineering/assessments/SCHEMA_DIFF_ANALYSIS.md`

**Template**:
```markdown
# Schema Diff Analysis

## Summary
- Tables Added: XXX
- Tables Removed: XXX
- Tables Modified: XXX
- Columns Added: XXX
- Columns Removed: XXX
- Columns Modified: XXX
- Functions Added: XXX
- Functions Removed: XXX
- Functions Modified: XXX

## Critical Changes
### Tables Removed
| Table | Rows | Impact | Strategy |
|-------|------|--------|----------|
| tb_old_table | 1,234 | High | Migrate to tb_new_table |

### Columns Removed
| Table | Column | Type | Impact | Strategy |
|-------|--------|------|--------|----------|
| tb_contact | old_field | text | Medium | Map to new_field |

### Breaking Changes
1. **Table Renames**: List tables that were renamed
2. **Column Type Changes**: List columns with type changes
3. **Constraint Changes**: List new/modified constraints

## Migration Complexity
- **Simple** (0-2h): XXX changes
- **Medium** (2-8h): XXX changes
- **Complex** (8-24h): XXX changes
- **Blocker** (>24h): XXX changes

## Recommended Actions
1. ...
2. ...
```

---

### Task 2.3: Create Table and Column Mapping Files

**Objective**: Document how old schema maps to new schema

**Process**:
1. Analyze the diff reports
2. Create mapping files for:
   - Table renames
   - Column renames
   - Type changes
   - Data transformations needed

**Commands**:
```bash
cd ../printoptim_migration

# Create mapping template
cat > reverse_engineering/mappings/table_mappings.yaml << 'EOF'
# Table Mappings: Old Production → New Schema
# Format:
#   old_table_name:
#     new_table: new_table_name
#     strategy: rename|merge|split|archive
#     columns:
#       old_column: new_column
#       old_column2:
#         new_column: new_column2
#         transform: SQL expression for transformation

# Example:
# contact:
#   new_table: tb_contact
#   strategy: rename
#   columns:
#     email: email
#     company_id:
#       new_column: company_ref
#       transform: "company_id::uuid"

EOF

# Start populating with data from diff
# (This will be a manual/semi-automated process based on diff analysis)
```

**Expected Output**:
- `reverse_engineering/mappings/table_mappings.yaml` - Complete table mappings
- `reverse_engineering/mappings/column_mappings.yaml` - Detailed column mappings
- `reverse_engineering/mappings/type_conversions.yaml` - Type conversion rules
- `reverse_engineering/mappings/data_transformations.sql` - Custom transformation functions

**Deliverable**: `reverse_engineering/mappings/MAPPING_STRATEGY.md`
```markdown
# Mapping Strategy

## Table Mapping Approach
### Direct Renames (Simple)
- old_name → new_name (XXX tables)

### Structure Changes (Medium)
- Merged tables: XXX
- Split tables: XXX
- Normalized tables: XXX

### Archived Tables (Low Priority)
- Tables to archive: XXX
- Reason: No longer used, deprecated, etc.

## Column Mapping Approach
### Direct Mappings
- XXX columns map 1:1

### Type Conversions
- text → uuid: XXX columns
- integer → bigint: XXX columns
- etc.

### Data Transformations
- Computed columns: XXX
- Merged columns: XXX
- Split columns: XXX

## Special Cases
1. ...
2. ...
```

---

### Task 2.4: Generate Confiture Migration Scripts

**Objective**: Use Confiture to generate executable migration scripts

**Commands**:
```bash
cd ../printoptim_migration

# Generate schema migration (DDL changes)
confiture migrate generate \
    --source printoptim_production_old \
    --target printoptim_local \
    --type schema \
    --output db/migrations/schema_migration/001_initial_schema.sql

# Generate data migration template
confiture migrate generate \
    --source printoptim_production_old \
    --target printoptim_local \
    --type data \
    --mappings reverse_engineering/mappings/table_mappings.yaml \
    --output db/migrations/data_migration/001_migrate_data.sql

# Generate validation script
cat > db/migrations/validation/001_validate_migration.sql << 'EOF'
-- Validation Script: Verify migration completeness

-- 1. Row count comparison
WITH old_counts AS (
    SELECT 'table_name' as table, COUNT(*) as count FROM old_schema.table_name
),
new_counts AS (
    SELECT 'table_name' as table, COUNT(*) as count FROM new_schema.table_name
)
SELECT
    o.table,
    o.count as old_count,
    n.count as new_count,
    n.count - o.count as difference
FROM old_counts o
FULL OUTER JOIN new_counts n ON o.table = n.table;

-- 2. Data integrity checks
-- (Add custom checks based on business logic)

-- 3. Foreign key validation
-- (Verify all relationships maintained)

EOF
```

**Expected Output**:
- `db/migrations/schema_migration/001_initial_schema.sql` - DDL migration
- `db/migrations/data_migration/001_migrate_data.sql` - Data migration
- `db/migrations/validation/001_validate_migration.sql` - Validation script

**Deliverable**: `db/migrations/MIGRATION_SCRIPTS_README.md`
```markdown
# Migration Scripts

## Execution Order
1. Schema migration (DDL)
2. Data migration (DML)
3. Validation

## Schema Migration
File: `schema_migration/001_initial_schema.sql`
- Creates missing tables
- Adds missing columns
- Updates constraints
- Creates indexes

Estimated time: XX minutes
Downtime required: Yes/No

## Data Migration
File: `data_migration/001_migrate_data.sql`
- Copies data from old → new tables
- Applies transformations
- Handles special cases

Estimated time: XX minutes
Downtime required: Yes/No

## Validation
File: `validation/001_validate_migration.sql`
- Verifies row counts
- Checks data integrity
- Validates relationships

Estimated time: XX minutes

## Rollback Plan
1. ...
2. ...
```

---

## Phase 3: Reverse Engineering Preparation (2-3 hours)

### Task 3.1: Identify Reverse Engineering Candidates

**Objective**: Catalog which SQL objects should be reverse engineered to SpecQL

**Process**:
1. Review function inventory
2. Identify business logic functions (vs framework/utility functions)
3. Categorize by complexity and reverse engineering feasibility

**Commands**:
```bash
cd ../printoptim_migration

# Create candidates file
cat > reverse_engineering/assessments/reverse_engineering_candidates.yaml << 'EOF'
# Reverse Engineering Candidates
#
# Categories:
# - high_priority: Business-critical, high-value for SpecQL
# - medium_priority: Useful but not critical
# - low_priority: Utility functions, can defer
# - skip: Framework code, not suitable for SpecQL

high_priority:
  # Functions that implement core business logic
  - function: app.qualify_contact_lead
    reason: Core CRM workflow
    complexity: low
    specql_action_steps: ["validate", "update"]
    estimated_hours: 1

  - function: app.create_quotation
    reason: Critical sales process
    complexity: medium
    specql_action_steps: ["validate", "insert", "call", "notify"]
    estimated_hours: 3

medium_priority:
  # Functions that add value but aren't critical
  - function: app.update_contact_status
    reason: Common pattern, good for reuse
    complexity: low
    estimated_hours: 1

low_priority:
  # Utility functions, less urgent
  - function: app.calculate_discount
    reason: Simple calculation
    complexity: low
    estimated_hours: 0.5

skip:
  # Not suitable for SpecQL reverse engineering
  - function: pg_stat_statements
    reason: PostgreSQL extension, not business logic
  - function: _audit_trigger
    reason: Framework function, handled by SpecQL

EOF

# Count candidates by priority
echo "=== Reverse Engineering Candidates Summary ===" > reverse_engineering/assessments/candidates_summary.txt
echo "" >> reverse_engineering/assessments/candidates_summary.txt
yq eval '.high_priority | length' reverse_engineering/assessments/reverse_engineering_candidates.yaml >> reverse_engineering/assessments/candidates_summary.txt
yq eval '.medium_priority | length' reverse_engineering/assessments/reverse_engineering_candidates.yaml >> reverse_engineering/assessments/candidates_summary.txt
yq eval '.low_priority | length' reverse_engineering/assessments/reverse_engineering_candidates.yaml >> reverse_engineering/assessments/candidates_summary.txt
```

**Expected Output**:
- `reverse_engineering/assessments/reverse_engineering_candidates.yaml` - Categorized functions
- `reverse_engineering/assessments/candidates_summary.txt` - Summary statistics

**Deliverable**: `reverse_engineering/assessments/REVERSE_ENGINEERING_PLAN.md`
```markdown
# Reverse Engineering Plan

## Summary
- High Priority: XX functions (~XX hours)
- Medium Priority: XX functions (~XX hours)
- Low Priority: XX functions (~XX hours)
- Total: XX functions (~XX hours)

## High Priority Functions (Immediate Focus)
| Function | Complexity | SpecQL Steps | Estimated Hours |
|----------|------------|--------------|-----------------|
| app.qualify_contact_lead | Low | validate, update | 1 |
| app.create_quotation | Medium | validate, insert, call | 3 |

## Medium Priority Functions (Next Phase)
...

## Dependencies and Ordering
1. Start with simple functions (low complexity)
2. Build patterns library
3. Apply patterns to medium complexity
4. Tackle complex functions last

## Success Metrics
- [ ] XX% of business logic converted to SpecQL
- [ ] Generated SQL matches original functionality
- [ ] All tests passing
```

---

### Task 3.2: Extract Sample Functions for SpecQL Testing

**Objective**: Extract a few representative functions to test SpecQL reverse engineering

**Commands**:
```bash
cd ../printoptim_migration

# Create samples directory
mkdir -p reverse_engineering/samples/{simple,medium,complex}

# Extract simple function sample
psql printoptim_production_old -c "
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'simple_function_name'
" > reverse_engineering/samples/simple/example_simple.sql

# Extract medium complexity function sample
psql printoptim_production_old -c "
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'medium_function_name'
" > reverse_engineering/samples/medium/example_medium.sql

# Extract complex function sample
psql printoptim_production_old -c "
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'complex_function_name'
" > reverse_engineering/samples/complex/example_complex.sql
```

**Expected Output**:
- Sample functions in `reverse_engineering/samples/`
- Ready for SpecQL `reverse` command testing

**Deliverable**: `reverse_engineering/samples/SAMPLES_README.md`
```markdown
# Sample Functions for Reverse Engineering Testing

## Simple Functions
- `example_simple.sql` - Basic CRUD operation
- Estimated reverse engineering time: 30 min
- Expected SpecQL confidence: >90%

## Medium Functions
- `example_medium.sql` - Multi-step workflow
- Estimated reverse engineering time: 2 hours
- Expected SpecQL confidence: >80%

## Complex Functions
- `example_complex.sql` - Complex business logic
- Estimated reverse engineering time: 4 hours
- Expected SpecQL confidence: >70%
- May require manual enhancement

## Testing Instructions
```bash
# Test reverse engineering on samples
cd /home/lionel/code/specql
specql reverse ../printoptim_migration/reverse_engineering/samples/simple/example_simple.sql \
    --output-dir ../printoptim_migration/reverse_engineering/specql_output \
    --preview
```
```

---

### Task 3.3: Document Known Issues and Blockers

**Objective**: Identify potential problems before starting reverse engineering

**Commands**:
```bash
cd ../printoptim_migration

# Create issues tracking file
cat > reverse_engineering/issues/KNOWN_ISSUES.md << 'EOF'
# Known Issues and Blockers

## Schema Issues
### Critical
- [ ] Issue 1: Description
  - **Impact**: High/Medium/Low
  - **Blocker**: Yes/No
  - **Resolution**: ...

### Non-Critical
- [ ] Issue 2: Description
  - **Impact**: Low
  - **Resolution**: Can defer

## Function Issues
### Missing SpecQL Features
- [ ] Custom step type needed: `loop_until`
  - **Current workaround**: Manual implementation
  - **SpecQL enhancement request**: Yes

### Complex Logic
- [ ] Function X has nested loops
  - **SpecQL support**: Partial (foreach step)
  - **Strategy**: Break into multiple actions

## Data Migration Issues
### Data Quality
- [ ] Orphaned records in table X
  - **Impact**: Medium
  - **Resolution**: Cleanup script needed

### Type Mismatches
- [ ] Column Y stored as text but should be UUID
  - **Impact**: High
  - **Resolution**: Type conversion during migration

## Testing Issues
- [ ] Missing test data for scenario Z
  - **Impact**: Medium
  - **Resolution**: Generate synthetic data

## Next Steps
1. Prioritize critical issues
2. Create resolution tasks
3. Update migration plan with dependencies
EOF
```

**Expected Output**:
- `reverse_engineering/issues/KNOWN_ISSUES.md` - Tracked issues
- Issue prioritization and resolution plan

**Deliverable**: Issue tracker with resolution timeline

---

## Phase 4: Documentation and Handoff (1-2 hours)

### Task 4.1: Create Executive Summary

**Objective**: Summarize findings for stakeholders

**Deliverable**: `docs/migration/MIGRATION_READINESS_REPORT.md`

**Template**:
```markdown
# PrintOptim Migration Readiness Report

**Date**: YYYY-MM-DD
**Status**: Ready for Reverse Engineering / Blockers Identified

## Executive Summary
The PrintOptim repository has been prepared for SpecQL reverse engineering.
Key findings:
- Database inventory: XXX tables, XXX functions, XXX views
- Schema diff: XXX changes required
- Reverse engineering candidates: XXX functions (XX high priority)
- Migration complexity: Simple/Medium/Complex

## Readiness Checklist
- [x] Repository structure prepared
- [x] Database inventory complete
- [x] Schema diff generated
- [x] Migration scripts prepared
- [x] Reverse engineering candidates identified
- [ ] SpecQL testing completed (next phase)
- [ ] Migration validation performed (next phase)

## Key Metrics
| Metric | Count |
|--------|-------|
| Total Tables | XXX |
| Total Functions | XXX |
| Schema Changes | XXX |
| Data Rows | XX million |
| Estimated Migration Time | XX hours |

## Risk Assessment
### Low Risk
- Tables with direct mappings: XXX
- Simple functions: XXX

### Medium Risk
- Tables requiring transformations: XXX
- Medium complexity functions: XXX

### High Risk
- Breaking changes: XXX
- Complex functions: XXX
- Data integrity issues: XXX

## Next Steps
1. Run SpecQL reverse engineering on sample functions
2. Validate generated SpecQL YAML
3. Generate test schema with SpecQL
4. Compare with target schema
5. Iterate on mappings
6. Execute full migration

## Timeline Estimate
- SpecQL reverse engineering: X weeks
- Schema validation: X weeks
- Data migration: X weeks
- Testing & validation: X weeks
- **Total**: X weeks

## Recommendations
1. ...
2. ...
3. ...
```

---

### Task 4.2: Create Migration Runbook

**Objective**: Step-by-step execution guide for the actual migration

**Deliverable**: `docs/migration/MIGRATION_RUNBOOK.md`

**Template**:
```markdown
# PrintOptim Migration Runbook

## Pre-Migration Checklist
- [ ] Production database backed up
- [ ] Downtime window scheduled
- [ ] Team notified
- [ ] Rollback plan reviewed
- [ ] Validation scripts tested

## Phase 1: Pre-Migration (T-24h)
### 1.1 Backup Production
```bash
pg_dump printoptim_production > backup_pre_migration.sql
```

### 1.2 Final Schema Build
```bash
cd ../printoptim_migration
confiture build --env new_local
```

### 1.3 Final Validation
```bash
# Run all validation scripts
psql -f db/migrations/validation/*.sql
```

## Phase 2: Migration Execution (Downtime Window)
### 2.1 Apply Schema Changes (Est: XX min)
```bash
psql printoptim_production < db/migrations/schema_migration/001_initial_schema.sql
```

### 2.2 Migrate Data (Est: XX min)
```bash
psql printoptim_production < db/migrations/data_migration/001_migrate_data.sql
```

### 2.3 Validate Migration (Est: XX min)
```bash
psql printoptim_production < db/migrations/validation/001_validate_migration.sql
```

## Phase 3: Post-Migration
### 3.1 Smoke Tests
- [ ] Critical queries execute
- [ ] Core functions work
- [ ] Data integrity verified

### 3.2 Application Start
```bash
# Start application services
systemctl start printoptim_api
systemctl start printoptim_worker
```

### 3.3 Monitoring
- [ ] Check error logs
- [ ] Monitor performance metrics
- [ ] Verify user access

## Rollback Procedure (If Needed)
### Step 1: Stop Application
```bash
systemctl stop printoptim_api
systemctl stop printoptim_worker
```

### Step 2: Restore Database
```bash
dropdb printoptim_production
createdb printoptim_production
psql printoptim_production < backup_pre_migration.sql
```

### Step 3: Restart Application
```bash
systemctl start printoptim_api
systemctl start printoptim_worker
```

## Success Criteria
- [ ] All tables migrated
- [ ] All data migrated (row counts match)
- [ ] All functions working
- [ ] Application operational
- [ ] No data loss
- [ ] Performance acceptable
```

---

## Final Deliverables Summary

Upon completion, the repository will contain:

```
../printoptim_migration/
├── reverse_engineering/
│   ├── assessments/
│   │   ├── database_inventory.txt
│   │   ├── INVENTORY_SUMMARY.md
│   │   ├── old_production_schema.sql
│   │   ├── OLD_SCHEMA_ANALYSIS.md
│   │   ├── new_schema.sql
│   │   ├── NEW_SCHEMA_BUILD_REPORT.md
│   │   ├── schema_diff.{sql,md,json}
│   │   ├── SCHEMA_DIFF_ANALYSIS.md
│   │   ├── reverse_engineering_candidates.yaml
│   │   ├── REVERSE_ENGINEERING_PLAN.md
│   │   └── WORKSPACE_SETUP.md
│   ├── mappings/
│   │   ├── table_mappings.yaml
│   │   ├── column_mappings.yaml
│   │   ├── type_conversions.yaml
│   │   ├── data_transformations.sql
│   │   └── MAPPING_STRATEGY.md
│   ├── samples/
│   │   ├── simple/example_simple.sql
│   │   ├── medium/example_medium.sql
│   │   ├── complex/example_complex.sql
│   │   └── SAMPLES_README.md
│   ├── issues/
│   │   └── KNOWN_ISSUES.md
│   └── sql_inventory/
│       ├── tables/table_ddl.sql
│       └── functions/all_functions.sql
├── db/migrations/
│   ├── schema_migration/
│   │   └── 001_initial_schema.sql
│   ├── data_migration/
│   │   └── 001_migrate_data.sql
│   ├── validation/
│   │   └── 001_validate_migration.sql
│   └── MIGRATION_SCRIPTS_README.md
└── docs/migration/
    ├── MIGRATION_READINESS_REPORT.md
    └── MIGRATION_RUNBOOK.md
```

---

## Success Criteria

Your preparation work is complete when:

1. ✅ **Repository Structure**
   - All directories created
   - Naming conventions documented

2. ✅ **Database Inventory**
   - Complete object inventory generated
   - Summary statistics documented
   - DDL extracted for both schemas

3. ✅ **Schema Comparison**
   - Confiture diff completed
   - Schema differences analyzed
   - Migration complexity assessed

4. ✅ **Migration Preparation**
   - Table and column mappings created
   - Migration scripts generated
   - Validation scripts prepared

5. ✅ **Reverse Engineering Planning**
   - Candidates identified and prioritized
   - Sample functions extracted
   - Known issues documented

6. ✅ **Documentation**
   - Executive summary completed
   - Migration runbook created
   - All deliverables reviewed

---

## Execution Methodology

Follow the **disciplined assessment approach**:

### For Each Phase:
1. **Execute** (DO): Run the commands and gather data
2. **Analyze** (THINK): Review outputs and extract insights
3. **Document** (WRITE): Create clear, actionable deliverables
4. **Validate** (CHECK): Verify completeness and accuracy

### Key Principles:
- **Thoroughness over speed**: Complete assessments prevent surprises
- **Documentation-first**: Every finding must be documented
- **Automation where possible**: Use scripts to reduce manual work
- **Continuous validation**: Test assumptions at each step

---

## Time Estimates

- **Phase 1**: Repository Preparation (2-3 hours)
- **Phase 2**: Confiture Schema Comparison (3-4 hours)
- **Phase 3**: Reverse Engineering Preparation (2-3 hours)
- **Phase 4**: Documentation and Handoff (1-2 hours)

**Total**: 8-12 hours

---

## Questions to Clarify (If Needed)

Before starting, you may ask:

1. **Access**: Do I have PostgreSQL superuser access?
2. **Confiture**: Is Confiture properly configured?
3. **Disk Space**: Is there sufficient space for multiple databases?
4. **Timing**: Is the production database in a stable state?
5. **Scope**: Are there specific schemas/tables to prioritize?

---

**Begin preparation when ready. Good luck! 🚀**
