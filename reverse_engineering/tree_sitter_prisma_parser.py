"""Tree-sitter based Prisma schema parser."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

# Conditional imports for optional dependencies
try:
    from .tree_sitter_compat import (
        HAS_TREE_SITTER,
        Language,
        Node,
        Parser,
        get_prisma_language,
        get_prisma_parser,
    )

    HAS_TREE_SITTER_PRISMA = HAS_TREE_SITTER
except ImportError:
    HAS_TREE_SITTER_PRISMA = False
    if not TYPE_CHECKING:
        # Create stub types for when the dependency is missing
        Language = Any  # type: ignore
        Parser = Any  # type: ignore
        Node = Any  # type: ignore
        get_prisma_language = None  # type: ignore
        get_prisma_parser = None  # type: ignore


@dataclass
class PrismaField:
    """Represents a field in a Prisma model."""

    name: str
    type: str
    is_required: bool = True
    is_list: bool = False
    is_id: bool = False
    is_unique: bool = False
    has_default: bool = False
    default_value: str | None = None
    relation_name: str | None = None
    attributes: list[str] = field(default_factory=list)


@dataclass
class PrismaModel:
    """Represents a Prisma model."""

    name: str
    fields: list[PrismaField] = field(default_factory=list)
    indexes: list[dict] = field(default_factory=list)
    unique_constraints: list[dict] = field(default_factory=list)
    table_name: str | None = None


@dataclass
class PrismaEnum:
    """Represents a Prisma enum."""

    name: str
    values: list[str] = field(default_factory=list)


class TreeSitterPrismaParser:
    """Parse Prisma schema files using tree-sitter."""

    def __init__(self):
        """Initialize tree-sitter parser with Prisma grammar."""
        if not HAS_TREE_SITTER_PRISMA:
            raise ImportError(
                "py-tree-sitter-languages is required for Prisma parsing. "
                "Install with: pip install specql[reverse]"
            )
        self.language = get_prisma_language()
        self.parser = get_prisma_parser()

    def parse(self, schema: str) -> Node:
        """Parse Prisma schema into AST."""
        tree = self.parser.parse(bytes(schema, "utf8"))
        return tree.root_node

    def extract_models(self, ast: Node) -> list[PrismaModel]:
        """Extract all model declarations from AST."""
        models = []

        # Find all model_block nodes (Prisma grammar v13 uses model_block, not model_declaration)
        for model_node in self._find_all(ast, "model_block"):
            model = self._parse_model(model_node)
            if model:
                models.append(model)

        return models

    def _parse_model(self, model_node: Node) -> PrismaModel | None:
        """Parse a model declaration."""
        # Get model name
        name = None
        fields = []
        indexes = []
        unique_constraints = []
        table_name = None

        for child in model_node.children:
            if child.type == "identifier" and name is None:
                name = self._get_node_text(child)

            elif child.type in ("{", "}", "model"):
                # Skip structural tokens
                continue
            else:
                # Process model fields and attributes directly (no statement_block in v13)
                if child.type == "model_field":
                    field = self._parse_field(child)
                    if field:
                        fields.append(field)
                elif child.type == "model_multi_attribute":
                    # v13 uses model_multi_attribute for @@index, @@unique, @@map, etc.
                    attr_text = self._get_node_text(child)
                    if "@@index" in attr_text:
                        index = self._parse_block_attribute(child)
                        if index:
                            indexes.append(index)
                    elif "@@unique" in attr_text:
                        unique = self._parse_block_attribute(child)
                        if unique:
                            unique_constraints.append(unique)
                    elif "@@map" in attr_text:
                        table_name = self._extract_table_name(child)

        if name:
            model = PrismaModel(
                name=name, fields=fields, indexes=indexes, unique_constraints=unique_constraints
            )
            # Store table_name as an attribute for later use
            model.table_name = table_name
            return model

        return None

    def _extract_table_name(self, attr_node: Node) -> str | None:
        """Extract table name from @@map(...) attribute."""
        # Look for string in arguments
        for child in attr_node.children:
            if child.type == "call_expression":
                for grandchild in child.children:
                    if grandchild.type == "arguments":
                        for arg_child in grandchild.children:
                            if arg_child.type == "string":
                                return self._get_node_text(arg_child).strip("\"'")
        return None

    def _parse_field(self, field_node: Node) -> PrismaField | None:
        """
        Parse a field declaration.

        Examples:
        - id Int @id @default(autoincrement())
        - email String @unique
        - name String?
        - posts Post[]
        """
        name = None
        field_type = None
        is_required = True
        is_list = False
        is_id = False
        is_unique = False
        has_default = False
        default_value = None
        relation_name = None
        attributes = []

        for child in field_node.children:
            if child.type == "identifier" and name is None:
                # First identifier is field name
                name = self._get_node_text(child)

            elif child.type == "field_type":
                # Field type (v13 uses field_type, which contains nullable_type or non_null_type)
                type_text = self._get_node_text(child)

                # Check for list and nullable
                is_list = "[]" in type_text
                is_required = "?" not in type_text

                # Extract the base type - strip ? but keep [] if it's a list
                if is_list:
                    field_type = type_text.replace("?", "")  # Keep []
                else:
                    field_type = type_text.rstrip("?")  # Remove optional marker

            elif child.type == "model_single_attribute":
                # Parse attributes like @id, @unique, @default(...) (v13 uses model_single_attribute)
                attr_text = self._get_node_text(child)
                attributes.append(attr_text)

                # Parse @relation
                if "@relation" in attr_text:
                    relation_name = self._extract_relation_name(child)

                if "@id" in attr_text:
                    is_id = True
                if "@unique" in attr_text:
                    is_unique = True
                if "@default" in attr_text:
                    has_default = True
                    default_value = self._extract_default_value(child)

        if name and field_type:
            return PrismaField(
                name=name,
                type=field_type,
                is_required=is_required,
                is_list=is_list,
                is_id=is_id,
                is_unique=is_unique,
                has_default=has_default,
                default_value=default_value,
                relation_name=relation_name,
                attributes=attributes,
            )

        return None

    def _extract_default_value(self, attr_node: Node) -> str | None:
        """Extract default value from @default(...) attribute."""
        # Look for apply_function (v13 uses apply_function for function calls)
        for child in attr_node.children:
            if child.type == "apply_function":
                # Get function name (e.g., autoincrement, now, uuid)
                func_text = self._get_node_text(child)
                if "(" in func_text:
                    return func_text.split("(")[0]
                return func_text
            elif child.type == "string":
                # String literal like "lead"
                return self._get_node_text(child).strip("\"'")

        return None

    def _extract_relation_name(self, attr_node: Node) -> str | None:
        """Extract relation name from @relation(...) attribute."""
        # In v13, look for string literals directly (they might not be nested in call_expression)
        for child in attr_node.children:
            if child.type == "(":
                # After opening paren, look for string
                continue
            elif child.type == "string":
                # Direct string child
                string_content = self._get_node_text(child)
                return string_content.strip("\"'")

        # Also check nested structure for complex cases
        for child in attr_node.children:
            for grandchild in child.children if hasattr(child, "children") else []:
                if grandchild.type == "string":
                    string_content = self._get_node_text(grandchild)
                    return string_content.strip("\"'")

        return None

    def extract_enums(self, ast: Node) -> list[PrismaEnum]:
        """Extract all enum declarations from AST."""
        enums = []

        # v13 uses enum_block, not enum_declaration
        for enum_node in self._find_all(ast, "enum_block"):
            enum = self._parse_enum(enum_node)
            if enum:
                enums.append(enum)

        return enums

    def _parse_enum(self, enum_node: Node) -> PrismaEnum | None:
        """Parse an enum declaration."""
        name = None
        values = []

        for child in enum_node.children:
            if child.type == "identifier":
                # In v13, enum identifiers are direct children (both name and values)
                if name is None:
                    # First identifier is the enum name
                    name = self._get_node_text(child)
                else:
                    # Subsequent identifiers are enum values
                    values.append(self._get_node_text(child))

        if name:
            return PrismaEnum(name=name, values=values)

        return None

    def _parse_block_attribute(self, attr_node: Node) -> dict | None:
        """Parse @@index or @@unique attributes."""
        fields = []

        # In v13, identifiers are direct children between [ and ]
        in_array = False
        for child in attr_node.children:
            if child.type == "[":
                in_array = True
            elif child.type == "]":
                in_array = False
            elif in_array and child.type == "identifier":
                fields.append(self._get_node_text(child))

        if fields:
            return {"fields": fields}

        return None

    def _find_all(self, node: Node, node_type: str) -> list[Node]:
        """Find all nodes of given type in tree."""
        results = []

        def _traverse(n: Node):
            if n.type == node_type:
                results.append(n)
            for child in n.children:
                _traverse(child)

        _traverse(node)
        return results

    def _get_node_text(self, node: Node) -> str:
        """Get text content of node."""
        return node.text.decode("utf8") if isinstance(node.text, bytes) else str(node.text)
