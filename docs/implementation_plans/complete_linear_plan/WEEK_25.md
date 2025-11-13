# Week 25: Universal Component Grammar Foundation

**Date**: TBD (After Week 24 complete)
**Duration**: 5-6 days
**Status**: 📅 Planned
**Objective**: Define and implement universal component grammar foundation based on specql_front design

**Prerequisites**: Week 24 complete (Go/GORM integration tested)

**Output**:
- Universal component grammar specification (TypeScript types)
- Parser infrastructure for reading component specs
- Validation framework
- Initial component type hierarchy
- Foundation for React/Vue/Angular generators (Weeks 26-36)

---

## 🎯 Executive Summary

This week implements the **universal component grammar** - a framework-agnostic way to describe UI components that can generate React, Vue, Angular, and more. Based on the complete design in the `specql_front` repository, we'll create the foundation that Weeks 26-36 will build upon.

**Key Insight from specql_front**: The grammar already exists as a comprehensive YAML specification. This week we formalize it into SpecQL's core, create the parser/validator, and establish the component type system.

**What Makes This Universal**:
- Framework-agnostic (describes WHAT, not HOW)
- Rich domain types (Company, User, Address - not just tables)
- Declarative pages (list, form, detail, custom)
- Actions with cascade support
- Layout and navigation

---

## 📅 Daily Breakdown

### Day 1: Component Grammar Specification

**Morning Block (4 hours): Core Type System**

Based on specql_front PRD, implement the TypeScript types:

**File**: `src/frontend/universal_component_schema.py`

```python
"""
Universal Component Grammar

Platform-agnostic UI specification that can generate React/Vue/Angular.
Based on specql_front comprehensive design.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Literal
from enum import Enum


# ============================================================================
# Entity Frontend Metadata
# ============================================================================

@dataclass
class EntityFrontend:
    """Frontend metadata for an entity (from specql_front)"""
    label: str  # Human-friendly plural "Users"
    label_singular: Optional[str] = None  # Singular "User"
    icon: Optional[str] = None  # Icon name
    default_list_route: Optional[str] = None  # "/users"
    default_detail_route: Optional[str] = None  # "/users/:id"
    auto_generate_pages: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Field Frontend Metadata
# ============================================================================

class WidgetType(str, Enum):
    """Widget types for form fields"""
    TEXT = "text"
    TEXTAREA = "textarea"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    INTEGER = "integer"
    DATE = "date"
    DATETIME = "datetime"
    CHECKBOX = "checkbox"
    SWITCH = "switch"
    SELECT = "select"
    MULTISELECT = "multiselect"
    TAGS = "tags"
    RADIO = "radio"
    JSON = "json"
    HIDDEN = "hidden"


@dataclass
class OptionsSource:
    """How to get options for select/multiselect"""
    type: Literal["enum", "static", "relation"]
    values: Optional[List[str]] = None  # For static
    entity: Optional[str] = None  # For relation
    label_field: Optional[str] = None  # For relation


@dataclass
class FieldListConfig:
    """Field configuration in list views"""
    visible: bool = True
    order: int = 0
    width: Literal["auto", "small", "medium", "large"] = "auto"


@dataclass
class FieldFormConfig:
    """Field configuration in forms"""
    visible: bool = True
    order: int = 0
    section: Optional[str] = None  # For grouping


@dataclass
class FieldDetailConfig:
    """Field configuration in detail views"""
    visible: bool = True
    order: int = 0


@dataclass
class FieldFrontend:
    """Frontend metadata for a field"""
    label: Optional[str] = None
    widget: Optional[WidgetType] = None
    required: Optional[bool] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    list: Optional[FieldListConfig] = None
    form: Optional[FieldFormConfig] = None
    detail: Optional[FieldDetailConfig] = None
    options: Optional[OptionsSource] = None
    meta: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Page Types
# ============================================================================

class PageType(str, Enum):
    """Page types in the application"""
    LIST = "list"
    FORM = "form"
    DETAIL = "detail"
    CUSTOM = "custom"


@dataclass
class FilterConfig:
    """Filter configuration for list pages"""
    field: str
    type: Literal["string", "number", "boolean", "date", "enum", "relation"]


@dataclass
class ListPageConfig:
    """Configuration for list pages"""
    columns: Optional[List[str]] = None
    default_sort: Optional[Dict[str, str]] = None  # {"field": "email", "direction": "asc"}
    page_size: int = 20
    filters: List[FilterConfig] = field(default_factory=list)
    row_actions: List[str] = field(default_factory=list)  # Action names
    primary_actions: List[str] = field(default_factory=list)


@dataclass
class FormPage:
    """Form page (create/edit)"""
    name: str
    route: str
    type: Literal["form"]
    entity: str
    mode: Literal["create", "edit"]
    layout: Optional[str] = None
    title: Optional[str] = None
    icon: Optional[str] = None
    fields: Optional[List[str]] = None
    submit_action: str = ""
    secondary_actions: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ListPage:
    """List page"""
    name: str
    route: str
    type: Literal["list"]
    entity: str
    layout: Optional[str] = None
    title: Optional[str] = None
    icon: Optional[str] = None
    list_config: Optional[ListPageConfig] = None
    roles: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetailPage:
    """Detail page"""
    name: str
    route: str
    type: Literal["detail"]
    entity: str
    layout: Optional[str] = None
    title: Optional[str] = None
    icon: Optional[str] = None
    fields: Optional[List[str]] = None
    actions: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomPage:
    """Custom page with arbitrary component"""
    name: str
    route: str
    type: Literal["custom"]
    component: str  # Component identifier
    layout: Optional[str] = None
    title: Optional[str] = None
    icon: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    roles: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


# Union of all page types
Page = ListPage | FormPage | DetailPage | CustomPage


# ============================================================================
# Actions
# ============================================================================

class ActionType(str, Enum):
    """Action types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    CUSTOM_MUTATION = "customMutation"
    NAVIGATE = "navigate"


@dataclass
class ActionOnSuccess:
    """Action behavior after success"""
    toast: Optional[str] = None
    redirect_to: Optional[str] = None
    refetch_entities: List[str] = field(default_factory=list)


@dataclass
class ActionOnError:
    """Action behavior after error"""
    toast: Optional[str] = None


@dataclass
class Action:
    """Action definition"""
    name: str
    type: ActionType
    entity: str
    label: Optional[str] = None
    icon: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    mutation: Optional[str] = None  # GraphQL mutation name
    navigate_to: Optional[str] = None
    on_success: Optional[ActionOnSuccess] = None
    on_error: Optional[ActionOnError] = None
    meta: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Layout & Navigation
# ============================================================================

@dataclass
class Layout:
    """Layout definition"""
    id: str
    label: Optional[str] = None
    sidebar: bool = True
    header: bool = True
    title_prefix: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NavItem:
    """Navigation item"""
    id: str
    label: str
    route: Optional[str] = None
    page_name: Optional[str] = None
    icon: Optional[str] = None
    section: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Complete Frontend Specification
# ============================================================================

@dataclass
class UniversalFrontend:
    """
    Complete frontend specification

    This is the universal representation that can be converted to:
    - React/Next.js components
    - Vue/Nuxt components
    - Angular components
    - Svelte components
    """
    # Entity metadata
    entities: Dict[str, EntityFrontend] = field(default_factory=dict)

    # Field metadata (entities[entity_name].fields[field_name])
    fields: Dict[str, Dict[str, FieldFrontend]] = field(default_factory=dict)

    # Page definitions
    pages: List[Page] = field(default_factory=list)

    # Layout definitions
    layouts: List[Layout] = field(default_factory=list)

    # Action definitions
    actions: List[Action] = field(default_factory=list)

    # Navigation items
    navigation: List[NavItem] = field(default_factory=list)

    # Metadata
    version: str = "1.0"
    meta: Dict[str, Any] = field(default_factory=dict)
```

**Afternoon Block (4 hours): YAML Parser**

Implement parser to read frontend specs from YAML:

```python
# src/frontend/yaml_parser.py
"""Parse frontend YAML to UniversalFrontend"""

import yaml
from typing import Dict, Any
from src.frontend.universal_component_schema import *


class FrontendYAMLParser:
    """Parse frontend YAML specifications"""

    def parse(self, yaml_content: str) -> UniversalFrontend:
        """Parse YAML to UniversalFrontend"""
        data = yaml.safe_load(yaml_content)
        frontend_data = data.get('frontend', {})

        return UniversalFrontend(
            entities=self._parse_entities(frontend_data.get('entities', {})),
            fields=self._parse_fields(frontend_data.get('fields', {})),
            pages=self._parse_pages(frontend_data.get('pages', [])),
            layouts=self._parse_layouts(frontend_data.get('layouts', [])),
            actions=self._parse_actions(frontend_data.get('actions', [])),
            navigation=self._parse_navigation(frontend_data.get('navigation', [])),
            version=frontend_data.get('version', '1.0'),
            meta=frontend_data.get('meta', {})
        )

    def _parse_entities(self, entities_data: Dict) -> Dict[str, EntityFrontend]:
        """Parse entity metadata"""
        entities = {}
        for entity_name, entity_data in entities_data.items():
            entities[entity_name] = EntityFrontend(**entity_data)
        return entities

    # ... implement other _parse_* methods
```

---

### Day 2: Validation Framework

**Morning Block (4 hours): Schema Validation**

Create validation for component specs:

```python
# src/frontend/validator.py
"""Validate frontend specifications"""

from typing import List, Dict
from src.frontend.universal_component_schema import UniversalFrontend


class ValidationError:
    """Validation error"""
    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message


class FrontendValidator:
    """Validate frontend specifications"""

    def validate(self, frontend: UniversalFrontend) -> List[ValidationError]:
        """Validate complete frontend spec"""
        errors = []

        errors.extend(self._validate_entities(frontend))
        errors.extend(self._validate_pages(frontend))
        errors.extend(self._validate_actions(frontend))
        errors.extend(self._validate_navigation(frontend))

        return errors

    def _validate_entities(self, frontend: UniversalFrontend) -> List[ValidationError]:
        """Validate entity metadata"""
        errors = []

        for entity_name, entity in frontend.entities.items():
            # Validate label
            if not entity.label:
                errors.append(ValidationError(
                    f"entities.{entity_name}",
                    "Entity must have a label"
                ))

            # Validate routes
            if entity.auto_generate_pages:
                if not entity.default_list_route:
                    errors.append(ValidationError(
                        f"entities.{entity_name}",
                        "Entity with auto_generate_pages must have default_list_route"
                    ))

        return errors

    def _validate_pages(self, frontend: UniversalFrontend) -> List[ValidationError]:
        """Validate page definitions"""
        errors = []
        routes_seen = set()

        for page in frontend.pages:
            # Check for duplicate routes
            if page.route in routes_seen:
                errors.append(ValidationError(
                    f"pages.{page.name}",
                    f"Duplicate route: {page.route}"
                ))
            routes_seen.add(page.route)

            # Validate entity exists
            if hasattr(page, 'entity') and page.entity not in frontend.entities:
                errors.append(ValidationError(
                    f"pages.{page.name}",
                    f"Referenced entity '{page.entity}' not found"
                ))

            # Validate actions exist
            if hasattr(page, 'list_config') and page.list_config:
                for action_name in page.list_config.row_actions:
                    if not any(a.name == action_name for a in frontend.actions):
                        errors.append(ValidationError(
                            f"pages.{page.name}.list_config.row_actions",
                            f"Action '{action_name}' not found"
                        ))

        return errors
```

**Afternoon Block (4 hours): Integration Tests**

Test parsing and validation with real specs from specql_front.

---

### Days 3-4: Component Type Hierarchy

Implement the component type system:

**Day 3**: Atomic components (text, button, input, select, etc.)
**Day 4**: Composite components (form, table, card, etc.)

---

### Day 5: CLI Integration & Documentation

**Morning**: Add `specql frontend` CLI commands
**Afternoon**: Documentation and examples

---

## ✅ Success Criteria

- [ ] Universal component grammar types defined
- [ ] YAML parser reads frontend specs
- [ ] Validation framework working
- [ ] Component type hierarchy established
- [ ] 100+ unit tests passing
- [ ] Integration with SpecQL core
- [ ] CLI commands for frontend validation
- [ ] Documentation complete

---

## 🔗 Related Files

- **Previous**: [Week 24: Go Integration Testing](./WEEK_24.md)
- **Next**: [Week 26: React Parser Foundation](./WEEK_26.md)
- **Reference**: `/home/lionel/code/specql_front/PRD.md` - Complete grammar design
- **Integration**: This week establishes foundation for Weeks 26-36

---

**Status**: 📅 Planned (comprehensive grammar based on specql_front)
**Complexity**: High (but design is complete)
**Risk**: Low (design proven, implementation straightforward)
