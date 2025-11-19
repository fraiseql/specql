# Simplified SpecQL Completion Plan - Single Agent TDD

**Key Insight**: FraiseQL now reads PostgreSQL COMMENT metadata directly!

**Impact**: Team D work is **90% done** already. We just need to enhance comments.

**Revised Timeline**: **2 weeks** instead of 4 weeks

---

## 🎯 What's Already Working

### ✅ Team A: Parser (95% complete)
- Complete SpecQL parsing
- All field types supported
- Action parsing complete

### ✅ Team B: Schema Generation (90% complete)
- Trinity pattern fully implemented
- Table generation with audit fields
- Foreign keys, indexes, constraints
- Rich scalar type support
- Already generating `COMMENT ON TABLE` and `COMMENT ON COLUMN`

### ✅ Team C: Action Compilation (85% complete)
- CRUD operations working
- App/Core two-layer pattern
- Expression compiler complete
- Database roundtrip tests passing
- Already generating `COMMENT ON FUNCTION app.function_name` with `@fraiseql:mutation`

### ✅ Team D: FraiseQL Metadata (70% complete!)
**Already generating**:
- ✅ `@fraiseql:type` for composite types
- ✅ `@fraiseql:field` for composite type fields
- ✅ `@fraiseql:mutation` for app wrapper functions
- ✅ Table and column comments

**What's Missing** (30%):
- Enhanced mutation metadata (impact, cache hints)
- Table/column FraiseQL annotations
- Documentation of metadata format

---

## 📊 Revised Progress Assessment

| Team | Previous Estimate | Actual Status | Reason |
|------|------------------|---------------|---------|
| Team A | 95% | **95%** | Accurate |
| Team B | 90% | **90%** | Accurate |
| Team C | 85% | **85%** | Accurate |
| Team D | 50% | **70%** | Basic FraiseQL comments already working! |
| Team E | 30% | **30%** | Accurate |

**Overall Project**: **80-85% complete** (not 70-75%!)

**Remaining Work**: **15-20%** (not 25-30%)

---

## 🚀 SIMPLIFIED 2-WEEK PLAN

### Week 1: Polish FraiseQL + Custom Actions (5 days)
**Goal**: Complete Team C & D to 100%

### Week 2: CLI & Documentation (5 days)
**Goal**: Ship production-ready system

---

# WEEK 1: FraiseQL Polish + Custom Actions

## Day 1: Enhanced FraiseQL Mutation Metadata

**Objective**: Add impact metadata to @fraiseql:mutation comments

### TDD Cycle 1: Add Impact Metadata to Mutation Comments (3 hours)

**🔴 RED** (30 min)
```python
# tests/unit/generators/test_app_wrapper_generator.py
def test_mutation_comment_includes_impact_metadata():
    """Mutation comment should include impact and cache hints"""
    entity = Entity(name="Contact", schema="crm")
    action = Action(
        name="qualify_lead",
        # In future, we might parse impact from action analysis
    )

    generator = AppWrapperGenerator()
    sql = generator.generate(entity, action)

    # Should have enhanced metadata
    assert "@fraiseql:mutation" in sql
    assert "primaryEntity=Contact" in sql
    assert "primaryOperation=UPDATE" in sql
    assert "affectedFields=[status,updatedAt]" in sql
    # Optional: cache hints
    assert "invalidates=[contacts]" in sql
```

Run: `uv run pytest tests/unit/generators/test_app_wrapper_generator.py::test_mutation_comment_includes_impact_metadata -v`
Expected: **FAIL**

**🟢 GREEN** (1.5 hours)
1. Update `src/generators/app_wrapper_generator.py`
2. Add method to analyze action and extract impact metadata
3. Update template to include enhanced metadata

```python
# In app_wrapper_generator.py
def _analyze_action_impact(self, entity: Entity, action: Action) -> dict:
    """Analyze action to determine impact metadata"""
    impact = {
        "primary_entity": entity.name,
        "primary_operation": self._infer_operation(action),
        "affected_fields": self._extract_affected_fields(action),
        "invalidates": self._infer_cache_invalidations(entity, action)
    }
    return impact

def _infer_operation(self, action: Action) -> str:
    """Infer operation type from action steps"""
    if any(step.type == "insert" for step in action.steps):
        return "CREATE"
    elif any(step.type == "update" for step in action.steps):
        return "UPDATE"
    elif any(step.type == "delete" for step in action.steps):
        return "DELETE"
    return "CUSTOM"
```

**🔧 REFACTOR** (45 min)
- Clean up impact analysis logic
- Add unit tests for helper methods
- Document metadata format

**✅ QA** (30 min)
- Run full test suite
- Verify comments format correctly
- Check no regressions

---

### TDD Cycle 2: Table and Field FraiseQL Annotations (2 hours)

**🔴 RED** (30 min)
```python
# tests/unit/generators/test_comment_generator.py
def test_table_comment_includes_fraiseql_type():
    """Table comment should include @fraiseql:type"""
    entity = Entity(name="Contact", schema="crm", description="Customer contact")

    generator = CommentGenerator()
    comment = generator.generate_table_comment_with_fraiseql(entity)

    assert "COMMENT ON TABLE crm.tb_contact" in comment
    assert "@fraiseql:type name=Contact" in comment
    assert "schema=crm" in comment
```

**🟢 GREEN** (1 hour)
Implement `generate_table_comment_with_fraiseql()` method

**🔧 REFACTOR** (20 min)
Clean up

**✅ QA** (10 min)
Test suite

---

### TDD Cycle 3: Field-level FraiseQL Annotations (2 hours)

**🔴 RED** (30 min)
```python
def test_field_comment_includes_fraiseql_metadata():
    """Field comments should include @fraiseql:field metadata"""
    field = FieldDefinition(
        name="email",
        type_name="email",
        nullable=False,
        postgres_type="TEXT",
        fraiseql_type="Email"
    )
    entity = Entity(name="Contact", schema="crm")

    generator = CommentGenerator()
    comment = generator.generate_field_comment_with_fraiseql(field, entity)

    assert "COMMENT ON COLUMN crm.tb_contact.email" in comment
    assert "@fraiseql:field name=email" in comment
    assert "type=Email" in comment
    assert "required=true" in comment  # Because nullable=False
```

**🟢 GREEN** (1 hour)
Implement field-level annotations

**🔧 REFACTOR** (20 min)
Template optimization

**✅ QA** (10 min)
Test suite

**END OF DAY 1**: Enhanced FraiseQL comments complete

---

## Day 2: Custom Actions (Team C Completion)

**Objective**: Support non-CRUD custom actions

### TDD Cycle 1: Custom Action Pattern Detection (1 hour)

**🔴 RED** (20 min)
```python
# tests/unit/generators/test_core_logic_generator.py
def test_detect_custom_action():
    """Detect custom actions vs CRUD"""
    action_crud = Action(name="create_contact", steps=[...])
    action_custom = Action(name="qualify_lead", steps=[...])

    generator = CoreLogicGenerator()

    assert generator.is_custom_action(action_crud) == False
    assert generator.is_custom_action(action_custom) == True
```

**🟢 GREEN** (30 min)
Implement detection logic

**🔧 REFACTOR** (10 min)
Clean up

**✅ QA** (5 min)
Test

---

### TDD Cycle 2: Custom Action Template (3 hours)

**🔴 RED** (45 min)
```python
def test_generate_custom_action_function():
    """Generate custom action PL/pgSQL function"""
    entity = Entity(name="Contact", schema="crm")
    action = Action(
        name="qualify_lead",
        steps=[
            ActionStep(type="validate", expression="status = 'lead'"),
            ActionStep(type="update", entity="Contact", fields={"status": "qualified"})
        ]
    )

    generator = CoreLogicGenerator()
    sql = generator.generate_custom_action(entity, action)

    # Should have function
    assert "CREATE FUNCTION crm.qualify_lead(" in sql
    # Should compile steps
    assert "status = 'lead'" in sql
    assert "UPDATE crm.tb_contact" in sql
    # Should return mutation_result
    assert "RETURNS app.mutation_result" in sql
```

**🟢 GREEN** (1.5 hours)
1. Create custom action generation logic
2. Reuse existing step compilers
3. Generate proper function signature

**🔧 REFACTOR** (45 min)
Clean up template, error handling

**✅ QA** (30 min)
Test suite

---

### TDD Cycle 3: Database Roundtrip for Custom Action (2 hours)

**🔴 RED** (45 min)
```python
# tests/integration/actions/test_custom_actions_database.py
def test_custom_action_executes_in_database(test_db):
    """Custom action qualify_lead works in real PostgreSQL"""
    # Generate SQL
    entity = create_contact_entity_with_custom_action()
    orchestrator = SchemaOrchestrator()
    sql = orchestrator.generate_complete_schema(entity)

    # Apply to database
    test_db.execute(sql)
    test_db.commit()

    # Create a lead
    contact_id = test_db.create_contact(status="lead")

    # Call custom action
    result = test_db.call_mutation("app.qualify_lead", {
        "contactId": str(contact_id)
    })

    # Verify success
    assert result["status"] == "success"

    # Verify database updated
    contact = test_db.get_contact(contact_id)
    assert contact["status"] == "qualified"
```

**🟢 GREEN** (45 min)
Fix any issues found

**🔧 REFACTOR** (20 min)
Improve SQL quality

**✅ QA** (10 min)
Full test suite

**END OF DAY 2**: Custom actions complete

---

## Day 3: Integration Testing

**Objective**: Verify complete SpecQL → PostgreSQL → FraiseQL pipeline

### TDD Cycle 1: Complete Pipeline Test (3 hours)

**🔴 RED** (1 hour)
```python
# tests/integration/test_complete_fraiseql_pipeline.py
def test_specql_to_fraiseql_complete():
    """Test SpecQL → SQL with FraiseQL comments → (manual FraiseQL introspection)"""
    yaml_content = """
    entity: Contact
    schema: crm
    fields:
      email: email!
      company: ref(Company)
      status: enum(lead, qualified, customer)
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

    # Verify SQL has all FraiseQL metadata
    assert "CREATE TABLE crm.tb_contact" in sql
    assert "COMMENT ON TABLE crm.tb_contact" in sql
    assert "@fraiseql:type name=Contact" in sql

    assert "CREATE FUNCTION app.create_contact" in sql
    assert "@fraiseql:mutation name=createContact" in sql
    assert "primaryEntity=Contact" in sql

    assert "CREATE FUNCTION app.qualify_lead" in sql
    assert "@fraiseql:mutation name=qualifyLead" in sql
    assert "primaryOperation=UPDATE" in sql

    # Apply to test database
    test_db.execute(sql)
    test_db.commit()

    # Verify functions work
    result = test_db.call_mutation("app.create_contact", {
        "email": "test@example.com",
        "status": "lead"
    })
    assert result["status"] == "success"

    result = test_db.call_mutation("app.qualify_lead", {
        "contactId": result["id"]
    })
    assert result["status"] == "success"
```

**🟢 GREEN** (1.5 hours)
Fix integration issues

**🔧 REFACTOR** (30 min)
Clean up

**✅ QA** (30 min)
Run multiple times

---

### TDD Cycle 2: Document FraiseQL Metadata Format (2 hours)

**Non-TDD Task**: Write documentation

Create `docs/architecture/FRAISEQL_METADATA_FORMAT.md`:

```markdown
# FraiseQL Metadata Format

This document describes the PostgreSQL COMMENT metadata format used for FraiseQL auto-discovery.

## Table Metadata

```sql
COMMENT ON TABLE schema.tb_entity IS
  'Entity description text

  @fraiseql:type name=Entity,schema=schema';
```

## Column Metadata

```sql
COMMENT ON COLUMN schema.tb_entity.field_name IS
  'Field description text

  @fraiseql:field name=fieldName,type=GraphQLType,required=true';
```

## Mutation Metadata

```sql
COMMENT ON FUNCTION app.mutation_name IS
  '@fraiseql:mutation name=mutationName,input=InputType,output=OutputType,primaryEntity=Entity,primaryOperation=UPDATE,affectedFields=[field1,field2],invalidates=[queryName]';
```

... (continue with full specification)
```

**END OF DAY 3**: FraiseQL integration complete and documented

---

## Days 4-5: Buffer / Polish

**Objective**: Clean up any rough edges

### Day 4 Morning: Code Review
- Review all new code
- Fix TODOs
- Improve error messages

### Day 4 Afternoon: Performance
- Profile generation speed
- Optimize slow parts
- Add benchmarks

### Day 5: Edge Cases
- Handle edge cases found in testing
- Add missing validations
- Polish error messages

**END OF WEEK 1**: Teams C & D complete at 100%

---

# WEEK 2: CLI & Documentation

## Day 6: CLI Generate Command

**Objective**: Production-ready `specql generate` command

### TDD Cycle 1: Basic Generate Command (3 hours)

**🔴 RED** (45 min)
```python
# tests/unit/cli/test_generate_command.py
def test_generate_command_creates_migration():
    """Test specql generate command"""
    # Mock file system
    with temp_directory() as tmp:
        # Create test entity file
        write_file(f"{tmp}/entities/contact.yaml", CONTACT_YAML)

        # Run CLI
        result = cli_runner.invoke(generate_command, [
            "entities/contact.yaml",
            f"--output={tmp}/migrations"
        ])

        assert result.exit_code == 0
        assert "✓ Generated: migrations/001_contact.sql" in result.output
        assert Path(f"{tmp}/migrations/001_contact.sql").exists()
```

**🟢 GREEN** (1.5 hours)
Implement generate command with:
- File reading
- Error handling
- Progress output
- Migration numbering

**🔧 REFACTOR** (45 min)
Add colors, better formatting

**✅ QA** (30 min)
Manual testing

---

### TDD Cycle 2: Batch Generation (2 hours)

**🔴 RED** (30 min)
```python
def test_generate_multiple_entities():
    """Generate from multiple YAML files"""
    result = cli_runner.invoke(generate_command, [
        "entities/*.yaml",
        "--output=migrations"
    ])

    assert result.exit_code == 0
    assert "✓ Generated 3 migrations" in result.output
```

**🟢 GREEN** (1 hour)
Implement glob pattern support

**🔧 REFACTOR** (20 min)
Clean up

**✅ QA** (10 min)
Test

---

## Day 7: CLI Validate & Docs Commands

### TDD Cycle 1: Validate Command (2 hours)

**🔴 RED** (30 min)
```python
def test_validate_command():
    """Test specql validate command"""
    result = cli_runner.invoke(validate_command, ["entities/contact.yaml"])

    assert result.exit_code == 0
    assert "✓ contact.yaml is valid" in result.output
```

**🟢 GREEN** (1 hour)
Implement validation

**🔧 REFACTOR** (20 min)
Error formatting

**✅ QA** (10 min)
Test

---

### TDD Cycle 2: Docs Command (2 hours)

**🔴 RED** (30 min)
```python
def test_docs_command():
    """Test specql docs command"""
    result = cli_runner.invoke(docs_command, [
        "entities/contact.yaml",
        "--output=docs/"
    ])

    assert result.exit_code == 0
    assert Path("docs/contact.md").exists()
```

**🟢 GREEN** (1 hour)
Generate markdown docs

**🔧 REFACTOR** (20 min)
Format templates

**✅ QA** (10 min)
Review output

---

## Day 8: User Documentation

**Objective**: Complete user-facing documentation

### Morning (4 hours): Core Guides

Write:
1. **Getting Started Guide** (`docs/guides/getting-started.md`)
   - Installation
   - First entity
   - Running migrations
   - Connecting FraiseQL

2. **SpecQL Language Reference** (`docs/reference/specql-syntax.md`)
   - All field types
   - Action syntax
   - Examples

3. **FraiseQL Integration Guide** (`docs/guides/fraiseql-integration.md`)
   - How metadata works
   - What FraiseQL discovers
   - GraphQL schema generation

### Afternoon (4 hours): Examples

Create working examples:
1. **Simple CRM** (`examples/crm/`)
   - Contact, Company entities
   - CRUD + custom actions
   - Complete migration
   - README with instructions

2. **E-commerce** (`examples/ecommerce/`)
   - Product, Order, Customer
   - Complex workflows
   - Custom actions

---

## Day 9: Polish & Testing

### Morning (4 hours): Polish
- Fix all TODOs
- Improve error messages
- Add helpful CLI output
- Code formatting

### Afternoon (4 hours): Testing Marathon
- Run test suite 20 times
- Fix flaky tests
- Test on different machines
- Document known issues

---

## Day 10: Release Preparation

### Morning (4 hours): Release Artifacts
1. Version bump to 1.0.0
2. Update CHANGELOG.md
3. Tag release
4. Write release notes

### Afternoon (4 hours): Demo & Announcement
1. Record demo video
2. Create example repository
3. Write blog post
4. Prepare stakeholder presentation

---

## 🎯 SUCCESS CRITERIA

### Functionality ✅
- [x] SpecQL → PostgreSQL (already working)
- [ ] Enhanced FraiseQL metadata
- [ ] Custom actions
- [ ] CLI commands
- [ ] 320+ tests passing

### Quality ✅
- [ ] No critical bugs
- [ ] Performance <5s for 10 entities
- [ ] Helpful error messages
- [ ] Complete documentation

### Deliverables ✅
- [ ] Enhanced `@fraiseql:*` comments in SQL
- [ ] Custom action support
- [ ] CLI tools (`generate`, `validate`, `docs`)
- [ ] User documentation
- [ ] Working examples

---

## 📊 DAILY PROGRESS TRACKING

```markdown
### Day 1 (YYYY-MM-DD) - Enhanced FraiseQL Metadata
- [ ] Cycle 1: Impact metadata in mutation comments
- [ ] Cycle 2: Table annotations
- [ ] Cycle 3: Field annotations
- Tests: ___/320 passing
- Blockers: ___

### Day 2 (YYYY-MM-DD) - Custom Actions
- [ ] Cycle 1: Detection logic
- [ ] Cycle 2: Generation template
- [ ] Cycle 3: Database roundtrip
- Tests: ___/325 passing
- Blockers: ___

... (continue for all 10 days)
```

---

## 🎉 KEY SIMPLIFICATIONS

### What Changed from Original Plan?

| Original (4 weeks) | Simplified (2 weeks) | Reason |
|-------------------|---------------------|---------|
| Generate mutation-impacts.json | ❌ REMOVED | FraiseQL reads SQL comments directly |
| Generate TypeScript .d.ts | ❌ REMOVED | FraiseQL generates this from SQL |
| Generate React hooks | ❌ REMOVED | FraiseQL generates this from SQL |
| Frontend codegen | ❌ REMOVED | FraiseQL handles this |
| Complex JSON schemas | ❌ REMOVED | SQL comments are sufficient |
| 20 days of work | ✅ 10 days | 50% reduction! |

### What We're Keeping

| Task | Why Essential |
|------|---------------|
| Enhanced SQL comments | FraiseQL needs this metadata |
| Custom actions | Core feature missing |
| CLI tools | Developer experience |
| Documentation | User needs |
| Examples | User needs |

---

## 🚀 READY TO START?

**Next Action**: Start Day 1, TDD Cycle 1 - Enhanced FraiseQL mutation metadata

This plan is:
- ✅ **50% shorter** (2 weeks vs 4 weeks)
- ✅ **More focused** (what actually matters)
- ✅ **Less code** (no redundant frontend generation)
- ✅ **Same outcome** (complete working system)

FraiseQL doing the heavy lifting of frontend code generation means we can focus on what matters: **great SQL generation with rich metadata**.

---

**Timeline**: 10 days (2 weeks)
**Estimated Completion**: Week 1 = Teams C & D complete, Week 2 = Ship
**Risk Level**: LOW (most code already working)
**Confidence**: HIGH (building on solid foundation)
