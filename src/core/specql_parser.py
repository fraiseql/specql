"""
SpecQL Parser

Extended to parse:
- Tier 1: Scalar rich types
"""

import re
from typing import Any

import yaml

from src.core.ast_models import (
    ActionDefinition,
    ActionStep,
    Agent,
    CDCConfig,
    EntityDefinition,
    ExceptionHandler,
    ExtraFilterColumn,
    FieldDefinition,
    FieldTier,
    IdentifierComponent,
    IdentifierConfig,
    IncludeRelation,
    Organization,
    RefreshScope,
    SwitchCase,
    TableViewConfig,
    TableViewMode,
)
from src.core.exceptions import SpecQLValidationError
from src.core.reserved_fields import (
    get_reserved_field_error_message,
    is_reserved_field_name,
)
from src.core.scalar_types import (
    get_composite_type,
    get_scalar_type,
    is_composite_type,
    is_scalar_type,
)
from src.core.separators import Separators
from src.core.universal_ast import (
    FieldType,
    StepType,
    UniversalEntity,
    UniversalField,
    UniversalAction,
    UniversalStep,
)
from src.core.validation_limits import ValidationLimits
from src.patterns import PatternLoader
from src.core.errors import (
    InvalidFieldTypeError,
    ErrorContext,
    InvalidEnumValueError,
    ParseError as EnhancedParseError,
)

# Valid field types
VALID_FIELD_TYPES = [
    # Basic types
    "text",
    "integer",
    "bigint",
    "float",
    "boolean",
    "timestamp",
    "date",
    "time",
    "json",
    "uuid",
    "inet",
    "macaddr",
    "point",
    # Rich scalar types (subset of SCALAR_TYPES keys)
    "email",
    "phoneNumber",
    "url",
    "slug",
    "markdown",
    "html",
    "ipAddress",
    "macAddress",
    "money",
    "percentage",
    "coordinates",
    "latitude",
    "longitude",
    "image",
    "file",
    "color",
    "hex",
    "languageCode",
    "localeCode",
    "timezone",
    "currencyCode",
    "countryCode",
    "mimeType",
    "semanticVersion",
    "stockSymbol",
    "trackingNumber",
    "licensePlate",
    "vin",
    "flightNumber",
    "portCode",
    "postalCode",
    "airportCode",
    "domainName",
    "apiKey",
    "iban",
    "swiftCode",
    "json",
    # Special types
    "enum",
    "ref",
    "list",  # These are handled separately but should be valid
]


# Backward compatibility alias
ParseError = EnhancedParseError


class SpecQLParser:
    """Parser for SpecQL YAML to AST"""

    def __init__(self):
        self.current_entity_fields = {}  # Track fields for expression validation
        self.pattern_loader = PatternLoader()  # Pattern library support
        self.entity_references = {}  # Track entity references for circular dependency detection

    def parse(self, yaml_content: str) -> EntityDefinition:
        """
        Parse SpecQL YAML to EntityDefinition AST

        Supports:
        - entity: EntityName
        - schema: schema_name
        - fields: { name: type }
        - actions: [...]
        """
        # VALIDATION 1: Check YAML file size
        ValidationLimits.validate_yaml_size(yaml_content)

        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            context = ErrorContext(file_path=getattr(self, "_file_path", None))
            raise EnhancedParseError(f"Invalid YAML: {e}", context=context)

        # VALIDATION 2: Check YAML nesting depth
        ValidationLimits.validate_nesting_depth(data)

        # Validate required fields
        if not isinstance(data, dict):
            context = ErrorContext(file_path=getattr(self, "_file_path", None))
            raise EnhancedParseError("YAML must be a dictionary", context=context)

        if "entity" not in data:
            context = ErrorContext(file_path=getattr(self, "_file_path", None))
            raise EnhancedParseError("Missing 'entity' key", context=context)

        # Parse entity metadata - supports both formats:
        # Lightweight: entity: EntityName
        # Complex: entity: {name: entity_name, schema: schema_name, description: "..."}
        if isinstance(data["entity"], dict):
            # Complex format
            entity_name = data["entity"]["name"]
            entity_schema = data["entity"].get("schema", data.get("schema", "public"))
            entity_description = data["entity"].get(
                "description", data.get("description", "")
            )
        else:
            # Lightweight format
            entity_name = data["entity"]
            entity_schema = data.get("schema", "public")
            entity_description = data.get("description", "")

        entity = EntityDefinition(
            name=entity_name,
            schema=entity_schema,
            description=entity_description,
        )

        # Parse fields - check both root level and inside entity dict (for complex format)
        if isinstance(data["entity"], dict) and "fields" in data["entity"]:
            # Complex format: fields are inside entity dict
            fields_data = data["entity"]["fields"]
        else:
            # Lightweight format: fields at root level
            fields_data = data.get("fields", {})

        for field_name, field_spec in fields_data.items():
            # VALIDATION: Check if field name is reserved
            if is_reserved_field_name(field_name):
                raise SpecQLValidationError(
                    entity=entity_name,
                    message=get_reserved_field_error_message(field_name),
                )

            field = self._parse_field(field_name, field_spec)
            entity.fields[field_name] = field

        # VALIDATION 3: Check field count
        ValidationLimits.validate_field_count(entity_name, len(entity.fields))

        # Set current entity fields for expression validation
        self.current_entity_fields = entity.fields

        # Set current entity for pattern expansion
        self._current_entity = entity

        actions_data = data.get("actions", [])
        for action_spec in actions_data:
            action = self._parse_action(action_spec, entity_name)
            entity.actions.append(action)

        # VALIDATION 4: Check action count
        ValidationLimits.validate_action_count(entity_name, len(entity.actions))

        # Parse agents
        agents_data = data.get("agents", [])
        for agent_spec in agents_data:
            agent = self._parse_agent(agent_spec)
            entity.agents.append(agent)

        # Parse organization
        if "organization" in data:
            entity.organization = self._parse_organization(data["organization"])
        elif "table_code" in data:
            # Support top-level table_code (more intuitive for simple cases)
            entity.organization = Organization(
                table_code=data["table_code"], domain_name=data.get("domain_name", None)
            )

        # Parse identifier configuration (NEW)
        entity.identifier = self._parse_identifier_config(data)

        # Parse table_views configuration (CQRS)
        if "table_views" in data:
            entity.table_views = self._parse_table_views(
                data["table_views"], entity_name
            )

        # Parse features (vector search, etc.)
        if "features" in data:
            entity.features = data["features"]

        # Parse vector configuration
        if "vector_config" in data:
            vector_config = data["vector_config"]
            if "search_functions" in vector_config:
                entity.search_functions = vector_config["search_functions"]

        # Check for circular dependencies
        self._check_circular_dependencies(entity_name, entity.fields)

        return entity

    def _check_circular_dependencies(
        self, entity_name: str, fields: dict[str, FieldDefinition]
    ) -> None:
        """Check for circular dependencies in entity references."""
        from src.core.errors import CircularDependencyError

        visited = set()
        path = []

        def visit(entity: str) -> None:
            if entity in path:
                # Found circular dependency
                cycle_start = path.index(entity)
                cycle = path[cycle_start:] + [entity]

                context = ErrorContext(entity_name=entity_name)
                raise CircularDependencyError(entities=cycle, context=context)

            if entity in visited:
                return

            visited.add(entity)
            path.append(entity)

            # Check references from this entity
            if entity in self.entity_references:
                for ref_entity in self.entity_references[entity]:
                    visit(ref_entity)

            path.pop()

        # Build reference map from fields
        for field_name, field_def in fields.items():
            if field_def.tier == FieldTier.REFERENCE and field_def.reference_entity:
                if entity_name not in self.entity_references:
                    self.entity_references[entity_name] = []
                self.entity_references[entity_name].append(field_def.reference_entity)

        # Check for cycles starting from current entity
        visit(entity_name)

    def parse_universal(self, yaml_content: str) -> UniversalEntity:
        """
        Parse SpecQL YAML to Universal AST (framework-agnostic)

        This method produces a UniversalEntity that can be used by any
        framework adapter (PostgreSQL, Django, Rails, etc.)
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            context = ErrorContext(file_path=getattr(self, "_file_path", None))
            raise EnhancedParseError(f"Invalid YAML: {e}", context=context)

        # Validate required fields
        if not isinstance(data, dict):
            context = ErrorContext(file_path=getattr(self, "_file_path", None))
            raise EnhancedParseError("YAML must be a dictionary", context=context)

        if "entity" not in data:
            context = ErrorContext(file_path=getattr(self, "_file_path", None))
            raise EnhancedParseError("Missing 'entity' key", context=context)

        # Parse entity metadata
        if isinstance(data["entity"], dict):
            # Complex format
            entity_name = data["entity"]["name"]
            entity_schema = data["entity"].get("schema", data.get("schema", "app"))
            entity_description = data["entity"].get(
                "description", data.get("description", "")
            )
            is_multi_tenant = data["entity"].get(
                "multi_tenant", data.get("multi_tenant", True)
            )
        else:
            # Lightweight format
            entity_name = data["entity"]
            entity_schema = data.get("schema", "app")
            entity_description = data.get("description", "")
            is_multi_tenant = data.get("multi_tenant", True)

        # Parse fields
        if isinstance(data["entity"], dict) and "fields" in data["entity"]:
            # Complex format: fields are inside entity dict
            fields_data = data["entity"]["fields"]
        else:
            # Lightweight format: fields at root level
            fields_data = data.get("fields", {})

        fields = []
        for field_name, field_spec in fields_data.items():
            # VALIDATION: Check if field name is reserved
            if is_reserved_field_name(field_name):
                raise SpecQLValidationError(
                    entity=entity_name,
                    message=get_reserved_field_error_message(field_name),
                )

            field = self._parse_universal_field(field_name, field_spec)
            fields.append(field)

        # Parse actions
        actions_data = data.get("actions", [])
        actions = []
        for action_spec in actions_data:
            action = self._parse_universal_action(action_spec, entity_name)
            actions.append(action)

        return UniversalEntity(
            name=entity_name,
            schema=entity_schema,
            fields=fields,
            actions=actions,
            is_multi_tenant=is_multi_tenant,
            description=entity_description,
        )

    def _parse_universal_field(
        self, field_name: str, field_spec: Any
    ) -> UniversalField:
        """
        Parse a field definition to UniversalField

        Converts SpecQL field types to universal FieldType enum
        """

        # Handle dict format (complex)
        if isinstance(field_spec, dict):
            return self._parse_universal_field_dict(field_name, field_spec)

        # Handle string format (lightweight)
        return self._parse_universal_field_string(field_name, field_spec)

    def _parse_universal_field_string(
        self, field_name: str, field_spec: str
    ) -> UniversalField:
        """Parse field from string specification to UniversalField"""

        type_str = str(field_spec).strip()
        required = False
        default = None

        # Check for default value first
        if " = " in type_str:
            type_str, default_str = type_str.split(" = ", 1)
            default = default_str.strip().strip("'\"")

        # Then check for required marker
        if type_str.endswith("!"):
            required = True
            type_str = type_str[:-1]

        # Map SpecQL types to Universal FieldType
        if type_str == "text":
            field_type = FieldType.TEXT
        elif type_str == "integer":
            field_type = FieldType.INTEGER
        elif type_str == "boolean":
            field_type = FieldType.BOOLEAN
        elif type_str == "datetime":
            field_type = FieldType.DATETIME
        elif type_str.startswith("ref(") and type_str.endswith(")"):
            field_type = FieldType.REFERENCE
        elif type_str.startswith("enum(") and type_str.endswith(")"):
            field_type = FieldType.ENUM
        elif type_str.startswith("list(") and type_str.endswith(")"):
            field_type = FieldType.LIST
        elif is_scalar_type(type_str):
            field_type = FieldType.RICH
        else:
            # Default to TEXT for unknown types
            field_type = FieldType.TEXT

        # Extract additional metadata
        references = None
        enum_values = None
        composite_type = None
        list_item_type = None

        if field_type == FieldType.REFERENCE:
            # Extract referenced entity: ref(Company) -> Company
            ref_match = re.match(r"ref\(([^)]+)\)", type_str)
            if ref_match:
                references = ref_match.group(1)

        elif field_type == FieldType.ENUM:
            # Extract enum values: enum(lead, qualified, customer) -> ['lead', 'qualified', 'customer']
            enum_match = re.match(r"enum\(([^)]+)\)", type_str)
            if enum_match:
                enum_values = [v.strip() for v in enum_match.group(1).split(",")]

        elif field_type == FieldType.LIST:
            # Extract list item type: list(text) -> text
            list_match = re.match(r"list\(([^)]+)\)", type_str)
            if list_match:
                list_item_type = list_match.group(1)

        elif field_type == FieldType.RICH:
            composite_type = type_str

        return UniversalField(
            name=field_name,
            type=field_type,
            required=required,
            default=default,
            references=references,
            enum_values=enum_values,
            composite_type=composite_type,
            list_item_type=list_item_type,
        )

    def _parse_universal_field_dict(
        self, field_name: str, field_spec: dict
    ) -> UniversalField:
        """Parse field from dict specification to UniversalField"""
        type_name = field_spec.get("type", "text")
        nullable = field_spec.get("nullable", True)
        default = field_spec.get("default")

        # Map type name to FieldType
        if type_name == "text":
            field_type = FieldType.TEXT
        elif type_name == "integer":
            field_type = FieldType.INTEGER
        elif type_name == "boolean":
            field_type = FieldType.BOOLEAN
        elif type_name == "datetime":
            field_type = FieldType.DATETIME
        elif type_name == "enum":
            field_type = FieldType.ENUM
        elif type_name == "reference":
            field_type = FieldType.REFERENCE
        elif type_name == "list":
            field_type = FieldType.LIST
        else:
            field_type = FieldType.TEXT  # Default

        # Extract metadata based on type
        references = None
        enum_values = None
        list_item_type = None

        if field_type == FieldType.REFERENCE:
            references = field_spec.get("references")
        elif field_type == FieldType.ENUM:
            enum_values = field_spec.get("values", [])
        elif field_type == FieldType.LIST:
            list_item_type = field_spec.get("items")

        return UniversalField(
            name=field_name,
            type=field_type,
            required=not nullable,
            default=default,
            references=references,
            enum_values=enum_values,
            list_item_type=list_item_type,
        )

    def _parse_universal_action(
        self, action_spec: dict, entity_name: str
    ) -> UniversalAction:
        """Parse action specification to UniversalAction"""
        if not isinstance(action_spec, dict):
            context = ErrorContext(
                entity_name=entity_name, action_name=action_spec.get("name")
            )
            raise EnhancedParseError("Action must be a dictionary", context=context)

        action_name = action_spec.get("name")
        if not action_name:
            context = ErrorContext(entity_name=entity_name)
            raise EnhancedParseError("Action must have a 'name' field", context=context)

        description = action_spec.get("description")
        steps_data = action_spec.get("steps", [])
        impacts = action_spec.get(
            "impacts", [entity_name]
        )  # Default to affecting the entity

        steps = []
        for step_data in steps_data:
            step = self._parse_universal_step(step_data)
            steps.append(step)

        return UniversalAction(
            name=action_name,
            entity=entity_name,
            steps=steps,
            impacts=impacts,
            description=description,
        )

    def _parse_universal_step(self, step_data: dict) -> UniversalStep:
        """Parse step specification to UniversalStep"""
        if not isinstance(step_data, dict):
            raise EnhancedParseError("Step must be a dictionary")

        # Extract step type
        step_type_str = None
        for key in step_data.keys():
            if key in [
                "validate",
                "if",
                "insert",
                "update",
                "delete",
                "call",
                "notify",
                "foreach",
            ]:
                step_type_str = key
                break

        if not step_type_str:
            raise EnhancedParseError(f"Unknown step type in: {step_data}")

        step_type = StepType(step_type_str)
        step_value = step_data[step_type_str]

        # Parse based on step type
        if step_type == StepType.VALIDATE:
            return UniversalStep(type=step_type, expression=step_value)
        elif step_type == StepType.UPDATE:
            # Parse "Entity SET field = value" format
            return self._parse_universal_update_step(step_value)
        elif step_type == StepType.INSERT:
            # Parse "Entity SET field = value" format
            return self._parse_universal_insert_step(step_value)
        elif step_type == StepType.DELETE:
            # Parse "Entity WHERE condition" format
            return self._parse_universal_delete_step(step_value)
        elif step_type == StepType.CALL:
            return UniversalStep(type=step_type, function=step_value)
        else:
            # For other step types, store the raw value
            return UniversalStep(type=step_type, expression=str(step_value))

    def _parse_universal_update_step(self, step_value: str) -> UniversalStep:
        """Parse update step like 'Contact SET status = qualified'"""
        # Simple parsing - can be enhanced
        parts = step_value.split(" SET ")
        if len(parts) != 2:
            raise EnhancedParseError(f"Invalid update step format: {step_value}")

        entity = parts[0].strip()
        field_assignments = parts[1].strip()

        # Parse field = value pairs
        fields = {}
        for assignment in field_assignments.split(","):
            if " = " in assignment:
                field, value = assignment.split(" = ", 1)
                fields[field.strip()] = value.strip().strip("'\"")

        return UniversalStep(type=StepType.UPDATE, entity=entity, fields=fields)

    def _parse_universal_insert_step(self, step_value: str) -> UniversalStep:
        """Parse insert step like 'Contact SET field = value'"""
        # Similar to update for now
        return self._parse_universal_update_step(step_value)

    def _parse_universal_delete_step(self, step_value: str) -> UniversalStep:
        """Parse delete step like 'Contact WHERE condition'"""
        parts = step_value.split(" WHERE ")
        if len(parts) != 2:
            raise EnhancedParseError(f"Invalid delete step format: {step_value}")

        entity = parts[0].strip()
        condition = parts[1].strip()

        return UniversalStep(type=StepType.DELETE, entity=entity, expression=condition)

    def _parse_field(self, field_name: str, field_spec: Any) -> FieldDefinition:
        """
        Parse a field definition

        Supports both lightweight and complex formats:

        Lightweight (string):
        - email!          → email scalar, NOT NULL
        - phoneNumber     → phoneNumber scalar, NULL
        - SimpleAddress   → composite type, NULL
        - text            → basic TEXT type
        - enum(values...)
        - ref(Entity)
        - list(type)

        Complex (dict):
        - type: email
          nullable: false
          description: "Primary email"
        """

        # Handle dict format (complex)
        if isinstance(field_spec, dict):
            return self._parse_field_dict(field_name, field_spec)

        # Handle string format (lightweight)
        return self._parse_field_string(field_name, field_spec)

    def _parse_field_string(self, field_name: str, field_spec: str) -> FieldDefinition:
        """Parse field from string specification (lightweight format)"""

        # Extract type and nullability
        type_str = str(field_spec).strip()
        nullable = True

        if type_str.endswith("!"):
            nullable = False
            type_str = type_str[:-1]

        # Check for default value: "enum(active, inactive) = active"
        default = None
        if " = " in type_str:
            type_str, default_str = type_str.split(" = ", 1)
            default = default_str.strip().strip("'\"")

        # Check if it's an enum type: enum(value1, value2, ...)
        if type_str.startswith("enum(") and type_str.endswith(")"):
            return self._parse_enum_field(field_name, type_str, nullable, default)

        # Check if it's a list type: list(type)
        if type_str.startswith("list(") and type_str.endswith(")"):
            return self._parse_list_field(field_name, type_str, nullable, default)

        # Check if it's a reference type: ref(Entity)
        if type_str.startswith("ref(") and type_str.endswith(")"):
            return self._parse_reference_field(field_name, type_str, nullable)

        # Check if it's a composite type
        if is_composite_type(type_str):
            return self._parse_composite_field(field_name, type_str, nullable)

        # Check if it's a scalar rich type
        if is_scalar_type(type_str):
            return self._parse_scalar_field(field_name, type_str, nullable, default)

        # Otherwise, it's a basic type
        return self._parse_basic_field(field_name, type_str, nullable, default)

    def _parse_field_dict(self, field_name: str, field_spec: dict) -> FieldDefinition:
        """Parse field from dict specification (complex format)"""
        type_name = field_spec.get("type", "text")
        nullable = field_spec.get("nullable", True)
        required = field_spec.get("required", False)
        # If required is explicitly set, it overrides nullable
        if "required" in field_spec:
            nullable = not required
        default = field_spec.get("default")
        schema = field_spec.get("schema")  # Optional cross-schema reference
        validation = field_spec.get("validation", {})

        # For dict format, we delegate to the string parser with constructed type string
        type_str = type_name

        # Handle cross-schema references: ref(Organization) + schema: management -> ref(management.Organization)
        if schema and type_str.startswith("ref(") and type_str.endswith(")"):
            # Extract entity from ref(Entity)
            entity = type_str[4:-1]
            # Reconstruct with schema: ref(schema.Entity)
            type_str = f"ref({schema}.{entity})"

        if not nullable:
            type_str += "!"
        if default is not None:
            type_str += f" = {default}"

        field_def = self._parse_field_string(field_name, type_str)

        # Apply field-specific validation overrides
        if validation:
            if "min" in validation:
                field_def.min_value = validation["min"]
            if "max" in validation:
                field_def.max_value = validation["max"]
            if "pattern" in validation:
                field_def.validation_pattern = validation["pattern"]

        return field_def

    def _parse_scalar_field(
        self, field_name: str, type_name: str, nullable: bool, default: str | None
    ) -> FieldDefinition:
        """Parse scalar rich type field"""
        scalar_def = get_scalar_type(type_name)
        if scalar_def is None:
            # Create error context
            context = ErrorContext(
                entity_name=getattr(self, "_current_entity", None).name
                if hasattr(self, "_current_entity")
                else None,
                field_name=field_name,
            )

            # Get all valid scalar types
            from src.core.scalar_types import SCALAR_TYPES

            valid_scalars = list(SCALAR_TYPES.keys())

            raise InvalidFieldTypeError(
                field_type=type_name, valid_types=valid_scalars, context=context
            )

        return FieldDefinition(
            name=field_name,
            type_name=type_name,
            nullable=nullable,
            default=default,
            tier=FieldTier.SCALAR,
            scalar_def=scalar_def,
            postgres_type=scalar_def.get_postgres_type_with_precision(),
            validation_pattern=scalar_def.validation_pattern,
            min_value=scalar_def.min_value,
            max_value=scalar_def.max_value,
            postgres_precision=scalar_def.postgres_precision,
            input_type=scalar_def.input_type,
            placeholder=scalar_def.placeholder,
            fraiseql_type=scalar_def.fraiseql_scalar_name,
        )

    def _parse_composite_field(
        self, field_name: str, type_name: str, nullable: bool
    ) -> FieldDefinition:
        """Parse composite type field"""

        composite_def = get_composite_type(type_name)
        assert composite_def is not None, f"Composite type '{type_name}' not found"

        return FieldDefinition(
            name=field_name,
            type_name=type_name,
            nullable=nullable,
            tier=FieldTier.COMPOSITE,
            composite_def=composite_def,
            postgres_type="JSONB",
            fraiseql_type=composite_def.fraiseql_type_name,
            fraiseql_schema=composite_def.get_jsonb_schema(),
            # Display metadata
            description=composite_def.description,
            example=composite_def.example,
            input_type="textarea",  # JSONB fields use textarea
        )

    def _parse_reference_field(
        self, field_name: str, type_str: str, nullable: bool
    ) -> FieldDefinition:
        """Parse reference to another entity (FK)"""

        ref_content = type_str[4:-1]  # Remove "ref(" and ")"

        # Handle polymorphic references: ref(Entity1|Entity2)
        if "|" in ref_content:
            target_entities = [entity.strip() for entity in ref_content.split("|")]
            primary_entity = target_entities[0]
            target_entities = target_entities
        else:
            primary_entity = ref_content.strip()
            target_entities = None

        # Parse schema.Entity syntax: ref(schema.Entity) or ref(Entity)
        if "." in primary_entity:
            schema, entity = primary_entity.split(".", 1)
        else:
            schema = "public"
            entity = primary_entity

        # Determine FK type based on Trinity Pattern
        # Trinity Pattern: pk_* = INTEGER PRIMARY KEY, id = UUID, identifier = TEXT
        # ALL foreign keys reference pk_* (INTEGER), NOT id (UUID)
        # This ensures referential integrity uses efficient INTEGER joins
        postgres_type = "INTEGER"  # All FKs are INTEGER (reference pk_*)

        # Track reference for circular dependency detection
        current_entity = getattr(self, "_current_entity", None)
        if current_entity and current_entity.name not in self.entity_references:
            self.entity_references[current_entity.name] = []
        if current_entity:
            self.entity_references[current_entity.name].append(entity)

        return FieldDefinition(
            name=field_name,
            type_name="ref",  # Just "ref" for type checking
            nullable=nullable,
            tier=FieldTier.REFERENCE,
            postgres_type=postgres_type,  # INTEGER for catalog, UUID for others
            fraiseql_type="ID",  # GraphQL ID type for references
            fraiseql_relation="many-to-one",  # Default relation type
            # Reference metadata
            reference_entity=entity,
            reference_schema=schema,
            # UI hints
            input_type="text",  # Could be a select dropdown in the future
        )

    def _parse_enum_field(
        self, field_name: str, type_str: str, nullable: bool, default: str | None
    ) -> FieldDefinition:
        """Parse enum field type"""

        # Extract values: enum(value1, value2, value3)
        values_str = type_str[5:-1]  # Remove "enum(" and ")"
        values = [v.strip() for v in values_str.split(",")]

        # Validate default value if provided
        if default and default not in values:
            context = ErrorContext(
                entity_name=getattr(self, "_current_entity", None).name
                if hasattr(self, "_current_entity")
                else None,
                field_name=field_name,
            )

            raise InvalidEnumValueError(
                value=default, valid_values=values, context=context
            )

        return FieldDefinition(
            name=field_name,
            type_name="enum",
            nullable=nullable,
            default=default,
            tier=FieldTier.BASIC,
            values=values,
            postgres_type="TEXT",  # Enums stored as TEXT with CHECK constraint
            fraiseql_type="String",  # GraphQL String type
        )

    def _parse_list_field(
        self, field_name: str, type_str: str, nullable: bool, default: str | None
    ) -> FieldDefinition:
        """Parse list field type"""

        # Extract item type: list(text) → text
        item_type_str = type_str[5:-1]  # Remove "list(" and ")"

        return FieldDefinition(
            name=field_name,
            type_name="list",
            nullable=nullable,
            default=default,
            tier=FieldTier.BASIC,
            item_type=item_type_str,
            postgres_type="JSONB",  # Lists stored as JSONB arrays
            fraiseql_type="[String]",  # GraphQL list type
        )

    def _parse_basic_field(
        self,
        field_name: str,
        type_name: str,
        nullable: bool,
        default: str | None = None,
    ) -> FieldDefinition:
        """Parse basic type field (text, integer, etc.)"""

        # Map basic types to PostgreSQL
        type_mapping = {
            "text": "TEXT",
            "integer": "INTEGER",
            "bigint": "BIGINT",
            "float": "DOUBLE PRECISION",
            "boolean": "BOOLEAN",
        }

        # Validate type is valid
        if type_name not in type_mapping:
            # Create error context
            context = ErrorContext(
                entity_name=getattr(self, "_current_entity", None).name
                if hasattr(self, "_current_entity")
                else None,
                field_name=field_name,
            )

            raise InvalidFieldTypeError(
                field_type=type_name,
                valid_types=list(type_mapping.keys()),
                context=context,
            )

        postgres_type = type_mapping[type_name]

        return FieldDefinition(
            name=field_name,
            type_name=type_name,
            nullable=nullable,
            default=default,
            tier=FieldTier.BASIC,
            postgres_type=postgres_type,
            fraiseql_type=type_name.capitalize(),  # Text → String in GraphQL
        )

    def _parse_action(
        self, action_spec: dict, entity_name: str = ""
    ) -> ActionDefinition:
        """Parse action definition with full step parsing and pattern support"""
        action = ActionDefinition(
            name=action_spec["name"],
            description=action_spec.get("description", ""),
        )

        # Parse CDC configuration
        if "cdc" in action_spec:
            cdc_spec = action_spec["cdc"]
            action.cdc = CDCConfig(
                enabled=cdc_spec.get("enabled", False),
                event_type=cdc_spec.get("event_type"),
                include_cascade=cdc_spec.get("include_cascade", True),
                include_payload=cdc_spec.get("include_payload", True),
                partition_key=cdc_spec.get("partition_key"),
            )

        # Check if this is a pattern-based action
        if "pattern" in action_spec:
            # Load and expand pattern
            pattern_name = action_spec["pattern"]
            config = action_spec.get("config", {})

            # We need the entity definition to expand patterns
            # This will be set during parse() call
            if hasattr(self, "_current_entity"):
                expanded = self.pattern_loader.expand_pattern(
                    pattern_name, self._current_entity, config
                )
                action.pattern = action_spec["pattern"]
                action.pattern_config = config

                # Convert expanded steps to ActionStep objects
                for step_data in expanded.expanded_steps:
                    step = self._parse_single_step(step_data)
                    action.steps.append(step)
            else:
                raise EnhancedParseError(
                    "Cannot expand patterns without entity context"
                )
        else:
            # Traditional step-based action
            for step_spec in action_spec.get("steps", []):
                step = self._parse_single_step(step_spec)
                action.steps.append(step)

        # VALIDATION 5: Check steps count
        ValidationLimits.validate_steps_count(
            entity_name, action.name, len(action.steps)
        )

        return action

    def _parse_agent(self, agent_spec: dict) -> Agent:
        """Parse AI agent definition"""
        return Agent(
            name=agent_spec["name"],
            type=agent_spec.get("type", "rule_based"),
            observes=agent_spec.get("observes", []),
            can_execute=agent_spec.get("can_execute", []),
            strategy=agent_spec.get("strategy", ""),
            audit=agent_spec.get("audit", "required"),
        )

    def _parse_organization(self, org_spec: dict) -> Organization:
        """Parse organization configuration"""
        return Organization(
            table_code=org_spec["table_code"], domain_name=org_spec.get("domain_name")
        )

    def _parse_single_step(self, step_data: dict) -> ActionStep:
        """Parse a single action step"""

        if "validate" in step_data:
            return self._parse_validate_step(step_data)
        elif "if" in step_data:
            return self._parse_if_step(step_data)
        elif "insert" in step_data:
            return self._parse_insert_step(step_data)
        elif "update" in step_data:
            return self._parse_update_step(step_data)
        elif "delete" in step_data:
            return self._parse_delete_step(step_data)
        elif "select" in step_data:
            return self._parse_select_step(step_data)
        elif "find" in step_data:
            return self._parse_find_step(step_data)
        elif "call" in step_data:
            return self._parse_call_step(step_data)
        elif "notify" in step_data:
            return self._parse_notify_step(step_data)
        elif "reject" in step_data:
            return self._parse_reject_step(step_data)
        elif "refresh_table_view" in step_data:
            return self._parse_refresh_table_view_step(step_data)
        elif "raw_sql" in step_data:
            return self._parse_raw_sql_step(step_data)
        elif "duplicate_check" in step_data:
            return self._parse_duplicate_check_step(step_data)
        elif "call_service" in step_data:
            return self._parse_call_service_step(step_data)
        elif "declare" in step_data:
            return self._parse_declare_step(step_data)
        elif "cte" in step_data:
            return self._parse_cte_step(step_data)
        elif "aggregate" in step_data:
            return self._parse_aggregate_step(step_data)
        elif "subquery" in step_data:
            return self._parse_subquery_step(step_data)
        elif "call_function" in step_data:
            return self._parse_call_function_step(step_data)
        elif "switch" in step_data:
            return self._parse_switch_step(step_data)
        elif "return_early" in step_data:
            return self._parse_return_early_step(step_data)
        elif "while" in step_data:
            return self._parse_while_step(step_data)
        elif "for_query" in step_data:
            return self._parse_for_query_step(step_data)
        elif "exception_handling" in step_data:
            return self._parse_exception_handling_step(step_data)
        elif "json_build" in step_data:
            return self._parse_json_build_step(step_data)
        elif "array_build" in step_data:
            return self._parse_array_build_step(step_data)
        elif "upsert" in step_data:
            return self._parse_upsert_step(step_data)
        elif "batch_operation" in step_data:
            return self._parse_batch_operation_step(step_data)
        elif "window_function" in step_data:
            return self._parse_window_function_step(step_data)
        elif "return_table" in step_data:
            return self._parse_return_table_step(step_data)
        elif "cursor" in step_data:
            return self._parse_cursor_step(step_data)
        elif "recursive_cte" in step_data:
            return self._parse_recursive_cte_step(step_data)
        elif "dynamic_sql" in step_data:
            return self._parse_dynamic_sql_step(step_data)
        elif "transaction_control" in step_data:
            return self._parse_transaction_control_step(step_data)
        elif "query" in step_data:
            return self._parse_query_step(step_data)
        elif "return" in step_data:
            return self._parse_return_step(step_data)
        else:
            raise EnhancedParseError(f"Unknown step type: {step_data}")

    def _parse_validate_step(self, step_data: dict) -> ActionStep:
        """Parse validate step"""
        validate_spec = step_data["validate"]
        error = step_data.get("error")

        # Validate field references in expression
        self._validate_expression_fields(validate_spec, self.current_entity_fields)

        return ActionStep(type="validate", expression=validate_spec, error=error)

    def _parse_if_step(self, step_data: dict) -> ActionStep:
        """Parse if/then/else step"""
        condition = step_data["if"]
        then_steps = [
            self._parse_single_step(step) for step in step_data.get("then", [])
        ]
        else_steps = [
            self._parse_single_step(step) for step in step_data.get("else", [])
        ]

        # Validate condition field references
        self._validate_expression_fields(condition, self.current_entity_fields)

        return ActionStep(
            type="if", condition=condition, then_steps=then_steps, else_steps=else_steps
        )

    def _parse_insert_step(self, step_data: dict) -> ActionStep:
        """Parse insert step"""
        insert_spec = step_data["insert"]
        # Simple parsing for now - just extract entity name
        entity = insert_spec.strip()

        return ActionStep(type="insert", entity=entity)

    def _parse_update_step(self, step_data: dict) -> ActionStep:
        """Parse update step"""
        update_spec = step_data["update"]

        # Handle dict format (for partial updates)
        if isinstance(update_spec, dict):
            entity = update_spec.get("entity", self._current_entity.name)
            fields = update_spec
            return ActionStep(
                type="update",
                entity=entity,
                fields=fields,
            )

        # Handle extended format with additional fields
        if isinstance(update_spec, str) and len(step_data) > 1:
            # update_spec is the entity name, additional fields in step_data
            entity = update_spec
            fields = {k: v for k, v in step_data.items() if k != "update"}
            return ActionStep(
                type="update",
                entity=entity,
                fields=fields,
            )

        # Handle simple format: update: Entity
        if isinstance(update_spec, str) and " SET " not in update_spec:
            return ActionStep(
                type="update",
                entity=update_spec,
                fields={},
            )

        # Parse: update: Entity SET field = value WHERE condition
        parts = update_spec.split(" SET ", 1)
        if len(parts) != 2:
            raise EnhancedParseError(f"Invalid update syntax: {update_spec}")

        entity = parts[0].strip()
        set_and_where = parts[1].split(" WHERE ", 1)

        raw_set = set_and_where[0].strip()
        where_clause = set_and_where[1].strip() if len(set_and_where) > 1 else None

        # Validate field references in SET clause (skip if it contains variables)
        if not any(var in raw_set.lower() for var in ["input_data", "auth_", "v_"]):
            self._validate_expression_fields(raw_set, self.current_entity_fields)
        if where_clause and not any(
            var in where_clause.lower() for var in ["input_data", "auth_", "v_"]
        ):
            self._validate_expression_fields(where_clause, self.current_entity_fields)

        return ActionStep(
            type="update",
            entity=entity,
            fields={"raw_set": raw_set},
            where_clause=where_clause,
        )

    def _parse_delete_step(self, step_data: dict) -> ActionStep:
        """Parse delete step"""
        delete_spec = step_data["delete"]

        # Parse: delete: Entity WHERE condition
        parts = delete_spec.split(" WHERE ", 1)
        entity = parts[0].strip()
        where_clause = parts[1].strip() if len(parts) > 1 else None

        if where_clause:
            self._validate_expression_fields(where_clause, self.current_entity_fields)

        return ActionStep(type="delete", entity=entity, where_clause=where_clause)

    def _parse_select_step(self, step_data: dict) -> ActionStep:
        """Parse select step"""
        select_spec = step_data["select"]

        # Handle simple format: select: Entity
        if isinstance(select_spec, str):
            return ActionStep(type="select", entity=select_spec, fields={})

        # Handle dict format for more complex selects
        if isinstance(select_spec, dict):
            entity = select_spec.get("entity", self._current_entity.name)
            fields = select_spec
            return ActionStep(type="select", entity=entity, fields=fields)

        return ActionStep(type="select", entity=str(select_spec), fields={})

    def _parse_find_step(self, step_data: dict) -> ActionStep:
        """Parse find step"""
        find_spec = step_data["find"]

        # Parse: find: Entity WHERE condition
        parts = find_spec.split(" WHERE ", 1)
        entity = parts[0].strip()
        where_clause = parts[1].strip() if len(parts) > 1 else None

        if where_clause:
            self._validate_expression_fields(where_clause, self.current_entity_fields)

        return ActionStep(type="find", entity=entity, where_clause=where_clause)

    def _parse_call_step(self, step_data: dict) -> ActionStep:
        """Parse function call step"""
        call_spec = step_data["call"]
        store_result = step_data.get("store")

        # Parse function call: function_name(arg1 = value1, arg2 = value2)
        match = re.match(r"(\w+)\s*\((.*)\)", call_spec)
        if not match:
            raise EnhancedParseError(f"Invalid call syntax: {call_spec}")

        function_name = match.group(1)
        args_str = match.group(2).strip()

        # Parse arguments
        arguments = {}
        if args_str:
            for arg in args_str.split(","):
                arg = arg.strip()
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    arguments[key] = value

        return ActionStep(
            type="call",
            function_name=function_name,
            arguments=arguments,
            store_result=store_result,
        )

    def _parse_notify_step(self, step_data: dict) -> ActionStep:
        """Parse notify step"""
        notify_spec = step_data["notify"]

        # Parse: notify: recipient(channel, "message")
        match = re.match(r"(\w+)\s*\(([^,]+),\s*(.+)\)", notify_spec)
        if not match:
            raise EnhancedParseError(f"Invalid notify syntax: {notify_spec}")

        recipient = match.group(1)
        channel = match.group(2).strip()
        message = match.group(3).strip().strip('"').strip("'")

        return ActionStep(
            type="notify",
            function_name=recipient,
            arguments={"channel": channel, "message": message},
        )

    def _parse_reject_step(self, step_data: dict) -> ActionStep:
        """Parse reject step"""
        reject_spec = step_data["reject"]

        return ActionStep(type="reject", error=reject_spec)

    def _parse_refresh_table_view_step(self, step_data: dict) -> ActionStep:
        """Parse refresh_table_view step"""

        refresh_config = step_data["refresh_table_view"]

        # Handle both string (view name) and dict (config) formats
        if isinstance(refresh_config, str):
            # Legacy format: just view name
            return ActionStep(
                type="refresh_table_view",
                view_name=refresh_config,
            )
        elif isinstance(refresh_config, dict):
            # New format: configuration dict
            # Parse scope
            scope_str = refresh_config.get("scope", "self")
            try:
                scope = RefreshScope(scope_str)
            except ValueError:
                raise EnhancedParseError(
                    f"Invalid refresh scope: {scope_str}. Must be one of: {[s.value for s in RefreshScope]}"
                )

            # Parse propagate entities
            propagate_entities = refresh_config.get("propagate", [])
            if not isinstance(propagate_entities, list):
                raise EnhancedParseError(
                    "refresh_table_view.propagate must be a list of entity names"
                )

            # Parse strategy
            strategy = refresh_config.get("strategy", "immediate")
            if strategy not in ["immediate", "deferred"]:
                raise EnhancedParseError(
                    f"Invalid refresh strategy: {strategy}. Must be: immediate or deferred"
                )

            return ActionStep(
                type="refresh_table_view",
                refresh_scope=scope,
                propagate_entities=propagate_entities,
                refresh_strategy=strategy,
            )
        else:
            raise EnhancedParseError(
                "refresh_table_view must be a string (view name) or dict (configuration)"
            )

    def _parse_raw_sql_step(self, step_data: dict) -> ActionStep:
        """Parse raw_sql step"""
        sql = step_data["raw_sql"]
        # Note: raw_sql steps contain arbitrary SQL and are not validated
        # for field references since they may reference database columns
        # that aren't defined as entity fields
        return ActionStep(
            type="raw_sql",
            sql=sql,
        )

    def _parse_duplicate_check_step(self, step_data: dict) -> ActionStep:
        """Parse duplicate_check step"""
        config = step_data["duplicate_check"]
        return ActionStep(
            type="duplicate_check",
            fields=config,
        )

    def _parse_call_service_step(self, step_data: dict) -> ActionStep:
        """Parse call_service step"""
        config = step_data["call_service"]

        # Validate required fields
        if "service" not in config:
            raise EnhancedParseError(
                "call_service step missing required field 'service'"
            )
        if "operation" not in config:
            raise EnhancedParseError(
                "call_service step missing required field 'operation'"
            )

        # Parse callbacks
        on_success = self._parse_callback_steps(config.get("on_success", []))
        on_failure = self._parse_callback_steps(config.get("on_failure", []))

        return ActionStep(
            type="call_service",
            service=config["service"],
            operation=config["operation"],
            input=config.get("input", {}),
            async_mode=config.get("async", True),
            timeout=config.get("timeout"),
            max_retries=config.get("max_retries"),
            on_success=on_success,
            on_failure=on_failure,
            correlation_field=config.get("correlation_field"),
        )

    def _parse_callback_steps(self, steps_config: list) -> list[ActionStep]:
        """Parse callback steps for call_service"""
        return [self._parse_single_step(step) for step in steps_config]

    def _validate_expression_fields(
        self, expression: str, entity_fields: dict[str, FieldDefinition]
    ) -> None:
        """Validate that fields referenced in expression exist, skipping quoted strings"""

        # Skip validation if no fields are defined (for testing or incomplete entities)
        if not entity_fields:
            return

        # Skip validation for expressions that look like SQL (contain SELECT, EXISTS, etc.)
        sql_indicators = ["select", "exists", "from", "where", "join", "tenant.", "tb_"]
        variable_indicators = ["input_data.", "auth_", "v_", "$"]
        if any(indicator in expression.lower() for indicator in sql_indicators) or any(
            indicator in expression for indicator in variable_indicators
        ):
            return

        # Remove quoted strings before extracting field names
        expression_without_quotes = re.sub(r"['\"]([^'\"]*)['\"]", "", expression)

        # Extract potential field names (words that could be field references)
        potential_fields = re.findall(
            r"\b([a-z_][a-z0-9_]*)\b", expression_without_quotes.lower()
        )

        # Keywords that are not field names
        keywords = {
            "and",
            "or",
            "not",
            "is",
            "null",
            "true",
            "false",
            "matches",
            "set",
            "where",
            "input",
            "output",
            "archived",  # Status value
            "active",  # Status value
            "email_pattern",  # Common validation pattern names
            # Audit fields (auto-generated)
            "created_at",
            "updated_at",
            "deleted_at",
            "created_by",
            "updated_by",
            "deleted_by",
            # State transition timestamps
            "approved_at",
            "cancelled_at",
            "submitted_at",
            "completed_at",
            # Other generated fields
            "identifier",
            "sequence_number",
            "display_identifier",
            # SQL functions
            "now",
            "current_timestamp",
            "auth_user_id",
            "auth_tenant_id",
        }

        for field_name in potential_fields:
            if field_name not in keywords and field_name not in entity_fields:
                raise EnhancedParseError(
                    f"Field '{field_name}' referenced in expression not found in entity. "
                    f"Available fields: {', '.join(sorted(entity_fields.keys()))}"
                )

    def _parse_identifier_config(self, yaml_data: dict) -> IdentifierConfig | None:
        """Parse identifier configuration from YAML."""

        if "identifier" not in yaml_data:
            return None

        id_config = yaml_data["identifier"]

        # Parse separators
        hierarchy_separator = id_config.get("separator", Separators.HIERARCHY)
        composition_separator = id_config.get(
            "composition_separator", Separators.COMPOSITION
        )
        internal_separator = id_config.get("internal_separator", Separators.INTERNAL)

        # Parse components
        components = self._parse_identifier_components(id_config.get("components", []))

        return IdentifierConfig(
            strategy=id_config.get("strategy", "simple"),
            separator=hierarchy_separator,
            composition_separator=composition_separator,
            internal_separator=internal_separator,
            components=components,
        )

    def _parse_identifier_components(
        self, components: list[Any]
    ) -> list[IdentifierComponent]:
        """Parse identifier components (with strip_tenant_prefix support)."""

        result = []

        for comp in components:
            if isinstance(comp, str):
                # Shorthand
                result.append(IdentifierComponent(field=comp, transform="slugify"))
            else:
                # Detailed config
                result.append(
                    IdentifierComponent(
                        field=comp["field"],
                        transform=comp.get("transform", "slugify"),
                        format=comp.get("format"),
                        separator=comp.get("separator", ""),
                        replace=comp.get("replace"),
                        strip_tenant_prefix=comp.get(
                            "strip_tenant_prefix", False
                        ),  # NEW
                    )
                )

        return result

    def _parse_table_views(self, config: dict, entity_name: str) -> TableViewConfig:
        """Parse table_views configuration block."""

        # Parse mode
        mode_str = config.get("mode", "auto")
        try:
            mode = TableViewMode(mode_str)
        except ValueError:
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"Invalid table_views.mode: '{mode_str}'. Must be: auto, force, or disable",
            )

        # Parse include_relations
        include_relations = []
        if "include_relations" in config:
            for rel_config in config["include_relations"]:
                rel = self._parse_include_relation(rel_config, entity_name)
                include_relations.append(rel)

        # Parse extra_filter_columns
        extra_filter_columns = []
        if "extra_filter_columns" in config:
            for col_config in config["extra_filter_columns"]:
                col = self._parse_extra_filter_column(col_config, entity_name)
                extra_filter_columns.append(col)

        # Parse refresh (always explicit for now)
        refresh = config.get("refresh", "explicit")
        if refresh != "explicit":
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"Only 'explicit' refresh strategy is supported (got '{refresh}')",
            )

        return TableViewConfig(
            mode=mode,
            include_relations=include_relations,
            extra_filter_columns=extra_filter_columns,
            refresh=refresh,
        )

    def _parse_include_relation(
        self, config: dict, entity_name: str
    ) -> IncludeRelation:
        """Parse include_relations entry."""

        # Format: - entity_name: { fields: [...], include_relations: [...] }
        if not isinstance(config, dict) or len(config) != 1:
            raise SpecQLValidationError(
                entity=entity_name,
                message="Invalid include_relations format. Expected single-key dict.",
            )

        relation_entity = list(config.keys())[0]
        relation_config = config[relation_entity]

        # Parse fields (required)
        if "fields" not in relation_config:
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"include_relations.{relation_entity} must specify 'fields'",
            )

        fields = relation_config["fields"]
        if not isinstance(fields, list):
            raise SpecQLValidationError(
                entity=entity_name,
                message=f"include_relations.{relation_entity}.fields must be a list",
            )

        # Parse nested include_relations (recursive)
        nested_relations = []
        if "include_relations" in relation_config:
            for nested_config in relation_config["include_relations"]:
                nested = self._parse_include_relation(nested_config, entity_name)
                nested_relations.append(nested)

        return IncludeRelation(
            entity_name=relation_entity,
            fields=fields,
            include_relations=nested_relations,
        )

    def _parse_extra_filter_column(self, config, entity_name: str) -> ExtraFilterColumn:
        """Parse extra_filter_columns entry."""

        # Simple string format
        if isinstance(config, str):
            return ExtraFilterColumn.from_string(config)

        # Dict format with options
        elif isinstance(config, dict):
            if len(config) != 1:
                raise SpecQLValidationError(
                    entity=entity_name, message="Invalid extra_filter_columns format"
                )

            col_name = list(config.keys())[0]
            col_config = config[col_name]

            return ExtraFilterColumn.from_dict(col_name, col_config)

        else:
            raise SpecQLValidationError(
                entity=entity_name,
                message="extra_filter_columns must be string or dict",
            )

    def _parse_declare_step(self, step_data: dict) -> ActionStep:
        """Parse declare step"""
        from src.core.ast_models import VariableDeclaration

        declare_data = step_data["declare"]

        # Single declaration
        if "name" in declare_data:
            return ActionStep(
                type="declare",
                variable_name=declare_data["name"],
                variable_type=declare_data.get("type", "text"),
                default_value=declare_data.get("default"),
            )

        # Multiple declarations
        elif isinstance(declare_data, list):
            declarations = [
                VariableDeclaration(
                    name=decl["name"],
                    type=decl.get("type", "text"),
                    default_value=decl.get("default"),
                )
                for decl in declare_data
            ]
            return ActionStep(type="declare", declarations=declarations)

        else:
            raise EnhancedParseError("Invalid declare step format")

    def _parse_cte_step(self, step_data: dict) -> ActionStep:
        """Parse cte step"""
        cte_data = step_data["cte"]
        return ActionStep(
            type="cte",
            cte_name=cte_data["name"],
            cte_query=cte_data["query"],
            cte_materialized=cte_data.get("materialized", False),
        )

    def _parse_aggregate_step(self, step_data: dict) -> ActionStep:
        """Parse aggregate step"""
        aggregate_data = step_data["aggregate"]
        return ActionStep(
            type="aggregate",
            aggregate_operation=aggregate_data["operation"],
            aggregate_field=aggregate_data["field"],
            aggregate_from=aggregate_data["from"],
            aggregate_where=aggregate_data.get("where"),
            aggregate_group_by=aggregate_data.get("group_by"),
            aggregate_as=aggregate_data["as"],
        )

    def _parse_subquery_step(self, step_data: dict) -> ActionStep:
        """Parse subquery step"""
        subquery_data = step_data["subquery"]
        return ActionStep(
            type="subquery",
            subquery_query=subquery_data["query"],
            subquery_result_variable=subquery_data["as"],
        )

    def _parse_call_function_step(self, step_data: dict) -> ActionStep:
        """Parse call_function step"""
        call_data = step_data["call_function"]
        return ActionStep(
            type="call_function",
            call_function_name=call_data["function"],
            call_function_arguments=call_data.get("arguments", {}),
            call_function_return_variable=call_data.get("returns"),
        )

    def _parse_switch_step(self, step_data: dict) -> ActionStep:
        """Parse switch step"""
        switch_data = step_data["switch"]

        # Parse cases
        cases = []
        for case_data in switch_data.get("cases", []):
            when_value = case_data.get("when")
            # For now, treat all 'when' as simple values
            # Complex conditions would be parsed differently
            case = SwitchCase(
                when_condition=None,  # Not used for simple switches
                when_value=when_value,
                then_steps=[
                    self._parse_single_step(step) for step in case_data.get("then", [])
                ],
            )
            cases.append(case)

        # Parse default steps
        default_steps = []
        if "default" in switch_data:
            default_steps = [
                self._parse_single_step(step) for step in switch_data["default"]
            ]

        return ActionStep(
            type="switch",
            switch_expression=switch_data.get("expression"),
            cases=cases,
            default_steps=default_steps,
        )

    def _parse_return_early_step(self, step_data: dict) -> ActionStep:
        """Parse return_early step"""
        return_data = step_data["return_early"]

        # Handle both dict format and simple value format
        if isinstance(return_data, dict):
            return ActionStep(type="return_early", return_value=return_data)
        else:
            # Simple value like NULL, a string, etc.
            return ActionStep(type="return_early", return_value=return_data)

    def _parse_while_step(self, step_data: dict) -> ActionStep:
        """Parse while loop"""
        while_data = step_data["while"]
        return ActionStep(
            type="while",
            while_condition=while_data,
            loop_body=[
                self._parse_single_step(step) for step in step_data.get("loop", [])
            ],
        )

    def _parse_for_query_step(self, step_data: dict) -> ActionStep:
        """Parse for_query loop"""
        for_data = step_data["for_query"]
        return ActionStep(
            type="for_query",
            for_query_sql=for_data,
            for_query_alias=step_data.get("as"),
            for_query_body=[
                self._parse_single_step(step) for step in step_data.get("loop", [])
            ],
        )

    def _parse_exception_handling_step(self, step_data: dict) -> ActionStep:
        """Parse exception handling block"""
        eh_data = step_data["exception_handling"]

        # Parse catch handlers
        catch_handlers = []
        for catch_data in eh_data.get("catch", []):
            handler = ExceptionHandler(
                when_condition=catch_data["when"],
                then_steps=[
                    self._parse_single_step(step) for step in catch_data.get("then", [])
                ],
            )
            catch_handlers.append(handler)

        return ActionStep(
            type="exception_handling",
            try_steps=[
                self._parse_single_step(step) for step in eh_data.get("try", [])
            ],
            catch_handlers=catch_handlers,
            finally_steps=[
                self._parse_single_step(step) for step in eh_data.get("finally", [])
            ],
        )

    def _parse_json_build_step(self, step_data: dict) -> ActionStep:
        """Parse json_build step"""
        json_data = step_data["json_build"]
        return ActionStep(
            type="json_build",
            json_variable_name=json_data["name"],
            json_object=json_data["object"],
        )

    def _parse_array_build_step(self, step_data: dict) -> ActionStep:
        """Parse array_build step"""
        array_data = step_data["array_build"]
        return ActionStep(
            type="array_build",
            array_variable_name=array_data["name"],
            array_elements=array_data["elements"],
        )

    def _parse_upsert_step(self, step_data: dict) -> ActionStep:
        """Parse upsert step"""
        upsert_data = step_data["upsert"]
        return ActionStep(
            type="upsert",
            upsert_entity=upsert_data["entity"],
            upsert_fields=upsert_data["fields"],
            upsert_conflict_target=upsert_data["conflict_target"],
            upsert_conflict_action=upsert_data["conflict_action"],
        )

    def _parse_batch_operation_step(self, step_data: dict) -> ActionStep:
        """Parse batch_operation step"""
        batch_data = step_data["batch_operation"]
        return ActionStep(
            type="batch_operation",
            batch_operation_type=batch_data["type"],
            batch_entity=batch_data["entity"],
            batch_data=batch_data["data"],
        )

    def _parse_window_function_step(self, step_data: dict) -> ActionStep:
        """Parse window_function step"""
        wf_data = step_data["window_function"]
        return ActionStep(
            type="window_function",
            window_function_name=wf_data["name"],
            window_partition_by=wf_data.get("partition_by"),
            window_order_by=wf_data.get("order_by"),
            window_frame=wf_data.get("frame"),
            window_as=wf_data.get("as"),
        )

    def _parse_return_table_step(self, step_data: dict) -> ActionStep:
        """Parse return_table step"""
        rt_data = step_data["return_table"]
        return ActionStep(type="return_table", return_table_query=rt_data["query"])

    def _parse_cursor_step(self, step_data: dict) -> ActionStep:
        """Parse cursor step"""
        cursor_data = step_data["cursor"]
        return ActionStep(
            type="cursor",
            cursor_name=cursor_data["name"],
            cursor_query=cursor_data["query"],
            cursor_operations=cursor_data.get("operations"),
        )

    def _parse_recursive_cte_step(self, step_data: dict) -> ActionStep:
        """Parse recursive_cte step"""
        rcte_data = step_data["recursive_cte"]
        return ActionStep(
            type="recursive_cte",
            recursive_cte_name=rcte_data["name"],
            recursive_cte_base_query=rcte_data["base_query"],
            recursive_cte_recursive_query=rcte_data["recursive_query"],
        )

    def _parse_dynamic_sql_step(self, step_data: dict) -> ActionStep:
        """Parse dynamic_sql step"""
        ds_data = step_data["dynamic_sql"]
        return ActionStep(
            type="dynamic_sql",
            dynamic_sql_template=ds_data["template"],
            dynamic_sql_parameters=ds_data.get("parameters"),
            dynamic_sql_result_variable=ds_data.get("result_variable"),
        )

    def _parse_transaction_control_step(self, step_data: dict) -> ActionStep:
        """Parse transaction_control step"""
        tc_data = step_data["transaction_control"]
        return ActionStep(
            type="transaction_control", transaction_command=tc_data["command"]
        )

    def _parse_query_step(self, step_data: dict) -> ActionStep:
        """Parse query step"""
        query_data = step_data["query"]
        return ActionStep(type="query", expression=query_data)

    def _parse_return_step(self, step_data: dict) -> ActionStep:
        """Parse return step"""
        return_data = step_data["return"]
        return ActionStep(type="return", expression=return_data)
