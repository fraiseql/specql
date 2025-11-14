# Week 00: Foundation Validation & Environment Setup

**Date**: Before Week 1
**Duration**: 3-5 days
**Status**: 📅 Planned
**Objective**: Validate SpecQL foundation is production-ready and set up PrintOptim migration environment

**Prerequisites**: All foundation work complete (14 weeks)

**Output**:
- Test suite passing with clear status report
- Development environment configured
- CI/CD pipeline validated
- Documentation reviewed and updated
- Migration workspace created
- Team onboarded and ready

---

## 🎯 Executive Summary

Before starting the PrintOptim migration (Week 1), we must ensure the SpecQL foundation is solid and the team is ready. This week validates all completed work, fixes critical issues, and prepares the migration environment.

**Key Deliverables**:
1. **Test Suite Health Check**: Fix any critical test failures, document known gaps
2. **Environment Setup**: Configure development, staging, and production environments
3. **CI/CD Pipeline**: Ensure automated testing and deployment work
4. **Team Readiness**: Documentation review, training, tooling setup
5. **Migration Workspace**: Create structured workspace for PrintOptim migration

**Critical Success Factors**:
- Core test suite (Teams A-E) must be >90% passing
- CI/CD pipeline must run successfully
- All team members can generate schema from YAML
- Migration workspace structure agreed upon

---

## 📅 Daily Breakdown

### Day 1: Test Suite Health Check

**Morning Block (4 hours): Run Full Test Suite & Analyze Results**

Run the complete test suite and generate comprehensive status report.

**Commands**:
```bash
cd /home/lionel/code/specql

# Run full test suite with coverage
uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Generate test report
uv run pytest tests/ --junit-xml=test-results.xml

# Analyze results
python scripts/analyze_test_results.py test-results.xml > docs/TEST_STATUS_REPORT.md
```

**Expected Output**:
- Test summary with pass/fail/skip counts
- Coverage report (target: >80% for core modules)
- List of failed tests categorized by severity
- Recommendations for fixes vs. documentation

**Afternoon Block (4 hours): Fix Critical Test Failures**

Focus on fixing tests that block PrintOptim migration.

**Priority**:
1. **Team A (Parser)**: Must be 100% passing
2. **Team B (Schema Generator)**: Must be >95% passing
3. **Team C (Action Compiler)**: Must be >95% passing
4. **Team D (FraiseQL)**: Must be >90% passing
5. **Team E (CLI)**: Must be >90% passing

**Action Items**:
- Fix import errors (like the one we found in test_python_reverse_engineering.py)
- Resolve test name conflicts (like test_performance_benchmark.py duplicate)
- Document tests that require database (mark as skipped in CI)
- Create issues for non-critical failures

---

### Day 2: Environment Configuration

**Morning Block (4 hours): Development Environment Setup**

Ensure consistent development environment across team.

**File**: `docs/DEVELOPMENT_SETUP.md`

```markdown
# SpecQL Development Environment Setup

## Prerequisites

- Python 3.11+ (using uv for dependency management)
- PostgreSQL 14+ (for integration tests)
- Git
- VS Code (recommended) or your preferred editor

## Setup Steps

### 1. Clone Repository
```bash
git clone https://github.com/yourorg/specql.git
cd specql
```

### 2. Install Dependencies
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

### 3. Configure PostgreSQL (Optional - for integration tests)
```bash
# Create test database
createdb specql_test

# Set environment variable
export DATABASE_URL="postgresql://localhost/specql_test"
```

### 4. Run Tests
```bash
# Run unit tests (no database required)
uv run pytest tests/unit/ -v

# Run all tests including integration
uv run pytest tests/ -v
```

### 5. Generate Schema (Smoke Test)
```bash
# Test basic schema generation
uv run specql generate examples/entities/contact.yaml

# Validate output
ls -la output/schema/
```

## Troubleshooting

### Common Issues

1. **Import errors**: Run `uv sync` to ensure all dependencies are installed
2. **Test failures**: Check if PostgreSQL is running for integration tests
3. **Permission errors**: Ensure output directories are writable

## Next Steps

- Read `.claude/CLAUDE.md` for project architecture
- Review `GETTING_STARTED.md` for quick start
- Check `docs/architecture/` for technical details
```

**Afternoon Block (4 hours): CI/CD Pipeline Validation**

Ensure continuous integration works correctly.

**File**: `.github/workflows/test.yml` (verify and update if needed)

```yaml
name: SpecQL Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: specql_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/specql_test
        run: |
          uv run pytest tests/ -v --junit-xml=test-results.xml

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.xml
```

**Validation**:
- Push a test commit and verify CI runs
- Check that test results are uploaded
- Ensure PostgreSQL service works correctly
- Fix any CI-specific issues

---

### Day 3: Migration Workspace Setup

**Morning Block (4 hours): Create PrintOptim Migration Structure**

Set up organized workspace for migration project.

**Commands**:
```bash
# Create migration workspace (outside specql repo)
mkdir -p ../printoptim_migration
cd ../printoptim_migration

# Create directory structure
mkdir -p {
  reverse_engineering/{assessments,mappings,patterns,issues},
  reverse_engineering/sql_inventory/{tables,functions,views,types},
  reverse_engineering/specql_output/{entities,actions},
  original_codebase/{db,src,tests,docs},
  specql_generated/{schema,migrations,tests,docs},
  deployment/{staging,production},
  reports/{weekly,technical,business}
}

# Create README
cat > README.md << 'EOF'
# PrintOptim → SpecQL Migration

**Timeline**: 8 weeks (Weeks 1-8)
**Status**: Preparation Phase (Week 0)

## Directory Structure

- `reverse_engineering/` - Analysis of existing PrintOptim system
  - `assessments/` - Database inventory, schema dumps, analysis reports
  - `mappings/` - Old schema → SpecQL YAML mappings
  - `patterns/` - Identified patterns and business logic
  - `issues/` - Challenges and decisions
  - `sql_inventory/` - Extracted SQL artifacts
  - `specql_output/` - Generated SpecQL YAML files

- `original_codebase/` - Copy of PrintOptim codebase for reference
  - `db/` - Original database migrations
  - `src/` - Original source code
  - `tests/` - Original tests
  - `docs/` - Original documentation

- `specql_generated/` - SpecQL-generated output
  - `schema/` - Generated PostgreSQL schema
  - `migrations/` - Migration files
  - `tests/` - Generated test fixtures
  - `docs/` - Generated documentation

- `deployment/` - Deployment configurations
  - `staging/` - Staging environment config
  - `production/` - Production environment config

- `reports/` - Progress reports and documentation
  - `weekly/` - Weekly status reports
  - `technical/` - Technical decision documents
  - `business/` - Business impact analysis

## Current Phase: Week 0 - Preparation

**Checklist**:
- [ ] SpecQL test suite validated (>90% passing)
- [ ] Development environment configured
- [ ] CI/CD pipeline working
- [ ] Migration workspace created
- [ ] Team trained on SpecQL
- [ ] PrintOptim access confirmed
- [ ] Backup strategy defined

## Next Steps

Week 1 starts with database inventory and reverse engineering.
EOF

# Create tracking document
cat > reports/MIGRATION_TRACKER.md << 'EOF'
# PrintOptim Migration Progress Tracker

## Week 0: Preparation (Current)
- [ ] Test suite health check
- [ ] Environment setup
- [ ] Workspace creation
- [ ] Team readiness
- [ ] Access verification

## Week 1: Database Inventory
- [ ] Extract schema
- [ ] Reverse engineer functions
- [ ] Document patterns
- [ ] Create entity mappings

[... Weeks 2-8 to be added]
EOF
```

**Afternoon Block (4 hours): Access Verification & Backup Strategy**

Ensure we have access to PrintOptim and can back up safely.

**Access Checklist**:
```bash
# Verify database access (staging first!)
psql printoptim_staging -c "SELECT version();"

# Test read-only queries
psql printoptim_staging -c "
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  LIMIT 5;
"

# Verify we can export schema
pg_dump printoptim_staging --schema-only --no-owner --no-privileges \
  -f original_codebase/db/staging_schema_backup.sql

# Test connection to production (read-only)
psql printoptim_production -c "SELECT current_database(), current_user;"
```

**Backup Strategy Document**:

**File**: `deployment/BACKUP_STRATEGY.md`

```markdown
# PrintOptim Migration Backup Strategy

## Pre-Migration Backups

### Full Database Backup
```bash
# Production backup before any changes
pg_dump printoptim_production --format=custom --file=backups/prod_pre_migration_$(date +%Y%m%d).dump
```

### Schema-Only Backup
```bash
pg_dump printoptim_production --schema-only \
  --file=backups/prod_schema_pre_migration_$(date +%Y%m%d).sql
```

### Data Checksum
```bash
# Generate checksums for verification
psql printoptim_production -c "
  SELECT schemaname, tablename, count(*) as row_count
  FROM pg_tables t
  JOIN pg_stat_user_tables s ON t.tablename = s.relname
  WHERE schemaname = 'public'
  GROUP BY schemaname, tablename
  ORDER BY tablename;
" > backups/row_counts_pre_migration_$(date +%Y%m%d).txt
```

## Rollback Plan

### Point 1: After Schema Migration (Week 3)
- Backup: New schema + old data
- Rollback: Drop new schema, restore old schema
- Risk: Low (no data modified yet)

### Point 2: After Data Migration (Week 4)
- Backup: Full database with both old and new schemas
- Rollback: Complex - requires data migration reversal
- Risk: Medium (data has been transformed)

### Point 3: After Application Cutover (Week 8)
- Backup: Full production backup
- Rollback: Application rollback + database rollback
- Risk: High (requires coordinated rollback)

## Safety Measures

1. **Staging First**: All changes tested in staging before production
2. **Blue-Green Deployment**: Keep old system running during migration
3. **Incremental Migration**: Migrate one domain at a time
4. **Verification Queries**: Run data integrity checks after each phase
5. **Monitoring**: Set up alerts for anomalies
```

---

### Day 4: Team Readiness & Documentation

**Morning Block (4 hours): Documentation Review & Updates**

Ensure all documentation is current and accessible.

**Documentation Checklist**:

1. **Project Overview** (`.claude/CLAUDE.md`)
   - Review for accuracy
   - Update status sections
   - Add migration notes

2. **Getting Started Guide** (`GETTING_STARTED.md`)
   - Test all examples
   - Update CLI commands
   - Add troubleshooting section

3. **Architecture Docs** (`docs/architecture/`)
   - Verify diagrams are current
   - Update component descriptions
   - Add migration architecture

4. **API Documentation**
   - Generate fresh API docs
   - Review all public interfaces
   - Document breaking changes (if any)

**Script to Generate Fresh Docs**:

**File**: `scripts/generate_docs.sh`

```bash
#!/bin/bash

echo "Generating SpecQL Documentation..."

# Generate API documentation
uv run pdoc --html --output-dir docs/api src/

# Generate CLI help documentation
uv run specql --help > docs/cli/COMMANDS.md
uv run specql generate --help >> docs/cli/COMMANDS.md
uv run specql validate --help >> docs/cli/COMMANDS.md
uv run specql diff --help >> docs/cli/COMMANDS.md

# Generate examples output
mkdir -p docs/examples/output
for example in examples/entities/*.yaml; do
  name=$(basename "$example" .yaml)
  echo "Generating example: $name"
  uv run specql generate "$example" --output docs/examples/output/$name/
done

# Generate test coverage report
uv run pytest tests/ --cov=src --cov-report=html --cov-report=term \
  > docs/TEST_COVERAGE.txt

echo "Documentation generated in docs/"
```

**Afternoon Block (4 hours): Team Training Session**

Conduct hands-on training for the team.

**Training Agenda** (4 hours):

**Hour 1: SpecQL Overview**
- What is SpecQL and why it exists
- The Trinity Pattern explained
- 100x code leverage demonstration
- Review of completed foundation work

**Hour 2: Hands-On Generation**
- Clone the repository
- Set up development environment
- Generate first schema from YAML
- Explore generated SQL
- Run tests

**Hour 3: PrintOptim Migration Overview**
- PrintOptim current architecture
- Migration strategy (8 weeks)
- Week 1 tasks breakdown
- Tools and processes
- Communication plan

**Hour 4: Q&A and Troubleshooting**
- Answer questions
- Resolve setup issues
- Assign Week 1 responsibilities
- Set up communication channels

**Training Materials**:

**File**: `docs/training/TEAM_TRAINING.md`

```markdown
# SpecQL Team Training Guide

## Session 1: SpecQL Fundamentals (Week 0)

### Learning Objectives
- Understand SpecQL architecture (Teams A-E)
- Generate schema from YAML
- Read and understand generated SQL
- Run test suite
- Use CLI commands

### Hands-On Exercises

#### Exercise 1: Generate a Contact Entity
```yaml
# Save as my_contact.yaml
entity: Contact
schema: crm
fields:
  email: email
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, prospect, customer)
actions:
  - name: convert_to_customer
    steps:
      - validate: status IN ('lead', 'prospect')
      - update: Contact SET status = 'customer'
```

Generate schema:
```bash
uv run specql generate my_contact.yaml --output output/
```

Explore output:
```bash
ls -la output/schema/
cat output/schema/01_write_side/*/tb_contact.sql
cat output/schema/02_mutations/*/app_convert_to_customer.sql
```

#### Exercise 2: Validate Edge Cases
Try these scenarios and understand the errors:
1. Missing required field
2. Invalid reference
3. Duplicate entity name
4. Invalid action step

### Success Criteria
- [ ] Can generate schema from YAML
- [ ] Understands Trinity Pattern
- [ ] Can read generated SQL
- [ ] Can run tests successfully
- [ ] Knows where to find documentation

## Session 2: Migration Process (Week 1 Prep)

### Topics
- PrintOptim current state
- Reverse engineering approach
- Week-by-week plan
- Communication and reporting

### Next Steps
- Review Week 1 plan
- Get PrintOptim access
- Set up workspace
- Join daily standups
```

---

### Day 5: Final Validation & Go/No-Go Decision

**Morning Block (4 hours): Comprehensive System Check**

Run through complete validation checklist.

**Validation Script**:

**File**: `scripts/week0_validation.sh`

```bash
#!/bin/bash

echo "========================================="
echo "Week 0 Validation - SpecQL Foundation"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

# Test 1: Python environment
echo -n "1. Python 3.11+ installed... "
if python3 --version | grep -q "Python 3.1[1-9]"; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 2: UV installed
echo -n "2. UV package manager... "
if command -v uv &> /dev/null; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 3: Dependencies installed
echo -n "3. Dependencies installed... "
if uv run python -c "import src.core.parser" 2>/dev/null; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 4: Core tests passing
echo -n "4. Core tests (Teams A-E)... "
CORE_PASS=$(uv run pytest tests/unit/core/ tests/unit/generators/ tests/unit/cli/ -q 2>/dev/null | grep -oP '\d+(?= passed)' || echo 0)
CORE_TOTAL=$(uv run pytest tests/unit/core/ tests/unit/generators/ tests/unit/cli/ --collect-only -q 2>/dev/null | wc -l)
CORE_PERCENT=$((CORE_PASS * 100 / CORE_TOTAL))

if [ $CORE_PERCENT -ge 90 ]; then
    echo -e "${GREEN}PASS${NC} ($CORE_PERCENT% passing)"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} ($CORE_PERCENT% passing, need ≥90%)"
    ((FAIL++))
fi

# Test 5: Schema generation works
echo -n "5. Schema generation... "
if uv run specql generate examples/entities/contact.yaml --output /tmp/specql_test/ &>/dev/null; then
    if [ -f /tmp/specql_test/schema/01_write_side/*/tb_contact.sql ]; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC} (no output generated)"
        ((FAIL++))
    fi
else
    echo -e "${RED}FAIL${NC} (generation failed)"
    ((FAIL++))
fi

# Test 6: Migration workspace exists
echo -n "6. Migration workspace... "
if [ -d ../printoptim_migration/reverse_engineering ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}SKIP${NC} (run Day 3 setup)"
fi

# Test 7: CI/CD configured
echo -n "7. CI/CD pipeline... "
if [ -f .github/workflows/test.yml ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}SKIP${NC} (manual verification needed)"
fi

# Test 8: Documentation current
echo -n "8. Documentation... "
if [ -f docs/TEST_STATUS_REPORT.md ] && [ -f docs/DEVELOPMENT_SETUP.md ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}SKIP${NC} (run Day 4 tasks)"
fi

echo ""
echo "========================================="
echo "Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "========================================="
echo ""

# Go/No-Go Decision
if [ $FAIL -eq 0 ] && [ $PASS -ge 6 ]; then
    echo -e "${GREEN}✓ READY FOR WEEK 1${NC}"
    echo ""
    echo "Next Steps:"
    echo "  1. Review Week 1 plan (WEEK_01.md)"
    echo "  2. Schedule PrintOptim database access"
    echo "  3. Hold team kickoff meeting"
    echo "  4. Start Week 1 Day 1 tasks"
    exit 0
else
    echo -e "${RED}✗ NOT READY - Fix issues above${NC}"
    echo ""
    echo "Required Actions:"
    [ $FAIL -gt 0 ] && echo "  - Fix $FAIL failed checks"
    [ $PASS -lt 6 ] && echo "  - Complete remaining setup tasks"
    exit 1
fi
```

**Afternoon Block (4 hours): Go/No-Go Meeting & Week 1 Kickoff Prep**

Hold decision meeting with stakeholders.

**Meeting Agenda**:

1. **Test Suite Status** (15 min)
   - Review test results
   - Discuss failed tests
   - Decision: Acceptable for migration?

2. **Environment Readiness** (15 min)
   - Development setup complete?
   - CI/CD working?
   - Tools accessible?

3. **Team Readiness** (15 min)
   - Training complete?
   - Roles assigned?
   - Questions resolved?

4. **PrintOptim Access** (15 min)
   - Database access confirmed?
   - Backup strategy approved?
   - Rollback plan understood?

5. **Go/No-Go Decision** (15 min)
   - Vote: Ready for Week 1?
   - If GO: Schedule Week 1 Day 1 start
   - If NO-GO: Define blockers and timeline

6. **Week 1 Preview** (15 min)
   - Review Week 1 objectives
   - Assign Day 1 tasks
   - Set first checkpoint

**Decision Criteria**:

**GO** if:
- ✅ Core tests >90% passing (Teams A-E)
- ✅ Schema generation works
- ✅ Team trained and ready
- ✅ PrintOptim access confirmed
- ✅ Backup strategy approved
- ✅ Migration workspace set up

**NO-GO** if:
- ❌ Core tests <80% passing
- ❌ Critical bugs in generation
- ❌ Team not ready
- ❌ No database access
- ❌ Safety concerns

---

## ✅ Success Criteria

- [ ] Test suite health report generated
- [ ] Core teams (A-E) tests >90% passing
- [ ] Known test failures documented with severity
- [ ] Development environment setup guide created
- [ ] All team members can generate schema from YAML
- [ ] CI/CD pipeline running successfully
- [ ] Migration workspace structure created
- [ ] PrintOptim database access verified (staging + production)
- [ ] Backup strategy documented and approved
- [ ] Team training completed
- [ ] Documentation reviewed and updated
- [ ] Week 0 validation script passes
- [ ] Go/No-Go decision: GO

---

## 🧪 Testing Strategy

**Test Prioritization**:

1. **Critical (Must Pass)**:
   - All Team A parser tests
   - Core Team B schema generation tests
   - Core Team C action compilation tests
   - Basic CLI functionality tests

2. **High Priority (Should Pass)**:
   - Team D FraiseQL annotation tests
   - Integration tests for basic workflows
   - Pattern library core patterns

3. **Medium Priority (Nice to Pass)**:
   - Advanced pattern tests
   - Multi-language reverse engineering
   - Diagram generation tests

4. **Low Priority (Document if Failing)**:
   - Database roundtrip tests (require live DB)
   - Performance benchmarks
   - Advanced edge cases

**Testing Commands**:
```bash
# Critical tests only
uv run pytest tests/unit/core/ tests/unit/generators/schema/ tests/unit/generators/actions/ tests/unit/cli/ -v

# Check coverage
uv run pytest tests/unit/core/ --cov=src/core --cov-report=term-missing

# Quick smoke test
uv run specql generate examples/entities/contact.yaml && echo "✓ Generation works"
```

---

## 🔗 Related Files

- **Next**: [Week 01](./WEEK_01.md) - Database Inventory & Reverse Engineering
- **Reference**: [ROADMAP.md](./ROADMAP.md) - Complete 50-week plan
- **Testing**: Test suite results in `docs/TEST_STATUS_REPORT.md`

---

**Status**: 📅 Planned
**Complexity**: Low (validation and setup)
**Risk**: Low (no code changes, pure preparation)
**Impact**: Critical - ensures successful Week 1 start

**Deliverables**:
1. Test health report
2. Development setup guide
3. Migration workspace structure
4. Team training materials
5. Backup strategy document
6. Go/No-Go decision
