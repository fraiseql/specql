from src.reverse_engineering.python_ast_parser import PythonASTParser
from src.reverse_engineering.python_to_specql_mapper import PythonToSpecQLMapper

class TestPythonToSpecQLMapper:

    def test_map_simple_method(self):
        """Test mapping simple Python method to SpecQL action"""
        source = '''
class Contact:
    status: str

    def qualify_lead(self) -> bool:
        if self.status != "lead":
            return False
        self.status = "qualified"
        return True
'''

        parser = PythonASTParser()
        entity = parser.parse_entity(source)
        method = entity.methods[0]

        mapper = PythonToSpecQLMapper()
        action = mapper.map_method_to_action(method, entity)

        assert action.name == "qualify_lead"
        assert len(action.steps) >= 2

        # Should have validation step
        validate_step = next(s for s in action.steps if s.type == 'validate')
        assert 'status' in validate_step.expression

        # Should have update step
        update_step = next(s for s in action.steps if s.type == 'update')
        assert update_step.entity == "Contact"
        assert 'status' in update_step.fields

    def test_map_assignment_to_update(self):
        """Test mapping self.field = value to UPDATE step"""
        source = '''
class User:
    email: str

    def update_email(self, new_email: str):
        self.email = new_email
'''

        parser = PythonASTParser()
        entity = parser.parse_entity(source)
        method = entity.methods[0]

        mapper = PythonToSpecQLMapper()
        action = mapper.map_method_to_action(method, entity)

        # Should have update step
        update_steps = [s for s in action.steps if s.type == 'update']
        assert len(update_steps) >= 1

    def test_map_function_call(self):
        """Test mapping function call to CALL step"""
        source = '''
class Order:
    def process_order(self):
        send_confirmation_email()
'''

        parser = PythonASTParser()
        entity = parser.parse_entity(source)
        method = entity.methods[0]

        mapper = PythonToSpecQLMapper()
        action = mapper.map_method_to_action(method, entity)

        # Should have call step
        call_steps = [s for s in action.steps if s.type == 'call']
        assert len(call_steps) >= 1