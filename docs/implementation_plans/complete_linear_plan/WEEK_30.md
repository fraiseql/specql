# Week 30: Multi-Framework Testing & Integration

**Date**: TBD (After Week 29 complete)
**Duration**: 5-6 days
**Status**: 📅 Planned
**Objective**: Comprehensive testing across React, Vue, and Angular with real-world applications

**Prerequisites**: Week 29 complete (Angular generation working)

**Output**:
- Cross-framework test suite
- Reference implementations for each framework
- Performance benchmarks
- Migration guides between frameworks
- Production readiness validation

---

## 🎯 Executive Summary

This week validates the **universal component grammar** across all three major frameworks - proving that a single YAML specification can generate production-ready code for React, Vue, and Angular.

**Key Deliverables**:
1. **Reference Apps**: Complete CRM app in all 3 frameworks
2. **Round-Trip Tests**: Parse → Generate → Compare for each framework
3. **Migration Tests**: React → UniversalFrontend → Vue
4. **Performance Benchmarks**: Generation speed, output quality
5. **Production Validation**: Real-world complexity testing

**Success Metric**: 1 YAML spec → 3 working apps (React/Vue/Angular) with 95%+ feature parity

---

## 📅 Daily Breakdown

### Day 1: Reference Application Design

**Morning Block (4 hours): Design Reference CRM App**

**Goal**: Design a comprehensive YAML spec that exercises all UniversalFrontend features

**File**: `tests/fixtures/reference_app/crm_frontend.yaml`

```yaml
frontend:
  version: "1.0"

  # Entity metadata
  entities:
    Contact:
      label: "Contacts"
      label_singular: "Contact"
      icon: "users"
      default_list_route: "/contacts"
      default_detail_route: "/contacts/:id"
      auto_generate_pages: true

    Company:
      label: "Companies"
      label_singular: "Company"
      icon: "building"
      default_list_route: "/companies"
      default_detail_route: "/companies/:id"
      auto_generate_pages: true

  # Field metadata
  fields:
    Contact:
      email:
        label: "Email Address"
        widget: email
        required: true
        placeholder: "contact@example.com"
        list:
          visible: true
          order: 1
          width: medium
        form:
          visible: true
          order: 1
          section: "Basic Information"
        detail:
          visible: true
          order: 1

      name:
        label: "Full Name"
        widget: text
        required: true
        list:
          visible: true
          order: 0
        form:
          visible: true
          order: 0
          section: "Basic Information"

      company:
        label: "Company"
        widget: select
        options:
          type: relation
          entity: Company
          label_field: name
        list:
          visible: true
          order: 2
        form:
          visible: true
          order: 2
          section: "Company Information"

      status:
        label: "Status"
        widget: select
        required: true
        options:
          type: enum
          values: ["lead", "qualified", "customer", "inactive"]
        list:
          visible: true
          order: 3
        form:
          visible: true
          order: 3

    Company:
      name:
        label: "Company Name"
        widget: text
        required: true
        list:
          visible: true
          order: 0
        form:
          visible: true
          order: 0

      industry:
        label: "Industry"
        widget: select
        options:
          type: enum
          values: ["technology", "finance", "healthcare", "retail"]
        list:
          visible: true
          order: 1

  # Pages
  pages:
    - name: contact-list
      type: list
      route: /contacts
      entity: Contact
      title: "All Contacts"
      icon: users
      list_config:
        columns: [name, email, company, status]
        default_sort:
          field: name
          direction: asc
        page_size: 20
        filters:
          - field: status
            type: enum
          - field: company
            type: relation
        row_actions: [view_contact, edit_contact, delete_contact]
        primary_actions: [create_contact]

    - name: contact-form
      type: form
      route: /contacts/new
      entity: Contact
      mode: create
      title: "Create Contact"
      fields: [name, email, company, status]
      submit_action: create_contact
      secondary_actions: [cancel]

    - name: contact-detail
      type: detail
      route: /contacts/:id
      entity: Contact
      title: "Contact Details"
      fields: [name, email, company, status, created_at, updated_at]
      actions: [edit_contact, delete_contact, qualify_lead]

  # Actions
  actions:
    - name: create_contact
      type: create
      entity: Contact
      label: "Create"
      icon: plus
      mutation: createContact
      on_success:
        toast: "Contact created successfully"
        redirect_to: /contacts/:id
        refetch_entities: [Contact]

    - name: edit_contact
      type: update
      entity: Contact
      label: "Edit"
      icon: edit
      mutation: updateContact
      on_success:
        toast: "Contact updated"
        refetch_entities: [Contact]

    - name: delete_contact
      type: delete
      entity: Contact
      label: "Delete"
      icon: trash
      mutation: deleteContact
      on_success:
        toast: "Contact deleted"
        redirect_to: /contacts
        refetch_entities: [Contact]

    - name: qualify_lead
      type: customMutation
      entity: Contact
      label: "Qualify Lead"
      icon: check
      mutation: qualifyLead
      on_success:
        toast: "Lead qualified"
        refetch_entities: [Contact]

  # Layouts
  layouts:
    - id: main
      label: "Main Layout"
      sidebar: true
      header: true
      title_prefix: "CRM - "

  # Navigation
  navigation:
    - id: nav-contacts
      label: "Contacts"
      page_name: contact-list
      icon: users
      section: "Sales"

    - id: nav-companies
      label: "Companies"
      page_name: company-list
      icon: building
      section: "Sales"
```

**Afternoon Block (4 hours): Generate All 3 Frameworks**

Implement test that generates React, Vue, and Angular from this single spec.

---

### Day 2: Round-Trip Testing

**Morning Block (4 hours): React Round-Trip**

**Test**: Parse existing React app → UniversalFrontend → Generate React → Compare

```python
# tests/integration/test_react_roundtrip.py
"""Round-trip test for React"""

import pytest
from pathlib import Path

from src.frontend.parsers.react_parser import ReactComponentExtractor
from src.frontend.generators.react_generator import ReactGenerator
from src.frontend.yaml_parser import FrontendYAMLParser


def test_react_roundtrip():
    """Parse React → YAML → Generate React → Compare"""

    # 1. Parse existing React app
    original_dir = Path('tests/fixtures/react_app')
    extractor = ReactComponentExtractor()

    # Parse all components
    components = []
    for file in original_dir.glob('**/*.tsx'):
        component = extractor.extract_component(file)
        if component:
            components.append(component)

    # 2. Convert to UniversalFrontend
    frontend = convert_to_universal_frontend(components)

    # 3. Generate new React app
    generator = ReactGenerator(output_dir=Path('output/react_generated'))
    generated_files = generator.generate(frontend)

    # 4. Write generated files
    for file in generated_files:
        file.path.parent.mkdir(parents=True, exist_ok=True)
        file.path.write_text(file.content)

    # 5. Compare structure
    assert_structure_matches(original_dir, Path('output/react_generated'))

    # 6. Compile check (tsc)
    result = subprocess.run(
        ['npx', 'tsc', '--noEmit'],
        cwd='output/react_generated',
        capture_output=True
    )
    assert result.returncode == 0, f"TypeScript compilation failed: {result.stderr}"
```

**Afternoon Block (4 hours): Vue & Angular Round-Trip**

Same tests for Vue and Angular.

---

### Day 3: Cross-Framework Migration

**Morning Block (4 hours): React → Vue Migration**

**Test**: Parse React app → Generate Vue app → Verify feature parity

```python
# tests/integration/test_cross_framework_migration.py
"""Test migration between frameworks"""

def test_react_to_vue_migration():
    """React app → UniversalFrontend → Vue app"""

    # 1. Parse React CRM
    react_app = Path('tests/fixtures/react_crm')
    frontend = parse_react_app(react_app)

    # 2. Generate Vue app
    vue_generator = VueGenerator(output_dir=Path('output/vue_crm'))
    vue_files = vue_generator.generate(frontend)

    # Write files
    for file in vue_files:
        file.path.parent.mkdir(parents=True, exist_ok=True)
        file.path.write_text(file.content)

    # 3. Verify feature parity
    assert has_list_page(vue_files, 'contact-list')
    assert has_form_page(vue_files, 'contact-form')
    assert has_detail_page(vue_files, 'contact-detail')

    # 4. Compile check
    result = subprocess.run(
        ['npm', 'run', 'build'],
        cwd='output/vue_crm',
        capture_output=True
    )
    assert result.returncode == 0


def test_vue_to_angular_migration():
    """Vue app → UniversalFrontend → Angular app"""
    # Similar test

def test_angular_to_react_migration():
    """Angular app → UniversalFrontend → React app"""
    # Similar test
```

**Afternoon Block (4 hours): Migration Documentation**

Document migration paths and gotchas for each framework pair.

---

### Day 4: Performance Benchmarks

**Morning Block (4 hours): Generation Performance**

Benchmark generation speed and output quality:

```python
# tests/performance/test_generation_benchmarks.py
"""Performance benchmarks for code generation"""

import time
import pytest


def test_generation_speed():
    """Benchmark generation speed for large apps"""

    # Large app: 50 entities, 200 fields, 150 pages
    frontend = generate_large_frontend_spec(
        num_entities=50,
        num_fields_per_entity=4,
        num_pages=150
    )

    # Benchmark React generation
    start = time.time()
    react_generator = ReactGenerator(output_dir=Path('output/bench_react'))
    react_files = react_generator.generate(frontend)
    react_time = time.time() - start

    # Benchmark Vue generation
    start = time.time()
    vue_generator = VueGenerator(output_dir=Path('output/bench_vue'))
    vue_files = vue_generator.generate(frontend)
    vue_time = time.time() - start

    # Benchmark Angular generation
    start = time.time()
    angular_generator = AngularGenerator(output_dir=Path('output/bench_angular'))
    angular_files = angular_generator.generate(frontend)
    angular_time = time.time() - start

    # Assertions
    assert react_time < 10.0, f"React generation too slow: {react_time}s"
    assert vue_time < 10.0, f"Vue generation too slow: {vue_time}s"
    assert angular_time < 10.0, f"Angular generation too slow: {angular_time}s"

    print(f"\nGeneration Times (50 entities, 150 pages):")
    print(f"  React:   {react_time:.2f}s ({len(react_files)} files)")
    print(f"  Vue:     {vue_time:.2f}s ({len(vue_files)} files)")
    print(f"  Angular: {angular_time:.2f}s ({len(angular_files)} files)")
```

**Afternoon Block (4 hours): Output Quality Metrics**

Measure code quality metrics:
- Lines of code generated
- TypeScript type coverage
- Bundle size
- Compilation time

---

### Day 5: Production Readiness Validation

**Morning Block (4 hours): Real-World Complexity**

Test with production-like scenarios:
- Large entity counts (100+ entities)
- Complex relationships
- Advanced validations
- Custom workflows
- Multi-step forms
- Nested layouts

**Afternoon Block (4 hours): Documentation & CLI Polish**

**CLI Commands Summary**:
```bash
# Test all frameworks with single YAML
specql test-frameworks frontend.yaml --output test-output/

# Migrate between frameworks
specql migrate-framework react-app/ --to vue --output vue-app/

# Benchmark generation
specql benchmark frontend.yaml --frameworks react,vue,angular
```

**Documentation**:
- Migration guides for each framework pair
- Performance tuning recommendations
- Best practices per framework
- Troubleshooting guide

---

## ✅ Success Criteria

- [ ] Reference CRM app generated for all 3 frameworks
- [ ] React round-trip test passing
- [ ] Vue round-trip test passing
- [ ] Angular round-trip test passing
- [ ] Cross-framework migrations working (6 paths)
- [ ] Performance benchmarks established
- [ ] Large app generation (100+ entities) < 30s
- [ ] All generated apps compile without errors
- [ ] Feature parity across frameworks 95%+
- [ ] 200+ integration tests passing
- [ ] CLI commands functional
- [ ] Complete migration guides

---

## 🧪 Testing Strategy

**Integration Tests**:
- Round-trip for each framework
- Cross-framework migrations
- Large app generation
- Compile checks for all generated code

**Performance Tests**:
- Generation speed benchmarks
- Memory usage profiling
- Output size metrics

**End-to-End Tests**:
- Run generated apps in browser
- Verify all CRUD operations work
- Check GraphQL integration
- Validate form submissions

---

## 📊 Success Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Generation Speed (50 entities) | < 10s | TBD |
| React Round-Trip | 95%+ match | TBD |
| Vue Round-Trip | 95%+ match | TBD |
| Angular Round-Trip | 95%+ match | TBD |
| TypeScript Compilation | 100% pass | TBD |
| Feature Parity | 95%+ | TBD |

---

## 🔗 Related Files

- **Previous**: [Week 29: Angular Parser & Generation](./WEEK_29.md)
- **Next**: [Week 31: Advanced UI Patterns](./WEEK_31.md)
- **Grammar**: [Week 25: Universal Component Grammar](./WEEK_25.md)
- **Parsers**: Weeks 26-29 (React/Vue/Angular)

---

**Status**: 📅 Planned (validates Weeks 25-29)
**Complexity**: High (comprehensive testing across 3 frameworks)
**Risk**: Low (validates proven implementations)
**Impact**: Proves universal grammar works in production
