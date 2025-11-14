"""Generate JPA entity classes from SpecQL entities"""

from dataclasses import dataclass
from typing import List
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


@dataclass
class JavaEntityGenerator:
    """Generates JPA @Entity classes from SpecQL entities"""

    def __init__(self, package_prefix: str = ""):
        self.package_prefix = package_prefix

    def generate(self, entity: UniversalEntity) -> str:
        """Generate complete Java entity class"""
        self.current_entity = entity  # Store for use in other methods
        lines = []
        """Generate complete Java entity class"""
        lines = []

        # Package declaration
        lines.append(f"package {entity.schema};")
        lines.append("")

        # Imports
        lines.extend(self._generate_imports(entity))
        lines.append("")

        # Class declaration
        lines.append("@Entity")
        lines.append(f'@Table(name = "tb_{entity.name.lower()}")')
        lines.append(f"public class {entity.name} {{")
        lines.append("")

        # Primary key (Trinity pattern)
        lines.extend(self._generate_primary_key())
        lines.append("")

        # Fields
        for field in entity.fields:
            lines.extend(self._generate_field(field))
            lines.append("")

        # Audit fields (Trinity pattern)
        lines.extend(self._generate_audit_fields())
        lines.append("")

        # Getters/Setters
        lines.extend(self._generate_accessors(entity))

        lines.append("}")

        return "\n".join(lines)

    def _generate_imports(self, entity: UniversalEntity) -> List[str]:
        """Generate import statements"""
        imports = [
            "import javax.persistence.*;",
            "import java.time.LocalDateTime;",
            "import org.springframework.data.annotation.CreatedDate;",
            "import org.springframework.data.annotation.LastModifiedDate;",
            "import org.springframework.data.jpa.domain.support.AuditingEntityListener;",
        ]

        # Add imports for collections if needed
        has_list = any(field.type == FieldType.LIST for field in entity.fields)
        if has_list:
            imports.extend(
                [
                    "import java.util.List;",
                    "import java.util.ArrayList;",
                ]
            )

        return imports

    def _generate_primary_key(self) -> List[str]:
        """Generate Trinity pattern primary key"""
        return [
            "    @Id",
            "    @GeneratedValue(strategy = GenerationType.IDENTITY)",
            "    private Long id;",
        ]

    def _generate_field(self, field: UniversalField) -> List[str]:
        """Generate single field with annotations"""
        lines = []

        if field.type == FieldType.REFERENCE:
            # Foreign key relationship
            if field.references is None:
                raise ValueError(
                    f"Reference field {field.name} must specify references"
                )
            lines.append("    @ManyToOne(fetch = FetchType.LAZY)")
            nullable = "false" if field.required else "true"
            lines.append(
                f'    @JoinColumn(name = "fk_{field.references.lower()}", nullable = {nullable})'
            )
            lines.append(f"    private {field.references} {field.name};")

        elif field.type == FieldType.ENUM:
            # Enum field
            lines.append("    @Enumerated(EnumType.STRING)")
            enum_class = self.current_entity.name + self._to_pascal_case(field.name)
            lines.append(f"    private {enum_class} {field.name};")

        elif field.type == FieldType.LIST:
            # OneToMany relationship
            lines.append(
                '    @OneToMany(mappedBy = "parent", cascade = CascadeType.ALL)'
            )
            lines.append(f"    private List<Object> {field.name} = new ArrayList<>();")

        else:
            # Regular field
            if field.required:
                lines.append("    @Column(nullable = false)")

            java_type = self._get_java_type(field)
            default_value = f" = {self._format_default(field)}" if field.default else ""
            lines.append(f"    private {java_type} {field.name}{default_value};")

        return lines

    def _generate_audit_fields(self) -> List[str]:
        """Generate Trinity pattern audit fields"""
        return [
            "    @CreatedDate",
            "    @Column(nullable = false, updatable = false)",
            "    private LocalDateTime createdAt;",
            "",
            "    @LastModifiedDate",
            "    @Column(nullable = false)",
            "    private LocalDateTime updatedAt;",
            "",
            "    @Column",
            "    private LocalDateTime deletedAt;",
        ]

    def _generate_accessors(self, entity: UniversalEntity) -> List[str]:
        """Generate getters and setters"""
        lines = []

        # ID accessors
        lines.append("    public Long getId() {")
        lines.append("        return id;")
        lines.append("    }")
        lines.append("")
        lines.append("    public void setId(Long id) {")
        lines.append("        this.id = id;")
        lines.append("    }")
        lines.append("")

        # Field accessors
        for field in entity.fields:
            java_type = self._get_java_type(field)
            capitalized = field.name[0].upper() + field.name[1:]

            # Getter
            lines.append(f"    public {java_type} get{capitalized}() {{")
            lines.append(f"        return {field.name};")
            lines.append("    }")
            lines.append("")

            # Setter
            lines.append(
                f"    public void set{capitalized}({java_type} {field.name}) {{"
            )
            lines.append(f"        this.{field.name} = {field.name};")
            lines.append("    }")
            lines.append("")

        return lines

    def _get_java_type(self, field: UniversalField) -> str:
        """Map SpecQL types to Java types"""
        type_map = {
            FieldType.TEXT: "String",
            FieldType.INTEGER: "Integer",
            FieldType.BOOLEAN: "Boolean",
            FieldType.DATETIME: "LocalDateTime",
        }

        if field.type == FieldType.REFERENCE:
            if field.references is None:
                raise ValueError(
                    f"Reference field {field.name} must specify references"
                )
            return field.references
        elif field.type == FieldType.ENUM:
            return self.current_entity.name + self._to_pascal_case(field.name)
        elif field.type == FieldType.LIST:
            # Extract item type from list
            return "List<Object>"  # Simplified for now
        else:
            return type_map.get(field.type, "Object")

    def _format_default(self, field: UniversalField) -> str:
        """Format default value for Java"""
        if field.type == FieldType.TEXT:
            return f'"{field.default}"'
        elif field.type == FieldType.BOOLEAN:
            return str(field.default).lower()
        else:
            return str(field.default)

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("_"))
