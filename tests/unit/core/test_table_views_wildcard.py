"""
Tests for wildcard field selection in table_views

Tests the parsing of fields: ["*"] for automatic field inclusion,
which eliminates the need to maintain explicit field lists when
entity structures change.

Related to Issue #5: Projection view composition pattern
"""

import pytest
from src.core.specql_parser import SpecQLParser


class TestWildcardFieldSelection:
    """Test parsing of wildcard field selection (fields: ["*"])"""

    def test_parse_wildcard_field_selection(self):
        """Test parsing fields: ["*"] for all-field inclusion"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)

        table_views:
          include_relations:
            - User:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        assert ast.table_views is not None
        assert len(ast.table_views.include_relations) == 1

        user_include = ast.table_views.include_relations[0]
        assert user_include.entity_name == "User"
        assert user_include.fields == ["*"]

    def test_wildcard_vs_explicit_mixed(self):
        """Test mixing wildcard and explicit field selections"""
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

        assert len(ast.table_views.include_relations) == 2

        org_include = ast.table_views.include_relations[0]
        currency_include = ast.table_views.include_relations[1]

        assert org_include.entity_name == "Organization"
        assert org_include.fields == ["*"]

        assert currency_include.entity_name == "Currency"
        assert currency_include.fields == ["iso_code", "symbol"]

    def test_wildcard_with_nested_composition(self):
        """Test wildcard at multiple nesting levels"""
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

        book_include = ast.table_views.include_relations[0]
        assert book_include.entity_name == "Book"
        assert book_include.fields == ["*"]

        assert len(book_include.include_relations) == 1
        publisher_include = book_include.include_relations[0]
        assert publisher_include.entity_name == "Publisher"
        assert publisher_include.fields == ["*"]

    def test_all_wildcards_multiple_entities(self):
        """Test all-wildcard strategy across multiple entities"""
        yaml_content = """
        entity: Invoice
        schema: tenant
        fields:
          contract: ref(Contract)
          customer: ref(Organization)
          currency: ref(Currency)

        table_views:
          include_relations:
            - Contract:
                fields: ["*"]
            - Organization:
                fields: ["*"]
            - Currency:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        assert len(ast.table_views.include_relations) == 3

        for include in ast.table_views.include_relations:
            assert include.fields == ["*"]

    def test_wildcard_single_element_list(self):
        """Test that wildcard is parsed as single-element list"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)

        table_views:
          include_relations:
            - User:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        user_include = ast.table_views.include_relations[0]
        assert isinstance(user_include.fields, list)
        assert len(user_include.fields) == 1
        assert user_include.fields[0] == "*"

    def test_explicit_fields_not_wildcard(self):
        """Test that explicit field lists are not confused with wildcards"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)

        table_views:
          include_relations:
            - User:
                fields: [name, email, avatar]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        user_include = ast.table_views.include_relations[0]
        assert user_include.fields == ["name", "email", "avatar"]
        assert "*" not in user_include.fields


class TestWildcardWithOtherFeatures:
    """Test wildcard interaction with other table_views features"""

    def test_wildcard_with_extra_filter_columns(self):
        """Test wildcard includes work with extra_filter_columns"""
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
             - status:
                 type: TEXT
                 index: btree
         """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        assert len(ast.table_views.include_relations) == 1
        assert ast.table_views.include_relations[0].fields == ["*"]

        assert len(ast.table_views.extra_filter_columns) == 1
        assert ast.table_views.extra_filter_columns[0].name == "status"

    def test_wildcard_with_mode_force(self):
        """Test wildcard with mode: force"""
        yaml_content = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)

        table_views:
          mode: force
          include_relations:
            - Organization:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        from src.core.ast_models import TableViewMode

        assert ast.table_views.mode == TableViewMode.FORCE
        assert ast.table_views.include_relations[0].fields == ["*"]

    def test_deep_nesting_all_wildcards(self):
        """Test deeply nested wildcards (3+ levels)"""
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
                      include_relations:
                        - Country:
                            fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        # Level 1: Book
        book = ast.table_views.include_relations[0]
        assert book.fields == ["*"]

        # Level 2: Publisher
        assert len(book.include_relations) == 1
        publisher = book.include_relations[0]
        assert publisher.fields == ["*"]

        # Level 3: Country
        assert len(publisher.include_relations) == 1
        country = publisher.include_relations[0]
        assert country.fields == ["*"]


class TestWildcardEdgeCases:
    """Test edge cases and error conditions for wildcard parsing"""

    def test_empty_fields_list_not_wildcard(self):
        """Test that empty fields list is different from wildcard"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)

        table_views:
          include_relations:
            - User:
                fields: []
        """
        parser = SpecQLParser()

        # Empty fields should be invalid
        # This test documents that empty fields raise ValueError
        with pytest.raises(
            ValueError, match="include_relations.User must specify fields"
        ):
            parser.parse(yaml_content)

    def test_wildcard_case_sensitive(self):
        """Test that wildcard is case-sensitive (must be asterisk)"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)

        table_views:
          include_relations:
            - User:
                fields: ["*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        user_include = ast.table_views.include_relations[0]
        # Wildcard must be exactly "*", not "all" or other aliases
        assert user_include.fields[0] == "*"

    def test_multiple_wildcards_in_list_treated_as_single(self):
        """Test that ["*", "*"] is parsed but treated as wildcard"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)

        table_views:
          include_relations:
            - User:
                fields: ["*", "*"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        user_include = ast.table_views.include_relations[0]
        # Documents that duplicate wildcards are parsed as-is
        assert user_include.fields == ["*", "*"]

    def test_wildcard_mixed_with_explicit_in_same_list(self):
        """Test wildcard mixed with explicit fields in same list"""
        yaml_content = """
        entity: Review
        schema: library
        fields:
          author: ref(User)

        table_views:
          include_relations:
            - User:
                fields: ["*", "name", "email"]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        user_include = ast.table_views.include_relations[0]
        # Documents current parsing behavior (may be invalid at generation)
        assert user_include.fields == ["*", "name", "email"]
        assert "*" in user_include.fields


class TestWildcardProductionPattern:
    """Test wildcard patterns specific to Production use case (Issue #5)"""

    def test_production_contract_pattern(self):
        """Test Production's exact pattern from Issue #5"""
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

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
            - Currency:
                fields: [iso_code, symbol, name]
        """
        parser = SpecQLParser()
        ast = parser.parse(yaml_content)

        # Verify wildcard for Organization
        org_include = ast.table_views.include_relations[0]
        assert org_include.entity_name == "Organization"
        assert org_include.fields == ["*"]

        # Verify explicit for Currency
        currency_include = ast.table_views.include_relations[1]
        assert currency_include.entity_name == "Currency"
        assert currency_include.fields == ["iso_code", "symbol", "name"]

    def test_47_entities_wildcard_pattern(self):
        """Test that wildcard reduces maintenance for 47+ entities"""
        # Simulate multiple entities all using wildcard for Organization
        entities_yaml = []
        for i in range(5):  # Represent 5 of the 47 entities
            entities_yaml.append(f"""
        entity: Entity{i}
        schema: tenant
        fields:
          org: ref(Organization)

        table_views:
          include_relations:
            - Organization:
                fields: ["*"]
            """)

        parser = SpecQLParser()

        # All entities parse successfully with wildcard
        for yaml_content in entities_yaml:
            ast = parser.parse(yaml_content)
            assert ast.table_views.include_relations[0].fields == ["*"]

    def test_wildcard_eliminates_field_list_maintenance(self):
        """Test that wildcard pattern requires zero field list updates"""
        # Original pattern (explicit) - requires maintenance
        explicit_yaml = """
        entity: Contract
        schema: tenant
        fields:
          customer: ref(Organization)

        table_views:
          include_relations:
            - Organization:
                fields: [id, name, code, identifier]
        """

        # New pattern (wildcard) - zero maintenance
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

        # Both parse successfully
        explicit_ast = parser.parse(explicit_yaml)
        wildcard_ast = parser.parse(wildcard_yaml)

        # Explicit has specific fields
        assert len(explicit_ast.table_views.include_relations[0].fields) == 4

        # Wildcard has single "*" element
        assert len(wildcard_ast.table_views.include_relations[0].fields) == 1
        assert wildcard_ast.table_views.include_relations[0].fields[0] == "*"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
