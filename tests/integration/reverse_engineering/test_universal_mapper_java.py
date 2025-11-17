"""
Integration tests for Java with universal mapper
"""

import pytest
from pathlib import Path
from src.reverse_engineering.universal_action_mapper import UniversalActionMapper
import yaml


class TestUniversalMapperJava:
    """Test Java integration with universal mapper"""

    @pytest.fixture
    def mapper(self):
        return UniversalActionMapper()

    def test_java_controller_to_specql(self, mapper, tmp_path):
        """Test converting Spring Boot controller to SpecQL"""
        java_file = tmp_path / "ContactController.java"
        java_file.write_text("""
package com.example.api;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/contacts")
public class ContactController {

    @PostMapping
    public Contact create(@RequestBody ContactRequest req) { }

    @GetMapping("/{id}")
    public Contact get(@PathVariable Long id) { }
}
        """)

        yaml_output = mapper.convert_file(java_file, language="java")

        # Verify YAML structure
        spec = yaml.safe_load(yaml_output)
        assert "entity" in spec
        assert "actions" in spec
        assert len(spec["actions"]) == 2
        assert spec["actions"][0]["name"] == "create"
        assert spec["actions"][1]["name"] == "get"

    def test_jpa_entity_to_specql(self, mapper, tmp_path):
        """Test converting JPA entity to SpecQL fields"""
        java_file = tmp_path / "Contact.java"
        java_file.write_text("""
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
        """)

        yaml_output = mapper.convert_file(java_file, language="java")

        # Verify YAML structure
        spec = yaml.safe_load(yaml_output)
        assert "entity" in spec
        assert "fields" in spec or "actions" in spec  # May have fields or actions

    def test_java_repository_to_specql(self, mapper, tmp_path):
        """Test converting Spring Data repository to SpecQL"""
        java_file = tmp_path / "ContactRepository.java"
        java_file.write_text("""
package com.example.repository;

import org.springframework.data.repository.CrudRepository;

public interface ContactRepository extends CrudRepository<Contact, Long> {
    // Standard CRUD methods inherited
}
        """)

        yaml_output = mapper.convert_file(java_file, language="java")

        # Verify YAML structure
        spec = yaml.safe_load(yaml_output)
        assert "entity" in spec
        assert "actions" in spec
        # Should have CRUD actions
        action_names = [a["name"] for a in spec["actions"]]
        assert "save" in action_names
        assert "findById" in action_names
        assert "findAll" in action_names
        assert "deleteById" in action_names

    def test_java_code_string_conversion(self, mapper):
        """Test converting Java code string directly"""
        java_code = """
@RestController
@RequestMapping("/users")
public class UserController {

    @GetMapping
    public List<User> listUsers() { }

    @PostMapping
    public User createUser(@RequestBody UserRequest req) { }
}
        """

        yaml_output = mapper.convert_code(java_code, language="java")

        # Verify YAML structure
        spec = yaml.safe_load(yaml_output)
        assert "entity" in spec
        assert "actions" in spec
        assert len(spec["actions"]) == 2
