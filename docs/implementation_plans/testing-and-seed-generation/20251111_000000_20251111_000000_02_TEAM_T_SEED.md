# Team T-Seed: Seed Data Generation with UUID Encoding

**Status**: Planning Phase
**Timeline**: Week 3 (5 days)
**Priority**: High - Enables integration testing
**Team Size**: 1-2 developers
**Dependencies**: Team T-Meta complete

---

## 🎯 Mission

**Generate realistic, traceable seed data for SpecQL entities using UUID encoding and group leader pattern.**

Seed data must be:
- **Realistic**: Uses Faker for human-readable values
- **Traceable**: UUIDs encode entity/scenario/instance
- **Consistent**: Group leaders ensure related fields match
- **Repeatable**: Same input → same output (deterministic)

---

## 📋 Responsibilities

### Core
1. **UUID Generator** - Encode entity/test-type/scenario/instance in UUIDs
2. **Field Value Generator** - Generate values based on type (random, FK, group leader)
3. **Entity Seed Generator** - Complete entity record generation
4. **SQL File Generator** - Output INSERT statements

### Integration
- Consume: Team T-Meta's metadata (entity config, field generators)
- Provide: Seed SQL files for Team T-Test, manual testing
- Coordinate: Team B for table codes, Team E for CLI

---

## 🏗️ Architecture

```
Test Metadata (from Team T-Meta)
    ↓
UUID Generator → Encoded UUIDs
    ↓
Field Value Generators
    ├─ Random Generator (Faker)
    ├─ FK Resolver (query existing records)
    ├─ Group Leader (atomic multi-field)
    └─ Fixed/Sequence
    ↓
Entity Seed Generator
    ↓
SQL INSERT Statements
    ↓
Output: seed/contact_scenario_0.sql
```

---

## 🧬 Component 1: UUID Generator

**File**: `src/testing/seed/uuid_generator.py`

### UUID Encoding Pattern

```
EEEEETTF-FFFF-0SSS-TTTT-00000000IIII

Parts:
- EEEEEE (6): Entity code (table_code from metadata)
- TT (2): Test type (21=seed, 22=mutation, 23=query)
- F (1): Function number last digit (or 0 for seed)
- FFFF (4): Full function number (or 0000 for seed)
- 0 (1): Reserved
- SSS (3): Scenario code high 3 digits
- TTTT (4): Scenario code low + test case
- 000000000000IIII (12): Instance number
```

### Implementation

```python
# src/testing/seed/uuid_generator.py

from uuid import UUID
from dataclasses import dataclass
from typing import Optional

@dataclass
class UUIDComponents:
    """Decoded UUID components"""
    entity_code: str        # "012321"
    test_type: str          # "21"
    function_num: str       # "0000"
    scenario: int           # 1000
    test_case: int          # 0
    instance: int           # 1

    def __str__(self) -> str:
        return (
            f"Entity: {self.entity_code}, "
            f"Type: {self.test_type}, "
            f"Function: {self.function_num}, "
            f"Scenario: {self.scenario}, "
            f"Test: {self.test_case}, "
            f"Instance: {self.instance}"
        )

class SpecQLUUIDGenerator:
    """
    Generate encoded UUIDs for SpecQL test data

    Pattern: EEEEETTF-FFFF-0SSS-TTTT-00000000IIII

    Example:
        gen = SpecQLUUIDGenerator.for_entity("Contact", entity_code="012321")
        uuid = gen.generate(scenario=1000, instance=1)
        # Result: "01232121-0000-0001-0001-000000000001"
    """

    # Test type codes
    TEST_TYPES = {
        "general_seed": "21",
        "mutation_test": "22",
        "query_test": "23",
        "staging": "00"
    }

    def __init__(
        self,
        entity_name: str,
        entity_code: str,  # From metadata: base_uuid_prefix
        test_type: str = "general_seed",
        function_num: Optional[int] = None
    ):
        self.entity_name = entity_name
        self.entity_code = entity_code.zfill(6)  # Ensure 6 digits
        self.test_type_code = self.TEST_TYPES[test_type]
        self.function_num = function_num

    @classmethod
    def from_metadata(
        cls,
        entity_config: dict,
        test_type: str = "general_seed"
    ) -> 'SpecQLUUIDGenerator':
        """Create from test metadata entity config"""
        return cls(
            entity_name=entity_config['entity_name'],
            entity_code=entity_config['base_uuid_prefix'],
            test_type=test_type
        )

    def generate(
        self,
        scenario: int = 0,
        instance: int = 1,
        test_case: int = 0
    ) -> UUID:
        """
        Generate encoded UUID

        Args:
            scenario: Scenario code (0=default, 1000=dedup, 2000=alt, etc.)
            instance: Instance number (sequential: 1, 2, 3...)
            test_case: Test case number (for multiple tests per scenario)

        Returns:
            UUID with encoded components

        Example:
            >>> gen = SpecQLUUIDGenerator("Contact", "012321")
            >>> str(gen.generate(scenario=1000, instance=5))
            '01232121-0000-0001-0005-000000000005'
        """
        # Part 1: EEEEETTF (8 hex chars)
        function_digit = "0"
        if self.function_num:
            function_digit = str(self.function_num)[-1]

        part1 = f"{self.entity_code}{self.test_type_code}{function_digit}"

        # Part 2: FFFF (4 hex chars)
        if self.function_num:
            func_str = str(self.function_num).zfill(4)[-4:]
        else:
            func_str = "0000"
        part2 = func_str

        # Part 3: 0SSS (4 hex chars) - Reserved + scenario high digit
        scenario_str = str(scenario).zfill(4)
        part3 = f"0{scenario_str[0:3]}"

        # Part 4: TTTT (4 hex chars) - Scenario low + test case
        part4 = f"{scenario_str[3]}{str(test_case).zfill(3)}"

        # Part 5: 00000000IIII (12 hex chars)
        part5 = str(instance).zfill(12)

        uuid_str = f"{part1}-{part2}-{part3}-{part4}-{part5}"
        return UUID(uuid_str)

    def generate_batch(
        self,
        count: int,
        scenario: int = 0,
        start_instance: int = 1
    ) -> list[UUID]:
        """Generate batch of UUIDs with sequential instances"""
        return [
            self.generate(scenario=scenario, instance=start_instance + i)
            for i in range(count)
        ]

    @staticmethod
    def decode(uuid: UUID) -> UUIDComponents:
        """
        Decode UUID into components

        Example:
            >>> components = SpecQLUUIDGenerator.decode(
            ...     UUID("01232122-3201-0001-0001-000000000001")
            ... )
            >>> components.entity_code
            '012321'
            >>> components.scenario
            1000
        """
        s = str(uuid).replace('-', '')

        return UUIDComponents(
            entity_code=s[0:6],
            test_type=s[6:8],
            function_num=s[9:13],
            scenario=int(s[14:17] + s[18:21]),
            test_case=int(s[21:24]),
            instance=int(s[24:36])
        )
```

### Tests

```python
# tests/unit/testing/test_uuid_generator.py

def test_generate_basic_uuid():
    gen = SpecQLUUIDGenerator("Contact", "012321")
    uuid = gen.generate(scenario=0, instance=1)

    assert str(uuid) == "01232121-0000-0000-0000-000000000001"

def test_generate_scenario_1000():
    gen = SpecQLUUIDGenerator("Contact", "012321")
    uuid = gen.generate(scenario=1000, instance=1)

    # Scenario 1000 → 0001-0001
    assert str(uuid) == "01232121-0000-0001-0001-000000000001"

def test_decode_uuid():
    uuid = UUID("01232122-3201-0001-0005-000000000042")
    components = SpecQLUUIDGenerator.decode(uuid)

    assert components.entity_code == "012321"
    assert components.test_type == "22"
    assert components.function_num == "3201"
    assert components.scenario == 1000
    assert components.test_case == 5
    assert components.instance == 42

def test_generate_batch():
    gen = SpecQLUUIDGenerator("Contact", "012321")
    uuids = gen.generate_batch(count=3, scenario=2000)

    assert len(uuids) == 3
    assert uuids[0] == UUID("01232121-0000-0002-0001-000000000001")
    assert uuids[1] == UUID("01232121-0000-0002-0002-000000000002")
    assert uuids[2] == UUID("01232121-0000-0002-0003-000000000003")
```

---

## 🌱 Component 2: Field Value Generators

**File**: `src/testing/seed/field_generators.py`

### Random Value Generator (with Faker)

```python
# src/testing/seed/field_generators.py

from faker import Faker
import random
from typing import Any, Dict, Optional

class FieldValueGenerator:
    """Generate field values based on type and metadata"""

    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: Random seed for deterministic generation
        """
        self.faker = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    def generate(
        self,
        field_mapping: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Any:
        """
        Generate value for field based on mapping

        Args:
            field_mapping: From test_metadata.tb_field_generator_mapping
            context: Previously generated field values (for dependencies)

        Returns:
            Generated value (type depends on field)
        """
        generator_type = field_mapping['generator_type']

        if generator_type == 'random':
            return self._generate_random(field_mapping)
        elif generator_type == 'fixed':
            return field_mapping['generator_params']['fixed_value']
        elif generator_type == 'sequence':
            return self._generate_sequence(field_mapping, context)
        else:
            raise ValueError(f"Unsupported generator type: {generator_type}")

    def _generate_random(self, mapping: Dict[str, Any]) -> Any:
        """Generate random value based on field type"""
        field_type = mapping['field_type']

        # Use example values if provided
        if mapping.get('example_values'):
            return random.choice(mapping['example_values'])

        # Rich scalar types
        if field_type == 'email':
            return self.faker.email()

        elif field_type == 'phoneNumber':
            return self.faker.phone_number()

        elif field_type == 'url':
            return self.faker.url()

        elif field_type == 'money':
            return round(random.uniform(10, 10000), 2)

        elif field_type == 'percentage':
            return round(random.uniform(0, 100), 2)

        elif field_type == 'ipAddress':
            return self.faker.ipv4()

        elif field_type == 'macAddress':
            return self.faker.mac_address()

        # Basic types
        elif field_type == 'text':
            return self.faker.sentence(nb_words=3).rstrip('.')

        elif field_type == 'integer':
            dist = mapping.get('seed_distribution', {})
            min_val = dist.get('min', 1)
            max_val = dist.get('max', 1000)
            return random.randint(min_val, max_val)

        elif field_type == 'boolean':
            return random.choice([True, False])

        elif field_type.startswith('enum('):
            # Parse: "enum(lead, qualified, customer)" → ["lead", "qualified", "customer"]
            if mapping.get('enum_values'):
                values = mapping['enum_values']
            else:
                values = field_type[5:-1].split(',')
                values = [v.strip() for v in values]
            return random.choice(values)

        elif field_type == 'date':
            return self.faker.date_between(start_date='-1y', end_date='today')

        elif field_type == 'timestamptz':
            return self.faker.date_time_between(start_date='-1y', end_date='now')

        else:
            # Fallback
            return None

    def _generate_sequence(self, mapping: Dict, context: Dict) -> Any:
        """Generate sequential value"""
        params = mapping.get('generator_params', {})
        start = params.get('start', 1)
        step = params.get('step', 1)
        instance_num = context.get('instance_num', 1)

        return start + (instance_num - 1) * step
```

### Tests

```python
# tests/unit/testing/test_field_generators.py

def test_generate_email():
    gen = FieldValueGenerator(seed=42)  # Deterministic
    mapping = {'field_type': 'email', 'generator_type': 'random'}

    email = gen.generate(mapping)
    assert '@' in email
    assert '.' in email

def test_generate_enum():
    gen = FieldValueGenerator(seed=42)
    mapping = {
        'field_type': 'enum(lead, qualified, customer)',
        'generator_type': 'random'
    }

    status = gen.generate(mapping)
    assert status in ['lead', 'qualified', 'customer']

def test_generate_from_examples():
    gen = FieldValueGenerator(seed=42)
    mapping = {
        'field_type': 'text',
        'generator_type': 'random',
        'example_values': ['red', 'green', 'blue']
    }

    color = gen.generate(mapping)
    assert color in ['red', 'green', 'blue']
```

---

## 🔗 Component 3: FK Resolver & Group Leader

**File**: `src/testing/seed/fk_resolver.py`

```python
# src/testing/seed/fk_resolver.py

from typing import Any, Dict, List, Optional
import psycopg

class ForeignKeyResolver:
    """Resolve foreign key values by querying database"""

    def __init__(self, db_connection: psycopg.Connection):
        self.db = db_connection

    def resolve(
        self,
        field_mapping: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[int]:
        """
        Resolve FK value by querying target table

        Returns:
            INTEGER pk value from target table
        """
        # Check dependencies satisfied
        dependencies = field_mapping.get('fk_dependencies', [])
        for dep in dependencies:
            if dep not in context:
                raise ValueError(f"FK dependency not satisfied: {dep}")

        # Use custom query if provided
        if field_mapping.get('fk_resolution_query'):
            query = field_mapping['fk_resolution_query']
            # Replace placeholders
            for key, value in context.items():
                if isinstance(value, str):
                    query = query.replace(f"${key}", f"'{value}'")
                else:
                    query = query.replace(f"${key}", str(value))
        else:
            # Default: random selection from target table
            query = self._build_default_query(field_mapping, context)

        result = self.db.execute(query).fetchone()
        return result[0] if result else None

    def _build_default_query(self, mapping: Dict, context: Dict) -> str:
        """Build default FK resolution query"""
        schema = mapping['fk_target_schema']
        table = mapping['fk_target_table']
        pk_field = mapping['fk_target_pk_field']

        query = f"SELECT {pk_field} FROM {schema}.{table} WHERE deleted_at IS NULL"

        # Add tenant filter if tenant-scoped
        if 'tenant_id' in context:
            query += f" AND tenant_id = '{context['tenant_id']}'"

        # Add custom filter conditions
        if mapping.get('fk_filter_conditions'):
            query += f" AND {mapping['fk_filter_conditions']}"

        query += " ORDER BY RANDOM() LIMIT 1"

        return query


class GroupLeaderExecutor:
    """Execute group leader queries to get multiple related field values"""

    def __init__(self, db_connection: psycopg.Connection):
        self.db = db_connection

    def execute(
        self,
        leader_mapping: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute group leader query, return all dependent field values

        Returns:
            Dict mapping field names to values
            Example: {'country_code': 'FR', 'postal_code': '75001', 'city_code': 'PAR'}
        """
        query = leader_mapping['generator_params']['leader_query']
        dependent_fields = leader_mapping['group_dependency_fields']

        result = self.db.execute(query).fetchone()

        if not result:
            raise ValueError(f"Group leader query returned no results: {query}")

        # Map result columns to dependent field names
        return dict(zip(dependent_fields, result))
```

---

## 🏭 Component 4: Entity Seed Generator

**File**: `src/testing/seed/seed_generator.py`

```python
# src/testing/seed/seed_generator.py

from typing import Dict, List, Any
from .uuid_generator import SpecQLUUIDGenerator
from .field_generators import FieldValueGenerator
from .fk_resolver import ForeignKeyResolver, GroupLeaderExecutor

class EntitySeedGenerator:
    """Generate complete entity records with all fields"""

    def __init__(
        self,
        entity_config: Dict[str, Any],
        field_mappings: List[Dict[str, Any]],
        db_connection=None,
        seed: int = None
    ):
        self.config = entity_config
        self.field_mappings = sorted(field_mappings, key=lambda x: x['priority_order'])

        self.uuid_gen = SpecQLUUIDGenerator.from_metadata(entity_config)
        self.field_gen = FieldValueGenerator(seed=seed)

        if db_connection:
            self.fk_resolver = ForeignKeyResolver(db_connection)
            self.group_leader = GroupLeaderExecutor(db_connection)
        else:
            self.fk_resolver = None
            self.group_leader = None

    def generate(
        self,
        scenario: int = 0,
        instance: int = 1,
        overrides: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate complete entity record

        Returns:
            Dict with all field values
        """
        entity_data = {}
        context = {'instance_num': instance}

        # Generate UUID first
        entity_data['id'] = self.uuid_gen.generate(scenario=scenario, instance=instance)
        context['id'] = entity_data['id']

        # Add tenant context
        if self.config['is_tenant_scoped']:
            entity_data['tenant_id'] = self.config['default_tenant_id']
            context['tenant_id'] = entity_data['tenant_id']

        # Process fields in dependency order
        for mapping in self.field_mappings:
            field_name = mapping['field_name']

            # Skip if overridden
            if overrides and field_name in overrides:
                entity_data[field_name] = overrides[field_name]
                context[field_name] = overrides[field_name]
                continue

            # Skip group dependents (handled by leader)
            if mapping['generator_type'] == 'group_dependent':
                continue

            # Generate value
            value = self._generate_field_value(mapping, context)

            # Group leader returns multiple values
            if isinstance(value, dict):
                entity_data.update(value)
                context.update(value)
            else:
                entity_data[field_name] = value
                context[field_name] = value

        return entity_data

    def _generate_field_value(self, mapping: Dict, context: Dict) -> Any:
        """Generate value for single field"""

        gen_type = mapping['generator_type']

        if gen_type in ('random', 'fixed', 'sequence'):
            return self.field_gen.generate(mapping, context)

        elif gen_type == 'fk_resolve':
            if not self.fk_resolver:
                raise ValueError("FK resolution requires database connection")
            return self.fk_resolver.resolve(mapping, context)

        elif gen_type == 'group_leader':
            if not self.group_leader:
                raise ValueError("Group leader requires database connection")
            return self.group_leader.execute(mapping, context)

        else:
            raise ValueError(f"Unknown generator type: {gen_type}")

    def generate_batch(
        self,
        count: int,
        scenario: int = 0,
        overrides: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Generate batch of entity records"""
        return [
            self.generate(scenario=scenario, instance=i+1, overrides=overrides)
            for i in range(count)
        ]
```

---

## 📄 Component 5: SQL File Generator

**File**: `src/testing/seed/sql_generator.py`

```python
# src/testing/seed/sql_generator.py

from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID

class SeedSQLGenerator:
    """Generate SQL INSERT statements from entity data"""

    def __init__(self, entity_config: Dict[str, Any]):
        self.config = entity_config
        self.schema = entity_config['schema_name']
        self.table = entity_config['table_name']

    def generate_insert(self, entity_data: Dict[str, Any]) -> str:
        """Generate single INSERT statement"""
        columns = []
        values = []

        for field, value in entity_data.items():
            columns.append(field)
            values.append(self._format_value(value))

        cols_str = ', '.join(columns)
        vals_str = ', '.join(values)

        return f"INSERT INTO {self.schema}.{self.table} ({cols_str}) VALUES ({vals_str});"

    def generate_file(
        self,
        entities: List[Dict[str, Any]],
        scenario: int = 0,
        description: str = None
    ) -> str:
        """Generate complete SQL file with multiple INSERTs"""
        lines = [
            f"-- Seed data for {self.config['entity_name']}",
            f"-- Schema: {self.schema}",
            f"-- Scenario: {scenario} ({description or 'default'})",
            f"-- Generated: {datetime.now().isoformat()}",
            f"-- Record count: {len(entities)}",
            "",
        ]

        for entity_data in entities:
            lines.append(self.generate_insert(entity_data))

        lines.append("")  # Trailing newline

        return '\n'.join(lines)

    def _format_value(self, value: Any) -> str:
        """Format Python value as SQL literal"""
        if value is None:
            return "NULL"
        elif isinstance(value, UUID):
            return f"'{value}'"
        elif isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime):
            return f"'{value.isoformat()}'"
        else:
            return f"'{value}'"
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/unit/testing/

test_uuid_generator.py              # UUID encoding/decoding
test_field_generators.py            # Random value generation
test_seed_generator.py              # Entity generation (no DB)
test_sql_generator.py               # SQL formatting
```

### Integration Tests
```python
# tests/integration/testing/

test_fk_resolution.py               # FK resolution with real DB
test_group_leader.py                # Group leader queries
test_full_seed_generation.py        # End-to-end Contact seed
```

---

## 📊 Success Criteria

### Week 3 Completion
- ✅ UUID generator with encode/decode
- ✅ Field value generators for all 23 scalar types
- ✅ FK resolver querying database
- ✅ Group leader pattern working
- ✅ EntitySeedGenerator producing valid records
- ✅ SQL file generator outputting valid INSERT statements
- ✅ Generate 100 Contact records in < 1 second
- ✅ 20+ unit tests passing
- ✅ 5+ integration tests passing

---

## 📝 Example Output

```sql
-- Seed data for Contact
-- Schema: crm
-- Scenario: 0 (default seed data)
-- Generated: 2025-11-08T14:30:00
-- Record count: 10

INSERT INTO crm.tb_contact (id, tenant_id, email, first_name, last_name, fk_company, status, country_code, postal_code, city_code) VALUES ('01232121-0000-0000-0001-000000000001', '22222222-2222-2222-2222-222222222222', 'alice.smith@example.com', 'Alice', 'Smith', 15, 'lead', 'FR', '75001', 'PAR');
INSERT INTO crm.tb_contact (id, tenant_id, email, first_name, last_name, fk_company, status, country_code, postal_code, city_code) VALUES ('01232121-0000-0000-0002-000000000002', '22222222-2222-2222-2222-222222222222', 'bob.jones@example.com', 'Bob', 'Jones', 23, 'qualified', 'US', '10001', 'NYC');
-- ... 8 more records
```

---

**Next**: [Team T-Test: Test Suite Generation](03_TEAM_T_TEST.md)
