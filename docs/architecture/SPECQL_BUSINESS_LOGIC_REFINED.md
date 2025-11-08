# SpecQL Business Logic - Refined YAML Schema

**Date**: November 8, 2025
**Context**: Integration with SpecQL language for FraiseQL
**Key Insight**: Framework handles boilerplate, YAML focuses on **business rules only**

---

## Executive Summary

After reviewing SpecQL language design, we can significantly **simplify the YAML schema** by leveraging framework-level features:

### **Framework Handles (SpecQL Layer)**
- ✅ CRUD generation
- ✅ Permission checks (`requires: caller.has_permission(...)`)
- ✅ Audit logging (`audit: required`)
- ✅ Event emission (`emit: event(...)`)
- ✅ Notifications (`notify: user(email, ...)`)
- ✅ Change detection (automatic)
- ✅ Response structure (standard mutation_result)
- ✅ Exception handling (standard patterns)

### **YAML Focuses On (Business Layer)**
- 🎯 **Entity relationships** (refs, cascades)
- 🎯 **Business validations** (domain rules)
- 🎯 **Workflow steps** (multi-step actions)
- 🎯 **Conflict detection** (domain-specific overlaps)
- 🎯 **Conditional logic** (if/then business rules)
- 🎯 **AI agents** (domain-specific automation)

**Result**: 70% reduction in YAML verbosity, clearer separation of concerns.

---

## 🎯 SpecQL Language Features (from /tmp/ analysis)

### **Built-in Framework Capabilities**

```yaml
# SpecQL provides these automatically:

entity: Task
  fields:
    title: text
    assignee: ref(User)
    status: enum(todo, in_progress, done)

  actions:
    - name: create_task
      # ✅ AUTO: validate inputs (type checking)
      # ✅ AUTO: check permissions (caller context)
      # ✅ AUTO: generate INSERT query
      # ✅ AUTO: emit event('task.created')
      # ✅ AUTO: return mutation_result
      # ✅ AUTO: log to audit trail
      steps:
        - validate: title.length >= 3        # BUSINESS RULE
        - insert: Task                       # FRAMEWORK ACTION
        - notify: assignee(email, 'Task assigned')  # FRAMEWORK ACTION

    - name: move_task
      requires: caller.is_owner OR caller.has_role('admin')  # FRAMEWORK
      steps:
        - validate: new_status IN allowed_transitions(current_status)  # BUSINESS RULE
        - update: status = new_status       # FRAMEWORK ACTION
        - if: new_status == 'done'          # BUSINESS LOGIC
          then: increment(assignee.tasks_completed)  # FRAMEWORK ACTION
```

### **What This Means**

**Framework provides:**
- Type validation
- Permission checks
- Standard mutations (insert/update/delete)
- Event emission
- Notifications
- Audit logging
- Response formatting
- Exception handling

**YAML only specifies:**
- Business-specific validation rules
- Domain-specific workflows
- Custom conflict detection
- Conditional business logic

---

## 📋 Revised YAML Schema (Business-Focused)

### **Example 1: Machine Item (Simplified)**

**Before (Framework + Business Mixed - 200+ lines):**
```yaml
entity:
  name: machine_item
  business_logic:
    validations: [15 validation rules]
    existence_checks: [5 existence checks]
    conflict_detection: [3 conflict rules]
    nested_creation: [order creation logic]
    side_effects: [charge insertion]
    cascade_updates: [3 refresh operations]
    exception_handling: [4 exception types]
    response_structure: [complex response]
```

**After (Business-Only - 40 lines):**
```yaml
entity: MachineItem
  fields:
    machine: ref(Machine)
    source_type: enum(MachineItem, ContractItem, Product)
    source_id: uuid
    order: ref(Order)
    installed_at: timestamp

  actions:
    - name: create_machine_item
      # Framework auto-validates types, permissions, logs, etc.

      steps:
        # Business rule: order_id and order_data are mutually exclusive
        - validate: NOT (order_id IS NOT NULL AND order_data IS NOT NULL)
          error: "conflicting_order_fields"

        # Business rule: Product cannot have orders
        - validate: NOT (source_type = 'Product' AND (order_id IS NOT NULL OR order_data IS NOT NULL))
          error: "invalid_order_usage_with_product"

        # Business rule: nested order creation
        - if: order_data IS NOT NULL
          then:
            - call: create_order(order_data)
            - set: order_id = result.id

        # Business rule: resolve source entity
        - switch: source_type
          cases:
            MachineItem:
              - validate: source.fk_machine IS NULL
                error: "machine_item_already_allocated"
              - update: source SET fk_machine = input.machine_id

            ContractItem:
              - fetch: source AS contract_item
              - set: fk_product = contract_item.fk_product
              - insert: MachineItem

            Product:
              - set: fk_product = source_id
              - insert: MachineItem

        # Business rule: conditional charge creation
        - if: source_type != 'Product'
          then:
            - compute: charge_end_date = resolve_machine_cost_period_end_date(...)
            - validate: installed_at <= charge_end_date
              error: "installation_date_incompatible_with_contract"
            - call: insert_machine_item_charge(...)

      # Framework handles: emit event, notify, audit log, return response
```

**Reduction: 200 lines → 40 lines (80% less YAML)**

---

### **Example 2: Reservation (Simplified)**

**Before (Framework + Business Mixed - 250+ lines)**

**After (Business-Only - 60 lines):**
```yaml
entity: Reservation
  table: allocation  # Stored in allocation table
  fields:
    machine: ref(Machine)
    reserved_from: date
    reserved_until: date
    organizational_unit: ref(OrganizationalUnit)
    location: ref(Location)
    is_provisionnal: boolean = true

  actions:
    - name: create_reservation
      # Framework: type checks, permission checks, audit log

      steps:
        # Business rule: date range validation
        - validate: reserved_from <= reserved_until
          error: "invalid_date_range"
        - validate: reserved_from >= CURRENT_DATE
          error: "past_date_not_allowed"

        # Business rule: resolve defaults
        - default: reserved_from = CURRENT_DATE + 1 year
        - default: reserved_until = '2099-12-31'
        - default: organizational_unit = get_or_create_ou_for_reservation(...)
        - default: location = get_legal_location(organization)

        # Business rule: conflict detection (temporal overlap)
        - validate: NOT EXISTS (
            SELECT 1 FROM allocation
            WHERE fk_machine = input.machine_id
              AND is_provisionnal = TRUE
              AND daterange(start_date, end_date) && daterange(reserved_from, reserved_until)
          )
          error: "overlapping_reservation_exists"
          context:
            - conflict_reservation: tv_allocation WHERE overlap
            - context_machine: tv_machine WHERE id = machine_id

        # Business rule: temporal continuity (close current allocation)
        - find: current_allocation WHERE
            fk_machine = input.machine_id AND
            is_provisionnal = FALSE AND
            start_date <= CURRENT_DATE AND
            end_date >= reserved_from
        - update: current_allocation SET
            end_date = reserved_from - 1 day,
            is_current = recalculate(...)

        # Business rule: insert reservation
        - insert: Allocation(
            machine = input.machine,
            start_date = reserved_from,
            end_date = reserved_until,
            is_provisionnal = true,
            is_stock = false
          )

        # Business rule: update machine flags
        - update: tv_machine SET data->is_reserved = true
          WHERE id = input.machine_id

      # Framework handles: event emission, notifications, response
```

**Reduction: 250 lines → 60 lines (76% less YAML)**

---

### **Example 3: Allocation (Simplified)**

**Before (Framework + Business Mixed - 180 lines)**

**After (Business-Only - 45 lines):**
```yaml
entity: Allocation
  fields:
    machine: ref(Machine)
    organizational_unit: ref(OrganizationalUnit)
    location: ref(Location)
    start_date: date
    end_date: date
    is_provisionnal: boolean = false

  actions:
    - name: create_allocation
      steps:
        # Business rule: check for identical current allocation
        - if: EXISTS current_allocation WITH same orgunit AND location
          then: reject("current_allocation_is_the_same")

        # Business rule: handle future provisional allocations
        - find: future_allocations WHERE
            fk_machine = input.machine AND
            start_date > input.start_date AND
            is_provisionnal = TRUE
        - if: future_allocations EXISTS AND NOT input.delete_future_allocations
          then: reject("future_allocations_exist")
        - if: input.delete_future_allocations
          then: delete(future_allocations)

        # Business rule: adjust neighboring allocations
        - call: adjust_allocation_neighbors(
            machine = input.machine,
            new_start = input.start_date,
            new_end = input.end_date
          )

        # Business rule: insert allocation
        - insert: Allocation(...)

        # Business rule: update temporal flags
        - call: update_allocation_flags(machine = input.machine)

      on_error:
        overlapping_allocation:
          error: "overlapping"
          context: conflict_allocation

    - name: update_allocation
      steps:
        # Business rule: detect what changed
        - detect_changes: [location, organizational_unit, start_date, end_date]
        - if: no_changes
          then: reject("noop:no_changes")

        # Business rule: conditional neighbor adjustment
        - if: start_date changed OR end_date changed
          then: call(adjust_allocation_neighbors(...))

        # Business rule: apply update
        - update: Allocation SET changed_fields

        # Business rule: recalculate temporal fields
        - update: Allocation SET
            is_past = (end_date < CURRENT_DATE),
            is_current = (start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE),
            is_future = (start_date > CURRENT_DATE)
```

**Reduction: 180 lines → 45 lines (75% less YAML)**

---

## 🏗️ Refined YAML Schema Structure

### **Top-Level (Entity Definition)**

```yaml
entity: EntityName
  # === Database Mapping ===
  table: string                    # Optional: if different from entity name
  schema: string                   # PostgreSQL schema
  description: string

  # === Fields (Standard) ===
  fields:
    field_name: type               # Simple field
    field_name: ref(Entity)        # Foreign key reference
    field_name: list(ref(Entity))  # Many-to-many
    field_name: enum(val1, val2)   # Enumeration
    field_name: type = default     # With default value

  # === Indexes (Optional) ===
  indexes:
    - columns: [field1, field2]
      type: btree | gin | gist

  # === Business Actions ===
  actions:
    - name: action_name
      requires: permission_expression   # Framework: permission check
      steps: [...]                      # Business logic steps

  # === AI Agents (Optional) ===
  agents:
    - name: agent_name
      type: ai_llm | rule_based
      observes: [event1, event2]
      can_execute: [action1, action2]
      strategy: |
        Business strategy description
      audit: required
```

---

### **Action Step DSL (Business Logic)**

```yaml
steps:
  # === VALIDATION (Business Rules) ===
  - validate: expression
    error: "error_code"
    context: {...}                    # Optional context for error

  # === CONDITIONAL LOGIC ===
  - if: condition
    then: [steps]
    else: [steps]                     # Optional

  - switch: field
    cases:
      value1: [steps]
      value2: [steps]

  # === DATA RETRIEVAL ===
  - find: entity WHERE conditions    # Find existing entity
  - fetch: entity AS variable        # Load entity data

  # === COMPUTATION ===
  - compute: variable = expression   # Calculate value
  - set: variable = value            # Set variable

  # === DEFAULT VALUES ===
  - default: field = expression      # Set if NULL

  # === DATABASE OPERATIONS ===
  - insert: Entity(fields)           # Framework handles INSERT
  - update: entity SET fields        # Framework handles UPDATE
  - delete: entity                   # Framework handles DELETE

  # === FUNCTION CALLS ===
  - call: function_name(args)        # Call PostgreSQL function
    store: variable_name              # Optional: store result

  # === NESTED OPERATIONS ===
  - increment: field                 # Increment counter
  - decrement: field                 # Decrement counter

  # === FRAMEWORK ACTIONS (Auto-Added) ===
  # emit: event(...)                 # Framework adds automatically
  # notify: user(...)                # Framework adds automatically
  # log: audit(...)                  # Framework adds automatically
```

---

## 📊 Framework vs Business Logic Split

### **Framework Responsibilities (Auto-Generated)**

| Feature | SpecQL Framework Handles | YAML Specifies |
|---------|-------------------------|----------------|
| **Type Validation** | ✅ Auto (field types) | Nothing |
| **Permission Checks** | ✅ Auto (requires: ...) | Permission expression |
| **Existence Checks** | ✅ Auto (ref(...) validation) | Nothing |
| **CRUD Operations** | ✅ Auto (insert/update/delete) | Entity + fields |
| **Event Emission** | ✅ Auto (entity.action) | Nothing |
| **Notifications** | ✅ Auto (notify: ...) | Recipients + message |
| **Audit Logging** | ✅ Auto (all mutations) | Nothing |
| **Response Format** | ✅ Auto (mutation_result) | Nothing |
| **Exception Handling** | ✅ Auto (standard errors) | Custom error codes |
| **Change Detection** | ✅ Auto (track fields) | Nothing |
| **GraphQL Generation** | ✅ Auto (types + mutations) | Nothing |
| **TypeScript Types** | ✅ Auto (codegen) | Nothing |

### **Business Logic Responsibilities (YAML)**

| Feature | Business Logic Handles | Framework Assists |
|---------|----------------------|-------------------|
| **Business Validations** | 🎯 YAML (validate: ...) | Error formatting |
| **Conflict Detection** | 🎯 YAML (EXISTS queries) | Query execution |
| **Conditional Workflows** | 🎯 YAML (if/switch) | Step execution |
| **Multi-Step Actions** | 🎯 YAML (steps: [...]) | Transaction mgmt |
| **Temporal Logic** | 🎯 YAML (date comparisons) | Date functions |
| **Neighbor Adjustment** | 🎯 YAML (find + update) | Query execution |
| **Nested Creation** | 🎯 YAML (call: create_...) | Function call |
| **Default Resolution** | 🎯 YAML (default: ...) | NULL handling |
| **Computed Values** | 🎯 YAML (compute: ...) | Expression eval |
| **AI Agents** | 🎯 YAML (strategy) | Agent runtime |

**Key Insight**: Framework handles **how** (infrastructure), YAML specifies **what** (business rules).

---

## 💡 Complete Example: CRM Contact (SpecQL Style)

```yaml
entity: Contact
  schema: crm
  description: "Customer contact with lead scoring"

  fields:
    first_name: text
    last_name: text
    email: text
    phone: text
    company: ref(Company)
    owner: ref(User)
    status: enum(lead, qualified, customer, inactive)
    lead_score: integer = 0
    tags: list(text)
    custom_fields: jsonb

  indexes:
    - columns: [email]
      type: unique
    - columns: [status, lead_score]
      type: btree

  actions:
    - name: create_contact
      requires: caller.has_permission('create_contact')

      steps:
        # Business validation
        - validate: email MATCHES email_pattern
          error: "invalid_email"
        - validate: phone MATCHES phone_pattern OR phone IS NULL
          error: "invalid_phone"

        # Business rule: deduplication
        - if: EXISTS Contact WHERE email = input.email
          then: reject("duplicate_email")

        # Business rule: insert contact
        - insert: Contact(all_fields)

        # Business rule: trigger AI agents
        - trigger: agent('lead_scoring_agent')
        - trigger: agent('enrichment_agent')

    - name: qualify_lead
      requires: contact.status = 'lead' AND caller.is_owner

      steps:
        # Business validation
        - validate: lead_score >= 70
          error: "insufficient_lead_score"

        # Business workflow
        - update: Contact SET status = 'qualified'
        - call: create_opportunity(contact_id = contact.id)

  agents:
    - name: lead_scoring_agent
      type: ai_llm
      observes: ['contact.created', 'activity.logged']
      can_execute: ['update_lead_score', 'qualify_lead']

      strategy: |
        Analyze contact data and score 0-100 based on:
        1. Company size (employees, revenue)
        2. Industry fit (target industries)
        3. Engagement level (emails, calls, meetings)
        4. Budget indicators (custom_fields.budget)

        Scoring thresholds:
        - 0-30: Low priority (routine follow-up)
        - 31-70: Medium priority (nurture campaign)
        - 71-100: High priority (auto-qualify if owner approves)

      audit: required

    - name: enrichment_agent
      observes: ['contact.created']
      can_execute: ['update_contact_data']

      strategy: |
        Call external enrichment API (Clearbit, Apollo):
        1. Fetch company data (size, industry, revenue)
        2. Fetch social profiles (LinkedIn, Twitter)
        3. Validate job title
        4. Update contact.custom_fields with enriched data

      audit: required
```

**Generated Output (Framework):**
```
✅ PostgreSQL table: crm.tb_contact
✅ PostgreSQL view: crm.v_contact (with JSONB data column)
✅ SQL function: crm.fn_create_contact(...)
✅ SQL function: crm.fn_qualify_lead(...)
✅ GraphQL type: Contact
✅ GraphQL mutations: createContact, qualifyLead
✅ GraphQL queries: contact(id), contacts(where, orderBy)
✅ TypeScript types: Contact, CreateContactInput, QualifyLeadInput
✅ Agent runtime config: lead_scoring_agent, enrichment_agent
✅ Test suite: 25 auto-generated tests
✅ Documentation: API docs + OpenAPI spec
```

**Result:**
- **YAML**: 60 lines (business logic only)
- **Generated Code**: 2,000+ lines (framework)
- **Time**: 2 hours YAML + 5 minutes compilation

---

## 🚀 Implementation Strategy (Revised)

### **Phase 1: Framework Foundation (Week 1-2)**

**Build SpecQL Compiler:**
- ✅ Parse YAML entity definitions
- ✅ Generate PostgreSQL tables + views
- ✅ Generate standard CRUD functions
- ✅ Generate GraphQL schema
- ✅ Generate TypeScript types

**Deliverable**: Basic CRUD works end-to-end

---

### **Phase 2: Action Step DSL (Week 3-4)**

**Implement Business Logic Steps:**
- ✅ `validate: expression` → SQL validation
- ✅ `if/then/else` → PL/pgSQL conditionals
- ✅ `insert/update/delete` → SQL operations
- ✅ `call: function(...)` → Function invocation
- ✅ `find/fetch` → SQL queries

**Deliverable**: Business workflows compile to SQL

---

### **Phase 3: Advanced Patterns (Week 5-6)**

**Implement Complex Features:**
- ✅ Conflict detection (EXISTS queries)
- ✅ Temporal logic (date ranges)
- ✅ Neighbor adjustment (UPDATE chains)
- ✅ Nested creation (function calls)
- ✅ Computed values (expressions)

**Deliverable**: Complex business logic supported

---

### **Phase 4: AI Agents (Week 7-8)**

**Implement Agent Runtime:**
- ✅ Agent sandbox (isolated execution)
- ✅ Event observation (trigger on events)
- ✅ Action execution (controlled permissions)
- ✅ LLM integration (OpenAI, Claude)
- ✅ Audit trail (all agent actions logged)

**Deliverable**: AI-powered automation

---

### **Phase 5: Production Ready (Week 9-10)**

**Polish & Optimize:**
- ✅ Error messages (business-friendly)
- ✅ Performance (query optimization)
- ✅ Testing (auto-generated tests)
- ✅ Documentation (auto-generated docs)
- ✅ Migration path (existing → SpecQL)

**Deliverable**: Production-ready platform

---

## 🎯 Key Benefits of SpecQL Approach

### **1. Massive Reduction in YAML Verbosity**

**Before** (Framework + Business Mixed):
```yaml
# 250 lines of YAML for reservation
business_logic:
  validations: [15 rules with error handling]
  existence_checks: [5 checks with error messages]
  conflict_detection: [3 complex checks]
  exception_handling: [4 exception types]
  response_structure: [complex response building]
  # ... etc
```

**After** (Business-Only):
```yaml
# 60 lines of YAML for reservation
actions:
  - name: create_reservation
    steps:
      - validate: reserved_from <= reserved_until
      - validate: NOT EXISTS overlapping_reservation
      - insert: Reservation(...)
      # Framework handles the rest automatically
```

**Reduction: 75-80% less YAML**

---

### **2. Clear Separation of Concerns**

| Layer | Responsibility | Implementation |
|-------|---------------|----------------|
| **Framework** | Infrastructure (CRUD, events, audit, errors) | SpecQL Compiler |
| **Business** | Domain rules (validations, workflows, agents) | YAML Specification |
| **UI** | Presentation (forms, lists, dashboards) | React + Generated Hooks |

---

### **3. Framework Evolution Without YAML Changes**

**Example: Improve Error Handling**

```yaml
# YAML stays the same
steps:
  - validate: email MATCHES email_pattern
    error: "invalid_email"
```

**Framework Evolution:**
```sql
-- V1: Simple error
IF NOT (email ~ email_pattern) THEN
  RETURN error('invalid_email');
END IF;

-- V2: Better error (framework update, no YAML change)
IF NOT (email ~ email_pattern) THEN
  RETURN error('invalid_email',
    message => format('Email %s is invalid', email),
    field => 'email',
    suggestion => 'Use format: name@domain.com'
  );
END IF;
```

---

### **4. AI Agent Integration (Built-In)**

```yaml
agents:
  - name: lead_scoring_agent
    type: ai_llm
    observes: ['contact.created']
    strategy: |
      Score leads 0-100 based on company size, industry fit, engagement
    audit: required
```

**Framework provides:**
- ✅ Agent sandbox (isolated execution)
- ✅ LLM integration (OpenAI, Claude)
- ✅ Permission system (can_execute: [...])
- ✅ Audit trail (all actions logged)
- ✅ Error handling (agent failures)

**Business specifies:**
- 🎯 When to trigger (observes)
- 🎯 What to do (strategy)
- 🎯 What's allowed (can_execute)

---

## ✅ Conclusion

### **Key Insights**

1. **Framework handles 80% of code** → CRUD, permissions, events, audit, errors
2. **YAML focuses on 20% of logic** → Business validations, workflows, agents
3. **Result: 75-80% reduction in YAML verbosity** → Cleaner, more maintainable

### **Revised YAML Schema**

```yaml
entity: EntityName
  fields: {...}           # Simple type definitions
  actions:
    - name: action_name
      steps:
        - validate: business_rule
        - if: condition then: [workflow]
        - insert/update/delete: Entity(...)
        - call: function(...)
  agents:
    - name: agent_name
      strategy: |
        AI strategy description
```

**Total**: 40-60 lines for complex entities (vs 200+ lines before)

### **Next Steps**

1. ✅ Build SpecQL compiler (Week 1-2)
2. ✅ Implement action step DSL (Week 3-4)
3. ✅ Add advanced patterns (Week 5-6)
4. ✅ Integrate AI agents (Week 7-8)
5. ✅ Production polish (Week 9-10)

**Timeline**: 10 weeks to production-ready SpecQL platform

**Result**: Build SaaS backends in 1-2 weeks instead of 6-12 months (90% time reduction)

---

**END OF REFINED ANALYSIS**
