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
            (r"#.*$", Comment.Single),
            # Entity-level keywords
            (
                r"^(entity|schema|description|identifier_template)(:)",
                bygroups(Keyword.Namespace, Punctuation),
            ),
            # Section keywords
            (
                r"^(fields|actions|views|patterns)(:)",
                bygroups(Keyword.Declaration, Punctuation),
            ),
            # Field types
            (
                r"\b(text|integer|float|boolean|date|timestamp|uuid|json|enum|ref|list)\b",
                Keyword.Type,
            ),
            # Action step keywords
            (
                r"\b(validate|if|then|else|update|insert|delete|call|notify|foreach|return)\b",
                Keyword.Reserved,
            ),
            # Pattern names
            (r"@(audit_trail|soft_delete|state_machine|multi_tenant)", Name.Decorator),
            # Strings
            (r'"[^"]*"', String.Double),
            (r"'[^']*'", String.Single),
            # Numbers
            (r"\b\d+\b", Number.Integer),
            # Operators
            (r"[=<>!]+", Operator),
            # Delimiters
            (r"[:{}[\],]", Punctuation),
            # Field names
            (r"\b[a-z_][a-z0-9_]*\b", Name.Variable),
            # Entity names (capitalized)
            (r"\b[A-Z][a-zA-Z0-9]*\b", Name.Class),
            # Whitespace
            (r"\s+", Text),
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
