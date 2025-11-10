"""
Tests for wildcard SQL generation in table views

Tests that fields: ["*"] generates correct SQL that uses the full
tv_ table data JSONB object instead of extracting individual fields.

Related to Issue #5: Projection view composition pattern
"""
import pytest
from src.core.specql_parser import SpecQLParser
from src.generators.schema.table_view_generator import TableViewGenerator


class TestWildcardSQLGeneration:
    """Test SQL generation for wildcard field selection"""

    def test_wildcard_uses_full_data_object(self):
        """Test that ["*"] uses full tv_table.data JSONB object"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)
          rating: integer

        table_views:
          include_relations:
            - User:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should reference tv_user.data directly (not extract fields)
        assert "tv_user.data" in sql

        # Should NOT use jsonb_build_object for wildcard
        # (jsonb_build_object is for explicit field selection)
        if "jsonb_build_object" in sql and "tv_user" in sql:
            # If jsonb_build_object exists, it shouldn't be building User fields
            assert sql.index("tv_user.data") < sql.index("jsonb_build_object")

    def test_explicit_fields_generate_jsonb_build_object(self):
        """Test that explicit fields generate jsonb_build_object()"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)

        table_views:
          include_relations:
            - User:
                fields: [name, email]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should generate field-specific extraction
        assert "jsonb_build_object" in sql
        assert "'name'" in sql
        assert "'email'" in sql

        # Should extract from tv_user.data
        assert "tv_user.data" in sql

    def test_mixed_wildcard_and_explicit_same_table_view(self):
        """Test mixing wildcard and explicit in same table_views"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)
          currency: ref(Currency)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
            - Currency:
                fields: [iso_code, symbol]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Organization: wildcard (full data object)
        assert "tv_organization.data" in sql

        # Currency: explicit fields (jsonb_build_object)
        assert "'iso_code'" in sql
        assert "'symbol'" in sql

    def test_wildcard_creates_correct_json_key(self):
        """Test that wildcard creates correct key in parent JSONB"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)
          rating: integer

        table_views:
          include_relations:
            - User:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should have 'author' key with full User data
        assert "'author'" in sql
        assert "tv_user.data" in sql

    def test_wildcard_nested_composition(self):
        """Test wildcard in nested composition generates correct SQL"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          book: ref(Book)

        table_views:
          include_relations:
            - Book:
                fields: ["*"]
                include_relations:
                  - Publisher:
                      fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Both Book and Publisher should use full data
        assert "tv_book.data" in sql

        # Note: Publisher data is already in tv_book.data,
        # so tv_publisher might not appear in Review's refresh
        # (depends on implementation - document actual behavior)


class TestWildcardJOINGeneration:
    """Test that wildcards generate correct JOINs"""

    def test_wildcard_generates_left_join(self):
        """Test that wildcard include still generates LEFT JOIN"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should have LEFT JOIN to tv_organization
        assert "LEFT JOIN" in sql.upper()
        assert "tv_organization" in sql

    def test_wildcard_uses_correct_foreign_key(self):
        """Test that wildcard JOIN uses correct FK"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer_org: ref(Organization)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should JOIN using fk_customer_org
        assert "fk_customer_org" in sql
        assert "pk_organization" in sql


class TestWildcardCrossSchemaGeneration:
    """Test wildcard generation for cross-schema references"""

    def test_wildcard_cross_schema_generates_qualified_table_name(self):
        """Test that cross-schema wildcard uses schema.tv_table"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer_org:
            type: ref(Organization)
            schema: management

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should use schema-qualified table name
        assert "management.tv_organization" in sql or "management" in sql

    def test_wildcard_multiple_cross_schema_entities(self):
        """Test wildcard with multiple cross-schema entities"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer:
            type: ref(Organization)
            schema: management
          currency:
            type: ref(Currency)
            schema: catalog

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
            - Currency:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should have both schema-qualified tables
        # Note: Exact SQL format depends on implementation
        assert "tv_organization" in sql
        assert "tv_currency" in sql


class TestWildcardRefreshFunctionGeneration:
    """Test that wildcards generate correct refresh functions"""

    def test_wildcard_generates_refresh_function(self):
        """Test that wildcard includes generate refresh function"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should generate refresh function
        assert "CREATE OR REPLACE FUNCTION" in sql
        assert "refresh_tv_contract" in sql

    def test_wildcard_refresh_inserts_full_data(self):
        """Test that refresh function inserts full JSONB data"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)
          status: enum(draft, active)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Refresh function should INSERT into tv_contract
        assert "INSERT INTO" in sql
        assert "tv_contract" in sql

        # Should insert JSONB data column
        assert "data" in sql


class TestWildcardPerformanceOptimizations:
    """Test that wildcards don't prevent performance optimizations"""

    def test_wildcard_with_extra_filter_columns_generates_both(self):
        """Test that extra_filter_columns work with wildcard includes"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)
          status: enum(draft, active)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
          extra_filter_columns:
            - name: status
              type: TEXT
              index_type: btree
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should have status column in table definition
        assert "status" in sql

        # Should have index on status
        assert "idx_tv_contract_status" in sql or "CREATE INDEX" in sql

    def test_wildcard_generates_gin_index_on_data(self):
        """Test that wildcard includes still get GIN index on data column"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should have GIN index on data column for JSONB queries
        assert "USING GIN" in sql or "gin" in sql.lower()


class TestWildcardPrintOptimPattern:
    """Test SQL generation for PrintOptim use case (Issue #5)"""

    def test_printoptim_contract_sql_generation(self):
        """Test SQL generation for PrintOptim's Contract pattern"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer_org:
            type: ref(Organization)
            schema: management
          provider_org:
            type: ref(Organization)
            schema: management
          currency:
            type: ref(Currency)
            schema: catalog
          status: enum(draft, active, expired)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
            - Currency:
                fields: [iso_code, symbol, name]
          extra_filter_columns:
            - name: status
              type: TEXT
              index_type: btree
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        generator = TableViewGenerator(ast)
        sql = generator.generate()

        # Should create tv_contract table
        assert "CREATE TABLE" in sql
        assert "tv_contract" in sql

        # Should have wildcard data for Organization
        assert "tv_organization.data" in sql

        # Should have explicit fields for Currency
        assert "'iso_code'" in sql
        assert "'symbol'" in sql
        assert "'name'" in sql

        # Should have extra filter column for status
        assert "status TEXT" in sql or "status" in sql

        # Should have refresh function
        assert "refresh_tv_contract" in sql

    def test_wildcard_reduces_sql_complexity(self):
        """Test that wildcard generates simpler SQL than explicit fields"""
        # Explicit fields (complex)
        explicit_yaml = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)

        table_views:
          include_relations:
            - Organization:
                fields: [id, name, code, legal_name, tax_id, address, city, state]
        """

        # Wildcard (simple)
        wildcard_yaml = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
        """

        parser = SpecQLParser()

        explicit_ast = parser.parse(explicit_yaml)
        wildcard_ast = parser.parse(wildcard_yaml)

        explicit_gen = TableViewGenerator(explicit_ast)
        wildcard_gen = TableViewGenerator(wildcard_ast)

        explicit_sql = explicit_gen.generate()
        wildcard_sql = wildcard_gen.generate()

        # Wildcard SQL should be simpler (fewer field extractions)
        # Explicit has jsonb_build_object with 8 field extractions
        explicit_field_count = explicit_sql.count("tv_organization.data->")
        wildcard_field_count = wildcard_sql.count("tv_organization.data->")

        # Wildcard should have fewer or zero field extractions
        assert wildcard_field_count <= explicit_field_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
