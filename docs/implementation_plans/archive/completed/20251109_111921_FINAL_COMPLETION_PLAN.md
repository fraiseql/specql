# FINAL SpecQL Completion Plan - FraiseQL YAML Format

**Date**: 2025-11-08
**Based On**: FraiseQL Comment Format Guide (YAML-based)
**Timeline**: 1.5-2 weeks (8-10 days)
**Current Completion**: 80-85%

---

## 🎯 Critical Discovery

**We're using the OLD format:**
```sql
COMMENT ON TYPE app.mutation_result IS
  '@fraiseql:type name=MutationResult';
```

**FraiseQL expects NEW format (YAML with description):**
```sql
COMMENT ON TYPE app.mutation_result IS
'Standard mutation result for all operations.

@fraiseql:composite
name: MutationResult
tier: 1';
```

**Impact**: Need to update ALL comment generation to match FraiseQL's YAML format

---

## 📋 What Needs to Change

### Current State vs Required State

| Component | Current Format | Required Format | Status |
|-----------|---------------|-----------------|--------|
| Composite types | Old `@fraiseql:type name=X` | YAML `@fraiseql:composite` + description | ❌ Needs update |
| Composite fields | Old `name=x,type=Y` | YAML multi-line | ❌ Needs update |
| Functions | Old single-line | YAML multi-line | ❌ Needs update |
| Tables | No comments | Need `@fraiseql:type` | ❌ Missing |
| Columns | Basic descriptions | Need `@fraiseql:field` | ❌ Missing |

---

## 🚀 REVISED 8-10 DAY PLAN

### Week 1 (Days 1-5): Update Comment Format to FraiseQL YAML Spec

### Week 2 (Days 6-8/10): Custom Actions + CLI + Docs

---

# WEEK 1: FraiseQL YAML Format Migration

## Day 1: Composite Type Comments

**Objective**: Update all composite type comments to YAML format

### TDD Cycle 1: Mutation Result Type (2 hours)

**🔴 RED** (30 min)
```python
# tests/unit/generators/test_app_schema_generator.py
def test_mutation_result_comment_yaml_format():
    """Mutation result should use YAML format with description"""
    generator = AppSchemaGenerator()
    sql = generator.generate_mutation_result_type()

    # Should have human-readable description
    assert "'Standard mutation result" in sql

    # Should have YAML metadata after blank line
    assert "@fraiseql:composite" in sql
    assert "name: MutationResult" in sql
    assert "tier: 1" in sql

    # Full format check
    expected_comment = """COMMENT ON TYPE app.mutation_result IS
'Standard mutation result for all operations.
Returns entity data, status, and optional metadata.

@fraiseql:composite
name: MutationResult
tier: 1
storage: composite';"""
    assert expected_comment in sql
```

Run: `uv run pytest tests/unit/generators/test_app_schema_generator.py::test_mutation_result_comment_yaml_format -v`
Expected: **FAIL**

**🟢 GREEN** (1 hour)
1. Update `src/generators/app_schema_generator.py`
2. Change comment generation to YAML format
3. Add description text before metadata

```python
def _generate_mutation_result_comment(self) -> str:
    """Generate FraiseQL-compatible YAML comment"""
    return """COMMENT ON TYPE app.mutation_result IS
'Standard mutation result for all operations.
Returns entity data, status, and optional metadata.

@fraiseql:composite
name: MutationResult
tier: 1
storage: composite';"""
```

**🔧 REFACTOR** (20 min)
Extract to template

**✅ QA** (10 min)
Test suite

---

### TDD Cycle 2: Composite Type Field Comments (2 hours)

**🔴 RED** (30 min)
```python
def test_mutation_result_field_comments_yaml_format():
    """Field comments should use YAML format"""
    generator = AppSchemaGenerator()
    sql = generator.generate_mutation_result_type()

    # Check id field comment
    expected_id_comment = """COMMENT ON COLUMN app.mutation_result.id IS
'Unique identifier of the affected entity.

@fraiseql:field
name: id
type: UUID!
required: true';"""
    assert expected_id_comment in sql

    # Check status field comment
    expected_status_comment = """COMMENT ON COLUMN app.mutation_result.status IS
'Operation status indicator.
Values: success, failed:error_code

@fraiseql:field
name: status
type: String!
required: true';"""
    assert expected_status_comment in sql
```

**🟢 GREEN** (1 hour)
Update field comment generation

**🔧 REFACTOR** (20 min)
Template optimization

**✅ QA** (10 min)
Test

---

### TDD Cycle 3: Generated Composite Types (3 hours)

**🔴 RED** (45 min)
```python
# tests/unit/generators/test_composite_type_generator.py
def test_generate_input_composite_with_yaml_comments():
    """Generated input composites should have YAML comments"""
    entity = Entity(name="Contact", schema="crm")
    action = Action(name="create_contact", ...)

    generator = CompositeTypeGenerator()
    sql = generator.generate_input_composite(entity, action)

    # Should have type-level comment
    expected_type_comment = """COMMENT ON TYPE app.type_create_contact_input IS
'Input parameters for creating Contact.

@fraiseql:composite
name: CreateContactInput
tier: 2';"""
    assert expected_type_comment in sql

    # Should have field-level comments
    expected_field_comment = """COMMENT ON COLUMN app.type_create_contact_input.email IS
'Email address (required).

@fraiseql:field
name: email
type: Email!
required: true';"""
    assert expected_field_comment in sql
```

**🟢 GREEN** (1.5 hours)
Update `CompositeTypeGenerator` to use YAML format

**🔧 REFACTOR** (45 min)
Clean up, add helpers for YAML generation

**✅ QA** (30 min)
Full test suite

**END OF DAY 1**: Composite type comments migrated to YAML

---

## Day 2: Function Comments

**Objective**: Update function comments to YAML format

### TDD Cycle 1: App Wrapper Function Comments (3 hours)

**🔴 RED** (45 min)
```python
# tests/unit/generators/test_app_wrapper_generator.py
def test_app_wrapper_comment_yaml_format():
    """App wrapper function should have YAML comment"""
    entity = Entity(name="Contact", schema="crm")
    action = Action(name="create_contact", ...)

    generator = AppWrapperGenerator()
    sql = generator.generate(entity, action)

    expected_comment = """COMMENT ON FUNCTION app.create_contact IS
'Creates a new contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createContact
input_type: app.type_create_contact_input
success_type: CreateContactSuccess
failure_type: CreateContactError';"""

    assert expected_comment in sql
```

**🟢 GREEN** (1.5 hours)
Update `AppWrapperGenerator` and template

**🔧 REFACTOR** (45 min)
Clean up template

**✅ QA** (30 min)
Test suite

---

### TDD Cycle 2: Generate Action Descriptions (2 hours)

**🔴 RED** (30 min)
```python
def test_generate_action_description_from_steps():
    """Should generate description from action steps"""
    action = Action(
        name="qualify_lead",
        steps=[
            ActionStep(type="validate", expression="status = 'lead'"),
            ActionStep(type="update", entity="Contact", fields={"status": "qualified"})
        ]
    )

    generator = AppWrapperGenerator()
    description = generator._generate_action_description(action)

    # Should describe what action does
    assert "Qualifies a lead" in description or "Updates lead status" in description
```

**🟢 GREEN** (1 hour)
Implement description generation logic

**🔧 REFACTOR** (20 min)
Improve heuristics

**✅ QA** (10 min)
Test

**END OF DAY 2**: Function comments migrated to YAML

---

## Day 3: Table and Column Comments

**Objective**: Add FraiseQL annotations to tables and columns

### TDD Cycle 1: Table Comments with @fraiseql:type (2 hours)

**🔴 RED** (30 min)
```python
# tests/unit/generators/test_table_generator.py
def test_table_comment_with_fraiseql_type():
    """Tables should have @fraiseql:type annotation"""
    entity = Entity(
        name="Contact",
        schema="crm",
        description="Customer contact record"
    )

    generator = TableGenerator()
    sql = generator.generate_table(entity)

    expected_comment = """COMMENT ON TABLE crm.tb_contact IS
'Customer contact record.
Stores contact information with email, phone, and company relationships.

@fraiseql:type
trinity: true';"""

    assert expected_comment in sql
```

**🟢 GREEN** (1 hour)
Update `TableGenerator` to add FraiseQL type comments

**🔧 REFACTOR** (20 min)
Clean up

**✅ QA** (10 min)
Test

---

### TDD Cycle 2: Column Comments with @fraiseql:field (3 hours)

**🔴 RED** (45 min)
```python
def test_column_comments_with_fraiseql_field():
    """Columns should have @fraiseql:field annotations"""
    entity = Entity(name="Contact", schema="crm", fields={
        "email": FieldDefinition(
            name="email",
            type_name="email",
            nullable=False,
            fraiseql_type="Email"
        )
    })

    generator = TableGenerator()
    sql = generator.generate_table(entity)

    expected_comment = """COMMENT ON COLUMN crm.tb_contact.email IS
'Email address (validated format).

@fraiseql:field
name: email
type: Email!
required: true';"""

    assert expected_comment in sql
```

**🟢 GREEN** (1.5 hours)
Implement column comment generation with YAML

**🔧 REFACTOR** (45 min)
Template optimization

**✅ QA** (30 min)
Test suite

---

### TDD Cycle 3: Trinity Helper Functions (1 hour)

**🔴 RED** (20 min)
```python
def test_trinity_helper_comments():
    """Trinity helper functions should have descriptions"""
    entity = Entity(name="Contact", schema="crm")

    generator = TrinityHelperGenerator()
    sql = generator.generate_helpers(entity)

    expected_comment = """COMMENT ON FUNCTION crm.contact_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_contact.';"""

    assert expected_comment in sql
```

**🟢 GREEN** (30 min)
Add comments to Trinity helpers

**🔧 REFACTOR** (5 min)
Clean up

**✅ QA** (5 min)
Test

**END OF DAY 3**: All table/column comments have FraiseQL annotations

---

## Day 4: Integration Testing

**Objective**: Verify complete pipeline generates correct YAML comments

### TDD Cycle 1: End-to-End Comment Format Test (3 hours)

**🔴 RED** (1 hour)
```python
# tests/integration/test_fraiseql_yaml_format.py
def test_complete_pipeline_generates_yaml_comments():
    """Complete SpecQL → SQL pipeline should generate YAML-formatted comments"""
    yaml_content = """
    entity: Contact
    schema: crm
    description: Customer contact information
    fields:
      email: email!
      company: ref(Company)
      status: enum(lead, qualified)
    actions:
      - name: create_contact
        steps:
          - validate: email IS NOT NULL
          - insert: Contact
      - name: qualify_lead
        steps:
          - validate: status = 'lead'
          - update: Contact SET status = 'qualified'
    """

    # Parse
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Generate
    orchestrator = SchemaOrchestrator()
    sql = orchestrator.generate_complete_schema(entity)

    # Verify YAML format in comments

    # 1. Table comment
    assert "COMMENT ON TABLE crm.tb_contact IS" in sql
    assert "@fraiseql:type" in sql
    assert "trinity: true" in sql

    # 2. Column comments
    assert "COMMENT ON COLUMN crm.tb_contact.email IS" in sql
    assert "@fraiseql:field" in sql
    assert "name: email" in sql  # YAML format
    assert "type: Email!" in sql
    assert "required: true" in sql

    # 3. Composite type comments
    assert "COMMENT ON TYPE app.type_create_contact_input IS" in sql
    assert "@fraiseql:composite" in sql
    assert "name: CreateContactInput" in sql
    assert "tier: 2" in sql

    # 4. Function comments
    assert "COMMENT ON FUNCTION app.create_contact IS" in sql
    assert "@fraiseql:mutation" in sql
    assert "name: createContact" in sql
    assert "input_type: app.type_create_contact_input" in sql

    # Verify NO old format remains
    assert "@fraiseql:type name=" not in sql  # Old format
    assert "@fraiseql:field name=email,type=" not in sql  # Old format
```

**🟢 GREEN** (1.5 hours)
Fix any integration issues found

**🔧 REFACTOR** (30 min)
Polish

**✅ QA** (30 min)
Run multiple times

---

### Task 2: FraiseQL Format Documentation (2 hours)

**Non-TDD**: Document our implementation

Create `docs/architecture/FRAISEQL_COMMENT_IMPLEMENTATION.md`:

```markdown
# FraiseQL Comment Implementation in SpecQL

This documents how SpecQL generates PostgreSQL comments compatible with FraiseQL's YAML format.

## Format Overview

All comments follow this structure:

```
[Human-readable description]

@fraiseql:[type]
[YAML configuration]
```

## Implementation

### Composite Types

Generator: `CompositeTypeGenerator`
Template: `templates/sql/composite_type_comments.sql.j2`

Example output:
```sql
COMMENT ON TYPE app.type_simple_address IS
'Simple postal address without validation.

@fraiseql:composite
name: SimpleAddress
tier: 2
storage: jsonb';
```

### Fields

Generator: `CompositeTypeGenerator`
Template: `templates/sql/field_comments.sql.j2`

Example output:
```sql
COMMENT ON COLUMN app.type_simple_address.street IS
'Street address line 1 (required).

@fraiseql:field
name: street
type: String!
required: true';
```

... (continue for all comment types)
```

**END OF DAY 4**: Integration complete, documented

---

## Day 5: Buffer / Polish

**Objective**: Clean up and prepare for custom actions

### Morning (4 hours): Code Review
- Review all comment generation code
- Ensure consistency across generators
- Fix any edge cases
- Add missing validations

### Afternoon (4 hours): Testing
- Run full test suite 10x
- Fix flaky tests
- Manual inspection of generated SQL
- Verify FraiseQL can parse all comments (if possible)

**END OF WEEK 1**: All comments migrated to FraiseQL YAML format

---

# WEEK 2: Custom Actions + CLI + Ship

## Day 6: Custom Actions

**Objective**: Support non-CRUD custom actions

### TDD Cycle 1: Custom Action Detection & Generation (4 hours)

**🔴 RED** (45 min)
```python
# tests/unit/generators/test_core_logic_generator.py
def test_generate_custom_action():
    """Generate custom business action"""
    entity = Entity(name="Contact", schema="crm")
    action = Action(
        name="qualify_lead",
        steps=[
            ActionStep(type="validate", expression="status = 'lead'"),
            ActionStep(type="update", entity="Contact", fields={"status": "qualified"}),
            ActionStep(type="notify", template="lead_qualified")
        ]
    )

    generator = CoreLogicGenerator()
    sql = generator.generate_custom_action(entity, action)

    # Should have function
    assert "CREATE FUNCTION crm.qualify_lead(" in sql

    # Should compile steps
    assert "status = 'lead'" in sql  # validate
    assert "UPDATE crm.tb_contact" in sql  # update
    assert "PERFORM app.emit_event" in sql  # notify

    # Should have YAML comment
    assert "@fraiseql:mutation" in sql
    assert "name: qualifyLead" in sql
```

**🟢 GREEN** (2.5 hours)
Implement custom action generation

**🔧 REFACTOR** (45 min)
Clean up

**✅ QA** (30 min)
Test suite

---

### TDD Cycle 2: Database Roundtrip (2 hours)

**🔴 RED** (30 min)
```python
def test_custom_action_database_execution(test_db):
    """Custom action executes in PostgreSQL"""
    # (Similar to previous plan)
```

**🟢 GREEN** (1 hour)
Fix execution issues

**🔧 REFACTOR** (20 min)
Polish

**✅ QA** (10 min)
Test

**END OF DAY 6**: Custom actions complete

---

## Day 7: CLI Generate Command

**Objective**: Production CLI

### TDD Cycle 1: Basic Generate (3 hours)

**🔴 RED** (45 min)
```python
def test_cli_generate_command():
    """CLI should generate migrations"""
    result = cli_runner.invoke(generate_command, ["entities/contact.yaml"])

    assert result.exit_code == 0
    assert "✓ Generated: migrations/001_contact.sql" in result.output
```

**🟢 GREEN** (1.5 hours)
Implement CLI

**🔧 REFACTOR** (45 min)
Polish output

**✅ QA** (30 min)
Test

---

### TDD Cycle 2: Validate Command (2 hours)

**🔴 RED** (30 min)
```python
def test_cli_validate_command():
    """Validate SpecQL files"""
    result = cli_runner.invoke(validate_command, ["entities/contact.yaml"])

    assert result.exit_code == 0
    assert "✓ contact.yaml is valid" in result.output
```

**🟢 GREEN** (1 hour)
Implement validation

**🔧 REFACTOR** (20 min)
Error messages

**✅ QA** (10 min)
Test

**END OF DAY 7**: CLI complete

---

## Day 8: Documentation + Examples

### Morning (4 hours): User Docs

Write:
1. **Getting Started** (`docs/guides/getting-started.md`)
2. **SpecQL Reference** (`docs/reference/specql-syntax.md`)
3. **FraiseQL Integration** (`docs/guides/fraiseql-integration.md`)

### Afternoon (4 hours): Examples

Create:
1. **CRM Example** (`examples/crm/`)
2. **E-commerce Example** (`examples/ecommerce/`)

**END OF DAY 8**: Documentation complete

---

## Day 9-10: Polish & Release

### Day 9: Final Polish
- Fix TODOs
- Improve error messages
- Code review
- Testing marathon

### Day 10: Release
- Version 1.0.0
- CHANGELOG.md
- Release notes
- Demo

**END OF DAY 10**: Ready to ship!

---

## 🎯 SUCCESS CRITERIA

### Functionality ✅
- [ ] All comments use YAML format (FraiseQL compatible)
- [ ] Composite types have proper annotations
- [ ] Functions have proper annotations
- [ ] Tables/columns have proper annotations
- [ ] Custom actions work
- [ ] CLI commands work
- [ ] 330+ tests passing

### Quality ✅
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Error messages helpful
- [ ] Documentation complete
- [ ] Examples working

### Deliverables ✅
- [ ] YAML-formatted comments throughout
- [ ] Custom action support
- [ ] CLI tools
- [ ] User documentation
- [ ] Working examples
- [ ] FraiseQL can introspect generated schema

---

## 📊 Comment Format Checklist

Before shipping, verify all comments match FraiseQL format:

### Composite Types ✅
```sql
COMMENT ON TYPE schema.type_name IS
'[Description]

@fraiseql:composite
name: GraphQLName
tier: 1|2|3';
```

### Composite Fields ✅
```sql
COMMENT ON COLUMN schema.type_name.field IS
'[Description]

@fraiseql:field
name: fieldName
type: GraphQLType
required: true|false';
```

### Functions ✅
```sql
COMMENT ON FUNCTION schema.func IS
'[Description]

@fraiseql:mutation
name: mutationName
input_type: schema.type_input
success_type: SuccessType
failure_type: FailureType';
```

### Tables ✅
```sql
COMMENT ON TABLE schema.tb_entity IS
'[Description]

@fraiseql:type
trinity: true';
```

### Columns ✅
```sql
COMMENT ON COLUMN schema.tb_entity.field IS
'[Description]

@fraiseql:field
name: fieldName
type: GraphQLType
required: true|false';
```

---

## 📈 Daily Progress Template

```markdown
### Day 1 (YYYY-MM-DD) - Composite Type Comments
- [ ] Cycle 1: mutation_result YAML format
- [ ] Cycle 2: Field comments YAML format
- [ ] Cycle 3: Generated composites YAML format
- Tests: ___/330 passing
- Blockers: ___
- Notes: ___

... (continue for all days)
```

---

## 🚀 CRITICAL DIFFERENCES FROM PREVIOUS PLANS

### What Changed:

1. **Comment Format**: YAML with description (not single-line)
2. **Annotation Names**: `@fraiseql:composite` (not `@fraiseql:type`)
3. **Field Format**: Multi-line YAML (not `name=x,type=y`)
4. **Required Fields**: Must include description text before metadata

### What Stayed Same:

1. Custom actions still needed
2. CLI still needed
3. Documentation still needed
4. Testing approach (TDD cycles)

---

**Timeline**: 8-10 days (1.5-2 weeks)
**Risk**: LOW (format migration is straightforward)
**Confidence**: HIGH (clear spec from FraiseQL team)
**Next Action**: Start Day 1, Cycle 1 - Update mutation_result comment

---

**READY TO BEGIN?**

This plan migrates all our comment generation to match FraiseQL's exact YAML format specification, then completes the remaining features (custom actions, CLI, docs).
