# Team C: Action Compiler - Phased Implementation Plan

## Executive Summary

Team C must implement the **Action Compiler** that transforms SpecQL action definitions into production-ready PL/pgSQL functions with FraiseQL integration. This is a **COMPLEX** task requiring structured phased development with TDD discipline.

**Current Status**:
- 1 failing test reveals pre-existing bug in custom action code generation
- `test_custom_action_database_execution` failing due to incorrect validation logic
- Need complete rewrite/overhaul of action compilation system

**Estimated Duration**: 4-5 weeks (Weeks 3-7 of project)

---

## 🎯 Team C Mission (Refined)

**Transform**: SpecQL action steps → Type-safe PL/pgSQL functions with FraiseQL composite types

**Key Requirements**:
1. ✅ Returns `mutation_result` type (FraiseQL standard)
2. ✅ Uses PostgreSQL composite types for `_meta` (type-safe!)
3. ✅ Trinity pattern resolution (UUID → INTEGER)
4. ✅ Full object returns (not deltas) with relationships
5. ✅ Side effect tracking in `extra_metadata`
6. ✅ Runtime impact metadata generation
7. ✅ Audit field updates
8. ✅ Event emission
9. ✅ Error handling with typed errors

---

## 📋 PHASES

### Phase 1: Foundation - Core Infrastructure (Week 3, Days 1-3)

**Objective**: Set up core action compiler architecture with proper type system

#### TDD Cycle 1.1: Mutation Result Type Setup

**RED**: Write failing test for mutation_result type generation
```python
# tests/unit/actions/test_mutation_result_type.py
def test_generates_mutation_result_type_schema():
    """Verify mutation_result composite type is generated"""
    compiler = ActionCompiler()
    result = compiler.generate_base_types()

    assert "CREATE TYPE app.mutation_result AS (" in result
    assert "status TEXT" in result
    assert "message TEXT" in result
    assert "object_data JSONB" in result
    assert "updated_fields TEXT[]" in result
    assert "extra_metadata JSONB" in result
```

**Expected failure**: `ActionCompiler has no attribute 'generate_base_types'`

**GREEN**: Implement minimal code
```python
# src/generators/actions/action_compiler.py
class ActionCompiler:
    def generate_base_types(self) -> str:
        """Generate mutation_result composite type"""
        return """
CREATE TYPE app.mutation_result AS (
    id UUID,
    status TEXT,
    message TEXT,
    object_data JSONB,
    updated_fields TEXT[],
    extra_metadata JSONB
);
"""
```

**REFACTOR**:
- Use Jinja2 template from `templates/sql/000_types.sql.jinja2`
- Add proper comments and annotations

**QA**:
```bash
uv run pytest tests/unit/actions/test_mutation_result_type.py -v
```

---

#### TDD Cycle 1.2: Impact Metadata Composite Types

**RED**: Write failing test for impact metadata types
```python
# tests/unit/actions/test_impact_metadata_types.py
def test_generates_impact_metadata_types():
    """Verify mutation_metadata composite types are generated"""
    compiler = ActionCompiler()
    result = compiler.generate_metadata_types()

    assert "CREATE SCHEMA IF NOT EXISTS mutation_metadata" in result
    assert "CREATE TYPE mutation_metadata.entity_impact AS (" in result
    assert "entity_type TEXT" in result
    assert "operation TEXT" in result
    assert "modified_fields TEXT[]" in result
    assert "CREATE TYPE mutation_metadata.mutation_impact_metadata AS (" in result
```

**GREEN**: Implement composite type generation
```python
def generate_metadata_types(self) -> str:
    """Generate FraiseQL impact metadata composite types"""
    # Use template from templates/sql/000_types.sql.jinja2
    return render_template('000_types.sql.jinja2')
```

**REFACTOR**:
- Follow Team B's schema registry pattern
- Add FraiseQL annotations
- Proper type safety checks

**QA**:
```bash
uv run pytest tests/unit/actions/ -k metadata -v
```

---

#### TDD Cycle 1.3: Action Context & AST Integration

**RED**: Test action parsing and context setup
```python
# tests/unit/actions/test_action_context.py
def test_action_context_from_ast():
    """Build compilation context from action AST"""
    action_ast = ActionDefinition(
        name="qualify_lead",
        steps=[
            ValidateStep(condition="status = 'lead'", error="not_a_lead"),
            UpdateStep(target="Contact", fields={"status": "'qualified'"})
        ],
        impact=ImpactDeclaration(
            primary=EntityImpact(
                entity="Contact",
                operation="UPDATE",
                fields=["status", "updatedAt"]
            )
        )
    )

    context = ActionContext.from_ast(action_ast, entity_ast)

    assert context.function_name == "crm.qualify_lead"
    assert context.entity_schema == "crm"
    assert context.entity_name == "Contact"
    assert len(context.steps) == 2
    assert context.has_impact_metadata is True
```

**GREEN**: Implement ActionContext class
```python
# src/generators/actions/action_context.py
@dataclass
class ActionContext:
    function_name: str
    entity_schema: str
    entity_name: str
    steps: List[ActionStep]
    impact: Optional[ImpactDeclaration]
    has_impact_metadata: bool

    @classmethod
    def from_ast(cls, action_ast: ActionDefinition, entity_ast: Entity) -> 'ActionContext':
        return cls(
            function_name=f"{entity_ast.schema}.{action_ast.name}",
            entity_schema=entity_ast.schema,
            entity_name=entity_ast.name,
            steps=action_ast.steps,
            impact=action_ast.impact,
            has_impact_metadata=action_ast.impact is not None
        )
```

**REFACTOR**:
- Add validation
- Add helper methods for step processing
- Type annotations

**QA**: Full action context tests pass

---

### Phase 2: Basic Step Compilation (Week 3, Days 4-5 + Week 4, Days 1-2)

**Objective**: Compile basic action steps (validate, update, insert)

#### TDD Cycle 2.1: Validate Step Compilation

**RED**: Test validate step → SQL generation
```python
# tests/unit/actions/test_validate_step.py
def test_compile_validate_step_simple():
    """Compile validate step to PL/pgSQL IF check"""
    step = ValidateStep(condition="status = 'lead'", error="not_a_lead")
    context = create_test_context()

    compiler = ValidateStepCompiler()
    sql = compiler.compile(step, context)

    # Should generate variable fetch + validation
    assert "SELECT status INTO v_status" in sql
    assert "FROM crm.tb_contact" in sql
    assert "WHERE pk_contact = v_pk" in sql
    assert "IF v_status != 'lead' THEN" in sql
    assert "v_result.status := 'error'" in sql
    assert "v_result.message := 'not_a_lead'" in sql
    assert "RETURN v_result" in sql
```

**Expected failure**: `ValidateStepCompiler does not exist`

**GREEN**: Implement validate step compiler
```python
# src/generators/actions/step_compilers/validate_compiler.py
class ValidateStepCompiler:
    def compile(self, step: ValidateStep, context: ActionContext) -> str:
        # Parse condition to extract field
        field = self._extract_field(step.condition)
        expected_value = self._extract_value(step.condition)

        return f"""
    -- Validation: {step.condition}
    SELECT {field} INTO v_{field}
    FROM {context.entity_schema}.tb_{context.entity_name.lower()}
    WHERE pk_{context.entity_name.lower()} = v_pk;

    IF v_{field} != {expected_value} THEN
        v_result.status := 'error';
        v_result.message := '{step.error}';
        v_result.object_data := (
            SELECT jsonb_build_object(
                '__typename', '{context.entity_name}',
                'id', c.id,
                '{field}', c.{field}
            )
            FROM {context.entity_schema}.tb_{context.entity_name.lower()} c
            WHERE c.pk_{context.entity_name.lower()} = v_pk
        );
        RETURN v_result;
    END IF;
"""
```

**REFACTOR**:
- Use expression parser (reuse from Team A if available)
- Template-based generation
- Handle complex conditions (AND/OR)
- Type-safe field resolution

**QA**: All validate step tests pass

---

#### TDD Cycle 2.2: Update Step Compilation

**RED**: Test update step → SQL UPDATE generation
```python
# tests/unit/actions/test_update_step.py
def test_compile_update_step_simple():
    """Compile update step to SQL UPDATE"""
    step = UpdateStep(target="Contact", fields={"status": "'qualified'"})
    context = create_test_context()

    compiler = UpdateStepCompiler()
    sql = compiler.compile(step, context)

    assert "UPDATE crm.tb_contact" in sql
    assert "SET status = 'qualified'" in sql
    assert "updated_at = now()" in sql  # Auto-audit
    assert "updated_by = p_caller_id" in sql  # Auto-audit
    assert "WHERE pk_contact = v_pk" in sql
```

**GREEN**: Implement update step compiler
```python
# src/generators/actions/step_compilers/update_compiler.py
class UpdateStepCompiler:
    def compile(self, step: UpdateStep, context: ActionContext) -> str:
        # Extract SET clause fields
        set_clauses = [f"{field} = {value}" for field, value in step.fields.items()]

        # Add audit fields automatically
        set_clauses.append("updated_at = now()")
        set_clauses.append("updated_by = p_caller_id")

        return f"""
    -- Update: {step.target}
    UPDATE {context.entity_schema}.tb_{step.target.lower()}
    SET {', '.join(set_clauses)}
    WHERE pk_{step.target.lower()} = v_pk;
"""
```

**REFACTOR**:
- Expression evaluation for field values
- Support for complex expressions
- Handle NULL values properly
- Reserved field validation (use Team B's reserved_fields module)

**QA**: Update step tests pass

---

#### TDD Cycle 2.3: Insert Step Compilation

**RED**: Test insert step → SQL INSERT generation
```python
# tests/unit/actions/test_insert_step.py
def test_compile_insert_step_simple():
    """Compile insert step to SQL INSERT"""
    step = InsertStep(
        target="Notification",
        fields={
            "fk_contact": "v_pk",
            "message": "'Contact qualified'",
            "notification_type": "'email'"
        }
    )
    context = create_test_context()

    compiler = InsertStepCompiler()
    sql = compiler.compile(step, context)

    assert "INSERT INTO core.tb_notification" in sql
    assert "fk_contact, message, notification_type" in sql
    assert "VALUES (v_pk, 'Contact qualified', 'email')" in sql
    assert "RETURNING id INTO v_notification_id" in sql  # Track created entity
```

**GREEN**: Implement insert step compiler

**REFACTOR**:
- Auto-add tenant_id if schema is multi-tenant
- Use schema_registry for tenant detection
- Track created IDs for side effect metadata

**QA**: Insert step tests pass

---

### Phase 3: Function Scaffolding (Week 4, Days 3-5)

**Objective**: Generate complete PL/pgSQL function wrapper with proper structure

#### TDD Cycle 3.1: Function Signature Generation

**RED**: Test function signature with parameters
```python
# tests/unit/actions/test_function_signature.py
def test_generate_function_signature():
    """Generate proper function signature from action"""
    action = ActionDefinition(name="qualify_lead", parameters=["contact_id"])
    context = ActionContext.from_ast(action, entity_ast)

    generator = FunctionGenerator()
    signature = generator.generate_signature(context)

    assert "CREATE OR REPLACE FUNCTION crm.qualify_lead(" in signature
    assert "p_contact_id UUID" in signature
    assert "p_caller_id UUID DEFAULT NULL" in signature  # Auto-added
    assert "RETURNS mutation_result" in signature  # FraiseQL type
```

**GREEN**: Implement signature generation

**REFACTOR**:
- Parameter type inference
- Auto-add audit parameters (caller_id, tenant_id)
- Proper NULL defaults

**QA**: Signature tests pass

---

#### TDD Cycle 3.2: Variable Declaration Block

**RED**: Test DECLARE block generation
```python
def test_generate_declare_block():
    """Generate DECLARE block with proper variable types"""
    context = create_test_context()

    generator = FunctionGenerator()
    declare_block = generator.generate_declare_block(context)

    assert "v_pk INTEGER" in declare_block  # Trinity resolution
    assert "v_result mutation_result" in declare_block  # Return value
    assert "v_meta mutation_metadata.mutation_impact_metadata" in declare_block  # Impact
```

**GREEN**: Implement DECLARE block generation

**REFACTOR**:
- Infer needed variables from steps
- Type-safe variable declarations
- Conditional variables (only if impact metadata needed)

**QA**: DECLARE tests pass

---

#### TDD Cycle 3.3: Trinity Resolution

**RED**: Test automatic UUID → INTEGER resolution
```python
def test_generates_trinity_resolution():
    """Auto-generate Trinity helper call"""
    context = create_test_context()

    generator = FunctionGenerator()
    resolution = generator.generate_trinity_resolution(context)

    assert "v_pk := crm.contact_pk(p_contact_id)" in resolution
```

**GREEN**: Implement Trinity resolution using Team B's helpers

**REFACTOR**: Use schema_registry to determine correct helper function

**QA**: Trinity resolution tests pass

---

### Phase 4: Success Response Generation (Week 5, Days 1-3)

**Objective**: Generate complete mutation_result success response with relationships and metadata

#### TDD Cycle 4.1: Primary Object Data with Relationships

**RED**: Test full object return with declared relationships
```python
# tests/unit/actions/test_success_response.py
def test_generates_object_data_with_relationships():
    """Generate object_data with relationships from impact.include_relations"""
    impact = ImpactDeclaration(
        primary=EntityImpact(
            entity="Contact",
            operation="UPDATE",
            fields=["status", "updatedAt"],
            include_relations=["company"]
        )
    )
    context = create_test_context(impact=impact)

    generator = SuccessResponseGenerator()
    object_sql = generator.generate_object_data(context)

    assert "SELECT jsonb_build_object(" in object_sql
    assert "'__typename', 'Contact'" in object_sql
    assert "'id', c.id" in object_sql
    assert "'status', c.status" in object_sql
    assert "'company', jsonb_build_object(" in object_sql  # Relationship
    assert "'__typename', 'Company'" in object_sql
    assert "LEFT JOIN management.tb_company co ON co.pk_company = c.fk_company" in object_sql
```

**GREEN**: Implement object_data generation with relationship resolution

**REFACTOR**:
- Use entity AST to resolve relationship fields
- Auto-detect FK columns from schema_registry
- Handle multi-level relationships
- Proper NULL handling for optional relations

**QA**: Object data tests pass

---

#### TDD Cycle 4.2: Impact Metadata Generation (Composite Types!)

**RED**: Test type-safe impact metadata construction
```python
def test_generates_impact_metadata_composite_type():
    """Generate _meta using type-safe composite type construction"""
    context = create_test_context_with_impact()

    generator = ImpactMetadataGenerator()
    meta_sql = generator.generate_metadata(context)

    # Should use ROW constructor with proper typing
    assert "v_meta.primary_entity := ROW(" in meta_sql
    assert "'Contact'," in meta_sql  # entity_type
    assert "'UPDATE'," in meta_sql  # operation
    assert "ARRAY['status', 'updated_at']" in meta_sql  # modified_fields
    assert ")::mutation_metadata.entity_impact" in meta_sql  # Type cast!

    # Should handle side effects array
    assert "v_meta.actual_side_effects := ARRAY[" in meta_sql
    assert "ROW('Notification', 'CREATE'" in meta_sql

    # Should convert to JSONB for return
    assert "to_jsonb(v_meta)" in meta_sql
```

**GREEN**: Implement type-safe metadata generation
```python
# src/generators/actions/impact_metadata_generator.py
class ImpactMetadataGenerator:
    def generate_metadata(self, context: ActionContext) -> str:
        if not context.has_impact_metadata:
            return ""

        impact = context.impact

        # Type-safe composite type construction
        primary = f"""
        v_meta.primary_entity := ROW(
            '{impact.primary.entity}',
            '{impact.primary.operation}',
            ARRAY{impact.primary.fields}::TEXT[]
        )::mutation_metadata.entity_impact;
"""

        # Side effects array (if any)
        side_effects = ""
        if impact.side_effects:
            effects = [
                f"ROW('{se.entity}', '{se.operation}', ARRAY{se.fields}::TEXT[])::mutation_metadata.entity_impact"
                for se in impact.side_effects
            ]
            side_effects = f"""
        v_meta.actual_side_effects := ARRAY[
            {', '.join(effects)}
        ];
"""

        # Cache invalidations
        cache_inv = ""
        if impact.cache_invalidations:
            invalidations = [
                f"ROW('{ci.query}', '{ci.filter}'::jsonb, '{ci.strategy}', '{ci.reason}')::mutation_metadata.cache_invalidation"
                for ci in impact.cache_invalidations
            ]
            cache_inv = f"""
        v_meta.cache_invalidations := ARRAY[
            {', '.join(invalidations)}
        ];
"""

        return primary + side_effects + cache_inv
```

**REFACTOR**:
- Use Jinja2 templates
- Validate composite type fields
- Handle optional fields
- Type checking

**QA**:
```bash
uv run pytest tests/unit/actions/test_impact_metadata.py -v
# Should verify PostgreSQL accepts the composite type syntax
```

---

#### TDD Cycle 4.3: Side Effects Collection

**RED**: Test side effect entity collection in extra_metadata
```python
def test_generates_side_effect_collections():
    """Collect created entities in extra_metadata collections"""
    impact = ImpactDeclaration(
        side_effects=[
            EntityImpact(
                entity="Notification",
                operation="CREATE",
                collection="createdNotifications"
            )
        ]
    )
    context = create_test_context(impact=impact)

    generator = SideEffectCollector()
    collections_sql = generator.generate_collections(context)

    assert "'createdNotifications'," in collections_sql
    assert "SELECT COALESCE(jsonb_agg(" in collections_sql
    assert "FROM core.tb_notification n" in collections_sql
    assert "WHERE n.fk_contact = v_pk" in collections_sql
    assert "AND n.created_at > (now() - interval '1 second')" in collections_sql  # Recent only
```

**GREEN**: Implement side effect collection queries

**REFACTOR**:
- Time-based filtering for "recent" entities
- Track created IDs from INSERT steps
- Use tracked IDs instead of time-based filtering (more reliable)

**QA**: Side effect tests pass

---

### Phase 5: Conditional Logic & Advanced Steps (Week 5, Days 4-5 + Week 6, Days 1-2)

**Objective**: Support if/then/else, loops, and complex action patterns

#### TDD Cycle 5.1: If/Then/Else Compilation

**RED**: Test conditional step compilation
```python
def test_compile_if_then_else():
    """Compile conditional logic to PL/pgSQL IF"""
    step = ConditionalStep(
        condition="status = 'lead'",
        then_steps=[UpdateStep(...)],
        else_steps=[RaiseErrorStep(...)]
    )

    compiler = ConditionalStepCompiler()
    sql = compiler.compile(step, context)

    assert "IF v_status = 'lead' THEN" in sql
    assert "UPDATE crm.tb_contact" in sql
    assert "ELSE" in sql
    assert "RAISE EXCEPTION" in sql
    assert "END IF" in sql
```

**GREEN**: Implement nested step compilation

**REFACTOR**:
- Recursive step compilation
- Proper indentation
- Nested condition support

**QA**: Conditional tests pass

---

#### TDD Cycle 5.2: Call Step (Function Invocation)

**RED**: Test calling other functions
```python
def test_compile_call_step():
    """Compile function call step"""
    step = CallStep(
        function="notify_owner",
        arguments={"contact_id": "p_contact_id", "message": "'Qualified'"}
    )

    compiler = CallStepCompiler()
    sql = compiler.compile(step, context)

    assert "PERFORM core.notify_owner(" in sql
    assert "p_contact_id," in sql
    assert "'Qualified'" in sql
```

**GREEN**: Implement function call generation

**REFACTOR**:
- Function resolution (schema.function)
- Parameter mapping
- Return value handling (if needed)

**QA**: Call step tests pass

---

#### TDD Cycle 5.3: Notify Step (Event Emission)

**RED**: Test event emission step
```python
def test_compile_notify_step():
    """Compile notify step to event emission"""
    step = NotifyStep(
        target="owner",
        channel="email",
        message="Contact qualified"
    )

    compiler = NotifyStepCompiler()
    sql = compiler.compile(step, context)

    assert "PERFORM core.emit_event(" in sql
    assert "'contact.qualified'" in sql
    assert "jsonb_build_object('id', p_contact_id)" in sql
```

**GREEN**: Implement event emission

**REFACTOR**:
- Event naming conventions
- Payload construction
- Integration with event system

**QA**: Notify tests pass

---

### Phase 6: Error Handling & Edge Cases (Week 6, Days 3-5)

**Objective**: Robust error handling, validation, and edge case coverage

#### TDD Cycle 6.1: Typed Error Responses

**RED**: Test error response generation
```python
def test_generates_typed_error_response():
    """Generate proper error response in mutation_result"""
    step = ValidateStep(condition="status = 'lead'", error="not_a_lead")

    compiler = ValidateStepCompiler()
    sql = compiler.compile(step, context)

    # Error response structure
    assert "v_result.status := 'error'" in sql
    assert "v_result.message := 'not_a_lead'" in sql
    assert "v_result.object_data := (" in sql  # Still return current object
    assert "__typename" in sql
```

**GREEN**: Implement error response generation

**REFACTOR**:
- Error code mapping
- User-friendly messages
- Include current state in error response

**QA**: Error handling tests pass

---

#### TDD Cycle 6.2: Exception Handling

**RED**: Test PostgreSQL exception handling
```python
def test_generates_exception_handler():
    """Wrap function in EXCEPTION handler"""
    context = create_test_context()

    generator = FunctionGenerator()
    function_sql = generator.generate_function(context)

    assert "EXCEPTION" in function_sql
    assert "WHEN OTHERS THEN" in function_sql
    assert "v_result.status := 'error'" in function_sql
    assert "SQLERRM" in function_sql  # Include error message
```

**GREEN**: Add EXCEPTION block to function template

**REFACTOR**:
- Specific exception types
- Error logging
- Rollback handling

**QA**: Exception tests pass

---

#### TDD Cycle 6.3: Validation of Generated SQL

**RED**: Test that generated SQL is valid PostgreSQL
```python
def test_generated_sql_is_valid_postgres():
    """Verify generated function compiles in PostgreSQL"""
    action = create_qualify_lead_action()
    entity = create_contact_entity()

    compiler = ActionCompiler()
    sql = compiler.compile_action(action, entity)

    # Execute in test database
    with test_db.cursor() as cur:
        cur.execute(sql)  # Should not raise syntax error
```

**GREEN**: Database integration test

**REFACTOR**:
- SQL syntax validation
- Type checking
- Indentation and formatting

**QA**:
```bash
uv run pytest tests/integration/actions/ -v
```

---

### Phase 7: Integration & Optimization (Week 7, Days 1-3)

**Objective**: End-to-end integration, performance, and production readiness

#### TDD Cycle 7.1: Full End-to-End Test (Fix Current Failure!)

**RED**: Fix `test_custom_action_database_execution`
```python
# tests/integration/actions/test_database_roundtrip.py
def test_custom_action_database_execution():
    """Execute qualify_lead action in real database"""
    # This test is CURRENTLY FAILING - Phase 7 will fix it!

    # Generate function from SpecQL
    action = parse_qualify_lead_action()
    entity = parse_contact_entity()

    compiler = ActionCompiler()
    function_sql = compiler.compile_action(action, entity)

    # Deploy to test database
    with test_db.cursor() as cur:
        cur.execute(function_sql)

    # Insert test contact
    contact_id = create_test_contact(status='lead')

    # Execute action
    result = execute_function('crm.qualify_lead', contact_id=contact_id)

    # Verify success response
    assert result['status'] == 'success'
    assert result['object_data']['__typename'] == 'Contact'
    assert result['object_data']['status'] == 'qualified'

    # Verify database state
    contact = get_contact(contact_id)
    assert contact['status'] == 'qualified'
    assert contact['updated_at'] is not None
```

**GREEN**: Complete ActionCompiler implementation to make test pass

**REFACTOR**:
- Code quality
- Performance optimization
- Proper error messages

**QA**:
```bash
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_custom_action_database_execution -v
# Should PASS after Phase 7!
```

---

#### TDD Cycle 7.2: Performance Testing

**RED**: Test function execution performance
```python
def test_action_execution_performance():
    """Verify action executes in < 100ms"""
    contact_id = create_test_contact()

    start = time.time()
    for _ in range(100):
        execute_function('crm.qualify_lead', contact_id=contact_id)
    duration = time.time() - start

    avg_duration = duration / 100
    assert avg_duration < 0.1  # < 100ms per call
```

**GREEN**: Optimize generated SQL

**REFACTOR**:
- Query optimization
- Index usage verification
- Minimize round trips

**QA**: Performance benchmarks pass

---

#### TDD Cycle 7.3: FraiseQL Integration Validation

**RED**: Verify FraiseQL can introspect generated functions
```python
def test_fraiseql_discovers_generated_function():
    """FraiseQL should discover mutation from COMMENT annotation"""
    # Generate function with Team D metadata
    function_sql = generate_with_fraiseql_metadata()

    # Deploy
    execute_sql(function_sql)

    # Verify COMMENT exists
    comment = get_function_comment('crm.qualify_lead')
    assert '@fraiseql:mutation' in comment
    assert 'name=qualifyLead' in comment
    assert 'success_type=QualifyLeadSuccess' in comment

    # Verify composite types have comments
    meta_comment = get_type_comment('mutation_metadata.mutation_impact_metadata')
    assert '@fraiseql:type' in meta_comment
```

**GREEN**: Integrate with Team D's FraiseQL metadata generator

**REFACTOR**: Ensure all metadata is correct

**QA**: FraiseQL integration tests pass

---

### Phase 8: Documentation & Cleanup (Week 7, Days 4-5)

**Objective**: Production-ready code, documentation, and handoff

#### Tasks:
1. **Code Documentation**
   - Add docstrings to all classes/methods
   - Document template variables
   - Add inline comments for complex logic

2. **User Documentation**
   - Update `docs/guides/action-compilation.md`
   - Add examples for each step type
   - Document impact metadata format

3. **Test Coverage**
   - Achieve 90%+ coverage
   - Add missing edge cases
   - Document test strategy

4. **Performance Documentation**
   - Document optimization techniques
   - Add performance benchmarks
   - Create tuning guide

5. **Cleanup**
   - Remove debug code
   - Fix linting issues
   - Update type annotations

---

## 🎯 Success Criteria

### Phase Completion Checklist

- [ ] **Phase 1**: Core infrastructure (mutation_result, composite types, context)
  - [ ] All base types generated
  - [ ] ActionContext working
  - [ ] Tests passing

- [ ] **Phase 2**: Basic steps (validate, update, insert)
  - [ ] ValidateStepCompiler working
  - [ ] UpdateStepCompiler working
  - [ ] InsertStepCompiler working
  - [ ] Tests passing

- [ ] **Phase 3**: Function scaffolding
  - [ ] Function signatures correct
  - [ ] DECLARE blocks complete
  - [ ] Trinity resolution working
  - [ ] Tests passing

- [ ] **Phase 4**: Success responses
  - [ ] Object data with relationships
  - [ ] Type-safe impact metadata (composite types!)
  - [ ] Side effect collections
  - [ ] Tests passing

- [ ] **Phase 5**: Advanced steps
  - [ ] If/then/else working
  - [ ] Call step working
  - [ ] Notify step working
  - [ ] Tests passing

- [ ] **Phase 6**: Error handling
  - [ ] Typed error responses
  - [ ] Exception handling
  - [ ] SQL validation
  - [ ] Tests passing

- [ ] **Phase 7**: Integration
  - [ ] `test_custom_action_database_execution` PASSING ✅
  - [ ] Performance benchmarks met
  - [ ] FraiseQL integration verified
  - [ ] All integration tests passing

- [ ] **Phase 8**: Production ready
  - [ ] Documentation complete
  - [ ] 90%+ test coverage
  - [ ] Code quality checks pass
  - [ ] Ready for Team E orchestration

---

## 🧪 Test Strategy

### Test Pyramid

```
         /\
        /E2E\         Integration: 10% (database execution)
       /------\
      /  INT   \      Integration: 20% (SQL validation)
     /----------\
    /    UNIT    \    Unit: 70% (step compilers, generators)
   /--------------\
```

### Test Commands

```bash
# Unit tests (fast, no database)
uv run pytest tests/unit/actions/ -v

# Integration tests (requires test database)
uv run pytest tests/integration/actions/ -v

# Specific test
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_custom_action_database_execution -v

# Coverage
uv run pytest tests/unit/actions/ --cov=src/generators/actions --cov-report=html

# Performance tests
uv run pytest tests/integration/actions/ -k performance -v
```

---

## 📊 Progress Tracking

### Week-by-Week Goals

| Week | Phase | Goal | Success Metric |
|------|-------|------|----------------|
| Week 3, Days 1-3 | Phase 1 | Core infrastructure | Base types + context working |
| Week 3, Days 4-5 + Week 4, Days 1-2 | Phase 2 | Basic steps | 3 step compilers working |
| Week 4, Days 3-5 | Phase 3 | Function scaffolding | Complete function generated |
| Week 5, Days 1-3 | Phase 4 | Success responses | Full mutation_result with metadata |
| Week 5, Days 4-5 + Week 6, Days 1-2 | Phase 5 | Advanced steps | Conditionals + calls working |
| Week 6, Days 3-5 | Phase 6 | Error handling | Robust error responses |
| Week 7, Days 1-3 | Phase 7 | Integration | **Current failing test PASSES** ✅ |
| Week 7, Days 4-5 | Phase 8 | Documentation | Production ready |

---

## 🚨 Critical Dependencies

### From Team A (SpecQL Parser)
- ✅ ActionDefinition AST
- ✅ Step type definitions
- ⚠️ May need ImpactDeclaration in AST (check if exists)

### From Team B (Schema Generator)
- ✅ schema_registry module
- ✅ Trinity helper functions
- ✅ reserved_fields validation
- ⚠️ Need composite type templates (000_types.sql.jinja2)

### From Team D (FraiseQL Metadata)
- ⚠️ Metadata annotation format (coordinate!)
- ⚠️ Composite type naming conventions

### For Team E (Orchestration)
- Stable API for action compilation
- Clear error messages
- Proper logging

---

## 💡 Key Design Decisions

### 1. **Use Composite Types for Metadata** (FraiseQL Recommended!)
**Decision**: Use PostgreSQL composite types instead of JSONB for `_meta`

**Reasoning**:
- ✅ Type-safe at database level
- ✅ Compile-time validation
- ✅ Better performance (binary format)
- ✅ FraiseQL team confirmed this is best practice

**Implementation**:
```sql
-- Type-safe construction
v_meta.primary_entity := ROW(
    'Contact',
    'UPDATE',
    ARRAY['status']::TEXT[]
)::mutation_metadata.entity_impact;
```

### 2. **Full Object Returns (Not Deltas)**
**Decision**: Return complete entity in `object_data`, not just modified fields

**Reasoning**:
- ✅ Apollo cache normalization works better
- ✅ Frontend gets complete state
- ✅ Simplifies frontend logic

### 3. **Auto-Audit Fields**
**Decision**: Automatically update `updated_at`, `updated_by` on all UPDATEs

**Reasoning**:
- ✅ Consistency across all actions
- ✅ Users don't forget
- ✅ Framework convention

### 4. **Trinity Resolution First**
**Decision**: Always resolve UUID → INTEGER at function start

**Reasoning**:
- ✅ Consistent with framework pattern
- ✅ Better query performance
- ✅ Single resolution point

---

## 🎓 Learning Resources for Team C

### PostgreSQL PL/pgSQL
- Composite types: https://www.postgresql.org/docs/current/rowtypes.html
- Function best practices: https://wiki.postgresql.org/wiki/PL/pgSQL_FAQ
- Error handling: https://www.postgresql.org/docs/current/plpgsql-errors-and-messages.html

### Project-Specific
- FraiseQL integration: `docs/analysis/FRAISEQL_INTEGRATION_REQUIREMENTS.md`
- Trinity pattern: `docs/analysis/POC_RESULTS.md`
- Action syntax: `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md`

---

## 🏁 Final Deliverable

**Complete ActionCompiler** that:
1. ✅ Transforms SpecQL actions → PL/pgSQL functions
2. ✅ Returns type-safe `mutation_result`
3. ✅ Uses composite types for impact metadata
4. ✅ Includes full objects + relationships
5. ✅ Tracks side effects
6. ✅ Handles errors gracefully
7. ✅ Integrates with FraiseQL
8. ✅ **Passes all tests, including `test_custom_action_database_execution`** 🎯

**Estimated Completion**: End of Week 7 (5 weeks total)

**Test Pass Rate Target**: 100% (496/496 tests passing)

---

*Phased TDD Development Plan for Team C*
*Focus: Type-Safe Actions • FraiseQL Integration • Production Ready*
