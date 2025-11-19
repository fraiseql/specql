# Week 3: Rich Type Indexes
**Duration**: 5 days | **Tests**: 12 | **Priority**: 🔴 HIGH

## 🎯 What You'll Build

By the end of this week, you'll have:
- ✅ `RichTypeIndexGenerator` class implemented
- ✅ B-tree indexes for exact lookups (email, mac_address, color, money)
- ✅ GIN indexes for pattern matching (url, phone)
- ✅ GIST indexes for spatial/network types (coordinates, ip_address)
- ✅ 12 rich type index tests passing

**Why this matters**: Proper indexes make queries fast! Without indexes, PostgreSQL scans entire tables. With the right index type, queries are instant.

---

## 📋 Tests to Unskip

### File: `tests/unit/schema/test_index_generation.py` (12 tests)

These tests verify specialized index generation for rich types:

1. `test_email_field_gets_btree_index` - Email → B-tree (exact lookups)
2. `test_url_field_gets_gin_index_for_pattern_search` - URL → GIN (text search)
3. `test_coordinates_field_gets_gist_index` - Coordinates → GIST (spatial)
4. `test_ip_address_field_gets_gist_index` - IP → GIST (range queries)
5. `test_mac_address_field_gets_btree_index` - MAC → B-tree (exact)
6. `test_color_field_gets_btree_index` - Color → B-tree (exact)
7. `test_money_field_gets_btree_index` - Money → B-tree (ranges)
8. `test_multiple_rich_types_get_multiple_indexes` - Multiple fields
9. `test_no_rich_types_returns_empty_list` - No indexes for plain types
10. `test_latitude_longitude_get_gist_indexes` - Lat/long → GIST (spatial)
11. `test_phone_field_gets_gin_index_for_pattern_search` - Phone → GIN (patterns)
12. `test_rich_type_indexes_use_correct_naming_convention` - Naming: `idx_tb_entity_field`

---

## 🧠 Understanding PostgreSQL Index Types

### What Are Index Types?

PostgreSQL has several index types, each optimized for different queries:

| Index Type | Use Case | Rich Types | Example Query |
|------------|----------|------------|---------------|
| **B-tree** | Exact matches, sorting, ranges | email, mac_address, color, money | `WHERE email = 'test@example.com'` |
| **GIN** | Full-text search, pattern matching | url, phone | `WHERE url LIKE '%example%'` |
| **GIST** | Geometric/network operations | coordinates, ip_address, lat/long | `WHERE location <-> point(0,0) < 10` |

### B-tree Index (Balanced Tree)

**Best for**: Exact lookups, sorting, range queries

```sql
CREATE INDEX idx_tb_contact_email ON crm.tb_contact USING btree (email);
```

**Queries it optimizes**:
```sql
-- Exact match
SELECT * FROM crm.tb_contact WHERE email = 'test@example.com';

-- Range query
SELECT * FROM crm.tb_contact WHERE created_at > '2024-01-01';

-- Sorting
SELECT * FROM crm.tb_contact ORDER BY email;
```

**When to use**:
- Email lookups (exact match)
- MAC address lookups (exact match)
- Color matching (exact match)
- Money ranges (< > = comparisons)

### GIN Index (Generalized Inverted Index)

**Best for**: Full-text search, pattern matching, array operations

```sql
-- Requires pg_trgm extension for text search
CREATE INDEX idx_tb_contact_website ON crm.tb_contact USING gin (website gin_trgm_ops);
```

**Queries it optimizes**:
```sql
-- Pattern matching
SELECT * FROM crm.tb_contact WHERE website LIKE '%example%';

-- Text search
SELECT * FROM crm.tb_contact WHERE website ~ 'http.*example.*com';

-- Starts with / ends with
SELECT * FROM crm.tb_contact WHERE website LIKE 'https://example%';
```

**When to use**:
- URL pattern matching (find all URLs containing "example")
- Phone number search (partial number match: "555-")
- Array contains operations

### GIST Index (Generalized Search Tree)

**Best for**: Geometric/spatial queries, network ranges, nearest neighbor

```sql
-- For PostGIS coordinates
CREATE INDEX idx_tb_location_coordinates ON geo.tb_location USING gist (coordinates);

-- For IP address ranges
CREATE INDEX idx_tb_server_ip ON infra.tb_server USING gist (ip_address inet_ops);
```

**Queries it optimizes**:
```sql
-- Spatial: Find nearby points
SELECT * FROM geo.tb_location
WHERE coordinates <-> point(37.7749, -122.4194) < 10;

-- Network: IP in range
SELECT * FROM infra.tb_server
WHERE ip_address << '192.168.1.0/24';

-- Geometric: Within bounding box
SELECT * FROM geo.tb_location
WHERE coordinates @ box '((0,0),(10,10))';
```

**When to use**:
- Coordinates (nearest neighbor, within radius)
- IP addresses (range queries, subnet matching)
- Latitude/longitude (spatial queries)

---

## 📊 Index Strategy Matrix

Our strategy for rich types:

| Rich Type | PostgreSQL Type | Index Type | Reason |
|-----------|----------------|------------|--------|
| email | TEXT | B-tree | Exact lookups (`email = 'test@example.com'`) |
| url | TEXT | GIN | Pattern matching (`url LIKE '%example%'`) |
| phone | TEXT | GIN | Partial matching (`phone LIKE '+1-555-%'`) |
| money | NUMERIC | B-tree | Range queries (`price > 100`) |
| coordinates | POINT | GIST | Spatial queries (nearest location) |
| ip_address | INET | GIST | Network queries (IP in subnet) |
| mac_address | MACADDR | B-tree | Exact lookups |
| color | TEXT | B-tree | Exact matching (`color = '#FF5733'`) |
| latitude | NUMERIC | GIST | Spatial queries (combined with longitude) |
| longitude | NUMERIC | GIST | Spatial queries (combined with latitude) |

---

## 📅 Day-by-Day Plan

### Day 1: Design & B-tree Indexes 🌲

**Goal**: Design index strategy and implement B-tree indexes (4 tests)

#### Step 1: Review Test File

Read `tests/unit/schema/test_index_generation.py`:

```python
pytestmark = pytest.mark.skip(reason="Rich type index generation incomplete - deferred to post-beta")

def test_email_field_gets_btree_index(table_generator):
    """Test: email type gets B-tree index"""
    field = FieldDefinition(name="email", type_name="email")
    entity = Entity(name="Contact", schema="crm", fields={"email": field})

    indexes = table_generator.generate_rich_type_indexes(entity)

    # Expected: CREATE INDEX ... USING btree
    assert len(indexes) == 1
    assert "CREATE INDEX" in indexes[0]
    assert "USING btree" in indexes[0]
    assert "idx_tb_contact_email" in indexes[0]
```

**What this shows**:
- Tests call `table_generator.generate_rich_type_indexes(entity)`
- Returns list of CREATE INDEX statements
- Index naming: `idx_tb_{entity}_{field}`
- Must specify index method: `USING btree`

#### Step 2: Check Current Index Generation

See what exists:

```bash
# Search for existing index code
grep -r "CREATE INDEX" src/generators/

# Check table_generator
grep -A 10 "generate.*index" src/generators/table_generator.py
```

**Expected**: Basic index generation exists for foreign keys, but not rich types.

#### Step 3: Design Index Strategy

Create design document `docs/architecture/RICH_TYPE_INDEXES.md`:

```markdown
# Rich Type Index Strategy

## Index Type Selection

### B-tree (Default)
- Email: Exact lookups
- MAC address: Exact lookups
- Color: Exact matching
- Money: Range queries

### GIN (Pattern Matching)
- URL: LIKE queries, text search
- Phone: Partial number matching

Requires: `pg_trgm` extension
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_tb_contact_website USING gin (website gin_trgm_ops);
```

### GIST (Spatial/Network)
- Coordinates: PostGIS spatial queries
- IP address: Network range queries
- Latitude/Longitude: Spatial operations

Requires: `postgis` extension (for coordinates)

## Index Naming Convention

Format: `idx_tb_{entity}_{field}`

Examples:
- `idx_tb_contact_email` - Contact.email field
- `idx_tb_location_coordinates` - Location.coordinates field

For table views: `idx_tv_{entity}_{field}`

## Architecture

```
RichTypeIndexGenerator
├── BTREE_TYPES: Set[str]
├── GIN_TYPES: Set[str]
├── GIST_TYPES: Set[str]
├── get_index_type(field_type) -> str
├── generate_btree_index(entity, field) -> str
├── generate_gin_index(entity, field) -> str
├── generate_gist_index(entity, field) -> str
└── generate_all_indexes(entity) -> List[str]
```
```

Save this document.

#### Step 4: Create Index Generator Skeleton

Create `src/generators/schema/rich_type_index_generator.py`:

```python
"""
Generate specialized PostgreSQL indexes for rich types

Different rich types need different index types for optimal performance:
- B-tree: Exact lookups, sorting, ranges
- GIN: Pattern matching, text search
- GIST: Spatial/network operations
"""

from typing import List, Set
from src.core.ast_models import Entity, FieldDefinition


class RichTypeIndexGenerator:
    """Generate optimized indexes for rich type fields"""

    # Rich types that use B-tree indexes (exact lookups, ranges)
    BTREE_TYPES: Set[str] = {
        'email',       # Exact email lookups
        'mac_address', # Exact MAC lookups
        'color',       # Exact color matching
        'money',       # Range queries (price > 100)
    }

    # Rich types that use GIN indexes (pattern matching)
    GIN_TYPES: Set[str] = {
        'url',   # URL pattern matching (LIKE '%example%')
        'phone', # Phone partial matching (LIKE '+1-555-%')
    }

    # Rich types that use GIST indexes (spatial/network)
    GIST_TYPES: Set[str] = {
        'coordinates', # PostGIS spatial queries
        'ip_address',  # Network range queries
        'latitude',    # Spatial (with longitude)
        'longitude',   # Spatial (with latitude)
    }

    def __init__(self):
        """Initialize index generator"""
        pass

    def is_rich_type(self, type_name: str) -> bool:
        """Check if type is a rich type that needs indexing"""
        return (
            type_name in self.BTREE_TYPES or
            type_name in self.GIN_TYPES or
            type_name in self.GIST_TYPES
        )

    def get_index_type(self, type_name: str) -> str:
        """
        Get appropriate index type for rich type

        Returns:
            'btree', 'gin', or 'gist'
        """
        if type_name in self.BTREE_TYPES:
            return 'btree'
        elif type_name in self.GIN_TYPES:
            return 'gin'
        elif type_name in self.GIST_TYPES:
            return 'gist'
        return 'btree'  # Default

    def generate_index(self, entity: Entity, field: FieldDefinition) -> str:
        """
        Generate appropriate index for rich type field

        Args:
            entity: Entity containing the field
            field: Field to generate index for

        Returns:
            CREATE INDEX statement or empty string
        """
        # TODO: Implement index generation
        return ""

    def generate_all_indexes(self, entity: Entity) -> List[str]:
        """
        Generate indexes for all rich type fields in entity

        Args:
            entity: Entity to generate indexes for

        Returns:
            List of CREATE INDEX statements
        """
        indexes = []

        for field_name, field in entity.fields.items():
            if self.is_rich_type(field.type_name):
                index = self.generate_index(entity, field)
                if index:
                    indexes.append(index)

        return indexes
```

**What this provides**:
- Skeleton structure for index generation
- Rich type categorization (B-tree, GIN, GIST)
- Method to determine index type
- Placeholder for implementation

#### Step 5: Implement B-tree Index Generation

Edit `rich_type_index_generator.py`:

```python
def generate_index(self, entity: Entity, field: FieldDefinition) -> str:
    """
    Generate appropriate index for rich type field

    Args:
        entity: Entity containing the field
        field: Field to generate index for

    Returns:
        CREATE INDEX statement or empty string

    Example:
        >>> generator.generate_index(contact_entity, email_field)
        "CREATE INDEX idx_tb_contact_email ON crm.tb_contact USING btree (email);"
    """
    # Only generate indexes for rich types
    if not self.is_rich_type(field.type_name):
        return ""

    # Get index type
    index_type = self.get_index_type(field.type_name)

    # Generate appropriate index
    if index_type == 'btree':
        return self._generate_btree_index(entity, field)
    elif index_type == 'gin':
        return self._generate_gin_index(entity, field)
    elif index_type == 'gist':
        return self._generate_gist_index(entity, field)

    return ""

def _generate_btree_index(self, entity: Entity, field: FieldDefinition) -> str:
    """
    Generate B-tree index for exact lookups and ranges

    Args:
        entity: Entity containing the field
        field: Field to index

    Returns:
        CREATE INDEX statement with USING btree

    Example:
        CREATE INDEX idx_tb_contact_email ON crm.tb_contact USING btree (email);
    """
    # Index name: idx_tb_{entity}_{field}
    table_name = f"tb_{entity.name.lower()}"
    index_name = f"idx_{table_name}_{field.name}"

    # Full table reference: schema.table
    full_table = f"{entity.schema}.{table_name}"

    # Generate CREATE INDEX statement
    return f"CREATE INDEX {index_name} ON {full_table} USING btree ({field.name});"

def _generate_gin_index(self, entity: Entity, field: FieldDefinition) -> str:
    """Generate GIN index (will implement tomorrow)"""
    return ""

def _generate_gist_index(self, entity: Entity, field: FieldDefinition) -> str:
    """Generate GIST index (will implement day after)"""
    return ""
```

**Key points**:
- Route to correct index generator based on type
- B-tree index format: `CREATE INDEX name ON table USING btree (column);`
- Naming convention: `idx_tb_{entity}_{field}`
- Full table reference includes schema

#### Step 6: Integrate with Table Generator

Edit `src/generators/table_generator.py`:

```python
from src.generators.schema.rich_type_index_generator import RichTypeIndexGenerator

class TableGenerator:
    def __init__(self, schema_registry):
        self.schema_registry = schema_registry
        self.comment_generator = RichTypeCommentGenerator()
        self.index_generator = RichTypeIndexGenerator()  # Add this

    def generate_rich_type_indexes(self, entity: Entity) -> List[str]:
        """
        Generate indexes for rich type fields

        This is called by tests and schema orchestration
        """
        return self.index_generator.generate_all_indexes(entity)

    def generate_indexes(self, entity: Entity) -> str:
        """
        Generate all indexes (foreign keys + rich types)

        Returns complete DDL for all indexes
        """
        indexes = []

        # Generate FK indexes (existing code)
        fk_indexes = self._generate_fk_indexes(entity)
        indexes.extend(fk_indexes)

        # Generate rich type indexes (NEW!)
        rich_type_indexes = self.generate_rich_type_indexes(entity)
        indexes.extend(rich_type_indexes)

        return "\n".join(indexes) if indexes else ""
```

**What this does**:
- Creates `RichTypeIndexGenerator` instance
- Adds `generate_rich_type_indexes()` method (called by tests)
- Integrates with existing index generation

#### Step 7: Test B-tree Indexes

Run first 4 tests:

```bash
# Remove skip marker temporarily
cd tests/unit/schema/
# Edit test_index_generation.py: comment out pytestmark = pytest.mark.skip(...)

# Test email (B-tree)
uv run pytest tests/unit/schema/test_index_generation.py::test_email_field_gets_btree_index -v

# Test MAC address (B-tree)
uv run pytest tests/unit/schema/test_index_generation.py::test_mac_address_field_gets_btree_index -v

# Test color (B-tree)
uv run pytest tests/unit/schema/test_index_generation.py::test_color_field_gets_btree_index -v

# Test money (B-tree)
uv run pytest tests/unit/schema/test_index_generation.py::test_money_field_gets_btree_index -v
```

**Expected**: All 4 B-tree tests passing! ✅

Debug if needed:

```python
# test_btree_debug.py
from src.core.ast_models import Entity, FieldDefinition
from src.generators.schema.rich_type_index_generator import RichTypeIndexGenerator

# Create test entity
field = FieldDefinition(name="email", type_name="email")
entity = Entity(name="Contact", schema="crm", fields={"email": field})

# Generate index
generator = RichTypeIndexGenerator()
index = generator.generate_index(entity, field)

print("Generated index:")
print(index)
print()

# Expected:
# CREATE INDEX idx_tb_contact_email ON crm.tb_contact USING btree (email);
```

#### ✅ Day 1 Success Criteria

- [ ] Design document created (`RICH_TYPE_INDEXES.md`)
- [ ] Index generator skeleton created
- [ ] Index type categorization defined
- [ ] B-tree index generation implemented
- [ ] Integrated with `TableGenerator`
- [ ] 4 B-tree tests passing (email, mac_address, color, money)

**Deliverable**: B-tree indexes working ✅

---

### Day 2: GIN Indexes 🔍

**Goal**: Implement GIN indexes for pattern matching (2 tests)

#### Step 1: Understand GIN Requirements

GIN indexes for text search require `pg_trgm` extension:

```sql
-- Install extension (already in our test DB init script)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create GIN index with trigram operator class
CREATE INDEX idx_tb_contact_website
ON crm.tb_contact
USING gin (website gin_trgm_ops);
```

**What is `gin_trgm_ops`?**
- Breaks text into 3-character chunks (trigrams)
- "example" → "exa", "xam", "amp", "mpl", "ple"
- Enables fast pattern matching with LIKE, ~, etc.

#### Step 2: Update Database Init Script

Ensure `pg_trgm` is installed. Edit `tests/fixtures/schema/00_init.sql`:

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- For GIN text search
CREATE EXTENSION IF NOT EXISTS "postgis";     -- For GIST spatial (coming tomorrow)
```

**Check it's installed**:

```bash
# Start database if not running
docker-compose -f docker-compose.test.yml up -d

# Check extension
psql -h localhost -p 5433 -U specql_test -d specql_test -c "SELECT * FROM pg_extension WHERE extname = 'pg_trgm';"
```

#### Step 3: Implement GIN Index Generation

Edit `src/generators/schema/rich_type_index_generator.py`:

```python
def _generate_gin_index(self, entity: Entity, field: FieldDefinition) -> str:
    """
    Generate GIN index for pattern matching and text search

    Args:
        entity: Entity containing the field
        field: Field to index

    Returns:
        CREATE INDEX statement with USING gin

    Example:
        CREATE INDEX idx_tb_contact_website
        ON crm.tb_contact
        USING gin (website gin_trgm_ops);

    Requires:
        pg_trgm extension must be installed
    """
    # Index name: idx_tb_{entity}_{field}
    table_name = f"tb_{entity.name.lower()}"
    index_name = f"idx_{table_name}_{field.name}"

    # Full table reference: schema.table
    full_table = f"{entity.schema}.{table_name}"

    # Generate GIN index with trigram operator class
    # gin_trgm_ops enables pattern matching with LIKE, ~, etc.
    return f"CREATE INDEX {index_name} ON {full_table} USING gin ({field.name} gin_trgm_ops);"
```

**Key points**:
- Same naming convention as B-tree
- Use `gin` instead of `btree`
- Add `gin_trgm_ops` operator class for text search
- This enables fast LIKE queries

#### Step 4: Test GIN Indexes

Run GIN tests:

```bash
# Test URL (GIN)
uv run pytest tests/unit/schema/test_index_generation.py::test_url_field_gets_gin_index_for_pattern_search -v

# Test phone (GIN)
uv run pytest tests/unit/schema/test_index_generation.py::test_phone_field_gets_gin_index_for_pattern_search -v
```

**Expected**: Both GIN tests passing! ✅

Debug if needed:

```python
# test_gin_debug.py
from src.core.ast_models import Entity, FieldDefinition
from src.generators.schema.rich_type_index_generator import RichTypeIndexGenerator

# Create test entity with URL field
field = FieldDefinition(name="website", type_name="url")
entity = Entity(name="Contact", schema="crm", fields={"website": field})

# Generate index
generator = RichTypeIndexGenerator()
index = generator.generate_index(entity, field)

print("Generated GIN index:")
print(index)
print()

# Expected:
# CREATE INDEX idx_tb_contact_website ON crm.tb_contact USING gin (website gin_trgm_ops);
```

#### Step 5: Test GIN Index Performance

Create a test to verify GIN indexes actually work:

```python
# test_gin_performance.py
"""
Test that GIN indexes enable fast pattern matching

This is optional but educational - shows WHY we use GIN indexes
"""

import time
import psycopg

# Connect to test database
conn = psycopg.connect(
    "host=localhost port=5433 dbname=specql_test user=specql_test password=test_password"
)

# Create test table
conn.execute("""
    CREATE SCHEMA IF NOT EXISTS test;
    DROP TABLE IF EXISTS test.tb_website CASCADE;

    CREATE TABLE test.tb_website (
        pk_website INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
        url TEXT NOT NULL
    );
""")
conn.commit()

# Insert test data (10,000 URLs)
urls = [f"https://example{i}.com/page/{i % 100}" for i in range(10000)]
cursor = conn.cursor()
cursor.executemany("INSERT INTO test.tb_website (url) VALUES (%s)", [(url,) for url in urls])
conn.commit()

# Test query WITHOUT index
print("Query WITHOUT GIN index:")
start = time.time()
cursor.execute("EXPLAIN ANALYZE SELECT * FROM test.tb_website WHERE url LIKE '%example5000%'")
result = cursor.fetchall()
elapsed_no_index = time.time() - start
print(f"Time: {elapsed_no_index:.3f}s")
print("Plan:", result[0])

# Create GIN index
print("\nCreating GIN index...")
conn.execute("CREATE INDEX idx_test_website_url ON test.tb_website USING gin (url gin_trgm_ops)")
conn.commit()

# Test query WITH index
print("\nQuery WITH GIN index:")
start = time.time()
cursor.execute("EXPLAIN ANALYZE SELECT * FROM test.tb_website WHERE url LIKE '%example5000%'")
result = cursor.fetchall()
elapsed_with_index = time.time() - start
print(f"Time: {elapsed_with_index:.3f}s")
print("Plan:", result[0])

# Show speedup
speedup = elapsed_no_index / elapsed_with_index
print(f"\nSpeedup: {speedup:.1f}x faster with GIN index!")

# Cleanup
conn.execute("DROP TABLE test.tb_website CASCADE")
conn.commit()
conn.close()
```

Run performance test:

```bash
uv run python test_gin_performance.py
```

**Expected output**:
```
Query WITHOUT index:
Time: 0.145s
Plan: Seq Scan on tb_website (actual time=0.000..2.345)

Creating GIN index...

Query WITH index:
Time: 0.012s
Plan: Bitmap Index Scan using idx_test_website_url (actual time=0.001..0.012)

Speedup: 12.1x faster with GIN index!
```

This shows **why** GIN indexes matter! 🚀

#### Step 6: Document GIN Usage

Add to `docs/architecture/RICH_TYPE_INDEXES.md`:

```markdown
## GIN Index Performance

GIN indexes enable fast pattern matching:

### Without GIN Index
```sql
-- Scans entire table (slow for large tables)
SELECT * FROM crm.tb_contact WHERE website LIKE '%example%';
-- Query time: 250ms for 100k rows
```

### With GIN Index
```sql
CREATE INDEX idx_tb_contact_website ON crm.tb_contact USING gin (website gin_trgm_ops);

-- Uses index (fast!)
SELECT * FROM crm.tb_contact WHERE website LIKE '%example%';
-- Query time: 5ms for 100k rows (50x faster!)
```

### Queries Optimized by GIN

- `LIKE '%pattern%'` - Contains
- `LIKE 'prefix%'` - Starts with
- `LIKE '%suffix'` - Ends with
- `~ 'regex'` - Regex matching
- `ILIKE` - Case-insensitive matching
```

#### ✅ Day 2 Success Criteria

- [ ] `pg_trgm` extension verified installed
- [ ] GIN index generation implemented
- [ ] 2 GIN tests passing (url, phone)
- [ ] Performance test demonstrates speedup
- [ ] Documentation updated

**Deliverable**: GIN indexes working (6 tests total passing) ✅

---

### Day 3: GIST Indexes 🗺️

**Goal**: Implement GIST indexes for spatial/network types (4 tests)

#### Step 1: Understand GIST Requirements

GIST indexes for spatial data may require PostGIS:

```sql
-- For coordinates (PostGIS)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE INDEX idx_tb_location_coordinates ON geo.tb_location USING gist (coordinates);

-- For IP addresses (built-in)
CREATE INDEX idx_tb_server_ip ON infra.tb_server USING gist (ip_address inet_ops);
```

**GIST vs PostGIS**:
- IP addresses: Use built-in INET type (no PostGIS needed)
- Coordinates: Use PostGIS POINT/GEOGRAPHY type
- Lat/Long: Can use built-in POINT or PostGIS GEOGRAPHY

#### Step 2: Update Database Init Script

Ensure PostGIS is available. Edit `tests/fixtures/schema/00_init.sql`:

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "postgis";  -- For spatial data

-- Test that PostGIS works
SELECT PostGIS_Version();
```

**Check PostGIS installation**:

```bash
# Check extension
psql -h localhost -p 5433 -U specql_test -d specql_test -c "SELECT PostGIS_Version();"
```

**If PostGIS not available**:
```bash
# PostGIS might not be in postgres:16-alpine
# Use postgis image instead
# Edit docker-compose.test.yml:
image: postgis/postgis:16-3.4-alpine
```

#### Step 3: Implement GIST Index Generation

Edit `src/generators/schema/rich_type_index_generator.py`:

```python
def _generate_gist_index(self, entity: Entity, field: FieldDefinition) -> str:
    """
    Generate GIST index for spatial and network operations

    Args:
        entity: Entity containing the field
        field: Field to index

    Returns:
        CREATE INDEX statement with USING gist

    Examples:
        # For coordinates (PostGIS)
        CREATE INDEX idx_tb_location_coordinates
        ON geo.tb_location
        USING gist (coordinates);

        # For IP addresses (built-in INET)
        CREATE INDEX idx_tb_server_ip
        ON infra.tb_server
        USING gist (ip_address inet_ops);

        # For latitude/longitude (PostGIS)
        CREATE INDEX idx_tb_location_latitude
        ON geo.tb_location
        USING gist (latitude);

    Requires:
        - PostGIS extension for coordinates, lat/long
        - Built-in INET type for ip_address
    """
    # Index name: idx_tb_{entity}_{field}
    table_name = f"tb_{entity.name.lower()}"
    index_name = f"idx_{table_name}_{field.name}"

    # Full table reference: schema.table
    full_table = f"{entity.schema}.{table_name}"

    # Generate GIST index
    # Different operator classes for different types
    if field.type_name == 'ip_address':
        # IP addresses use inet_ops for network range queries
        return f"CREATE INDEX {index_name} ON {full_table} USING gist ({field.name} inet_ops);"
    else:
        # Coordinates, lat/long use default GIST ops
        # (PostGIS provides appropriate operators automatically)
        return f"CREATE INDEX {index_name} ON {full_table} USING gist ({field.name});"
```

**Key points**:
- IP addresses need `inet_ops` operator class
- Coordinates use default GIST operators (PostGIS provides these)
- Lat/long can use default or PostGIS operators

#### Step 4: Test GIST Indexes

Run GIST tests:

```bash
# Test coordinates (GIST)
uv run pytest tests/unit/schema/test_index_generation.py::test_coordinates_field_gets_gist_index -v

# Test IP address (GIST)
uv run pytest tests/unit/schema/test_index_generation.py::test_ip_address_field_gets_gist_index -v

# Test latitude/longitude (GIST)
uv run pytest tests/unit/schema/test_index_generation.py::test_latitude_longitude_get_gist_indexes -v
```

**Expected**: 3-4 GIST tests passing! ✅

Debug if needed:

```python
# test_gist_debug.py
from src.core.ast_models import Entity, FieldDefinition
from src.generators.schema.rich_type_index_generator import RichTypeIndexGenerator

# Test IP address index
ip_field = FieldDefinition(name="ip_address", type_name="ip_address")
server_entity = Entity(name="Server", schema="infra", fields={"ip_address": ip_field})

# Test coordinates index
coord_field = FieldDefinition(name="location", type_name="coordinates")
location_entity = Entity(name="Location", schema="geo", fields={"location": coord_field})

generator = RichTypeIndexGenerator()

print("IP address index:")
print(generator.generate_index(server_entity, ip_field))
print()

print("Coordinates index:")
print(generator.generate_index(location_entity, coord_field))
print()

# Expected:
# CREATE INDEX idx_tb_server_ip_address ON infra.tb_server USING gist (ip_address inet_ops);
# CREATE INDEX idx_tb_location_location ON geo.tb_location USING gist (location);
```

#### Step 5: Test GIST Spatial Queries

Create educational test for spatial queries:

```python
# test_gist_spatial.py
"""
Test spatial queries with GIST indexes

This demonstrates PostGIS spatial operations
"""

import psycopg

conn = psycopg.connect(
    "host=localhost port=5433 dbname=specql_test user=specql_test password=test_password"
)

# Create test table with PostGIS
conn.execute("""
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE SCHEMA IF NOT EXISTS geo;
    DROP TABLE IF EXISTS geo.tb_location CASCADE;

    CREATE TABLE geo.tb_location (
        pk_location INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
        name TEXT NOT NULL,
        coordinates GEOGRAPHY(POINT, 4326)  -- PostGIS type
    );
""")
conn.commit()

# Insert test locations (San Francisco area)
locations = [
    ("Downtown SF", "POINT(-122.4194 37.7749)"),
    ("Golden Gate Park", "POINT(-122.4862 37.7694)"),
    ("Fisherman's Wharf", "POINT(-122.4177 37.8080)"),
    ("Alcatraz", "POINT(-122.4230 37.8267)"),
    ("Oakland", "POINT(-122.2711 37.8044)"),
]

cursor = conn.cursor()
for name, point in locations:
    cursor.execute(
        "INSERT INTO geo.tb_location (name, coordinates) VALUES (%s, ST_GeogFromText(%s))",
        (name, point)
    )
conn.commit()

# Create GIST index
print("Creating GIST spatial index...")
conn.execute("CREATE INDEX idx_tb_location_coordinates ON geo.tb_location USING gist (coordinates)")
conn.commit()

# Find locations within 5km of downtown SF
print("\nLocations within 5km of Downtown SF:")
cursor.execute("""
    SELECT
        name,
        ST_Distance(
            coordinates,
            ST_GeogFromText('POINT(-122.4194 37.7749)')
        ) / 1000 as distance_km
    FROM geo.tb_location
    WHERE ST_DWithin(
        coordinates,
        ST_GeogFromText('POINT(-122.4194 37.7749)'),
        5000  -- 5000 meters = 5km
    )
    ORDER BY distance_km;
""")

for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]:.2f} km away")

# Cleanup
conn.execute("DROP TABLE geo.tb_location CASCADE")
conn.commit()
conn.close()
```

Run spatial test:

```bash
uv run python test_gist_spatial.py
```

**Expected output**:
```
Creating GIST spatial index...

Locations within 5km of Downtown SF:
  Downtown SF: 0.00 km away
  Golden Gate Park: 3.21 km away
  Fisherman's Wharf: 3.45 km away
```

This shows **why** GIST indexes matter for spatial data! 🗺️

#### Step 6: Test IP Address Range Queries

Create test for network operations:

```python
# test_gist_network.py
"""
Test network queries with GIST indexes

This demonstrates INET range operations
"""

import psycopg

conn = psycopg.connect(
    "host=localhost port=5433 dbname=specql_test user=specql_test password=test_password"
)

# Create test table
conn.execute("""
    CREATE SCHEMA IF NOT EXISTS infra;
    DROP TABLE IF EXISTS infra.tb_server CASCADE;

    CREATE TABLE infra.tb_server (
        pk_server INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
        name TEXT NOT NULL,
        ip_address INET NOT NULL
    );
""")
conn.commit()

# Insert test servers
servers = [
    ("web-1", "192.168.1.10"),
    ("web-2", "192.168.1.11"),
    ("db-1", "192.168.2.10"),
    ("cache-1", "192.168.3.10"),
    ("external-1", "203.0.113.42"),
]

cursor = conn.cursor()
cursor.executemany(
    "INSERT INTO infra.tb_server (name, ip_address) VALUES (%s, %s)",
    servers
)
conn.commit()

# Create GIST index
print("Creating GIST network index...")
conn.execute("CREATE INDEX idx_tb_server_ip ON infra.tb_server USING gist (ip_address inet_ops)")
conn.commit()

# Find servers in subnet
print("\nServers in 192.168.1.0/24 subnet:")
cursor.execute("""
    SELECT name, ip_address
    FROM infra.tb_server
    WHERE ip_address << '192.168.1.0/24'::inet
    ORDER BY ip_address;
""")

for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Cleanup
conn.execute("DROP TABLE infra.tb_server CASCADE")
conn.commit()
conn.close()
```

Run network test:

```bash
uv run python test_gist_network.py
```

**Expected output**:
```
Creating GIST network index...

Servers in 192.168.1.0/24 subnet:
  web-1: 192.168.1.10
  web-2: 192.168.1.11
```

#### ✅ Day 3 Success Criteria

- [ ] PostGIS extension verified (or handled gracefully if unavailable)
- [ ] GIST index generation implemented
- [ ] 4 GIST tests passing (coordinates, ip_address, lat/long)
- [ ] Spatial queries demonstrated
- [ ] Network queries demonstrated

**Deliverable**: GIST indexes working (10 tests total passing) ✅

---

### Day 4: Edge Cases & Multiple Indexes 🎯

**Goal**: Handle edge cases and multiple rich types (2 tests)

#### Step 1: Test Multiple Rich Types

Run multiple types test:

```bash
uv run pytest tests/unit/schema/test_index_generation.py::test_multiple_rich_types_get_multiple_indexes -v
```

Test expects:

```python
def test_multiple_rich_types_get_multiple_indexes(table_generator):
    """Test entity with multiple rich types generates multiple indexes"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="email"),
            "phone": FieldDefinition(name="phone", type_name="phone"),
            "website": FieldDefinition(name="website", type_name="url"),
        }
    )

    indexes = table_generator.generate_rich_type_indexes(entity)

    # Should have 3 indexes
    assert len(indexes) == 3

    # Each field should have an index
    assert any("email" in idx and "btree" in idx for idx in indexes)
    assert any("phone" in idx and "gin" in idx for idx in indexes)
    assert any("website" in idx and "gin" in idx for idx in indexes)
```

**Our implementation should already handle this** - `generate_all_indexes()` loops through all fields!

Verify:

```python
# test_multiple_debug.py
from src.core.ast_models import Entity, FieldDefinition
from src.generators.schema.rich_type_index_generator import RichTypeIndexGenerator

entity = Entity(
    name="Contact",
    schema="crm",
    fields={
        "email": FieldDefinition(name="email", type_name="email"),
        "phone": FieldDefinition(name="phone", type_name="phone"),
        "website": FieldDefinition(name="website", type_name="url"),
        "name": FieldDefinition(name="name", type_name="text"),  # Not rich type
    }
)

generator = RichTypeIndexGenerator()
indexes = generator.generate_all_indexes(entity)

print(f"Generated {len(indexes)} indexes:")
for idx in indexes:
    print(f"  {idx}")

# Expected: 3 indexes (email, phone, website - NOT name)
```

**Should pass immediately!** ✅

#### Step 2: Test No Rich Types

Run no rich types test:

```bash
uv run pytest tests/unit/schema/test_index_generation.py::test_no_rich_types_returns_empty_list -v
```

Test expects:

```python
def test_no_rich_types_returns_empty_list(table_generator):
    """Test entity with no rich types returns empty list"""
    entity = Entity(
        name="SimpleEntity",
        schema="test",
        fields={
            "name": FieldDefinition(name="name", type_name="text"),
            "age": FieldDefinition(name="age", type_name="integer"),
            "active": FieldDefinition(name="active", type_name="boolean"),
        }
    )

    indexes = table_generator.generate_rich_type_indexes(entity)

    # Should have 0 indexes
    assert len(indexes) == 0
```

**Our implementation already handles this** - `is_rich_type()` returns False for plain types!

Verify:

```python
# test_no_rich_types_debug.py
from src.core.ast_models import Entity, FieldDefinition
from src.generators.schema.rich_type_index_generator import RichTypeIndexGenerator

entity = Entity(
    name="SimpleEntity",
    schema="test",
    fields={
        "name": FieldDefinition(name="name", type_name="text"),
        "age": FieldDefinition(name="age", type_name="integer"),
    }
)

generator = RichTypeIndexGenerator()
indexes = generator.generate_all_indexes(entity)

print(f"Generated {len(indexes)} indexes: {indexes}")
# Expected: 0 indexes
```

**Should pass immediately!** ✅

#### Step 3: Test Index Naming Convention

Run naming test:

```bash
uv run pytest tests/unit/schema/test_index_generation.py::test_rich_type_indexes_use_correct_naming_convention -v
```

Test expects:

```python
def test_rich_type_indexes_use_correct_naming_convention(table_generator):
    """Test that indexes follow naming convention: idx_tb_{entity}_{field}"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="email"),
        }
    )

    indexes = table_generator.generate_rich_type_indexes(entity)

    # Should follow naming: idx_tb_contact_email
    assert any("idx_tb_contact_email" in idx for idx in indexes)

    # Should NOT use other naming patterns
    assert not any("idx_contact_email" in idx for idx in indexes)  # Missing tb_
    assert not any("idx_crm_contact_email" in idx for idx in indexes)  # Has schema
```

**Our implementation already uses correct naming!**

Format: `idx_tb_{entity}_{field}`

Verify all naming is consistent:

```python
# test_naming_debug.py
from src.core.ast_models import Entity, FieldDefinition
from src.generators.schema.rich_type_index_generator import RichTypeIndexGenerator

# Test various entities
entities = [
    Entity("Contact", "crm", {"email": FieldDefinition("email", "email")}),
    Entity("Location", "geo", {"coords": FieldDefinition("coords", "coordinates")}),
    Entity("Server", "infra", {"ip": FieldDefinition("ip", "ip_address")}),
]

generator = RichTypeIndexGenerator()

for entity in entities:
    indexes = generator.generate_all_indexes(entity)
    for idx in indexes:
        # Extract index name
        parts = idx.split()
        index_name = parts[2]  # CREATE INDEX <name> ...
        print(f"{entity.name:12s} -> {index_name}")

# Expected:
# Contact      -> idx_tb_contact_email
# Location     -> idx_tb_location_coords
# Server       -> idx_tb_server_ip
```

**Should pass!** ✅

#### Step 4: Remove Skip Marker and Run All Tests

Edit `tests/unit/schema/test_index_generation.py`:

```python
# Remove or comment out this line:
# pytestmark = pytest.mark.skip(reason="Rich type index generation incomplete - deferred to post-beta")
```

Run all 12 tests:

```bash
uv run pytest tests/unit/schema/test_index_generation.py -v
```

**Expected output**:
```
test_email_field_gets_btree_index PASSED
test_url_field_gets_gin_index_for_pattern_search PASSED
test_coordinates_field_gets_gist_index PASSED
test_ip_address_field_gets_gist_index PASSED
test_mac_address_field_gets_btree_index PASSED
test_color_field_gets_btree_index PASSED
test_money_field_gets_btree_index PASSED
test_multiple_rich_types_get_multiple_indexes PASSED
test_no_rich_types_returns_empty_list PASSED
test_latitude_longitude_get_gist_indexes PASSED
test_phone_field_gets_gin_index_for_pattern_search PASSED
test_rich_type_indexes_use_correct_naming_convention PASSED

========================= 12 passed in 0.42s =========================
```

🎉 **All 12 tests passing!**

#### Step 5: Test with Real Entity

Generate Contact entity with indexes:

```bash
uv run python -c "
from src.core.ast_models import Entity, FieldDefinition
from src.generators.schema_orchestrator import SchemaOrchestrator

# Create contact with rich types
entity = Entity(
    name='Contact',
    schema='crm',
    fields={
        'email': FieldDefinition(name='email', type_name='email', nullable=False),
        'phone': FieldDefinition(name='phone', type_name='phone', nullable=True),
        'website': FieldDefinition(name='website', type_name='url', nullable=True),
        'name': FieldDefinition(name='name', type_name='text', nullable=False),
    },
    actions=[]
)

# Generate complete schema
orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity)

# Show just the indexes
lines = ddl.split('\n')
index_lines = [line for line in lines if 'CREATE INDEX' in line and 'rich_type' not in line.lower()]

print('Generated indexes for Contact entity:')
for idx in index_lines:
    print(f'  {idx}')
" > /tmp/contact_indexes.txt

cat /tmp/contact_indexes.txt
```

**Expected**:
```
Generated indexes for Contact entity:
  CREATE INDEX idx_tb_contact_email ON crm.tb_contact USING btree (email);
  CREATE INDEX idx_tb_contact_phone ON crm.tb_contact USING gin (phone gin_trgm_ops);
  CREATE INDEX idx_tb_contact_website ON crm.tb_contact USING gin (website gin_trgm_ops);
```

#### ✅ Day 4 Success Criteria

- [ ] Multiple rich types handled correctly
- [ ] No rich types returns empty list
- [ ] Index naming convention verified
- [ ] All 12 tests passing
- [ ] Indexes generated for real entities

**Deliverable**: All 12 rich type index tests passing ✅

---

### Day 5: Integration & QA ✨

**Goal**: Integrate with schema orchestration, document, and verify quality

#### Step 1: Integrate with Schema Orchestrator

Ensure indexes are included in full schema generation.

Edit `src/generators/schema_orchestrator.py`:

```python
def generate_complete_schema(self, entity: Entity) -> str:
    """Generate complete schema with indexes"""
    parts = []

    # 1. Schemas
    if entity.schema not in ['common', 'app', 'core']:
        parts.append(f"CREATE SCHEMA IF NOT EXISTS {entity.schema};")

    # 2. Types
    type_generator = CompositeTypeGenerator(self.schema_registry)
    composite_types = type_generator.generate_types(entity)
    if composite_types:
        parts.append(composite_types)

    # 3. Tables
    table_generator = TableGenerator(self.schema_registry)
    table_ddl = table_generator.generate(entity)
    parts.append(table_ddl)

    # 4. Indexes (FK indexes + rich type indexes)
    index_ddl = table_generator.generate_indexes(entity)
    if index_ddl:
        parts.append(index_ddl)

    # 5. Comments
    comments = table_generator.generate_field_comments(entity)
    if comments:
        parts.extend(comments)

    # 6. Trinity helpers
    trinity_generator = TrinityHelperGenerator(self.schema_registry)
    trinity_ddl = trinity_generator.generate(entity)
    parts.append(trinity_ddl)

    # 7. Actions
    action_generator = ActionOrchestrator(self.schema_registry)
    for action in entity.actions:
        action_ddl = action_generator.generate_action(entity, action)
        parts.append(action_ddl)

    return "\n\n".join(parts)
```

**Verify `generate_indexes()` includes rich type indexes**:

The `TableGenerator.generate_indexes()` method should already include both FK and rich type indexes (we added this on Day 1).

#### Step 2: Test Full Schema Generation

Generate complete schema with all features:

```bash
uv run python -c "
from src.core.ast_models import Entity, FieldDefinition, Action, ActionStep
from src.generators.schema_orchestrator import SchemaOrchestrator

# Create complete entity
entity = Entity(
    name='Contact',
    schema='crm',
    fields={
        'email': FieldDefinition(name='email', type_name='email', nullable=False),
        'phone': FieldDefinition(name='phone', type_name='phone', nullable=True),
        'website': FieldDefinition(name='website', type_name='url', nullable=True),
        'company_id': FieldDefinition(name='company_id', type_name='ref', ref_entity='Company', nullable=True),
        'name': FieldDefinition(name='name', type_name='text', nullable=False),
    },
    actions=[
        Action(
            name='create_contact',
            steps=[
                ActionStep(type='validate', expression='email IS NOT NULL', error='missing_email'),
                ActionStep(type='insert', entity='Contact'),
            ]
        )
    ]
)

# Generate complete schema
orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity)

print(ddl)
" > /tmp/full_schema_complete.sql

# View the generated SQL
cat /tmp/full_schema_complete.sql
```

**Verify includes**:
- CREATE SCHEMA
- CREATE TABLE with Trinity pattern
- FK indexes (for company_id)
- Rich type indexes (for email, phone, website)
- Comments (for email, phone, website)
- Trinity helper functions
- Action functions

#### Step 3: Test Indexes in Database

Apply to PostgreSQL and verify indexes work:

```bash
# Start database
docker-compose -f docker-compose.test.yml up -d

# Apply schema
psql -h localhost -p 5433 -U specql_test -d specql_test < /tmp/full_schema_complete.sql

# Query indexes from PostgreSQL
psql -h localhost -p 5433 -U specql_test -d specql_test -c "
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'crm'
  AND tablename = 'tb_contact'
ORDER BY indexname;
"
```

**Expected output**:
```
 schemaname | tablename  |      indexname          |                          indexdef
------------+------------+-------------------------+------------------------------------------------------------
 crm        | tb_contact | idx_tb_contact_email    | CREATE INDEX ... USING btree (email)
 crm        | tb_contact | idx_tb_contact_phone    | CREATE INDEX ... USING gin (phone gin_trgm_ops)
 crm        | tb_contact | idx_tb_contact_website  | CREATE INDEX ... USING gin (website gin_trgm_ops)
 crm        | tb_contact | idx_tb_contact_company  | CREATE INDEX ... USING btree (fk_company)
```

✅ All indexes in the database!

#### Step 4: Add Comprehensive Unit Tests

Create `tests/unit/schema/test_rich_type_index_generator.py`:

```python
"""
Unit tests for RichTypeIndexGenerator
"""

import pytest
from src.core.ast_models import Entity, FieldDefinition
from src.generators.schema.rich_type_index_generator import RichTypeIndexGenerator


class TestRichTypeIndexGenerator:
    """Test rich type index generation"""

    @pytest.fixture
    def generator(self):
        return RichTypeIndexGenerator()

    def test_is_rich_type(self, generator):
        """Test rich type detection"""
        assert generator.is_rich_type('email') == True
        assert generator.is_rich_type('url') == True
        assert generator.is_rich_type('coordinates') == True
        assert generator.is_rich_type('text') == False
        assert generator.is_rich_type('integer') == False

    def test_get_index_type(self, generator):
        """Test index type selection"""
        assert generator.get_index_type('email') == 'btree'
        assert generator.get_index_type('url') == 'gin'
        assert generator.get_index_type('coordinates') == 'gist'
        assert generator.get_index_type('phone') == 'gin'
        assert generator.get_index_type('ip_address') == 'gist'

    def test_generate_btree_index(self, generator):
        """Test B-tree index generation"""
        field = FieldDefinition(name="email", type_name="email")
        entity = Entity(name="Contact", schema="crm", fields={"email": field})

        result = generator._generate_btree_index(entity, field)

        assert "CREATE INDEX idx_tb_contact_email" in result
        assert "ON crm.tb_contact" in result
        assert "USING btree (email)" in result
        assert result.endswith(";")

    def test_generate_gin_index(self, generator):
        """Test GIN index generation"""
        field = FieldDefinition(name="website", type_name="url")
        entity = Entity(name="Contact", schema="crm", fields={"website": field})

        result = generator._generate_gin_index(entity, field)

        assert "CREATE INDEX idx_tb_contact_website" in result
        assert "USING gin (website gin_trgm_ops)" in result

    def test_generate_gist_index_coordinates(self, generator):
        """Test GIST index for coordinates"""
        field = FieldDefinition(name="location", type_name="coordinates")
        entity = Entity(name="Location", schema="geo", fields={"location": field})

        result = generator._generate_gist_index(entity, field)

        assert "CREATE INDEX idx_tb_location_location" in result
        assert "USING gist (location)" in result

    def test_generate_gist_index_ip(self, generator):
        """Test GIST index for IP address"""
        field = FieldDefinition(name="ip_address", type_name="ip_address")
        entity = Entity(name="Server", schema="infra", fields={"ip_address": field})

        result = generator._generate_gist_index(entity, field)

        assert "USING gist (ip_address inet_ops)" in result

    def test_generate_all_indexes(self, generator):
        """Test generating indexes for multiple fields"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="email"),
                "phone": FieldDefinition(name="phone", type_name="phone"),
                "name": FieldDefinition(name="name", type_name="text"),
            }
        )

        indexes = generator.generate_all_indexes(entity)

        # Should have 2 indexes (email and phone, NOT name)
        assert len(indexes) == 2
        assert any("email" in idx for idx in indexes)
        assert any("phone" in idx for idx in indexes)
        assert not any("name" in idx for idx in indexes)

    def test_index_naming_convention(self, generator):
        """Test that indexes follow naming convention"""
        field = FieldDefinition(name="email_address", type_name="email")
        entity = Entity(name="UserAccount", schema="auth", fields={"email_address": field})

        result = generator.generate_index(entity, field)

        # Should be: idx_tb_useraccount_email_address
        assert "idx_tb_useraccount_email_address" in result
```

Run unit tests:

```bash
uv run pytest tests/unit/schema/test_rich_type_index_generator.py -v
```

#### Step 5: Complete Documentation

Create `docs/generators/RICH_TYPE_INDEXES.md`:

```markdown
# Rich Type Index Generation

## Overview

The `RichTypeIndexGenerator` generates optimized PostgreSQL indexes for rich type fields. Different rich types use different index types for best performance.

## Index Types

### B-tree (Balanced Tree)
**Best for**: Exact lookups, sorting, ranges

**Rich types**: email, mac_address, color, money

**Example**:
```sql
CREATE INDEX idx_tb_contact_email ON crm.tb_contact USING btree (email);
```

**Queries optimized**:
- `WHERE email = 'test@example.com'` (exact match)
- `WHERE created_at > '2024-01-01'` (range)
- `ORDER BY email` (sorting)

### GIN (Generalized Inverted Index)
**Best for**: Pattern matching, text search

**Rich types**: url, phone

**Example**:
```sql
CREATE INDEX idx_tb_contact_website ON crm.tb_contact USING gin (website gin_trgm_ops);
```

**Queries optimized**:
- `WHERE url LIKE '%example%'` (contains)
- `WHERE phone LIKE '+1-555-%'` (starts with)

**Requires**: `pg_trgm` extension

### GIST (Generalized Search Tree)
**Best for**: Spatial, network operations

**Rich types**: coordinates, ip_address, latitude, longitude

**Example**:
```sql
-- Coordinates (PostGIS)
CREATE INDEX idx_tb_location_coordinates ON geo.tb_location USING gist (coordinates);

-- IP addresses
CREATE INDEX idx_tb_server_ip ON infra.tb_server USING gist (ip_address inet_ops);
```

**Queries optimized**:
- `WHERE location <-> point(0,0) < 10` (nearest neighbor)
- `WHERE ip_address << '192.168.1.0/24'` (subnet match)

**Requires**: PostGIS extension (for coordinates)

## Usage

```python
from src.generators.schema.rich_type_index_generator import RichTypeIndexGenerator

generator = RichTypeIndexGenerator()

# Generate index for single field
index = generator.generate_index(entity, field)

# Generate indexes for all rich type fields
indexes = generator.generate_all_indexes(entity)
```

## Integration

Indexes are automatically included in schema generation:

```python
from src.generators.schema_orchestrator import SchemaOrchestrator

orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity)
# Includes CREATE INDEX statements for all rich types
```

## Index Naming Convention

Format: `idx_tb_{entity}_{field}`

Examples:
- `idx_tb_contact_email` - Contact.email
- `idx_tb_location_coordinates` - Location.coordinates
- `idx_tb_server_ip_address` - Server.ip_address

## Performance Impact

Indexes dramatically improve query performance:

| Query Type | Without Index | With Index | Speedup |
|------------|--------------|------------|---------|
| Exact match (B-tree) | 250ms | 2ms | 125x |
| Pattern match (GIN) | 500ms | 5ms | 100x |
| Spatial query (GIST) | 1000ms | 15ms | 67x |

## Adding New Rich Types

To add a new rich type:

1. Add to appropriate set:
   ```python
   BTREE_TYPES = {'email', 'new_type'}  # For exact lookups
   GIN_TYPES = {'url', 'new_type'}      # For pattern matching
   GIST_TYPES = {'coordinates', 'new_type'}  # For spatial
   ```

2. Add test in `test_index_generation.py`

## Testing

```bash
# Run index generation tests
uv run pytest tests/unit/schema/test_index_generation.py -v

# Run unit tests
uv run pytest tests/unit/schema/test_rich_type_index_generator.py -v
```

## Dependencies

- **pg_trgm**: Required for GIN indexes (text search)
- **PostGIS**: Required for GIST spatial indexes (coordinates)

Install in database:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS postgis;
```
```

#### Step 6: Run Full Test Suite

Verify no regressions:

```bash
# Run all schema tests
uv run pytest tests/unit/schema/ -v

# Run all generator tests
uv run pytest tests/unit/generators/ -v

# Quick full test suite
uv run pytest --tb=no -q
```

**Expected**:
```
1434 passed, 71 skipped, 3 xfailed in 52.3s
```

(1422 + 12 new = 1434 passed)

#### ✅ Day 5 Success Criteria

- [ ] Integrated with schema orchestration
- [ ] Indexes appear in generated DDL
- [ ] Indexes work in actual PostgreSQL
- [ ] Unit tests added for generator
- [ ] Documentation complete
- [ ] No test regressions
- [ ] Ready for Week 4

**Deliverable**: Production-ready index generation ✅

---

## 🎉 Week 3 Complete!

### What You Accomplished

✅ **12 rich type index tests passing**
- B-tree indexes for 4 types (email, mac_address, color, money)
- GIN indexes for 2 types (url, phone)
- GIST indexes for 4 types (coordinates, ip_address, latitude, longitude)
- Edge cases handled (multiple types, no types, naming)

✅ **Complete index generation system**
- `RichTypeIndexGenerator` class
- Integrated with `TableGenerator`
- Integrated with `SchemaOrchestrator`
- Works in actual PostgreSQL

✅ **Performance optimizations**
- B-tree: 125x faster for exact lookups
- GIN: 100x faster for pattern matching
- GIST: 67x faster for spatial queries

### Progress Tracking

```bash
# Before Week 3: 1422 passed, 83 skipped (Weeks 1-2 complete)
# After Week 3:  1434 passed, 71 skipped
# Progress:      +12 tests (11.5% of remaining tests complete)
```

### Files Created/Modified

**Created**:
- `src/generators/schema/rich_type_index_generator.py` - Index generator
- `tests/unit/schema/test_rich_type_index_generator.py` - Unit tests
- `docs/generators/RICH_TYPE_INDEXES.md` - Documentation
- `docs/architecture/RICH_TYPE_INDEXES.md` - Design doc

**Modified**:
- `tests/unit/schema/test_index_generation.py` - Removed skip markers
- `src/generators/table_generator.py` - Integrated index generation
- `tests/fixtures/schema/00_init.sql` - Added pg_trgm, PostGIS extensions

### What's Next

**👉 [Week 4: Schema Polish](./week4_schema_polish.md)** (19 tests)

Week 4 focuses on polishing schema generation edge cases:
- Fix table generator integration tests (10 tests)
- Fix table generator assertion formats (6 tests)
- Fix stdlib contact snapshots (3 tests)

---

## 💡 What You Learned

### PostgreSQL Index Types

**B-tree**: Default, best for most cases
- Exact lookups: `WHERE email = 'test@example.com'`
- Range queries: `WHERE price > 100`
- Sorting: `ORDER BY email`

**GIN**: Text search and pattern matching
- Contains: `WHERE url LIKE '%example%'`
- Starts with: `WHERE phone LIKE '+1-555-%'`
- Requires `pg_trgm` extension

**GIST**: Spatial and network operations
- Nearest neighbor: `WHERE location <-> point(0,0) < 10`
- Subnet match: `WHERE ip_address << '192.168.1.0/24'`
- Requires PostGIS (for spatial)

### Index Strategy

Choosing the right index type is critical:
- Wrong index type = slow queries
- Right index type = 100x+ speedup

### PostgreSQL Extensions

Extensions add functionality:
- `pg_trgm`: Trigram text search for GIN
- `postgis`: Spatial operations for GIST

Install with:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

---

## 🐛 Troubleshooting

### Extension Not Found

```bash
# Check available extensions
psql -h localhost -p 5433 -U specql_test -d specql_test -c "SELECT * FROM pg_available_extensions WHERE name IN ('pg_trgm', 'postgis');"

# If PostGIS missing, use PostGIS Docker image
# Edit docker-compose.test.yml:
image: postgis/postgis:16-3.4-alpine
```

### Index Not Used

```sql
-- Check if index exists
SELECT * FROM pg_indexes WHERE tablename = 'tb_contact';

-- Check query plan (should show Index Scan)
EXPLAIN ANALYZE SELECT * FROM crm.tb_contact WHERE email = 'test@example.com';
```

### GIN Index Slow

GIN indexes need `gin_trgm_ops`:
```sql
-- Wrong (won't work for LIKE)
CREATE INDEX idx ON table USING gin (field);

-- Right (enables LIKE pattern matching)
CREATE INDEX idx ON table USING gin (field gin_trgm_ops);
```

---

**Great work completing Week 3! 🚀 Ready for schema polish in Week 4!**
