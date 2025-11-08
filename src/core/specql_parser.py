"""
SpecQL YAML Parser
Parses business-focused YAML into Entity AST
"""

import re
from typing import Any, Dict, List

import yaml

from src.core.ast_models import Action, ActionStep, Agent, Entity, FieldDefinition, Organization


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
        Parse individual field specification

        Formats:
        - field_name: text
        - field_name: ref(Entity)
        - field_name: enum(val1, val2)
        - field_name: list(type)
        - field_name: text = default_value
        """
        # Handle default values (text = "default")
        if isinstance(spec, str) and " = " in spec:
            type_part, default_part = spec.split(" = ", 1)
            spec = type_part.strip()
            default = default_part.strip().strip("\"'")
        else:
            default = None

        # Simple type
        if isinstance(spec, str):
            # Check for ref(Entity)
            ref_match = self.REF_PATTERN.match(spec)
            if ref_match:
                return FieldDefinition(
                    name=name, type="ref", target_entity=ref_match.group(1), default=default
                )

            # Check for enum(val1, val2, ...)
            enum_match = self.ENUM_PATTERN.match(spec)
            if enum_match:
                values = [v.strip() for v in enum_match.group(1).split(",")]
                return FieldDefinition(name=name, type="enum", values=values, default=default)

            # Check for list(type)
            list_match = self.LIST_PATTERN.match(spec)
            if list_match:
                item_spec = list_match.group(1)
                return FieldDefinition(name=name, type="list", item_type=item_spec, default=default)

            # Simple type (text, integer, etc.)
            return FieldDefinition(name=name, type=spec, default=default)

        # Complex specification (dict)
        elif isinstance(spec, dict):
            return FieldDefinition(
                name=name,
                type=spec.get("type", "text"),
                nullable=spec.get("nullable", True),
                default=spec.get("default"),
                values=spec.get("values"),
                target_entity=spec.get("ref"),
            )

        raise ParseError(f"Invalid field specification for '{name}': {spec}")

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

        else:
            raise ParseError(f"Unknown step type: {step_data}")

    def _validate_expression_fields(
        self, expression: str, entity_fields: Dict[str, FieldDefinition]
    ) -> None:
        """Validate that fields referenced in expression exist"""
        # Extract potential field names (simple heuristic: words before operators)
        potential_fields = re.findall(r"\b([a-z_][a-z0-9_]*)\b", expression.lower())

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
