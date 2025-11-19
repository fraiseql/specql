"""
Unit tests for Java entity parser - JPA entities
"""

import pytest

from src.reverse_engineering.java_action_parser import JavaActionParser


class TestJPAEntityParser:
    """Test JPA entity field extraction"""

    @pytest.fixture
    def parser(self):
        return JavaActionParser()

    def test_simple_entity_fields(self, parser):
        """Test extracting fields from simple JPA entity"""
        java_code = """
package com.example.model;

import javax.persistence.*;

@Entity
@Table(name = "tb_contact")
public class Contact {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "email", nullable = false)
    private String email;

    @Column(name = "name")
    private String name;

    private Integer age;
}
"""
        # EXPECTED TO FAIL: Field extraction not implemented
        fields = parser.extract_entity_fields_from_code(java_code)

        assert len(fields) >= 3  # email, name, age (id is auto)
        assert any(f["name"] == "email" for f in fields)
        assert any(f["name"] == "name" for f in fields)
        assert any(f["name"] == "age" for f in fields)

    def test_field_types(self, parser):
        """Test Java type to SpecQL type mapping"""
        java_code = """
@Entity
public class Contact {
    private String email;        // -> text
    private Integer age;         // -> integer
    private Long companyId;      // -> integer
    private Boolean active;      // -> boolean
    private LocalDateTime createdAt;  // -> timestamp
}
"""
        fields = parser.extract_entity_fields_from_code(java_code)

        # EXPECTED TO FAIL
        email_field = next(f for f in fields if f["name"] == "email")
        assert email_field["type"] == "text"

        age_field = next(f for f in fields if f["name"] == "age")
        assert age_field["type"] == "integer"

    def test_relationship_annotations(self, parser):
        """Test detecting relationships (@ManyToOne, @OneToMany)"""
        java_code = """
@Entity
public class Contact {
    @ManyToOne
    @JoinColumn(name = "company_id")
    private Company company;

    @OneToMany(mappedBy = "contact")
    private List<Order> orders;
}
"""
        fields = parser.extract_entity_fields_from_code(java_code)

        # Both relationships should be detected and parsed
        company_field = next(f for f in fields if f["name"] == "company")
        assert company_field["type"] == "ref(Company)"
        assert company_field["is_foreign_key"]

        orders_field = next(f for f in fields if f["name"] == "orders")
        assert orders_field["type"] == "ref(Order)"
        assert orders_field["is_list"]
        assert orders_field["relationship_metadata"]["mapped_by"] == "contact"

    def test_column_nullable_detection(self, parser):
        """Test detecting nullable fields"""
        java_code = """
@Entity
public class Contact {
    @Column(nullable = false)
    private String email;

    @Column(nullable = true)
    private String phone;
}
"""
        fields = parser.extract_entity_fields_from_code(java_code)

        # EXPECTED TO FAIL
        email_field = next(f for f in fields if f["name"] == "email")
        assert email_field["nullable"] is False

        phone_field = next(f for f in fields if f["name"] == "phone")
        assert phone_field["nullable"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
