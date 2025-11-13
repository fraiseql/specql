"""
JPA Annotation Visitor

Extracts JPA annotations from Java AST to identify:
- Entities (@Entity)
- Fields and their types
- Relationships (@ManyToOne, @OneToMany, etc.)
- Column mappings (@Column, @JoinColumn)
- Enums (@Enumerated)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class FieldSpec:
    """Field specification for SpecQL"""
    name: str
    type: Any  # Will be FieldType from universal_ast
    nullable: bool = True
    unique: bool = False


@dataclass
class EntitySpec:
    """Entity specification for SpecQL"""
    name: str
    schema: str = "public"
    table_name: Optional[str] = None
    fields: List[FieldSpec] = field(default_factory=list)


@dataclass
class JPAField:
    """Represents a field in a JPA entity"""
    name: str
    java_type: str
    column_name: Optional[str] = None
    nullable: bool = True
    unique: bool = False
    length: Optional[int] = None

    # Relationship info
    is_relationship: bool = False
    relationship_type: Optional[str] = None  # ManyToOne, OneToMany, etc.
    target_entity: Optional[str] = None
    join_column: Optional[str] = None

    # Enum info
    is_enum: bool = False
    enum_type: Optional[str] = None  # STRING or ORDINAL


@dataclass
class JPAEntity:
    """Represents a JPA entity class"""
    class_name: str
    table_name: Optional[str] = None
    schema: Optional[str] = None
    fields: List[JPAField] = field(default_factory=list)
    id_field: Optional[str] = None


class JPAAnnotationVisitor:
    """Visit Java AST and extract JPA annotations"""

    def __init__(self, compilation_unit):
        """
        Initialize visitor

        Args:
            compilation_unit: Eclipse JDT CompilationUnit or MockCompilationUnit
        """
        self.cu = compilation_unit
        self.entities: List[JPAEntity] = []

    def visit(self) -> List[JPAEntity]:
        """Visit AST and extract JPA entities"""
        # Get all types in compilation unit
        types = self.cu.types()

        for type_decl in types:
            if self._is_entity(type_decl):
                entity = self._extract_entity(type_decl)
                self.entities.append(entity)

        return self.entities

    def _is_entity(self, type_decl) -> bool:
        """Check if type is a JPA entity"""
        modifiers = type_decl.modifiers()

        for modifier in modifiers:
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()
                if annotation_name in ('Entity', 'jakarta.persistence.Entity', 'javax.persistence.Entity'):
                    return True

        return False

    def _extract_entity(self, type_decl) -> JPAEntity:
        """Extract entity information from type declaration"""
        class_name = type_decl.getName().getIdentifier()

        # Extract @Table annotation
        table_name = None
        schema = None

        for modifier in type_decl.modifiers():
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()

                if annotation_name in ('Table', 'jakarta.persistence.Table', 'javax.persistence.Table'):
                    table_info = self._extract_table_annotation(modifier)
                    table_name = table_info.get('name')
                    schema = table_info.get('schema')

        # Create entity
        entity = JPAEntity(
            class_name=class_name,
            table_name=table_name or self._to_snake_case(class_name),
            schema=schema
        )

        # Extract fields
        for field_decl in type_decl.bodyDeclarations():
            if field_decl.getNodeType() == field_decl.FIELD_DECLARATION:
                jpa_field = self._extract_field(field_decl)
                entity.fields.append(jpa_field)

                # Check if ID field
                if self._is_id_field(field_decl):
                    entity.id_field = jpa_field.name

        return entity

    def _extract_field(self, field_decl) -> JPAField:
        """Extract field information"""
        # Get field name
        fragments = field_decl.fragments()
        field_name = fragments[0].getName().getIdentifier()

        # Get field type
        field_type = field_decl.getType().toString()

        # Initialize field
        jpa_field = JPAField(
            name=field_name,
            java_type=field_type
        )

        # Extract annotations
        for modifier in field_decl.modifiers():
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()

                if annotation_name in ('Column', 'jakarta.persistence.Column', 'javax.persistence.Column'):
                    column_info = self._extract_column_annotation(modifier)
                    jpa_field.column_name = column_info.get('name')
                    jpa_field.nullable = column_info.get('nullable', True)
                    jpa_field.unique = column_info.get('unique', False)
                    jpa_field.length = column_info.get('length')

                elif annotation_name in ('ManyToOne', 'jakarta.persistence.ManyToOne', 'javax.persistence.ManyToOne'):
                    jpa_field.is_relationship = True
                    jpa_field.relationship_type = 'ManyToOne'
                    jpa_field.target_entity = field_type

                elif annotation_name in ('OneToMany', 'jakarta.persistence.OneToMany', 'javax.persistence.OneToMany'):
                    jpa_field.is_relationship = True
                    jpa_field.relationship_type = 'OneToMany'
                    # Extract target from generic type
                    jpa_field.target_entity = self._extract_generic_type(field_type)

                elif annotation_name in ('JoinColumn', 'jakarta.persistence.JoinColumn', 'javax.persistence.JoinColumn'):
                    join_info = self._extract_join_column_annotation(modifier)
                    jpa_field.join_column = join_info.get('name')

                elif annotation_name in ('Enumerated', 'jakarta.persistence.Enumerated', 'javax.persistence.Enumerated'):
                    jpa_field.is_enum = True
                    enum_info = self._extract_enumerated_annotation(modifier)
                    jpa_field.enum_type = enum_info.get('value', 'ORDINAL')

        return jpa_field

    def _is_id_field(self, field_decl) -> bool:
        """Check if field is annotated with @Id"""
        for modifier in field_decl.modifiers():
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()
                if annotation_name in ('Id', 'jakarta.persistence.Id', 'javax.persistence.Id'):
                    return True
        return False

    def _extract_table_annotation(self, annotation) -> Dict[str, Any]:
        """Extract @Table annotation values"""
        values = {}

        if annotation.isSingleMemberAnnotation():
            values['name'] = self._get_annotation_value(annotation.getValue())
        elif annotation.isNormalAnnotation():
            for pair in annotation.values():
                key = pair.getName().getIdentifier()
                value = self._get_annotation_value(pair.getValue())
                values[key] = value

        return values

    def _extract_column_annotation(self, annotation) -> Dict[str, Any]:
        """Extract @Column annotation values"""
        return self._extract_table_annotation(annotation)  # Same logic

    def _extract_join_column_annotation(self, annotation) -> Dict[str, Any]:
        """Extract @JoinColumn annotation values"""
        return self._extract_table_annotation(annotation)  # Same logic

    def _extract_enumerated_annotation(self, annotation) -> Dict[str, Any]:
        """Extract @Enumerated annotation values"""
        return self._extract_table_annotation(annotation)  # Same logic

    def _get_annotation_value(self, value_node):
        """Extract value from annotation"""
        # Handle string literals
        if hasattr(value_node, 'getNodeType'):
            if value_node.getNodeType() == value_node.STRING_LITERAL:
                return value_node.getLiteralValue()

            # Handle boolean literals
            if value_node.getNodeType() == value_node.BOOLEAN_LITERAL:
                return value_node.booleanValue()

            # Handle number literals
            if value_node.getNodeType() == value_node.NUMBER_LITERAL:
                return int(value_node.getToken())

            # Handle qualified names (e.g., EnumType.STRING)
            if value_node.getNodeType() == value_node.QUALIFIED_NAME:
                return value_node.getFullyQualifiedName().split('.')[-1]

        # Fallback for mock implementation
        if hasattr(value_node, 'literal_value'):
            return value_node.literal_value

        return None

    def _extract_generic_type(self, type_str: str) -> Optional[str]:
        """Extract generic type from List<Entity>"""
        if '<' in type_str and '>' in type_str:
            start = type_str.index('<') + 1
            end = type_str.index('>')
            return type_str[start:end].strip()
        return None

    def _to_snake_case(self, camel_case: str) -> str:
        """Convert CamelCase to snake_case"""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()