"""Tests for exception handling action"""

from src.core.specql_parser import SpecQLParser


def test_exception_handling_basic():
    """Test basic try/catch exception handling"""
    yaml_content = """
    entity: Transaction
    actions:
      - name: process_payment
        steps:
          - exception_handling:
              try:
                - call_service:
                    service: payment_gateway
                    operation: charge
                    input: {amount: $amount, card: $card_token}
                - update: Transaction SET status = 'completed'
              catch:
                - when: 'payment_failed'
                  then:
                    - update: Transaction SET status = 'failed'
                    - reject: "Payment processing failed"
                - when: 'network_error'
                  then:
                    - update: Transaction SET status = 'retry'
                    - call_function:
                        function: schedule_retry
              finally:
                - call_function:
                    function: cleanup_resources
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "exception_handling"
    assert len(action.steps[0].try_steps) == 2
    assert len(action.steps[0].catch_handlers) == 2
    assert len(action.steps[0].finally_steps) == 1


def test_exception_handling_multiple_catches():
    """Test multiple exception handlers"""
    yaml_content = """
    entity: FileProcessor
    actions:
      - name: import_data
        steps:
          - exception_handling:
              try:
                - call_function:
                    function: parse_file
                - call_function:
                    function: validate_data
                - call_function:
                    function: save_records
              catch:
                    - when: 'parse_error'
                      then:
                        - call_function:
                            function: log_error
                        - reject: invalid_format
                    - when: 'validation_error'
                      then:
                        - call_function:
                            function: log_error
                        - reject: invalid_data
                    - when: 'database_error'
                      then:
                        - call_function:
                            function: log_error
                        - call_function:
                            function: rollback_transaction
                    - when: 'OTHERS'
                      then:
                        - call_function:
                            function: log_error
                        - reject: system_error
    """
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)
    action = entity_def.actions[0]

    assert action.steps[0].type == "exception_handling"
    assert len(action.steps[0].try_steps) == 3
    assert len(action.steps[0].catch_handlers) == 4
    assert action.steps[0].catch_handlers[3].when_condition == "OTHERS"
