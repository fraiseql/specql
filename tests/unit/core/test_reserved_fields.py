import pytest

from src.core.exceptions import SpecQLValidationError
from src.core.specql_parser import SpecQLParser


class TestReservedFieldNames:
    """Test that reserved field names are properly rejected."""

    def setup_method(self):
        self.parser = SpecQLParser()

    def test_reserved_exact_match(self):
        """Test exact reserved field names are rejected."""
        reserved_names = [
            "id",
            "path",
            "identifier",
            "sequence_number",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

        for field_name in reserved_names:
            yaml_content = f"""
            entity: TestEntity
            fields:
              {field_name}: text
            """

            with pytest.raises(SpecQLValidationError) as exc_info:
                self.parser.parse(yaml_content)

            assert field_name in str(exc_info.value)
            assert "reserved" in str(exc_info.value).lower()

    def test_reserved_prefix_pk(self):
        """Test pk_* prefix is rejected."""
        yaml_content = """
        entity: Location
        fields:
          pk_custom: integer
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse(yaml_content)

        assert "pk_custom" in str(exc_info.value)
        assert "pk_*" in str(exc_info.value)

    def test_reserved_prefix_fk(self):
        """Test fk_* prefix is rejected."""
        yaml_content = """
        entity: Location
        fields:
          fk_custom: integer
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse(yaml_content)

        assert "fk_custom" in str(exc_info.value)

    def test_tenant_id_reserved(self):
        """Test tenant_id is reserved."""
        yaml_content = """
        entity: Location
        fields:
          tenant_id: text
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse(yaml_content)

        assert "tenant_id" in str(exc_info.value)

    def test_non_reserved_allowed(self):
        """Test non-reserved field names are allowed."""
        yaml_content = """
        entity: Location
        fields:
          name: text
          description: text
          custom_field: integer
        """

        # Should NOT raise
        result = self.parser.parse(yaml_content)
        assert result is not None
        assert len(result.fields) == 3

    def test_error_message_helpful(self):
        """Test error message is helpful to users."""
        yaml_content = """
        entity: Location
        fields:
          path: text
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse(yaml_content)

        error_msg = str(exc_info.value)

        # Should contain helpful info
        assert "path" in error_msg
        assert "reserved" in error_msg.lower()
        assert "different field name" in error_msg.lower()

        # Should list categories of reserved fields
        assert "Primary/Foreign Keys" in error_msg or "pk_*" in error_msg
        assert "Audit" in error_msg or "created_at" in error_msg
