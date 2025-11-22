# tests/unit/cli/commands/reverse/test_java.py
"""Tests for reverse java CLI command."""

import sys
from pathlib import Path

# Add src to path for new CLI structure
project_root = Path(__file__).parent.parent.parent.parent.parent  # /home/lionel/code/specql
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def sample_jpa_entity():
    return """
package com.example.model;

import javax.persistence.*;

@Entity
@Table(name = "contacts")
public class Contact {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "email", nullable = false)
    private String email;

    @Column(name = "name")
    private String name;

    @ManyToOne
    @JoinColumn(name = "company_id")
    private Company company;

    @Column(name = "status")
    private String status;

    // Getters and setters omitted
}
"""


@pytest.fixture
def sample_hibernate_entity():
    return """
package com.example.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "tb_task", schema = "projects")
public class Task {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "title", nullable = false, length = 255)
    private String title;

    @Column(name = "description")
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(name = "status")
    private TaskStatus status;

    @Column(name = "due_date")
    private LocalDateTime dueDate;

    @ManyToOne
    @JoinColumn(name = "assignee_id")
    private User assignee;

    @OneToMany(mappedBy = "task")
    private List<Comment> comments;
}
"""


@pytest.fixture
def sample_spring_data_entity():
    return """
package com.example.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import javax.persistence.*;

@Entity
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String orderNumber;

    @ManyToOne
    @JoinColumn(name = "customer_id", nullable = false)
    private Customer customer;

    @Column(nullable = false)
    private BigDecimal totalAmount;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}
"""


# ============================================================================
# Basic CLI argument tests
# ============================================================================


def test_reverse_java_requires_files():
    """reverse java should require file arguments."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "java"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Error" in result.output


def test_reverse_java_requires_output_dir(cli_runner):
    """reverse java should require output directory."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text("public class Contact {}")
        result = cli_runner.invoke(app, ["reverse", "java", "Contact.java"])

        assert result.exit_code != 0


def test_reverse_java_file_not_found(cli_runner):
    """reverse java should error on missing file."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("out").mkdir()
        result = cli_runner.invoke(app, ["reverse", "java", "nonexistent.java", "-o", "out/"])

        assert result.exit_code != 0


# ============================================================================
# JPA entity parsing tests
# ============================================================================


def test_reverse_java_parses_jpa_entity(cli_runner, sample_jpa_entity):
    """reverse java should parse JPA entities."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text(sample_jpa_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "Contact.java", "-o", "out/"])

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        # Check YAML content
        yaml_content = yaml_files[0].read_text()
        assert "Contact" in yaml_content or "contact" in yaml_content


def test_reverse_java_extracts_jpa_fields(cli_runner, sample_jpa_entity):
    """reverse java should extract fields from JPA entities."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text(sample_jpa_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "Contact.java", "-o", "out/"])

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        yaml_content = yaml_files[0].read_text()
        assert "email" in yaml_content


def test_reverse_java_parses_hibernate_entity(cli_runner, sample_hibernate_entity):
    """reverse java should parse Hibernate entities (jakarta.persistence)."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Task.java").write_text(sample_hibernate_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "Task.java", "-o", "out/"])

        assert result.exit_code == 0


def test_reverse_java_detects_relationships(cli_runner, sample_jpa_entity):
    """reverse java should detect @ManyToOne relationships."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text(sample_jpa_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "Contact.java", "-o", "out/"])

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        yaml_content = yaml_files[0].read_text()
        # Company is a ManyToOne relation - should be a reference
        assert "company" in yaml_content or "ref(" in yaml_content


# ============================================================================
# Preview mode tests
# ============================================================================


def test_reverse_java_preview_mode(cli_runner, sample_jpa_entity):
    """reverse java --preview should not write files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text(sample_jpa_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "java", "Contact.java", "-o", "out/", "--preview"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) == 0


def test_reverse_java_preview_shows_entities(cli_runner, sample_jpa_entity):
    """reverse java --preview should show what would be generated."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text(sample_jpa_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "java", "Contact.java", "-o", "out/", "--preview"]
        )

        assert result.exit_code == 0
        # Should mention the entity name in preview
        assert "contact" in result.output.lower() or "Contact" in result.output


# ============================================================================
# Multiple files tests
# ============================================================================


def test_reverse_java_multiple_files(cli_runner, sample_jpa_entity, sample_hibernate_entity):
    """reverse java should handle multiple files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text(sample_jpa_entity)
        Path("Task.java").write_text(sample_hibernate_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "java", "Contact.java", "Task.java", "-o", "out/"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        # Should generate YAML for entities from both files
        assert len(yaml_files) >= 1


# ============================================================================
# Edge case tests
# ============================================================================


def test_reverse_java_handles_empty_file(cli_runner):
    """reverse java should handle empty Java files gracefully."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Empty.java").write_text("")
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "Empty.java", "-o", "out/"])

        # Should not crash
        assert result.exit_code == 0


def test_reverse_java_handles_non_entity_class(cli_runner):
    """reverse java should handle files with no JPA entities."""
    from cli.main import app

    non_entity_code = """
package com.example.util;

public class StringUtils {
    public static String trim(String s) {
        return s != null ? s.trim() : null;
    }
}
"""

    with cli_runner.isolated_filesystem():
        Path("StringUtils.java").write_text(non_entity_code)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "StringUtils.java", "-o", "out/"])

        # Should not crash, just find 0 entities
        assert result.exit_code == 0


def test_reverse_java_handles_interface(cli_runner):
    """reverse java should handle interface files (e.g., Spring Data repositories)."""
    from cli.main import app

    repository_code = """
package com.example.repository;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ContactRepository extends JpaRepository<Contact, Long> {
    Contact findByEmail(String email);
}
"""

    with cli_runner.isolated_filesystem():
        Path("ContactRepository.java").write_text(repository_code)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "ContactRepository.java", "-o", "out/"])

        # Should not crash
        assert result.exit_code == 0


# ============================================================================
# YAML output format tests
# ============================================================================


def test_reverse_java_yaml_has_metadata(cli_runner, sample_jpa_entity):
    """Generated YAML should include source metadata."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text(sample_jpa_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "Contact.java", "-o", "out/"])

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        yaml_content = yaml_files[0].read_text()
        # Should have metadata about source language
        assert "java" in yaml_content.lower() or "_metadata" in yaml_content


def test_reverse_java_yaml_has_entity_name(cli_runner, sample_jpa_entity):
    """Generated YAML should have entity name."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text(sample_jpa_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "Contact.java", "-o", "out/"])

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        yaml_content = yaml_files[0].read_text()
        assert "entity:" in yaml_content


def test_reverse_java_yaml_has_schema(cli_runner, sample_hibernate_entity):
    """Generated YAML should extract schema from @Table annotation."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Task.java").write_text(sample_hibernate_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(app, ["reverse", "java", "Task.java", "-o", "out/"])

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        yaml_content = yaml_files[0].read_text()
        # Schema from @Table annotation should be preserved
        assert "schema:" in yaml_content


# ============================================================================
# ORM option tests
# ============================================================================


def test_reverse_java_orm_option(cli_runner, sample_jpa_entity):
    """reverse java --orm should specify ORM type."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("Contact.java").write_text(sample_jpa_entity)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "java", "Contact.java", "-o", "out/", "--orm", "hibernate"]
        )

        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
