"""
Custom syntax highlighting for SpecQL YAML

Uses Pygments to provide rich syntax highlighting in the interactive CLI
"""

# ruff: noqa: F403,F405
from rich.syntax import Syntax
from pygments.lexer import RegexLexer, bygroups
from pygments.token import *


class SpecQLLexer(RegexLexer):
    """
    Custom Pygments lexer for SpecQL YAML

    Highlights:
    - Entity keywords (entity, schema, fields, actions)
    - Field types (text, integer, ref, enum)
    - Step keywords (validate, update, insert, if)
    - Patterns
    """

    name = "SpecQL"
    aliases = ["specql", "specql-yaml"]
    filenames = ["*.specql.yaml", "*.specql"]

    tokens = {
        "root": [
            # Comments
            (r"#.*$", Comment.Single),  # type: ignore
            # Entity-level keywords
            (
                r"^(entity|schema|description|identifier_template)(:)",
                bygroups(Keyword.Namespace, Punctuation),  # type: ignore
            ),
            # Section keywords
            (
                r"^(fields|actions|views|patterns)(:)",
                bygroups(Keyword.Declaration, Punctuation),  # type: ignore
            ),
            # Field types
            (
                r"\b(text|integer|float|boolean|date|timestamp|uuid|json|enum|ref|list)\b",
                Keyword.Type,  # type: ignore
            ),
            # Action step keywords
            (
                r"\b(validate|if|then|else|update|insert|delete|call|notify|foreach|return)\b",
                Keyword.Reserved,  # type: ignore
            ),
            # Pattern names
            (r"@(audit_trail|soft_delete|state_machine|multi_tenant)", Name.Decorator),  # type: ignore
            # Strings
            (r'"[^"]*"', String.Double),  # type: ignore
            (r"'[^']*'", String.Single),  # type: ignore
            # Numbers
            (r"\b\d+\b", Number.Integer),  # type: ignore
            # Operators
            (r"[=<>!]+", Operator),  # type: ignore
            # Delimiters
            (r"[:{}[\],]", Punctuation),  # type: ignore
            # Field names
            (r"\b[a-z_][a-z0-9_]*\b", Name.Variable),  # type: ignore
            # Entity names (capitalized)
            (r"\b[A-Z][a-zA-Z0-9]*\b", Name.Class),  # type: ignore
            # Whitespace
            (r"\s+", Text),  # type: ignore
        ],
    }


def highlight_specql(code: str, theme: str = "monokai") -> Syntax:
    """
    Highlight SpecQL YAML code

    Args:
        code: SpecQL YAML text
        theme: Pygments theme name

    Returns:
        Rich Syntax object
    """
    return Syntax(
        code,
        lexer=SpecQLLexer(),
        theme=theme,
        line_numbers=True,
        word_wrap=True,
        indent_guides=True,
    )
