"""Tests for Hibernate type mapper"""

import pytest
from src.reverse_engineering.java.hibernate_type_mapper import HibernateTypeMapper
from src.reverse_engineering.java.jpa_visitor import JPAField


class TestHibernateTypeMapper:
    """Test Hibernate type mapping"""

    @pytest.fixture
    def type_mapper(self):
        return HibernateTypeMapper()

    def test_primitive_type_mapping(self, type_mapper):
        """Test mapping of Java primitives"""
        jpa_field = JPAField(name="count", java_type="int")
        result = type_mapper.map_type("int", jpa_field)
        assert result == "integer"

        jpa_field = JPAField(name="flag", java_type="boolean")
        result = type_mapper.map_type("boolean", jpa_field)
        assert result == "boolean"

    def test_wrapper_type_mapping(self, type_mapper):
        """Test mapping of Java wrapper types"""
        jpa_field = JPAField(name="count", java_type="Integer")
        result = type_mapper.map_type("Integer", jpa_field)
        assert result == "integer"

        jpa_field = JPAField(name="flag", java_type="Boolean")
        result = type_mapper.map_type("Boolean", jpa_field)
        assert result == "boolean"

    def test_string_type_mapping(self, type_mapper):
        """Test mapping of String types"""
        jpa_field = JPAField(name="name", java_type="String")
        result = type_mapper.map_type("String", jpa_field)
        assert result == "text"

    def test_date_time_mapping(self, type_mapper):
        """Test mapping of date/time types"""
        jpa_field = JPAField(name="created", java_type="LocalDateTime")
        result = type_mapper.map_type("LocalDateTime", jpa_field)
        assert result == "timestamp"

        jpa_field = JPAField(name="birth_date", java_type="LocalDate")
        result = type_mapper.map_type("LocalDate", jpa_field)
        assert result == "date"

    def test_relationship_mapping(self, type_mapper):
        """Test mapping of JPA relationships"""
        jpa_field = JPAField(
            name="company",
            java_type="Company",
            is_relationship=True,
            relationship_type="ManyToOne",
            target_entity="Company",
        )
        result = type_mapper.map_type("Company", jpa_field)
        assert result == "ref(Company)"

        jpa_field = JPAField(
            name="employees",
            java_type="List<Employee>",
            is_relationship=True,
            relationship_type="OneToMany",
            target_entity="Employee",
        )
        result = type_mapper.map_type("List<Employee>", jpa_field)
        assert result == "list(Employee)"

    def test_enum_mapping(self, type_mapper):
        """Test mapping of enum fields"""
        jpa_field = JPAField(
            name="status", java_type="ContactStatus", is_enum=True, enum_type="STRING"
        )
        result = type_mapper.map_type("ContactStatus", jpa_field)
        assert result == "text"

    def test_collection_mapping(self, type_mapper):
        """Test mapping of collections"""
        jpa_field = JPAField(name="tags", java_type="List<String>")
        result = type_mapper.map_type("List<String>", jpa_field)
        assert result == "list(String)"

        jpa_field = JPAField(name="categories", java_type="Set<Category>")
        result = type_mapper.map_type("Set<Category>", jpa_field)
        assert result == "list(Category)"

    def test_unknown_type_mapping(self, type_mapper):
        """Test mapping of unknown types defaults to text"""
        jpa_field = JPAField(name="custom", java_type="CustomType")
        result = type_mapper.map_type("CustomType", jpa_field)
        assert result == "text"
