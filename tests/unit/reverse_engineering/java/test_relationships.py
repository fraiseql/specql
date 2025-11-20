"""
Tests for Java JPA relationship reverse engineering

These tests focus on parsing various JPA relationship types.
"""

from reverse_engineering.java_action_parser import JavaActionParser


class TestJavaRelationships:
    """Test Java JPA relationship parsing"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = JavaActionParser()

    def test_one_to_many_relationship(self):
        """Test @OneToMany relationship parsing"""
        code = """
        import javax.persistence.*;
        import java.util.List;

        @Entity
        public class Company {
            @Id
            private Long id;

            @OneToMany(mappedBy="company", cascade=CascadeType.ALL)
            private List<Contact> contacts;
        }
        """

        # Parse entity
        entity = self.parser.parse_entity_from_code(code)

        # Should extract relationship field
        contacts_field = next(f for f in entity.fields if f["name"] == "contacts")
        assert contacts_field is not None
        assert "ref(Contact)" in contacts_field["type"]
        assert contacts_field["is_list"]
        assert contacts_field["relationship_metadata"]["type"] == "one_to_many"
        assert contacts_field["relationship_metadata"]["mapped_by"] == "company"

    def test_many_to_one_relationship(self):
        """Test @ManyToOne relationship parsing"""
        code = """
        import javax.persistence.*;

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

        # Parse entity
        entity = self.parser.parse_entity_from_code(code)

        # Should have both simple and relationship fields (id is skipped)
        assert len(entity.fields) == 2  # email, company

        company_field = next(f for f in entity.fields if f["name"] == "company")
        assert "ref(Company)" in company_field["type"]
        assert company_field["is_foreign_key"]
        assert company_field["relationship_metadata"]["type"] == "many_to_one"

    def test_one_to_one_relationship(self):
        """Test @OneToOne relationship parsing"""
        code = """
        import javax.persistence.*;

        @Entity
        public class User {
            @Id
            private Long id;

            private String username;

            @OneToOne
            @JoinColumn(name="profile_id")
            private UserProfile profile;
        }
        """

        # Parse entity
        entity = self.parser.parse_entity_from_code(code)

        # Should extract relationship field
        profile_field = next(f for f in entity.fields if f["name"] == "profile")
        assert profile_field is not None
        assert "ref(UserProfile)" in profile_field["type"]
        assert profile_field["is_foreign_key"]
        assert profile_field["relationship_metadata"]["type"] == "one_to_one"

    def test_many_to_many_relationship(self):
        """Test @ManyToMany relationship parsing"""
        code = """
        import javax.persistence.*;
        import java.util.Set;

        @Entity
        public class User {
            @Id
            private Long id;

            private String username;

            @ManyToMany
            @JoinTable(name="user_roles",
                joinColumns=@JoinColumn(name="user_id"),
                inverseJoinColumns=@JoinColumn(name="role_id"))
            private Set<Role> roles;
        }
        """

        # Parse entity
        entity = self.parser.parse_entity_from_code(code)

        # Should extract relationship field
        roles_field = next(f for f in entity.fields if f["name"] == "roles")
        assert roles_field is not None
        assert "ref(Role)" in roles_field["type"]
        assert roles_field["is_list"]
        assert roles_field["is_many_to_many"]
        assert roles_field["relationship_metadata"]["type"] == "many_to_many"
