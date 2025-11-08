"""Tests for app schema foundation generation (Team B)"""

import pytest
from src.generators.app_schema_generator import AppSchemaGenerator


class TestAppSchemaGenerator:
    """Test app schema foundation generation"""

    @pytest.fixture
    def generator(self):
        """Create app schema generator"""
        return AppSchemaGenerator()

    def test_mutation_result_comment_yaml_format(self, generator):
        """Mutation result should use YAML format with description"""
        sql = generator._generate_mutation_result_type()

        # Should have human-readable description
        assert "'Standard mutation result" in sql

        # Should have YAML metadata after blank line
        assert "@fraiseql:composite" in sql
        assert "name: MutationResult" in sql
        assert "tier: 1" in sql
        assert "storage: composite" in sql

        # Full format check
        expected_comment = """COMMENT ON TYPE app.mutation_result IS
'Standard mutation result for all operations.
Returns entity data, status, and optional metadata.

@fraiseql:composite
name: MutationResult
tier: 1
storage: composite';"""
        assert expected_comment in sql

    def test_mutation_result_field_comments_yaml_format(self, generator):
        """Field comments should use YAML format"""
        sql = generator._generate_mutation_result_type()

        # Check id field comment
        expected_id_comment = """COMMENT ON COLUMN app.mutation_result.id IS
'Unique identifier of the affected entity.

@fraiseql:field
name: id
type: UUID!
required: true';"""
        assert expected_id_comment in sql

        # Check status field comment
        expected_status_comment = """COMMENT ON COLUMN app.mutation_result.status IS
'Operation status indicator.
Values: success, failed:error_code

@fraiseql:field
name: status
type: String!
required: true';"""
        assert expected_status_comment in sql
