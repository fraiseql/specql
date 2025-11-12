# Track C: Three-Tier Pattern Architecture - Implementation Plan

**Duration**: 12 weeks
**Objective**: Build composable pattern hierarchy from primitives → domain patterns → business entities
**Team**: All teams (Parser, Schema, Actions, Pattern Library)
**Output**: NPM-like marketplace for business logic

---

## 🎯 Vision

Transform SpecQL from low-level primitives to high-level business solutions through three tiers:

**Tier 1: Primitives** (Track A)
- 35 atomic actions (declare, if, query, etc.)
- Universal building blocks
- Language-agnostic

**Tier 2: Domain Patterns** (This track)
- 15+ reusable business logic patterns
- Compose from Tier 1 primitives
- Domain-specific (state machines, workflows, hierarchies)

**Tier 3: Business Entities** (This track)
- Industry-specific entity templates
- Compose from Tier 2 patterns
- Ready-to-use (CRM.Contact, E-Commerce.Product)

**Result**: Developer types `specql instantiate crm.contact` → Full entity with state machine, audit trail, validation

---

## 📊 Current State

**What Users Write Today**:
```yaml
entity: Contact
fields:
  email: text
  status: enum(lead, prospect, customer)
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'prospect'
      # ... 20 more lines for validation, audit, etc.
```

**Limitations**:
- Every entity reimplements state machines
- No reusable audit trail pattern
- No approval workflow template
- No hierarchy navigation pattern
- 100+ lines YAML for simple entity

---

## 🚀 Target State

**What Users Will Write**:
```yaml
entity: Contact
extends: crm.contact_template  # Tier 3
fields:
  custom_field: text  # Add custom fields
```

**What They Get**:
- Full Contact entity with 20+ fields
- State machine (lead → prospect → customer)
- Audit trail (created_by, updated_by, version)
- Approval workflow
- Hierarchy navigation
- 15+ actions pre-built
- GraphQL API
- TypeScript types
- Django models

**Result**: 5 lines YAML → 2000+ lines production code

---

## 📅 12-Week Timeline

### Phase 1: Tier 2 Foundation (Weeks 1-3)
**Goal**: Database schema for domain patterns + 3 example patterns
- Design pattern storage schema
- Implement pattern instantiation engine
- Create 3 core patterns (state_machine, audit_trail, validation_chain)

### Phase 2: Tier 2 Expansion (Weeks 4-6)
**Goal**: 15 domain patterns
- 12 additional domain patterns
- Pattern composition system
- Pattern testing framework

### Phase 3: Tier 3 Foundation (Weeks 7-9)
**Goal**: Business entity templates + CRM entities
- Design entity template schema
- Template instantiation engine
- CRM entities (Contact, Lead, Opportunity, Account)

### Phase 4: Tier 3 Expansion (Weeks 10-12)
**Goal**: 15+ business entity templates
- E-Commerce entities (Product, Order, Cart, Customer)
- Healthcare entities (Patient, Appointment, Prescription)
- Template marketplace foundation

---

## 🗄️ Database Schema Extensions

### Additional Tables for Pattern Library

```sql
-- Tier 2: Domain Patterns
CREATE TABLE domain_patterns (
    domain_pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name TEXT NOT NULL UNIQUE,
    pattern_category TEXT NOT NULL, -- state_machine, workflow, hierarchy, audit, validation
    description TEXT,
    parameters JSONB NOT NULL, -- Pattern parameters schema
    implementation JSONB NOT NULL, -- Pattern logic in Tier 1 primitives
    usage_count INTEGER DEFAULT 0,
    popularity_score REAL DEFAULT 0.0,
    tags TEXT, -- Comma-separated tags
    icon TEXT, -- Emoji or icon name
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tier 3: Business Entity Templates
CREATE TABLE entity_templates (
    entity_template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_pattern_id INTEGER, -- Optional: based on domain pattern
    template_name TEXT NOT NULL UNIQUE,
    template_namespace TEXT NOT NULL, -- e.g., 'crm', 'ecommerce', 'healthcare'
    description TEXT,
    default_fields JSONB NOT NULL, -- Fields included in template
    default_patterns JSONB NOT NULL, -- Domain patterns applied
    default_actions JSONB NOT NULL, -- Pre-built actions
    configuration_options JSONB, -- Customization options
    icon TEXT,
    tags TEXT,
    usage_count INTEGER DEFAULT 0,
    popularity_score REAL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_pattern_id) REFERENCES domain_patterns(domain_pattern_id)
);

-- Pattern Dependencies (reuse from Track B)
-- Already defined: pattern_dependencies

-- Entity Template Dependencies
CREATE TABLE entity_template_dependencies (
    dependency_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_template_id INTEGER NOT NULL,
    depends_on_template_id INTEGER,
    depends_on_pattern_id INTEGER,
    dependency_type TEXT NOT NULL, -- requires, suggests, conflicts_with
    FOREIGN KEY (entity_template_id) REFERENCES entity_templates(entity_template_id),
    FOREIGN KEY (depends_on_template_id) REFERENCES entity_templates(entity_template_id),
    FOREIGN KEY (depends_on_pattern_id) REFERENCES domain_patterns(domain_pattern_id)
);

-- Pattern Instantiations (track usage)
CREATE TABLE pattern_instantiations (
    instantiation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name TEXT NOT NULL,
    domain_pattern_id INTEGER,
    entity_template_id INTEGER,
    parameters JSONB,
    instantiated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_pattern_id) REFERENCES domain_patterns(domain_pattern_id),
    FOREIGN KEY (entity_template_id) REFERENCES entity_templates(entity_template_id)
);

-- Indexes
CREATE INDEX idx_domain_patterns_category ON domain_patterns(pattern_category);
CREATE INDEX idx_entity_templates_namespace ON entity_templates(template_namespace);
CREATE INDEX idx_entity_templates_popularity ON entity_templates(popularity_score DESC);
```

---

## WEEK 1-3: Tier 2 Foundation

### Objective
Create foundation for domain patterns with 3 core patterns.

---

### 🔴 RED Phase (Days 1-3): Write Failing Tests

#### Test 1: Domain Pattern Storage
**File**: `tests/unit/pattern_library/test_domain_patterns.py`

```python
from src.pattern_library.api import PatternLibrary

def test_add_domain_pattern():
    """Test adding a domain pattern"""
    library = PatternLibrary(db_path=":memory:")

    pattern_id = library.add_domain_pattern(
        name="state_machine",
        category="workflow",
        description="State machine pattern with transitions",
        parameters={
            "entity": {"type": "string", "required": True},
            "states": {"type": "array", "required": True},
            "transitions": {"type": "object", "required": True},
            "guards": {"type": "object", "required": False}
        },
        implementation={
            "actions": [
                {
                    "name": "transition_to_{state}",
                    "steps": [
                        {"type": "query", "sql": "SELECT state FROM tb_{entity} WHERE id = $id"},
                        {"type": "validate", "condition": "state IN allowed_states"},
                        {"type": "validate", "condition": "transition_allowed"},
                        {"type": "update", "entity": "{entity}", "fields": {"state": "{target_state}"}},
                        {"type": "insert", "entity": "{entity}_audit", "fields": {"transition": "...", "timestamp": "NOW()"}}
                    ]
                }
            ]
        }
    )

    assert pattern_id > 0

    # Retrieve
    pattern = library.get_domain_pattern("state_machine")
    assert pattern is not None
    assert pattern["pattern_name"] == "state_machine"
    assert pattern["pattern_category"] == "workflow"

def test_instantiate_domain_pattern():
    """Test instantiating a domain pattern for an entity"""
    library = PatternLibrary(db_path=":memory:")

    # Add pattern
    library.add_domain_pattern(
        name="audit_trail",
        category="audit",
        description="Automatic audit trail",
        parameters={"entity": {"type": "string"}},
        implementation={
            "fields": [
                {"name": "created_at", "type": "timestamp", "default": "NOW()"},
                {"name": "created_by", "type": "uuid"},
                {"name": "updated_at", "type": "timestamp", "default": "NOW()"},
                {"name": "updated_by", "type": "uuid"},
                {"name": "version", "type": "integer", "default": 1}
            ],
            "triggers": [
                {"event": "before_update", "action": "increment_version"}
            ]
        }
    )

    # Instantiate for Contact entity
    result = library.instantiate_domain_pattern(
        pattern_name="audit_trail",
        entity_name="Contact",
        parameters={"entity": "Contact"}
    )

    assert result is not None
    assert "fields" in result
    assert len(result["fields"]) == 5
    assert result["fields"][0]["name"] == "created_at"
```

#### Test 2: Pattern Composition
**File**: `tests/unit/pattern_library/test_pattern_composition.py`

```python
def test_compose_multiple_patterns():
    """Test composing multiple domain patterns into one entity"""
    library = PatternLibrary(db_path=":memory:")

    # Add patterns
    library.add_domain_pattern(name="audit_trail", category="audit", description="...", parameters={}, implementation={...})
    library.add_domain_pattern(name="state_machine", category="workflow", description="...", parameters={}, implementation={...})
    library.add_domain_pattern(name="soft_delete", category="data_management", description="...", parameters={}, implementation={...})

    # Compose
    result = library.compose_patterns(
        entity_name="Contact",
        patterns=[
            {"pattern": "audit_trail", "params": {}},
            {"pattern": "state_machine", "params": {"states": ["lead", "prospect", "customer"]}},
            {"pattern": "soft_delete", "params": {}}
        ]
    )

    assert result is not None
    assert "fields" in result
    assert "actions" in result

    # Should have fields from all 3 patterns
    field_names = [f["name"] for f in result["fields"]]
    assert "created_at" in field_names  # audit_trail
    assert "state" in field_names  # state_machine
    assert "deleted_at" in field_names  # soft_delete
```

**Expected Output**: Tests FAIL

---

### 🟢 GREEN Phase (Days 4-12): Implementation

#### Step 1: Extend PatternLibrary API
**File**: `src/pattern_library/api.py` (extend)

```python
class PatternLibrary:
    # ... existing methods ...

    # ===== Tier 2: Domain Patterns =====

    def add_domain_pattern(
        self,
        name: str,
        category: str,
        description: str,
        parameters: Dict[str, Any],
        implementation: Dict[str, Any],
        tags: str = "",
        icon: str = ""
    ) -> int:
        """Add a domain pattern (Tier 2)"""
        cursor = self.db.execute(
            """
            INSERT INTO domain_patterns
            (pattern_name, pattern_category, description, parameters, implementation, tags, icon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, category, description, json.dumps(parameters), json.dumps(implementation), tags, icon)
        )
        self.db.commit()
        return cursor.lastrowid

    def get_domain_pattern(self, name: str) -> Optional[Dict[str, Any]]:
        """Get domain pattern by name"""
        cursor = self.db.execute(
            "SELECT * FROM domain_patterns WHERE pattern_name = ?",
            (name,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result["parameters"] = json.loads(result["parameters"])
            result["implementation"] = json.loads(result["implementation"])
            return result
        return None

    def get_all_domain_patterns(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all domain patterns, optionally filtered by category"""
        if category:
            cursor = self.db.execute(
                "SELECT * FROM domain_patterns WHERE pattern_category = ? ORDER BY popularity_score DESC",
                (category,)
            )
        else:
            cursor = self.db.execute(
                "SELECT * FROM domain_patterns ORDER BY popularity_score DESC"
            )

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["parameters"] = json.loads(result["parameters"])
            result["implementation"] = json.loads(result["implementation"])
            results.append(result)

        return results

    def instantiate_domain_pattern(
        self,
        pattern_name: str,
        entity_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Instantiate a domain pattern for a specific entity

        Returns:
            Dictionary with instantiated fields, actions, etc.
        """
        pattern = self.get_domain_pattern(pattern_name)
        if not pattern:
            raise ValueError(f"Domain pattern not found: {pattern_name}")

        # Validate parameters
        self._validate_pattern_parameters(pattern["parameters"], parameters)

        # Instantiate implementation
        instantiated = self._instantiate_implementation(
            pattern["implementation"],
            entity_name,
            parameters
        )

        # Record instantiation
        self.db.execute(
            """
            INSERT INTO pattern_instantiations (entity_name, domain_pattern_id, parameters)
            VALUES (?, ?, ?)
            """,
            (entity_name, pattern["domain_pattern_id"], json.dumps(parameters))
        )
        self.db.commit()

        return instantiated

    def _validate_pattern_parameters(
        self,
        param_schema: Dict[str, Any],
        provided_params: Dict[str, Any]
    ):
        """Validate provided parameters against schema"""
        for param_name, param_def in param_schema.items():
            if param_def.get("required", False) and param_name not in provided_params:
                raise ValueError(f"Required parameter missing: {param_name}")

    def _instantiate_implementation(
        self,
        implementation: Dict[str, Any],
        entity_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Instantiate pattern implementation with entity-specific values

        Replaces placeholders like {entity}, {state}, etc. with actual values
        """
        from jinja2 import Template

        # Convert implementation to JSON string, replace placeholders, parse back
        impl_json = json.dumps(implementation)
        template = Template(impl_json)

        context = {
            "entity": entity_name,
            **parameters
        }

        instantiated_json = template.render(**context)
        instantiated = json.loads(instantiated_json)

        return instantiated

    def compose_patterns(
        self,
        entity_name: str,
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compose multiple domain patterns into single entity definition

        Args:
            entity_name: Name of entity
            patterns: List of {"pattern": "pattern_name", "params": {...}}

        Returns:
            Composed entity definition with merged fields, actions, etc.
        """
        composed = {
            "entity": entity_name,
            "fields": [],
            "actions": [],
            "triggers": [],
            "indexes": []
        }

        for pattern_spec in patterns:
            pattern_name = pattern_spec["pattern"]
            params = pattern_spec.get("params", {})

            instantiated = self.instantiate_domain_pattern(
                pattern_name, entity_name, params
            )

            # Merge fields
            if "fields" in instantiated:
                composed["fields"].extend(instantiated["fields"])

            # Merge actions
            if "actions" in instantiated:
                composed["actions"].extend(instantiated["actions"])

            # Merge triggers
            if "triggers" in instantiated:
                composed["triggers"].extend(instantiated["triggers"])

            # Merge indexes
            if "indexes" in instantiated:
                composed["indexes"].extend(instantiated["indexes"])

        return composed
```

#### Step 2: Create 3 Core Domain Patterns

**Pattern 1: State Machine**
**File**: `src/pattern_library/seed_domain_patterns.py`

```python
def seed_state_machine_pattern(library: PatternLibrary):
    """Seed state machine domain pattern"""

    library.add_domain_pattern(
        name="state_machine",
        category="workflow",
        description="State machine with transitions, guards, and audit trail",
        parameters={
            "entity": {"type": "string", "required": True},
            "states": {"type": "array", "required": True, "description": "List of valid states"},
            "transitions": {"type": "object", "required": True, "description": "Allowed state transitions"},
            "guards": {"type": "object", "required": False, "description": "Validation rules per transition"},
            "initial_state": {"type": "string", "required": False, "description": "Default initial state"}
        },
        implementation={
            "fields": [
                {
                    "name": "state",
                    "type": "enum",
                    "values": "{{ states }}",
                    "default": "{{ initial_state }}",
                    "required": True
                },
                {
                    "name": "state_changed_at",
                    "type": "timestamp",
                    "default": "NOW()"
                },
                {
                    "name": "state_changed_by",
                    "type": "uuid"
                }
            ],
            "actions": [
                {
                    "name": "transition_to",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "target_state", "type": "text"},
                        {"name": "user_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT state FROM tb_{{ entity }} WHERE id = $id",
                            "into": "current_state"
                        },
                        {
                            "type": "validate",
                            "condition": "target_state IN ({{ states | map('tojson') | join(', ') }})",
                            "error": "Invalid target state"
                        },
                        {
                            "type": "validate",
                            "condition": "transition_allowed(current_state, target_state)",
                            "error": "Transition not allowed"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "state": "$target_state",
                                "state_changed_at": "NOW()",
                                "state_changed_by": "$user_id"
                            }
                        },
                        {
                            "type": "insert",
                            "entity": "{{ entity }}_state_history",
                            "fields": {
                                "entity_id": "$id",
                                "from_state": "$current_state",
                                "to_state": "$target_state",
                                "changed_by": "$user_id",
                                "changed_at": "NOW()"
                            }
                        }
                    ]
                }
            ],
            "tables": [
                {
                    "name": "{{ entity }}_state_history",
                    "fields": [
                        {"name": "pk_{{ entity }}_state_history", "type": "integer", "primary_key": True},
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "from_state", "type": "text"},
                        {"name": "to_state", "type": "text"},
                        {"name": "changed_by", "type": "uuid"},
                        {"name": "changed_at", "type": "timestamp", "default": "NOW()"}
                    ]
                }
            ]
        },
        tags="workflow,state,transition,audit",
        icon="🔄"
    )

    print("✅ Seeded state_machine pattern")
```

**Pattern 2: Audit Trail**
```python
def seed_audit_trail_pattern(library: PatternLibrary):
    """Seed audit trail domain pattern"""

    library.add_domain_pattern(
        name="audit_trail",
        category="audit",
        description="Automatic audit trail tracking who created/updated and when",
        parameters={
            "entity": {"type": "string", "required": True},
            "track_versions": {"type": "boolean", "required": False, "default": True}
        },
        implementation={
            "fields": [
                {"name": "created_at", "type": "timestamp", "default": "NOW()", "required": True},
                {"name": "created_by", "type": "uuid", "required": True},
                {"name": "updated_at", "type": "timestamp", "default": "NOW()", "required": True},
                {"name": "updated_by", "type": "uuid"},
                {"name": "version", "type": "integer", "default": 1}
            ],
            "triggers": [
                {
                    "event": "before_insert",
                    "action": "set_created_fields",
                    "logic": {
                        "steps": [
                            {"type": "assign", "variable": "created_at", "value": "NOW()"},
                            {"type": "assign", "variable": "created_by", "value": "$current_user_id"},
                            {"type": "assign", "variable": "version", "value": 1}
                        ]
                    }
                },
                {
                    "event": "before_update",
                    "action": "set_updated_fields",
                    "logic": {
                        "steps": [
                            {"type": "assign", "variable": "updated_at", "value": "NOW()"},
                            {"type": "assign", "variable": "updated_by", "value": "$current_user_id"},
                            {"type": "assign", "variable": "version", "value": "version + 1"}
                        ]
                    }
                }
            ]
        },
        tags="audit,tracking,version,history",
        icon="📋"
    )

    print("✅ Seeded audit_trail pattern")
```

**Pattern 3: Soft Delete**
```python
def seed_soft_delete_pattern(library: PatternLibrary):
    """Seed soft delete domain pattern"""

    library.add_domain_pattern(
        name="soft_delete",
        category="data_management",
        description="Soft delete pattern with deleted_at timestamp",
        parameters={
            "entity": {"type": "string", "required": True}
        },
        implementation={
            "fields": [
                {"name": "deleted_at", "type": "timestamp", "nullable": True},
                {"name": "deleted_by", "type": "uuid", "nullable": True}
            ],
            "actions": [
                {
                    "name": "soft_delete",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "user_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "deleted_at IS NULL",
                            "error": "{{ entity }} already deleted"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "deleted_at": "NOW()",
                                "deleted_by": "$user_id"
                            }
                        }
                    ]
                },
                {
                    "name": "restore",
                    "parameters": [
                        {"name": "id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "deleted_at IS NOT NULL",
                            "error": "{{ entity }} not deleted"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "deleted_at": "NULL",
                                "deleted_by": "NULL"
                            }
                        }
                    ]
                }
            ],
            "views": [
                {
                    "name": "{{ entity }}_active",
                    "query": "SELECT * FROM tb_{{ entity }} WHERE deleted_at IS NULL"
                }
            ]
        },
        tags="delete,soft,restore,data_management",
        icon="🗑️"
    )

    print("✅ Seeded soft_delete pattern")
```

---

### 🔧 REFACTOR Phase (Days 13-15): Optimize

**Refactorings**:
1. Pattern validation utility
2. Conflict detection (e.g., two patterns defining same field)
3. Pattern dependency resolver
4. Performance optimization for composition

---

### ✅ QA Phase (Days 16-18): Verification

**Tests**:
- [ ] 10 unit tests for domain patterns
- [ ] 5 integration tests for pattern composition
- [ ] E2E test: Compose Contact entity from 3 patterns

---

## WEEK 4-6: Tier 2 Expansion (12 More Patterns)

### 12 Additional Domain Patterns

1. **validation_chain** - Chainable validation rules
2. **approval_workflow** - Multi-stage approval process
3. **hierarchy_navigation** - Parent-child relationships with recursive queries
4. **computed_fields** - Auto-calculated fields
5. **search_optimization** - Full-text search indexes
6. **internationalization** - i18n field support
7. **file_attachment** - File upload/storage pattern
8. **tagging** - Flexible tagging system
9. **commenting** - Comments/notes on entities
10. **notification** - Event-triggered notifications
11. **scheduling** - Date-based scheduling pattern
12. **rate_limiting** - API rate limiting pattern

**Deliverable**: 15 total domain patterns (3 + 12)

---

## WEEK 7-9: Tier 3 Foundation (CRM Entities)

### Objective
Create business entity templates using Tier 2 patterns.

### Example: CRM Contact Template
**File**: `src/pattern_library/seed_entity_templates.py`

```python
def seed_crm_contact_template(library: PatternLibrary):
    """Seed CRM Contact entity template"""

    library.add_entity_template(
        template_name="contact",
        template_namespace="crm",
        description="CRM contact with state machine, audit trail, and soft delete",
        default_fields={
            # Core fields
            "first_name": {"type": "text", "required": True},
            "last_name": {"type": "text", "required": True},
            "email": {"type": "email", "required": True, "unique": True},
            "phone": {"type": "text"},
            "company": {"type": "ref", "entity": "Company"},

            # Address
            "street": {"type": "text"},
            "city": {"type": "text"},
            "state": {"type": "text"},
            "postal_code": {"type": "text"},
            "country": {"type": "text", "default": "US"},

            # Metadata
            "source": {"type": "enum", "values": ["website", "referral", "import", "manual"]},
            "tags": {"type": "array"},
            "notes": {"type": "text"}
        },
        default_patterns={
            "state_machine": {
                "states": ["lead", "prospect", "qualified", "customer", "inactive"],
                "transitions": {
                    "lead->prospect": {"action": "initial_contact"},
                    "prospect->qualified": {"action": "qualify", "guard": "has_budget"},
                    "qualified->customer": {"action": "convert", "guard": "has_signed_contract"},
                    "customer->inactive": {"action": "deactivate"}
                },
                "initial_state": "lead"
            },
            "audit_trail": {
                "track_versions": True
            },
            "soft_delete": {}
        },
        default_actions={
            "qualify": {
                "description": "Qualify lead as prospect",
                "steps": [
                    {"type": "validate", "condition": "state = 'lead'"},
                    {"type": "validate", "condition": "email IS NOT NULL"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "prospect"}}
                ]
            },
            "convert_to_customer": {
                "description": "Convert qualified prospect to customer",
                "steps": [
                    {"type": "validate", "condition": "state = 'qualified'"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "customer"}},
                    {"type": "notify", "recipients": ["sales_team"], "message": "New customer: {first_name} {last_name}"}
                ]
            }
        },
        configuration_options={
            "enable_duplicates_detection": {"type": "boolean", "default": True},
            "require_phone": {"type": "boolean", "default": False},
            "enable_lead_scoring": {"type": "boolean", "default": False}
        },
        icon="👤",
        tags="crm,contact,lead,customer,sales"
    )

    print("✅ Seeded CRM Contact template")
```

**CLI Usage**:
```bash
# Instantiate CRM Contact template
specql instantiate crm.contact --output=entities/contact.yaml

# Generates full entity YAML with all patterns applied
```

**Generated YAML**:
```yaml
entity: Contact
schema: crm
fields:
  # 20+ fields from template
  first_name: text
  last_name: text
  email: email
  # ... all default fields ...
  # From audit_trail pattern
  created_at: timestamp
  created_by: uuid
  # From state_machine pattern
  state: enum(lead, prospect, qualified, customer, inactive)
  # From soft_delete pattern
  deleted_at: timestamp?

actions:
  # From state_machine pattern
  - name: transition_to
    # ...

  # From template
  - name: qualify
    # ...

  - name: convert_to_customer
    # ...

  # From soft_delete pattern
  - name: soft_delete
    # ...

  - name: restore
    # ...
```

**Deliverable**: 4 CRM entity templates (Contact, Lead, Opportunity, Account)

---

## WEEK 10-12: Tier 3 Expansion (More Industries)

### E-Commerce Entity Templates

1. **Product** - With inventory, pricing, variants
2. **Order** - With state machine (pending → paid → shipped → delivered)
3. **Cart** - With expiration, calculation
4. **Customer** - With loyalty, payment methods

### Healthcare Entity Templates

1. **Patient** - With privacy, consent, medical records
2. **Appointment** - With scheduling, reminders
3. **Prescription** - With validation, refills
4. **Provider** - With credentials, specialties

### Additional Templates

1. **Project Management**: Project, Task, Milestone
2. **HR**: Employee, Position, Department, Timesheet
3. **Finance**: Invoice, Payment, Transaction

**Deliverable**: 15+ entity templates across 5 industries

---

## 📊 Track C Summary (12 Weeks)

### Deliverables

**Database**:
- ✅ Domain patterns table + entity templates table
- ✅ 15 domain patterns
- ✅ 15+ business entity templates

**Code**:
- ✅ Pattern instantiation engine
- ✅ Pattern composition system
- ✅ Template instantiation engine
- ✅ CLI commands (`specql instantiate`)

**Tests**:
- ✅ 30+ unit tests
- ✅ 15+ integration tests
- ✅ E2E tests for each template

**Documentation**:
- ✅ Domain pattern catalog
- ✅ Entity template catalog
- ✅ Pattern composition guide
- ✅ Template customization guide

### Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Reusable Patterns** | 0 | 15 | +15 |
| **Entity Templates** | 0 | 15+ | +15 |
| **Lines YAML (typical entity)** | 100+ | 5-10 | -90% |
| **Time to First Entity** | 30 min | 30 sec | -99% |

### Success Criteria

- [x] 15 domain patterns implemented
- [x] 15+ entity templates created
- [x] Pattern composition working
- [x] Template instantiation working
- [x] CLI commands functional
- [x] Documentation complete

---

## 🚀 Marketplace Foundation

After Track C, foundation is ready for:
- Community-contributed patterns
- Template sharing
- Pattern versioning
- Template marketplace UI

**Next Phase**: Track F (Deployment & Community)

---

**Last Updated**: 2025-11-12
**Status**: Ready for Implementation
**Next**: Week 1-3 - Tier 2 Foundation (3 core patterns)
