# Week 43: Core Component Grammar & Parser Foundation

**Date**: 2025-11-13
**Duration**: 5 days
**Status**: 🔴 Planning
**Objective**: Implement production-ready SpecQL frontend grammar parser with full validation and error handling

---

## 🎯 Overview

Transform weeks 39-42 research into production implementation: complete SpecQL frontend grammar that parses YAML definitions into validated AST.

**Deliverables**:
- Complete frontend grammar specification
- YAML parser with validation
- AST data structures
- Error handling and reporting
- CLI integration

---

## Day 1-2: Grammar Specification & AST Design

### Complete Grammar Spec

**File**: `docs/specification/FRONTEND_GRAMMAR_SPEC.md`

Core grammar elements:
- Atomic components (40 types)
- Composite patterns (55 types)
- Workflows (28 types)
- Layouts, navigation, theming
- Platform-specific overrides

### AST Structure

```python
# src/core/frontend/ast_nodes.py

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum

class ComponentTier(Enum):
    ATOMIC = 1
    COMPOSITE = 2
    WORKFLOW = 3

@dataclass
class FrontendAST:
    """Root AST node"""
    entities: Dict[str, EntityFrontend]
    patterns: List[Pattern]
    workflows: List[Workflow]
    layouts: List[Layout]
    navigation: NavigationConfig
    theme: Optional[ThemeConfig] = None

@dataclass
class AtomicComponent:
    """Tier 1: Atomic component"""
    tier: int = 1
    type: str  # text_input, button, etc.
    name: str
    properties: Dict[str, Any]
    events: Dict[str, EventHandler]
    validation: List[ValidationRule]
    platform_mapping: Dict[str, str]

@dataclass
class CompositePattern:
    """Tier 2: Composite pattern"""
    tier: int = 2
    id: str
    category: str
    components: List[AtomicComponent]
    layout: Layout
    behavior: Dict[str, Any]
    state: List[StateVariable]

@dataclass
class Workflow:
    """Tier 3: Complete workflow"""
    tier: int = 3
    name: str
    entity: str
    states: Dict[str, WorkflowState]
    transitions: List[StateTransition]
    queries: Dict[str, str]
    mutations: Dict[str, str]
```

### YAML Parser Implementation

```python
# src/core/frontend/frontend_parser.py

import yaml
from typing import Dict, Any
from .ast_nodes import *

class FrontendParser:
    """Parse SpecQL frontend YAML into AST"""

    def parse_file(self, file_path: str) -> FrontendAST:
        """Parse frontend spec file"""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        return self.parse_dict(data)

    def parse_dict(self, data: Dict[str, Any]) -> FrontendAST:
        """Parse frontend spec dictionary"""
        frontend_section = data.get('frontend', {})

        return FrontendAST(
            entities=self._parse_entities(frontend_section.get('entities', {})),
            patterns=self._parse_patterns(frontend_section.get('patterns', [])),
            workflows=self._parse_workflows(frontend_section.get('workflows', [])),
            layouts=self._parse_layouts(frontend_section.get('layouts', [])),
            navigation=self._parse_navigation(frontend_section.get('navigation', {})),
            theme=self._parse_theme(frontend_section.get('theme'))
        )

    def _parse_entities(self, entities_data: Dict) -> Dict[str, EntityFrontend]:
        """Parse entity-level UI metadata"""
        entities = {}
        for entity_name, entity_def in entities_data.items():
            entities[entity_name] = EntityFrontend(
                name=entity_name,
                label=entity_def.get('label'),
                icon=entity_def.get('icon'),
                defaultListRoute=entity_def.get('defaultListRoute'),
                defaultDetailRoute=entity_def.get('defaultDetailRoute'),
                fields=self._parse_field_metadata(entity_def.get('fields', {}))
            )
        return entities

    def _parse_patterns(self, patterns_data: List) -> List[Pattern]:
        """Parse composite patterns"""
        return [self._parse_pattern(p) for p in patterns_data]

    def _parse_workflows(self, workflows_data: List) -> List[Workflow]:
        """Parse workflow definitions"""
        return [self._parse_workflow(w) for w in workflows_data]

# Unit tests
class TestFrontendParser:
    def test_parse_atomic_component(self):
        yaml_content = """
        frontend:
          components:
            - type: text_input
              name: email
              label: Email Address
              required: true
        """
        parser = FrontendParser()
        ast = parser.parse_dict(yaml.safe_load(yaml_content))
        assert len(ast.components) == 1
        assert ast.components[0].type == 'text_input'
```

---

## Day 3: Validation Engine

### Comprehensive Validation

```python
# src/core/frontend/validator.py

from typing import List, Dict
from .ast_nodes import FrontendAST

class ValidationError:
    def __init__(self, path: str, message: str, severity: str = 'error'):
        self.path = path
        self.message = message
        self.severity = severity

class FrontendValidator:
    """Validate frontend AST"""

    def validate(self, ast: FrontendAST) -> List[ValidationError]:
        """Run all validations"""
        errors = []
        errors.extend(self._validate_components(ast))
        errors.extend(self._validate_patterns(ast))
        errors.extend(self._validate_workflows(ast))
        errors.extend(self._validate_references(ast))
        return errors

    def _validate_components(self, ast: FrontendAST) -> List[ValidationError]:
        """Validate atomic components"""
        errors = []
        for comp in ast.components:
            # Check required properties
            if not comp.name:
                errors.append(ValidationError(
                    f'components.{comp.type}',
                    'Component name is required'
                ))
            # Validate property types
            # Check platform mappings exist
        return errors

    def _validate_references(self, ast: FrontendAST) -> List[ValidationError]:
        """Validate all entity/component references"""
        errors = []
        # Check workflows reference valid entities
        # Check patterns reference valid components
        # Check layouts reference valid pages
        return errors
```

---

## Day 4-5: CLI Integration & Testing

### CLI Commands

```bash
# Parse and validate frontend spec
specql frontend parse entities/user.yaml
specql frontend validate entities/*.yaml

# Generate AST visualization
specql frontend ast entities/user.yaml --output ast.json

# List all patterns/workflows
specql frontend patterns list
specql frontend workflows list
```

### Integration Tests

```python
def test_complete_frontend_parsing():
    """Test parsing complete frontend spec"""
    spec = """
    frontend:
      entities:
        User:
          label: Users
          icon: user
      pages:
        - name: UserList
          type: list
          entity: User
      workflows:
        - name: user_crud
          entity: User
          states: [list, detail, create, edit]
    """
    parser = FrontendParser()
    ast = parser.parse_dict(yaml.safe_load(spec))

    assert 'User' in ast.entities
    assert len(ast.pages) == 1
    assert len(ast.workflows) == 1

    # Validate
    validator = FrontendValidator()
    errors = validator.validate(ast)
    assert len(errors) == 0
```

---

**Status**: ✅ Week 43 Complete - Grammar implemented, ready for code generation
