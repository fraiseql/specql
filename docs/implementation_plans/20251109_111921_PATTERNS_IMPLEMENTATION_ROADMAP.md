# Missing Patterns Implementation Roadmap

**Purpose**: Master roadmap for implementing the three missing patterns from PrintOptim backend
**Status**: Ready for execution
**Timeline**: 6 weeks total

---

## 📚 Documentation Overview

This roadmap ties together three complementary documents:

### 1. [MISSING_PATTERNS_IMPLEMENTATION.md](./MISSING_PATTERNS_IMPLEMENTATION.md)
**Complete phased implementation plans** with TDD cycles for:
- Pattern 1: Identifier Recalculation (recalcid functions)
- Pattern 2: LTREE Hierarchical Data
- Pattern 3: Node + Info Two-Table Split

**Contains**:
- Detailed RED → GREEN → REFACTOR → QA cycles
- Test specifications
- Code examples
- Quality gates

### 2. [IDENTIFIER_CALCULATION_PATTERNS.md](./IDENTIFIER_CALCULATION_PATTERNS.md)
**Real-world analysis** from PrintOptim backend showing:
- How identifiers are actually calculated
- Slug-based hierarchical patterns
- Deduplication strategies
- Production code examples

**Contains**:
- 4 production patterns (Location, OrgUnit, Machine, Model)
- Slugify implementation
- SpecQL integration proposals
- Code generation strategy

### 3. This Roadmap
**High-level coordination** and decision points

---

## 🎯 Strategic Priorities

### SQL Architect Validation

> "For hierarchical entities, this 'node + info' split is a **good, intentional design**, not over-engineering."

**Key Insight**: All three patterns work together:
- **LTREE**: Structural hierarchy (`path` for queries)
- **Node+Info**: Separation of concerns (structure vs attributes)
- **recalcid**: Keep identifiers consistent with hierarchy

**Decision**: Implement all three as integrated framework features

---

## 📅 6-Week Implementation Plan

### Weeks 1-2: Pattern 1 - Identifier Recalculation (Foundation)

**Why First**: Other patterns depend on identifier infrastructure

**Deliverables**:
- ✅ `recalculation_context` composite type (migration 000)
- ✅ `slugify()` functions (migration 000)
- ✅ `identifier` and `base_identifier` fields in schema (Team B)
- ✅ Identifier config in SpecQL AST (Team A)
- ✅ Basic `recalcid_{entity}()` generation (Team C)
- ✅ Hierarchical slug strategy working (Team C)

**Critical Path**:
```
Day 1-2:   Foundation types (recalculation_context, slugify)
Day 3-4:   AST support for identifier config
Day 5-7:   Basic recalcid generation (flat entities)
Day 8-10:  Hierarchical recalcid (with recursive CTE)
```

**Success Criteria**:
- [ ] Can parse `identifier:` section in SpecQL YAML
- [ ] Generates `recalcid_{entity}()` for hierarchical entities
- [ ] Slug-based identifiers calculated correctly
- [ ] Deduplication works (adds `#2`, `#3` suffixes)
- [ ] Integration test: Location identifiers recalculated on name change

**Reference**: See `IDENTIFIER_CALCULATION_PATTERNS.md` for production examples

---

### Weeks 3-4: Pattern 2 - LTREE Hierarchical Data

**Why Second**: Complements identifier work, enables efficient queries

**Deliverables**:
- ✅ LTREE extension in migration 000
- ✅ Auto-detect hierarchical entities (`parent: ref(self)`)
- ✅ Generate `path LTREE` column
- ✅ Generate GIST index on path
- ✅ Generate path maintenance trigger
- ✅ Handle node moves (update descendant paths)
- ✅ Helper functions (ancestors, descendants, children, depth)

**Critical Path**:
```
Day 1-2:   LTREE extension + detection logic
Day 3-5:   Schema generation (path column, GIST index)
Day 6-7:   Path maintenance trigger
Day 8-9:   Helper functions
Day 10:    Integration testing + documentation
```

**Success Criteria**:
- [ ] LTREE paths automatically maintained on INSERT/UPDATE
- [ ] Moving nodes updates all descendant paths
- [ ] Can query: "Find all descendants of node X"
- [ ] Can query: "Get ancestors of node Y"
- [ ] Integration test: 1000-node tree with moves

**Key Decision**:
- **Path vs Identifier**: Path is structural (`USA.CA.SF`), identifier is business logic (`toulouse|legal.hq`)
- They can differ! Path for queries, identifier for display

---

### Weeks 5-6: Pattern 3 - Node + Info Two-Table Split

**Why Last**: Most complex, builds on LTREE and recalcid

**Deliverables**:
- ✅ `metadata_split: true` flag in SpecQL
- ✅ Field classifier (node vs info)
- ✅ Generate `tb_{entity}` node table (structure only)
- ✅ Generate `tb_{entity}_info` table (attributes)
- ✅ FK from node to info
- ✅ LTREE path in node table
- ✅ Convenience view `v_{entity}` (joins both)
- ✅ FraiseQL annotations on view
- ✅ recalcid updates both tables

**Critical Path**:
```
Day 1-2:   AST support (metadata_split flag)
Day 3-4:   Field classification logic
Day 5-6:   Node table generation
Day 7-8:   Info table generation
Day 9:     Convenience view generation
Day 10:    FraiseQL integration
Day 11-12: Testing + documentation
```

**Success Criteria**:
- [ ] Can query through view: `SELECT * FROM v_location`
- [ ] View exposes both structural (path, parent) and domain (name, type) fields
- [ ] recalcid updates both tables correctly
- [ ] FraiseQL exposes view as GraphQL type
- [ ] Integration test: Complex Location hierarchy with 3-level depth

**Architecture Decision**:
```sql
-- Node table (structure - reusable across all hierarchies)
CREATE TABLE tenant.tb_location (
    pk_location INTEGER PRIMARY KEY,
    id UUID UNIQUE,
    identifier TEXT UNIQUE,
    path LTREE,                           -- For hierarchy queries
    fk_parent_location INTEGER,           -- Self-reference
    fk_location_info INTEGER NOT NULL,    -- Link to attributes
    -- Audit fields
);

-- Info table (domain-specific attributes)
CREATE TABLE tenant.tb_location_info (
    pk_location_info INTEGER PRIMARY KEY,
    id UUID UNIQUE,
    fk_location_type INTEGER,
    legal_name TEXT,
    tax_id TEXT,
    -- No hierarchy fields here
);

-- Convenience view (for queries)
CREATE VIEW v_location AS
SELECT
    n.pk_location,
    n.path,
    n.fk_parent_location AS parent_id,
    i.legal_name,
    i.tax_id
FROM tb_location n
JOIN tb_location_info i ON n.fk_location_info = i.pk_location_info;
```

---

## 🔗 Pattern Integration

### How They Work Together

**Example: Location Entity**

```yaml
# SpecQL Definition
entity: Location
schema: tenant

hierarchical: true          # Triggers LTREE path
metadata_split: true        # Triggers node+info split

fields:
  parent: ref(Location)     # Self-reference for hierarchy

  # Domain attributes (go in info table)
  location_type: ref(LocationType)
  name: text
  legal_name: text
  public_address: ref(PublicAddress)
  int_ordered: integer

# Identifier calculation
identifier:
  strategy: hierarchical_slug
  components:
    - field: public_address.identifier
      prefix: true
    - field: location_type.identifier
      transform: slugify
      separator: "."
    - field: int_ordered
      format: "LPAD({value}, 3, '0')"
      separator: "-"
    - field: name
      transform: slugify
  deduplication: suffix
  recalculate:
    on: [insert, update, parent_change]
    cascade: descendants

operations:
  recalcid: true
```

**Generated SQL** (2000+ lines):

1. **Node Table** (`tb_location`):
```sql
CREATE TABLE tenant.tb_location (
    pk_location INTEGER PRIMARY KEY,
    id UUID UNIQUE,
    identifier TEXT UNIQUE,              -- "toulouse|legal.001-hq#2"
    base_identifier TEXT,                 -- "toulouse|legal.001-hq"
    path LTREE NOT NULL,                  -- "toulouse.legal.hq" (for queries)
    fk_parent_location INTEGER REFERENCES tb_location,
    fk_location_info INTEGER NOT NULL REFERENCES tb_location_info
);

CREATE INDEX idx_location_path_gist ON tb_location USING GIST (path);
CREATE INDEX idx_location_base_identifier ON tb_location(base_identifier);
```

2. **Info Table** (`tb_location_info`):
```sql
CREATE TABLE tenant.tb_location_info (
    pk_location_info INTEGER PRIMARY KEY,
    id UUID UNIQUE,
    identifier TEXT,                      -- Base identifier (no suffix)
    fk_location_type INTEGER,
    name TEXT,
    legal_name TEXT,
    fk_public_address INTEGER,
    int_ordered INTEGER
);
```

3. **Path Maintenance Trigger**:
```sql
CREATE FUNCTION update_location_path() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fk_parent_location IS NULL THEN
        NEW.path := text2ltree(NEW.identifier);
    ELSE
        SELECT path || text2ltree(NEW.identifier)
        INTO NEW.path
        FROM tb_location
        WHERE pk_location = NEW.fk_parent_location;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_location_path
    BEFORE INSERT OR UPDATE OF fk_parent_location, identifier
    ON tb_location
    FOR EACH ROW EXECUTE FUNCTION update_location_path();
```

4. **Identifier Recalculation Function**:
```sql
CREATE FUNCTION core.recalcid_location(
    ctx core.recalculation_context
) RETURNS VOID AS $$
BEGIN
    -- Recursive CTE to build hierarchy
    WITH RECURSIVE t_hierarchy AS (
        -- Root locations
        SELECT
            l.pk_location,
            l.fk_location_info,
            pa.identifier || '|' ||
            slugify(lt.identifier) || '.' ||
            LPAD(COALESCE(li.int_ordered, 10)::text, 3, '0') || '-' ||
            slugify(li.name) AS base_identifier
        FROM tb_location l
        JOIN tb_location_info li ON l.fk_location_info = li.pk_location_info
        JOIN tb_location_type lt ON li.fk_location_type = lt.pk_location_type
        JOIN tb_public_address pa ON li.fk_public_address = pa.pk_public_address
        WHERE l.fk_parent_location IS NULL

        UNION ALL

        -- Child locations
        SELECT
            child.pk_location,
            child.fk_location_info,
            parent.base_identifier || '.' ||
            LPAD(COALESCE(child_info.int_ordered, 10)::text, 3, '0') || '-' ||
            slugify(child_info.name)
        FROM tb_location child
        JOIN tb_location_info child_info ON child.fk_location_info = child_info.pk_location_info
        JOIN t_hierarchy parent ON child.fk_parent_location = parent.pk_location
    )
    -- Deduplicate and update both tables
    -- ... (see IDENTIFIER_CALCULATION_PATTERNS.md for full code)
END;
$$ LANGUAGE plpgsql;
```

5. **Convenience View**:
```sql
CREATE VIEW v_location AS
SELECT
    n.pk_location,
    n.id,
    n.identifier,
    n.path,
    n.fk_parent_location AS parent_id,
    i.name,
    i.legal_name,
    i.fk_location_type
FROM tb_location n
JOIN tb_location_info i ON n.fk_location_info = i.pk_location_info
WHERE n.deleted_at IS NULL;

COMMENT ON VIEW v_location IS '@fraiseql:type name=Location';
```

6. **FraiseQL GraphQL Schema** (auto-generated):
```graphql
type Location {
  id: UUID!
  identifier: String!
  path: String!
  parentId: Int
  name: String!
  legalName: String
  locationType: LocationType!

  # Hierarchy helpers (from LTREE functions)
  ancestors: [Location!]!
  descendants: [Location!]!
  children: [Location!]!
  depth: Int!
}

query {
  location(id: "...") { name, path, parent { name } }
  locations(filter: { pathStartsWith: "toulouse.legal" }) { name }
}
```

**Result**: 20 lines YAML → 2000+ lines production SQL + GraphQL

---

## 🧪 Testing Strategy

### Unit Tests (Per Pattern)

**Pattern 1: Recalcid**
```python
# Test slug generation
def test_hierarchical_slug_format()
def test_flat_slug_format()
def test_deduplication_adds_suffix()

# Test recalcid function generation
def test_generate_recalcid_for_hierarchical_entity()
def test_generate_recalcid_for_flat_entity()
def test_skip_recalcid_if_no_identifier_config()
```

**Pattern 2: LTREE**
```python
# Test path column generation
def test_generate_ltree_path_column()
def test_generate_gist_index()

# Test trigger generation
def test_generate_path_maintenance_trigger()
def test_handle_root_nodes()
def test_handle_child_nodes()
```

**Pattern 3: Node+Info**
```python
# Test table generation
def test_generate_node_table()
def test_generate_info_table()
def test_generate_convenience_view()

# Test field classification
def test_classify_structural_vs_domain_fields()
def test_respect_explicit_table_placement()
```

---

### Integration Tests (End-to-End)

**Scenario 1: Create Location Hierarchy**
```python
def test_location_hierarchy_full_lifecycle(test_db):
    """Test complete location lifecycle with all patterns"""

    # 1. Create root location
    test_db.execute("""
        INSERT INTO v_location (name, location_type, public_address)
        VALUES ('Headquarters', 'legal', 'toulouse-address')
    """)

    # 2. Verify tables updated
    # - tb_location (node) has path, identifier
    # - tb_location_info has attributes
    # - identifier is "toulouse|legal.001-headquarters"
    # - path is "toulouse.legal.headquarters"

    # 3. Create child location
    test_db.execute("""
        INSERT INTO v_location (name, parent_id, ...)
        VALUES ('Building A', root_id, ...)
    """)

    # 4. Verify child
    # - identifier is "toulouse|legal.001-headquarters.002-building-a"
    # - path is "toulouse.legal.headquarters.building-a"

    # 5. Rename parent
    test_db.execute("""
        UPDATE v_location SET name = 'HQ'
        WHERE id = root_id
    """)

    # 6. Verify recalcid cascaded
    # - Parent identifier: "toulouse|legal.001-hq"
    # - Child identifier: "toulouse|legal.001-hq.002-building-a"

    # 7. Move child to different parent
    test_db.execute("""
        UPDATE v_location SET parent_id = other_id
        WHERE id = child_id
    """)

    # 8. Verify path updated
    # - Child path now reflects new parent
    # - recalcid recalculated identifier

    # 9. Query hierarchy
    result = test_db.execute("""
        SELECT name FROM v_location
        WHERE path <@ 'toulouse.legal'
    """)
    # Should return all descendants
```

**Scenario 2: Deduplication**
```python
def test_identifier_deduplication(test_db):
    """Test automatic deduplication with #n suffix"""

    # Create two locations with same name
    test_db.execute("""
        INSERT INTO v_location (name, ...) VALUES ('Office', ...)
    """)
    test_db.execute("""
        INSERT INTO v_location (name, ...) VALUES ('Office', ...)
    """)

    # Call recalcid
    test_db.execute("SELECT core.recalcid_location()")

    # Verify identifiers
    identifiers = test_db.execute("""
        SELECT identifier FROM v_location WHERE name = 'Office'
    """).fetchall()

    assert identifiers[0] == "toulouse|legal.001-office"
    assert identifiers[1] == "toulouse|legal.001-office#2"
```

---

## 🎓 Knowledge Transfer

### For Team A (SpecQL Parser)

**New Responsibilities**:
1. Parse `hierarchical: true` flag → set `entity.is_hierarchical`
2. Parse `metadata_split: true` flag → set `entity.metadata_split`
3. Parse `identifier:` section → create `IdentifierConfig` object
4. Validate: `metadata_split` requires `hierarchical`

**New AST Models**:
```python
@dataclass
class IdentifierConfig:
    strategy: str  # "hierarchical_slug", "flat_slug", "composite_key"
    components: List[IdentifierComponent]
    deduplication: str  # "suffix", "none"
    recalculate: RecalculateConfig

@dataclass
class IdentifierComponent:
    field: str  # Field path (e.g., "public_address.identifier")
    transform: Optional[str]  # "slugify", None
    prefix: bool = False  # Is this the tenant prefix?
    format: Optional[str] = None  # Custom format string
    separator: Optional[str] = None  # Separator after this component
```

---

### For Team B (Schema Generator)

**New Responsibilities**:
1. Generate `slugify()` functions in migration 000
2. Add `identifier` and `base_identifier` columns to all entities
3. Generate `path LTREE` column for hierarchical entities
4. Generate GIST index on `path`
5. Generate path maintenance triggers
6. For `metadata_split` entities:
   - Generate `tb_{entity}` node table
   - Generate `tb_{entity}_info` table
   - Generate `v_{entity}` convenience view
7. Generate helper functions (`ancestors`, `descendants`, etc.)

**New Generators**:
```python
class LtreeGenerator:
    def generate_path_column() -> str
    def generate_gist_index() -> str
    def generate_path_trigger() -> str
    def generate_helper_functions() -> str

class MetadataSplitGenerator:
    def generate_node_table() -> str
    def generate_info_table() -> str
    def generate_convenience_view() -> str

class FieldClassifier:
    def classify() -> Tuple[List[Field], List[Field]]
```

---

### For Team C (Action Compiler)

**New Responsibilities**:
1. Generate `recalcid_{entity}()` functions based on `IdentifierConfig`
2. Build recursive CTEs for hierarchical entities
3. Generate slug expression from components
4. Generate deduplication loop
5. Generate two-table updates (node + info)
6. Integrate with cascade updates

**New Generators**:
```python
class RecalcidGenerator:
    def generate() -> str
    def _build_hierarchy_cte() -> str
    def _build_slug_expression() -> str
    def _build_deduplication_loop() -> str
    def _build_update_statements() -> str

# Strategies
class HierarchicalSlugStrategy:
    def generate_cte() -> str

class FlatSlugStrategy:
    def generate_select() -> str

class CompositeKeyStrategy:
    def generate_select() -> str
```

---

## 📊 Progress Tracking

### Week 1-2: Identifier Recalculation
- [ ] Migration 000: `recalculation_context` type
- [ ] Migration 000: `slugify()` functions
- [ ] AST: `IdentifierConfig` model
- [ ] Parser: Parse `identifier:` section
- [ ] Schema: Add identifier columns
- [ ] Schema: Add identifier indexes
- [ ] Generator: Basic recalcid template
- [ ] Generator: Hierarchical slug strategy
- [ ] Tests: Unit tests (20+ tests)
- [ ] Tests: Integration test (Location)
- [ ] Docs: SpecQL syntax guide

### Week 3-4: LTREE Hierarchical Data
- [ ] Migration 000: LTREE extension
- [ ] Parser: Detect `hierarchical: true`
- [ ] Schema: Generate `path LTREE` column
- [ ] Schema: Generate GIST index
- [ ] Generator: Path maintenance trigger
- [ ] Generator: Descendant path updates
- [ ] Generator: Helper functions
- [ ] Tests: Unit tests (15+ tests)
- [ ] Tests: Integration test (1000-node tree)
- [ ] Docs: LTREE usage examples

### Week 5-6: Node + Info Split
- [ ] Parser: Parse `metadata_split: true`
- [ ] Generator: Field classifier
- [ ] Schema: Node table generation
- [ ] Schema: Info table generation
- [ ] Schema: FK constraints
- [ ] Schema: Convenience view
- [ ] Generator: View FraiseQL annotations
- [ ] Generator: Two-table recalcid
- [ ] Tests: Unit tests (25+ tests)
- [ ] Tests: Integration test (Complex hierarchy)
- [ ] Docs: Node+info pattern guide

---

## 🚀 Getting Started

### Phase 0: Preparation (Before Week 1)

1. **Review documentation**:
   - Read `MISSING_PATTERNS_IMPLEMENTATION.md` (implementation plans)
   - Read `IDENTIFIER_CALCULATION_PATTERNS.md` (production examples)
   - Review PrintOptim backend code (optional)

2. **Set up test database**:
   ```bash
   # Install PostgreSQL 14+
   # Enable extensions
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "ltree";
   CREATE EXTENSION IF NOT EXISTS "unaccent";  # Optional but recommended
   ```

3. **Create test data fixtures**:
   ```bash
   # Sample organizations
   # Sample addresses
   # Sample location types
   # Sample manufacturers
   ```

4. **Team alignment**:
   - Team A: Review AST changes needed
   - Team B: Review schema generation patterns
   - Team C: Review recalcid generation requirements

---

### Phase 1: Week 1, Day 1 (Kickoff)

**Morning**:
1. Create migration 000 file: `migrations/000_framework_foundations.sql`
2. Add `recalculation_context` type (copy from implementation plan)
3. Add `slugify()` functions (copy from identifier patterns doc)
4. Add LTREE extension
5. Run migration: `psql < migrations/000_framework_foundations.sql`

**Afternoon**:
1. Write test: `test_recalculation_context_type_exists()`
2. Write test: `test_slugify_function_works()`
3. Run tests: `uv run pytest tests/integration/test_foundation_types.py -v`
4. ✅ All tests pass

**Evening**: Commit and push

---

## 🔍 Monitoring Success

### Key Metrics

**Code Coverage**: 90%+ for all new code
**Test Pass Rate**: 100% (all tests must pass)
**Integration Success**: All patterns work together
**Performance**: Hierarchical queries < 100ms for 10k nodes

### Weekly Demo

**End of each 2-week cycle**:
1. Live demo of new functionality
2. Show generated SQL
3. Run integration tests
4. Show GraphQL queries (FraiseQL)
5. Performance benchmarks

---

## 📞 Support & Questions

**For Implementation Questions**:
- Check implementation plan first
- Check identifier patterns doc for examples
- Review PrintOptim backend code (if accessible)

**For Architectural Decisions**:
- Create ADR (Architecture Decision Record)
- Get team consensus
- Document in `/docs/architecture/`

**For Bugs/Issues**:
- Create failing test first
- Debug with isolated reproduction
- Fix and verify test passes

---

## 🎉 Success Criteria

**Pattern 1 (Identifier Recalculation)**:
✅ Location identifiers: `toulouse|legal.001-hq.002-building-a`
✅ Deduplication works: `office#2`, `office#3`
✅ Hierarchical recalculation cascades to children

**Pattern 2 (LTREE)**:
✅ Paths auto-maintained: `toulouse.legal.hq.building_a`
✅ Query all descendants: `WHERE path <@ 'toulouse.legal'`
✅ Move nodes updates descendant paths

**Pattern 3 (Node+Info)**:
✅ Two tables generated: `tb_location` + `tb_location_info`
✅ View joins both: `SELECT * FROM v_location`
✅ FraiseQL exposes as GraphQL type

**Overall**:
✅ 20 lines YAML → 2000+ lines production SQL
✅ All tests pass (90%+ coverage)
✅ GraphQL API works through FraiseQL
✅ Performance acceptable (< 100ms queries)
✅ Documentation complete

---

**Ready to start? Begin with Week 1, Day 1 tasks above! 🚀**
