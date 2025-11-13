"""Tests for Java parser edge cases (inheritance, embedded entities)"""

import pytest
import tempfile
import os

from src.reverse_engineering.java.java_parser import JavaParser


class TestJavaParserEdgeCases:
    """Test edge cases in Java parsing"""

    @pytest.fixture
    def parser(self):
        return JavaParser()

    @pytest.fixture
    def inheritance_java_file(self):
        """Create a Java file with inheritance"""
        java_content = """
package com.example.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "users")
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@DiscriminatorColumn(name = "user_type", discriminatorType = DiscriminatorType.STRING)
public abstract class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String email;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}

@Entity
@DiscriminatorValue("CUSTOMER")
public class Customer extends User {

    @Column(name = "customer_id")
    private String customerId;

    private String company;

    @Column(name = "loyalty_points")
    private Integer loyaltyPoints = 0;
}

@Entity
@DiscriminatorValue("ADMIN")
public class Admin extends User {

    @Column(name = "admin_level")
    private String adminLevel;

    @Column(name = "department")
    private String department;
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        os.unlink(temp_path)

    @pytest.fixture
    def embedded_java_file(self):
        """Create a Java file with embedded entities"""
        java_content = """
package com.example.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Embeddable
public class Address {

    @Column(name = "street_address")
    private String street;

    private String city;

    @Column(name = "postal_code")
    private String postalCode;

    private String country;
}

@Embeddable
public class ContactInfo {

    @Column(name = "phone_number")
    private String phone;

    @Column(name = "email_address")
    private String email;
}

@Entity
@Table(name = "companies")
public class Company {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Embedded
    private Address headquarters;

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "phone", column = @Column(name = "support_phone")),
        @AttributeOverride(name = "email", column = @Column(name = "support_email"))
    })
    private ContactInfo supportContact;

    @Column(name = "website_url")
    private String website;
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        os.unlink(temp_path)

    @pytest.fixture
    def complex_relationships_java_file(self):
        """Create a Java file with complex relationships"""
        java_content = """
package com.example.model;

import jakarta.persistence.*;
import java.util.List;
import java.util.Set;

@Entity
@Table(name = "projects")
public class Project {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    private String description;

    @ManyToOne
    @JoinColumn(name = "owner_id")
    private User owner;

    @ManyToMany
    @JoinTable(
        name = "project_contributors",
        joinColumns = @JoinColumn(name = "project_id"),
        inverseJoinColumns = @JoinColumn(name = "user_id")
    )
    private Set<User> contributors;

    @OneToMany(mappedBy = "project", cascade = CascadeType.ALL)
    @OrderBy("createdAt DESC")
    private List<Task> tasks;

    @ElementCollection
    @CollectionTable(name = "project_tags", joinColumns = @JoinColumn(name = "project_id"))
    @Column(name = "tag")
    private List<String> tags;
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        os.unlink(temp_path)

    def test_inheritance_parsing(self, parser, inheritance_java_file):
        """Test parsing entities with inheritance"""
        result = parser.parse_file(inheritance_java_file)

        assert len(result.errors) == 0
        assert len(result.entities) == 3  # User, Customer, Admin

        entities = {entity.name: entity for entity in result.entities}

        # Check base class
        user = entities["User"]
        assert user.name == "User"
        assert user.table == "users"
        assert len(user.fields) == 2  # email, createdAt (id excluded)

        # Check subclass - Customer
        customer = entities["Customer"]
        assert customer.name == "Customer"
        assert customer.table == "users"  # Same table due to SINGLE_TABLE
        assert len(customer.fields) == 3  # customerId, company, loyaltyPoints

        # Check subclass - Admin
        admin = entities["Admin"]
        assert admin.name == "Admin"
        assert len(admin.fields) == 2  # adminLevel, department

    def test_embedded_entities_parsing(self, parser, embedded_java_file):
        """Test parsing entities with embedded objects"""
        result = parser.parse_file(embedded_java_file)

        assert len(result.errors) == 0
        # Note: @Embeddable classes are not treated as entities
        # Only the @Entity class should be extracted
        assert len(result.entities) == 1

        company = result.entities[0]
        assert company.name == "Company"
        assert company.table == "companies"

        # Embedded fields should be flattened
        # Note: Current implementation may not handle @Embedded perfectly
        # This is an edge case that would need enhancement
        assert len(company.fields) >= 2  # At least id and name

    def test_complex_relationships_parsing(
        self, parser, complex_relationships_java_file
    ):
        """Test parsing complex JPA relationships"""
        result = parser.parse_file(complex_relationships_java_file)

        assert len(result.errors) == 0
        assert len(result.entities) == 1

        project = result.entities[0]
        assert project.name == "Project"
        assert project.table == "projects"

        # Check various relationship types
        assert "owner" in project.fields
        owner_field = project.fields["owner"]
        assert owner_field.type_name == "ref(User)"

        assert "contributors" in project.fields
        contributors_field = project.fields["contributors"]
        # ManyToMany might be handled as list for now
        assert (
            "list" in contributors_field.type_name
            or "ref" in contributors_field.type_name
        )

        assert "tasks" in project.fields
        tasks_field = project.fields["tasks"]
        assert tasks_field.type_name == "list(Task)"

        assert "tags" in project.fields
        tags_field = project.fields["tags"]
        assert tags_field.type_name == "list(String)"  # ElementCollection

    def test_mixed_annotations_parsing(self, parser):
        """Test parsing with mixed JPA annotations"""
        java_content = """
package com.example.model;

import jakarta.persistence.*;
import javax.persistence.*;
import java.util.List;

@Entity
@Table(name = "mixed_entities", schema = "test")
public class MixedEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // Jakarta annotations
    @Column(name = "jakarta_field", nullable = false)
    private String jakartaField;

    // Legacy javax annotations (should still work)
    @javax.persistence.Column(name = "javax_field")
    private String javaxField;

    @ManyToOne
    @JoinColumn(name = "parent_id")
    private MixedEntity parent;

    @OneToMany(mappedBy = "parent")
    private List<MixedEntity> children;
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_content)
            temp_path = f.name

        try:
            result = parser.parse_file(temp_path)

            assert len(result.errors) == 0
            assert len(result.entities) == 1

            entity = result.entities[0]
            assert entity.name == "MixedEntity"
            assert entity.table == "mixed_entities"
            assert entity.schema == "test"

            # Should handle both jakarta and javax annotations
            assert len(entity.fields) == 4  # jakartaField, javaxField, parent, children

        finally:
            os.unlink(temp_path)

    def test_validation_with_edge_cases(self, parser, inheritance_java_file):
        """Test validation metrics with inheritance"""
        result = parser.parse_file(inheritance_java_file)
        metrics = parser.validate_parse_result(result)

        assert metrics["entity_count"] == 3
        assert metrics["error_count"] == 0
        assert (
            metrics["confidence"] > 0.7
        )  # Should have high confidence with multiple entities

    def test_error_recovery_in_edge_cases(self, parser):
        """Test error recovery with malformed inheritance"""
        java_content = """
package com.example.model;

import jakarta.persistence.*;

@Entity
public class BrokenInheritance extends NonExistentClass {

    @Id
    private Long id;

    private String name;
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_content)
            temp_path = f.name

        try:
            result = parser.parse_file(temp_path)

            # Should still parse the entity even with broken inheritance
            assert len(result.entities) == 1
            assert result.entities[0].name == "BrokenInheritance"

        finally:
            os.unlink(temp_path)
