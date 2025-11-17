"""
Tests for simple Java JPA entity reverse engineering

These tests ensure basic functionality continues to work
while we enhance complex case handling.
"""

import pytest
from src.reverse_engineering.java_action_parser import JavaActionParser


class TestSimpleJavaEntities:
    """Test simple Java JPA entity parsing (should maintain 80%+ confidence)"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = JavaActionParser()

    def test_basic_jpa_entity(self):
        """Test basic JPA entity parsing"""
        code = """
        @Entity
        public class Contact {
            @Id
            private Long id;

            private String name;
            private String email;
            private Integer age;
        }
        """

        entity = self.parser.parse_entity_from_code(code)

        # Should extract basic fields (id is skipped)
        assert len(entity.fields) == 3

        # Check field types
        name_field = next(f for f in entity.fields if f["name"] == "name")
        assert name_field["type"] == "text"
        assert name_field["nullable"] == True

        email_field = next(f for f in entity.fields if f["name"] == "email")
        assert email_field["type"] == "text"

        age_field = next(f for f in entity.fields if f["name"] == "age")
        assert age_field["type"] == "integer"

    def test_entity_with_relationships(self):
        """Test entity with basic relationships"""
        code = """
        @Entity
        public class Contact {
            @Id
            private Long id;

            private String email;

            @ManyToOne
            @JoinColumn(name="company_id")
            private Company company;
        }
        """

        entity = self.parser.parse_entity_from_code(code)

        # Should have both simple and relationship fields (id is skipped)
        assert len(entity.fields) == 2  # email, company

        company_field = next(f for f in entity.fields if f["name"] == "company")
        assert "ref(Company)" in company_field["type"]
        assert company_field["is_foreign_key"] == True
