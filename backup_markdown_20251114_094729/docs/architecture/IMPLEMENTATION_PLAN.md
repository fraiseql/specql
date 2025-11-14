# Implementation Plan: Numbering, Group Leader, and FraiseQL Integration

## Overview

This plan integrates three systems:
1. Materialized numbering system for hierarchical codes
2. Group leader pattern for data coherence
3. FraiseQL integration for GraphQL API generation

## Timeline

- 4 weeks total
- 4 development phases
- ~120 hours effort

---

## Critical Success Factors

### Pre-Flight Checklist
- [ ] Team approval obtained
- [ ] Git repository backed up
- [ ] Development environment ready (Python 3.8+, PostgreSQL 14+)
- [ ] Test database instance available
- [ ] CI/CD pipeline access confirmed

### Core Principles
1. **Test-Driven**: Write failing tests → Minimal implementation → Refactor → QA
2. **Incremental**: Each phase delivers working features
3. **Reversible**: Can rollback to previous phase at any time
4. **Validated**: Every phase ends with working system

---

## PHASE 1: Numbering System Foundation (Week 1)

**Objective**: Implement hierarchical numbering system with manifest generation
**Duration**: 30 hours
**Complexity**: Complex - Phased TDD

### Phase 1 Overview

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: YAML with table_code                                 │
│   organization:                                             │
│     table_code: "013211"                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: Numbered directory structure + manifest.yaml       │
│   01_write_side/013_catalog/0132_manufacturer/...          │
│   manifest.yaml (with execution order)                     │
└─────────────────────────────────────────────────────────────┘
```

---

### Iteration 1.1: NumberingParser (TDD Cycle)

#### 🔴 RED Phase - Write Failing Test
**Time**: 1 hour

```python
# tests/test_numbering_parser.py
import pytest
from src.numbering_parser import NumberingParser

def test_parse_table_code_6_digit():
    """Test parsing 6-digit table code into components"""
    parser = NumberingParser()
    result = parser.parse_table_code("013211")

    assert result == {
        'schema_layer': '01',      # write_side
        'domain_code': '3',        # catalog
        'subdomain_code': '2',     # manufacturer subdomain
        'entity_sequence': '1',    # manufacturer entity
        'file_sequence': '1',      # first file
        'full_domain': '013',      # schema_layer + domain
        'full_group': '0132',      # + subdomain_code
        'full_entity': '01321'     # + entity_sequence
    }

def test_parse_invalid_code():
    """Test error handling for invalid codes"""
    parser = NumberingParser()

    with pytest.raises(ValueError, match="Invalid table_code"):
        parser.parse_table_code("12345")  # 5 digits

    with pytest.raises(ValueError, match="Invalid table_code"):
        parser.parse_table_code("ABC123")  # Non-numeric

def test_generate_directory_path():
    """Test directory path generation from table code"""
    parser = NumberingParser()
    path = parser.generate_directory_path("013211", "manufacturer")

    expected = "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer"
    assert path == expected

def test_generate_file_path():
    """Test file path generation"""
    parser = NumberingParser()
    path = parser.generate_file_path(
        table_code="013211",
        entity_name="manufacturer",
        file_type="table"
    )

    expected = "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql"
    assert path == expected
```

**Run test** (expect failures):
```bash
uv run pytest tests/test_numbering_parser.py -v
# Expected: FAILED - NumberingParser module not found
```

#### 🟢 GREEN Phase - Minimal Implementation
**Time**: 2 hours

```python
# src/numbering_parser.py
"""
Numbering System Parser
Parses 6-digit table codes into hierarchical components
"""
from typing import Dict
import re

class NumberingParser:
    """Parse and validate materialized numbering codes"""

    LAYER_NAMES = {
        '01': 'write_side',
        '02': 'query_side',
        '03': 'functions',
        '09': 'testfoundry'
    }

    def parse_table_code(self, table_code: str) -> Dict[str, str]:
        """
        Parse 6-digit table code into components

        Format: LLDDGEF
        L = Schema Layer (01, 02, 03, 09)
        D = Domain Code (0-9)
        G = Entity Group (0-9)
        E = Entity Code (0-9)
        F = File Sequence (0-9)

        Example: 013211
        - 01 = write_side
        - 3 = catalog domain
        - 2 = manufacturer group
        - 1 = manufacturer entity
        - 1 = first file
        """
        if not table_code:
            raise ValueError("table_code is required")

        if not re.match(r'^\d{6}$', table_code):
            raise ValueError(f"Invalid table_code: {table_code}. Must be 6 digits.")

        schema_layer = table_code[0:2]
        domain_code = table_code[2]
        subdomain_code = table_code[3]
        entity_sequence = table_code[4]
        file_sequence = table_code[5]

        if schema_layer not in self.LAYER_NAMES:
            raise ValueError(f"Invalid schema layer: {schema_layer}. Must be 01, 02, 03, or 09")

        return {
            'schema_layer': schema_layer,
            'domain_code': domain_code,
            'subdomain_code': subdomain_code,
            'entity_sequence': entity_sequence,
            'file_sequence': file_sequence,
            'full_domain': table_code[0:3],      # 013
            'full_group': table_code[0:4],        # 0132
            'full_entity': table_code[0:5]        # 01321
        }

    def generate_directory_path(self, table_code: str, entity_name: str) -> str:
        """Generate directory path from table code"""
        parsed = self.parse_table_code(table_code)

        layer_name = self.LAYER_NAMES[parsed['schema_layer']]

        path_parts = [
            f"{parsed['schema_layer']}_{layer_name}",
            f"{parsed['full_domain']}_catalog",  # TODO: Domain name mapping
            f"{parsed['full_group']}_{entity_name}",
            f"{parsed['full_entity']}_{entity_name}"
        ]

        return '/'.join(path_parts)

    def generate_file_path(self, table_code: str, entity_name: str, file_type: str) -> str:
        """Generate full file path for entity file"""
        dir_path = self.generate_directory_path(table_code, entity_name)

        file_prefix_map = {
            'table': f'tb_{entity_name}.sql',
            'view': f'v_{entity_name}.sql',
            'function': f'fn_{entity_name}.sql'
        }

        filename = file_prefix_map.get(file_type, f'{entity_name}.sql')

        return f"{dir_path}/{table_code}_{filename}"
```

**Run test**:
```bash
uv run pytest tests/test_numbering_parser.py -v
# Expected: PASSED (all tests green)
```

#### 🔧 REFACTOR Phase - Clean Up
**Time**: 1 hour

**Improvements:**
1. Add domain name mapping (not hardcoded "catalog")
2. Extract configuration to constants
3. Add comprehensive docstrings
4. Type hints for all methods

```python
# src/numbering_parser.py (refactored)
from typing import Dict, Optional
from dataclasses import dataclass
import re

@dataclass
class TableCodeComponents:
    """Parsed components of a table code"""
    schema_layer: str
    domain_code: str
    subdomain_code: str
    entity_sequence: str
    file_sequence: str
    full_domain: str
    full_group: str
    full_entity: str
    layer_name: str

    def to_dict(self) -> Dict[str, str]:
        return {
            'schema_layer': self.schema_layer,
            'domain_code': self.domain_code,
            'subdomain_code': self.subdomain_code,
            'entity_sequence': self.entity_sequence,
            'file_sequence': self.file_sequence,
            'full_domain': self.full_domain,
            'full_group': self.full_group,
            'full_entity': self.full_entity
        }

class NumberingParser:
    """Parse and validate materialized numbering codes"""

    LAYER_NAMES = {
        '01': 'write_side',
        '02': 'query_side',
        '03': 'functions',
        '09': 'testfoundry'
    }

    # Domain code to name mapping (extend as needed)
    DOMAIN_NAMES = {
        '0': 'common',
        '1': 'i18n',
        '2': 'management',
        '3': 'catalog',
        '4': 'dimension',
        '5': 'operations'
    }

    def __init__(self, domain_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize parser with optional domain mapping

        Args:
            domain_mapping: Custom domain code to name mapping
        """
        self.domain_mapping = domain_mapping or self.DOMAIN_NAMES

    def parse_table_code(self, table_code: str) -> Dict[str, str]:
        """Parse 6-digit table code into components (backward compatible)"""
        components = self.parse_table_code_detailed(table_code)
        return components.to_dict()

    def parse_table_code_detailed(self, table_code: str) -> TableCodeComponents:
        """
        Parse 6-digit table code into structured components

        Format: LLDDGEF
        - LL = Schema Layer (01=write_side, 02=query_side, 03=functions, 09=testfoundry)
        - D = Domain Code (0-9)
        - G = Entity Group (0-9)
        - E = Entity Code (0-9)
        - F = File Sequence (0-9)

        Example: 013211
        - 01 = write_side layer
        - 3 = catalog domain
        - 2 = manufacturer group
        - 1 = manufacturer entity
        - 1 = first file in sequence

        Returns:
            TableCodeComponents with parsed values

        Raises:
            ValueError: If table_code is invalid
        """
        if not table_code:
            raise ValueError("table_code is required")

        if not re.match(r'^\d{6}$', table_code):
            raise ValueError(
                f"Invalid table_code: {table_code}. Must be exactly 6 digits."
            )

        schema_layer = table_code[0:2]

        if schema_layer not in self.LAYER_NAMES:
            raise ValueError(
                f"Invalid schema layer: {schema_layer}. "
                f"Must be one of: {', '.join(self.LAYER_NAMES.keys())}"
            )

        return TableCodeComponents(
            schema_layer=schema_layer,
            domain_code=table_code[2],
            subdomain_code=table_code[3],
            entity_sequence=table_code[4],
            file_sequence=table_code[5],
            full_domain=table_code[0:3],
            full_group=table_code[0:4],
            full_entity=table_code[0:5],
            layer_name=self.LAYER_NAMES[schema_layer]
        )

    def get_domain_name(self, domain_code: str) -> str:
        """
        Get domain name from domain code

        Args:
            domain_code: Single digit domain code

        Returns:
            Domain name (e.g., 'catalog', 'management')
        """
        return self.domain_mapping.get(domain_code, f'domain_{domain_code}')

    def generate_directory_path(
        self,
        table_code: str,
        entity_name: str,
        domain_name: Optional[str] = None
    ) -> str:
        """
        Generate directory path from table code

        Args:
            table_code: 6-digit table code
            entity_name: Entity name (e.g., 'manufacturer')
            domain_name: Optional override for domain name

        Returns:
            Directory path (e.g., '01_write_side/013_catalog/0132_manufacturer/01321_manufacturer')
        """
        components = self.parse_table_code_detailed(table_code)

        if domain_name is None:
            domain_name = self.get_domain_name(components.domain_code)

        return '/'.join([
            f"{components.schema_layer}_{components.layer_name}",
            f"{components.full_domain}_{domain_name}",
            f"{components.full_group}_{entity_name}",
            f"{components.full_entity}_{entity_name}"
        ])

    def generate_file_path(
        self,
        table_code: str,
        entity_name: str,
        file_type: str,
        domain_name: Optional[str] = None
    ) -> str:
        """
        Generate full file path for entity file

        Args:
            table_code: 6-digit table code
            entity_name: Entity name
            file_type: Type of file ('table', 'view', 'function', etc.)
            domain_name: Optional domain name override

        Returns:
            Full file path including directory and filename
        """
        dir_path = self.generate_directory_path(table_code, entity_name, domain_name)

        file_prefix_map = {
            'table': f'tb_{entity_name}.sql',
            'view': f'v_{entity_name}.sql',
            'function': f'fn_{entity_name}.sql',
            'mutation': f'fn_{entity_name}_mutation.sql',
            'test': f'test_{entity_name}.sql'
        }

        filename = file_prefix_map.get(file_type, f'{entity_name}.sql')

        return f"{dir_path}/{table_code}_{filename}"
```

**Run tests again**:
```bash
uv run pytest tests/test_numbering_parser.py -v --cov=src/numbering_parser
# Expected: PASSED with high coverage
```

#### ✅ QA Phase - Verify Quality
**Time**: 30 minutes

```bash
# Run full test suite
uv run pytest --tb=short

# Run linting
uv run ruff check src/

# Run type checking
uv run mypy src/

# Check test coverage
uv run pytest --cov=src --cov-report=html
```

**Quality Gates:**
- [ ] All tests pass
- [ ] Code coverage > 90%
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Code reviewed (self or peer)

---

### Iteration 1.2: Manifest Generator (TDD Cycle)

#### 🔴 RED Phase - Write Failing Test
**Time**: 1 hour

```python
# tests/test_manifest_generator.py
import pytest
from pathlib import Path
from src.manifest_generator import ManifestGenerator

def test_create_empty_manifest():
    """Test creating empty manifest structure"""
    generator = ManifestGenerator()
    manifest = generator.create_manifest()

    assert 'metadata' in manifest
    assert 'execution_order' in manifest
    assert 'entities' in manifest
    assert manifest['metadata']['total_entities'] == 0

def test_add_entity_to_manifest():
    """Test adding entity files to manifest"""
    generator = ManifestGenerator()

    entity_def = {
        'name': 'manufacturer',
        'schema': 'catalog',
        'organization': {
            'table_code': '013211',
            'domain_code': '013'
        }
    }

    files = [
        {
            'code': '013211',
            'path': '01_write_side/.../013211_tb_manufacturer.sql',
            'type': 'table',
            'dependencies': []
        },
        {
            'code': '013212',
            'path': '01_write_side/.../013212_fn_manufacturer_pk.sql',
            'type': 'function',
            'dependencies': ['013211']
        }
    ]

    generator.add_entity(entity_def, files)
    manifest = generator.create_manifest()

    assert manifest['metadata']['total_entities'] == 1
    assert manifest['metadata']['total_files'] == 2
    assert len(manifest['execution_order']) == 2
    assert manifest['execution_order'][0]['code'] == '013211'
    assert manifest['execution_order'][1]['code'] == '013212'

def test_execution_order_sorting():
    """Test that execution order respects dependencies"""
    generator = ManifestGenerator()

    # Add files in random order
    generator.add_file({
        'code': '013213',
        'dependencies': ['013211', '013212']
    })
    generator.add_file({
        'code': '013211',
        'dependencies': []
    })
    generator.add_file({
        'code': '013212',
        'dependencies': ['013211']
    })

    manifest = generator.create_manifest()
    order = [f['code'] for f in manifest['execution_order']]

    # Should be sorted by dependencies, then by code
    assert order == ['013211', '013212', '013213']

def test_circular_dependency_detection():
    """Test detection of circular dependencies"""
    generator = ManifestGenerator()

    generator.add_file({'code': '013211', 'dependencies': ['013212']})
    generator.add_file({'code': '013212', 'dependencies': ['013211']})

    with pytest.raises(ValueError, match="Circular dependency"):
        generator.create_manifest()

def test_export_to_yaml(tmp_path):
    """Test exporting manifest to YAML file"""
    generator = ManifestGenerator()
    generator.add_file({'code': '013211', 'dependencies': []})

    output_file = tmp_path / "manifest.yaml"
    generator.export_yaml(output_file)

    assert output_file.exists()

    # Verify content
    import yaml
    with open(output_file) as f:
        data = yaml.safe_load(f)

    assert 'metadata' in data
    assert 'execution_order' in data
```

**Run test**:
```bash
uv run pytest tests/test_manifest_generator.py -v
# Expected: FAILED - ManifestGenerator not found
```

#### 🟢 GREEN Phase - Minimal Implementation
**Time**: 3 hours

```python
# src/manifest_generator.py
"""
Manifest Generator
Creates manifest.yaml with execution order and entity metadata
"""
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from datetime import datetime
import yaml

class ManifestGenerator:
    """Generate manifest.yaml with execution order"""

    def __init__(self):
        self.entities: Dict[str, Dict] = {}
        self.files: List[Dict] = []
        self.version = "2.0.0"

    def add_entity(self, entity_def: Dict, files: List[Dict]):
        """
        Add entity to manifest

        Args:
            entity_def: Entity definition from YAML
            files: List of file metadata dictionaries
        """
        entity_name = entity_def['name']

        self.entities[entity_name] = {
            'table_code': entity_def['organization']['table_code'],
            'schema': entity_def['schema'],
            'description': entity_def.get('description', ''),
            'files': [f['path'] for f in files]
        }

        self.files.extend(files)

    def add_file(self, file_metadata: Dict):
        """Add single file to manifest"""
        self.files.append(file_metadata)

    def _topological_sort(self, files: List[Dict]) -> List[Dict]:
        """
        Sort files by dependencies using topological sort

        Raises:
            ValueError: If circular dependency detected
        """
        # Build dependency graph
        graph = {f['code']: f.get('dependencies', []) for f in files}
        file_map = {f['code']: f for f in files}

        # Detect cycles
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    raise ValueError(f"Circular dependency detected involving: {node}")

        # Topological sort (Kahn's algorithm)
        in_degree = {code: 0 for code in graph}
        for code, deps in graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        queue = [code for code, degree in in_degree.items() if degree == 0]
        sorted_codes = []

        while queue:
            # Sort queue to ensure deterministic ordering
            queue.sort()
            code = queue.pop(0)
            sorted_codes.append(code)

            for other_code, deps in graph.items():
                if code in deps:
                    in_degree[other_code] -= 1
                    if in_degree[other_code] == 0:
                        queue.append(other_code)

        # Convert codes back to file objects
        return [file_map[code] for code in sorted_codes]

    def create_manifest(self) -> Dict[str, Any]:
        """
        Create manifest dictionary

        Returns:
            Manifest dictionary ready for YAML export
        """
        # Sort files by dependencies
        if self.files:
            sorted_files = self._topological_sort(self.files)
        else:
            sorted_files = []

        return {
            'metadata': {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'generator_version': self.version,
                'total_entities': len(self.entities),
                'total_files': len(sorted_files)
            },
            'execution_order': sorted_files,
            'entities': self.entities
        }

    def export_yaml(self, output_path: Path):
        """
        Export manifest to YAML file

        Args:
            output_path: Path to output manifest.yaml
        """
        manifest = self.create_manifest()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            yaml.dump(
                manifest,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
```

**Run test**:
```bash
uv run pytest tests/test_manifest_generator.py -v
# Expected: PASSED
```

#### 🔧 REFACTOR Phase
**Time**: 1 hour

Add better error messages, extract constants, improve algorithm efficiency.

#### ✅ QA Phase
**Time**: 30 minutes

```bash
uv run pytest tests/test_manifest_generator.py -v --cov=src/manifest_generator
uv run ruff check src/
uv run mypy src/
```

---

### Iteration 1.3: Directory Structure Generator (TDD Cycle)

#### 🔴 RED Phase
**Time**: 1 hour

```python
# tests/test_directory_generator.py
import pytest
from pathlib import Path
from src.directory_generator import DirectoryGenerator

def test_create_entity_directories(tmp_path):
    """Test creating full directory structure for entity"""
    generator = DirectoryGenerator(output_dir=tmp_path)

    entity_def = {
        'name': 'manufacturer',
        'organization': {'table_code': '013211'}
    }

    paths = generator.create_entity_directories(entity_def)

    # Check all directories created
    expected_base = tmp_path / "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer"
    assert expected_base.exists()
    assert expected_base.is_dir()

    # Check README.md created
    readme = expected_base / "README.md"
    assert readme.exists()

def test_generate_entity_readme(tmp_path):
    """Test README.md generation for entity"""
    generator = DirectoryGenerator(output_dir=tmp_path)

    entity_def = {
        'name': 'manufacturer',
        'schema': 'catalog',
        'description': 'Printer manufacturers',
        'organization': {'table_code': '013211'}
    }

    readme_content = generator.generate_entity_readme(entity_def)

    assert '# 01321 - Manufacturer' in readme_content
    assert 'Table Code: 013211' in readme_content
    assert 'Schema: catalog' in readme_content
    assert 'Printer manufacturers' in readme_content

def test_create_all_layers(tmp_path):
    """Test creating directories for all schema layers"""
    generator = DirectoryGenerator(output_dir=tmp_path)

    entity_def = {
        'name': 'manufacturer',
        'organization': {'table_code': '013211'}
    }

    # Generate for multiple layers
    generator.create_layer_directories(entity_def, layers=['01', '02', '03', '09'])

    # Check all layers exist
    assert (tmp_path / "01_write_side").exists()
    assert (tmp_path / "02_query_side").exists()
    assert (tmp_path / "03_functions").exists()
    assert (tmp_path / "09_testfoundry").exists()
```

#### 🟢 GREEN Phase
**Time**: 2 hours

```python
# src/directory_generator.py
from pathlib import Path
from typing import Dict, List
from src.numbering_parser import NumberingParser

class DirectoryGenerator:
    """Generate directory structure with README files"""

    def __init__(self, output_dir: Path = Path('generated')):
        self.output_dir = Path(output_dir)
        self.parser = NumberingParser()

    def create_entity_directories(self, entity_def: Dict) -> Dict[str, Path]:
        """Create all directories for an entity"""
        table_code = entity_def['organization']['table_code']
        entity_name = entity_def['name']

        # Get domain name if specified
        domain_name = entity_def.get('organization', {}).get('domain_name')

        dir_path = self.parser.generate_directory_path(
            table_code, entity_name, domain_name
        )

        full_path = self.output_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

        # Generate README
        readme_content = self.generate_entity_readme(entity_def)
        readme_path = full_path / "README.md"
        readme_path.write_text(readme_content)

        return {
            'base': full_path,
            'readme': readme_path
        }

    def generate_entity_readme(self, entity_def: Dict) -> str:
        """Generate README.md content for entity"""
        table_code = entity_def['organization']['table_code']
        components = self.parser.parse_table_code(table_code)
        entity_name = entity_def['name']

        return f"""# {components['full_entity']} - {entity_name.title()}

**Table Code**: {table_code}
**Schema**: {entity_def.get('schema', 'N/A')}
**Layer**: {components['schema_layer']} ({self.parser.LAYER_NAMES[components['schema_layer']]})
**Domain**: {components['full_domain']}

## Description

{entity_def.get('description', 'No description provided.')}

## Files

Generated files for this entity will appear here.

## Generated

This documentation was auto-generated on {datetime.utcnow().strftime('%Y-%m-%d')}.
"""

    def create_layer_directories(self, entity_def: Dict, layers: List[str]):
        """Create directories across multiple schema layers"""
        for layer in layers:
            # Modify table_code to use this layer
            original_code = entity_def['organization']['table_code']
            layer_code = layer + original_code[2:]

            temp_def = entity_def.copy()
            temp_def['organization'] = entity_def['organization'].copy()
            temp_def['organization']['table_code'] = layer_code

            self.create_entity_directories(temp_def)
```

#### 🔧 REFACTOR Phase
**Time**: 1 hour

#### ✅ QA Phase
**Time**: 30 minutes

---

### Iteration 1.4: Integration with SQLGenerator (TDD Cycle)

#### 🔴 RED Phase
**Time**: 1 hour

Update existing tests to expect numbered output:

```python
# tests/test_sql_generator_integration.py
def test_generate_with_numbering_system(tmp_path):
    """Test SQL generation with numbering system"""
    generator = SQLGenerator(output_dir=tmp_path)

    entity_file = create_test_entity_yaml({
        'name': 'manufacturer',
        'organization': {'table_code': '013211'},
        'schema': 'catalog'
    })

    result = generator.generate_entity(entity_file)

    # Check files in numbered directories
    expected_table = (
        tmp_path / "01_write_side/013_catalog/0132_manufacturer/"
        "01321_manufacturer/013211_tb_manufacturer.sql"
    )
    assert expected_table.exists()

    # Check manifest generated
    manifest = tmp_path / "manifest.yaml"
    assert manifest.exists()
```

#### 🟢 GREEN Phase
**Time**: 3 hours

Update `scripts/dev/generate_sql.py` to use new numbering system:

```python
# src/sql_generator.py (updated)
class SQLGenerator:
    def __init__(self, templates_dir='templates', entities_dir='entities', output_dir='generated'):
        self.templates_dir = Path(templates_dir)
        self.entities_dir = Path(entities_dir)
        self.output_dir = Path(output_dir)

        # NEW: Add numbering and directory generators
        self.numbering_parser = NumberingParser()
        self.directory_generator = DirectoryGenerator(output_dir)
        self.manifest_generator = ManifestGenerator()

        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate_entity(self, entity_file):
        """Generate all SQL for a single entity with numbering"""
        entity = self.load_entity(entity_file)

        # Create numbered directory structure
        directories = self.directory_generator.create_entity_directories(entity)

        # Generate table SQL
        table_sql = self.generate_table(entity)

        # Write to numbered path
        table_code = entity['organization']['table_code']
        file_path = self.numbering_parser.generate_file_path(
            table_code,
            entity['name'],
            'table'
        )

        full_path = self.output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(table_sql)

        # Add to manifest
        self.manifest_generator.add_file({
            'code': table_code,
            'path': str(file_path),
            'entity': entity['name'],
            'type': 'table',
            'schema': entity['schema'],
            'dependencies': []
        })

        return {'table_path': full_path}

    def generate_all(self):
        """Generate SQL for all entities and create manifest"""
        entity_files = sorted(self.entities_dir.glob('*.yaml'))

        for entity_file in entity_files:
            self.generate_entity(entity_file)

        # Export manifest
        manifest_path = self.output_dir / 'manifest.yaml'
        self.manifest_generator.export_yaml(manifest_path)

        print(f"✅ Generated manifest: {manifest_path}")
```

#### 🔧 REFACTOR Phase
**Time**: 2 hours

#### ✅ QA Phase
**Time**: 1 hour

**Quality Gates:**
- [ ] All tests pass
- [ ] Numbered directories created correctly
- [ ] Manifest.yaml generated with correct execution order
- [ ] Existing POC still works
- [ ] README.md files auto-generated

---

### Phase 1 Deliverables

**Completion Checklist:**
- [ ] NumberingParser class with tests (>90% coverage)
- [ ] ManifestGenerator class with tests
- [ ] DirectoryGenerator class with tests
- [ ] SQLGenerator updated to use numbering system
- [ ] Generated output follows numbered hierarchy
- [ ] manifest.yaml auto-generated
- [ ] Entity README.md files auto-generated
- [ ] All existing POC tests still pass
- [ ] Documentation updated

**Acceptance Test:**
```bash
# Run full generation
python scripts/dev/generate_sql.py

# Verify output structure
ls -R generated/
# Should show:
#   01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql
#   manifest.yaml
#   01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/README.md

# Verify manifest
cat generated/manifest.yaml
# Should show execution_order with dependencies
```

**Exit Criteria:**
- [ ] Can generate numbered SQL from YAML
- [ ] Manifest validates and executes in order
- [ ] Team review and approval

---

## PHASE 2: Group Leader Pattern (Week 2)

**Objective**: Implement group leader pattern with trigger generation
**Duration**: 30 hours
**Complexity**: Complex - Phased TDD

### Phase 2 Overview

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: YAML with field_groups                               │
│   field_groups:                                             │
│     - group_leader: fk_company                              │
│       dependent_fields: [company_country]                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: SQL table with triggers                             │
│   - Dependent fields added to table                         │
│   - Trigger function to populate fields                     │
│   - Trigger on INSERT/UPDATE                                │
└─────────────────────────────────────────────────────────────┘
```

---

### Iteration 2.1: Group Leader Validator (TDD Cycle)

#### 🔴 RED Phase
**Time**: 1 hour

```python
# tests/test_group_leader_validator.py
def test_validate_group_leader_exists():
    """Test validation that group leader field exists"""
    validator = GroupLeaderValidator()

    entity_def = {
        'foreign_keys': {'fk_company': {...}},
        'field_groups': [
            {'group_leader': 'fk_company', 'dependent_fields': ['country']}
        ]
    }

    # Should not raise
    validator.validate(entity_def)

def test_validate_group_leader_missing():
    """Test error when group leader doesn't exist"""
    validator = GroupLeaderValidator()

    entity_def = {
        'foreign_keys': {},
        'field_groups': [
            {'group_leader': 'fk_missing', 'dependent_fields': ['country']}
        ]
    }

    with pytest.raises(ValueError, match="Group leader.*not found"):
        validator.validate(entity_def)

def test_validate_dependent_field_not_in_base_fields():
    """Test that dependent fields aren't already defined"""
    validator = GroupLeaderValidator()

    entity_def = {
        'fields': {'country': {'type': 'TEXT'}},
        'foreign_keys': {'fk_company': {...}},
        'field_groups': [
            {'group_leader': 'fk_company', 'dependent_fields': ['country']}
        ]
    }

    with pytest.raises(ValueError, match="Dependent field.*already defined"):
        validator.validate(entity_def)
```

#### 🟢 GREEN Phase
**Time**: 2 hours

```python
# src/group_leader_validator.py
class GroupLeaderValidator:
    """Validate group leader configuration in entity definitions"""

    def validate(self, entity_def: Dict) -> None:
        """
        Validate group leader configuration

        Raises:
            ValueError: If configuration is invalid
        """
        field_groups = entity_def.get('field_groups', [])

        for group in field_groups:
            self._validate_group(group, entity_def)

    def _validate_group(self, group: Dict, entity_def: Dict) -> None:
        """Validate a single field group"""
        leader = group.get('group_leader')
        dependents = group.get('dependent_fields', [])

        if not leader:
            raise ValueError("group_leader is required in field_groups")

        # Check leader exists in foreign_keys
        fks = entity_def.get('foreign_keys', {})
        if leader not in fks:
            raise ValueError(
                f"Group leader '{leader}' not found in foreign_keys. "
                f"Available: {list(fks.keys())}"
            )

        # Check dependent fields not in base fields
        base_fields = entity_def.get('fields', {})
        for dep in dependents:
            if dep in base_fields:
                raise ValueError(
                    f"Dependent field '{dep}' already defined in fields. "
                    "Dependent fields should only be in field_groups."
                )
```

#### 🔧 REFACTOR Phase
**Time**: 30 minutes

#### ✅ QA Phase
**Time**: 30 minutes

---

### Iteration 2.2: Group Leader Trigger Template (TDD Cycle)

#### 🔴 RED Phase
**Time**: 1 hour

```python
# tests/test_trigger_generation.py
def test_generate_trigger_function():
    """Test trigger function generation"""
    generator = TriggerGenerator()

    entity_def = {
        'name': 'manufacturer',
        'schema': 'catalog',
        'foreign_keys': {
            'fk_company': {
                'references': 'management.tb_organization',
                'on': 'pk_organization'
            }
        },
        'field_groups': [
            {
                'group_name': 'company_data',
                'group_leader': 'fk_company',
                'dependent_fields': ['company_country', 'company_address']
            }
        ]
    }

    sql = generator.generate_trigger_sql(entity_def)

    # Verify SQL contains key elements
    assert 'CREATE OR REPLACE FUNCTION' in sql
    assert 'fn_populate_company_data' in sql
    assert 'NEW.fk_company IS NOT NULL' in sql
    assert 'NEW.company_country :=' in sql
    assert 'CREATE TRIGGER' in sql
    assert 'BEFORE INSERT OR UPDATE' in sql
```

#### 🟢 GREEN Phase
**Time**: 3 hours

Create Jinja2 template:

```jinja2
{# templates/group_leader_triggers.sql.j2 #}
{%- if entity.field_groups %}
-- ============================================================================
-- Group Leader Triggers for {{ entity.schema }}.tb_{{ entity.name }}
-- ============================================================================
-- Auto-populate dependent fields when group leader is set
-- This ensures data coherence across related fields
-- ============================================================================

{%- for group in entity.field_groups %}

-- Group: {{ group.group_name }}
-- Leader: {{ group.group_leader }} → Dependents: {{ group.dependent_fields | join(', ') }}
-- Purpose: {{ group.description | default('Ensure data coherence') }}

CREATE OR REPLACE FUNCTION {{ entity.schema }}.fn_populate_{{ group.group_name }}()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_source_record RECORD;
BEGIN
    -- Only populate when group leader {{ group.group_leader }} is set
    IF NEW.{{ group.group_leader }} IS NOT NULL THEN

        -- Fetch dependent fields from source table
        SELECT
            {%- for dep_field in group.dependent_fields %}
            {{ dep_field }}{% if not loop.last %},{% endif %}
            {%- endfor %}
        INTO v_source_record
        FROM {{ entity.foreign_keys[group.group_leader].references }}
        WHERE {{ entity.foreign_keys[group.group_leader].on }} = NEW.{{ group.group_leader }};

        -- Populate dependent fields in NEW record
        {%- for dep_field in group.dependent_fields %}
        NEW.{{ dep_field }} := v_source_record.{{ dep_field }};
        {%- endfor %}

    ELSE
        -- If group leader is NULL, clear dependent fields
        {%- for dep_field in group.dependent_fields %}
        NEW.{{ dep_field }} := NULL;
        {%- endfor %}
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION {{ entity.schema }}.fn_populate_{{ group.group_name }}() IS
'Auto-populate dependent fields {{ group.dependent_fields | join(", ") }} when {{ group.group_leader }} is set. '
'Ensures {{ group.group_name }} data coherence.';

-- Create trigger to execute function
CREATE TRIGGER trg_populate_{{ group.group_name }}
    BEFORE INSERT OR UPDATE ON {{ entity.schema }}.tb_{{ entity.name }}
    FOR EACH ROW
    EXECUTE FUNCTION {{ entity.schema }}.fn_populate_{{ group.group_name }}();

COMMENT ON TRIGGER trg_populate_{{ group.group_name }} ON {{ entity.schema }}.tb_{{ entity.name }} IS
'Maintains coherence for {{ group.group_name }} by auto-populating dependent fields.';

{%- endfor %}
{%- endif %}
```

Python generator:

```python
# src/trigger_generator.py
class TriggerGenerator:
    """Generate group leader trigger SQL"""

    def __init__(self, templates_dir='templates'):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate_trigger_sql(self, entity_def: Dict) -> str:
        """Generate trigger SQL for all field groups"""
        template = self.env.get_template('group_leader_triggers.sql.j2')
        return template.render(entity=entity_def)
```

#### 🔧 REFACTOR Phase
**Time**: 1 hour

#### ✅ QA Phase
**Time**: 1 hour

---

### Iteration 2.3: Update Table Template (TDD Cycle)

#### 🔴 RED Phase
**Time**: 1 hour

```python
def test_table_includes_dependent_fields():
    """Test that table SQL includes dependent fields from groups"""
    generator = SQLGenerator()

    entity_def = {
        'name': 'manufacturer',
        'fields': {'identifier': {'type': 'TEXT'}},
        'field_groups': [
            {
                'group_leader': 'fk_company',
                'dependent_fields': ['company_country', 'company_address']
            }
        ]
    }

    sql = generator.generate_table(entity_def)

    # Should include dependent fields
    assert 'company_country TEXT' in sql
    assert 'company_address TEXT' in sql
    assert '-- Auto-populated by group leader' in sql
```

#### 🟢 GREEN Phase
**Time**: 2 hours

Update table template:

```jinja2
{# templates/table.sql.j2 - add section for dependent fields #}

-- Foreign Keys
{%- for fk_name, fk_def in entity.foreign_keys.items() %}
{{ fk_name }} INTEGER{% if not fk_def.nullable %} NOT NULL{% endif %},
{%- endfor %}

-- Group Leader Dependent Fields (auto-populated by triggers)
{%- if entity.field_groups %}
{%- for group in entity.field_groups %}
{%- for dep_field in group.dependent_fields %}
{{ dep_field }} TEXT,  -- Auto-populated by {{ group.group_leader }} ({{ group.group_name }})
{%- endfor %}
{%- endfor %}
{%- endif %}

-- Audit Fields
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
...
```

#### 🔧 REFACTOR Phase
**Time**: 1 hour

#### ✅ QA Phase
**Time**: 1 hour

---

### Iteration 2.4: Integration Testing (TDD Cycle)

#### 🔴 RED Phase
**Time**: 2 hours

Write integration test that:
1. Generates full table with group leaders
2. Applies SQL to test database
3. Tests trigger behavior

```python
# tests/integration/test_group_leader_integration.py
@pytest.mark.integration
def test_group_leader_trigger_behavior(test_db):
    """Test that group leader triggers work correctly"""
    # Generate SQL
    generator = SQLGenerator()
    entity_file = create_test_entity_with_groups()
    generator.generate_entity(entity_file)

    # Apply to database
    apply_sql_to_db(test_db, generated_files)

    # Test trigger
    test_db.execute("""
        INSERT INTO catalog.tb_manufacturer (identifier, fk_company)
        VALUES ('canon', 1)
    """)

    # Verify dependent fields populated
    result = test_db.query("""
        SELECT company_country, company_address
        FROM catalog.tb_manufacturer
        WHERE identifier = 'canon'
    """)

    assert result['company_country'] is not None
    assert result['company_address'] is not None
```

#### 🟢 GREEN Phase
**Time**: 4 hours

Implement full integration, fix any issues.

#### 🔧 REFACTOR Phase
**Time**: 2 hours

#### ✅ QA Phase
**Time**: 2 hours

**Quality Gates:**
- [ ] Integration tests pass
- [ ] Triggers work in real database
- [ ] Performance acceptable (< 10ms overhead per INSERT)
- [ ] Dependent fields populate correctly
- [ ] NULL handling works

---

### Phase 2 Deliverables

**Completion Checklist:**
- [ ] GroupLeaderValidator with tests
- [ ] TriggerGenerator with tests
- [ ] group_leader_triggers.sql.j2 template
- [ ] Updated table.sql.j2 template
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] Example entity with group leaders

**Acceptance Test:**
```bash
# Generate entity with group leaders
python scripts/dev/generate_sql.py

# Apply to test database
psql test_db < generated/01_write_side/.../013211_tb_manufacturer.sql

# Test trigger
psql test_db -c "INSERT INTO catalog.tb_manufacturer (identifier, fk_company) VALUES ('test', 1); SELECT company_country FROM catalog.tb_manufacturer WHERE identifier='test';"
# Should show auto-populated country
```

**Exit Criteria:**
- [ ] Group leader triggers generate correctly
- [ ] Triggers work in database
- [ ] Tests validate behavior
- [ ] Performance benchmarked
- [ ] Team review and approval

---

## PHASE 3: FraiseQL + TestFoundry Integration (Week 3)

**Objective**: Generate FraiseQL metadata and TestFoundry test suite
**Duration**: 35 hours
**Complexity**: Complex - Phased TDD

### Iteration 3.1: FraiseQL Metadata Generation
**Time**: 10 hours (RED 2h, GREEN 5h, REFACTOR 2h, QA 1h)

### Iteration 3.2: Mutation Function Templates
**Time**: 12 hours (RED 2h, GREEN 7h, REFACTOR 2h, QA 1h)

### Iteration 3.3: TestFoundry Metadata Template
**Time**: 8 hours

### Iteration 3.4: Test Generation Templates
**Time**: 5 hours

---

## PHASE 4: Polish + Documentation + Migration (Week 4)

**Objective**: Production-ready system with migration tooling
**Duration**: 25 hours

### Iteration 4.1: Health Check System
**Time**: 8 hours

### Iteration 4.2: Migration Tooling
**Time**: 10 hours

### Iteration 4.3: Documentation + Training
**Time**: 7 hours

---

## Success Metrics

### Phase 1 Success
- [ ] Generated SQL uses numbered directories
- [ ] Manifest.yaml validates execution order
- [ ] Can generate manufacturer entity in < 30 seconds

### Phase 2 Success
- [ ] Group leader triggers generate correctly
- [ ] Integration tests pass
- [ ] Trigger overhead < 10ms per operation

### Phase 3 Success
- [ ] FraiseQL discovers types automatically
- [ ] GraphQL API works without Python code
- [ ] TestFoundry tests auto-generated

### Phase 4 Success
- [ ] Can migrate existing entity to YAML in < 30 minutes
- [ ] Health checks prevent broken commits
- [ ] Team trained and productive

---

## Risk Mitigation

### Technical Risks
1. **Trigger Performance** → Benchmark early in Phase 2
2. **Manifest Drift** → Health checks in Phase 4
3. **Complex Dependencies** → Topological sort validation

### Process Risks
1. **Team Adoption** → Training and examples
2. **Migration Effort** → Tooling automation
3. **Breaking Changes** → Phased rollout

---

## Rollback Strategy

Each phase is independently reversible:
- **Phase 1**: Remove numbered directories, keep flat structure
- **Phase 2**: Drop triggers, remove field_groups from YAML
- **Phase 3**: Remove FraiseQL annotations, keep SQL
- **Phase 4**: Manual migrations continue working

**Critical**: Maintain parallel systems during Phase 1-2 transition.

---

**Ready to begin Phase 1?** 🚀
