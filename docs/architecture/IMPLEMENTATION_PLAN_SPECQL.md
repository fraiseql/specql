# Implementation Plan: SpecQL-Based Schema Generator

**Project**: PrintOptim Backend - SpecQL Integration
**Date**: November 8, 2025
**Status**: Implementation Plan - APPROVED (SpecQL-Aligned)
**Methodology**: Phased TDD Approach

---

## Executive Summary

This plan implements a **SpecQL-compatible schema generator** that:

1. **Parses business-focused YAML** (40-60 lines vs 200+ lines)
2. **Generates PostgreSQL schema** (tables, views, functions)
3. **Generates SpecQL action steps** (business logic DSL)
4. **Auto-generates GraphQL API** (via FraiseQL introspection)
5. **Integrates AI agents** (optional automation layer)

**Key Insight**: Framework handles 80% (infrastructure), YAML specifies 20% (business rules)

**Timeline**: 10 weeks (5 phases)
**Complexity**: Complex - Phased TDD Approach
**Total Effort**: ~280 hours
**ROI**: 90% reduction in backend development time

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ YAML Entity (Business-Focused - 40-60 lines)                │
│   entity: Manufacturer                                      │
│     fields: {identifier, name, abbreviation}                │
│     actions:                                                │
│       - name: create_manufacturer                           │
│         steps: [validate, insert, notify]                   │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────────┐  ┌─────────────────────┐
│ SpecQL Compiler     │  │ Numbering System    │
│ (Business → SQL)    │  │ (Hierarchy)         │
└──────────┬──────────┘  └──────────┬──────────┘
           │                        │
           ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Generated PostgreSQL Schema                                 │
│   01_write_side/013_catalog/.../013211_tb_manufacturer.sql  │
│   - Trinity Pattern table                                   │
│   - Group leader triggers                                   │
│   - Business logic functions                                │
│   - COMMENT annotations for FraiseQL                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FraiseQL Auto-Discovery                                     │
│   - GraphQL types (Contact, Manufacturer, etc.)             │
│   - Queries (contact, contacts, manufacturers)              │
│   - Mutations (createContact, qualifyLead)                  │
│   - Filters (where, orderBy, pagination)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Full-Stack Backend API                                      │
│   - TypeScript types                                        │
│   - React hooks                                             │
│   - Auto-generated tests                                    │
│   - API documentation                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Critical Success Factors

### Pre-Flight Checklist
- [ ] SpecQL DSL syntax finalized (action step grammar)
- [ ] FraiseQL integration tested (COMMENT → GraphQL)
- [ ] PostgreSQL 14+ with Trinity Pattern support
- [ ] Test database instance available
- [ ] Python 3.8+, Jinja2, YAML parser ready

### Core Principles
1. **Business-Focused YAML**: Only domain logic, no infrastructure
2. **Framework Generates Boilerplate**: CRUD, permissions, audit, events
3. **SpecQL DSL**: Declarative business workflows
4. **Incremental**: Each phase delivers working system
5. **Test-Driven**: Every feature has failing → passing → refactored tests

---

## PHASE 1: SpecQL YAML Parser + Validator (Week 1-2)

**Objective**: Parse SpecQL-style YAML and validate business logic
**Duration**: 50 hours
**Complexity**: Complex - Phased TDD

### Phase 1 Overview

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: SpecQL YAML                                          │
│   entity: Contact                                           │
│     fields:                                                 │
│       email: text                                           │
│       status: enum(lead, qualified, customer)               │
│     actions:                                                │
│       - name: create_contact                                │
│         steps:                                              │
│           - validate: email MATCHES email_pattern           │
│           - insert: Contact(...)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: Parsed AST + Validation                             │
│   - Entity metadata                                         │
│   - Field definitions (types, refs, enums)                  │
│   - Action workflows (validated steps)                      │
│   - Business rules (validated expressions)                  │
└─────────────────────────────────────────────────────────────┘
```

---

### Iteration 1.1: SpecQL YAML Schema Validator (TDD Cycle)

#### 🔴 RED Phase - Write Failing Test
**Time**: 2 hours

```python
# tests/test_specql_parser.py
import pytest
from src.specql_parser import SpecQLParser, ParseError

def test_parse_simple_entity():
    """Test parsing basic SpecQL entity definition"""
    yaml_content = """
entity: Contact
  schema: crm
  description: "Customer contact"

  fields:
    first_name: text
    last_name: text
    email: text
    status: enum(lead, qualified, customer)
    company: ref(Company)

  actions:
    - name: create_contact
      steps:
        - validate: email MATCHES email_pattern
          error: "invalid_email"
        - insert: Contact
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Verify entity metadata
    assert entity.name == 'Contact'
    assert entity.schema == 'crm'
    assert entity.description == 'Customer contact'

    # Verify fields
    assert 'email' in entity.fields
    assert entity.fields['email'].type == 'text'

    # Verify enum field
    assert entity.fields['status'].type == 'enum'
    assert entity.fields['status'].values == ['lead', 'qualified', 'customer']

    # Verify ref field
    assert entity.fields['company'].type == 'ref'
    assert entity.fields['company'].target_entity == 'Company'

    # Verify actions
    assert len(entity.actions) == 1
    assert entity.actions[0].name == 'create_contact'
    assert len(entity.actions[0].steps) == 2

def test_parse_action_steps():
    """Test parsing action step DSL"""
    yaml_content = """
entity: Reservation
  actions:
    - name: create_reservation
      steps:
        - validate: reserved_from <= reserved_until
          error: "invalid_date_range"

        - if: reserved_from < CURRENT_DATE
          then:
            - reject: "past_date_not_allowed"

        - find: current_allocation WHERE fk_machine = input.machine_id

        - update: current_allocation SET end_date = reserved_from - 1

        - insert: Allocation(machine, start_date, end_date)

        - call: update_machine_flags(machine_id = input.machine_id)
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    action = entity.actions[0]

    # Verify step types
    assert action.steps[0].type == 'validate'
    assert action.steps[0].expression == 'reserved_from <= reserved_until'
    assert action.steps[0].error == 'invalid_date_range'

    assert action.steps[1].type == 'if'
    assert action.steps[1].condition == 'reserved_from < CURRENT_DATE'
    assert len(action.steps[1].then_steps) == 1

    assert action.steps[2].type == 'find'
    assert action.steps[2].entity == 'current_allocation'

    assert action.steps[3].type == 'update'
    assert action.steps[4].type == 'insert'
    assert action.steps[5].type == 'call'

def test_validate_action_steps():
    """Test validation of business logic steps"""
    yaml_content = """
entity: Contact
  actions:
    - name: create_contact
      steps:
        - validate: invalid_field_name > 10
"""

    parser = SpecQLParser()

    with pytest.raises(ParseError, match="Field 'invalid_field_name' not found"):
        parser.parse(yaml_content)

def test_parse_ai_agents():
    """Test parsing AI agent configuration"""
    yaml_content = """
entity: Contact
  agents:
    - name: lead_scoring_agent
      type: ai_llm
      observes: ['contact.created', 'activity.logged']
      can_execute: ['update_lead_score', 'qualify_lead']
      strategy: |
        Analyze contact data and score 0-100 based on:
        1. Company size
        2. Industry fit
        3. Engagement level
      audit: required
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert len(entity.agents) == 1
    agent = entity.agents[0]

    assert agent.name == 'lead_scoring_agent'
    assert agent.type == 'ai_llm'
    assert 'contact.created' in agent.observes
    assert 'update_lead_score' in agent.can_execute
    assert agent.audit == 'required'
    assert 'Company size' in agent.strategy

def test_parse_with_numbering_system():
    """Test integration with numbering system"""
    yaml_content = """
entity: Manufacturer
  schema: catalog
  organization:
    table_code: "013211"
    domain_name: "catalog"

  fields:
    identifier: text
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.organization.table_code == '013211'
    assert entity.organization.domain_name == 'catalog'
```

**Run test** (expect failures):
```bash
uv run pytest tests/test_specql_parser.py -v
# Expected: FAILED - SpecQLParser not found
```

---

#### 🟢 GREEN Phase - Minimal Implementation
**Time**: 8 hours

```python
# src/specql_parser.py
"""
SpecQL YAML Parser
Parses business-focused entity definitions into AST
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import yaml
import re

class ParseError(Exception):
    """Raised when YAML parsing fails"""
    pass

@dataclass
class FieldDefinition:
    """Parsed field definition"""
    name: str
    type: str  # text, integer, enum, ref, list
    nullable: bool = True
    default: Optional[Any] = None

    # For enum fields
    values: Optional[List[str]] = None

    # For ref fields
    target_entity: Optional[str] = None

    # For list fields
    item_type: Optional[str] = None

@dataclass
class ActionStep:
    """Parsed action step"""
    type: str  # validate, if, insert, update, delete, call, find, etc.

    # For validate steps
    expression: Optional[str] = None
    error: Optional[str] = None

    # For conditional steps
    condition: Optional[str] = None
    then_steps: List['ActionStep'] = field(default_factory=list)
    else_steps: List['ActionStep'] = field(default_factory=list)

    # For database operations
    entity: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None
    where_clause: Optional[str] = None

    # For function calls
    function_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    store_result: Optional[str] = None

@dataclass
class Action:
    """Parsed action definition"""
    name: str
    requires: Optional[str] = None  # Permission expression
    steps: List[ActionStep] = field(default_factory=list)

@dataclass
class Agent:
    """Parsed AI agent definition"""
    name: str
    type: str  # ai_llm, rule_based
    observes: List[str] = field(default_factory=list)
    can_execute: List[str] = field(default_factory=list)
    strategy: str = ""
    audit: str = "required"

@dataclass
class Organization:
    """Entity organization metadata (numbering system)"""
    table_code: str
    domain_name: Optional[str] = None

@dataclass
class Entity:
    """Parsed SpecQL entity"""
    name: str
    schema: str = "public"
    table: Optional[str] = None  # If different from entity name
    description: str = ""

    fields: Dict[str, FieldDefinition] = field(default_factory=dict)
    actions: List[Action] = field(default_factory=list)
    agents: List[Agent] = field(default_factory=list)

    # Numbering system integration
    organization: Optional[Organization] = None

class SpecQLParser:
    """Parse SpecQL YAML into AST"""

    def parse(self, yaml_content: str) -> Entity:
        """
        Parse YAML content into Entity AST

        Args:
            yaml_content: YAML string to parse

        Returns:
            Entity AST

        Raises:
            ParseError: If YAML is invalid
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ParseError(f"Invalid YAML: {e}")

        if 'entity' not in data:
            raise ParseError("Missing 'entity' key in YAML")

        entity_data = data['entity']

        # Parse entity metadata
        if isinstance(entity_data, str):
            # Simple form: entity: EntityName
            entity_name = entity_data
            entity_config = data
        else:
            # Complex form: entity contains all config
            entity_name = entity_data.get('name')
            if not entity_name:
                raise ParseError("Entity name is required")
            entity_config = entity_data

        entity = Entity(
            name=entity_name,
            schema=entity_config.get('schema', 'public'),
            table=entity_config.get('table'),
            description=entity_config.get('description', '')
        )

        # Parse organization (numbering system)
        if 'organization' in entity_config:
            org_data = entity_config['organization']
            entity.organization = Organization(
                table_code=org_data['table_code'],
                domain_name=org_data.get('domain_name')
            )

        # Parse fields
        if 'fields' in entity_config:
            entity.fields = self._parse_fields(entity_config['fields'])

        # Parse actions
        if 'actions' in entity_config:
            entity.actions = self._parse_actions(
                entity_config['actions'],
                entity.fields
            )

        # Parse agents
        if 'agents' in entity_config:
            entity.agents = self._parse_agents(entity_config['agents'])

        return entity

    def _parse_fields(self, fields_data: Dict) -> Dict[str, FieldDefinition]:
        """Parse field definitions"""
        fields = {}

        for field_name, field_spec in fields_data.items():
            field_def = self._parse_field_spec(field_name, field_spec)
            fields[field_name] = field_def

        return fields

    def _parse_field_spec(self, name: str, spec: Any) -> FieldDefinition:
        """
        Parse individual field specification

        Formats:
        - field_name: text
        - field_name: ref(Entity)
        - field_name: enum(val1, val2, val3)
        - field_name: list(ref(Entity))
        - field_name: text = default_value
        """
        # Handle default values (text = "default")
        if isinstance(spec, str) and ' = ' in spec:
            type_part, default_part = spec.split(' = ', 1)
            spec = type_part.strip()
            default = default_part.strip().strip('"\'')
        else:
            default = None

        # Simple type
        if isinstance(spec, str):
            # Check for ref(Entity)
            ref_match = re.match(r'ref\((\w+)\)', spec)
            if ref_match:
                return FieldDefinition(
                    name=name,
                    type='ref',
                    target_entity=ref_match.group(1),
                    default=default
                )

            # Check for enum(val1, val2, ...)
            enum_match = re.match(r'enum\((.*)\)', spec)
            if enum_match:
                values = [v.strip() for v in enum_match.group(1).split(',')]
                return FieldDefinition(
                    name=name,
                    type='enum',
                    values=values,
                    default=default
                )

            # Check for list(type)
            list_match = re.match(r'list\((.*)\)', spec)
            if list_match:
                item_spec = list_match.group(1)
                return FieldDefinition(
                    name=name,
                    type='list',
                    item_type=item_spec,
                    default=default
                )

            # Simple type (text, integer, etc.)
            return FieldDefinition(
                name=name,
                type=spec,
                default=default
            )

        # Complex specification (dict)
        elif isinstance(spec, dict):
            return FieldDefinition(
                name=name,
                type=spec.get('type', 'text'),
                nullable=spec.get('nullable', True),
                default=spec.get('default'),
                values=spec.get('values'),
                target_entity=spec.get('ref')
            )

        raise ParseError(f"Invalid field specification for '{name}': {spec}")

    def _parse_actions(
        self,
        actions_data: List[Dict],
        entity_fields: Dict[str, FieldDefinition]
    ) -> List[Action]:
        """Parse action definitions"""
        actions = []

        for action_data in actions_data:
            action = Action(
                name=action_data['name'],
                requires=action_data.get('requires')
            )

            # Parse action steps
            if 'steps' in action_data:
                action.steps = self._parse_steps(
                    action_data['steps'],
                    entity_fields
                )

            actions.append(action)

        return actions

    def _parse_steps(
        self,
        steps_data: List,
        entity_fields: Dict[str, FieldDefinition]
    ) -> List[ActionStep]:
        """Parse action step DSL"""
        steps = []

        for step_data in steps_data:
            step = self._parse_single_step(step_data, entity_fields)
            steps.append(step)

        return steps

    def _parse_single_step(
        self,
        step_data: Dict,
        entity_fields: Dict[str, FieldDefinition]
    ) -> ActionStep:
        """Parse single action step"""

        # Validate step
        if 'validate' in step_data:
            expression = step_data['validate']

            # Validate field references in expression
            self._validate_expression_fields(expression, entity_fields)

            return ActionStep(
                type='validate',
                expression=expression,
                error=step_data.get('error', 'validation_failed')
            )

        # If-then-else step
        elif 'if' in step_data:
            condition = step_data['if']
            then_steps = self._parse_steps(
                step_data.get('then', []),
                entity_fields
            )
            else_steps = self._parse_steps(
                step_data.get('else', []),
                entity_fields
            )

            return ActionStep(
                type='if',
                condition=condition,
                then_steps=then_steps,
                else_steps=else_steps
            )

        # Insert step
        elif 'insert' in step_data:
            entity_spec = step_data['insert']

            # Parse entity name and fields
            if isinstance(entity_spec, str):
                # Simple form: insert: Entity
                entity_name = entity_spec
                fields = None
            else:
                # Complex form: insert: Entity(field1, field2)
                match = re.match(r'(\w+)\((.*)\)', entity_spec)
                if match:
                    entity_name = match.group(1)
                    field_list = [f.strip() for f in match.group(2).split(',')]
                    fields = {f: f"input.{f}" for f in field_list}
                else:
                    raise ParseError(f"Invalid insert syntax: {entity_spec}")

            return ActionStep(
                type='insert',
                entity=entity_name,
                fields=fields
            )

        # Update step
        elif 'update' in step_data:
            update_spec = step_data['update']

            # Parse: update: entity SET field = value WHERE condition
            parts = re.split(r'\s+SET\s+|\s+WHERE\s+', update_spec, flags=re.IGNORECASE)

            entity_name = parts[0].strip()
            set_clause = parts[1].strip() if len(parts) > 1 else None
            where_clause = parts[2].strip() if len(parts) > 2 else None

            return ActionStep(
                type='update',
                entity=entity_name,
                fields={'raw_set': set_clause},
                where_clause=where_clause
            )

        # Delete step
        elif 'delete' in step_data:
            return ActionStep(
                type='delete',
                entity=step_data['delete']
            )

        # Find step
        elif 'find' in step_data:
            find_spec = step_data['find']

            # Parse: find: entity WHERE condition
            parts = re.split(r'\s+WHERE\s+', find_spec, maxsplit=1, flags=re.IGNORECASE)
            entity_name = parts[0].strip()
            where_clause = parts[1].strip() if len(parts) > 1 else None

            return ActionStep(
                type='find',
                entity=entity_name,
                where_clause=where_clause
            )

        # Call step
        elif 'call' in step_data:
            call_spec = step_data['call']

            # Parse: call: function_name(arg1 = val1, arg2 = val2)
            match = re.match(r'(\w+)\((.*)\)', call_spec)
            if match:
                function_name = match.group(1)
                args_str = match.group(2)

                # Parse arguments
                arguments = {}
                if args_str:
                    for arg in args_str.split(','):
                        arg = arg.strip()
                        if '=' in arg:
                            key, value = arg.split('=', 1)
                            arguments[key.strip()] = value.strip()

                return ActionStep(
                    type='call',
                    function_name=function_name,
                    arguments=arguments,
                    store_result=step_data.get('store')
                )
            else:
                raise ParseError(f"Invalid call syntax: {call_spec}")

        # Reject step
        elif 'reject' in step_data:
            return ActionStep(
                type='reject',
                error=step_data['reject']
            )

        else:
            raise ParseError(f"Unknown step type: {step_data}")

    def _validate_expression_fields(
        self,
        expression: str,
        entity_fields: Dict[str, FieldDefinition]
    ) -> None:
        """Validate that fields referenced in expression exist"""
        # Extract field names (simple heuristic: words before operators)
        potential_fields = re.findall(r'\b([a-z_][a-z0-9_]*)\b', expression.lower())

        # Filter out common keywords
        keywords = {'and', 'or', 'not', 'null', 'true', 'false', 'current_date',
                   'exists', 'is', 'in', 'like', 'between', 'input', 'matches'}

        for field_name in potential_fields:
            if field_name not in keywords and field_name not in entity_fields:
                # Allow input.field_name
                if not expression.startswith(f'input.{field_name}'):
                    raise ParseError(
                        f"Field '{field_name}' referenced in expression not found in entity. "
                        f"Available fields: {', '.join(entity_fields.keys())}"
                    )

    def _parse_agents(self, agents_data: List[Dict]) -> List[Agent]:
        """Parse AI agent definitions"""
        agents = []

        for agent_data in agents_data:
            agent = Agent(
                name=agent_data['name'],
                type=agent_data.get('type', 'rule_based'),
                observes=agent_data.get('observes', []),
                can_execute=agent_data.get('can_execute', []),
                strategy=agent_data.get('strategy', ''),
                audit=agent_data.get('audit', 'required')
            )
            agents.append(agent)

        return agents
```

**Run test**:
```bash
uv run pytest tests/test_specql_parser.py -v
# Expected: PASSED (most tests green)
```

---

#### 🔧 REFACTOR Phase - Clean Up
**Time**: 3 hours

**Improvements:**
1. Extract regex patterns to constants
2. Add comprehensive docstrings
3. Better error messages with line numbers
4. Support for switch/case statements
5. Support for computed fields

```python
# src/specql_parser.py (refactored)

class SpecQLParser:
    """Parse SpecQL YAML into AST with comprehensive validation"""

    # Regex patterns (extracted)
    REF_PATTERN = re.compile(r'ref\((\w+)\)')
    ENUM_PATTERN = re.compile(r'enum\((.*)\)')
    LIST_PATTERN = re.compile(r'list\((.*)\)')
    INSERT_PATTERN = re.compile(r'(\w+)\((.*)\)')
    UPDATE_PATTERN = re.compile(r'(\w+)\s+SET\s+(.*?)(?:\s+WHERE\s+(.*))?$', re.IGNORECASE)
    CALL_PATTERN = re.compile(r'(\w+)\((.*)\)')

    # Reserved keywords
    KEYWORDS = {
        'and', 'or', 'not', 'null', 'true', 'false', 'current_date',
        'exists', 'is', 'in', 'like', 'between', 'input', 'matches',
        'current_timestamp', 'now', 'select', 'from', 'where'
    }

    def parse_with_context(self, yaml_content: str, filename: str = '<string>') -> Entity:
        """
        Parse YAML with context for better error messages

        Args:
            yaml_content: YAML string
            filename: Source filename for error reporting

        Returns:
            Parsed Entity
        """
        try:
            return self.parse(yaml_content)
        except ParseError as e:
            raise ParseError(f"{filename}: {e}")

    # ... rest of refactored implementation
```

---

#### ✅ QA Phase - Verify Quality
**Time**: 2 hours

```bash
# Run full test suite
uv run pytest tests/test_specql_parser.py -v --cov=src/specql_parser

# Run linting
uv run ruff check src/specql_parser.py

# Run type checking
uv run mypy src/specql_parser.py

# Check test coverage (should be >90%)
uv run pytest --cov=src --cov-report=html
```

**Quality Gates:**
- [ ] All tests pass
- [ ] Code coverage > 90%
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Handles all SpecQL step types
- [ ] Clear error messages

---

### Iteration 1.2: SQL Generator for SpecQL Actions (TDD Cycle)

#### 🔴 RED Phase
**Time**: 2 hours

```python
# tests/test_specql_sql_generator.py
def test_generate_action_function():
    """Test generating SQL function from SpecQL action"""
    generator = SpecQLSQLGenerator()

    entity = Entity(
        name='Contact',
        schema='crm',
        fields={
            'email': FieldDefinition(name='email', type='text'),
            'status': FieldDefinition(name='status', type='enum',
                                     values=['lead', 'qualified'])
        },
        actions=[
            Action(
                name='create_contact',
                steps=[
                    ActionStep(
                        type='validate',
                        expression='email MATCHES email_pattern',
                        error='invalid_email'
                    ),
                    ActionStep(
                        type='insert',
                        entity='Contact'
                    )
                ]
            )
        ]
    )

    sql = generator.generate_action_function(entity, entity.actions[0])

    # Verify SQL structure
    assert 'CREATE OR REPLACE FUNCTION crm.fn_create_contact' in sql
    assert 'IF NOT (email ~ email_pattern) THEN' in sql
    assert "RETURN error('invalid_email')" in sql
    assert 'INSERT INTO crm.tb_contact' in sql
    assert 'RETURN success(result)' in sql

def test_generate_conditional_logic():
    """Test generating if-then-else SQL"""
    step = ActionStep(
        type='if',
        condition='status = \'lead\'',
        then_steps=[
            ActionStep(type='call', function_name='score_lead')
        ],
        else_steps=[
            ActionStep(type='call', function_name='skip_scoring')
        ]
    )

    generator = SpecQLSQLGenerator()
    sql = generator.generate_step_sql(step)

    assert 'IF (status = \'lead\') THEN' in sql
    assert 'score_lead()' in sql
    assert 'ELSE' in sql
    assert 'skip_scoring()' in sql
```

---

#### 🟢 GREEN Phase
**Time**: 12 hours

Create comprehensive SQL generator:

```python
# src/specql_sql_generator.py
"""
SpecQL SQL Generator
Compiles SpecQL action steps to PostgreSQL functions
"""
from typing import List
from src.specql_parser import Entity, Action, ActionStep
from jinja2 import Environment, FileSystemLoader

class SpecQLSQLGenerator:
    """Generate PostgreSQL functions from SpecQL actions"""

    def __init__(self, templates_dir='templates'):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate_action_function(self, entity: Entity, action: Action) -> str:
        """
        Generate complete SQL function for action

        Returns:
            PostgreSQL function SQL
        """
        template = self.env.get_template('specql_action_function.sql.j2')

        # Generate SQL for each step
        steps_sql = []
        for step in action.steps:
            step_sql = self.generate_step_sql(step, entity)
            steps_sql.append(step_sql)

        return template.render(
            entity=entity,
            action=action,
            steps_sql=steps_sql
        )

    def generate_step_sql(self, step: ActionStep, entity: Entity) -> str:
        """
        Generate SQL for single action step

        Converts SpecQL DSL to PL/pgSQL
        """
        if step.type == 'validate':
            return self._generate_validate_sql(step)

        elif step.type == 'if':
            return self._generate_if_sql(step, entity)

        elif step.type == 'insert':
            return self._generate_insert_sql(step, entity)

        elif step.type == 'update':
            return self._generate_update_sql(step, entity)

        elif step.type == 'find':
            return self._generate_find_sql(step)

        elif step.type == 'call':
            return self._generate_call_sql(step)

        elif step.type == 'reject':
            return f"RETURN error('{step.error}');"

        else:
            raise ValueError(f"Unknown step type: {step.type}")

    def _generate_validate_sql(self, step: ActionStep) -> str:
        """Generate validation SQL"""
        # Convert SpecQL expression to SQL
        sql_expression = self._convert_expression_to_sql(step.expression)

        return f"""
-- Validation: {step.expression}
IF NOT ({sql_expression}) THEN
    RETURN error('{step.error}',
        message => 'Validation failed: {step.expression}',
        field => '{self._extract_field_name(step.expression)}'
    );
END IF;
"""

    def _generate_if_sql(self, step: ActionStep, entity: Entity) -> str:
        """Generate if-then-else SQL"""
        condition_sql = self._convert_expression_to_sql(step.condition)

        then_sql = '\n'.join([
            self.generate_step_sql(s, entity) for s in step.then_steps
        ])

        if step.else_steps:
            else_sql = '\n'.join([
                self.generate_step_sql(s, entity) for s in step.else_steps
            ])
            return f"""
IF ({condition_sql}) THEN
    {self._indent(then_sql)}
ELSE
    {self._indent(else_sql)}
END IF;
"""
        else:
            return f"""
IF ({condition_sql}) THEN
    {self._indent(then_sql)}
END IF;
"""

    def _generate_insert_sql(self, step: ActionStep, entity: Entity) -> str:
        """Generate INSERT SQL"""
        table_name = f"{entity.schema}.tb_{step.entity.lower()}"

        if step.fields:
            # Explicit fields
            field_names = ', '.join(step.fields.keys())
            field_values = ', '.join(step.fields.values())

            return f"""
-- Insert into {step.entity}
INSERT INTO {table_name} ({field_names})
VALUES ({field_values})
RETURNING * INTO v_result;
"""
        else:
            # All fields from input
            return f"""
-- Insert into {step.entity}
INSERT INTO {table_name}
SELECT * FROM jsonb_populate_record(NULL::{table_name}, p_input)
RETURNING * INTO v_result;
"""

    def _generate_update_sql(self, step: ActionStep, entity: Entity) -> str:
        """Generate UPDATE SQL"""
        table_name = f"{entity.schema}.tb_{step.entity.lower()}"
        set_clause = step.fields.get('raw_set', '')
        where_clause = step.where_clause or 'TRUE'

        return f"""
-- Update {step.entity}
UPDATE {table_name}
SET {set_clause}
WHERE {where_clause};
"""

    def _generate_find_sql(self, step: ActionStep) -> str:
        """Generate SELECT/FIND SQL"""
        return f"""
-- Find {step.entity}
SELECT * INTO v_{step.entity}
FROM {step.entity}
WHERE {step.where_clause or 'TRUE'};
"""

    def _generate_call_sql(self, step: ActionStep) -> str:
        """Generate function call SQL"""
        args = ', '.join([
            f"{k} => {v}" for k, v in (step.arguments or {}).items()
        ])

        if step.store_result:
            return f"""
-- Call {step.function_name}
SELECT {step.function_name}({args}) INTO v_{step.store_result};
"""
        else:
            return f"""
-- Call {step.function_name}
PERFORM {step.function_name}({args});
"""

    def _convert_expression_to_sql(self, expression: str) -> str:
        """
        Convert SpecQL expression to SQL

        Examples:
        - email MATCHES email_pattern → email ~ email_pattern
        - status IN allowed_statuses → status = ANY(allowed_statuses)
        - reserved_from <= reserved_until → (same)
        """
        # Replace MATCHES with SQL regex operator
        expression = expression.replace(' MATCHES ', ' ~ ')

        # Replace input.field with p_input->'field'
        expression = re.sub(
            r'\binput\.(\w+)',
            r"p_input->'\1'",
            expression
        )

        return expression

    def _extract_field_name(self, expression: str) -> str:
        """Extract primary field name from expression"""
        # Simple heuristic: first word
        match = re.match(r'(\w+)', expression)
        return match.group(1) if match else 'unknown'

    def _indent(self, text: str, spaces: int = 4) -> str:
        """Indent text block"""
        indent = ' ' * spaces
        return '\n'.join([indent + line for line in text.split('\n')])
```

Create Jinja2 template:

```jinja2
{# templates/specql_action_function.sql.j2 #}
-- ============================================================================
-- SpecQL Action Function: {{ entity.schema }}.{{ action.name }}
-- ============================================================================
-- Auto-generated from SpecQL YAML definition
-- Entity: {{ entity.name }}
-- Action: {{ action.name }}
-- ============================================================================

CREATE OR REPLACE FUNCTION {{ entity.schema }}.fn_{{ action.name }}(
    p_input JSONB,
    p_caller JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE(
    success BOOLEAN,
    result JSONB,
    error TEXT,
    message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_result RECORD;
    {%- for field in entity.fields.values() %}
    v_{{ field.name }} {{ field.type | upper }};
    {%- endfor %}
BEGIN
    -- ========================================================================
    -- Permission Check
    -- ========================================================================
    {%- if action.requires %}
    IF NOT ({{ action.requires }}) THEN
        RETURN QUERY SELECT
            FALSE AS success,
            NULL::jsonb AS result,
            'permission_denied' AS error,
            'You do not have permission to perform this action' AS message;
        RETURN;
    END IF;
    {%- endif %}

    -- ========================================================================
    -- Extract Input Fields
    -- ========================================================================
    {%- for field in entity.fields.values() %}
    v_{{ field.name }} := (p_input->>'{{ field.name }}')::{{ field.type | upper }};
    {%- endfor %}

    -- ========================================================================
    -- Business Logic Steps
    -- ========================================================================
    {%- for step_sql in steps_sql %}
    {{ step_sql }}
    {%- endfor %}

    -- ========================================================================
    -- Success Response
    -- ========================================================================
    RETURN QUERY SELECT
        TRUE AS success,
        to_jsonb(v_result) AS result,
        NULL::text AS error,
        'Action completed successfully' AS message;

    -- ========================================================================
    -- Audit Log (Framework)
    -- ========================================================================
    INSERT INTO audit.tb_audit_log (
        entity_name,
        action_name,
        caller_id,
        input_data,
        result_data,
        timestamp
    ) VALUES (
        '{{ entity.name }}',
        '{{ action.name }}',
        (p_caller->>'user_id')::uuid,
        p_input,
        to_jsonb(v_result),
        now()
    );

    -- ========================================================================
    -- Event Emission (Framework)
    -- ========================================================================
    PERFORM emit_event(
        event_type => '{{ entity.name.lower() }}.{{ action.name }}',
        event_data => to_jsonb(v_result)
    );

EXCEPTION
    WHEN OTHERS THEN
        -- Framework-level exception handling
        RETURN QUERY SELECT
            FALSE AS success,
            NULL::jsonb AS result,
            SQLSTATE AS error,
            SQLERRM AS message;
END;
$$;

COMMENT ON FUNCTION {{ entity.schema }}.fn_{{ action.name }}(JSONB, JSONB) IS
'{{ action.name }} - Auto-generated from SpecQL';

-- ============================================================================
-- FraiseQL Metadata Annotation
-- ============================================================================
COMMENT ON FUNCTION {{ entity.schema }}.fn_{{ action.name }}(JSONB, JSONB) IS
'@fraiseql:mutation
name: {{ action.name }}
input_type: {{ entity.name }}Input
output_type: {{ entity.name }}Result
';
```

---

#### 🔧 REFACTOR Phase
**Time**: 4 hours

- Extract SQL generation helpers to utility module
- Add expression parser for complex SpecQL syntax
- Support for switch/case statements
- Better error messages with line numbers

---

#### ✅ QA Phase
**Time**: 3 hours

```bash
# Integration test: Parse YAML → Generate SQL → Apply to DB
uv run pytest tests/integration/test_specql_end_to_end.py -v

# Check generated SQL is valid
uv run python -m src.validate_sql generated/
```

---

### Phase 1 Deliverables

**Completion Checklist:**
- [ ] SpecQLParser with full action step DSL support
- [ ] SpecQLSQLGenerator generates valid PL/pgSQL
- [ ] Support for: validate, if/then/else, insert, update, delete, find, call
- [ ] Framework annotations (permissions, audit, events)
- [ ] FraiseQL COMMENT annotations
- [ ] Tests coverage > 90%
- [ ] Example entity (Contact) parses and generates

**Acceptance Test:**
```bash
# Parse SpecQL YAML
python -c "
from src.specql_parser import SpecQLParser
entity = SpecQLParser().parse(open('entities/contact.yaml').read())
print(f'Parsed entity: {entity.name}')
print(f'Actions: {len(entity.actions)}')
print(f'Fields: {len(entity.fields)}')
"

# Generate SQL
python generate_specql_sql.py --entity contact

# Verify SQL syntax
psql -d test_db --dry-run < generated/03_functions/.../fn_create_contact.sql
```

---

## PHASE 2: Table + View Generation with Trinity Pattern (Week 3-4)

**Objective**: Generate PostgreSQL tables and views from SpecQL entities
**Duration**: 50 hours

### Iteration 2.1: Trinity Pattern Table Generator
### Iteration 2.2: Group Leader Trigger Integration
### Iteration 2.3: FraiseQL View Generation
### Iteration 2.4: Type Resolution System

(Detailed implementation similar to Phase 1 structure)

---

## PHASE 3: Numbering System + Manifest (Week 5-6)

**Objective**: Integrate materialized numbering and execution order
**Duration**: 40 hours

(Implementation details as per original plan, adapted for SpecQL)

---

## PHASE 4: AI Agent Runtime (Week 7-8)

**Objective**: Implement AI agent sandbox and execution
**Duration**: 60 hours

### Agent Capabilities
- [ ] Event observation and triggering
- [ ] Controlled action execution
- [ ] LLM integration (OpenAI, Anthropic)
- [ ] Audit trail for all agent actions
- [ ] Safety constraints and quotas

---

## PHASE 5: Production Polish (Week 9-10)

**Objective**: Migration tools, documentation, testing
**Duration**: 80 hours

### Deliverables
- [ ] Migration tool (existing SQL → SpecQL YAML)
- [ ] Health check system
- [ ] Auto-generated test suites
- [ ] API documentation
- [ ] Team training materials

---

## Success Metrics

### Overall Success Criteria
- [ ] Parse SpecQL YAML (40-60 lines) → Generate 2000+ lines SQL
- [ ] 75-80% reduction in YAML verbosity vs previous approach
- [ ] FraiseQL auto-discovers types and mutations
- [ ] AI agents can observe and execute actions
- [ ] Full backend generated in < 10 minutes from YAML

---

## Estimated Timeline

| Phase | Duration | Hours | Deliverable |
|-------|----------|-------|-------------|
| **Phase 1** | Week 1-2 | 50h | SpecQL Parser + SQL Generator |
| **Phase 2** | Week 3-4 | 50h | Trinity Tables + Views |
| **Phase 3** | Week 5-6 | 40h | Numbering + Manifest |
| **Phase 4** | Week 7-8 | 60h | AI Agent Runtime |
| **Phase 5** | Week 9-10 | 80h | Production Polish |
| **Total** | 10 weeks | 280h | Full SpecQL Platform |

---

**Ready to begin Phase 1?** 🚀

This plan implements the **SpecQL vision** of business-focused YAML with framework-generated infrastructure.
