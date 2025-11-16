# tests/unit/adapters/test_adapter_interface.py
import pytest
from src.adapters.base_adapter import (
    FrameworkAdapter,
    GeneratedCode,
    FrameworkConventions,
)
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


def test_framework_adapter_is_abstract():
    """FrameworkAdapter should be an abstract base class"""
    # Should not be able to instantiate directly
    with pytest.raises(TypeError):
        FrameworkAdapter()


def test_adapter_can_generate_entity():
    """Adapter can convert UniversalEntity → framework code"""
    entity = UniversalEntity(
        name="Contact",
        schema="crm",
        fields=[UniversalField(name="email", type=FieldType.TEXT)],
        actions=[],
    )

    # Create a mock adapter for testing
    class MockAdapter(FrameworkAdapter):
        def generate_entity(self, entity):
            return [
                GeneratedCode(
                    file_path=f"{entity.name.lower()}.mock",
                    content=f"mock code for {entity.name}",
                    language="mock",
                )
            ]

        def generate_action(self, action, entity):
            return []

        def generate_relationship(self, field, entity):
            return ""

        def get_conventions(self):
            return FrameworkConventions(
                naming_case="snake_case",
                primary_key_name="pk_{entity}",
                foreign_key_pattern="fk_{entity}",
                timestamp_fields=["created_at", "updated_at"],
                supports_multi_tenancy=True,
            )

        def get_framework_name(self):
            return "mock"

    adapter = MockAdapter()
    result = adapter.generate_entity(entity)

    assert len(result) == 1
    assert result[0].file_path == "contact.mock"
    assert "mock code for Contact" in result[0].content
    assert result[0].language == "mock"


def test_adapter_requires_abstract_methods():
    """All adapters must implement required abstract methods"""

    class IncompleteAdapter(FrameworkAdapter):
        pass

    # Should fail because abstract methods are not implemented
    with pytest.raises(TypeError):
        IncompleteAdapter()


def test_adapter_get_conventions():
    """Adapter provides framework-specific conventions"""

    class TestAdapter(FrameworkAdapter):
        def generate_entity(self, entity):
            return []

        def generate_action(self, action, entity):
            return []

        def generate_relationship(self, field, entity):
            return ""

        def get_conventions(self):
            return FrameworkConventions(
                naming_case="PascalCase",
                primary_key_name="Id",
                foreign_key_pattern="{Entity}Id",
                timestamp_fields=["CreatedAt", "UpdatedAt"],
                supports_multi_tenancy=False,
            )

        def get_framework_name(self):
            return "test"

    adapter = TestAdapter()
    conventions = adapter.get_conventions()

    assert conventions.naming_case == "PascalCase"
    assert conventions.primary_key_name == "Id"
    assert not conventions.supports_multi_tenancy


def test_adapter_get_framework_name():
    """Adapter returns its framework identifier"""

    class TestAdapter(FrameworkAdapter):
        def generate_entity(self, entity):
            return []

        def generate_action(self, action, entity):
            return []

        def generate_relationship(self, field, entity):
            return ""

        def get_conventions(self):
            return FrameworkConventions(
                naming_case="snake_case",
                primary_key_name="id",
                foreign_key_pattern="fk_{entity}",
                timestamp_fields=["created_at", "updated_at"],
                supports_multi_tenancy=True,
            )

        def get_framework_name(self):
            return "test_framework"

    adapter = TestAdapter()
    assert adapter.get_framework_name() == "test_framework"


def test_generated_code_structure():
    """GeneratedCode contains required fields"""
    code = GeneratedCode(
        file_path="models/contact.py",
        content="class Contact:\n    pass",
        language="python",
    )

    assert code.file_path == "models/contact.py"
    assert code.content == "class Contact:\n    pass"
    assert code.language == "python"


def test_framework_conventions_structure():
    """FrameworkConventions contains all required fields"""
    conventions = FrameworkConventions(
        naming_case="camelCase",
        primary_key_name="id",
        foreign_key_pattern="{entity}Id",
        timestamp_fields=["createdAt", "updatedAt"],
        supports_multi_tenancy=True,
    )

    assert conventions.naming_case == "camelCase"
    assert conventions.primary_key_name == "id"
    assert conventions.foreign_key_pattern == "{entity}Id"
    assert conventions.timestamp_fields == ["createdAt", "updatedAt"]
    assert conventions.supports_multi_tenancy is True
