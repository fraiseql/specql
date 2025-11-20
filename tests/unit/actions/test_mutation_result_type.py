"""
Test mutation_result type generation
"""

from generators.actions.action_compiler import ActionCompiler


def test_generates_mutation_result_type_schema():
    """Verify mutation_result composite type is generated"""
    compiler = ActionCompiler()
    result = compiler.generate_base_types()

    assert "CREATE TYPE app.mutation_result AS (" in result
    assert "status TEXT" in result
    assert "message TEXT" in result
    assert "object_data JSONB" in result
    assert "updated_fields TEXT[]" in result
    assert "extra_metadata JSONB" in result


def test_generates_impact_metadata_types():
    """Verify mutation_metadata composite types are generated"""
    compiler = ActionCompiler()
    result = compiler.generate_metadata_types()

    assert "CREATE SCHEMA IF NOT EXISTS mutation_metadata" in result
    assert "CREATE TYPE mutation_metadata.entity_impact AS (" in result
    assert "entity_type TEXT" in result
    assert "operation TEXT" in result
    assert "modified_fields TEXT[]" in result
    assert "CREATE TYPE mutation_metadata.mutation_impact_metadata AS (" in result
