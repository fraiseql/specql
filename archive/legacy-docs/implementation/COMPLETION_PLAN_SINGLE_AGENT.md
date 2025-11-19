# Complete SpecQL System - Single Agent Phased TDD Plan

**Goal**: Finish the remaining 25-30% of the SpecQL → PostgreSQL → GraphQL system
**Timeline**: 3-4 weeks (15-20 working days)
**Methodology**: TDD cycles (RED → GREEN → REFACTOR → QA) for each phase
**Progress Tracking**: Update this file after each phase completion

---

## 📊 Starting Point Assessment

**Current Completion**: 70-75%

| Team | Status | What's Done | What's Missing |
|------|--------|-------------|----------------|
| Team A | 95% | Parser complete | Edge cases |
| Team B | 90% | Schema gen complete | Mutation metadata schema |
| Team C | 85% | CRUD actions work | Custom actions |
| Team D | 50% | Type system design | GraphQL generation |
| Team E | 30% | Basic orchestration | CLI commands, docs |

**Test Status**: 305/312 passing (98%)

---

## 🎯 Overall Strategy

### Three Major Workstreams

1. **Team D - FraiseQL Integration** (10 days)
   - GraphQL metadata generation
   - Frontend code generation
   - Most critical gap

2. **Team C - Custom Actions** (3 days)
   - Complete action compiler
   - Enable complex workflows

3. **Team E - CLI & Developer Experience** (5 days)
   - Developer tools
   - Documentation generation
   - Polish & ship

---

## 📅 PHASE PLAN OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│ WEEK 1: Team D - FraiseQL Core                         │
│ Days 1-5: GraphQL metadata + mutation annotations      │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ WEEK 2: Team D - Frontend Codegen                      │
│ Days 6-10: TypeScript types + mutation hooks           │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ WEEK 3: Team C + Team E                                │
│ Days 11-13: Custom actions (Team C)                    │
│ Days 14-15: CLI commands (Team E)                      │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ WEEK 4: Integration & Ship                             │
│ Days 16-18: End-to-end testing + docs                  │
│ Days 19-20: Polish & release                           │
└─────────────────────────────────────────────────────────┘
```

---

# WEEK 1: Team D - FraiseQL Core (Days 1-5)

## Phase 1: Mutation Metadata Schema (Day 1)

**Objective**: Generate the `mutation_metadata` schema with composite types for FraiseQL

### TDD Cycle 1: Entity Impact Type

**🔴 RED** (30 min)
```python
# tests/unit/generators/test_mutation_metadata_generator.py
def test_generate_entity_impact_type():
    """Generate mutation_metadata.entity_impact composite type"""
    generator = MutationMetadataGenerator()
    sql = generator.generate_entity_impact_type()

    assert "CREATE TYPE mutation_metadata.entity_impact AS" in sql
    assert "entity_type TEXT" in sql
    assert "operation TEXT" in sql
    assert "modified_fields TEXT[]" in sql
    assert "@fraiseql:type name=EntityImpact" in sql
```

Run: `uv run pytest tests/unit/generators/test_mutation_metadata_generator.py::test_generate_entity_impact_type -v`
Expected: **FAIL** (file doesn't exist)

**🟢 GREEN** (45 min)
1. Create `src/generators/mutation_metadata_generator.py`
2. Implement `generate_entity_impact_type()` method
3. Return SQL with composite type definition

```python
class MutationMetadataGenerator:
    def generate_entity_impact_type(self) -> str:
        return """
CREATE TYPE mutation_metadata.entity_impact AS (
    entity_type TEXT,
    operation TEXT,
    modified_fields TEXT[]
);

COMMENT ON TYPE mutation_metadata.entity_impact IS
  '@fraiseql:type name=EntityImpact';
"""
```

Run: `uv run pytest tests/unit/generators/test_mutation_metadata_generator.py::test_generate_entity_impact_type -v`
Expected: **PASS**

**🔧 REFACTOR** (15 min)
- Extract template to `templates/sql/mutation_metadata_types.sql.j2`
- Use Jinja2 for rendering
- Add type safety checks

Run: `uv run pytest tests/unit/generators/test_mutation_metadata_generator.py -v`
Expected: All pass

**✅ QA** (10 min)
- Run full test suite: `uv run pytest`
- Check code quality: `uv run ruff check src/generators/mutation_metadata_generator.py`
- Verify no regressions

---

### TDD Cycle 2: Cache Invalidation Type

**🔴 RED** (20 min)
```python
def test_generate_cache_invalidation_type():
    """Generate mutation_metadata.cache_invalidation composite type"""
    generator = MutationMetadataGenerator()
    sql = generator.generate_cache_invalidation_type()

    assert "CREATE TYPE mutation_metadata.cache_invalidation AS" in sql
    assert "query_name TEXT" in sql
    assert "filter_json JSONB" in sql
    assert "strategy TEXT" in sql
    assert "reason TEXT" in sql
```

Run: `uv run pytest tests/unit/generators/test_mutation_metadata_generator.py::test_generate_cache_invalidation_type -v`
Expected: **FAIL**

**🟢 GREEN** (30 min)
Implement `generate_cache_invalidation_type()` method

**🔧 REFACTOR** (15 min)
Clean up template usage

**✅ QA** (10 min)
Run full test suite

---

### TDD Cycle 3: Complete Metadata Schema

**🔴 RED** (30 min)
```python
def test_generate_complete_mutation_metadata_schema():
    """Generate complete mutation_metadata schema"""
    generator = MutationMetadataGenerator()
    sql = generator.generate_complete_schema()

    # Should include schema creation
    assert "CREATE SCHEMA IF NOT EXISTS mutation_metadata" in sql

    # All three types
    assert "entity_impact" in sql
    assert "cache_invalidation" in sql
    assert "mutation_impact_metadata" in sql

    # FraiseQL annotations
    assert "@fraiseql:type name=MutationImpactMetadata" in sql
```

**🟢 GREEN** (1 hour)
Implement complete schema generation

**🔧 REFACTOR** (30 min)
- Ensure proper ordering (dependencies first)
- Add schema-level comments
- Template optimization

**✅ QA** (15 min)
- Full test suite
- Integration test with SchemaOrchestrator

**END OF DAY 1**: Mutation metadata schema types complete

---

## Phase 2: Mutation Annotation Generator (Day 2)

**Objective**: Generate @fraiseql:mutation annotations for action functions

### TDD Cycle 1: Basic Mutation Annotation

**🔴 RED** (30 min)
```python
# tests/unit/generators/test_fraiseql_annotator.py
def test_generate_mutation_annotation_for_create_action():
    """Generate @fraiseql:mutation annotation for CREATE action"""
    entity = Entity(name="Contact", schema="crm", fields={...})
    action = Action(name="create_contact", steps=[...])

    annotator = FraiseQLAnnotator()
    sql = annotator.generate_mutation_annotation(entity, action)

    assert "COMMENT ON FUNCTION crm.create_contact" in sql
    assert "@fraiseql:mutation" in sql
    assert "name=createContact" in sql
    assert "input=CreateContactInput" in sql
    assert "success_type=CreateContactSuccess" in sql
    assert "error_type=CreateContactError" in sql
```

Run: `uv run pytest tests/unit/generators/test_fraiseql_annotator.py::test_generate_mutation_annotation_for_create_action -v`
Expected: **FAIL**

**🟢 GREEN** (1 hour)
1. Create `src/generators/fraiseql_annotator.py`
2. Implement `generate_mutation_annotation()` method
3. Parse action metadata to build annotation

```python
class FraiseQLAnnotator:
    def generate_mutation_annotation(self, entity: Entity, action: Action) -> str:
        mutation_name = self._to_camel_case(action.name)
        input_type = self._to_pascal_case(action.name) + "Input"
        success_type = self._to_pascal_case(action.name) + "Success"
        error_type = self._to_pascal_case(action.name) + "Error"

        annotation = f"""
COMMENT ON FUNCTION {entity.schema}.{action.name} IS
  '@fraiseql:mutation
   name={mutation_name}
   input={input_type}
   success_type={success_type}
   error_type={error_type}
   primary_entity={entity.name}';
"""
        return annotation
```

**🔧 REFACTOR** (30 min)
- Extract name transformation to helper methods
- Add validation for annotation format
- Template-based generation

**✅ QA** (15 min)
Full test suite

---

### TDD Cycle 2: Impact Metadata in Annotations

**🔴 RED** (30 min)
```python
def test_mutation_annotation_includes_impact_metadata():
    """Annotation should include impact hints for FraiseQL"""
    entity = Entity(...)
    action = Action(
        name="qualify_lead",
        impact=ImpactDeclaration(
            primary=EntityImpact(entity="Contact", operation="UPDATE", fields=["status"]),
            side_effects=[EntityImpact(entity="Notification", operation="CREATE")],
            optimistic_safe=True
        )
    )

    annotator = FraiseQLAnnotator()
    sql = annotator.generate_mutation_annotation(entity, action)

    assert "metadata_mapping" in sql
    assert '"_meta": "MutationImpactMetadata"' in sql
    assert "impact={" in sql
    assert '"optimistic_safe": true' in sql
```

**🟢 GREEN** (1.5 hours)
Implement impact metadata serialization to annotation

**🔧 REFACTOR** (30 min)
Clean up JSON serialization, format annotation

**✅ QA** (15 min)
Full test suite

**END OF DAY 2**: FraiseQL mutation annotations complete

---

## Phase 3: Mutation Impacts JSON Generator (Day 3)

**Objective**: Generate `mutation-impacts.json` for frontend consumption

### TDD Cycle 1: Basic Impact JSON Structure

**🔴 RED** (45 min)
```python
# tests/unit/generators/test_impact_json_generator.py
def test_generate_impact_json_for_single_mutation():
    """Generate mutation impact JSON for a single action"""
    entity = Entity(...)
    action = Action(name="qualify_lead", steps=[...])

    generator = ImpactJsonGenerator()
    impact_data = generator.generate_impact_for_action(entity, action)

    assert impact_data["description"] is not None
    assert "input" in impact_data
    assert "impact" in impact_data
    assert impact_data["impact"]["primary"]["entity"] == "Contact"
    assert impact_data["impact"]["primary"]["operation"] == "UPDATE"
    assert len(impact_data["impact"]["sideEffects"]) >= 0
    assert len(impact_data["impact"]["cacheInvalidations"]) >= 0
```

Run: `uv run pytest tests/unit/generators/test_impact_json_generator.py::test_generate_impact_json_for_single_mutation -v`
Expected: **FAIL**

**🟢 GREEN** (2 hours)
1. Create `src/generators/impact_json_generator.py`
2. Implement `generate_impact_for_action()` method
3. Build JSON structure from action steps analysis

```python
class ImpactJsonGenerator:
    def generate_impact_for_action(self, entity: Entity, action: Action) -> dict:
        return {
            "description": self._generate_description(action),
            "input": self._extract_input_schema(entity, action),
            "impact": {
                "primary": self._analyze_primary_impact(entity, action),
                "sideEffects": self._analyze_side_effects(action),
                "cacheInvalidations": self._infer_cache_invalidations(entity, action),
                "permissions": self._extract_permissions(action),
                "optimisticUpdateSafe": self._is_optimistic_safe(action),
                "idempotent": self._is_idempotent(action),
                "estimatedDuration": 150  # ms, can be refined
            },
            "examples": self._generate_examples(entity, action),
            "errors": self._extract_possible_errors(action)
        }
```

**🔧 REFACTOR** (1 hour)
- Break down into smaller helper methods
- Add validation for JSON schema
- Document expected format

**✅ QA** (20 min)
Full test suite + JSON validation

---

### TDD Cycle 2: Complete mutation-impacts.json File

**🔴 RED** (30 min)
```python
def test_generate_complete_mutation_impacts_json():
    """Generate complete mutation-impacts.json for all entities"""
    entities = [
        Entity(name="Contact", actions=[...]),
        Entity(name="Company", actions=[...])
    ]

    generator = ImpactJsonGenerator()
    json_output = generator.generate_complete_impacts_file(entities)

    data = json.loads(json_output)
    assert data["version"] == "1.0.0"
    assert "generatedAt" in data
    assert "mutations" in data
    assert "qualifyLead" in data["mutations"]
    assert "createContact" in data["mutations"]
```

**🟢 GREEN** (1.5 hours)
Implement complete file generation with metadata

**🔧 REFACTOR** (30 min)
Add pretty-printing, sorting, validation

**✅ QA** (20 min)
Verify JSON structure matches frontend expectations

**END OF DAY 3**: mutation-impacts.json generation complete

---

## Phase 4: TypeScript Type Generator (Day 4)

**Objective**: Generate `mutation-impacts.d.ts` TypeScript definitions

### TDD Cycle 1: Basic Type Definitions

**🔴 RED** (45 min)
```python
# tests/unit/generators/test_typescript_generator.py
def test_generate_typescript_types_for_mutation_impact():
    """Generate TypeScript interface for MutationImpact"""
    generator = TypeScriptGenerator()
    ts_code = generator.generate_mutation_impact_interface()

    assert "export interface MutationImpact {" in ts_code
    assert "description: string;" in ts_code
    assert "input: Record<string, { type: string; required: boolean }>;" in ts_code
    assert "impact: {" in ts_code
    assert "primary: EntityImpact;" in ts_code
    assert "sideEffects: EntityImpact[];" in ts_code
```

Run: `uv run pytest tests/unit/generators/test_typescript_generator.py::test_generate_typescript_types_for_mutation_impact -v`
Expected: **FAIL**

**🟢 GREEN** (2 hours)
1. Create `src/generators/typescript_generator.py`
2. Implement TypeScript interface generation
3. Map JSON schema to TypeScript types

```python
class TypeScriptGenerator:
    def generate_mutation_impact_interface(self) -> str:
        return """
export interface MutationImpact {
  description: string;
  input: Record<string, { type: string; required: boolean }>;
  impact: {
    primary: EntityImpact;
    sideEffects: EntityImpact[];
    cacheInvalidations: CacheInvalidation[];
    permissions: string[];
    optimisticUpdateSafe: boolean;
    idempotent: boolean;
    estimatedDuration: number;
  };
  examples: MutationExample[];
  errors: MutationError[];
}
"""
```

**🔧 REFACTOR** (45 min)
- Use templates for type generation
- Add JSDoc comments
- Validate TypeScript syntax

**✅ QA** (20 min)
Verify types compile in TypeScript

---

### TDD Cycle 2: Complete .d.ts File Generation

**🔴 RED** (30 min)
```python
def test_generate_complete_typescript_definitions():
    """Generate complete mutation-impacts.d.ts file"""
    entities = [Entity(...), Entity(...)]

    generator = TypeScriptGenerator()
    ts_code = generator.generate_complete_definitions(entities)

    assert "export const MUTATION_IMPACTS: {" in ts_code
    assert "qualifyLead: MutationImpact;" in ts_code
    assert "createContact: MutationImpact;" in ts_code
    assert "export interface EntityImpact" in ts_code
    assert "export interface CacheInvalidation" in ts_code
```

**🟢 GREEN** (2 hours)
Generate complete TypeScript module

**🔧 REFACTOR** (30 min)
Format code, add type guards

**✅ QA** (20 min)
Compile with TypeScript compiler

**END OF DAY 4**: TypeScript types complete

---

## Phase 5: Integration with Schema Orchestrator (Day 5)

**Objective**: Integrate Team D generators into main pipeline

### TDD Cycle 1: Add FraiseQL Step to Orchestrator

**🔴 RED** (30 min)
```python
# tests/unit/generators/test_schema_orchestrator.py (add to existing)
def test_orchestrator_includes_fraiseql_metadata():
    """Orchestrator should include FraiseQL metadata in output"""
    entity = Entity(name="Contact", ...)

    orchestrator = SchemaOrchestrator()
    complete_sql = orchestrator.generate_complete_schema(entity)

    # Should include mutation metadata schema
    assert "CREATE SCHEMA mutation_metadata" in complete_sql
    assert "CREATE TYPE mutation_metadata.entity_impact" in complete_sql

    # Should include mutation annotations
    assert "@fraiseql:mutation" in complete_sql
```

Run: `uv run pytest tests/unit/generators/test_schema_orchestrator.py::test_orchestrator_includes_fraiseql_metadata -v`
Expected: **FAIL**

**🟢 GREEN** (1.5 hours)
1. Update `SchemaOrchestrator.generate_complete_schema()` to include:
   - Mutation metadata schema (one-time)
   - FraiseQL annotations for each action
2. Ensure proper ordering (schema before functions)

**🔧 REFACTOR** (45 min)
- Clean up orchestration logic
- Add flags for what to include
- Document generation phases

**✅ QA** (30 min)
Run all orchestrator tests

---

### TDD Cycle 2: Frontend Artifacts Generation

**🔴 RED** (30 min)
```python
def test_generate_frontend_artifacts():
    """Generate mutation-impacts.json and .d.ts files"""
    entities = [Entity(...), Entity(...)]

    orchestrator = SchemaOrchestrator()
    artifacts = orchestrator.generate_frontend_artifacts(
        entities,
        output_dir="generated/"
    )

    assert artifacts["mutation_impacts_json"] is not None
    assert artifacts["typescript_definitions"] is not None
    assert len(artifacts["mutation_impacts_json"]) > 1000  # Substantial content
```

**🟢 GREEN** (1.5 hours)
Implement frontend artifact generation

**🔧 REFACTOR** (30 min)
File writing, error handling

**✅ QA** (30 min)
Integration test that writes actual files

---

### TDD Cycle 3: End-to-End FraiseQL Test

**🔴 RED** (45 min)
```python
# tests/integration/test_fraiseql_integration.py
def test_complete_fraiseql_pipeline():
    """Test complete SpecQL → SQL + FraiseQL metadata pipeline"""
    yaml_content = """
    entity: Contact
    schema: crm
    fields:
      email: email!
      status: enum(lead, qualified)
    actions:
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
    complete_sql = orchestrator.generate_complete_schema(entity)
    frontend_artifacts = orchestrator.generate_frontend_artifacts([entity])

    # Verify SQL has FraiseQL metadata
    assert "@fraiseql:mutation name=qualifyLead" in complete_sql
    assert "mutation_metadata.entity_impact" in complete_sql

    # Verify JSON artifact
    impacts = json.loads(frontend_artifacts["mutation_impacts_json"])
    assert "qualifyLead" in impacts["mutations"]
    assert impacts["mutations"]["qualifyLead"]["impact"]["primary"]["entity"] == "Contact"

    # Verify TypeScript artifact
    assert "export interface MutationImpact" in frontend_artifacts["typescript_definitions"]
```

Run: `uv run pytest tests/integration/test_fraiseql_integration.py::test_complete_fraiseql_pipeline -v`
Expected: **FAIL**

**🟢 GREEN** (2 hours)
Wire everything together, fix integration issues

**🔧 REFACTOR** (1 hour)
Clean up interfaces, add logging

**✅ QA** (30 min)
- Run full test suite
- Verify 310+ tests passing
- Check generated artifacts manually

**END OF WEEK 1**: Team D core FraiseQL generation complete

---

# WEEK 2: Team D - Frontend Codegen (Days 6-10)

## Phase 6: Mutation Hook Generator (Days 6-7)

**Objective**: Generate pre-configured React hooks with cache management

### TDD Cycle 1: Basic Hook Structure

**🔴 RED** (1 hour)
```python
# tests/unit/generators/test_mutation_hook_generator.py
def test_generate_basic_mutation_hook():
    """Generate React hook for a mutation"""
    entity = Entity(...)
    action = Action(name="qualify_lead", ...)

    generator = MutationHookGenerator()
    ts_code = generator.generate_hook(entity, action)

    assert "export function useQualifyLead" in ts_code
    assert "useMutation" in ts_code
    assert "QUALIFY_LEAD" in ts_code  # GraphQL query constant
    assert "MutationHookOptions" in ts_code
```

Run test, expected: **FAIL**

**🟢 GREEN** (3 hours)
1. Create `src/generators/mutation_hook_generator.py`
2. Implement basic hook generation
3. Use templates for TypeScript code

**🔧 REFACTOR** (1 hour)
Clean up template, add JSDoc

**✅ QA** (30 min)
Verify TypeScript compiles

---

### TDD Cycle 2: Cache Invalidation in Hooks

**🔴 RED** (45 min)
```python
def test_hook_includes_cache_invalidations():
    """Hook should auto-configure refetchQueries from impact"""
    action = Action(
        name="qualify_lead",
        impact=ImpactDeclaration(
            cache_invalidations=[
                CacheInvalidation(query="contacts", strategy="REFETCH"),
                CacheInvalidation(query="dashboardStats", strategy="EVICT")
            ]
        )
    )

    generator = MutationHookGenerator()
    ts_code = generator.generate_hook(entity, action)

    assert "refetchQueries: [" in ts_code
    assert "'contacts'" in ts_code
    assert "cache.evict({ fieldName: 'dashboardStats' })" in ts_code
```

**🟢 GREEN** (2 hours)
Implement cache management code generation

**🔧 REFACTOR** (45 min)
Optimize generated code

**✅ QA** (30 min)
Test suite

---

### TDD Cycle 3: Optimistic Updates

**🔴 RED** (45 min)
```python
def test_hook_includes_optimistic_response_if_safe():
    """Generate optimistic response for safe mutations"""
    action = Action(
        name="update_contact",
        impact=ImpactDeclaration(optimistic_safe=True)
    )

    generator = MutationHookGenerator()
    ts_code = generator.generate_hook(entity, action)

    assert "optimisticResponse" in ts_code
```

**🟢 GREEN** (2 hours)
Generate optimistic response code

**🔧 REFACTOR** (30 min)
Clean up

**✅ QA** (30 min)
Full test suite

**END OF DAY 7**: Mutation hooks complete

---

## Phase 7: Complete Frontend Module (Days 8-9)

### TDD Cycle 1: GraphQL Query Constants

**🔴 RED** (30 min)
```python
def test_generate_graphql_query_constants():
    """Generate GraphQL query definitions"""
    entity = Entity(...)
    action = Action(name="qualify_lead", ...)

    generator = GraphQLQueryGenerator()
    ts_code = generator.generate_query_constant(entity, action)

    assert "export const QUALIFY_LEAD = gql`" in ts_code
    assert "mutation QualifyLead" in ts_code
    assert "$contactId: UUID!" in ts_code
```

**🟢 GREEN** (2 hours)
Generate GraphQL query constants

**🔧 REFACTOR** (30 min)
Template optimization

**✅ QA** (20 min)
Test suite

---

### TDD Cycle 2: Complete mutations.ts Module

**🔴 RED** (1 hour)
```python
def test_generate_complete_mutations_module():
    """Generate complete frontend mutations module"""
    entities = [Entity(...), Entity(...)]

    generator = FrontendModuleGenerator()
    ts_code = generator.generate_mutations_module(entities)

    # Should include imports
    assert "import { useMutation }" in ts_code
    assert "import { gql }" in ts_code

    # Should include all hooks
    assert "export function useQualifyLead" in ts_code
    assert "export function useCreateContact" in ts_code

    # Should re-export impacts
    assert "export { MUTATION_IMPACTS }" in ts_code
```

**🟢 GREEN** (3 hours)
Generate complete module with all pieces

**🔧 REFACTOR** (1 hour)
Code organization, formatting

**✅ QA** (30 min)
Compile with TypeScript

**END OF DAY 9**: Complete frontend module generation

---

## Phase 8: Integration & Testing (Day 10)

### TDD Cycle 1: CLI Integration for Frontend Generation

**🔴 RED** (30 min)
```python
# tests/integration/test_cli_frontend_generation.py
def test_cli_generates_frontend_artifacts():
    """CLI should generate frontend files"""
    # Mock CLI call
    result = cli_generate(
        entities=["entities/contact.yaml"],
        output_frontend="frontend/src/generated"
    )

    assert result.success
    assert Path("frontend/src/generated/mutations.ts").exists()
    assert Path("frontend/src/generated/mutation-impacts.json").exists()
    assert Path("frontend/src/generated/mutation-impacts.d.ts").exists()
```

**🟢 GREEN** (2 hours)
Wire frontend generation into CLI

**🔧 REFACTOR** (30 min)
Error handling, progress reporting

**✅ QA** (30 min)
Manual testing of CLI

---

### TDD Cycle 2: End-to-End with Real Frontend

**🔴 RED** (1 hour)
Create a real React component that uses generated hooks

```typescript
// tests/integration/frontend-test/src/TestComponent.tsx
import { useQualifyLead } from './generated/mutations';

export function TestComponent() {
  const [qualifyLead, { loading, error }] = useQualifyLead();

  return (
    <button onClick={() => qualifyLead({ variables: { contactId: '...' }})}>
      Qualify Lead
    </button>
  );
}
```

Try to compile, expected: **FAIL** (not generated yet)

**🟢 GREEN** (2 hours)
1. Generate complete frontend code
2. Set up minimal React test app
3. Verify compilation and type checking

**🔧 REFACTOR** (1 hour)
Fix type errors, improve generated code quality

**✅ QA** (1 hour)
- Full test suite: `uv run pytest`
- TypeScript compilation: `cd tests/integration/frontend-test && npm run typecheck`
- All ~320 tests passing

**END OF WEEK 2**: Complete FraiseQL + Frontend generation done

---

# WEEK 3: Custom Actions + CLI (Days 11-15)

## Phase 9: Custom Actions (Team C) (Days 11-13)

**Objective**: Support custom business actions beyond CRUD

### TDD Cycle 1: Custom Action Detection

**🔴 RED** (30 min)
```python
# tests/unit/generators/test_core_logic_generator.py (add)
def test_detect_custom_action_pattern():
    """Detect custom actions vs CRUD"""
    action_create = Action(name="create_contact", ...)
    action_custom = Action(name="qualify_lead", ...)

    generator = CoreLogicGenerator()

    assert generator.detect_action_pattern(action_create) == "create"
    assert generator.detect_action_pattern(action_custom) == "custom"
```

**🟢 GREEN** (45 min)
Implement action pattern detection

**🔧 REFACTOR** (15 min)
Clean up logic

**✅ QA** (10 min)
Test suite

---

### TDD Cycle 2: Custom Action Template

**🔴 RED** (45 min)
```python
def test_generate_custom_action_qualify_lead():
    """Generate custom action function"""
    entity = Entity(name="Contact", ...)
    action = Action(
        name="qualify_lead",
        steps=[
            ActionStep(type="validate", expression="status = 'lead'"),
            ActionStep(type="update", entity="Contact", fields={"status": "qualified"}),
            ActionStep(type="notify", template="lead_qualified")
        ]
    )

    generator = CoreLogicGenerator()
    sql = generator.generate_core_custom_action(entity, action)

    assert "CREATE OR REPLACE FUNCTION crm.qualify_lead(" in sql
    assert "input_data app.type_qualify_lead_input" in sql
    # Should have compiled steps
    assert "IF NOT (status = 'lead')" in sql  # Validation
    assert "UPDATE crm.tb_contact SET status = 'qualified'" in sql  # Update
    assert "PERFORM app.emit_event" in sql  # Notify
```

**🟢 GREEN** (4 hours)
1. Create `templates/sql/core_custom_action.sql.j2`
2. Implement `generate_core_custom_action()` method
3. Use existing step compilers to compile action steps

**🔧 REFACTOR** (1 hour)
Template optimization, error handling

**✅ QA** (30 min)
Test suite

---

### TDD Cycle 3: Database Roundtrip for Custom Action

**🔴 RED** (1 hour)
```python
# tests/integration/actions/test_custom_actions_roundtrip.py
def test_custom_action_qualify_lead_executes_in_database(test_db):
    """Custom action executes successfully in PostgreSQL"""
    # Generate SQL for entity with custom action
    entity = create_contact_with_qualify_lead_action()
    orchestrator = SchemaOrchestrator()
    sql = orchestrator.generate_complete_schema(entity)

    # Apply to database
    test_db.execute(sql)
    test_db.commit()

    # Create a lead
    test_db.execute("""
        INSERT INTO crm.tb_contact (id, email, status, tenant_id)
        VALUES (gen_random_uuid(), 'test@example.com', 'lead', %s)
    """, (TEST_TENANT_ID,))

    # Call custom action
    cursor = test_db.cursor()
    cursor.execute("""
        SELECT (crm.qualify_lead(%s, ROW(...)::app.type_qualify_lead_input, %s, %s)).*
    """, (...))
    result = cursor.fetchone()

    # Verify success
    assert result[2] == "success"  # status

    # Verify database state
    cursor.execute("SELECT status FROM crm.tb_contact WHERE email = 'test@example.com'")
    assert cursor.fetchone()[0] == "qualified"
```

**🟢 GREEN** (3 hours)
Fix any issues found during actual execution

**🔧 REFACTOR** (1 hour)
Improve generated SQL quality

**✅ QA** (1 hour)
Full test suite, verify database tests pass

**END OF DAY 13**: Custom actions complete

---

## Phase 10: CLI Commands (Team E) (Days 14-15)

**Objective**: Polish CLI for production use

### TDD Cycle 1: Generate Command

**🔴 RED** (1 hour)
```python
# tests/unit/cli/test_generate_command.py
def test_cli_generate_command():
    """Test specql generate command"""
    result = run_cli(["generate", "entities/contact.yaml"])

    assert result.exit_code == 0
    assert "✓ Generated: migrations/001_contact.sql" in result.output
    assert Path("migrations/001_contact.sql").exists()
```

**🟢 GREEN** (2 hours)
Implement full generate command with:
- File reading
- Progress output
- Migration file writing
- Frontend artifacts (if --with-impacts)

**🔧 REFACTOR** (1 hour)
Add colors, better error messages

**✅ QA** (30 min)
Manual testing

---

### TDD Cycle 2: Validate Command

**🔴 RED** (45 min)
```python
def test_cli_validate_command():
    """Test specql validate command"""
    result = run_cli(["validate", "entities/contact.yaml"])

    assert result.exit_code == 0
    assert "✓ contact.yaml is valid" in result.output
```

**🟢 GREEN** (1.5 hours)
Implement validation with helpful error messages

**🔧 REFACTOR** (30 min)
Error formatting

**✅ QA** (20 min)
Test invalid YAML

---

### TDD Cycle 3: Docs Command

**🔴 RED** (30 min)
```python
def test_cli_docs_command():
    """Test specql docs command"""
    result = run_cli(["docs", "entities/contact.yaml", "--output=docs/"])

    assert result.exit_code == 0
    assert Path("docs/mutations.md").exists()
```

**🟢 GREEN** (2 hours)
Generate markdown documentation

**🔧 REFACTOR** (30 min)
Template formatting

**✅ QA** (30 min)
Review generated docs

**END OF DAY 15**: CLI complete

---

# WEEK 4: Integration & Ship (Days 16-20)

## Phase 11: End-to-End Testing (Days 16-17)

### TDD Cycle 1: Complete Pipeline Test

**🔴 RED** (2 hours)
```python
# tests/integration/test_complete_pipeline.py
def test_complete_specql_to_graphql_pipeline():
    """Test complete SpecQL → PostgreSQL → GraphQL pipeline"""

    # 1. Write SpecQL
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
          - notify: owner(email, "Contact qualified")
    """

    # 2. Generate SQL
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    orchestrator = SchemaOrchestrator()
    sql = orchestrator.generate_complete_schema(entity)
    frontend_artifacts = orchestrator.generate_frontend_artifacts([entity])

    # 3. Apply to database
    test_db.execute(sql)
    test_db.commit()

    # 4. Test CRUD operations
    test_db.execute("SELECT crm.create_contact(...)")
    test_db.execute("SELECT crm.qualify_lead(...)")

    # 5. Verify frontend artifacts
    assert "useCreateContact" in frontend_artifacts["mutations_module"]
    assert "useQualifyLead" in frontend_artifacts["mutations_module"]

    # 6. Verify FraiseQL can introspect
    # (Manual verification or mock FraiseQL tool)
    assert "@fraiseql:mutation" in sql
```

Run test, expected: **FAIL** (integration issues)

**🟢 GREEN** (4 hours)
Fix all integration issues found

**🔧 REFACTOR** (2 hours)
Clean up rough edges

**✅ QA** (2 hours)
Run complete test suite multiple times

---

### TDD Cycle 2: Performance Testing

**🔴 RED** (1 hour)
```python
def test_generation_performance():
    """Verify generation is fast enough for production use"""
    entities = [create_entity(i) for i in range(10)]  # 10 entities

    import time
    start = time.time()

    for entity in entities:
        orchestrator.generate_complete_schema(entity)

    elapsed = time.time() - start

    # Should generate 10 entities in under 5 seconds
    assert elapsed < 5.0
```

**🟢 GREEN** (2 hours)
Optimize slow parts if needed

**✅ QA** (1 hour)
Profile and optimize

**END OF DAY 17**: All tests passing, system working end-to-end

---

## Phase 12: Documentation (Day 18)

### Task 1: User Documentation

**Time: 4 hours**

Write comprehensive docs:

1. **Getting Started Guide** (`docs/guides/getting-started.md`)
   - Installation
   - First entity
   - Running migrations
   - Using generated GraphQL

2. **SpecQL Language Reference** (`docs/reference/specql-syntax.md`)
   - Field types
   - Action syntax
   - Examples

3. **CLI Reference** (`docs/reference/cli-commands.md`)
   - All commands
   - Options
   - Examples

4. **Architecture Guide** (`docs/architecture/overview.md`)
   - Pipeline explanation
   - Team structure
   - Extension points

### Task 2: API Documentation

**Time: 2 hours**

Generate API docs:
- Generator classes
- Method signatures
- Usage examples

### Task 3: Examples

**Time: 2 hours**

Create working examples:
- Simple CRM (Contact, Company)
- E-commerce (Product, Order)
- Multi-tenant SaaS

**END OF DAY 18**: Documentation complete

---

## Phase 13: Polish & Release (Days 19-20)

### Day 19: Final Polish

**Morning** (4 hours)
- Fix any remaining TODO comments
- Improve error messages
- Add helpful CLI output
- Code review of all new code

**Afternoon** (4 hours)
- Run full test suite 10x
- Fix any flaky tests
- Performance profiling
- Memory leak checking

---

### Day 20: Release Preparation

**Morning** (4 hours)
1. Version bump to 1.0.0
2. Update CHANGELOG.md
3. Final test run
4. Tag release
5. Write release notes

**Afternoon** (4 hours)
1. Create demo video (recording)
2. Write blog post announcement
3. Prepare demo for stakeholders
4. Deploy documentation site

---

## 🎯 Success Criteria Checklist

### Functionality
- [ ] SpecQL → PostgreSQL works (already ✅)
- [ ] PostgreSQL → FraiseQL metadata works
- [ ] Frontend code generation works
- [ ] All 320+ tests passing
- [ ] Database roundtrip tests pass
- [ ] Custom actions work
- [ ] CLI commands work

### Quality
- [ ] No critical bugs
- [ ] Performance acceptable (<5s for 10 entities)
- [ ] Error messages helpful
- [ ] Documentation complete
- [ ] Code coverage >90%

### Deliverables
- [ ] `mutation-impacts.json` generation ✅
- [ ] `mutation-impacts.d.ts` generation ✅
- [ ] `mutations.ts` hooks generation ✅
- [ ] GraphQL query constants ✅
- [ ] Complete CLI (`specql generate/validate/docs`) ✅
- [ ] User documentation ✅
- [ ] Working examples ✅

---

## 📊 Daily Progress Tracking

Update after each day:

```markdown
### Day 1 (YYYY-MM-DD)
- ✅ Phase 1, Cycle 1-3 complete
- Tests: 308/312 passing
- Blockers: None
- Tomorrow: Phase 2

### Day 2 (YYYY-MM-DD)
- ✅ Phase 2 complete
- Tests: 315/320 passing
- Blockers: None
- Tomorrow: Phase 3

... (continue for all 20 days)
```

---

## 🚨 Risk Mitigation

### If Behind Schedule

**Week 1 behind?**
- Skip frontend hook generation
- Focus on JSON/TypeScript generation only
- Defer hooks to later

**Week 2 behind?**
- Simplify hook generation
- Basic functionality only
- Skip optimistic updates

**Week 3 behind?**
- Skip custom actions
- Focus on CLI polish
- Custom actions can be v1.1

### If Blocked

**Technical issues?**
1. Document the blocker
2. Create failing test
3. Ask for help / research
4. Consider workaround

**Integration issues?**
1. Write integration test that fails
2. Debug one piece at a time
3. Add logging/tracing
4. Simplify if needed

---

## 🎓 TDD Best Practices for This Plan

### RED Phase Tips
- Write the test you wish existed
- Make it specific and focused
- Run it and watch it fail
- Commit the failing test

### GREEN Phase Tips
- Simplest possible implementation
- Don't worry about elegance
- Just make the test pass
- Commit when green

### REFACTOR Phase Tips
- Now make it beautiful
- Extract methods
- Add comments
- Keep tests passing
- Commit after refactor

### QA Phase Tips
- Run full test suite
- Check code quality
- Manual testing
- Integration verification
- Document any issues

---

## 📞 Questions to Ask Yourself Daily

1. **Progress**: Am I on track for today's phase?
2. **Quality**: Are all tests passing?
3. **Blockers**: What's slowing me down?
4. **Tomorrow**: What's the next TDD cycle?
5. **Help**: Do I need to escalate anything?

---

**Last Updated**: 2025-11-08
**Status**: Ready to Execute
**Estimated Completion**: 3-4 weeks (15-20 days)
**Next Action**: Start Day 1, Phase 1, TDD Cycle 1
