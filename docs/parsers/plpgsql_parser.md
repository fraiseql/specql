# PL/pgSQL Parser Documentation

## Overview

The PL/pgSQL Parser is a comprehensive reverse engineering tool that converts PostgreSQL databases into SpecQL YAML entities. It provides the missing foundation for PL/pgSQL support in SpecQL by enabling bidirectional conversion between databases and SpecQL schemas.

## Architecture

The parser consists of several key components:

- **PLpgSQLParser**: Main entry point for parsing operations
- **SchemaAnalyzer**: Parses CREATE TABLE DDL statements
- **TypeMapper**: Maps PostgreSQL types to SpecQL FieldTypes
- **PatternDetector**: Detects SpecQL patterns (Trinity, audit fields, etc.)
- **FunctionAnalyzer**: Parses PL/pgSQL functions into actions

## Usage

### CLI Usage

The PL/pgSQL parser is integrated into the SpecQL CLI for easy command-line usage:

```bash
# Parse DDL from file
specql parse-plpgsql schema.sql

# Parse with preview mode (shows summary without full output)
specql parse-plpgsql schema.sql --preview

# Parse database directly
specql parse-plpgsql --connection-string "postgresql://user:pass@localhost:5432/db"

# Parse specific schemas
specql parse-plpgsql --connection-string "postgresql://..." --schemas crm sales

# Include PL/pgSQL functions as actions
specql parse-plpgsql --connection-string "postgresql://..." --include-functions

# Adjust confidence threshold (0.0-1.0)
specql parse-plpgsql schema.sql --confidence-threshold 0.5

# Get help
specql parse-plpgsql --help
```

### Basic DDL Parsing

```python
from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser

parser = PLpgSQLParser()

ddl = """
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY,
    id UUID NOT NULL,
    identifier TEXT,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
"""

entities = parser.parse_ddl_string(ddl)
print(f"Parsed {len(entities)} entities")
```

### Database Connection Parsing

```python
# Parse entire database
connection_string = "postgresql://user:pass@localhost:5432/mydb"
entities = parser.parse_database(connection_string, schemas=['public'])

# Parse specific schemas
entities = parser.parse_database(connection_string, schemas=['crm', 'sales'])
```

### File-based Parsing

```python
# Parse DDL from file
entities = parser.parse_ddl_file("schema.sql")
```

## Pattern Detection

The parser automatically detects SpecQL patterns with confidence scoring:

### Trinity Pattern (40% weight)
- `pk_*` field (INTEGER PRIMARY KEY)
- `id` field (UUID)
- `identifier` field (TEXT)

### Audit Fields (30% weight)
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)
- `deleted_at` (TIMESTAMPTZ, nullable)

### Deduplication Pattern (15% weight)
- `dedup_key` (TEXT)
- `dedup_hash` (TEXT)
- `is_unique` (BOOLEAN)

### Hierarchical Pattern (10% weight)
- `fk_parent`, `parent_id`, or `fk_{entity}_parent` fields

### Soft Delete Pattern (5% weight)
- `deleted_at` field presence

## Type Mapping

| PostgreSQL Type | SpecQL FieldType | Notes |
|-----------------|------------------|-------|
| INTEGER, INT, BIGINT | INTEGER | All integer variants |
| TEXT, VARCHAR, CHAR | TEXT | All text types |
| BOOLEAN, BOOL | BOOLEAN | Boolean values |
| TIMESTAMP, TIMESTAMPTZ | DATETIME | Date/time with time zone |
| DATE | TEXT | Mapped to TEXT for now |
| UUID | TEXT | Mapped to TEXT for now |
| JSON, JSONB | TEXT | Mapped to TEXT for now |
| Arrays | LIST | PostgreSQL arrays |
| Foreign keys | REFERENCE | Detected by `fk_*` or `*_id` patterns |

## Configuration

### Confidence Threshold

Control which entities are included based on pattern detection confidence:

```python
# Only include entities with 70%+ confidence (default)
parser = PLpgSQLParser(confidence_threshold=0.7)

# Include all entities regardless of patterns
parser = PLpgSQLParser(confidence_threshold=0.0)
```

### Function Parsing

Enable or disable PL/pgSQL function parsing:

```python
# Parse functions as actions (default: True)
entities = parser.parse_database(connection_string, include_functions=True)
```

## Output Format

The parser returns `UniversalEntity` objects with the following structure:

```python
@dataclass
class UniversalEntity:
    name: str              # Entity name (e.g., "Contact")
    schema: str           # Database schema (e.g., "crm")
    fields: List[UniversalField]  # Business fields only
    actions: List[UniversalAction]  # PL/pgSQL functions as actions
    is_multi_tenant: bool = True
    description: Optional[str] = None
```

### Field Structure

```python
@dataclass
class UniversalField:
    name: str
    type: FieldType        # TEXT, INTEGER, BOOLEAN, etc.
    required: bool         # NOT NULL constraint
    unique: bool = False
    default: Any = None
    references: Optional[str] = None  # For REFERENCE types
```

## Filtering Logic

The parser automatically filters out SpecQL auto-generated fields:

- **Trinity fields**: `pk_*`, `id`, `identifier`
- **Audit fields**: `created_at`, `updated_at`, `deleted_at`
- **Deduplication fields**: `dedup_key`, `dedup_hash`, `is_unique`

Only business fields are included in the final entity.

## Error Handling

The parser provides robust error handling:

- Invalid DDL syntax → ValueError with details
- Database connection issues → psycopg exceptions
- File not found → FileNotFoundError
- Unsupported PostgreSQL features → Warning logged, parsing continues

## Performance Considerations

- **DDL parsing**: Fast, regex-based parsing
- **Database parsing**: Network-bound, scales with database size
- **Pattern detection**: Computed once per entity
- **Memory usage**: Proportional to number of tables and columns

### Performance Benchmarks

Comprehensive performance benchmarks are included:

```bash
# Run all performance tests
uv run pytest tests/performance/test_plpgsql_parser_performance.py -v

# Run with benchmark output
uv run pytest tests/performance/test_plpgsql_parser_performance.py --benchmark-only
```

**Typical Performance Results:**
- Small DDL (5 tables): ~1.3ms
- Medium DDL (20 tables): ~7.5ms
- Large DDL (50 tables): ~18.7ms
- Small database parsing: ~89.9ms
- Medium database parsing: ~191.7ms
- Function parsing: ~164.2ms
- Confidence filtering: ~4.6ms
- Memory usage (100 tables): <100MB

## Testing

Comprehensive test suite included:

- **Unit tests**: 21 tests covering all components
- **Integration tests**: 5 tests for end-to-end functionality
- **Coverage**: 65%+ code coverage
- **Database tests**: Real PostgreSQL integration tests

Run tests with:
```bash
# Unit tests
uv run pytest tests/unit/parsers/plpgsql/

# Integration tests
uv run pytest tests/integration/plpgsql/

# With coverage
uv run pytest --cov=src/parsers/plpgsql --cov-report=html
```

## Limitations

### Current Limitations
- PL/pgSQL function parsing is basic (framework in place)
- Complex PostgreSQL types (composite, enum) not fully supported
- View and trigger parsing not implemented
- Some PostgreSQL-specific syntax may not be handled

### Future Enhancements
- Complete PL/pgSQL function parsing
- Composite type support
- View and trigger reverse engineering
- Advanced pattern detection
- Performance optimizations

## Examples

### Complete Example

```python
from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser

# Initialize parser
parser = PLpgSQLParser(confidence_threshold=0.8)

# Parse complex schema
ddl = """
CREATE SCHEMA crm;

CREATE TABLE crm.tb_contact (
    pk_contact SERIAL PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    fk_company INTEGER REFERENCES crm.tb_company(pk_company),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE crm.tb_company (
    pk_company SERIAL PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT,
    name TEXT NOT NULL,
    website TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

# Parse entities
entities = parser.parse_ddl_string(ddl)

# Output results
for entity in entities:
    print(f"Entity: {entity.name}")
    print(f"  Schema: {entity.schema}")
    print(f"  Fields: {[f.name for f in entity.fields]}")
    print(f"  Actions: {len(entity.actions)}")
    print()
```

Output:
```
Entity: Contact
  Schema: crm
  Fields: ['email', 'first_name', 'last_name', 'phone', 'fk_company']
  Actions: 0

Entity: Company
  Schema: crm
  Fields: ['name', 'website']
  Actions: 0
```

## Integration with SpecQL

The PL/pgSQL Parser integrates seamlessly with the broader SpecQL ecosystem:

1. **Reverse Engineering**: Convert existing PostgreSQL databases to SpecQL YAML
2. **Bidirectional Support**: Enable round-trip development (DB → SpecQL → DB)
3. **Pattern Recognition**: Automatically detect and preserve SpecQL conventions
4. **Multi-language**: Foundation for consistent parsing across all supported languages

## Contributing

When extending the parser:

1. **Add unit tests** for new functionality
2. **Update integration tests** for end-to-end validation
3. **Maintain backward compatibility** with existing APIs
4. **Document new features** in this guide
5. **Follow existing patterns** for consistency

## Troubleshooting

### Common Issues

**Low confidence entities filtered out:**
- Reduce `confidence_threshold` or add missing SpecQL patterns

**Database connection failures:**
- Verify connection string format
- Check PostgreSQL server status
- Ensure user has proper permissions

**DDL parsing errors:**
- Validate DDL syntax
- Check for unsupported PostgreSQL features
- Review error messages for specific issues

**Import errors:**
- Ensure all dependencies are installed
- Check Python path configuration
- Verify package structure