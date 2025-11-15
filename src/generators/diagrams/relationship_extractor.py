from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum

class RelationshipType(Enum):
    """Type of relationship between entities"""
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_ONE = "N:1"
    MANY_TO_MANY = "N:M"
    SELF_REFERENTIAL = "self"

class RelationshipCardinality(Enum):
    """Cardinality notation"""
    ZERO_OR_ONE = "0..1"
    EXACTLY_ONE = "1"
    ZERO_OR_MANY = "0..*"
    ONE_OR_MANY = "1..*"

@dataclass
class Relationship:
    """Represents a relationship between two entities"""
    from_entity: str
    to_entity: str
    from_field: str  # FK field name
    relationship_type: RelationshipType
    from_cardinality: RelationshipCardinality
    to_cardinality: RelationshipCardinality
    nullable: bool = False
    description: Optional[str] = None

@dataclass
class EntityNode:
    """Represents an entity in the diagram"""
    name: str
    schema: str
    fields: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[str]
    description: Optional[str] = None
    color: Optional[str] = None  # For visual grouping

class RelationshipExtractor:
    """
    Extract relationships from SpecQL entities

    Analyzes:
    - ref() field types
    - Foreign key constraints
    - Cardinality based on field properties
    - Self-referential relationships
    """

    def __init__(self):
        self.entities: Dict[str, EntityNode] = {}
        self.relationships: List[Relationship] = []

    def extract_from_entities(self, entities: List) -> None:
        """
        Extract all relationships from entity list

        Args:
            entities: List of parsed SpecQL entities
        """
        # First pass: Build entity nodes
        for entity in entities:
            node = self._build_entity_node(entity)
            self.entities[entity.name] = node

        # Second pass: Extract relationships
        for entity in entities:
            self._extract_entity_relationships(entity)

    def _build_entity_node(self, entity) -> EntityNode:
        """Build entity node from SpecQL entity"""
        # Pre-compute primary key names for this entity
        primary_keys = ['pk_' + entity.name.lower(), 'id']

        fields = []
        foreign_keys = []

        for field_name, field_def in entity.fields.items():
            field_info = {
                'name': field_name,
                'type': self._get_display_type(field_def),
                'required': not field_def.nullable,
                'is_pk': field_name in primary_keys,  # O(1) lookup now
                'is_fk': self._is_foreign_key(field_def),
            }

            fields.append(field_info)

            if field_info['is_fk']:
                foreign_keys.append(field_name)

        return EntityNode(
            name=entity.name,
            schema=entity.schema,
            fields=fields,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            description=entity.description or "",
        )

    def _extract_entity_relationships(self, entity) -> None:
        """Extract relationships for single entity"""
        for field_name, field_def in entity.fields.items():
            if self._is_foreign_key(field_def):
                relationship = self._analyze_relationship(entity, field_def)
                if relationship:
                    self.relationships.append(relationship)

    def _is_foreign_key(self, field_def) -> bool:
        """Check if field is a foreign key"""
        field_type = field_def.type_name

        # ref() syntax
        if field_type.startswith('ref('):
            return True

        # _id suffix convention
        if field_def.name.endswith('_id'):
            return True

        return False

    def _analyze_relationship(self, entity, field_def) -> Optional[Relationship]:
        """
        Analyze relationship type and cardinality

        Rules:
        - ref(Entity) → N:1 relationship (many-to-one)
        - Nullable ref → 0..1 cardinality
        - Required ref → 1 cardinality
        """
        field_type = field_def.type_name

        # Extract target entity
        target_entity = None

        if field_type.startswith('ref('):
            # ref(Company) → Company
            target_entity = field_type[4:-1]
        elif field_def.name.endswith('_id'):
            # company_id → Company
            target_entity = field_def.name[:-3].capitalize()

        if not target_entity:
            return None

        # Determine cardinality
        nullable = field_def.nullable

        # From cardinality (FK side)
        from_card = (RelationshipCardinality.ZERO_OR_ONE if nullable
                    else RelationshipCardinality.EXACTLY_ONE)

        # To cardinality (PK side) - default to "one or many"
        to_card = RelationshipCardinality.ONE_OR_MANY

        # Determine relationship type
        rel_type = RelationshipType.MANY_TO_ONE

        # Check for self-referential
        if target_entity == entity.name:
            rel_type = RelationshipType.SELF_REFERENTIAL

        return Relationship(
            from_entity=entity.name,
            to_entity=target_entity,
            from_field=field_def.name,
            relationship_type=rel_type,
            from_cardinality=from_card,
            to_cardinality=to_card,
            nullable=nullable,
            description=f"{entity.name}.{field_def.name} → {target_entity}"
        )

    def _get_display_type(self, field_def) -> str:
        """Get display-friendly type name"""
        field_type = field_def.type_name or 'UNKNOWN'

        # Map SpecQL types to diagram types
        type_mapping = {
            'text': 'TEXT',
            'integer': 'INT',
            'float': 'FLOAT',
            'boolean': 'BOOL',
            'date': 'DATE',
            'timestamp': 'TIMESTAMP',
            'uuid': 'UUID',
            'json': 'JSON',
        }

        if field_type.startswith('ref('):
            return 'FK'

        return type_mapping.get(field_type, field_type.upper())

    def get_relationship_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'relationship_types': {
                rel_type.value: sum(1 for r in self.relationships
                                   if r.relationship_type == rel_type)
                for rel_type in RelationshipType
            },
            'schemas': list(set(e.schema for e in self.entities.values())),
        }