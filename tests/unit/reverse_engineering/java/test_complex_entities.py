"""
Tests for complex Java JPA entity reverse engineering

These tests target capabilities that currently have low confidence
and need enhancement to reach 85%+ confidence.
"""

from reverse_engineering.java_action_parser import JavaActionParser


class TestComplexJavaEntities:
    """Test complex Java JPA entity parsing capabilities"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = JavaActionParser()

    def test_jpa_inheritance_parsing(self):
        """Test parsing JPA inheritance strategies"""
        # Test SINGLE_TABLE inheritance
        single_table_code = """
        import javax.persistence.*;

        @Entity
        @Inheritance(strategy=InheritanceType.SINGLE_TABLE)
        @DiscriminatorColumn(name="contact_type", discriminatorType=DiscriminatorType.STRING)
        public class Contact {
            @Id
            private Long id;
            private String name;
        }

        @Entity
        @DiscriminatorValue("LEAD")
        public class Lead extends Contact {
            private String leadSource;
        }
        """

        # Parse base entity
        base_entity = self.parser.parse_entity_from_code(single_table_code)
        assert base_entity.name == "Contact"
        assert base_entity.metadata is not None
        assert base_entity.metadata["jpa_inheritance"]["strategy"] == "SINGLE_TABLE"
        assert base_entity.metadata["jpa_inheritance"]["discriminator_column"] == "contact_type"

        # Should have discriminator field added
        discriminator_field = next(f for f in base_entity.fields if f["name"] == "contact_type")
        assert discriminator_field["type"] == "enum"
        assert "LEAD" in discriminator_field["values"]

        # Test JOINED inheritance
        joined_code = """
        import javax.persistence.*;

        @Entity
        @Inheritance(strategy=InheritanceType.JOINED)
        public class Contact {
            @Id
            private Long id;
            private String name;
        }

        @Entity
        @Table(name="tb_lead")
        public class Lead extends Contact {
            private String leadSource;
        }
        """

        joined_entity = self.parser.parse_entity_from_code(joined_code)
        assert joined_entity.metadata["jpa_inheritance"]["strategy"] == "JOINED"

        # Test TABLE_PER_CLASS inheritance
        table_per_class_code = """
        import javax.persistence.*;

        @Entity
        @Inheritance(strategy=InheritanceType.TABLE_PER_CLASS)
        public class Contact {
            @Id
            private Long id;
            private String name;
        }
        """

        table_entity = self.parser.parse_entity_from_code(table_per_class_code)
        assert table_entity.metadata["jpa_inheritance"]["strategy"] == "TABLE_PER_CLASS"

    def test_embedded_entities_parsing(self):
        """Test parsing @Embedded entities"""
        code = """
        import javax.persistence.*;

        @Embeddable
        public class Address {
            private String street;
            private String city;
            private String zipCode;
        }

        @Entity
        public class Contact {
            @Id
            private Long id;

            private String name;

            @Embedded
            private Address address;
        }
        """

        entity = self.parser.parse_entity_from_code(code)

        # Should have flattened embedded fields
        address_fields = [f for f in entity.fields if f["name"].startswith("address_")]
        assert len(address_fields) == 3

        # Check field names and types
        street_field = next(f for f in address_fields if f["name"] == "address_street")
        assert street_field["type"] == "text"
        assert street_field["embedded_from"] == "Address"

        city_field = next(f for f in address_fields if f["name"] == "address_city")
        assert city_field["type"] == "text"

        zip_field = next(f for f in address_fields if f["name"] == "address_zip_code")
        assert zip_field["type"] == "text"

    def test_bidirectional_relationships_parsing(self):
        """Test parsing bidirectional JPA relationships"""
        code = """
        import javax.persistence.*;

        @Entity
        public class Company {
            @Id
            private Long id;

            @OneToMany(mappedBy="company")
            private List<Contact> contacts;  // Inverse side
        }

        @Entity
        public class Contact {
            @Id
            private Long id;

            @ManyToOne
            @JoinColumn(name="company_id")
            private Company company;  // Owning side
        }
        """

        # Parse Company entity
        company_entity = self.parser.parse_entity_from_code(
            code.replace("@Entity\npublic class Contact", "@Entity\npublic class Company")
        )
        contacts_field = next(f for f in company_entity.fields if f["name"] == "contacts")
        assert contacts_field["relationship_metadata"]["is_bidirectional"]
        assert contacts_field["relationship_metadata"]["side"] == "inverse"
        assert contacts_field["relationship_metadata"]["owned_by"] == "company"

        # Parse Contact entity
        contact_entity = self.parser.parse_entity_from_code(
            code.replace("@Entity\npublic class Company", "@Entity\npublic class Contact")
        )
        company_field = next(f for f in contact_entity.fields if f["name"] == "company")
        assert company_field["relationship_metadata"]["is_bidirectional"]
        assert company_field["relationship_metadata"]["side"] == "owning"
        assert company_field["relationship_metadata"]["foreign_key"] == "company_id"

    def test_custom_types_and_converters(self):
        """Test parsing custom types with @Convert"""
        code = """
        import javax.persistence.*;

        @Converter
        public class StatusConverter implements AttributeConverter<Status, String> {
            // Conversion logic
        }

        @Entity
        public class Contact {
            @Id
            private Long id;

            @Convert(converter=StatusConverter.class)
            private Status status;
        }
        """

        entity = self.parser.parse_entity_from_code(code)

        # Should detect custom converter
        status_field = next(f for f in entity.fields if f["name"] == "status")
        assert status_field["type"] == "text"  # Custom types map to text
        # Note: The converter detection happens in field processing, but we may need to enhance this

    def test_composite_primary_keys(self):
        """Test parsing composite primary keys with @IdClass and @EmbeddedId"""
        # Test @IdClass
        id_class_code = """
        import javax.persistence.*;

        @IdClass(ContactId.class)
        @Entity
        public class Contact {
            @Id
            private String email;

            @Id
            private Long companyId;

            private String name;
        }

        public class ContactId implements Serializable {
            private String email;
            private Long companyId;
        }
        """

        entity = self.parser.parse_entity_from_code(id_class_code)

        # Should have multiple primary key components
        email_pk_field = next(
            f for f in entity.fields if f["name"] == "email" and f.get("is_primary_key_component")
        )
        assert email_pk_field["is_primary_key_component"]
        assert email_pk_field["composite_key"] == "ContactId"

        company_id_pk_field = next(
            f
            for f in entity.fields
            if f["name"] == "company_id" and f.get("is_primary_key_component")
        )
        assert company_id_pk_field["is_primary_key_component"]
        assert company_id_pk_field["composite_key"] == "ContactId"

        # Test @EmbeddedId
        embedded_id_code = """
        import javax.persistence.*;

        @Entity
        public class Contact {
            @EmbeddedId
            private ContactId id;

            private String name;
        }

        @Embeddable
        public class ContactId implements Serializable {
            private String email;
            private Long companyId;
        }
        """

        entity2 = self.parser.parse_entity_from_code(embedded_id_code)

        # Should have embedded ID field
        id_field = next(f for f in entity2.fields if f["name"] == "id")
        assert id_field["type"] == "composite"
        assert id_field["composite_key"] == "ContactId"
