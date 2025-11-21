# Numbering System

The Numbering System provides hierarchical organization and manifest generation for SpecQL entities using 6-digit table codes.

## Overview

Table codes follow the format: `SSDGGE`
- **SS**: Schema layer (01=write_side, 02=read_side, 03=analytics)
- **D**: Domain code (1=core, 2=management, 3=catalog, 4=tenant)
- **G**: Entity group
- **E**: Entity code
- **S**: File sequence

## Components

### NumberingParser
Parses 6-digit codes and generates directory/file paths.

```python
from src.numbering.numbering_parser import NumberingParser

parser = NumberingParser()

# Parse code into components
components = parser.parse_table_code("013211")
# Returns: {'schema_layer': '01', 'domain_code': '3', ...}

# Generate directory path
path = parser.generate_directory_path("013211", "manufacturer")
# Returns: "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer"

# Generate file path
file_path = parser.generate_file_path("013211", "manufacturer", "table")
# Returns: "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql"
```

### ManifestGenerator
Creates execution manifests with dependency resolution and topological ordering.

```python
from src.numbering.manifest_generator import ManifestGenerator

generator = ManifestGenerator()
generator.add_entity("manufacturer", "013211")
generator.add_entity("organization", "012111")
generator.add_dependency("manufacturer", "organization")  # manufacturer depends on organization

manifest = generator.generate_manifest()
# Returns ordered list of ManifestEntry objects
```

### DependencyResolver
Provides standalone topological sorting for dependency resolution.

```python
from src.numbering.dependency_resolver import DependencyResolver

resolver = DependencyResolver()
resolver.add_dependency("A", "B")  # A depends on B
resolver.add_dependency("B", "C")  # B depends on C

order = resolver.resolve(["A", "B", "C"])
# Returns: ["C", "B", "A"] - dependencies first
```

### Directory Structure
Generated directory structure follows hierarchical organization:

```
01_write_side/
├── 011_core/
│   ├── 0111_user/
│   │   └── 01111_user/
│   │       └── 011111_tb_user.sql
│   └── 0112_role/
│       └── 01121_role/
│           └── 011211_tb_role.sql
└── 013_catalog/
    └── 0132_manufacturer/
        └── 01321_manufacturer/
            ├── 013211_tb_manufacturer.sql
            ├── 013211_fn_manufacturer.sql
            └── 013211_vw_manufacturer.sql
```

## Testing

Run the numbering system tests:

```bash
make teamC-test
# or
uv run pytest tests/unit/numbering/ -v
```

## Integration

The numbering system integrates with the SpecQL parser through the `Entity.organization` field:

```yaml
entity:
  name: manufacturer
  table_code: "013211"  # Used by numbering system
```

## Files

- `numbering_parser.py` - Core parsing and path generation
- `manifest_generator.py` - Execution manifest creation
- `dependency_resolver.py` - Topological sorting utilities
- `README.md` - This documentation
