# Post-Beta Phased Implementation Plan
## Unskipping 104 Tests - 8 Week Roadmap

**Goal**: Complete all deferred enhancements and optional features
**Timeline**: 8 weeks (40 work days)
**Current Status**: 1401/1508 tests passing (92.9%)
**Target**: 1508/1508 tests passing (100%)

---

## 📊 Overview

| Phase | Focus Area | Tests | Duration | Priority |
|-------|-----------|-------|----------|----------|
| Week 1 | Database Integration | 8 tests | 5 days | HIGH |
| Week 2 | Rich Type Comments | 13 tests | 5 days | HIGH |
| Week 3 | Rich Type Indexes | 12 tests | 5 days | HIGH |
| Week 4 | Schema Generation Polish | 19 tests | 5 days | MEDIUM |
| Week 5 | FraiseQL GraphQL Polish | 7 tests | 5 days | MEDIUM |
| Week 6 | Advanced Validation (Part 1) | 16 tests | 5 days | MEDIUM |
| Week 7 | Advanced Validation (Part 2) | 6 tests | 5 days | LOW |
| Week 8 | Reverse Engineering & Future | 30 tests | 5 days | LOW |

**Total**: 104 tests unskipped over 8 weeks

---

## Week 1: Database Integration (HIGH PRIORITY)
**Tests**: 8 tests | **Duration**: 5 days | **Priority**: HIGH

### 🎯 Objective
Make all database-dependent integration tests pass reliably with proper infrastructure setup.

### 📋 Tests to Unskip

1. **Database Roundtrip Tests** (6 tests)
   - File: `tests/integration/actions/test_database_roundtrip.py`
   - Tests:
     - `test_create_contact_action_database_execution`
     - `test_validation_error_database_execution`
     - `test_trinity_resolution_database_execution`
     - `test_update_action_database_execution`
     - `test_soft_delete_database_execution`
     - `test_custom_action_database_execution`

2. **Confiture Integration Tests** (2 tests)
   - File: `tests/integration/test_confiture_integration.py`
   - Tests:
     - `test_confiture_migrate_up_and_down`
     - `test_confiture_fallback_when_unavailable`

### 📅 Day-by-Day Plan

#### Day 1: Infrastructure Setup
**RED Phase**: Document current state
- ✅ Verify tests fail correctly without database
- ✅ Document PostgreSQL setup requirements
- ✅ Create docker-compose.yml for test database
- ✅ Write CI/CD configuration for database tests

**Tasks**:
```bash
# Create docker-compose for test database
cat > docker-compose.test.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: specql_test
      POSTGRES_USER: specql_test
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    volumes:
      - ./tests/fixtures/schema:/docker-entrypoint-initdb.d
EOF

# Create test database initialization script
# Document environment variables
```

**Deliverable**: Docker setup + CI configuration

---

#### Day 2: Database Test Infrastructure
**GREEN Phase**: Make first test pass
- Implement test database setup/teardown
- Create schema initialization helpers
- Make `test_create_contact_action_database_execution` pass

**Tasks**:
1. Update `tests/conftest.py` to handle database lifecycle
2. Create `tests/fixtures/schema/00_init.sql` with base schema
3. Run first test with PostgreSQL:
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   export TEST_DB_HOST=localhost TEST_DB_PORT=5433
   uv run pytest tests/integration/actions/test_database_roundtrip.py::test_create_contact_action_database_execution -v
   ```

**Deliverable**: First database test passing ✅

---

#### Day 3: Database Roundtrip Tests (6 tests)
**GREEN Phase**: Make all roundtrip tests pass
- Unskip all 6 database roundtrip tests
- Verify CREATE, UPDATE, validation, Trinity resolution
- Test soft delete and custom actions

**Tasks**:
1. Remove `@pytest.mark.skip` from all 6 tests
2. Run full test suite:
   ```bash
   uv run pytest tests/integration/actions/test_database_roundtrip.py -v
   ```
3. Fix any schema generation issues
4. Verify transaction rollback between tests

**Success Criteria**: All 6 tests passing ✅

---

#### Day 4: Confiture Integration Tests (2 tests)
**GREEN Phase**: Make Confiture tests pass
- Unskip Confiture integration tests
- Test migration up/down workflow
- Test fallback behavior

**Tasks**:
1. Remove `@pytest.mark.skip` from `test_confiture_integration.py`
2. Verify Confiture CLI integration:
   ```bash
   uv run pytest tests/integration/test_confiture_integration.py -v
   ```
3. Test migration state management
4. Document Confiture + SpecQL workflow

**Success Criteria**: Both Confiture tests passing ✅

---

#### Day 5: Refactor & QA
**REFACTOR Phase**: Clean up and optimize
- Refactor database test fixtures
- Optimize schema initialization
- Add database test documentation

**QA Phase**: Verify everything works
- Run full database test suite
- Test with fresh database
- Test concurrent test execution
- Update CI/CD pipeline

**Tasks**:
```bash
# Full test suite with database
uv run pytest tests/integration/ -v --tb=short

# Verify CI works
# Update GitHub Actions workflow
```

**Deliverable**:
- 8 database tests passing ✅
- CI/CD configured for database tests
- Documentation updated

---

## Week 2: Rich Type Comments (HIGH PRIORITY)
**Tests**: 13 tests | **Duration**: 5 days | **Priority**: HIGH

### 🎯 Objective
Implement comprehensive PostgreSQL COMMENT generation for rich types to enable better GraphQL schema documentation via FraiseQL.

### 📋 Tests to Unskip

**File**: `tests/unit/schema/test_comment_generation.py` (13 tests)
- `test_email_field_generates_descriptive_comment`
- `test_url_field_generates_descriptive_comment`
- `test_coordinates_field_generates_descriptive_comment`
- `test_money_field_generates_descriptive_comment`
- `test_rich_type_comment_includes_validation_info`
- `test_phone_field_generates_descriptive_comment`
- `test_ip_address_field_generates_descriptive_comment`
- `test_mac_address_field_generates_descriptive_comment`
- `test_color_field_generates_descriptive_comment`
- `test_latitude_longitude_generate_descriptive_comments`
- `test_composite_rich_types_generate_multiple_comments`
- `test_rich_type_with_nullable_includes_in_comment`
- `test_rich_type_comments_include_fraiseql_metadata`

### 📅 Day-by-Day Plan

#### Day 1: Design Comment System
**RED Phase**: Write failing tests
- Review all 13 test expectations
- Design comment generation architecture
- Document comment format specification

**Tasks**:
1. Review test expectations:
   ```bash
   uv run pytest tests/unit/schema/test_comment_generation.py -v --collect-only
   ```
2. Design comment template system:
   ```python
   # Rich type comment templates
   COMMENT_TEMPLATES = {
       'email': 'Email address (validated: RFC 5322)',
       'url': 'URL (validated: HTTPS preferred)',
       'phone': 'Phone number (format: E.164)',
       'money': 'Monetary amount (currency: {currency}, precision: 2)',
       # ... etc
   }
   ```
3. Create comment generator specification

**Deliverable**: Comment system design document

---

#### Day 2: Implement Comment Generator
**GREEN Phase**: Implement basic comment generation
- Create `RichTypeCommentGenerator` class
- Implement comment templates for each rich type
- Generate basic COMMENT ON COLUMN statements

**Tasks**:
1. Create `src/generators/schema/rich_type_comment_generator.py`:
   ```python
   class RichTypeCommentGenerator:
       """Generate PostgreSQL COMMENT statements for rich types"""

       def generate_field_comment(self, entity: Entity, field: FieldDefinition) -> str:
           """Generate COMMENT ON COLUMN for rich type field"""
           if not self._is_rich_type(field.type_name):
               return ""

           template = self._get_comment_template(field.type_name)
           comment_text = self._format_comment(template, field)

           return f"COMMENT ON COLUMN {entity.schema}.tb_{entity.name.lower()}.{field.name} IS '{comment_text}';"
   ```

2. Run tests to see progress:
   ```bash
   uv run pytest tests/unit/schema/test_comment_generation.py::test_email_field_generates_descriptive_comment -v
   ```

**Deliverable**: Basic comment generation working (5 tests passing)

---

#### Day 3: Advanced Comment Features
**GREEN Phase**: Add validation info and metadata
- Include validation patterns in comments
- Add FraiseQL metadata annotations
- Support composite types

**Tasks**:
1. Enhance comment generation with validation info:
   ```python
   def _format_comment(self, template: str, field: FieldDefinition) -> str:
       """Format comment with validation info and metadata"""
       comment = template

       # Add validation pattern
       if field.validation_pattern:
           comment += f" | Pattern: {field.validation_pattern}"

       # Add nullable info
       if field.nullable:
           comment += " | Nullable"

       # Add FraiseQL metadata
       comment += f" | @fraiseql:type={field.type_name}"

       return comment
   ```

2. Test validation info comments:
   ```bash
   uv run pytest tests/unit/schema/test_comment_generation.py::test_rich_type_comment_includes_validation_info -v
   ```

**Deliverable**: Validation and metadata comments (10 tests passing)

---

#### Day 4: Complete All Rich Type Comments
**GREEN Phase**: Support all rich types
- Implement comments for all 10+ rich types
- Handle composite types (lat/long pairs)
- Test edge cases (nullable, multiple rich types)

**Tasks**:
1. Complete comment templates for all types:
   - Geographic: coordinates, latitude, longitude
   - Network: ip_address, mac_address
   - Visual: color (hex, rgb, rgba)
   - Financial: money (with currency)
   - Contact: phone, email

2. Unskip and run all 13 tests:
   ```bash
   # Remove pytestmark = pytest.mark.skip from test_comment_generation.py
   uv run pytest tests/unit/schema/test_comment_generation.py -v
   ```

**Success Criteria**: All 13 tests passing ✅

---

#### Day 5: Integration & QA
**REFACTOR Phase**: Clean up implementation
- Refactor comment generator for maintainability
- Add helper methods for common patterns
- Document comment format standards

**QA Phase**: Verify integration
- Test comment generation in full schema orchestration
- Verify comments appear in PostgreSQL
- Test FraiseQL can read comment metadata

**Tasks**:
```bash
# Integration test
uv run pytest tests/integration/fraiseql/ -v -k comment

# Generate sample schema with comments
specql generate stdlib/crm/contact.yaml --output /tmp/contact_with_comments.sql

# Verify comments in SQL
grep "COMMENT ON COLUMN" /tmp/contact_with_comments.sql
```

**Deliverable**:
- 13 rich type comment tests passing ✅
- Comments integrated into schema generation
- Documentation updated

---

## Week 3: Rich Type Indexes (HIGH PRIORITY)
**Tests**: 12 tests | **Duration**: 5 days | **Priority**: HIGH

### 🎯 Objective
Implement specialized index generation for rich types (B-tree, GIN, GIST) to optimize query performance.

### 📋 Tests to Unskip

**File**: `tests/unit/schema/test_index_generation.py` (12 tests)
- `test_email_field_gets_btree_index`
- `test_url_field_gets_gin_index_for_pattern_search`
- `test_coordinates_field_gets_gist_index`
- `test_ip_address_field_gets_gist_index`
- `test_mac_address_field_gets_btree_index`
- `test_color_field_gets_btree_index`
- `test_money_field_gets_btree_index`
- `test_multiple_rich_types_get_multiple_indexes`
- `test_no_rich_types_returns_empty_list`
- `test_latitude_longitude_get_gist_indexes`
- `test_phone_field_gets_gin_index_for_pattern_search`
- `test_rich_type_indexes_use_correct_naming_convention`

### 📅 Day-by-Day Plan

#### Day 1: Design Index Strategy
**RED Phase**: Understand index requirements
- Review PostgreSQL index types (B-tree, GIN, GIST)
- Design index selection algorithm
- Document when to use each index type

**Tasks**:
1. Create index strategy matrix:
   ```
   Rich Type      | Index Type | Reason
   ---------------|------------|---------------------------------------
   email          | B-tree     | Exact lookups, sorting
   url            | GIN        | Pattern matching, text search
   phone          | GIN        | Pattern matching (partial numbers)
   coordinates    | GIST       | Spatial queries (PostGIS)
   ip_address     | GIST       | Range queries, network operations
   mac_address    | B-tree     | Exact lookups
   color          | B-tree     | Exact lookups, sorting
   money          | B-tree     | Range queries, sorting
   ```

2. Review test expectations:
   ```bash
   uv run pytest tests/unit/schema/test_index_generation.py -v --collect-only
   ```

**Deliverable**: Index strategy document

---

#### Day 2: Implement B-tree Indexes
**GREEN Phase**: Implement basic B-tree indexes
- Create `RichTypeIndexGenerator` class
- Implement B-tree index generation for simple types
- Test email, mac_address, color, money

**Tasks**:
1. Create `src/generators/schema/rich_type_index_generator.py`:
   ```python
   class RichTypeIndexGenerator:
       """Generate specialized indexes for rich types"""

       BTREE_TYPES = {'email', 'mac_address', 'color', 'money'}
       GIN_TYPES = {'url', 'phone'}
       GIST_TYPES = {'coordinates', 'ip_address', 'latitude', 'longitude'}

       def generate_index(self, entity: Entity, field: FieldDefinition) -> str:
           """Generate appropriate index for rich type field"""
           if field.type_name in self.BTREE_TYPES:
               return self._generate_btree_index(entity, field)
           elif field.type_name in self.GIN_TYPES:
               return self._generate_gin_index(entity, field)
           elif field.type_name in self.GIST_TYPES:
               return self._generate_gist_index(entity, field)
           return ""

       def _generate_btree_index(self, entity: Entity, field: FieldDefinition) -> str:
           """Generate B-tree index for exact lookups"""
           index_name = f"idx_tb_{entity.name.lower()}_{field.name}"
           table_name = f"{entity.schema}.tb_{entity.name.lower()}"
           return f"CREATE INDEX {index_name} ON {table_name} USING btree ({field.name});"
   ```

2. Test B-tree indexes:
   ```bash
   uv run pytest tests/unit/schema/test_index_generation.py::test_email_field_gets_btree_index -v
   uv run pytest tests/unit/schema/test_index_generation.py::test_mac_address_field_gets_btree_index -v
   ```

**Deliverable**: B-tree index generation (4 tests passing)

---

#### Day 3: Implement GIN Indexes
**GREEN Phase**: Implement GIN indexes for text search
- Add GIN index support for url, phone fields
- Test pattern matching use cases
- Verify index syntax

**Tasks**:
1. Implement GIN index generation:
   ```python
   def _generate_gin_index(self, entity: Entity, field: FieldDefinition) -> str:
       """Generate GIN index for pattern matching and text search"""
       index_name = f"idx_tb_{entity.name.lower()}_{field.name}"
       table_name = f"{entity.schema}.tb_{entity.name.lower()}"

       # GIN index with pg_trgm for pattern matching
       return f"CREATE INDEX {index_name} ON {table_name} USING gin ({field.name} gin_trgm_ops);"
   ```

2. Test GIN indexes:
   ```bash
   uv run pytest tests/unit/schema/test_index_generation.py::test_url_field_gets_gin_index_for_pattern_search -v
   uv run pytest tests/unit/schema/test_index_generation.py::test_phone_field_gets_gin_index_for_pattern_search -v
   ```

**Deliverable**: GIN index generation (2 tests passing)

---

#### Day 4: Implement GIST Indexes
**GREEN Phase**: Implement GIST indexes for spatial/network types
- Add GIST index support for coordinates, ip_address
- Implement paired indexes for latitude/longitude
- Test PostGIS and network extensions

**Tasks**:
1. Implement GIST index generation:
   ```python
   def _generate_gist_index(self, entity: Entity, field: FieldDefinition) -> str:
       """Generate GIST index for spatial/network queries"""
       index_name = f"idx_tb_{entity.name.lower()}_{field.name}"
       table_name = f"{entity.schema}.tb_{entity.name.lower()}"

       if field.type_name == 'coordinates':
           # PostGIS spatial index
           return f"CREATE INDEX {index_name} ON {table_name} USING gist ({field.name});"
       elif field.type_name == 'ip_address':
           # Network address index
           return f"CREATE INDEX {index_name} ON {table_name} USING gist ({field.name} inet_ops);"
       return ""
   ```

2. Test GIST indexes:
   ```bash
   uv run pytest tests/unit/schema/test_index_generation.py::test_coordinates_field_gets_gist_index -v
   uv run pytest tests/unit/schema/test_index_generation.py::test_ip_address_field_gets_gist_index -v
   uv run pytest tests/unit/schema/test_index_generation.py::test_latitude_longitude_get_gist_indexes -v
   ```

**Deliverable**: GIST index generation (3 tests passing)

---

#### Day 5: Complete & QA
**GREEN Phase**: Handle edge cases
- Support multiple rich types in one entity
- Handle entities with no rich types
- Verify index naming conventions

**REFACTOR Phase**: Optimize and clean up
- Refactor index generator for clarity
- Add index type selection documentation
- Optimize index generation performance

**QA Phase**: Integration testing
- Test indexes in full schema generation
- Verify indexes work with PostgreSQL
- Performance test index selection

**Tasks**:
```bash
# Unskip all tests
# Remove pytestmark from test_index_generation.py
uv run pytest tests/unit/schema/test_index_generation.py -v

# Integration test
uv run pytest tests/unit/schema/test_table_generator_integration.py -v -k index

# Generate schema with indexes
specql generate stdlib/crm/contact.yaml --output /tmp/contact_with_indexes.sql
grep "CREATE INDEX" /tmp/contact_with_indexes.sql
```

**Success Criteria**: All 12 index tests passing ✅

**Deliverable**:
- 12 rich type index tests passing ✅
- Indexes integrated into schema generation
- Performance documentation

---

## Week 4: Schema Generation Polish (MEDIUM PRIORITY)
**Tests**: 19 tests | **Duration**: 5 days | **Priority**: MEDIUM

### 🎯 Objective
Polish schema generation edge cases, fix assertion format differences, and ensure snapshot tests match actual output.

### 📋 Tests to Unskip

1. **Table Generator Integration** (10 tests)
   - File: `tests/unit/schema/test_table_generator_integration.py`
   - Focus: Index method specifications, complete DDL orchestration

2. **Table Generator** (6 tests)
   - File: `tests/unit/generators/test_table_generator.py`
   - Focus: Assertion format differences

3. **Stdlib Contact Generation** (3 tests)
   - File: `tests/integration/stdlib/test_stdlib_contact_generation.py`
   - Focus: Snapshot assertion differences

### 📅 Day-by-Day Plan

#### Day 1: Analyze Assertion Failures
**RED Phase**: Understand what's failing
- Run all 19 tests to see actual failures
- Document expected vs actual output
- Categorize failures by type

**Tasks**:
```bash
# Run tests to see failures (they're currently skipped)
# Temporarily remove skip markers to see actual errors

# Analyze table_generator_integration failures
uv run pytest tests/unit/schema/test_table_generator_integration.py -v --tb=short

# Analyze table_generator failures
uv run pytest tests/unit/generators/test_table_generator.py -v --tb=short

# Analyze stdlib contact failures
uv run pytest tests/integration/stdlib/test_stdlib_contact_generation.py -v --tb=short
```

**Deliverable**: Failure analysis document with examples

---

#### Day 2: Fix Table Generator Integration (10 tests)
**GREEN Phase**: Fix index method specification issues
- Update index generation to match expected format
- Fix DDL orchestration order
- Correct multi-tenant field handling

**Tasks**:
1. Fix index method specification:
   ```python
   # Issue: Test expects "USING btree" but generator outputs different format
   # Fix in table_generator.py or index_generator.py

   # Expected: CREATE INDEX idx_tb_contact_email ON crm.tb_contact USING btree (email);
   # Actual:   CREATE INDEX idx_tb_contact_email ON crm.tb_contact (email);

   # Add explicit method specification
   def generate_index(self, table_name: str, field: str, method: str = "btree") -> str:
       return f"CREATE INDEX idx_{table_name}_{field} ON {table_name} USING {method} ({field});"
   ```

2. Fix complete DDL orchestration:
   - Ensure correct order: schemas → types → tables → indexes → comments
   - Verify no duplicate comments
   - Check audit fields always present

3. Run tests:
   ```bash
   uv run pytest tests/unit/schema/test_table_generator_integration.py -v
   ```

**Success Criteria**: 10 tests passing ✅

---

#### Day 3: Fix Table Generator Assertions (6 tests)
**GREEN Phase**: Fix assertion format differences
- Update test assertions to match actual output
- Or update generator to match expected format
- Standardize DDL formatting

**Tasks**:
1. Identify format differences:
   ```bash
   # Run tests with verbose output
   uv run pytest tests/unit/generators/test_table_generator.py::test_generate_simple_table -vv

   # Compare expected vs actual
   # Common issues: whitespace, order, naming
   ```

2. Fix format issues:
   - Standardize SQL formatting (indentation, line breaks)
   - Ensure consistent naming conventions
   - Fix comment generation format

3. Update tests or generator:
   ```python
   # Option A: Update test expectations
   def test_generate_simple_table(table_generator):
       result = table_generator.generate(entity)
       # Update expected output to match actual
       assert "CREATE TABLE crm.tb_contact" in result

   # Option B: Update generator output format
   def generate_ddl(self, entity: Entity) -> str:
       # Ensure consistent formatting
       ddl = self._format_ddl(raw_ddl)
       return ddl
   ```

**Success Criteria**: 6 tests passing ✅

---

#### Day 4: Fix Stdlib Contact Snapshots (3 tests)
**GREEN Phase**: Update snapshot tests
- Regenerate snapshots with current output
- Verify production-readiness of contact entity
- Test complete DDL generation

**Tasks**:
1. Regenerate contact entity snapshots:
   ```bash
   # Generate current output
   specql generate stdlib/crm/contact.yaml --output /tmp/contact_current.sql

   # Compare with snapshot
   diff tests/fixtures/snapshots/contact_expected.sql /tmp/contact_current.sql

   # Update snapshot if current output is correct
   cp /tmp/contact_current.sql tests/fixtures/snapshots/contact_expected.sql
   ```

2. Verify production readiness:
   - Check all fields present
   - Verify Trinity pattern applied
   - Confirm foreign keys correct
   - Test audit fields

3. Run tests:
   ```bash
   uv run pytest tests/integration/stdlib/test_stdlib_contact_generation.py -v
   ```

**Success Criteria**: 3 tests passing ✅

---

#### Day 5: Refactor & QA
**REFACTOR Phase**: Standardize DDL generation
- Create DDL formatting helper
- Standardize assertion patterns in tests
- Document DDL format standards

**QA Phase**: Comprehensive testing
- Run all schema generation tests
- Verify no regressions
- Test edge cases

**Tasks**:
```bash
# Run all schema tests
uv run pytest tests/unit/schema/ -v
uv run pytest tests/unit/generators/ -v
uv run pytest tests/integration/stdlib/ -v

# Verify full schema generation
make teamB-test
```

**Deliverable**:
- 19 schema polish tests passing ✅
- DDL format standardized
- Documentation updated

---

## Week 5: FraiseQL GraphQL Polish (MEDIUM PRIORITY)
**Tests**: 7 tests | **Duration**: 5 days | **Priority**: MEDIUM

### 🎯 Objective
Complete rich type GraphQL scalar mapping and enhance FraiseQL autodiscovery metadata for better GraphQL schema generation.

### 📋 Tests to Unskip

**File**: `tests/integration/fraiseql/test_rich_type_graphql_generation.py` (7 tests)
- `test_generate_complete_schema_with_rich_types`
- `test_rich_type_comments_for_graphql_descriptions`
- `test_fraiseql_autodiscovery_metadata_complete`
- `test_rich_type_scalar_mappings_complete`
- `test_postgresql_types_support_fraiseql_autodiscovery`
- `test_validation_patterns_produce_meaningful_comments`
- `test_fraiseql_would_generate_correct_schema`

### 📅 Day-by-Day Plan

#### Day 1: Design GraphQL Scalar Mappings
**RED Phase**: Define scalar mapping strategy
- Design PostgreSQL → GraphQL type mappings
- Document FraiseQL autodiscovery format
- Create scalar resolver specifications

**Tasks**:
1. Create scalar mapping specification:
   ```
   PostgreSQL Type → GraphQL Scalar → Resolver
   ------------------------------------------------
   TEXT (email)    → EmailAddress    → validateEmail()
   TEXT (url)      → URL             → validateURL()
   TEXT (phone)    → PhoneNumber     → validatePhone()
   NUMERIC         → Money           → formatMoney()
   POINT           → Coordinates     → parsePoint()
   INET            → IPAddress       → validateIP()
   ```

2. Review FraiseQL autodiscovery format:
   ```sql
   COMMENT ON COLUMN crm.tb_contact.email IS
     'Email address | @fraiseql:type=EmailAddress | @fraiseql:validation=RFC5322';
   ```

3. Review test expectations:
   ```bash
   uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py -v --collect-only
   ```

**Deliverable**: GraphQL scalar mapping specification

---

#### Day 2: Implement Scalar Metadata Generation
**GREEN Phase**: Generate FraiseQL metadata for rich types
- Enhance comment generation with GraphQL metadata
- Add scalar type annotations
- Include validation info

**Tasks**:
1. Create `src/generators/fraiseql/rich_type_scalar_generator.py`:
   ```python
   class RichTypeScalarGenerator:
       """Generate FraiseQL scalar metadata for rich types"""

       SCALAR_MAPPINGS = {
           'email': 'EmailAddress',
           'url': 'URL',
           'phone': 'PhoneNumber',
           'money': 'Money',
           'coordinates': 'Coordinates',
           'ip_address': 'IPAddress',
       }

       def generate_scalar_metadata(self, field: FieldDefinition) -> str:
           """Generate FraiseQL scalar metadata annotation"""
           if field.type_name not in self.SCALAR_MAPPINGS:
               return ""

           scalar_type = self.SCALAR_MAPPINGS[field.type_name]
           metadata = [
               f"@fraiseql:type={scalar_type}",
               f"@fraiseql:validation={self._get_validation(field)}",
           ]

           return " | ".join(metadata)
   ```

2. Integrate with comment generator from Week 2:
   ```python
   # In RichTypeCommentGenerator
   def _format_comment(self, template: str, field: FieldDefinition) -> str:
       comment = template

       # Add FraiseQL scalar metadata
       scalar_gen = RichTypeScalarGenerator()
       metadata = scalar_gen.generate_scalar_metadata(field)
       if metadata:
           comment += f" | {metadata}"

       return comment
   ```

3. Test scalar metadata:
   ```bash
   uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::test_rich_type_scalar_mappings_complete -v
   ```

**Deliverable**: Scalar metadata generation (2 tests passing)

---

#### Day 3: Complete Schema with Rich Types
**GREEN Phase**: Generate complete schema with all metadata
- Integrate rich type comments into full schema generation
- Verify all rich types have FraiseQL annotations
- Test complete DDL output

**Tasks**:
1. Test complete schema generation:
   ```bash
   uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::test_generate_complete_schema_with_rich_types -v
   ```

2. Verify rich type integration:
   - All rich type fields have comments
   - Comments include FraiseQL metadata
   - Validation patterns present
   - Scalar types mapped correctly

3. Test with stdlib contact entity:
   ```bash
   specql generate stdlib/crm/contact.yaml --with-fraiseql --output /tmp/contact_fraiseql.sql
   grep "@fraiseql:" /tmp/contact_fraiseql.sql
   ```

**Success Criteria**: 3 tests passing ✅

---

#### Day 4: Validation Patterns & GraphQL Descriptions
**GREEN Phase**: Enhance validation pattern comments
- Generate meaningful validation descriptions
- Map PostgreSQL constraints to GraphQL descriptions
- Test autodiscovery metadata completeness

**Tasks**:
1. Enhance validation pattern generation:
   ```python
   def _get_validation_description(self, field: FieldDefinition) -> str:
       """Generate human-readable validation description for GraphQL"""
       if field.type_name == 'email':
           return "Valid email address (RFC 5322)"
       elif field.type_name == 'url':
           return "Valid URL (HTTPS preferred)"
       elif field.type_name == 'phone':
           return "Phone number in E.164 format"
       # ... etc
   ```

2. Test validation patterns:
   ```bash
   uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::test_validation_patterns_produce_meaningful_comments -v
   uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py::test_rich_type_comments_for_graphql_descriptions -v
   ```

**Success Criteria**: 2 tests passing ✅

---

#### Day 5: FraiseQL Autodiscovery & QA
**GREEN Phase**: Complete autodiscovery support
- Verify PostgreSQL types support autodiscovery
- Test FraiseQL would generate correct GraphQL schema
- Validate end-to-end workflow

**REFACTOR Phase**: Clean up implementation
- Refactor scalar generator
- Document FraiseQL integration
- Add examples

**QA Phase**: End-to-end testing
- Test full PostgreSQL → FraiseQL → GraphQL workflow
- Verify all rich types discoverable
- Test with real FraiseQL server

**Tasks**:
```bash
# Run all FraiseQL tests
uv run pytest tests/integration/fraiseql/ -v

# Test with FraiseQL CLI (if available)
fraiseql introspect postgres://localhost/specql_test

# Verify GraphQL schema generation
fraiseql generate-schema postgres://localhost/specql_test --output /tmp/schema.graphql
```

**Success Criteria**: All 7 FraiseQL tests passing ✅

**Deliverable**:
- 7 FraiseQL GraphQL tests passing ✅
- Rich type scalar mapping complete
- FraiseQL autodiscovery working
- Documentation with examples

---

## Week 6: Advanced Validation Part 1 (MEDIUM PRIORITY)
**Tests**: 16 tests | **Duration**: 5 days | **Priority**: MEDIUM

### 🎯 Objective
Implement template inheritance patterns for validation rules, enabling reusable validation templates across entities.

### 📋 Tests to Unskip

**File**: `tests/unit/patterns/validation/test_template_inheritance.py` (16 tests)
- `test_basic_template_definition`
- `test_template_inheritance_single_level`
- `test_template_inheritance_multi_level`
- `test_template_override_validation_rule`
- `test_template_merge_validation_rules`
- `test_template_with_parameters`
- `test_template_parameter_substitution`
- `test_template_parameter_validation`
- `test_template_circular_reference_detection`
- `test_template_undefined_template_error`
- `test_template_apply_to_entity`
- `test_template_apply_to_field`
- `test_template_library_management`
- `test_template_versioning`
- `test_template_documentation_generation`
- `test_template_performance_caching`

### 📅 Day-by-Day Plan

#### Day 1: Design Template System
**RED Phase**: Design template inheritance architecture
- Define template definition format
- Design inheritance mechanism
- Document parameter substitution

**Tasks**:
1. Design template format:
   ```yaml
   # Template definition
   template: contact_validation
   description: Standard contact field validations
   parameters:
     - email_required: true
     - phone_required: false

   validations:
     email:
       - type: pattern
         pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
         error: invalid_email
       - type: required
         when: $email_required
     phone:
       - type: pattern
         pattern: "^\\+[1-9]\\d{1,14}$"
         error: invalid_phone
       - type: required
         when: $phone_required
   ```

2. Design inheritance:
   ```yaml
   # Entity using template
   entity: Contact
   inherits:
     - template: contact_validation
       parameters:
         email_required: true
         phone_required: false
     - template: audit_fields

   fields:
     email: text
     phone: text
   ```

3. Create specification document

**Deliverable**: Template inheritance specification

---

#### Day 2: Implement Template Parser
**GREEN Phase**: Parse template definitions
- Create template definition parser
- Implement parameter extraction
- Test basic template loading

**Tasks**:
1. Create `src/core/template_parser.py`:
   ```python
   @dataclass
   class ValidationTemplate:
       name: str
       description: str
       parameters: Dict[str, Any]
       validations: Dict[str, List[ValidationRule]]
       inherits: List[str] = field(default_factory=list)

   class TemplateParser:
       """Parse validation template definitions"""

       def parse(self, yaml_content: str) -> ValidationTemplate:
           """Parse template YAML into ValidationTemplate object"""
           data = yaml.safe_load(yaml_content)

           return ValidationTemplate(
               name=data['template'],
               description=data.get('description', ''),
               parameters=self._parse_parameters(data.get('parameters', [])),
               validations=self._parse_validations(data.get('validations', {})),
               inherits=data.get('inherits', [])
           )
   ```

2. Test template parsing:
   ```bash
   uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::test_basic_template_definition -v
   ```

**Deliverable**: Template parser (3 tests passing)

---

#### Day 3: Implement Template Inheritance
**GREEN Phase**: Implement single and multi-level inheritance
- Create template resolver
- Implement inheritance chain resolution
- Handle template overrides and merging

**Tasks**:
1. Create `src/patterns/validation/template_resolver.py`:
   ```python
   class TemplateResolver:
       """Resolve template inheritance chains"""

       def __init__(self, template_library: Dict[str, ValidationTemplate]):
           self.templates = template_library
           self._resolution_cache: Dict[str, ValidationTemplate] = {}

       def resolve(self, template_name: str, parameters: Dict[str, Any] = None) -> ValidationTemplate:
           """Resolve template with all inherited validations"""
           if template_name in self._resolution_cache:
               return self._resolution_cache[template_name]

           template = self.templates[template_name]

           # Resolve inheritance chain
           if template.inherits:
               base_templates = [self.resolve(base) for base in template.inherits]
               template = self._merge_templates(base_templates, template)

           # Apply parameters
           if parameters:
               template = self._apply_parameters(template, parameters)

           self._resolution_cache[template_name] = template
           return template

       def _merge_templates(self, bases: List[ValidationTemplate],
                           derived: ValidationTemplate) -> ValidationTemplate:
           """Merge base templates with derived template"""
           merged_validations = {}

           # Start with base validations
           for base in bases:
               for field, rules in base.validations.items():
                   if field not in merged_validations:
                       merged_validations[field] = []
                   merged_validations[field].extend(rules)

           # Override with derived validations
           for field, rules in derived.validations.items():
               merged_validations[field] = rules  # Override

           return ValidationTemplate(
               name=derived.name,
               description=derived.description,
               parameters=derived.parameters,
               validations=merged_validations
           )
   ```

2. Test inheritance:
   ```bash
   uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::test_template_inheritance_single_level -v
   uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::test_template_inheritance_multi_level -v
   uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::test_template_override_validation_rule -v
   uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::test_template_merge_validation_rules -v
   ```

**Deliverable**: Template inheritance (4 tests passing)

---

#### Day 4: Parameter Substitution & Validation
**GREEN Phase**: Implement template parameters
- Parameter substitution in validation rules
- Parameter validation
- Circular reference detection

**Tasks**:
1. Implement parameter substitution:
   ```python
   def _apply_parameters(self, template: ValidationTemplate,
                        parameters: Dict[str, Any]) -> ValidationTemplate:
       """Apply parameter values to template"""
       substituted_validations = {}

       for field, rules in template.validations.items():
           substituted_rules = []
           for rule in rules:
               # Substitute parameter references
               rule_dict = asdict(rule)
               for key, value in rule_dict.items():
                   if isinstance(value, str) and value.startswith('$'):
                       param_name = value[1:]
                       if param_name in parameters:
                           rule_dict[key] = parameters[param_name]

               substituted_rules.append(ValidationRule(**rule_dict))

           substituted_validations[field] = substituted_rules

       return ValidationTemplate(
           name=template.name,
           description=template.description,
           parameters=parameters,
           validations=substituted_validations
       )
   ```

2. Add circular reference detection:
   ```python
   def _detect_circular_reference(self, template_name: str,
                                  visited: Set[str] = None) -> None:
       """Detect circular template references"""
       if visited is None:
           visited = set()

       if template_name in visited:
           raise ValueError(f"Circular template reference detected: {template_name}")

       visited.add(template_name)
       template = self.templates[template_name]

       for base in template.inherits:
           self._detect_circular_reference(base, visited.copy())
   ```

3. Test parameters:
   ```bash
   uv run pytest tests/unit/patterns/validation/test_template_inheritance.py -v -k parameter
   uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::test_template_circular_reference_detection -v
   ```

**Deliverable**: Parameter system (5 tests passing)

---

#### Day 5: Template Application & QA
**GREEN Phase**: Apply templates to entities
- Implement template application to entities
- Template library management
- Documentation generation

**REFACTOR Phase**: Optimize and clean up
- Add caching for template resolution
- Optimize inheritance chain resolution
- Document template system

**QA Phase**: Comprehensive testing
- Test all template features
- Verify performance
- Generate documentation

**Tasks**:
```python
# Template application to entities
class TemplateApplicator:
    """Apply validation templates to entities"""

    def apply_to_entity(self, entity: Entity,
                       template_refs: List[TemplateReference]) -> Entity:
        """Apply templates to entity fields"""
        resolver = TemplateResolver(self.template_library)

        for template_ref in template_refs:
            template = resolver.resolve(template_ref.name, template_ref.parameters)
            entity = self._merge_validations(entity, template)

        return entity
```

Run all tests:
```bash
# Unskip all 16 tests
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py -v
```

**Success Criteria**: All 16 template tests passing ✅

**Deliverable**:
- 16 template inheritance tests passing ✅
- Template system fully implemented
- Documentation with examples
- Performance optimized with caching

---

## Week 7: Advanced Validation Part 2 (LOW PRIORITY)
**Tests**: 6 tests | **Duration**: 5 days | **Priority**: LOW

### 🎯 Objective
Implement recursive dependency validation to detect circular dependencies and complex dependency cycles in entity relationships.

### 📋 Tests to Unskip

**File**: `tests/unit/patterns/validation/test_recursive_dependency_validator.py` (6 tests)
- `test_detect_simple_circular_dependency`
- `test_detect_multi_level_circular_dependency`
- `test_detect_self_referencing_entity`
- `test_validate_complex_dependency_graph`
- `test_suggest_dependency_resolution_order`
- `test_detect_optional_vs_required_dependencies`

### 📅 Day-by-Day Plan

#### Day 1-2: Design & Implement Dependency Graph
**RED Phase**: Design dependency validation system
- Design dependency graph representation
- Plan cycle detection algorithm
- Document dependency types

**GREEN Phase**: Implement basic cycle detection
- Create dependency graph builder
- Implement simple cycle detection (DFS)
- Test self-referencing entities

**Tasks**:
1. Create `src/patterns/validation/dependency_validator.py`:
   ```python
   from typing import Dict, List, Set, Optional
   from dataclasses import dataclass

   @dataclass
   class DependencyEdge:
       from_entity: str
       to_entity: str
       field_name: str
       required: bool  # True if NOT NULL, False if nullable

   class DependencyGraph:
       """Represent entity dependency relationships"""

       def __init__(self):
           self.edges: List[DependencyEdge] = []
           self.nodes: Set[str] = set()

       def add_dependency(self, from_entity: str, to_entity: str,
                         field_name: str, required: bool = True):
           """Add dependency edge"""
           self.edges.append(DependencyEdge(from_entity, to_entity, field_name, required))
           self.nodes.add(from_entity)
           self.nodes.add(to_entity)

       def get_dependencies(self, entity: str) -> List[DependencyEdge]:
           """Get all dependencies for an entity"""
           return [e for e in self.edges if e.from_entity == entity]

       def build_from_entities(self, entities: List[Entity]) -> 'DependencyGraph':
           """Build dependency graph from entity definitions"""
           for entity in entities:
               for field_name, field in entity.fields.items():
                   if field.type_name == 'ref':
                       # Extract referenced entity from ref(EntityName)
                       ref_entity = self._extract_ref_entity(field.type_name)
                       self.add_dependency(
                           entity.name,
                           ref_entity,
                           field_name,
                           required=not field.nullable
                       )
           return self

   class RecursiveDependencyValidator:
       """Validate entity dependencies and detect cycles"""

       def __init__(self, graph: DependencyGraph):
           self.graph = graph

       def detect_cycles(self) -> List[List[str]]:
           """Detect all circular dependencies using DFS"""
           cycles = []
           visited = set()
           rec_stack = set()

           def dfs(node: str, path: List[str]) -> None:
               visited.add(node)
               rec_stack.add(node)
               path.append(node)

               for edge in self.graph.get_dependencies(node):
                   next_node = edge.to_entity

                   if next_node not in visited:
                       dfs(next_node, path.copy())
                   elif next_node in rec_stack:
                       # Found cycle
                       cycle_start = path.index(next_node)
                       cycle = path[cycle_start:] + [next_node]
                       cycles.append(cycle)

               rec_stack.remove(node)

           for node in self.graph.nodes:
               if node not in visited:
                   dfs(node, [])

           return cycles

       def has_circular_dependency(self) -> bool:
           """Check if graph has any circular dependencies"""
           return len(self.detect_cycles()) > 0
   ```

2. Test cycle detection:
   ```bash
   uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py::test_detect_simple_circular_dependency -v
   uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py::test_detect_self_referencing_entity -v
   ```

**Deliverable**: Basic cycle detection (2 tests passing)

---

#### Day 3: Multi-Level Cycles & Complex Graphs
**GREEN Phase**: Detect complex dependency cycles
- Implement multi-level cycle detection
- Handle complex dependency graphs
- Differentiate required vs optional dependencies

**Tasks**:
1. Enhance cycle detection for complex graphs:
   ```python
   def detect_multi_level_cycles(self) -> Dict[str, List[List[str]]]:
       """Detect cycles at different dependency levels"""
       required_graph = self._filter_required_dependencies()
       optional_graph = self._filter_optional_dependencies()

       return {
           'required_cycles': RecursiveDependencyValidator(required_graph).detect_cycles(),
           'optional_cycles': RecursiveDependencyValidator(optional_graph).detect_cycles(),
       }

   def _filter_required_dependencies(self) -> DependencyGraph:
       """Create graph with only required (NOT NULL) dependencies"""
       filtered = DependencyGraph()
       for edge in self.graph.edges:
           if edge.required:
               filtered.edges.append(edge)
               filtered.nodes.add(edge.from_entity)
               filtered.nodes.add(edge.to_entity)
       return filtered

   def validate_complex_graph(self) -> ValidationResult:
       """Validate complex dependency graph"""
       cycles = self.detect_multi_level_cycles()

       # Required cycles are errors (prevent insertion)
       if cycles['required_cycles']:
           return ValidationResult(
               valid=False,
               errors=[f"Required circular dependency: {' -> '.join(cycle)}"
                      for cycle in cycles['required_cycles']]
           )

       # Optional cycles are warnings (allow insertion, may need NULL first)
       warnings = []
       if cycles['optional_cycles']:
           warnings = [f"Optional circular dependency: {' -> '.join(cycle)}"
                      for cycle in cycles['optional_cycles']]

       return ValidationResult(valid=True, warnings=warnings)
   ```

2. Test complex graphs:
   ```bash
   uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py::test_detect_multi_level_circular_dependency -v
   uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py::test_validate_complex_dependency_graph -v
   uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py::test_detect_optional_vs_required_dependencies -v
   ```

**Deliverable**: Complex cycle detection (3 tests passing)

---

#### Day 4: Dependency Resolution Order
**GREEN Phase**: Suggest dependency resolution order
- Implement topological sort for dependency order
- Handle circular dependencies gracefully
- Provide insertion order recommendations

**Tasks**:
1. Implement topological sort:
   ```python
   def suggest_resolution_order(self) -> List[str]:
       """Suggest entity creation order using topological sort"""
       # Use Kahn's algorithm for topological sort
       in_degree = {node: 0 for node in self.graph.nodes}

       # Calculate in-degrees
       for edge in self.graph.edges:
           if edge.required:  # Only consider required dependencies
               in_degree[edge.to_entity] += 1

       # Queue nodes with no dependencies
       queue = [node for node, degree in in_degree.items() if degree == 0]
       result = []

       while queue:
           node = queue.pop(0)
           result.append(node)

           # Reduce in-degree for dependents
           for edge in self.graph.get_dependencies(node):
               if edge.required:
                   in_degree[edge.to_entity] -= 1
                   if in_degree[edge.to_entity] == 0:
                       queue.append(edge.to_entity)

       # Check if all nodes processed (no cycles)
       if len(result) != len(self.graph.nodes):
           cycles = self.detect_cycles()
           raise ValueError(f"Cannot determine order due to cycles: {cycles}")

       return result

   def generate_migration_plan(self) -> MigrationPlan:
       """Generate step-by-step migration plan"""
       try:
           order = self.suggest_resolution_order()
           return MigrationPlan(
               steps=[
                   MigrationStep(order=i, entity=entity, action='CREATE')
                   for i, entity in enumerate(order)
               ],
               has_cycles=False
           )
       except ValueError as e:
           # Has cycles - need special handling
           cycles = self.detect_cycles()
           return MigrationPlan(
               steps=[],
               has_cycles=True,
               cycles=cycles,
               recommendations=[
                   "Consider making some foreign keys nullable",
                   "Use ALTER TABLE ADD CONSTRAINT after insertion",
                   "Break cycles by deferring constraint checking"
               ]
           )
   ```

2. Test resolution order:
   ```bash
   uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py::test_suggest_dependency_resolution_order -v
   ```

**Deliverable**: Dependency resolution (1 test passing)

---

#### Day 5: Integration & QA
**REFACTOR Phase**: Optimize and document
- Optimize graph algorithms
- Add caching for large graphs
- Document dependency validation

**QA Phase**: Comprehensive testing
- Test with real entity schemas
- Verify performance on large graphs
- Generate validation reports

**Tasks**:
```bash
# Run all dependency validation tests
uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py -v

# Integration test with real schemas
uv run pytest tests/integration/ -v -k dependency

# Test with stdlib entities
python -c "
from src.patterns.validation.dependency_validator import DependencyGraph, RecursiveDependencyValidator
from src.core.specql_parser import SpecQLParser

# Load all stdlib entities
entities = []
for yaml_file in Path('stdlib').rglob('*.yaml'):
    entity = SpecQLParser().parse(yaml_file.read_text())
    entities.append(entity)

# Build and validate dependency graph
graph = DependencyGraph().build_from_entities(entities)
validator = RecursiveDependencyValidator(graph)

cycles = validator.detect_cycles()
if cycles:
    print(f'Found {len(cycles)} cycles:')
    for cycle in cycles:
        print(f'  {\" -> \".join(cycle)}')
else:
    print('No cycles detected ✅')
    order = validator.suggest_resolution_order()
    print(f'Suggested order: {order}')
"
```

**Success Criteria**: All 6 dependency validation tests passing ✅

**Deliverable**:
- 6 recursive dependency tests passing ✅
- Dependency validation system complete
- Migration plan generator working
- Documentation with examples

---

## Week 8: Reverse Engineering & Future Features (LOW PRIORITY)
**Tests**: 30 tests | **Duration**: 5 days | **Priority**: LOW

### 🎯 Objective
Complete optional reverse engineering features (TypeScript/Rust → SpecQL YAML) and future enhancements.

### 📋 Tests to Unskip

1. **Rust Action Parser** (13 tests)
   - File: `tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py`

2. **TypeScript Tree-sitter Parser** (9 tests)
   - File: `tests/unit/reverse_engineering/test_tree_sitter_typescript.py`

3. **TypeScript Parser** (5 tests)
   - File: `tests/unit/reverse_engineering/test_typescript_parser.py`

4. **Rust End-to-End** (2 tests)
   - File: `tests/integration/reverse_engineering/test_rust_end_to_end.py`

5. **Composite Hierarchical** (1 test)
   - File: `tests/integration/test_composite_hierarchical_e2e.py`

### 📅 Day-by-Day Plan

#### Day 1: TypeScript Parser Setup
**RED Phase**: Set up tree-sitter TypeScript parsing
- Install tree-sitter dependencies
- Configure TypeScript grammar
- Test basic AST parsing

**Tasks**:
1. Install dependencies:
   ```bash
   pip install tree-sitter tree-sitter-typescript
   ```

2. Create `src/reverse_engineering/typescript/tree_sitter_setup.py`:
   ```python
   from tree_sitter import Language, Parser
   import tree_sitter_typescript as ts_typescript

   class TypeScriptParser:
       """Parse TypeScript code using tree-sitter"""

       def __init__(self):
           self.parser = Parser()
           self.parser.set_language(Language(ts_typescript.language_typescript()))

       def parse(self, source_code: str):
           """Parse TypeScript source into AST"""
           return self.parser.parse(bytes(source_code, "utf8"))
   ```

3. Test basic parsing:
   ```bash
   uv run pytest tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_express_routes -v
   ```

**Deliverable**: Tree-sitter setup (1 test passing)

---

#### Day 2: TypeScript Route Extraction
**GREEN Phase**: Extract API routes from TypeScript
- Parse Express.js routes
- Parse Fastify routes
- Parse Next.js API routes

**Tasks**:
1. Create route extractors for each framework:
   ```python
   class ExpressRouteExtractor:
       """Extract routes from Express.js code"""

       def extract_routes(self, ast) -> List[APIRoute]:
           """Extract app.get(), app.post(), etc."""
           routes = []

           # Walk AST looking for method calls
           for node in self._walk_tree(ast.root_node):
               if self._is_route_definition(node):
                   route = self._parse_route(node)
                   routes.append(route)

           return routes

       def _is_route_definition(self, node) -> bool:
           """Check if node is app.get/post/put/delete"""
           return (
               node.type == 'call_expression' and
               node.child(0).type == 'member_expression' and
               node.child(0).child(2).text in [b'get', b'post', b'put', b'delete']
           )
   ```

2. Test route extraction:
   ```bash
   uv run pytest tests/unit/reverse_engineering/test_tree_sitter_typescript.py -v -k "express or fastify or nextjs"
   ```

**Deliverable**: TypeScript route extraction (5 tests passing)

---

#### Day 3: Rust Parser & Route Extraction
**GREEN Phase**: Parse Rust Actix/Rocket/Axum routes
- Set up Rust parsing
- Extract Actix-web routes
- Extract Rocket routes
- Extract Axum routes

**Tasks**:
1. Similar approach for Rust frameworks:
   ```python
   class ActixRouteExtractor:
       """Extract routes from Actix-web Rust code"""

       def extract_routes(self, source: str) -> List[APIRoute]:
           """Parse Actix route macros and service builders"""
           # Pattern: #[get("/path")]
           # Pattern: web::get().to(handler)
           pass
   ```

2. Test Rust parsers:
   ```bash
   uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py -v
   ```

**Deliverable**: Rust route extraction (13 tests passing)

---

#### Day 4: Route → SpecQL YAML Conversion
**GREEN Phase**: Convert extracted routes to SpecQL actions
- Map HTTP routes to SpecQL actions
- Infer action steps from handler code
- Generate SpecQL YAML output

**Tasks**:
1. Create SpecQL generator:
   ```python
   class RouteToSpecQLConverter:
       """Convert API routes to SpecQL action definitions"""

       def convert_route(self, route: APIRoute) -> Action:
           """Convert single route to SpecQL action"""
           return Action(
               name=self._generate_action_name(route),
               steps=self._infer_steps(route),
               impacts=self._infer_impacts(route)
           )

       def _generate_action_name(self, route: APIRoute) -> str:
           """Generate action name from route path"""
           # POST /contacts -> create_contact
           # PUT /contacts/:id -> update_contact
           pass

       def _infer_steps(self, route: APIRoute) -> List[ActionStep]:
           """Infer action steps from handler code"""
           # Simple heuristics:
           # - If inserts into DB -> insert step
           # - If updates DB -> update step
           # - If checks conditions -> validate step
           pass
   ```

2. Test conversion:
   ```bash
   uv run pytest tests/unit/reverse_engineering/test_typescript_parser.py -v
   uv run pytest tests/integration/reverse_engineering/test_rust_end_to_end.py -v
   ```

**Deliverable**: Route to SpecQL conversion (7 tests passing)

---

#### Day 5: Composite Identifier & Final QA
**GREEN Phase**: Implement composite identifier recalculation
- Generate identifier recalculation functions
- Handle hierarchical composite identifiers
- Test allocation-style identifiers

**REFACTOR Phase**: Clean up reverse engineering code
- Optimize parsers
- Document reverse engineering workflow
- Add examples

**QA Phase**: Final testing
- Run all reverse engineering tests
- Test end-to-end workflows
- Generate documentation

**Tasks**:
```python
# Composite identifier recalculation
class CompositeIdentifierGenerator:
    """Generate identifier recalculation functions"""

    def generate_recalc_function(self, entity: Entity) -> str:
        """Generate PL/pgSQL function to recalculate composite identifier"""
        # For allocation: tenant|machine.path|location.path|daterange
        # When machine or location changes, recalculate identifier
        pass
```

Run all tests:
```bash
# All reverse engineering tests
uv run pytest tests/unit/reverse_engineering/ -v
uv run pytest tests/integration/reverse_engineering/ -v

# Composite identifier test
uv run pytest tests/integration/test_composite_hierarchical_e2e.py -v

# Final full test suite
uv run pytest -v
```

**Success Criteria**: All 30 tests passing ✅

**Deliverable**:
- 30 reverse engineering and future feature tests passing ✅
- TypeScript → SpecQL YAML working
- Rust → SpecQL YAML working
- Composite identifier recalculation complete
- Documentation complete

---

## 🎯 Success Metrics

### Weekly Checkpoints

| Week | Tests Unskipped | Cumulative Total | Completion % |
|------|----------------|------------------|--------------|
| 1    | 8              | 1409/1508        | 93.4%        |
| 2    | 13             | 1422/1508        | 94.3%        |
| 3    | 12             | 1434/1508        | 95.1%        |
| 4    | 19             | 1453/1508        | 96.4%        |
| 5    | 7              | 1460/1508        | 96.8%        |
| 6    | 16             | 1476/1508        | 97.9%        |
| 7    | 6              | 1482/1508        | 98.3%        |
| 8    | 30             | 1508/1508        | 100.0% ✅    |

### Quality Gates

Each week must meet these criteria before moving to next week:

✅ All tests for the week passing
✅ No regressions in previously passing tests
✅ Code reviewed and refactored
✅ Documentation updated
✅ Integration tests passing

### Risk Mitigation

**Week 1 (Database)**: CRITICAL - If blocked, all other weeks can proceed
**Weeks 2-3 (Rich Types)**: HIGH - Core feature, prioritize
**Weeks 4-5 (Polish)**: MEDIUM - Quality improvements
**Weeks 6-7 (Validation)**: LOW - Advanced features
**Week 8 (Reverse Eng)**: LOW - Optional features

---

## 📚 Resources Needed

### Infrastructure
- PostgreSQL 16 database for testing
- Docker/Docker Compose for CI/CD
- GitHub Actions for automated testing

### Dependencies
- tree-sitter, tree-sitter-typescript (Week 8)
- tree-sitter-rust (Week 8)
- PostgreSQL extensions: pg_trgm, PostGIS (Week 3)

### Documentation
- API documentation updates (ongoing)
- User guides for new features (ongoing)
- Example repositories (Week 8)

---

## 🚀 Delivery

### End of Week 8 Deliverables

✅ **1508/1508 tests passing (100%)**
✅ **Complete feature set implemented**
✅ **Full documentation**
✅ **Production-ready v1.0.0**

### Release Checklist

- [ ] All 1508 tests passing
- [ ] Documentation complete
- [ ] CHANGELOG updated
- [ ] Version bumped to 1.0.0
- [ ] Release notes written
- [ ] PyPI package published
- [ ] Docker images updated
- [ ] Migration guide published

---

## 📊 Tracking Progress

Use this command to track progress weekly:

```bash
# Weekly progress report
uv run pytest --tb=no -q | tee weekly_progress.txt

# Compare with previous week
diff week{N-1}_progress.txt week{N}_progress.txt
```

Create GitHub issues for each week:
- Issue #1: Week 1 - Database Integration (8 tests)
- Issue #2: Week 2 - Rich Type Comments (13 tests)
- Issue #3: Week 3 - Rich Type Indexes (12 tests)
- ... etc

---

**Timeline**: 8 weeks (Nov 18 → Jan 13)
**Effort**: ~320 hours (8 weeks × 40 hours)
**Priority**: HIGH → MEDIUM → LOW (front-loaded critical features)
**Risk**: LOW (production-ready now, these are enhancements)

🎯 **Goal**: Achieve 100% test coverage and complete all deferred features!
