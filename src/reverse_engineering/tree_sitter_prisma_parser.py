"""Tree-sitter based Prisma schema parser."""

from dataclasses import dataclass, field
from typing import List, Optional, Any, TYPE_CHECKING

# Conditional imports for optional dependencies
try:
    import tree_sitter_prisma as ts_prisma
    from tree_sitter import Language, Parser, Node

    HAS_TREE_SITTER_PRISMA = True
except ImportError:
    HAS_TREE_SITTER_PRISMA = False
    ts_prisma = None
    if not TYPE_CHECKING:
        # Create stub types for when the dependency is missing
        Language = Any  # type: ignore
        Parser = Any  # type: ignore
        Node = Any  # type: ignore


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
    default_value: Optional[str] = None
    relation_name: Optional[str] = None
    attributes: List[str] = field(default_factory=list)


@dataclass
class PrismaModel:
    """Represents a Prisma model."""

    name: str
    fields: List[PrismaField] = field(default_factory=list)
    indexes: List[dict] = field(default_factory=list)
    unique_constraints: List[dict] = field(default_factory=list)
    table_name: Optional[str] = None


@dataclass
class PrismaEnum:
    """Represents a Prisma enum."""

    name: str
    values: List[str] = field(default_factory=list)


class TreeSitterPrismaParser:
    """Parse Prisma schema files using tree-sitter."""

    def __init__(self):
        """Initialize tree-sitter parser with Prisma grammar."""
        if not HAS_TREE_SITTER_PRISMA:
            raise ImportError(
                "tree-sitter-prisma is required for Prisma parsing. "
                "Install with: pip install specql[reverse]"
            )
        self.language = Language(ts_prisma.language())
        self.parser = Parser(self.language)

    def parse(self, schema: str) -> Node:
        """Parse Prisma schema into AST."""
        tree = self.parser.parse(bytes(schema, "utf8"))
        return tree.root_node

    def extract_models(self, ast: Node) -> List[PrismaModel]:
        """Extract all model declarations from AST."""
        models = []

        # Find all model_declaration nodes
        for model_node in self._find_all(ast, "model_declaration"):
            model = self._parse_model(model_node)
            if model:
                models.append(model)

        return models

    def _parse_model(self, model_node: Node) -> Optional[PrismaModel]:
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

            elif child.type == "statement_block":
                # Extract fields and block attributes from model body
                fields, indexes, unique_constraints, table_name = self._parse_model_body(child)

        if name:
            model = PrismaModel(
                name=name, fields=fields, indexes=indexes, unique_constraints=unique_constraints
            )
            # Store table_name as an attribute for later use
            model.table_name = table_name
            return model

        return None

    def _parse_model_body(
        self, body_node: Node
    ) -> tuple[List[PrismaField], List[dict], List[dict], Optional[str]]:
        """Parse fields and block attributes from model body."""
        fields = []
        indexes = []
        unique_constraints = []
        table_name = None

        for child in body_node.children:
            if child.type == "column_declaration":
                field = self._parse_field(child)
                if field:
                    fields.append(field)

            elif child.type == "block_attribute_declaration":
                # Parse @@index, @@unique, @@map, etc.
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

        return fields, indexes, unique_constraints, table_name

    def _extract_table_name(self, attr_node: Node) -> Optional[str]:
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

    def _parse_field(self, field_node: Node) -> Optional[PrismaField]:
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

            elif child.type == "column_type":
                # Field type (may include ?, [])
                type_text = self._get_node_text(child)

                # Preserve [] for list types, only strip ?
                field_type = type_text.rstrip("?")

                is_required = "?" not in type_text
                is_list = "[]" in type_text

            elif child.type == "attribute":
                # Parse attributes like @id, @unique, @default(...)
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

    def _extract_default_value(self, attr_node: Node) -> Optional[str]:
        """Extract default value from @default(...) attribute."""
        # Look for arguments in the call expression
        for child in attr_node.children:
            if child.type == "call_expression":
                for grandchild in child.children:
                    if grandchild.type == "arguments":
                        for arg_child in grandchild.children:
                            if arg_child.type == "string":
                                # String literal like "lead"
                                return self._get_node_text(arg_child).strip("\"'")
                            elif arg_child.type == "function_call":
                                # Function call like now()
                                func_name = self._get_node_text(arg_child)
                                # Extract just the function name
                                if "(" in func_name:
                                    return func_name.split("(")[0]
                                return func_name

        return None

    def _extract_relation_name(self, attr_node: Node) -> Optional[str]:
        """Extract relation name from @relation(...) attribute."""
        # Look for string node in the arguments
        for child in attr_node.children:
            if child.type == "call_expression":
                for grandchild in child.children:
                    if grandchild.type == "arguments":
                        for arg_child in grandchild.children:
                            if arg_child.type == "string":
                                # Remove quotes
                                string_content = self._get_node_text(arg_child)
                                return string_content.strip("\"'")
                            elif arg_child.type == "type_expression":
                                # For named parameters, we might not have a simple relation name
                                # For now, skip complex relations
                                pass

        return None

    def extract_enums(self, ast: Node) -> List[PrismaEnum]:
        """Extract all enum declarations from AST."""
        enums = []

        for enum_node in self._find_all(ast, "enum_declaration"):
            enum = self._parse_enum(enum_node)
            if enum:
                enums.append(enum)

        return enums

    def _parse_enum(self, enum_node: Node) -> Optional[PrismaEnum]:
        """Parse an enum declaration."""
        name = None
        values = []

        for child in enum_node.children:
            if child.type == "identifier":
                name = self._get_node_text(child)

            elif child.type == "enum_block":
                # Extract enum values
                values = self._parse_enum_body(child)

        if name:
            return PrismaEnum(name=name, values=values)

        return None

    def _parse_enum_body(self, body_node: Node) -> List[str]:
        """Parse enum values from enum body."""
        values = []

        for child in body_node.children:
            if child.type == "enumeral":
                # Extract identifier from enumeral
                for grandchild in child.children:
                    if grandchild.type == "identifier":
                        values.append(self._get_node_text(grandchild))

        return values

    def _parse_block_attribute(self, attr_node: Node) -> Optional[dict]:
        """Parse @@index or @@unique attributes."""
        fields = []

        # Find the arguments node and extract identifiers from array
        for child in attr_node.children:
            if child.type == "call_expression":
                for grandchild in child.children:
                    if grandchild.type == "arguments":
                        for arg_child in grandchild.children:
                            if arg_child.type == "array":
                                for array_child in arg_child.children:
                                    if array_child.type == "identifier":
                                        fields.append(self._get_node_text(array_child))

        if fields:
            return {"fields": fields}

        return None

    def _find_all(self, node: Node, node_type: str) -> List[Node]:
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
