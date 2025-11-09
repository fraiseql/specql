"""
Unit tests for SpecQL Parser (Team A)
Tests SpecQL YAML parsing into Entity AST
"""

import pytest

from src.core.specql_parser import ParseError, SpecQLParser


class TestSpecQLParser:
    """Test SpecQL YAML parsing functionality"""

    def setup_method(self):
        """Setup parser instance for each test"""
        self.parser = SpecQLParser()

    def test_parse_simple_entity(self):
        """Test parsing basic entity with minimal fields"""
        yaml_content = """
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: text
  first_name: text
  last_name: text
"""

        entity = self.parser.parse(yaml_content)

        assert entity.name == "Contact"
        assert entity.schema == "crm"
        assert entity.description == "Customer contact information"
        assert len(entity.fields) == 3
        assert "email" in entity.fields
        assert entity.fields["email"].type_name == "text"
        assert entity.fields["first_name"].type_name == "text"
        assert entity.fields["last_name"].type_name == "text"

    def test_parse_enum_field(self):
        """Test parsing enum field type"""
        yaml_content = """
entity: Contact
fields:
  status: enum(lead, qualified, customer)
  priority: enum(low, medium, high)
"""

        entity = self.parser.parse(yaml_content)

        assert entity.fields["status"].type_name == "enum"
        assert entity.fields["status"].values == ["lead", "qualified", "customer"]
        assert entity.fields["priority"].type_name == "enum"
        assert entity.fields["priority"].values == ["low", "medium", "high"]

    def test_parse_ref_field(self):
        """Test parsing reference field type"""
        yaml_content = """
entity: Contact
fields:
  company: ref(Company)
  owner: ref(User)
"""

        entity = self.parser.parse(yaml_content)

        assert entity.fields["company"].type_name == "ref"
        assert entity.fields["company"].reference_entity == "Company"
        assert entity.fields["owner"].type_name == "ref"
        assert entity.fields["owner"].reference_entity == "User"

    def test_parse_list_field(self):
        """Test parsing list field type"""
        yaml_content = """
entity: Contact
fields:
  tags: list(text)
  skills: list(ref(Skill))
"""

        entity = self.parser.parse(yaml_content)

        assert entity.fields["tags"].type_name == "list"
        assert entity.fields["tags"].item_type == "text"
        assert entity.fields["skills"].type_name == "list"
        assert entity.fields["skills"].item_type == "ref(Skill)"

    def test_parse_field_with_default(self):
        """Test parsing field with default value"""
        yaml_content = """
entity: Contact
fields:
  status: enum(active, inactive) = active
  score: integer = 0
"""

        entity = self.parser.parse(yaml_content)

        assert entity.fields["status"].default == "active"
        assert entity.fields["score"].default == "0"

    def test_parse_action_with_validate_step(self):
        """Test parsing action with validate step"""
        yaml_content = """
entity: Contact
fields:
  email: text
  score: integer

actions:
  - name: create_contact
    steps:
      - validate: email MATCHES email_pattern
        error: "invalid_email"
      - validate: score >= 0 AND score <= 100
        error: "invalid_score"
"""

        entity = self.parser.parse(yaml_content)

        assert len(entity.actions) == 1
        action = entity.actions[0]
        assert action.name == "create_contact"
        assert len(action.steps) == 2

        # First step
        step1 = action.steps[0]
        assert step1.type == "validate"
        assert step1.expression == "email MATCHES email_pattern"
        assert step1.error == "invalid_email"

        # Second step
        step2 = action.steps[1]
        assert step2.type == "validate"
        assert step2.expression == "score >= 0 AND score <= 100"
        assert step2.error == "invalid_score"

    def test_parse_if_then_else_action(self):
        """Test parsing if/then/else conditional action"""
        yaml_content = """
entity: Contact
fields:
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    steps:
      - if: status = 'lead'
        then:
          - update: Contact SET status = 'qualified'
        else:
          - reject: "contact_not_lead"
"""

        entity = self.parser.parse(yaml_content)

        action = entity.actions[0]
        assert len(action.steps) == 1

        step = action.steps[0]
        assert step.type == "if"
        assert step.condition == "status = 'lead'"
        assert len(step.then_steps) == 1
        assert len(step.else_steps) == 1

        # Then step
        then_step = step.then_steps[0]
        assert then_step.type == "update"
        assert then_step.entity == "Contact"
        assert then_step.fields["raw_set"] == "status = 'qualified'"

        # Else step
        else_step = step.else_steps[0]
        assert else_step.type == "reject"
        assert else_step.error == "contact_not_lead"

    def test_parse_insert_action(self):
        """Test parsing insert action step"""
        yaml_content = """
entity: Contact
actions:
  - name: create_contact
    steps:
      - insert: Contact
"""

        entity = self.parser.parse(yaml_content)

        step = entity.actions[0].steps[0]
        assert step.type == "insert"
        assert step.entity == "Contact"
        assert step.fields is None  # All fields from input

    def test_parse_update_action(self):
        """Test parsing update action step"""
        yaml_content = """
entity: Contact
actions:
  - name: update_status
    steps:
      - update: Contact SET status = 'qualified' WHERE pk_contact = input.contact_id
"""

        entity = self.parser.parse(yaml_content)

        step = entity.actions[0].steps[0]
        assert step.type == "update"
        assert step.entity == "Contact"
        assert step.fields["raw_set"] == "status = 'qualified'"
        assert step.where_clause == "pk_contact = input.contact_id"

    def test_parse_find_action(self):
        """Test parsing find action step"""
        yaml_content = """
entity: Contact
actions:
  - name: find_contact
    steps:
      - find: Contact WHERE email = input.email
"""

        entity = self.parser.parse(yaml_content)

        step = entity.actions[0].steps[0]
        assert step.type == "find"
        assert step.entity == "Contact"
        assert step.where_clause == "email = input.email"

    def test_parse_call_action(self):
        """Test parsing function call action step"""
        yaml_content = """
entity: Contact
actions:
  - name: create_and_notify
    steps:
      - call: send_notification(email = input.email, message = 'Welcome!')
      - call: log_event(type = 'contact_created', data = input)
        store: event_id
"""

        entity = self.parser.parse(yaml_content)

        steps = entity.actions[0].steps
        assert len(steps) == 2

        # First call
        step1 = steps[0]
        assert step1.type == "call"
        assert step1.function_name == "send_notification"
        assert step1.arguments == {"email": "input.email", "message": "'Welcome!'"}

        # Second call with store
        step2 = steps[1]
        assert step2.type == "call"
        assert step2.function_name == "log_event"
        assert step2.arguments == {"type": "'contact_created'", "data": "input"}
        assert step2.store_result == "event_id"

    def test_parse_agent_definition(self):
        """Test parsing AI agent definition"""
        yaml_content = """
entity: Contact
agents:
  - name: lead_scoring_agent
    type: ai_llm
    observes: ['contact.created', 'activity.logged']
    can_execute: ['update_lead_score', 'qualify_lead']
    strategy: |
      Score leads based on company size and engagement
    audit: required
"""

        entity = self.parser.parse(yaml_content)

        assert len(entity.agents) == 1
        agent = entity.agents[0]
        assert agent.name == "lead_scoring_agent"
        assert agent.type == "ai_llm"
        assert "contact.created" in agent.observes
        assert "activity.logged" in agent.observes
        assert "update_lead_score" in agent.can_execute
        assert "qualify_lead" in agent.can_execute
        assert "company size" in agent.strategy
        assert agent.audit == "required"

    def test_parse_with_organization(self):
        """Test parsing entity with numbering system organization"""
        yaml_content = """
entity: Manufacturer
schema: catalog
organization:
  table_code: "013211"
  domain_name: "catalog"

fields:
  code: text
"""

        entity = self.parser.parse(yaml_content)

        assert entity.organization is not None
        assert entity.organization.table_code == "013211"
        assert entity.organization.domain_name == "catalog"

    def test_validate_field_references(self):
        """Test validation of field references in expressions"""
        yaml_content = """
entity: Contact
fields:
  email: text
  score: integer

actions:
  - name: validate_contact
    steps:
      - validate: email IS NOT NULL
      - validate: score >= 0
"""

        # Should parse successfully
        entity = self.parser.parse(yaml_content)
        assert len(entity.actions[0].steps) == 2

    def test_validate_invalid_field_reference(self):
        """Test validation fails for invalid field references"""
        yaml_content = """
entity: Contact
fields:
  email: text

actions:
  - name: validate_contact
    steps:
      - validate: invalid_field > 10
"""

        with pytest.raises(
            ParseError, match="Field 'invalid_field' referenced in expression not found"
        ):
            self.parser.parse(yaml_content)

    def test_parse_minimal_entity(self):
        """Test parsing entity with just name and one field"""
        yaml_content = """
entity: User
fields:
  username: text
"""

        entity = self.parser.parse(yaml_content)

        assert entity.name == "User"
        assert entity.schema == "public"  # default
        assert len(entity.fields) == 1
        assert entity.fields["username"].type_name == "text"

    def test_parse_error_invalid_yaml(self):
        """Test error handling for invalid YAML"""
        yaml_content = """
entity: Contact
  fields:
    - invalid: format
"""

        with pytest.raises(ParseError, match="Invalid YAML"):
            self.parser.parse(yaml_content)

    def test_parse_error_missing_entity(self):
        """Test error handling for missing entity key"""
        yaml_content = """
fields:
  name: text
"""

        with pytest.raises(ParseError, match="Missing 'entity' key"):
            self.parser.parse(yaml_content)

    def test_validate_enum_literal_in_expression(self):
        """Test validation allows enum literals in expressions"""
        yaml_content = """
entity: Contact
fields:
  status: enum(lead, qualified, customer)
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
"""

        entity = self.parser.parse(yaml_content)

        assert len(entity.actions) == 1
        action = entity.actions[0]
        assert action.name == "qualify_lead"
        assert len(action.steps) == 1

        step = action.steps[0]
        assert step.type == "validate"
        assert step.expression == "status = 'lead'"
        assert step.error == "not_a_lead"

    def test_parse_notify_action(self):
        """Test parsing notify action step"""
        yaml_content = """
entity: Contact
actions:
  - name: notify_owner
    steps:
      - notify: owner(email, "Contact qualified")
"""

        entity = self.parser.parse(yaml_content)

        assert len(entity.actions) == 1
        action = entity.actions[0]
        assert action.name == "notify_owner"
        assert len(action.steps) == 1

        step = action.steps[0]
        assert step.type == "notify"
        assert step.function_name == "owner"
        assert step.arguments == {"channel": "email", "message": "Contact qualified"}

    def test_parse_refresh_table_view_action(self):
        """Test parsing refresh_table_view action step"""
        from src.core.ast_models import RefreshScope

        yaml_content = """
entity: Review
schema: library

fields:
  rating: integer!
  comment: text
  author: ref(User)
  book: ref(Book)

actions:
  - name: update_rating
    steps:
      - validate: rating >= 1 AND rating <= 5
      - update: Review SET rating = 5
      - refresh_table_view:
          scope: self
          propagate: [author]
"""

        entity = self.parser.parse(yaml_content)

        assert len(entity.actions) == 1
        action = entity.actions[0]
        assert action.name == "update_rating"
        assert len(action.steps) == 3

        # Check the refresh step
        refresh_step = action.steps[2]
        assert refresh_step.type == "refresh_table_view"
        assert refresh_step.refresh_scope == RefreshScope.SELF
        assert refresh_step.propagate_entities == ["author"]
        assert refresh_step.refresh_strategy == "immediate"
