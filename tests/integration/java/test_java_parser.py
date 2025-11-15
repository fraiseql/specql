"""Integration tests for Java parser with real Spring Boot entities"""

import pytest
import tempfile
import os
from pathlib import Path

from src.reverse_engineering.java.java_parser import (
    JavaParser,
    JavaParseConfig,
)


class TestJavaParserIntegration:
    """Integration tests for Java parser with real Spring Boot entities"""

    @pytest.fixture
    def parser(self):
        return JavaParser()

    @pytest.fixture
    def temp_java_file(self):
        """Create a temporary Java file for testing"""
        java_content = """
package com.example.crm.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "contacts")
public class Contact {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 255)
    private String email;

    @Column(name = "full_name")
    private String name;

    @Column(nullable = false)
    private Boolean active = true;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "company_id")
    private Company company;

    @OneToMany(mappedBy = "contact", cascade = CascadeType.ALL)
    private List<Task> tasks;

    @Enumerated(EnumType.STRING)
    private ContactStatus status;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Getters and setters omitted for brevity
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        os.unlink(temp_path)

    @pytest.fixture
    def temp_spring_boot_project(self):
        """Create a temporary directory with Spring Boot entities"""
        temp_dir = tempfile.mkdtemp()

        # Create package structure
        package_dir = (
            Path(temp_dir)
            / "src"
            / "main"
            / "java"
            / "com"
            / "example"
            / "crm"
            / "model"
        )
        package_dir.mkdir(parents=True)

        # Contact entity
        contact_java = """
package com.example.crm.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "contacts")
public class Contact {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String email;

    private String name;

    @ManyToOne
    @JoinColumn(name = "company_id")
    private Company company;

    @OneToMany(mappedBy = "contact")
    private List<Task> tasks;

    @Enumerated(EnumType.STRING)
    private ContactStatus status;
}
"""
        (package_dir / "Contact.java").write_text(contact_java)

        # Company entity
        company_java = """
package com.example.crm.model;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "companies")
public class Company {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    private String website;

    @OneToMany(mappedBy = "company")
    private List<Contact> contacts;
}
"""
        (package_dir / "Company.java").write_text(company_java)

        # Task entity
        task_java = """
package com.example.crm.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "tasks")
public class Task {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    private String description;

    @ManyToOne
    @JoinColumn(name = "contact_id")
    private Contact contact;

    @Column(name = "due_date")
    private LocalDateTime dueDate;
}
"""
        (package_dir / "Task.java").write_text(task_java)

        yield temp_dir

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)

    def test_parse_single_java_file(self, parser, temp_java_file):
        """Test parsing a single Java file with JPA entities"""
        result = parser.parse_file(temp_java_file)

        assert result.file_path == temp_java_file
        assert len(result.errors) == 0
        assert len(result.entities) == 1

        entity = result.entities[0]
        assert entity.name == "Contact"
        assert entity.table == "contacts"
        assert entity.schema == "public"

        # Check fields (excluding id)
        assert (
            len(entity.fields) == 8
        )  # email, name, active, company, tasks, status, createdAt, updatedAt

        # Check specific fields
        email_field = entity.fields["email"]
        assert email_field.type_name == "text"
        assert not email_field.nullable

        company_field = entity.fields["company"]
        assert company_field.type_name == "ref(Company)"

        tasks_field = entity.fields["tasks"]
        assert tasks_field.type_name == "list(Task)"

        status_field = entity.fields["status"]
        assert status_field.type_name == "text"  # Enum

    def test_parse_spring_boot_project(self, parser, temp_spring_boot_project):
        """Test parsing a complete Spring Boot project structure"""
        config = JavaParseConfig(recursive=True)
        results = parser.parse_directory(temp_spring_boot_project, config)

        # Should find 3 Java files
        assert len(results) == 3

        # All should parse successfully
        for result in results:
            assert len(result.errors) == 0
            assert len(result.entities) == 1

        # Extract entities
        entities = {}
        for result in results:
            for entity in result.entities:
                entities[entity.name] = entity

        # Verify all entities were found
        assert "Contact" in entities
        assert "Company" in entities
        assert "Task" in entities

        # Verify relationships
        contact = entities["Contact"]
        company_field = contact.fields["company"]
        assert company_field.type_name == "ref(Company)"

        tasks_field = contact.fields["tasks"]
        assert tasks_field.type_name == "list(Task)"

        company = entities["Company"]
        contacts_field = company.fields["contacts"]
        assert contacts_field.type_name == "list(Contact)"

    def test_parse_package_method(self, parser, temp_spring_boot_project):
        """Test the parse_package convenience method"""
        entities_by_file = parser.parse_package(temp_spring_boot_project)

        # Should return entities grouped by file
        assert len(entities_by_file) == 3

        # Each file should have exactly one entity
        for file_path, entities in entities_by_file.items():
            assert len(entities) == 1
            assert file_path.endswith(".java")

    def test_validation_metrics(self, parser, temp_java_file):
        """Test validation of parse results"""
        result = parser.parse_file(temp_java_file)
        metrics = parser.validate_parse_result(result)

        assert metrics["file_path"] == temp_java_file
        assert metrics["entity_count"] == 1
        assert metrics["error_count"] == 0
        assert metrics["confidence"] > 0.5  # Should have decent confidence

    def test_error_handling(self, parser):
        """Test error handling for invalid files"""
        # Non-existent file
        result = parser.parse_file("/non/existent/file.java")
        assert len(result.entities) == 0
        assert len(result.errors) == 1
        assert "File not found" in result.errors[0]

    def test_config_patterns(self, parser, temp_spring_boot_project):
        """Test include/exclude patterns in config"""
        # Test with test exclusion (should exclude nothing in this case)
        config = JavaParseConfig(
            include_patterns=["*.java"], exclude_patterns=["**/test/**"]
        )

        results = parser.parse_directory(temp_spring_boot_project, config)
        assert len(results) == 3  # All files included

    def test_empty_directory(self, parser, tmp_path):
        """Test parsing empty directory"""
        results = parser.parse_directory(str(tmp_path))
        assert len(results) == 0

    def test_non_recursive_parsing(self, parser, temp_spring_boot_project):
        """Test non-recursive directory parsing"""
        config = JavaParseConfig(recursive=False)

        # Parse just the root directory (should find nothing)
        results = parser.parse_directory(temp_spring_boot_project, config)
        assert len(results) == 0

        # Parse the actual package directory
        package_dir = os.path.join(
            temp_spring_boot_project,
            "src",
            "main",
            "java",
            "com",
            "example",
            "crm",
            "model",
        )
        results = parser.parse_directory(package_dir, config)
        assert len(results) == 3
