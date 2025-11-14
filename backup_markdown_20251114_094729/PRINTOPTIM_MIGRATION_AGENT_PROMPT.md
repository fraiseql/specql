# PrintOptim Migration to SpecQL - Agent Evaluation & Planning Prompt

## Mission
You are a senior software architect tasked with evaluating and planning the complete migration of the PrintOptim project to SpecQL's universal code generation framework. Your goal is to produce a comprehensive, phased implementation plan that leverages SpecQL's reverse engineering, CI/CD, and code generation capabilities.

## Context

### PrintOptim Project (Source)
**Location**: `../printoptim_migration`
**Technology Stack**:
- PostgreSQL database with custom functions and mutations
- GitHub Actions CI/CD workflows
- pytest test suite
- Python application layer
- Multi-environment deployment (local, staging, production)

**Database Structure**:
- Organized using Confiture-style hierarchical directories
- `db/0_schema/` - Schema definitions
- `db/1_seed_common/` - Common seed data
- `db/2_seed_backend/` - Backend seeds
- `db/3_seed_frontend/` - Frontend seeds
- `db/environments/` - Environment configurations (local.yaml, old_production.yaml, etc.)
- Existing database: `printoptim_production_old`

### SpecQL Framework (Target)
**Location**: Current working directory (`/home/lionel/code/specql`)
**Core Capabilities**:

1. **Reverse Engineering** (Team A)
   - `specql reverse` - SQL functions → SpecQL YAML
   - `specql reverse-python` - Python code → SpecQL YAML
   - `specql reverse-tests` - Test files → SpecQL YAML
   - `specql cicd reverse-cicd` - CI/CD configs → Universal format

2. **Code Generation** (Teams B, C, D)
   - Team B: PostgreSQL schema with Trinity pattern (pk_*, id, identifier)
   - Team C: PL/pgSQL functions with FraiseQL metadata
   - Team D: FraiseQL annotations for GraphQL discovery
   - Frontend: TypeScript types, Apollo hooks, mutation impacts

3. **Confiture Integration** (Team E)
   - `specql generate --env local` - Generate to Confiture structure
   - `confiture migrate up --env local` - Apply migrations
   - Hierarchical file organization support

4. **Universal Format**
   - Business domain YAML (20 lines → 2000+ lines production code)
   - 100x code leverage
   - Automatic conventions (Trinity pattern, audit fields, indexes)

## Your Tasks

### Phase 1: Discovery & Assessment (4-6 hours)

#### 1.1 Database Analysis
**Objective**: Understand the current PostgreSQL schema and functions

**Actions**:
1. Analyze database structure:
   ```bash
   # From ../printoptim_migration
   find db/0_schema/ -name "*.sql" -type f
   find db/1_seed_common/ -name "*.sql" -type f
   ```

2. Inventory entities and relationships:
   - Extract all table definitions
   - Map foreign key relationships
   - Identify enum types
   - Document composite types (if any)

3. Catalog PostgreSQL functions/mutations:
   - List all custom functions
   - Identify FraiseQL-compatible patterns
   - Document business logic flows

4. Database dump analysis:
   ```bash
   # Analyze existing production database
   cat db/environments/old_production.yaml
   # Connection to printoptim_production_old database
   ```

**Deliverables**:
- `ASSESSMENT_01_DATABASE_INVENTORY.md`:
  - Total tables count
  - Entity relationship diagram (textual/Mermaid)
  - List of all functions/mutations
  - Identified patterns (CRUD, state machines, workflows)

#### 1.2 Python Application Analysis
**Objective**: Understand business logic in Python layer

**Actions**:
1. Find all Python business logic:
   ```bash
   find ../printoptim_migration -name "*.py" -path "*/models/*"
   find ../printoptim_migration -name "*.py" -path "*/services/*"
   find ../printoptim_migration -name "*.py" -path "*/views/*"
   ```

2. Identify reverse engineering candidates:
   - Django/SQLAlchemy models
   - Business logic functions
   - Validation rules
   - State transitions

**Deliverables**:
- `ASSESSMENT_02_PYTHON_INVENTORY.md`:
  - Models list with fields
  - Business logic patterns
  - Validation rules
  - Integration points

#### 1.3 CI/CD Pipeline Analysis
**Objective**: Document current CI/CD workflows

**Actions**:
1. Analyze GitHub Actions workflows:
   ```bash
   cat ../printoptim_migration/.github/workflows/*.yml
   ```

2. Document pipeline stages:
   - Test execution
   - Database migrations
   - Deployment strategies
   - Environment-specific configurations

**Deliverables**:
- `ASSESSMENT_03_CICD_INVENTORY.md`:
  - Current workflows diagram
  - Deployment environments
  - Migration strategies
  - Test execution patterns

#### 1.4 Testing Infrastructure Analysis
**Objective**: Understand test coverage and patterns

**Actions**:
1. Inventory pytest tests:
   ```bash
   find ../printoptim_migration -name "test_*.py"
   find ../printoptim_migration -name "*_test.py"
   ```

2. Analyze test patterns:
   - Unit tests
   - Integration tests
   - Database tests
   - API tests

**Deliverables**:
- `ASSESSMENT_04_TEST_INVENTORY.md`:
  - Test coverage areas
  - Testing patterns
  - Fixtures and test data
  - Migration test strategy

### Phase 2: Gap Analysis & Mapping (3-4 hours)

#### 2.1 SpecQL Feature Mapping
**Objective**: Map PrintOptim features to SpecQL capabilities

**Actions**:
1. For each database entity:
   - Can it be expressed in SpecQL YAML?
   - Which field types are needed?
   - Are there custom types needed?

2. For each PostgreSQL function:
   - Map to SpecQL action steps
   - Identify missing step types
   - Document custom logic requirements

3. For each CI/CD workflow:
   - Map to SpecQL universal CI/CD format
   - Identify platform-specific features

**Deliverables**:
- `GAP_ANALYSIS_01_ENTITY_MAPPING.yaml`:
  ```yaml
  entities:
    - name: Contact
      printoptim_table: tb_contact
      specql_compatibility: 95%
      missing_features:
        - custom_field_type: phone_number
      reverse_engineering_strategy: sql_to_specql
  ```

- `GAP_ANALYSIS_02_FUNCTION_MAPPING.yaml`:
  ```yaml
  functions:
    - name: qualify_lead
      printoptim_function: app.qualify_contact_lead
      specql_action_steps:
        - validate: status = 'lead'
        - update: Contact SET status = 'qualified'
      confidence: high
      manual_review: false
  ```

#### 2.2 Migration Complexity Assessment
**Objective**: Categorize migration tasks by complexity

**Categories**:
- **Simple** (0-2 hours): Direct 1:1 mapping to SpecQL
- **Medium** (2-8 hours): Requires minor adjustments
- **Complex** (8-24 hours): Needs custom code or new SpecQL features
- **Blocker** (>24 hours): Missing SpecQL capabilities

**Deliverables**:
- `GAP_ANALYSIS_03_COMPLEXITY_MATRIX.md`:
  - Complexity breakdown by entity
  - Risk assessment
  - Dependency graph

### Phase 3: Detailed Implementation Plan (6-8 hours)

#### 3.1 Phased Migration Strategy
**Objective**: Create a safe, incremental migration plan

**Proposed Phases**:

##### Phase 3.1: Foundation Setup (Week 1)
**Goals**:
- Set up SpecQL project structure
- Configure Confiture environments
- Establish migration database

**Tasks**:
1. Initialize SpecQL registry:
   ```bash
   cd /home/lionel/code/specql
   specql registry init --schema-tier multitenant --schema-name printoptim
   ```

2. Configure Confiture environment:
   ```yaml
   # In ../printoptim_migration/db/environments/migration.yaml
   source_db: printoptim_production_old
   target_db: printoptim_specql_migration
   ```

3. Create migration workspace:
   ```bash
   mkdir -p ../printoptim_migration/specql_entities
   mkdir -p ../printoptim_migration/specql_migrations
   ```

**Deliverables**:
- Configured SpecQL registry
- Migration environment setup
- Documentation: `PHASE_01_FOUNDATION_SETUP.md`

##### Phase 3.2: Schema Reverse Engineering (Week 2-3)
**Goals**:
- Convert all PostgreSQL tables to SpecQL YAML
- Validate field mappings
- Generate test SpecQL schema

**Tasks**:
1. **Automated Reverse Engineering**:
   ```bash
   # For each schema SQL file
   for sql_file in ../printoptim_migration/db/0_schema/**/*.sql; do
     specql reverse "$sql_file" \
       --output-dir ../printoptim_migration/specql_entities \
       --min-confidence 0.80
   done
   ```

2. **Manual Review & Enhancement**:
   - Review low-confidence conversions (<80%)
   - Add business logic from Python models
   - Enhance with SpecQL patterns

3. **Validation**:
   ```bash
   specql validate ../printoptim_migration/specql_entities/**/*.yaml
   ```

4. **Test Generation**:
   ```bash
   specql generate ../printoptim_migration/specql_entities/**/*.yaml \
     --env migration \
     --output-dir ../printoptim_migration/specql_migrations \
     --verbose
   ```

5. **Comparison**:
   ```bash
   # Compare generated schema with original
   confiture diff \
     --source ../printoptim_migration/db/0_schema \
     --target ../printoptim_migration/specql_migrations
   ```

**Deliverables**:
- All entities in SpecQL YAML format
- Validation report
- Schema comparison report
- Documentation: `PHASE_02_SCHEMA_REVERSE_ENGINEERING.md`

##### Phase 3.3: Business Logic Migration (Week 4-5)
**Goals**:
- Convert PostgreSQL functions to SpecQL actions
- Reverse engineer Python business logic
- Generate PL/pgSQL with FraiseQL metadata

**Tasks**:
1. **Function Reverse Engineering**:
   ```bash
   # For each function SQL file
   for func_file in ../printoptim_migration/db/0_schema/**/functions/*.sql; do
     specql reverse "$func_file" \
       --output-dir ../printoptim_migration/specql_entities \
       --use-heuristics
   done
   ```

2. **Python Logic Extraction**:
   ```bash
   # Extract business logic from Python models
   specql reverse-python ../printoptim_migration/models/*.py \
     --output-dir ../printoptim_migration/specql_entities \
     --discover-patterns
   ```

3. **Action Generation**:
   ```bash
   specql generate ../printoptim_migration/specql_entities/**/*.yaml \
     --env migration \
     --include-tv \
     --output-format hierarchical
   ```

4. **FraiseQL Validation**:
   - Verify mutation_result types
   - Check impact metadata
   - Validate Trinity resolution

**Deliverables**:
- All actions in SpecQL YAML
- Generated PL/pgSQL functions
- FraiseQL metadata files
- Documentation: `PHASE_03_BUSINESS_LOGIC_MIGRATION.md`

##### Phase 3.4: CI/CD Pipeline Migration (Week 6)
**Goals**:
- Convert GitHub Actions to universal format
- Generate SpecQL-aware pipelines
- Integrate with Confiture migrations

**Tasks**:
1. **Reverse Engineer Existing Pipelines**:
   ```bash
   specql cicd reverse-cicd \
     ../printoptim_migration/.github/workflows/test.yml \
     --output ../printoptim_migration/cicd/universal_test.yaml

   specql cicd reverse-cicd \
     ../printoptim_migration/.github/workflows/deploy.yml \
     --output ../printoptim_migration/cicd/universal_deploy.yaml
   ```

2. **Generate SpecQL Pipelines**:
   ```bash
   specql cicd convert-cicd \
     ../printoptim_migration/cicd/universal_test.yaml \
     github-actions \
     --output .github/workflows/specql_test.yml
   ```

3. **Integration Tasks**:
   - Add SpecQL validation step
   - Add schema generation step
   - Add Confiture migration step
   - Configure environment-specific deployments

**Deliverables**:
- Universal CI/CD format
- Generated GitHub Actions workflows
- Integration documentation
- Documentation: `PHASE_04_CICD_MIGRATION.md`

##### Phase 3.5: Test Migration (Week 7)
**Goals**:
- Reverse engineer pytest tests
- Generate SpecQL test data
- Validate migration completeness

**Tasks**:
1. **Test Reverse Engineering**:
   ```bash
   specql reverse-tests \
     ../printoptim_migration/tests/**/*.py \
     --output-dir ../printoptim_migration/specql_tests
   ```

2. **Test Data Generation**:
   - Convert fixtures to SpecQL seed data
   - Generate test scenarios
   - Create validation tests

3. **Integration Testing**:
   - Run tests against generated schema
   - Compare with original behavior
   - Document discrepancies

**Deliverables**:
- Test migration report
- SpecQL test data
- Integration test results
- Documentation: `PHASE_05_TEST_MIGRATION.md`

##### Phase 3.6: Production Migration (Week 8)
**Goals**:
- Migrate production database
- Deploy new schema
- Cutover strategy

**Tasks**:
1. **Database Preparation**:
   ```bash
   # Dump production data
   confiture dump --env old_production \
     --output ../printoptim_migration/dumps/production_data.sql
   ```

2. **Schema Deployment**:
   ```bash
   # Generate final schema
   specql generate ../printoptim_migration/specql_entities/**/*.yaml \
     --env production \
     --output-dir db/schema/

   # Build with Confiture
   confiture build --env production

   # Apply migration
   confiture migrate up --env production
   ```

3. **Data Migration**:
   - Map old tables to new Trinity pattern
   - Migrate data with transformations
   - Validate data integrity

4. **Cutover**:
   - Blue/green deployment
   - Rollback plan
   - Monitoring and verification

**Deliverables**:
- Production migration runbook
- Rollback procedures
- Post-migration validation report
- Documentation: `PHASE_06_PRODUCTION_MIGRATION.md`

#### 3.2 Risk Mitigation Plan
**Objective**: Identify and mitigate migration risks

**Risk Categories**:
1. **Technical Risks**:
   - Data loss during migration
   - Schema incompatibilities
   - Performance regressions
   - Missing features in SpecQL

2. **Process Risks**:
   - Extended downtime
   - Team knowledge gaps
   - Coordination failures

**Mitigation Strategies**:
```markdown
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data loss | Low | Critical | - Multiple backups<br>- Validation scripts<br>- Rollback plan |
| Schema incompatibilities | Medium | High | - Extensive testing<br>- Schema diff tools<br>- Gradual migration |
| Performance issues | Medium | Medium | - Load testing<br>- Query optimization<br>- Monitoring |
| Missing SpecQL features | High | Medium | - Gap analysis upfront<br>- Custom extensions<br>- Hybrid approach |
```

**Deliverables**:
- `RISK_MITIGATION_PLAN.md`
- Rollback procedures for each phase
- Monitoring and alerting setup

#### 3.3 Success Criteria & Metrics
**Objective**: Define measurable success criteria

**Metrics**:
1. **Migration Completeness**:
   - [ ] 100% of entities converted to SpecQL YAML
   - [ ] 100% of functions converted to SpecQL actions
   - [ ] 100% of CI/CD workflows converted
   - [ ] 100% of tests passing

2. **Code Quality**:
   - [ ] All SpecQL YAML validates successfully
   - [ ] Generated SQL matches original functionality
   - [ ] FraiseQL metadata complete
   - [ ] TypeScript types generated

3. **Performance**:
   - [ ] Query performance within 10% of original
   - [ ] Migration execution time < 4 hours
   - [ ] Zero data loss

4. **Code Leverage**:
   - [ ] Achieve >50x code reduction (YAML vs SQL)
   - [ ] Document 100x leverage opportunity areas

**Deliverables**:
- `SUCCESS_CRITERIA.md`
- Automated validation scripts
- Performance benchmarks

### Phase 4: Implementation Execution Plan (Detailed)

#### 4.1 Week-by-Week Breakdown
**Objective**: Provide day-by-day task breakdown

**Format**:
```markdown
## Week 1: Foundation Setup

### Day 1: Environment Configuration
- [ ] Task 1.1: Initialize SpecQL registry (2h)
  - Command: `specql registry init...`
  - Expected output: Registry YAML created
  - Validation: `specql registry list`

- [ ] Task 1.2: Configure Confiture environments (2h)
  - Files to create: `db/environments/migration.yaml`
  - Validation: `confiture validate --env migration`

### Day 2: Database Connection Setup
- [ ] Task 2.1: Test connection to old_production (1h)
- [ ] Task 2.2: Create migration database (1h)
- [ ] Task 2.3: Initial schema dump (2h)

...
```

**Deliverables**:
- `IMPLEMENTATION_WEEK_01_08.md` (8 separate files)
- Daily task checklists
- Validation commands for each task

#### 4.2 Tooling & Automation Scripts
**Objective**: Create automation to accelerate migration

**Scripts to Create**:
1. `scripts/migration/batch_reverse_engineer.sh`:
   ```bash
   #!/bin/bash
   # Batch reverse engineer all SQL files
   for file in ../printoptim_migration/db/0_schema/**/*.sql; do
     specql reverse "$file" --output-dir specql_entities/
   done
   ```

2. `scripts/migration/validate_migration.py`:
   ```python
   # Compare original vs generated schema
   # Validate data integrity
   # Check FraiseQL metadata completeness
   ```

3. `scripts/migration/generate_comparison_report.sh`:
   ```bash
   # Generate HTML report comparing:
   # - Original SQL vs Generated SQL
   # - Original functions vs Generated functions
   # - Test coverage before/after
   ```

**Deliverables**:
- Migration automation scripts
- Validation scripts
- Reporting tools
- Documentation: `MIGRATION_TOOLS.md`

### Phase 5: Documentation & Knowledge Transfer

#### 5.1 Migration Documentation
**Documents to Create**:
1. `MIGRATION_OVERVIEW.md` - Executive summary
2. `REVERSE_ENGINEERING_GUIDE.md` - How we reverse engineered
3. `SPECQL_PATTERNS_USED.md` - SpecQL patterns applied
4. `LESSONS_LEARNED.md` - Insights and gotchas
5. `MAINTENANCE_GUIDE.md` - How to maintain going forward

#### 5.2 Team Training Materials
**Topics**:
1. SpecQL YAML syntax
2. Confiture workflow
3. FraiseQL metadata
4. CI/CD integration
5. Troubleshooting common issues

**Deliverables**:
- Training presentation slides
- Video walkthroughs
- Hands-on exercises
- FAQ document

### Final Deliverable Structure

```
../printoptim_migration/
├── migration_docs/
│   ├── assessments/
│   │   ├── ASSESSMENT_01_DATABASE_INVENTORY.md
│   │   ├── ASSESSMENT_02_PYTHON_INVENTORY.md
│   │   ├── ASSESSMENT_03_CICD_INVENTORY.md
│   │   └── ASSESSMENT_04_TEST_INVENTORY.md
│   ├── gap_analysis/
│   │   ├── GAP_ANALYSIS_01_ENTITY_MAPPING.yaml
│   │   ├── GAP_ANALYSIS_02_FUNCTION_MAPPING.yaml
│   │   └── GAP_ANALYSIS_03_COMPLEXITY_MATRIX.md
│   ├── implementation_plans/
│   │   ├── PHASE_01_FOUNDATION_SETUP.md
│   │   ├── PHASE_02_SCHEMA_REVERSE_ENGINEERING.md
│   │   ├── PHASE_03_BUSINESS_LOGIC_MIGRATION.md
│   │   ├── PHASE_04_CICD_MIGRATION.md
│   │   ├── PHASE_05_TEST_MIGRATION.md
│   │   └── PHASE_06_PRODUCTION_MIGRATION.md
│   ├── weekly_plans/
│   │   ├── IMPLEMENTATION_WEEK_01.md
│   │   ├── IMPLEMENTATION_WEEK_02.md
│   │   └── ...WEEK_08.md
│   ├── RISK_MITIGATION_PLAN.md
│   ├── SUCCESS_CRITERIA.md
│   └── MIGRATION_OVERVIEW.md
├── specql_entities/          # Generated SpecQL YAML
├── specql_migrations/        # Generated SQL schema
├── scripts/
│   └── migration/            # Automation scripts
└── cicd/
    └── universal/            # Universal CI/CD format
```

## Agent Success Criteria

Your plan is successful if it:

1. ✅ **Comprehensive**: Covers all aspects (schema, logic, CI/CD, tests)
2. ✅ **Actionable**: Each task has clear commands and validation steps
3. ✅ **Risk-Aware**: Identifies risks with mitigation strategies
4. ✅ **Measurable**: Includes success metrics and validation criteria
5. ✅ **Incremental**: Phased approach with clear milestones
6. ✅ **Automated**: Leverages SpecQL reverse engineering tools maximally
7. ✅ **Documented**: Creates comprehensive documentation for knowledge transfer

## Agent Methodology

Follow the **Phased TDD Development Approach** from CLAUDE.md:

### For Each Assessment/Analysis Phase:
1. **Discovery** (RED): What do we need to know?
2. **Analysis** (GREEN): Extract and document the information
3. **Validation** (REFACTOR): Verify completeness and accuracy
4. **Documentation** (QA): Create clear, actionable deliverables

### Key Principles:
- **Discipline Over Speed**: Thorough assessment before implementation
- **Progressive Complexity**: Start simple, build to complex
- **Continuous Validation**: Test assumptions at every step
- **Clear Objectives**: Each deliverable has measurable success criteria

## Next Steps for Agent

1. **Read and understand**:
   - SpecQL architecture (`docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md`)
   - Confiture integration (`docs/implementation_plans/03_frameworks/20251109_182139_EXECUTIVE_SUMMARY_CONFITURE_INTEGRATION.md`)
   - Reverse engineering capabilities (`src/cli/reverse.py`, `src/cli/reverse_python.py`)

2. **Analyze PrintOptim**:
   - Database structure in `../printoptim_migration/db/`
   - Python codebase
   - CI/CD pipelines
   - Test suite

3. **Produce deliverables**:
   - Start with Phase 1 assessments
   - Build gap analysis
   - Create detailed implementation plans
   - Develop automation scripts

4. **Iterate and refine**:
   - As you discover new information, update plans
   - Adjust complexity estimates
   - Refine risk assessments

## Estimated Time Investment

- **Phase 1 (Discovery)**: 4-6 hours
- **Phase 2 (Gap Analysis)**: 3-4 hours
- **Phase 3 (Planning)**: 6-8 hours
- **Phase 4 (Detailed Execution Plan)**: 4-6 hours
- **Phase 5 (Documentation)**: 2-3 hours

**Total Agent Planning Work**: ~20-27 hours

**Actual Migration Execution** (after plan approval): ~6-8 weeks

---

## Questions for Clarification (Ask if needed)

Before starting, you may want to clarify:

1. **Database Access**: Do I have credentials for `printoptim_production_old`?
2. **Priority**: Are there critical entities/functions to prioritize?
3. **Timeline**: Is the 8-week timeline flexible?
4. **Resources**: How many developers will execute the migration?
5. **Downtime**: What is acceptable downtime for production cutover?

---

**Begin your assessment when ready. Good luck! 🚀**
