# Three-Tier Pattern Hierarchy: From Primitives to Business Domains

**Date**: 2025-11-12
**Vision**: Hierarchical pattern library from atomic operations → domain patterns → industry entities
**Status**: Architecture Design

---

## 🎯 The Three-Tier Vision

> "We could have three libraries:
> 1. **Tier 1**: Basic primitive actions (like FraiseQL types)
> 2. **Tier 2**: Complex domain patterns (abstract business logic)
> 3. **Tier 3**: Business domain entities (industry-specific templates)"

**This is the composable architecture for universal business logic.**

---

## 📊 Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ TIER 3: Business Domain Entities (Industry-Specific)          │
│                                                                 │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│ │ CRM Domain   │  │ E-Commerce   │  │ Healthcare   │          │
│ │ - Contact    │  │ - Product    │  │ - Patient    │          │
│ │ - Company    │  │ - Order      │  │ - Appointment│          │
│ │ - Opportunity│  │ - Cart       │  │ - Medication │          │
│ └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│        │                  │                  │                  │
│        └──────────────────┼──────────────────┘                  │
│                           ▼                                     │
├─────────────────────────────────────────────────────────────────┤
│ TIER 2: Domain Patterns (Abstract Business Logic)             │
│                                                                 │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│ │ Approval     │  │ State        │  │ Hierarchy    │          │
│ │ Workflow     │  │ Machine      │  │ Navigation   │          │
│ │              │  │              │  │              │          │
│ │ - request    │  │ - transition │  │ - ancestors  │          │
│ │ - approve    │  │ - validate   │  │ - descendants│          │
│ │ - reject     │  │ - guard      │  │ - siblings   │          │
│ └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│        │                  │                  │                  │
│        └──────────────────┼──────────────────┘                  │
│                           ▼                                     │
├─────────────────────────────────────────────────────────────────┤
│ TIER 1: Primitive Actions (Atomic Operations)                 │
│                                                                 │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│ │ Variables    │  │ Queries      │  │ Control Flow │          │
│ │              │  │              │  │              │          │
│ │ - declare    │  │ - query      │  │ - if/else    │          │
│ │ - assign     │  │ - cte        │  │ - switch     │          │
│ │ - let        │  │ - aggregate  │  │ - while      │          │
│ └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Tier 1: Primitive Actions (35 Patterns)

**Purpose**: Atomic, language-agnostic operations
**Analogy**: Like FraiseQL scalar types (email, money, uuid)
**Storage**: `patterns` table with `tier = 'primitive'`

### Categories

#### 1.1 Variables & State
- `declare` - Variable declaration
- `assign` - Variable assignment
- `let` - Immutable binding
- `const` - Constant declaration

#### 1.2 Queries & Data Access
- `query` - SELECT with INTO
- `cte` - Common table expressions
- `aggregate` - GROUP BY, HAVING
- `subquery` - Correlated subqueries
- `join` - Table joins

#### 1.3 Control Flow
- `if` - Conditional branching
- `switch` - Multi-way branching
- `while` - Conditional loop
- `for_query` - Query iteration
- `foreach` - Collection iteration

#### 1.4 Data Manipulation
- `insert` - Create records
- `update` - Modify records
- `delete` - Remove records
- `upsert` - Insert or update
- `batch_operation` - Bulk operations

#### 1.5 Functions & Composition
- `call_function` - Invoke function
- `return` - Return value
- `return_early` - Early exit
- `return_table` - Table-returning function

#### 1.6 Advanced Operations
- `json_build` - JSON construction
- `array_build` - Array operations
- `transform` - Data pipelines
- `cursor` - Cursor operations
- `exception_handling` - Error handling

**Database Schema**:
```sql
INSERT INTO patterns VALUES (
    1,
    'declare',
    'primitive',
    'variables',
    'tier_1',
    'Declare a typed variable',
    'declare:\n  name: type [= value]',
    '[]',
    2
);
```

---

## 🏗️ Tier 2: Domain Patterns (Reusable Business Logic)

**Purpose**: Abstract business patterns that apply across domains
**Analogy**: Like design patterns (Observer, Strategy, State Machine)
**Storage**: `domain_patterns` table (new)
**Composition**: Built from Tier 1 primitives

### Categories

#### 2.1 State Management Patterns

##### State Machine Pattern
```yaml
# Pattern Definition
domain_pattern: state_machine
description: Manage entity state transitions with validation
parameters:
  - entity: Entity name
  - states: List of valid states
  - transitions: Allowed state changes
  - guards: Validation rules per transition

# Implementation (uses Tier 1 primitives)
implementation:
  transition_action:
    steps:
      - query:
          into: current_state
          select: state
          from: "tb_{{ entity }}"
          where: "id = $input.id"

      - validate:
          expression: "$input.target_state IN {{ states }}"
          error: "invalid_target_state"

      - validate:
          expression: "$current_state -> $input.target_state IN {{ transitions }}"
          error: "invalid_transition"

      - if:
          condition: "{{ guards[$current_state][$input.target_state] }}"
          then:
            - update:
                entity: "{{ entity }}"
                set:
                  state: "$input.target_state"
                  state_changed_at: "now()"
                where: "id = $input.id"
          else:
            - return_early:
                error: "guard_failed"

# Usage in Tier 3 entities
entity: Order
uses_pattern: state_machine
pattern_config:
  states: [pending, confirmed, shipped, delivered, cancelled]
  transitions:
    - [pending, confirmed]
    - [pending, cancelled]
    - [confirmed, shipped]
    - [confirmed, cancelled]
    - [shipped, delivered]
  guards:
    pending->confirmed: "$order.payment_received = true"
    confirmed->shipped: "$order.items_packed = true"
```

---

#### 2.2 Approval Workflow Pattern
```yaml
domain_pattern: approval_workflow
description: Multi-level approval process with notifications
parameters:
  - entity: Entity requiring approval
  - approval_levels: Number of approval levels
  - approver_roles: Roles that can approve
  - notification_channels: Where to notify

implementation:
  request_approval_action:
    steps:
      - insert:
          entity: "{{ entity }}Approval"
          set:
            entity_id: "$input.entity_id"
            requester: "$auth_user_id"
            status: "pending"
            level: 1

      - call_function:
          function: "notify_approvers"
          args:
            entity_id: "$input.entity_id"
            level: 1
            roles: "{{ approver_roles[1] }}"

  approve_action:
    steps:
      - query:
          into: approval
          select: "*"
          from: "tb_{{ entity }}_approval"
          where: "entity_id = $input.entity_id AND status = 'pending'"

      - validate:
          expression: "$auth_user.role IN {{ approver_roles[$approval.level] }}"
          error: "unauthorized_approver"

      - if:
          condition: "$approval.level < {{ approval_levels }}"
          then:
            # More levels required
            - update:
                entity: "{{ entity }}Approval"
                set:
                  level: "$approval.level + 1"
                where: "entity_id = $input.entity_id"

            - call_function:
                function: "notify_approvers"
                args:
                  level: "$approval.level + 1"
          else:
            # Final approval
            - update:
                entity: "{{ entity }}Approval"
                set:
                  status: "approved"
                  approved_at: "now()"

            - update:
                entity: "{{ entity }}"
                set:
                  approval_status: "approved"
                where: "id = $input.entity_id"

# Usage
entity: PurchaseOrder
uses_pattern: approval_workflow
pattern_config:
  approval_levels: 3
  approver_roles:
    1: [manager]
    2: [director]
    3: [cfo]
  notification_channels: [email, slack]
```

---

#### 2.3 Hierarchical Navigation Pattern
```yaml
domain_pattern: hierarchy_navigation
description: Navigate tree structures (ancestors, descendants, siblings)
parameters:
  - entity: Hierarchical entity
  - parent_field: FK to parent
  - max_depth: Maximum traversal depth

implementation:
  get_ancestors_action:
    steps:
      - cte:
          name: hierarchy
          recursive: true
          base:
            select: "*"
            from: "tb_{{ entity }}"
            where: "id = $input.id"
          recursive_part:
            select: "parent.*"
            from: "tb_{{ entity }} parent"
            join:
              table: "hierarchy h"
              on: "parent.id = h.{{ parent_field }}"

      - query:
          into: ancestors
          select: "*"
          from: hierarchy
          order_by: "level ASC"

      - return: ancestors

  get_descendants_action:
    steps:
      - cte:
          name: hierarchy
          recursive: true
          base:
            select: "*, 0 as depth"
            from: "tb_{{ entity }}"
            where: "id = $input.id"
          recursive_part:
            select: "child.*, h.depth + 1"
            from: "tb_{{ entity }} child"
            join:
              table: "hierarchy h"
              on: "child.{{ parent_field }} = h.id"
            where: "h.depth < {{ max_depth }}"

      - query:
          into: descendants
          select: "*"
          from: hierarchy
          order_by: "depth ASC"

      - return: descendants

# Usage
entity: AdministrativeUnit
uses_pattern: hierarchy_navigation
pattern_config:
  parent_field: fk_parent_administrative_unit
  max_depth: 10
```

---

#### 2.4 Audit Trail Pattern
```yaml
domain_pattern: audit_trail
description: Automatic change tracking with before/after snapshots
parameters:
  - entity: Entity to audit
  - tracked_fields: Fields to track changes
  - retention_days: How long to keep audit logs

implementation:
  # Auto-injected into all mutations
  after_mutation_hook:
    steps:
      - query:
          into: before_state
          select: "{{ tracked_fields | join(', ') }}"
          from: "tb_{{ entity }}"
          where: "id = $entity_id"

      # Mutation happens here

      - query:
          into: after_state
          select: "{{ tracked_fields | join(', ') }}"
          from: "tb_{{ entity }}"
          where: "id = $entity_id"

      - for_query:
          iterator: field
          query: "SELECT * FROM jsonb_each_text($before_state)"
          steps:
            - if:
                condition: "$before_state[$field.key] != $after_state[$field.key]"
                then:
                  - insert:
                      entity: "{{ entity }}AuditLog"
                      set:
                        entity_id: "$entity_id"
                        field_name: "$field.key"
                        old_value: "$before_state[$field.key]"
                        new_value: "$after_state[$field.key]"
                        changed_by: "$auth_user_id"
                        changed_at: "now()"

# Usage
entity: Contact
uses_pattern: audit_trail
pattern_config:
  tracked_fields: [email, phone, company, status]
  retention_days: 2555  # 7 years
```

---

#### 2.5 Soft Delete with Cascade Pattern
```yaml
domain_pattern: soft_delete_cascade
description: Soft delete with automatic cascade to related entities
parameters:
  - entity: Entity to soft delete
  - cascade_entities: Related entities to cascade
  - cascade_rules: How to cascade (nullify, restrict, cascade)

implementation:
  soft_delete_action:
    steps:
      - validate:
          expression: "$input.id IS NOT NULL"
          error: "id_required"

      - query:
          into: entity_data
          select: "*"
          from: "tb_{{ entity }}"
          where: "id = $input.id AND deleted_at IS NULL"

      - if:
          condition: "entity_data IS NULL"
          then:
            - return_early:
                error: "entity_not_found"

      # Check cascade restrictions
      {% for cascade in cascade_entities %}
      - if:
          condition: "{{ cascade.rule }} = 'restrict'"
          then:
            - query:
                into: related_count
                select: "COUNT(*)"
                from: "tb_{{ cascade.entity }}"
                where: "{{ cascade.fk }} = $input.id AND deleted_at IS NULL"

            - if:
                condition: "$related_count > 0"
                then:
                  - return_early:
                      error: "cannot_delete_has_references"
                      metadata:
                        related_entity: "{{ cascade.entity }}"
                        count: "$related_count"
      {% endfor %}

      # Perform cascade
      {% for cascade in cascade_entities %}
      - if:
          condition: "{{ cascade.rule }} = 'cascade'"
          then:
            - update:
                entity: "{{ cascade.entity }}"
                set:
                  deleted_at: "now()"
                  deleted_by: "$auth_user_id"
                where: "{{ cascade.fk }} = $input.id AND deleted_at IS NULL"

      - if:
          condition: "{{ cascade.rule }} = 'nullify'"
          then:
            - update:
                entity: "{{ cascade.entity }}"
                set:
                  "{{ cascade.fk }}": NULL
                where: "{{ cascade.fk }} = $input.id"
      {% endfor %}

      # Soft delete main entity
      - update:
          entity: "{{ entity }}"
          set:
            deleted_at: "now()"
            deleted_by: "$auth_user_id"
          where: "id = $input.id"

# Usage
entity: Company
uses_pattern: soft_delete_cascade
pattern_config:
  cascade_entities:
    - entity: Contact
      fk: fk_company
      rule: cascade
    - entity: Opportunity
      fk: fk_company
      rule: restrict
    - entity: Invoice
      fk: fk_company
      rule: nullify
```

---

#### 2.6 More Domain Patterns

- **Versioning Pattern**: Maintain entity version history
- **Tagging Pattern**: Flexible tagging system
- **Search Pattern**: Full-text search with ranking
- **Rate Limiting Pattern**: Request throttling
- **Idempotency Pattern**: Prevent duplicate operations
- **Bulk Import Pattern**: CSV/Excel import with validation
- **Export Pattern**: Generate reports in multiple formats
- **Notification Pattern**: Multi-channel notifications
- **Scheduling Pattern**: Cron-like scheduling
- **Locking Pattern**: Pessimistic/optimistic locking

---

## 🏢 Tier 3: Business Domain Entities (Industry Templates)

**Purpose**: Pre-built, industry-specific entity templates
**Analogy**: Like NPM packages, but for business entities
**Storage**: `entity_templates` table (new)
**Composition**: Built from Tier 2 domain patterns + Tier 1 primitives

### Database Schema

```sql
-- ============================================================================
-- Tier 2: Domain Patterns
-- ============================================================================

CREATE TABLE domain_patterns (
    pattern_id INTEGER PRIMARY KEY,
    pattern_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,              -- 'state_management', 'approval', 'hierarchy'
    tier TEXT DEFAULT 'tier_2',
    description TEXT,
    parameters JSONB NOT NULL,           -- Pattern parameters schema
    implementation TEXT NOT NULL,        -- YAML implementation using Tier 1
    dependencies TEXT,                   -- JSON array of required Tier 1 patterns
    complexity_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_domain_patterns_category ON domain_patterns(category);

-- Example: State Machine pattern
INSERT INTO domain_patterns VALUES (
    1,
    'state_machine',
    'state_management',
    'tier_2',
    'Manage entity state transitions with validation',
    '{"entity": "string", "states": "array", "transitions": "array", "guards": "object"}',
    '--- YAML implementation here ---',
    '["query", "validate", "update", "if"]',
    6,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- ============================================================================
-- Tier 3: Entity Templates (Business Domains)
-- ============================================================================

CREATE TABLE business_domains (
    domain_id INTEGER PRIMARY KEY,
    domain_name TEXT NOT NULL UNIQUE,    -- 'crm', 'ecommerce', 'healthcare'
    domain_category TEXT,                -- 'sales', 'commerce', 'medical'
    description TEXT,
    icon TEXT,                           -- Icon for UI
    documentation_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE entity_templates (
    template_id INTEGER PRIMARY KEY,
    domain_id INTEGER NOT NULL,
    entity_name TEXT NOT NULL,           -- 'Contact', 'Product', 'Patient'
    template_code TEXT NOT NULL,         -- 'crm.contact', 'ecommerce.product'
    description TEXT,
    fields JSONB NOT NULL,               -- Field definitions
    domain_patterns JSONB,               -- Which Tier 2 patterns to use
    custom_actions JSONB,                -- Additional custom actions
    relationships JSONB,                 -- Relationships to other entities
    icon TEXT,
    tags TEXT,                           -- 'popular', 'essential', 'advanced'
    downloads INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_id) REFERENCES business_domains(domain_id),
    UNIQUE (template_code)
);

CREATE INDEX idx_entity_templates_domain ON entity_templates(domain_id);
CREATE INDEX idx_entity_templates_tags ON entity_templates(tags);

-- ============================================================================
-- Template Instantiation (User's entities from templates)
-- ============================================================================

CREATE TABLE user_entities (
    user_entity_id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,               -- User/organization ID
    entity_name TEXT NOT NULL,
    template_id INTEGER,                 -- NULL if custom entity
    customizations JSONB,                -- Overrides from template
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES entity_templates(template_id),
    UNIQUE (user_id, entity_name)
);
```

---

### Business Domain: CRM

```sql
-- CRM Domain
INSERT INTO business_domains VALUES (
    1,
    'crm',
    'sales',
    'Customer Relationship Management - manage contacts, companies, and sales pipeline',
    '🤝',
    'https://docs.specql.io/domains/crm',
    CURRENT_TIMESTAMP
);

-- Contact Template
INSERT INTO entity_templates VALUES (
    1,
    1,  -- CRM domain
    'Contact',
    'crm.contact',
    'Individual person with contact information and relationships',
    '{
        "email": {"type": "email", "required": true, "unique": true},
        "first_name": {"type": "text", "required": true},
        "last_name": {"type": "text", "required": true},
        "phone": {"type": "phone"},
        "company": {"type": "ref(Company)"},
        "status": {"type": "enum", "values": ["lead", "prospect", "customer", "inactive"]},
        "lifecycle_stage": {"type": "enum", "values": ["subscriber", "lead", "mql", "sql", "opportunity", "customer", "evangelist"]},
        "source": {"type": "enum", "values": ["website", "referral", "advertising", "social", "event", "cold_call"]},
        "owner": {"type": "ref(User)"},
        "tags": {"type": "list(text)"}
    }',
    '{
        "state_machine": {
            "states": ["lead", "prospect", "customer", "inactive"],
            "transitions": [
                ["lead", "prospect"],
                ["prospect", "customer"],
                ["customer", "inactive"],
                ["inactive", "prospect"]
            ],
            "guards": {
                "lead->prospect": "email_verified = true",
                "prospect->customer": "deal_closed = true"
            }
        },
        "audit_trail": {
            "tracked_fields": ["email", "phone", "company", "status", "owner"]
        },
        "soft_delete_cascade": {
            "cascade_entities": [
                {"entity": "Activity", "fk": "fk_contact", "rule": "cascade"},
                {"entity": "Opportunity", "fk": "fk_contact", "rule": "nullify"}
            ]
        }
    }',
    '{
        "qualify_lead": {
            "description": "Mark lead as qualified prospect",
            "uses_pattern": "state_machine.transition",
            "config": {"target_state": "prospect"}
        },
        "convert_to_customer": {
            "description": "Convert prospect to customer",
            "uses_pattern": "state_machine.transition",
            "config": {"target_state": "customer"}
        },
        "merge_contacts": {
            "description": "Merge duplicate contacts",
            "steps": ["custom_merge_logic"]
        }
    }',
    '{
        "company": {"type": "many_to_one", "entity": "Company"},
        "opportunities": {"type": "one_to_many", "entity": "Opportunity"},
        "activities": {"type": "one_to_many", "entity": "Activity"},
        "owner": {"type": "many_to_one", "entity": "User"}
    }',
    '👤',
    'popular,essential',
    15420,
    4.8,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Company Template
INSERT INTO entity_templates VALUES (
    2,
    1,  -- CRM domain
    'Company',
    'crm.company',
    'Organization with multiple contacts and business relationships',
    '{
        "name": {"type": "text", "required": true},
        "website": {"type": "url"},
        "industry": {"type": "enum", "values": ["technology", "finance", "healthcare", "manufacturing", "retail", "other"]},
        "size": {"type": "enum", "values": ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]},
        "annual_revenue": {"type": "money"},
        "address": {"type": "composite(Address)"},
        "owner": {"type": "ref(User)"}
    }',
    '{
        "hierarchy_navigation": {
            "parent_field": "fk_parent_company",
            "max_depth": 5
        },
        "audit_trail": {
            "tracked_fields": ["name", "industry", "annual_revenue", "owner"]
        }
    }',
    '{
        "add_subsidiary": {
            "description": "Add subsidiary company",
            "uses_pattern": "hierarchy_navigation.add_child"
        },
        "calculate_total_revenue": {
            "description": "Sum revenue across all subsidiaries",
            "uses_pattern": "hierarchy_navigation.aggregate_descendants"
        }
    }',
    '{
        "parent_company": {"type": "many_to_one", "entity": "Company"},
        "subsidiaries": {"type": "one_to_many", "entity": "Company"},
        "contacts": {"type": "one_to_many", "entity": "Contact"},
        "opportunities": {"type": "one_to_many", "entity": "Opportunity"}
    }',
    '🏢',
    'popular,essential',
    12890,
    4.7,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Opportunity Template
INSERT INTO entity_templates VALUES (
    3,
    1,  -- CRM domain
    'Opportunity',
    'crm.opportunity',
    'Sales opportunity with pipeline stage tracking',
    '{
        "name": {"type": "text", "required": true},
        "amount": {"type": "money", "required": true},
        "close_date": {"type": "date", "required": true},
        "stage": {"type": "enum", "values": ["qualification", "needs_analysis", "proposal", "negotiation", "closed_won", "closed_lost"]},
        "probability": {"type": "integer", "min": 0, "max": 100},
        "contact": {"type": "ref(Contact)"},
        "company": {"type": "ref(Company)"},
        "owner": {"type": "ref(User)"}
    }',
    '{
        "state_machine": {
            "states": ["qualification", "needs_analysis", "proposal", "negotiation", "closed_won", "closed_lost"],
            "transitions": [
                ["qualification", "needs_analysis"],
                ["needs_analysis", "proposal"],
                ["proposal", "negotiation"],
                ["negotiation", "closed_won"],
                ["negotiation", "closed_lost"]
            ]
        },
        "approval_workflow": {
            "approval_levels": 2,
            "approver_roles": {
                "1": ["sales_manager"],
                "2": ["vp_sales"]
            },
            "trigger_condition": "amount > 50000"
        }
    }',
    '{}',
    '{
        "contact": {"type": "many_to_one", "entity": "Contact"},
        "company": {"type": "many_to_one", "entity": "Company"},
        "owner": {"type": "many_to_one", "entity": "User"}
    }',
    '💰',
    'popular',
    8930,
    4.6,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

---

### Business Domain: E-Commerce

```sql
-- E-Commerce Domain
INSERT INTO business_domains VALUES (
    2,
    'ecommerce',
    'commerce',
    'Online store with products, orders, and inventory management',
    '🛒',
    'https://docs.specql.io/domains/ecommerce',
    CURRENT_TIMESTAMP
);

-- Product Template
INSERT INTO entity_templates VALUES (
    10,
    2,  -- E-Commerce domain
    'Product',
    'ecommerce.product',
    'Product catalog item with variants and pricing',
    '{
        "name": {"type": "text", "required": true},
        "sku": {"type": "text", "required": true, "unique": true},
        "description": {"type": "rich_text"},
        "price": {"type": "money", "required": true},
        "cost": {"type": "money"},
        "category": {"type": "ref(Category)"},
        "inventory_quantity": {"type": "integer", "default": 0},
        "low_stock_threshold": {"type": "integer", "default": 10},
        "status": {"type": "enum", "values": ["draft", "active", "archived"]},
        "images": {"type": "list(url)"},
        "tags": {"type": "list(text)"}
    }',
    '{
        "state_machine": {
            "states": ["draft", "active", "archived"],
            "transitions": [
                ["draft", "active"],
                ["active", "archived"],
                ["archived", "active"]
            ]
        },
        "versioning": {
            "tracked_fields": ["price", "cost", "description"]
        },
        "notification": {
            "events": {
                "low_stock": "inventory_quantity < low_stock_threshold",
                "out_of_stock": "inventory_quantity = 0"
            }
        }
    }',
    '{
        "adjust_inventory": {
            "description": "Adjust inventory quantity",
            "steps": [
                {"validate": "adjustment_quantity != 0"},
                {"update": "Product SET inventory_quantity = inventory_quantity + $adjustment"}
            ]
        },
        "apply_discount": {
            "description": "Apply temporary discount",
            "uses_pattern": "versioning.create_version",
            "steps": [
                {"assign": "original_price = $product.price"},
                {"update": "Product SET price = $original_price * (1 - $discount_percent)"}
            ]
        }
    }',
    '{
        "category": {"type": "many_to_one", "entity": "Category"},
        "variants": {"type": "one_to_many", "entity": "ProductVariant"},
        "reviews": {"type": "one_to_many", "entity": "Review"}
    }',
    '📦',
    'popular,essential',
    18750,
    4.9,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Order Template
INSERT INTO entity_templates VALUES (
    11,
    2,  -- E-Commerce domain
    'Order',
    'ecommerce.order',
    'Customer order with items and fulfillment tracking',
    '{
        "order_number": {"type": "text", "required": true, "unique": true},
        "customer": {"type": "ref(Customer)"},
        "status": {"type": "enum", "values": ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"]},
        "subtotal": {"type": "money", "required": true},
        "tax": {"type": "money"},
        "shipping": {"type": "money"},
        "total": {"type": "money", "required": true},
        "shipping_address": {"type": "composite(Address)"},
        "billing_address": {"type": "composite(Address)"},
        "payment_method": {"type": "enum", "values": ["credit_card", "debit_card", "paypal", "bank_transfer", "cash"]},
        "payment_status": {"type": "enum", "values": ["pending", "authorized", "captured", "failed", "refunded"]}
    }',
    '{
        "state_machine": {
            "states": ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"],
            "transitions": [
                ["pending", "confirmed"],
                ["pending", "cancelled"],
                ["confirmed", "processing"],
                ["confirmed", "cancelled"],
                ["processing", "shipped"],
                ["shipped", "delivered"],
                ["delivered", "refunded"]
            ],
            "guards": {
                "pending->confirmed": "payment_status = \\'captured\\'",
                "processing->shipped": "all_items_packed = true"
            }
        },
        "notification": {
            "events": {
                "order_confirmed": "status = \\'confirmed\\'",
                "order_shipped": "status = \\'shipped\\'",
                "order_delivered": "status = \\'delivered\\'"
            },
            "channels": ["email", "sms"]
        }
    }',
    '{
        "calculate_totals": {
            "description": "Recalculate order totals",
            "steps": [
                {"aggregate": "SELECT SUM(quantity * price) FROM OrderItem WHERE order_id = $id INTO subtotal"},
                {"assign": "tax = $subtotal * $tax_rate"},
                {"assign": "total = $subtotal + $tax + $shipping"},
                {"update": "Order SET subtotal, tax, total"}
            ]
        },
        "process_refund": {
            "description": "Process full or partial refund",
            "uses_pattern": "state_machine.transition",
            "config": {"target_state": "refunded"},
            "additional_steps": [
                {"call_function": "payment_gateway.refund", "args": {"amount": "$refund_amount"}}
            ]
        }
    }',
    '{
        "customer": {"type": "many_to_one", "entity": "Customer"},
        "items": {"type": "one_to_many", "entity": "OrderItem"},
        "shipments": {"type": "one_to_many", "entity": "Shipment"}
    }',
    '🛍️',
    'popular,essential',
    14200,
    4.7,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

---

### Business Domain: Healthcare

```sql
-- Healthcare Domain
INSERT INTO business_domains VALUES (
    3,
    'healthcare',
    'medical',
    'Patient management, appointments, and medical records',
    '🏥',
    'https://docs.specql.io/domains/healthcare',
    CURRENT_TIMESTAMP
);

-- Patient Template
INSERT INTO entity_templates VALUES (
    20,
    3,  -- Healthcare domain
    'Patient',
    'healthcare.patient',
    'Patient with medical history and appointments',
    '{
        "medical_record_number": {"type": "text", "required": true, "unique": true},
        "first_name": {"type": "text", "required": true},
        "last_name": {"type": "text", "required": true},
        "date_of_birth": {"type": "date", "required": true},
        "gender": {"type": "enum", "values": ["male", "female", "other", "prefer_not_to_say"]},
        "email": {"type": "email"},
        "phone": {"type": "phone", "required": true},
        "address": {"type": "composite(Address)"},
        "emergency_contact": {"type": "composite(EmergencyContact)"},
        "insurance_info": {"type": "composite(InsuranceInfo)"},
        "primary_physician": {"type": "ref(Physician)"},
        "status": {"type": "enum", "values": ["active", "inactive", "deceased"]}
    }',
    '{
        "audit_trail": {
            "tracked_fields": ["*"],
            "retention_days": 3650,
            "hipaa_compliant": true
        },
        "access_control": {
            "roles": {
                "physician": ["read", "write"],
                "nurse": ["read", "write_limited"],
                "admin": ["read"],
                "patient": ["read_own"]
            }
        },
        "versioning": {
            "tracked_fields": ["address", "phone", "insurance_info"],
            "retain_all_versions": true
        }
    }',
    '{
        "schedule_appointment": {
            "description": "Schedule patient appointment",
            "steps": [
                {"validate": "appointment_time > now()"},
                {"validate": "physician_available($physician_id, $appointment_time)"},
                {"insert": "Appointment SET patient, physician, datetime, type"}
            ]
        },
        "add_diagnosis": {
            "description": "Add diagnosis to patient record",
            "uses_pattern": "versioning.create_version",
            "steps": [
                {"validate": "auth_user.role IN [\\'physician\\', \\'specialist\\']"},
                {"insert": "Diagnosis SET patient, icd_code, description, diagnosed_by, diagnosed_at"}
            ]
        }
    }',
    '{
        "primary_physician": {"type": "many_to_one", "entity": "Physician"},
        "appointments": {"type": "one_to_many", "entity": "Appointment"},
        "diagnoses": {"type": "one_to_many", "entity": "Diagnosis"},
        "prescriptions": {"type": "one_to_many", "entity": "Prescription"}
    }',
    '🩺',
    'essential',
    5400,
    4.9,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

---

## 🎯 Usage: Three-Tier Composition

### Example: Create CRM Contact from Template

```yaml
# Step 1: Use template from Tier 3
entity: Contact
from_template: crm.contact

# Step 2: Template automatically includes Tier 2 patterns
# - state_machine (for lead → prospect → customer)
# - audit_trail (track all changes)
# - soft_delete_cascade (cascade to activities)

# Step 3: Patterns use Tier 1 primitives
# - declare, query, update, if, foreach, etc.

# Customizations (optional)
customize:
  fields:
    # Add custom field
    linkedin_profile: url

  actions:
    # Override default action with custom logic
    qualify_lead:
      steps:
        - validate: email_verified = true
        - validate: phone_verified = true
        - call_function: credit_check
          args: {company: $company}
        - uses_pattern: state_machine.transition
          config: {target_state: "prospect"}
```

**What happens**:
1. ✅ Template provides: fields, relationships, domain patterns
2. ✅ Domain patterns provide: state_machine, audit_trail, soft_delete
3. ✅ Patterns use: query, validate, update, if (Tier 1 primitives)
4. ✅ Code generated for: PostgreSQL, Python, TypeScript, Ruby, etc.

---

## 🎯 CLI for Three-Tier System

```bash
# ============================================================================
# Tier 1: Primitive Actions (Developer-facing)
# ============================================================================

# List available primitives
specql primitives list --category query
# Output: query, cte, aggregate, subquery, join

# Add new primitive
specql primitives add window_function \
  --category query \
  --implementation postgresql "{{ expression }} OVER ({{ window_spec }})"

# ============================================================================
# Tier 2: Domain Patterns (Power Users)
# ============================================================================

# List domain patterns
specql patterns list --category state_management
# Output:
# - state_machine: Manage state transitions
# - workflow: Multi-step workflows
# - saga: Distributed transactions

# Inspect pattern
specql patterns show state_machine
# Output: Parameters, implementation, dependencies, usage examples

# Create custom pattern
specql patterns create my_approval_workflow \
  --based-on approval_workflow \
  --customize levels=5

# ============================================================================
# Tier 3: Business Entities (End Users - Non-Developers)
# ============================================================================

# Browse available domains
specql domains list
# Output:
# 🤝 CRM (15 entities)
# 🛒 E-Commerce (12 entities)
# 🏥 Healthcare (18 entities)
# 📚 Education (10 entities)
# 🏦 Finance (20 entities)

# Browse entities in domain
specql entities list --domain crm
# Output:
# 👤 Contact (★4.8, 15.4k downloads)
# 🏢 Company (★4.7, 12.9k downloads)
# 💰 Opportunity (★4.6, 8.9k downloads)
# 📅 Activity (★4.5, 7.2k downloads)

# Show entity details
specql entities show crm.contact
# Output:
# Contact - Individual person with contact information
#
# Fields:
#   - email (email, required, unique)
#   - first_name (text, required)
#   - company (ref(Company))
#   - status (enum: lead, prospect, customer)
#
# Domain Patterns:
#   - state_machine: lead → prospect → customer
#   - audit_trail: Track all changes
#   - soft_delete_cascade: Cascade to activities
#
# Actions:
#   - qualify_lead: Mark lead as qualified
#   - convert_to_customer: Convert to customer
#   - merge_contacts: Merge duplicates
#
# Relationships:
#   - company: many-to-one Company
#   - opportunities: one-to-many Opportunity

# Create entity from template
specql create entity Contact --from crm.contact

# Creates: entities/contact.yaml with template content

# Customize and generate
specql generate entities/contact.yaml --languages postgresql,python

# ============================================================================
# Package Management
# ============================================================================

# Search for entities
specql search "customer management"
# Output: crm.contact, crm.company, crm.customer, ...

# Install entity pack
specql install crm-starter-pack
# Installs: Contact, Company, Opportunity, Activity

# Create from multiple templates
specql init --domain crm --entities contact,company,opportunity

# ============================================================================
# Analytics
# ============================================================================

# Popular templates
specql trending --timeframe week
# 1. crm.contact (+420 installs)
# 2. ecommerce.product (+380 installs)
# 3. ecommerce.order (+350 installs)

# Domain coverage
specql coverage --domain crm
# Contact: ✅ Complete (state_machine, audit_trail, soft_delete)
# Company: ⚠️  Partial (missing approval_workflow)
# Opportunity: ✅ Complete
```

---

## 🎓 Benefits of Three-Tier Architecture

### 1. **Separation of Concerns**
- **Tier 1**: Language primitives (developer concern)
- **Tier 2**: Business patterns (architect concern)
- **Tier 3**: Domain entities (business user concern)

### 2. **Composability**
```
CRM Contact (Tier 3)
    ↓ uses
State Machine Pattern (Tier 2)
    ↓ uses
query, validate, update (Tier 1)
    ↓ compiles to
PostgreSQL, Python, TypeScript, Ruby...
```

### 3. **Reusability**
- **Tier 1**: Reused across all patterns and entities
- **Tier 2**: Reused across multiple domains
- **Tier 3**: Industry-specific, ready to use

### 4. **Marketplace Potential**
```
NPM for Business Logic
├── Free Tier
│   └── Basic entities (Contact, Product, Order)
├── Premium Tier
│   └── Advanced patterns (Approval workflow, State machine)
└── Enterprise Tier
    └── Industry packs (Healthcare HIPAA, Finance SOX)
```

### 5. **Learning Curve**
- **Beginners**: Start with Tier 3 templates
- **Intermediate**: Customize with Tier 2 patterns
- **Advanced**: Create new Tier 1 primitives

### 6. **AI Code Generation**
```python
# AI prompt: "Create a CRM system"

# AI queries Tier 3
entities = library.search_domain("crm")
# → [Contact, Company, Opportunity, Activity]

# AI generates
for entity in entities:
    specql_yaml = library.instantiate_template(entity)
    code = library.generate(specql_yaml, "postgresql")
```

---

## 📊 Database Query Examples

### Find Entities Using Specific Pattern
```sql
SELECT
    et.entity_name,
    et.template_code,
    et.description,
    bd.domain_name
FROM entity_templates et
JOIN business_domains bd ON bd.domain_id = et.domain_id
WHERE et.domain_patterns->>'state_machine' IS NOT NULL;
```

### Pattern Popularity
```sql
SELECT
    dp.pattern_name,
    dp.category,
    COUNT(et.template_id) as used_by_entities
FROM domain_patterns dp
LEFT JOIN entity_templates et ON et.domain_patterns ? dp.pattern_name
GROUP BY dp.pattern_id, dp.pattern_name, dp.category
ORDER BY used_by_entities DESC;
```

### Domain Completeness
```sql
SELECT
    bd.domain_name,
    COUNT(et.template_id) as total_entities,
    AVG(et.rating) as avg_rating,
    SUM(et.downloads) as total_downloads
FROM business_domains bd
LEFT JOIN entity_templates et ON et.domain_id = bd.domain_id
GROUP BY bd.domain_id, bd.domain_name
ORDER BY total_downloads DESC;
```

---

## ✅ Implementation Roadmap

### Phase C1: Domain Patterns Library (3 weeks)
**Deliverables**:
- `domain_patterns` table schema
- 15 domain patterns (state_machine, approval, hierarchy, etc.)
- Pattern → Tier 1 primitives compiler
- Pattern testing framework

### Phase C2: Entity Templates (4 weeks)
**Deliverables**:
- `business_domains` and `entity_templates` tables
- CRM domain (5 entities)
- E-Commerce domain (5 entities)
- Healthcare domain (5 entities)
- Template instantiation engine

### Phase C3: Package Manager (2 weeks)
**Deliverables**:
- Entity search and discovery
- Template installation
- Version management
- Community contributions

### Phase C4: Marketplace (3 weeks)
**Deliverables**:
- Web interface for browsing
- Rating and reviews
- Premium templates
- Analytics dashboard

**Total Effort**: 12 weeks

---

## 🎯 Combined Architecture

### Complete System (All Tracks)

```
YAML (User Input)
    ↓
Tier 3: Entity Templates (healthcare.patient)
    ↓
Tier 2: Domain Patterns (audit_trail, versioning)
    ↓
Tier 1: Primitives (query, update, foreach)
    ↓
Pattern Library Database (SQLite)
    ├── Pattern Implementations
    ├── Type Mappings
    └── Expression Syntax
    ↓
Code Generators (Per Language)
    ├── PostgreSQL
    ├── Python (Django)
    ├── TypeScript (Prisma)
    └── Ruby (Rails)
    ↓
Generated Code
```

---

## ✅ Final Recommendation

**PROCEED with Three-Tier Architecture**

**Combined Implementation**:
- **Track A**: DSL Expansion (7 weeks) → Tier 1 primitives
- **Track B**: Pattern Library (10 weeks) → Database + multi-language
- **Track C**: Domain Patterns + Templates (12 weeks) → Tier 2 + Tier 3

**Total Effort**: 29 weeks (tracks can overlap)
**Result**: Universal, composable, marketplace-ready code generation platform

**Strategic Value**:
- SpecQL becomes **NPM for business logic**
- Community-driven growth
- AI-friendly code generation
- Industry-specific solutions

---

**Last Updated**: 2025-11-12
**Status**: Three-Tier Architecture Complete
**Vision**: Composable business logic from primitives to industries
