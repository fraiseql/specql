# Team T-Prop: Property-Based Testing with Hypothesis

**Status**: Planning Phase
**Timeline**: Week 5 (5 days)
**Priority**: Medium - Advanced testing
**Team Size**: 1 developer
**Dependencies**: Teams T-Meta, T-Seed, T-Test complete

---

## 🎯 Mission

**Generate property-based tests using Hypothesis to find edge cases automatically.**

Property-based testing doesn't test specific examples - it tests **properties that should always be true**, using automatically generated test cases.

### Examples of Properties
- **Idempotency**: `create(x) then create(x) → error`
- **Reversibility**: `create(x) then delete(x) → no record`
- **Invariants**: `status can only be lead|qualified|customer`
- **Relationships**: `delete(company) → cascade to contacts`

---

## 🏗️ Architecture

```
Test Metadata
    ↓
Hypothesis Strategy Generator
    ├─ Field strategies (email, phone, etc.)
    ├─ Entity strategies (full Contact)
    └─ Scenario strategies (valid/invalid)
    ↓
Property Test Generator
    ├─ Idempotency properties
    ├─ Constraint properties
    ├─ Relationship properties
    └─ State machine properties
    ↓
Output: tests/property/test_contact_properties.py
```

---

## 📦 Component 1: Hypothesis Strategies from Metadata

**File**: `src/testing/property/strategies.py`

```python
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy
from typing import Dict, Any
import string

class SpecQLStrategies:
    """Generate Hypothesis strategies from SpecQL field metadata"""

    @staticmethod
    def for_field(field_mapping: Dict[str, Any]) -> SearchStrategy:
        """Generate strategy for field based on metadata"""
        field_type = field_mapping['field_type']

        # Rich scalar types
        if field_type == 'email':
            return st.emails()

        elif field_type == 'url':
            return st.from_regex(r'https?://[a-z0-9-]+\.[a-z]{2,}(/[a-z0-9-]*)*', fullmatch=True)

        elif field_type == 'phoneNumber':
            return st.from_regex(r'\+1-[0-9]{3}-[0-9]{3}-[0-9]{4}', fullmatch=True)

        elif field_type == 'money':
            return st.decimals(
                min_value=0,
                max_value=1000000,
                places=2
            )

        elif field_type == 'percentage':
            return st.decimals(
                min_value=0,
                max_value=100,
                places=2
            )

        # Basic types
        elif field_type == 'text':
            max_len = field_mapping.get('postgres_type', '').replace('TEXT', '').replace('VARCHAR(', '').replace(')', '')
            if max_len.isdigit():
                return st.text(alphabet=string.printable, max_size=int(max_len))
            else:
                return st.text(alphabet=string.printable, max_size=255)

        elif field_type == 'integer':
            dist = field_mapping.get('seed_distribution', {})
            return st.integers(
                min_value=dist.get('min', 1),
                max_value=dist.get('max', 2**31 - 1)
            )

        elif field_type == 'boolean':
            return st.booleans()

        elif field_type.startswith('enum('):
            values = field_mapping.get('enum_values', [])
            if not values:
                # Parse from type string
                values = [v.strip() for v in field_type[5:-1].split(',')]
            return st.sampled_from(values)

        elif field_type == 'date':
            return st.dates()

        elif field_type == 'timestamptz':
            return st.datetimes()

        else:
            return st.none()

    @staticmethod
    def for_entity(
        entity_config: Dict[str, Any],
        field_mappings: list[Dict[str, Any]]
    ) -> SearchStrategy:
        """Generate strategy for complete entity"""

        # Build dictionary strategy for required fields
        required_fields = {}
        optional_fields = {}

        for field in field_mappings:
            if field['generator_type'] in ('random', 'fixed'):
                strategy = SpecQLStrategies.for_field(field)

                if field['nullable']:
                    optional_fields[field['field_name']] = strategy
                else:
                    required_fields[field['field_name']] = strategy

        return st.fixed_dictionaries(
            required_fields,
            optional=optional_fields
        )

    @staticmethod
    def invalid_for_field(field_mapping: Dict[str, Any]) -> SearchStrategy:
        """Generate INVALID values for field (for negative testing)"""
        field_type = field_mapping['field_type']

        if field_type == 'email':
            # Invalid emails
            return st.one_of(
                st.just("not-an-email"),
                st.just("@example.com"),
                st.just("user@"),
                st.text(alphabet=string.ascii_letters, min_size=1, max_size=10)
            )

        elif field_type.startswith('enum('):
            # Values NOT in enum
            valid_values = field_mapping.get('enum_values', [])
            return st.text(alphabet=string.ascii_letters).filter(lambda x: x not in valid_values)

        elif field_type == 'integer':
            # Out of range integers
            dist = field_mapping.get('seed_distribution', {})
            min_val = dist.get('min', 1)
            max_val = dist.get('max', 2**31 - 1)
            return st.one_of(
                st.integers(max_value=min_val - 1),
                st.integers(min_value=max_val + 1)
            )

        else:
            return st.none()
```

---

## 📦 Component 2: Property Test Generator

**File**: `src/testing/property/property_generator.py`

```python
class PropertyTestGenerator:
    """Generate property-based tests for entities"""

    def generate_idempotency_tests(
        self,
        entity_config: Dict[str, Any],
        field_mappings: List[Dict[str, Any]]
    ) -> str:
        """Generate idempotency property tests"""
        entity = entity_config['entity_name']

        return f'''
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from uuid import UUID

from src.testing.property.strategies import SpecQLStrategies

class Test{entity}Idempotency:
    """Property tests for {entity} idempotency"""

    @given(
        data=SpecQLStrategies.for_entity(
            {repr(entity_config)},
            {repr(field_mappings)}
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_create_duplicate_fails(self, clean_db, data):
        """Property: Creating duplicate entity should always fail"""
        tenant_id = UUID("{entity_config['default_tenant_id']}")
        user_id = UUID("{entity_config['default_user_id']}")

        with clean_db.cursor() as cur:
            # First create - should succeed
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, data)
            )
            result1 = cur.fetchone()[0]
            assert result1['status'] == 'success', f"First create failed: {{result1}}"

            # Second create with same data - should fail
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, data)
            )
            result2 = cur.fetchone()[0]
            assert result2['status'].startswith('failed:'), \\
                f"Duplicate create should fail but got: {{result2}}"
'''

    def generate_constraint_tests(
        self,
        entity_config: Dict[str, Any],
        field_mappings: List[Dict[str, Any]]
    ) -> str:
        """Generate constraint property tests"""
        entity = entity_config['entity_name']

        # Find fields with constraints
        constrained_fields = [f for f in field_mappings if f.get('validation_pattern') or f.get('check_constraint')]

        tests = []
        for field in constrained_fields:
            test = f'''
    @given(
        valid_data=SpecQLStrategies.for_entity(...),
        invalid_{field['field_name']}=SpecQLStrategies.invalid_for_field({repr(field)})
    )
    def test_{field['field_name']}_constraint(self, clean_db, valid_data, invalid_{field['field_name']}):
        """Property: Invalid {field['field_name']} should always fail"""
        valid_data['{field['field_name']}'] = invalid_{field['field_name']}

        with clean_db.cursor() as cur:
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (UUID("{entity_config['default_tenant_id']}"), UUID("{entity_config['default_user_id']}"), valid_data)
            )
            result = cur.fetchone()[0]

        assert result['status'].startswith('failed:'), \\
            f"Invalid {field['field_name']} should fail but got: {{result}}"
'''
            tests.append(test)

        return '\n\n'.join(tests)

    def generate_roundtrip_tests(
        self,
        entity_config: Dict[str, Any],
        field_mappings: List[Dict[str, Any]]
    ) -> str:
        """Generate create → read → update roundtrip property tests"""
        entity = entity_config['entity_name']

        return f'''
    @given(
        create_data=SpecQLStrategies.for_entity(...),
        update_data=SpecQLStrategies.for_entity(...)
    )
    def test_create_update_roundtrip(self, clean_db, create_data, update_data):
        """Property: Created entity can always be updated"""
        tenant_id = UUID("{entity_config['default_tenant_id']}")
        user_id = UUID("{entity_config['default_user_id']}")

        with clean_db.cursor() as cur:
            # Create
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, create_data)
            )
            create_result = cur.fetchone()[0]
            assert create_result['status'] == 'success'

            entity_id = UUID(create_result['object_data']['id'])

            # Update
            cur.execute(
                "SELECT app.update_{entity.lower()}(%s, %s, %s)",
                (entity_id, user_id, update_data)
            )
            update_result = cur.fetchone()[0]

        # Property: Update should succeed for any valid data
        assert update_result['status'] == 'success', \\
            f"Update failed: {{update_result}}"

        # Property: Updated fields should match input
        for field, value in update_data.items():
            assert update_result['object_data'][field] == value, \\
                f"Field {{field}} not updated correctly"
'''

    def generate_state_machine_tests(
        self,
        entity_config: Dict[str, Any],
        actions: List[Dict[str, Any]]
    ) -> str:
        """Generate state machine property tests for actions"""
        entity = entity_config['entity_name']

        # Find enum fields (potential state fields)
        # For Contact: status = enum(lead, qualified, customer)
        # Generate state transition tests

        return f'''
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize

class {entity}StateMachine(RuleBasedStateMachine):
    """State machine property tests for {entity}"""

    def __init__(self):
        super().__init__()
        self.entity_id = None
        self.current_status = None

    @initialize()
    def create_{entity.lower()}(self):
        """Initialize by creating entity"""
        # Create entity with initial state
        self.entity_id = UUID("...")
        self.current_status = "lead"

    @rule()
    def qualify_lead(self):
        """Try to qualify lead"""
        if self.current_status == "lead":
            # Should succeed
            result = execute_action("qualify_lead", self.entity_id)
            assert result['status'] == 'success'
            self.current_status = "qualified"
        else:
            # Should fail
            result = execute_action("qualify_lead", self.entity_id)
            assert result['status'].startswith('failed:')

Test{entity}StateMachine.TestCase.settings = settings(max_examples=100)
'''
```

---

## 📊 Success Criteria

### Week 5 Completion
- ✅ Hypothesis strategies for all 23 scalar types
- ✅ Entity-level strategy generation
- ✅ Invalid value strategies (negative testing)
- ✅ Idempotency property tests
- ✅ Constraint property tests
- ✅ Roundtrip property tests
- ✅ Run 1000+ auto-generated test cases
- ✅ Find at least 2 edge case bugs

---

## 📝 Example Output

**File**: `tests/property/test_contact_properties.py`

```python
"""Auto-generated property-based tests for Contact"""

from hypothesis import given, settings
from hypothesis import strategies as st
from uuid import UUID
import pytest

class TestContactIdempotency:
    """Idempotency properties for Contact"""

    @given(st.emails(), st.sampled_from(['lead', 'qualified', 'customer']))
    @settings(max_examples=100)
    def test_duplicate_email_always_fails(self, clean_db, email, status):
        """Property: Duplicate email should always fail"""
        data = {"email": email, "status": status}
        tenant_id = UUID("22222222-2222-2222-2222-222222222222")
        user_id = UUID("01232022-0000-0000-0000-000000000001")

        with clean_db.cursor() as cur:
            # First create
            cur.execute("SELECT app.create_contact(%s, %s, %s)", (tenant_id, user_id, data))
            result1 = cur.fetchone()[0]
            assert result1['status'] == 'success'

            # Duplicate
            cur.execute("SELECT app.create_contact(%s, %s, %s)", (tenant_id, user_id, data))
            result2 = cur.fetchone()[0]
            assert result2['status'].startswith('failed:')


class TestContactConstraints:
    """Constraint properties for Contact"""

    @given(
        st.text(alphabet='abc', min_size=1, max_size=100).filter(lambda x: '@' not in x)
    )
    def test_invalid_email_always_fails(self, clean_db, invalid_email):
        """Property: Invalid email format should always fail"""
        data = {"email": invalid_email, "status": "lead"}

        with clean_db.cursor() as cur:
            cur.execute("SELECT app.create_contact(%s, %s, %s)", (..., data))
            result = cur.fetchone()[0]

        assert result['status'].startswith('failed:'), \\
            f"Invalid email {invalid_email} should fail"
```

---

**Next**: [Integration Plan](05_INTEGRATION.md)
