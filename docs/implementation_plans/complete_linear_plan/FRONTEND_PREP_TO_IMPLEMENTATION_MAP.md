# Frontend Preparation Work → Implementation Plan Mapping

**Date**: 2025-11-13
**Purpose**: Map the preparation work in `../specql_front/` to the linear implementation plan

---

## 📋 Overview

The `specql_front` repository contains **conceptual preparation and architectural thinking** that has been translated into a **concrete 12-week implementation plan** (Weeks 39-50).

```
../specql_front/           →    Weeks 39-50
(Preparation)                   (Implementation)

Conceptual Design          →    Concrete Deliverables
Architecture Thinking      →    Phased TDD Execution
Framework Analysis         →    Working Code Generators
```

---

## 🗺️ Document Mapping

### 1. PRD.md → Week 39-44 (Grammar & Specification)

**Preparation Work** (`../specql_front/PRD.md`):
- Core concepts (Entity, Field, Page, Action, Layout)
- Data model (TypeScript-like types)
- Frontend block structure
- Postgres comments format

**Implementation** (Weeks 39-44):
- **Week 39-40**: Implement core component grammar
  - Basic components (text_input, select, checkbox, etc.)
  - Form components with validation
  - List/table components
  - Layout components

- **Week 41-42**: Implement complex patterns
  - Card layouts & grids
  - Nested tables & tree views
  - Timeline & activity feeds
  - Dashboard & metrics
  - Navigation patterns
  - Modal & dialog patterns

- **Week 43-44**: Build pattern library
  - Pattern definition system
  - Pattern storage & indexing
  - AI-powered recommendations
  - Pattern generation from examples

**Key Deliverables**:
```python
# Pattern registry
class PatternRegistry:
    def register_pattern(self, pattern: Pattern)
    def search(self, query: str) -> List[Pattern]
    def search_by_tags(self, tags: List[str]) -> List[Pattern]

# Pattern recommender
class PatternRecommender:
    def recommend(self, context: str, entity: Entity = None) -> List[Pattern]
    def recommend_from_screenshot(self, image: Image) -> List[Pattern]
```

---

### 2. formal_schema.md → Core Type System (Week 39)

**Preparation Work** (`../specql_front/formal_schema.md`):
- Formal schema definitions
- Type specifications
- Component contracts

**Implementation** (Week 39 Day 1):
```yaml
# Component type system
components:
  - type: text_input
    props:
      label: string
      placeholder: string
      value: string
      validation: ValidationRule[]

  - type: select
    props:
      label: string
      options: Option[]
      value: string | string[]
      multiple: boolean
```

**Key Files**:
- `src/generators/frontend/grammar/component_parser.py`
- `src/generators/frontend/grammar/type_system.py`
- `src/generators/frontend/grammar/validation.py`

---

### 3. frontend_architect_prompt.md → Week 39-40 Implementation

**Preparation Work** (`../specql_front/frontend_architect_prompt.md`):
- YAML structure design
- Component hierarchy
- Rich type support
- Domain-first naming

**Implementation** (Week 39-40):
```yaml
# Entity-level metadata
entities:
  User:
    label: "Users"
    icon: "user"
    defaultListRoute: "/users"

# Field-level metadata
fields:
  User:
    email:
      label: "Email Address"
      widget: "email"
      validation:
        - type: "pattern"
          value: "^[\\w-\\.]+@([\\w-]+\\.)+[\\w-]{2,4}$"
          message: "Please enter a valid email"

# Page definitions
pages:
  - name: UserList
    type: list
    entity: User
    listConfig:
      columns: ["email", "name", "role"]
```

**Key Outputs**:
- Complete YAML grammar for frontend
- Field visibility (list, form, detail)
- Actions and navigation
- Layout configuration

---

### 4. cross_framework_adapter_prompt.md → Weeks 48-50 (Code Generation)

**Preparation Work** (`../specql_front/cross_framework_adapter_prompt.md`):
- Framework-agnostic design principles
- Meta fields for framework-specific config
- Core vs optional separation

**Implementation** (Weeks 48-50):

**Week 48**: React/Next.js Generation
```python
class ReactGenerator:
    def generate_page(self, page: Page) -> str:
        """Generate React component from SpecQL page"""
        if page.type == "list":
            return self._generate_list_page(page)
        elif page.type == "form":
            return self._generate_form_page(page)

class NextJsGenerator:
    def generate_project(self, frontend: FrontendSpec, output_dir: Path):
        """Generate complete Next.js project"""
        self._generate_app_router(frontend.pages, output_dir / "app")
        self._generate_layouts(frontend.layouts, output_dir / "app")
```

**Week 49**: Vue/Nuxt Generation
```python
class VueGenerator:
    def generate_page(self, page: Page) -> str:
        """Generate Vue SFC from SpecQL page"""
        template = self._generate_template(page)
        script = self._generate_script(page)
        style = self._generate_style(page)

class NuxtGenerator:
    def generate_project(self, frontend: FrontendSpec, output_dir: Path):
        """Generate Nuxt 3 project"""
```

**Week 50**: UI Library Adapters
```python
class UILibraryAdapter:
    def __init__(self, library: str):
        self.library = library  # "shadcn", "mui", "chakra", etc.

    def map_component(self, specql_component: Component) -> str:
        """Map SpecQL component to library component"""
```

**Framework Support**:
- React/Next.js (shadcn, MUI, Chakra UI, Ant Design)
- Vue/Nuxt (Vuetify, PrimeVue, Element Plus)
- Angular (Material, PrimeNG)
- Svelte (SvelteUI, Carbon)

---

### 5. validator.md → Validation System (Week 39 Day 2)

**Preparation Work** (`../specql_front/validator.md`):
- Validation rule specifications
- Error handling patterns
- Client-side validation logic

**Implementation** (Week 39 Day 2):
```yaml
# Validation rules
ValidationRule:
  type: "required" | "pattern" | "minLength" | "maxLength" | "min" | "max" | "custom"
  value: any
  message: string

# Example
fields:
  email:
    validation:
      - type: "required"
        message: "Email is required"
      - type: "pattern"
        value: "^[\\w-\\.]+@([\\w-]+\\.)+[\\w-]{2,4}$"
        message: "Please enter a valid email"
  password:
    validation:
      - type: "minLength"
        value: 8
        message: "Password must be at least 8 characters"
```

**Key Files**:
- `src/generators/frontend/grammar/validation_parser.py`
- `templates/react/validation.ts.j2`
- `templates/vue/validation.ts.j2`

---

### 6. example_generator.md → Pattern Generation (Week 43 Day 4)

**Preparation Work** (`../specql_front/example_generator.md`):
- Generate examples from patterns
- Code generation strategies
- Template-based approach

**Implementation** (Week 43 Day 4):
```python
class PatternGenerator:
    def generate_from_code(self, code: str, framework: str) -> Pattern:
        """
        Generate SpecQL pattern from example code

        Input: React/Vue/Angular component code
        Output: SpecQL pattern definition
        """
        ast = self._parse_framework_code(code, framework)
        components = self._extract_components(ast)
        layout = self._infer_layout(components)

        return Pattern(
            id=self._generate_id(components),
            components=components,
            layout=layout
        )

    def generate_from_description(self, description: str) -> Pattern:
        """Generate pattern from natural language description"""
        prompt = f"Generate SpecQL frontend pattern for: {description}"
        pattern_yaml = self.llm.complete(prompt)
        return self._parse_pattern_yaml(pattern_yaml)
```

---

### 7. docs/ → Integration Guides

**Preparation Work** (`../specql_front/docs/`):
- `fraiseql-integration.md` - Backend integration
- `server-integration-guide.md` - Server-side rendering

**Implementation** (Week 50):
- Integration documentation
- Backend ↔ Frontend connection
- GraphQL cascade handling
- SSR patterns

**Key Integration Points**:
```typescript
// Auto-generated GraphQL queries
const { data, loading } = useQuery(LIST_USERS);

// Auto-generated mutations with cascade
const [createUser] = useMutation(CREATE_USER, {
  onSuccess: (result) => {
    // Apply cascade to cache
    applyCascade(result.cascade);
  }
});
```

---

## 🎯 Key Innovations in Implementation

### 1. **AI-Powered Pattern Library** (Week 43-44)

**Beyond Preparation**:
The preparation work outlined the concept, but the implementation adds:

- **Semantic Search**: Vector embeddings for natural language pattern search
- **AI Recommendations**: LLM-powered pattern suggestions based on context
- **Screenshot Analysis**: Claude Vision to recommend patterns from UI screenshots
- **Pattern Generation**: Auto-generate patterns from example code

```python
# AI-powered features
recommender.recommend("I need a user management dashboard")
# → Returns: [Pattern(id="user_directory"), Pattern(id="stats_dashboard")]

recommender.recommend_from_screenshot(screenshot)
# → Analyzes UI and recommends matching patterns
```

### 2. **Reverse Engineering** (Week 45-47)

**Beyond Preparation**:
The preparation focused on forward generation. Implementation adds bidirectional translation:

- **React → SpecQL**: Extract grammar from existing React apps
- **Vue → SpecQL**: Extract grammar from existing Vue apps
- **Auto-detection**: Automatically detect framework and parse appropriately

```bash
specql reverse frontend . --auto-detect
# Scans codebase, detects React/Vue/Angular, extracts SpecQL
```

### 3. **Multi-Framework Output** (Week 48-50)

**Beyond Preparation**:
The preparation outlined framework-agnostic design. Implementation delivers:

- **5+ frameworks**: React, Vue, Angular, Svelte, + Web Components
- **10+ UI libraries**: shadcn, MUI, Chakra, Ant Design, Vuetify, etc.
- **Type-safe generation**: Full TypeScript support
- **Production-ready**: Includes routing, state management, error handling

```bash
specql generate react entities/*.yaml --ui-library shadcn
specql generate vue entities/*.yaml --ui-library vuetify
specql generate angular entities/*.yaml --ui-library material
```

### 4. **Complete Stack Integration**

**Beyond Preparation**:
Integration with the full SpecQL ecosystem:

```yaml
# Single YAML defines entire app
entity: User
fields:
  email: text!
  name: text!

# Backend auto-generated (Weeks 1-38)
# - PostgreSQL schema ✅
# - PL/pgSQL functions ✅
# - GraphQL types ✅

# Frontend auto-generated (Weeks 39-50)
# - List page with table
# - Create/edit forms
# - Detail view
# - Navigation
# - GraphQL queries/mutations
```

---

## 📊 Preparation → Implementation Metrics

| Concept (Preparation) | Implementation (Weeks) | Lines of Code | Tests |
|-----------------------|------------------------|---------------|-------|
| Core grammar design | Week 39-40 | ~3,000 | 50+ |
| Complex patterns | Week 41-42 | ~2,500 | 40+ |
| Pattern library | Week 43-44 | ~2,000 | 30+ |
| React reverse eng | Week 45 | ~1,500 | 25+ |
| Vue reverse eng | Week 46 | ~1,500 | 25+ |
| Other frameworks | Week 47 | ~1,000 | 20+ |
| React generation | Week 48 | ~2,500 | 35+ |
| Vue generation | Week 49 | ~2,000 | 30+ |
| Testing & polish | Week 50 | ~1,000 | 50+ |
| **Total** | **12 weeks** | **~17,000** | **305+** |

---

## 🚀 Development Flow

### Preparation Phase (Completed)
1. ✅ Conceptual design (`PRD.md`)
2. ✅ Formal schema (`formal_schema.md`)
3. ✅ Architecture patterns (`frontend_architect_prompt.md`)
4. ✅ Framework considerations (`cross_framework_adapter_prompt.md`)

### Implementation Phase (Weeks 39-50)

**Week 39-40**: Transform concepts → Working grammar parser
```python
# Input: YAML spec
frontend:
  pages:
    - name: UserList
      type: list

# Output: Validated AST
page = FrontendParser().parse(yaml)
assert page.type == PageType.LIST
assert page.entity == "User"
```

**Week 41-42**: Complex patterns → Reusable components
```python
# 50+ patterns in library
pattern = registry.get("user_directory")
assert pattern.category == "list"
assert len(pattern.components) > 0
```

**Week 43-44**: Static library → AI-powered recommendations
```python
# Semantic search
patterns = recommender.recommend("dashboard with charts")
assert any("dashboard" in p.tags for p in patterns)

# Screenshot analysis
patterns = recommender.recommend_from_screenshot(image)
```

**Week 45-47**: One-way generation → Bidirectional translation
```bash
# Extract from existing app
specql reverse react src/ > extracted.specql.yaml

# Modify
vim extracted.specql.yaml

# Regenerate
specql generate vue extracted.specql.yaml --output src/
```

**Week 48-50**: Single framework → Multi-framework support
```bash
# Generate for all frameworks
specql generate react entities/*.yaml --output frontend/react/
specql generate vue entities/*.yaml --output frontend/vue/
specql generate angular entities/*.yaml --output frontend/angular/
```

---

## 🎯 Success Criteria

### From Preparation
- [x] Framework-agnostic grammar ✅ Week 39-40
- [x] Rich type support ✅ Week 39-40
- [x] Domain-first naming ✅ Week 39-40
- [x] Validation rules ✅ Week 39
- [x] Layout system ✅ Week 39-40

### Added in Implementation
- [ ] AI-powered pattern search (Week 43)
- [ ] Screenshot analysis (Week 43)
- [ ] Bidirectional translation (Week 45-47)
- [ ] 5+ framework support (Week 48-50)
- [ ] 10+ UI library adapters (Week 48-50)
- [ ] Production-ready code quality (Week 50)

---

## 📚 Key Files

### Preparation (../specql_front/)
- `PRD.md` - Product requirements
- `formal_schema.md` - Type system
- `frontend_architect_prompt.md` - Architecture
- `cross_framework_adapter_prompt.md` - Framework agnostic design
- `validator.md` - Validation system

### Implementation (Weeks 39-50)
- `src/generators/frontend/grammar/` - Grammar parser
- `src/generators/frontend/patterns/` - Pattern library
- `src/reverse_engineering/react/` - React reverse engineering
- `src/reverse_engineering/vue/` - Vue reverse engineering
- `src/generators/frontend/react/` - React code generation
- `src/generators/frontend/vue/` - Vue code generation
- `registry/frontend_patterns.yaml` - Pattern definitions
- `templates/react/` - React templates
- `templates/vue/` - Vue templates

---

## 🔗 Related Documents

- [Complete Timeline Overview](./COMPLETE_TIMELINE_OVERVIEW.md)
- [Week 39-50 Implementation Plan](./WEEK_39_50_FRONTEND_UNIVERSAL_LANGUAGE.md)
- [Architecture Documentation](../../architecture/)

---

**Status**: Preparation work successfully translated into concrete 12-week implementation plan with clear deliverables, tests, and success criteria.
