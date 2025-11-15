"""Tests for JPA annotation visitor"""

import pytest
from src.reverse_engineering.java.jdt_bridge import get_jdt_bridge
from src.reverse_engineering.java.jpa_visitor import JPAAnnotationVisitor


class TestJPAAnnotationVisitor:
    """Test JPA annotation extraction"""

    @pytest.fixture
    def jdt_bridge(self):
        return get_jdt_bridge()

    def test_simple_entity_extraction(self, jdt_bridge):
        """Test extracting a simple JPA entity"""
        java_code = """
import jakarta.persistence.*;

@Entity
@Table(name = "contacts")
public class Contact {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String email;

    private String name;
}
"""

        # Parse Java code
        cu = jdt_bridge.parse_java(java_code)

        # Extract entities
        visitor = JPAAnnotationVisitor(cu)
        entities = visitor.visit()

        # Assertions
        assert len(entities) == 1
        entity = entities[0]

        assert entity.class_name == "Contact"
        assert entity.table_name == "contacts"  # From @Table(name = "contacts")
        assert entity.id_field == "id"
        assert len(entity.fields) == 3

        # Check email field
        email_field = next(f for f in entity.fields if f.name == "email")
        assert not email_field.nullable
        assert email_field.java_type == "String"

    def test_relationship_extraction(self, jdt_bridge):
        """Test extracting JPA relationships"""
        java_code = """
import jakarta.persistence.*;

@Entity
public class Contact {
    @Id
    private Long id;

    @ManyToOne
    @JoinColumn(name = "company_id")
    private Company company;
}
"""

        cu = jdt_bridge.parse_java(java_code)
        visitor = JPAAnnotationVisitor(cu)
        entities = visitor.visit()

        assert len(entities) == 1
        entity = entities[0]

        company_field = next(f for f in entity.fields if f.name == "company")
        assert company_field.is_relationship  is True
        assert company_field.relationship_type == "ManyToOne"
        assert company_field.target_entity == "Company"
        assert company_field.join_column == "company_id"

    def test_enum_field_extraction(self, jdt_bridge):
        """Test extracting enum fields"""
        java_code = """
import jakarta.persistence.*;

@Entity
public class Contact {
    @Id
    private Long id;

    @Enumerated(EnumType.STRING)
    private ContactStatus status;
}
"""

        cu = jdt_bridge.parse_java(java_code)
        visitor = JPAAnnotationVisitor(cu)
        entities = visitor.visit()

        assert len(entities) == 1
        entity = entities[0]

        status_field = next(f for f in entity.fields if f.name == "status")
        assert status_field.is_enum  is True
        assert status_field.enum_type == "STRING"

    def test_one_to_many_relationship(self, jdt_bridge):
        """Test extracting OneToMany relationships"""
        java_code = """
import jakarta.persistence.*;
import java.util.List;

@Entity
public class Company {
    @Id
    private Long id;

    @OneToMany(mappedBy = "company")
    private List<Contact> contacts;
}
"""

        cu = jdt_bridge.parse_java(java_code)
        visitor = JPAAnnotationVisitor(cu)
        entities = visitor.visit()

        assert len(entities) == 1
        entity = entities[0]

        contacts_field = next(f for f in entity.fields if f.name == "contacts")
        assert contacts_field.is_relationship  is True
        assert contacts_field.relationship_type == "OneToMany"
        assert contacts_field.target_entity == "Contact"

    def test_column_annotations(self, jdt_bridge):
        """Test extracting @Column annotations"""
        java_code = """
import jakarta.persistence.*;

@Entity
public class Product {
    @Id
    private Long id;

    @Column(name = "product_name", nullable = false, unique = true, length = 100)
    private String name;

    @Column(precision = 10, scale = 2)
    private BigDecimal price;
}
"""

        cu = jdt_bridge.parse_java(java_code)
        visitor = JPAAnnotationVisitor(cu)
        entities = visitor.visit()

        assert len(entities) == 1
        entity = entities[0]

        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.column_name == "product_name"
        assert not name_field.nullable
        assert name_field.unique  is True
        assert name_field.length == 100

    def test_no_entity_class(self, jdt_bridge):
        """Test that non-entity classes are ignored"""
        java_code = """
public class Helper {
    private String value;
}
"""

        cu = jdt_bridge.parse_java(java_code)
        visitor = JPAAnnotationVisitor(cu)
        entities = visitor.visit()

        assert len(entities) == 0
