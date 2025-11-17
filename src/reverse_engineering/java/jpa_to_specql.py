"""
JPA to SpecQL Converter

Converts JPA entities to SpecQL entity specifications.
"""

from src.reverse_engineering.java.jpa_visitor import JPAEntity
from src.reverse_engineering.java.hibernate_type_mapper import HibernateTypeMapper
from src.core.ast_models import Entity, FieldDefinition, FieldTier


class JPAToSpecQLConverter:
    """Convert JPA entities to SpecQL"""

    def __init__(self):
        self.type_mapper = HibernateTypeMapper()

    def convert(self, jpa_entity: JPAEntity) -> Entity:
        """
        Convert JPA entity to SpecQL Entity

        Args:
            jpa_entity: Parsed JPA entity

        Returns:
            SpecQL Entity
        """
        # Convert fields
        fields = {}
        for jpa_field in jpa_entity.fields:
            # Skip ID field (Trinity pattern handles this)
            if jpa_field.name == jpa_entity.id_field:
                continue

            # Map type
            field_type = self.type_mapper.map_type(jpa_field.java_type, jpa_field)

            # Create FieldDefinition
            field_def = FieldDefinition(
                name=jpa_field.name,
                type_name=field_type,  # field_type is already a string
                nullable=jpa_field.nullable,
            )

            # Set additional properties based on type
            if jpa_field.is_relationship and jpa_field.relationship_type == "ManyToOne":
                field_def.reference_entity = jpa_field.target_entity
                field_def.tier = FieldTier.REFERENCE
            elif jpa_field.is_enum:
                field_def.tier = FieldTier.BASIC  # Enums are basic for now
            elif (
                jpa_field.is_relationship and jpa_field.relationship_type == "OneToMany"
            ):
                field_def.item_type = jpa_field.target_entity
                field_def.tier = FieldTier.COMPOSITE  # Lists are composite

            fields[jpa_field.name] = field_def

        # Create Entity
        entity = Entity(
            name=jpa_entity.class_name,
            schema=jpa_entity.schema or "public",
            table=jpa_entity.table_name,
            fields=fields,
        )

        return entity
