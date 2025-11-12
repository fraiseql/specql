"""
Integration tests for pattern-based action compilation.
"""

import pytest

from src.core.specql_parser import SpecQLParser


class TestPatternCompilation:
    """Test pattern-based actions compile to SQL"""

    def test_state_machine_pattern_parsing(self):
        """Test that state machine pattern is parsed correctly"""
        yaml_content = """
entity: Machine
schema: tenant

fields:
  status: text
  decommission_date: date
  decommission_reason: text

actions:
  - name: decommission_machine
    pattern: state_machine/transition
    config:
      from_states: [active, maintenance]
      to_state: decommissioned
      input_fields:
        - name: decommission_date
          type: date
        - name: decommission_reason
          type: text
      validation_checks:
        - name: no_active_allocations
          condition: "NOT EXISTS (SELECT 1 FROM allocation WHERE machine_id = $entity_id)"
          error: "Cannot decommission machine with active allocations"
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.name == "Machine"
        assert len(entity.actions) == 1

        action = entity.actions[0]
        assert action.name == "decommission_machine"
        assert action.pattern == "state_machine/transition"
        assert action.pattern_config is not None
        assert action.pattern_config["from_states"] == ["active", "maintenance"]
        assert action.pattern_config["to_state"] == "decommissioned"
        assert len(action.steps) > 0  # Pattern should expand to steps

    def test_multi_entity_pattern_parsing(self):
        """Test that multi-entity pattern is parsed correctly"""
        yaml_content = """
entity: Allocation
schema: tenant

actions:
  - name: allocate_to_stock
    pattern: multi_entity/coordinated_update
    config:
      primary_entity: Machine
      operations:
        - action: get_or_create
          entity: Location
          where:
            code: 'STOCK'
          create_if_missing:
            code: STOCK
            name: Stock
          store_as: stock_location_id
        - action: insert
          entity: Allocation
          values:
            machine_id: $input_data.machine_id
            location_id: $stock_location_id
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.name == "Allocation"
        assert len(entity.actions) == 1

        action = entity.actions[0]
        assert action.name == "allocate_to_stock"
        assert action.pattern == "multi_entity/coordinated_update"
        assert len(action.steps) > 0

    def test_batch_pattern_parsing(self):
        """Test that batch operation pattern is parsed correctly"""
        yaml_content = """
entity: ContractItem
schema: tenant

actions:
  - name: bulk_update_prices
    pattern: batch/bulk_operation
    config:
      batch_input: price_updates
      operation:
        action: update
        entity: ContractItem
        set:
          unit_price: $item.unit_price
        where:
          id: $item.id
      error_handling: continue_on_error
      return_summary:
        processed_count: v_processed_count
        failed_count: v_failed_count
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.name == "ContractItem"
        assert len(entity.actions) == 1

        action = entity.actions[0]
        assert action.name == "bulk_update_prices"
        assert action.pattern == "batch/bulk_operation"
        assert len(action.steps) > 0

    def test_guarded_transition_pattern_parsing(self):
        """Test that guarded transition pattern is parsed correctly"""
        yaml_content = """
entity: Contract
schema: tenant

actions:
  - name: approve_contract
    pattern: state_machine/guarded_transition
    config:
      from_states: [draft, pending_review]
      to_state: approved
      guards:
        - name: budget_available
          condition: "input_data.total_value <= 100000"
          error: "Contract value exceeds budget"
      input_fields:
        - name: approved_by
          type: uuid
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.name == "Contract"
        assert len(entity.actions) == 1

        action = entity.actions[0]
        assert action.name == "approve_contract"
        assert action.pattern == "state_machine/guarded_transition"
        assert len(action.steps) > 0

    def test_parent_child_cascade_pattern_parsing(self):
        """Test that parent-child cascade pattern is parsed correctly"""
        yaml_content = """
entity: Department
schema: tenant

actions:
  - name: delete_department
    pattern: multi_entity/parent_child_cascade
    config:
      parent_entity: Department
      child_entities:
        - entity: Employee
          foreign_key: department_id
      cascade_type: soft_delete
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.name == "Department"
        assert len(entity.actions) == 1

        action = entity.actions[0]
        assert action.name == "delete_department"
        assert action.pattern == "multi_entity/parent_child_cascade"
        assert len(action.steps) > 0

    def test_validation_chain_pattern_parsing(self):
        """Test that validation chain pattern is parsed correctly"""
        yaml_content = """
entity: Contract
schema: tenant

actions:
  - name: validate_contract
    pattern: validation/validation_chain
    config:
      validations:
        - name: amount_positive
          condition: "input_data.total_value > 0"
          message: "Contract value must be positive"
      collect_all_errors: true
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.name == "Contract"
        assert len(entity.actions) == 1

        action = entity.actions[0]
        assert action.name == "validate_contract"
        assert action.pattern == "validation/validation_chain"
        assert len(action.steps) > 0

    def test_traditional_action_still_works(self):
        """Test that traditional step-based actions still work"""
        yaml_content = """
entity: Contact
schema: tenant

fields:
  name: text

actions:
  - name: create_contact
    steps:
      - insert: Contact
      - refresh_table_view: contact_projection
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.name == "Contact"
        assert len(entity.actions) == 1

        action = entity.actions[0]
        assert action.name == "create_contact"
        assert action.pattern is None  # Traditional action
        assert len(action.steps) == 2

    def test_pattern_with_invalid_config_fails(self):
        """Test that invalid pattern config raises error"""
        yaml_content = """
entity: Machine
schema: tenant

actions:
  - name: invalid_transition
    pattern: state_machine/transition
    config:
      # Missing required 'from_states' parameter
      to_state: active
"""

        parser = SpecQLParser()
        with pytest.raises(ValueError) as exc_info:
            parser.parse(yaml_content)

        assert "Invalid pattern configuration" in str(exc_info.value)

    def test_nonexistent_pattern_fails(self):
        """Test that referencing nonexistent pattern fails"""
        yaml_content = """
entity: Test
schema: tenant

actions:
  - name: test_action
    pattern: nonexistent/pattern
    config: {}
"""

        parser = SpecQLParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(yaml_content)
