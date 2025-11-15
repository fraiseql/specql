"""Generate Spring @Service classes with business logic"""

from typing import List, Optional, Any
from src.core.universal_ast import (
    UniversalEntity,
    UniversalAction,
    UniversalStep,
    StepType,
    FieldType,
)


class JavaServiceGenerator:
    """Generates Spring @Service classes"""

    def __init__(self):
        self.current_entity = None

    def generate(self, entity: UniversalEntity) -> str:
        self.current_entity = entity
        """Generate complete service class"""
        lines = []

        # Package declaration
        lines.append(f"package {entity.schema}.service;")
        lines.append("")

        # Imports
        lines.extend(self._generate_imports(entity))
        lines.append("")

        # Class declaration
        lines.append("@Service")
        lines.append(f"public class {entity.name}Service {{")
        lines.append("")

        # Repository dependency injection
        lines.extend(self._generate_dependencies(entity))
        lines.append("")

        # Constructor
        lines.extend(self._generate_constructor(entity))
        lines.append("")

        # CRUD methods
        lines.extend(self._generate_crud_methods(entity))
        lines.append("")

        # Custom action methods
        for action in entity.actions:
            lines.extend(self._generate_action_method(entity, action))
            lines.append("")

        lines.append("}")

        return "\n".join(lines)

    def _generate_imports(self, entity: UniversalEntity) -> List[str]:
        """Generate import statements"""
        return [
            "import org.springframework.stereotype.Service;",
            "import org.springframework.transaction.annotation.Transactional;",
            f"import {entity.schema}.{entity.name};",
            f"import {entity.schema}.repository.{entity.name}Repository;",
            "import java.util.List;",
            "import java.util.Optional;",
        ]

    def _generate_dependencies(self, entity: UniversalEntity) -> List[str]:
        """Generate repository field"""
        repo_field = f"{entity.name.lower()}Repository"
        return [
            f"    private final {entity.name}Repository {repo_field};",
        ]

    def _generate_constructor(self, entity: UniversalEntity) -> List[str]:
        """Generate constructor with dependency injection"""
        repo_field = f"{entity.name.lower()}Repository"
        return [
            f"    public {entity.name}Service({entity.name}Repository {repo_field}) {{",
            f"        this.{repo_field} = {repo_field};",
            "    }",
        ]

    def _generate_crud_methods(self, entity: UniversalEntity) -> List[str]:
        """Generate standard CRUD operations"""
        lines = []
        repo = f"{entity.name.lower()}Repository"

        # CREATE
        lines.append("    @Transactional")
        lines.append(
            f"    public {entity.name} create({entity.name} {entity.name.lower()}) {{"
        )
        lines.append(f"        return {repo}.save({entity.name.lower()});")
        lines.append("    }")
        lines.append("")

        # READ
        lines.append(f"    public Optional<{entity.name}> findById(Long id) {{")
        lines.append(f"        return {repo}.findById(id);")
        lines.append("    }")
        lines.append("")

        lines.append(f"    public List<{entity.name}> findAll() {{")
        lines.append(f"        return {repo}.findAll();")
        lines.append("    }")
        lines.append("")

        # UPDATE
        lines.append("    @Transactional")
        lines.append(
            f"    public {entity.name} update(Long id, {entity.name} {entity.name.lower()}) {{"
        )
        lines.append(f"        {entity.name} existing = {repo}.findById(id)")
        lines.append(
            f'            .orElseThrow(() -> new RuntimeException("{entity.name} not found"));'
        )
        lines.append("")
        lines.append("        // Update fields")
        lines.append("        // TODO: Add field setters")
        lines.append("")
        lines.append(f"        return {repo}.save(existing);")
        lines.append("    }")
        lines.append("")

        # DELETE (soft delete)
        lines.append("    @Transactional")
        lines.append("    public void delete(Long id) {")
        lines.append(f"        {entity.name} entity = {repo}.findById(id)")
        lines.append(
            f'            .orElseThrow(() -> new RuntimeException("{entity.name} not found"));'
        )
        lines.append("")
        lines.append("        entity.setDeletedAt(LocalDateTime.now());")
        lines.append(f"        {repo}.save(entity);")
        lines.append("    }")

        return lines

    def _generate_action_method(
        self, entity: UniversalEntity, action: UniversalAction
    ) -> List[str]:
        """Generate custom business logic method from SpecQL action"""
        lines = []

        method_name = self._to_camel_case(action.name)

        lines.append("    @Transactional")
        lines.append(
            f"    public {entity.name} {method_name}(Long {entity.name.lower()}Id) {{"
        )

        # Load entity
        repo = f"{entity.name.lower()}Repository"
        lines.append(
            f"        {entity.name} {entity.name.lower()} = {repo}.findById({entity.name.lower()}Id)"
        )
        lines.append(
            f'            .orElseThrow(() -> new RuntimeException("{entity.name} not found"));'
        )
        lines.append("")

        # Generate steps
        for step in action.steps:
            lines.extend(self._generate_step(entity, step))

        # Save and return
        lines.append("")
        lines.append(f"        return {repo}.save({entity.name.lower()});")
        lines.append("    }")

        return lines

    def _generate_step(self, entity: UniversalEntity, step: UniversalStep) -> List[str]:
        """Generate Java code for a single action step"""
        if step.type == StepType.VALIDATE:
            return self._generate_validate_step(entity, step)
        elif step.type == StepType.UPDATE:
            return self._generate_update_step(entity, step)
        elif step.type == StepType.IF:
            return self._generate_if_step(entity, step)
        else:
            return [f"        // TODO: Implement {step.type.value} step"]

    def _generate_validate_step(
        self, entity: UniversalEntity, step: UniversalStep
    ) -> List[str]:
        """Generate validation check"""
        if step.expression is None:
            return ["        // TODO: Validation step without expression"]

        # Parse expression (simplified)
        # Example: "status = 'pending'" → if (!order.getStatus().equals(OrderStatus.PENDING))
        condition = self._parse_expression_to_java(entity, step.expression)

        return [
            f"        if (!({condition})) {{",
            f'            throw new IllegalStateException("Validation failed: {step.expression}");',
            "        }",
        ]

    def _generate_update_step(
        self, entity: UniversalEntity, step: UniversalStep
    ) -> List[str]:
        """Generate field update"""
        lines = []

        if step.fields is None:
            return ["        // TODO: Update step without fields"]

        for field_name, value in step.fields.items():
            setter = f"set{field_name[0].upper()}{field_name[1:]}"
            # Format value based on type
            formatted_value = self._format_value(value)
            lines.append(f"        {entity.name.lower()}.{setter}({formatted_value});")

        return lines

    def _generate_if_step(
        self, entity: UniversalEntity, step: UniversalStep
    ) -> List[str]:
        """Generate if/else block"""
        condition = self._parse_expression_to_java(entity, step.expression)

        lines = [f"        if ({condition}) {{"]

        # Then steps
        if step.steps is not None:
            for sub_step in step.steps:
                sub_lines = self._generate_step(entity, sub_step)
                lines.extend([f"    {line}" for line in sub_lines])

        lines.append("        }")

        return lines

    def _parse_expression_to_java(
        self, entity: UniversalEntity, expression: Optional[str]
    ) -> str:
        """Convert SpecQL expression to Java condition"""
        # Simplified parser
        # Example: "status = 'pending'" → "order.getStatus().equals(OrderStatus.PENDING)"

        if expression is None:
            return "true"  # Default condition

        if "=" in expression:
            field, value = expression.split("=")
            field = field.strip()
            value = value.strip().strip("'\"")

            getter = f"get{field[0].upper()}{field[1:]}"
            formatted_value = self._format_value(value)

            return f"{entity.name.lower()}.{getter}().equals({formatted_value})"

        return expression

    def _format_value(self, value: Any) -> str:
        """Format value for Java"""
        if isinstance(value, str):
            # Check if it's an enum value (simplified - assume enum values are lowercase)
            if self.current_entity and any(
                field.type == FieldType.ENUM and value in (field.enum_values or [])
                for field in self.current_entity.fields
            ):
                # It's an enum value, format as EnumClass.VALUE
                enum_class = f"{self.current_entity.name}{self._to_pascal_case('status')}"  # Assuming status field
                return f"{enum_class}.{value.upper()}"
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        else:
            return str(value)

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case to camelCase"""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("_"))
