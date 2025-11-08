"""
SpecQL YAML Parser
Parses business-focused YAML into Entity AST
"""

import re
from typing import Any, Dict, List, Optional, Tuple

import yaml

from src.core.ast_models import (
    Action,
    ActionStep,
    Agent,
    DeduplicationRule,
    DeduplicationStrategy,
    Entity,
    FieldDefinition,
    ForeignKey,
    GraphQLSchema,
    Index,
    OperationConfig,
    Organization,
    TranslationConfig,
    TrinityHelper,
    TrinityHelpers,
    ValidationRule,
)
from src.core.type_registry import get_type_registry


class ParseError(Exception):
    """Raised when YAML parsing fails"""

    pass


class SpecQLParser:
    """Parse SpecQL YAML into AST with comprehensive validation"""

    # Regex patterns (extracted for maintainability)
    REF_PATTERN = re.compile(r"ref\((\w+)\)")
    ENUM_PATTERN = re.compile(r"enum\((.*)\)")
    LIST_PATTERN = re.compile(r"list\((.*)\)")
    INSERT_PATTERN = re.compile(r"(\w+)\((.*)\)")
    UPDATE_PATTERN = re.compile(r"(\w+)\s+SET\s+(.*?)(?:\s+WHERE\s+(.*))?$", re.IGNORECASE)
    CALL_PATTERN = re.compile(r"(\w+)\((.*)\)")

    def __init__(self) -> None:
        self.type_registry = get_type_registry()

    # Reserved keywords for expression validation
    KEYWORDS = {
        "and",
        "or",
        "not",
        "null",
        "true",
        "false",
        "current_date",
        "exists",
        "is",
        "in",
        "like",
        "between",
        "input",
        "matches",
        "current_timestamp",
        "now",
        "select",
        "from",
        "where",
    }

    def parse_string(self, yaml_content: str) -> Entity:
        """Parse YAML string into Entity AST (alias for parse)"""
        return self.parse(yaml_content)

    def parse(self, yaml_content: str) -> Entity:
        """
        Parse YAML content into Entity AST

        Args:
            yaml_content: YAML string to parse

        Returns:
            Entity AST

        Raises:
            ParseError: If YAML is invalid
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ParseError(f"Invalid YAML: {e}")

        if "entity" not in data:
            raise ParseError("Missing 'entity' key in YAML")

        entity_data = data["entity"]

        # Handle both simple and complex entity formats
        if isinstance(entity_data, str):
            # Simple form: entity: EntityName
            entity_name = entity_data
            entity_config = data
        else:
            # Complex form: entity contains all config
            entity_name = entity_data.get("name")
            if not entity_name:
                raise ParseError("Entity name is required")
            entity_config = entity_data

        entity = Entity(
            name=entity_name,
            schema=entity_config.get("schema", "public"),
            table=entity_config.get("table"),
            table_code=entity_config.get("table_code"),
            description=entity_config.get("description", ""),
        )

        # Parse organization (numbering system)
        if "organization" in entity_config:
            org_data = entity_config["organization"]
            entity.organization = Organization(
                table_code=org_data["table_code"], domain_name=org_data.get("domain_name")
            )

        # Parse fields
        if "fields" in entity_config:
            entity.fields = self._parse_fields(entity_config["fields"])

        # Parse foreign keys
        if "foreign_keys" in entity_config:
            entity.foreign_keys = self._parse_foreign_keys(entity_config["foreign_keys"])

        # Parse indexes
        if "indexes" in entity_config:
            entity.indexes = self._parse_indexes(entity_config["indexes"])

        # Parse validation rules
        if "validation" in entity_config:
            entity.validation = self._parse_validation_rules(entity_config["validation"])

        # Parse deduplication strategy
        if "deduplication" in entity_config:
            entity.deduplication = self._parse_deduplication(entity_config["deduplication"])

        # Parse operations config
        if "operations" in entity_config:
            entity.operations = self._parse_operations(entity_config["operations"])

        # Parse trinity helpers
        if "trinity_helpers" in entity_config:
            entity.trinity_helpers = self._parse_trinity_helpers(entity_config["trinity_helpers"])

        # Parse GraphQL schema
        if "graphql" in entity_config:
            entity.graphql = self._parse_graphql(entity_config["graphql"])

        # Parse translations
        if "translations" in entity_config:
            entity.translations = self._parse_translations(entity_config["translations"])

        # Parse notes
        if "notes" in entity_config:
            entity.notes = entity_config["notes"]

        # Parse actions
        if "actions" in entity_config:
            entity.actions = self._parse_actions(entity_config["actions"], entity.fields)

        # Parse agents
        if "agents" in entity_config:
            entity.agents = self._parse_agents(entity_config["agents"])

        return entity

    def _parse_fields(self, fields_data: Dict) -> Dict[str, FieldDefinition]:
        """Parse field definitions"""
        fields = {}

        for field_name, field_spec in fields_data.items():
            field_def = self._parse_field_spec(field_name, field_spec)
            fields[field_name] = field_def

        return fields

    def _parse_field_spec(self, name: str, spec: Any) -> FieldDefinition:
        """
        Parse individual field specification with rich type support

        Formats:
        - field_name: text
        - field_name: email
        - field_name: money(currency=USD)
        - field_name: ref(Entity)
        - field_name: enum(val1, val2)
        - field_name: list(type)
        - field_name: text = default_value
        """
        # Handle simple string type: "email: email"
        if isinstance(spec, str):
            return self._parse_simple_field_spec(name, spec)

        # Handle dict with options: "email: {type: email, nullable: false}"
        elif isinstance(spec, dict):
            return self._parse_complex_field_spec(name, spec)

        else:
            raise ParseError(f"Invalid field specification for '{name}': {spec}")

    def _parse_simple_field_spec(self, name: str, type_spec: str) -> FieldDefinition:
        """Parse simple field type string with rich type support"""

        # Check for nullable marker: "email!"
        nullable = True
        if type_spec.endswith("!"):
            nullable = False
            type_spec = type_spec[:-1]

        # Check for default value: "color = '#000000'"
        default = None
        if " = " in type_spec:
            type_spec, default_str = type_spec.split(" = ", 1)
            default = default_str.strip().strip("'\"")

        # Check for special types first (enum, ref, list)
        # Check for ref(Entity)
        ref_match = self.REF_PATTERN.match(type_spec)
        if ref_match:
            return FieldDefinition(
                name=name,
                type="ref",
                target_entity=ref_match.group(1),
                nullable=nullable,
                default=default,
            )

        # Check for enum(val1, val2, ...)
        enum_match = self.ENUM_PATTERN.match(type_spec)
        if enum_match:
            values = [v.strip() for v in enum_match.group(1).split(",")]
            return FieldDefinition(
                name=name, type="enum", values=values, nullable=nullable, default=default
            )

        # Check for list(type)
        list_match = self.LIST_PATTERN.match(type_spec)
        if list_match:
            item_spec = list_match.group(1)
            return FieldDefinition(
                name=name, type="list", item_type=item_spec, nullable=nullable, default=default
            )

        # Parse regular/rich types with metadata: "money(currency=USD)"
        type_name, type_metadata = self._parse_type_with_metadata(type_spec)

        # Validate type exists
        self._validate_type(type_name)

        return FieldDefinition(
            name=name,
            type=type_name,
            nullable=nullable,
            default=default,
            type_metadata=type_metadata,
        )

    def _parse_complex_field_spec(self, name: str, field_dict: Dict[str, Any]) -> FieldDefinition:
        """Parse complex field definition with explicit options"""

        type_spec = field_dict.get("type")
        if not type_spec:
            raise ParseError(f"Missing 'type' for field {name}")

        type_name, type_metadata = self._parse_type_with_metadata(type_spec)

        # Validate type
        self._validate_type(type_name)

        return FieldDefinition(
            name=name,
            type=type_name,
            nullable=field_dict.get("nullable", True),
            default=field_dict.get("default"),
            type_metadata=type_metadata,
        )

    def _parse_type_with_metadata(self, type_spec: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Parse type with optional metadata: money(currency=USD, precision=2)"""

        # Check for metadata: "money(currency=USD)"
        match = re.match(r"(\w+)\((.*)\)", type_spec)
        if match:
            type_name = match.group(1)
            metadata_str = match.group(2)

            # Parse metadata key=value pairs
            metadata = {}
            for pair in metadata_str.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")

                    # Try to parse as number
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep as string

                    metadata[key] = value

            return type_name, metadata

        # No metadata, just type name
        return type_spec, None

    def _validate_type(self, type_name: str) -> None:
        """Validate type with helpful error messages"""
        # Check rich types
        if self.type_registry.is_rich_type(type_name):
            return

        # Check basic types
        basic_types = {"text", "integer", "boolean", "jsonb", "timestamp", "uuid"}
        if type_name in basic_types:
            return

        # Check special types
        if type_name in {"ref", "list", "enum"}:
            return

        # Unknown type - find similar suggestions
        similar = self._find_similar_types(type_name)
        suggestion = f" Did you mean: {', '.join(similar)}?" if similar else ""

        raise ValueError(f"Unknown type: {type_name}.{suggestion}")

    def _find_similar_types(self, type_name: str) -> List[str]:
        """Find similar type names for typo suggestions"""
        import difflib

        all_types = self.type_registry.get_all_rich_types() | {
            "text",
            "integer",
            "boolean",
            "jsonb",
            "timestamp",
            "uuid",
            "ref",
            "list",
            "enum",
        }

        # Find close matches (ratio > 0.6)
        matches = difflib.get_close_matches(type_name, all_types, n=3, cutoff=0.6)
        return matches

    def _parse_actions(
        self, actions_data: List[Dict], entity_fields: Dict[str, FieldDefinition]
    ) -> List[Action]:
        """Parse action definitions"""
        actions = []

        for action_data in actions_data:
            action = Action(name=action_data["name"], requires=action_data.get("requires"))

            # Parse action steps
            if "steps" in action_data:
                action.steps = self._parse_steps(action_data["steps"], entity_fields)

            actions.append(action)

        return actions

    def _parse_steps(
        self, steps_data: List, entity_fields: Dict[str, FieldDefinition]
    ) -> List[ActionStep]:
        """Parse action step DSL"""
        steps = []

        for step_data in steps_data:
            step = self._parse_single_step(step_data, entity_fields)
            steps.append(step)

        return steps

    def _parse_single_step(
        self, step_data: Dict, entity_fields: Dict[str, FieldDefinition]
    ) -> ActionStep:
        """Parse single action step"""

        # Validate step
        if "validate" in step_data:
            expression = step_data["validate"]

            # Validate field references in expression
            self._validate_expression_fields(expression, entity_fields)

            return ActionStep(
                type="validate",
                expression=expression,
                error=step_data.get("error", "validation_failed"),
            )

        # If-then-else step
        elif "if" in step_data:
            condition = step_data["if"]
            then_steps = self._parse_steps(step_data.get("then", []), entity_fields)
            else_steps = self._parse_steps(step_data.get("else", []), entity_fields)

            return ActionStep(
                type="if", condition=condition, then_steps=then_steps, else_steps=else_steps
            )

        # Insert step
        elif "insert" in step_data:
            entity_spec = step_data["insert"]

            # Parse entity name and fields
            if isinstance(entity_spec, str):
                # Simple form: insert: Entity
                entity_name = entity_spec
                fields = None
            else:
                # Complex form: insert: Entity(field1, field2)
                match = self.INSERT_PATTERN.match(entity_spec)
                if match:
                    entity_name = match.group(1)
                    field_list = [f.strip() for f in match.group(2).split(",")]
                    fields = {f: f"input.{f}" for f in field_list}
                else:
                    raise ParseError(f"Invalid insert syntax: {entity_spec}")

            return ActionStep(type="insert", entity=entity_name, fields=fields)

        # Update step
        elif "update" in step_data:
            update_spec = step_data["update"]

            # Parse: update: entity SET field = value WHERE condition
            match = self.UPDATE_PATTERN.match(update_spec)
            if match:
                entity_name = match.group(1)
                set_clause = match.group(2)
                where_clause = match.group(3)
            else:
                raise ParseError(f"Invalid update syntax: {update_spec}")

            return ActionStep(
                type="update",
                entity=entity_name,
                fields={"raw_set": set_clause},
                where_clause=where_clause,
            )

        # Delete step
        elif "delete" in step_data:
            return ActionStep(type="delete", entity=step_data["delete"])

        # Find step
        elif "find" in step_data:
            find_spec = step_data["find"]

            # Parse: find: entity WHERE condition
            parts = re.split(r"\s+WHERE\s+", find_spec, maxsplit=1, flags=re.IGNORECASE)
            entity_name = parts[0].strip()
            where_clause = parts[1].strip() if len(parts) > 1 else None

            return ActionStep(type="find", entity=entity_name, where_clause=where_clause)

        # Call step
        elif "call" in step_data:
            call_spec = step_data["call"]

            # Parse: call: function_name(arg1 = val1, arg2 = val2)
            match = self.CALL_PATTERN.match(call_spec)
            if match:
                function_name = match.group(1)
                args_str = match.group(2)

                # Parse arguments
                arguments = {}
                if args_str:
                    for arg in args_str.split(","):
                        arg = arg.strip()
                        if "=" in arg:
                            key, value = arg.split("=", 1)
                            arguments[key.strip()] = value.strip()

                return ActionStep(
                    type="call",
                    function_name=function_name,
                    arguments=arguments,
                    store_result=step_data.get("store"),
                )
            else:
                raise ParseError(f"Invalid call syntax: {call_spec}")

        # Reject step
        elif "reject" in step_data:
            return ActionStep(type="reject", error=step_data["reject"])

        # Notify step
        elif "notify" in step_data:
            notify_spec = step_data["notify"]

            # Parse: notify: recipient(channel, "message")
            match = self.CALL_PATTERN.match(notify_spec)
            if match:
                recipient = match.group(1)
                args_str = match.group(2)

                # Parse arguments: channel, "message"
                arguments = {}
                if args_str:
                    parts = [
                        arg.strip() for arg in args_str.split(",", 1)
                    ]  # Split only on first comma
                    if len(parts) >= 1:
                        arguments["channel"] = parts[0].strip().strip("\"'")
                    if len(parts) >= 2:
                        arguments["message"] = parts[1].strip().strip("\"'")

                return ActionStep(type="notify", function_name=recipient, arguments=arguments)
            else:
                raise ParseError(f"Invalid notify syntax: {notify_spec}")

        else:
            raise ParseError(f"Unknown step type: {step_data}")

    def _validate_expression_fields(
        self, expression: str, entity_fields: Dict[str, FieldDefinition]
    ) -> None:
        """Validate that fields referenced in expression exist"""
        # Remove quoted strings before extracting field names
        expression_without_quotes = re.sub(r"['\"]([^'\"]*)['\"]", "", expression)
        potential_fields = re.findall(r"\b([a-z_][a-z0-9_]*)\b", expression_without_quotes.lower())

        # Additional allowed terms (patterns, functions, etc.)
        allowed_terms = {
            "email_pattern",
            "phone_pattern",
            "url_pattern",  # Common patterns
            "current_date",
            "current_timestamp",
            "now",  # Date/time functions
            "length",
            "upper",
            "lower",  # String functions
            "true",
            "false",
            "null",  # Literals
        }

        # Filter out common keywords and allowed terms
        for field_name in potential_fields:
            if (
                field_name not in self.KEYWORDS
                and field_name not in entity_fields
                and field_name not in allowed_terms
            ):
                # Allow input.field_name pattern
                if not (
                    f"input.{field_name}" in expression
                    or f"{field_name}(" in expression  # function call
                    or field_name.endswith("_pattern")
                ):  # pattern reference
                    raise ParseError(
                        f"Field '{field_name}' referenced in expression not found in entity. "
                        f"Available fields: {', '.join(entity_fields.keys())}"
                    )

    def _parse_foreign_keys(self, foreign_keys_data: Dict) -> List[ForeignKey]:
        """Parse foreign key definitions"""
        foreign_keys = []

        for fk_name, fk_spec in foreign_keys_data.items():
            foreign_key = ForeignKey(
                name=fk_name,
                references=fk_spec["references"],
                on=fk_spec["on"],
                nullable=fk_spec.get("nullable", True),
                description=fk_spec.get("description", ""),
            )
            foreign_keys.append(foreign_key)

        return foreign_keys

    def _parse_indexes(self, indexes_data: List[Dict]) -> List[Index]:
        """Parse index definitions"""
        indexes = []

        for index_data in indexes_data:
            index = Index(
                columns=index_data["columns"],
                type=index_data.get("type", "btree"),
                name=index_data.get("name"),
            )
            indexes.append(index)

        return indexes

    def _parse_validation_rules(self, validation_data: List[Dict]) -> List[ValidationRule]:
        """Parse validation rule definitions"""
        rules = []

        for rule_data in validation_data:
            rule = ValidationRule(
                name=rule_data["name"],
                condition=rule_data["condition"],
                error=rule_data["error"],
            )
            rules.append(rule)

        return rules

    def _parse_deduplication(self, deduplication_data: Dict) -> DeduplicationStrategy:
        """Parse deduplication strategy"""
        strategy = DeduplicationStrategy(strategy=deduplication_data["strategy"])

        if "rules" in deduplication_data:
            for rule_data in deduplication_data["rules"]:
                rule = DeduplicationRule(
                    fields=rule_data["fields"],
                    when=rule_data.get("when"),
                    priority=rule_data.get("priority", 1),
                    message=rule_data.get("message", ""),
                )
                strategy.rules.append(rule)

        return strategy

    def _parse_operations(self, operations_data: Dict) -> OperationConfig:
        """Parse operations configuration"""
        return OperationConfig(
            create=operations_data.get("create", True),
            update=operations_data.get("update", True),
            delete=operations_data.get("delete", "soft"),
            recalcid=operations_data.get("recalcid", True),
        )

    def _parse_trinity_helpers(self, helpers_data: Dict) -> TrinityHelpers:
        """Parse trinity helpers configuration"""
        helpers = TrinityHelpers(
            generate=helpers_data.get("generate", True),
            lookup_by=helpers_data.get("lookup_by"),
        )

        if "helpers" in helpers_data:
            for helper_data in helpers_data["helpers"]:
                helper = TrinityHelper(
                    name=helper_data["name"],
                    params=helper_data["params"],
                    returns=helper_data["returns"],
                    description=helper_data.get("description", ""),
                )
                helpers.helpers.append(helper)

        return helpers

    def _parse_graphql(self, graphql_data: Dict) -> GraphQLSchema:
        """Parse GraphQL schema configuration"""
        return GraphQLSchema(
            type_name=graphql_data["type_name"],
            queries=graphql_data.get("queries", []),
            mutations=graphql_data.get("mutations", []),
        )

    def _parse_translations(self, translations_data: Dict) -> TranslationConfig:
        """Parse translations configuration"""
        return TranslationConfig(
            enabled=translations_data.get("enabled", False),
            table_name=translations_data.get("table_name"),
            fields=translations_data.get("fields", []),
        )

    def _parse_agents(self, agents_data: List[Dict]) -> List[Agent]:
        """Parse AI agent definitions"""
        agents = []

        for agent_data in agents_data:
            agent = Agent(
                name=agent_data["name"],
                type=agent_data.get("type", "rule_based"),
                observes=agent_data.get("observes", []),
                can_execute=agent_data.get("can_execute", []),
                strategy=agent_data.get("strategy", ""),
                audit=agent_data.get("audit", "required"),
            )
            agents.append(agent)

        return agents
