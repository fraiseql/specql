"""
CTE Parser: Dedicated parser for Common Table Expressions

Handles parsing of WITH clauses, recursive CTEs, and nested CTEs
with proper parenthesis matching and error handling.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from src.core.ast_models import ActionStep


@dataclass
class CTEInfo:
    """Information about a parsed CTE"""

    name: str
    query: str
    is_recursive: bool = False
    dependencies: List[str] = field(default_factory=list)  # Other CTEs this one references


class CTEParser:
    """Dedicated parser for Common Table Expressions"""

    def __init__(self):
        self.cte_stack = []
        self.depth_tracker = {}
        self.max_nesting_depth = 10  # Prevent infinite recursion

    def parse(self, sql: str) -> List[ActionStep]:
        """
        Parse CTEs with arbitrary nesting depth

        Args:
            sql: SQL containing WITH clauses

        Returns:
            List of ActionStep objects representing CTEs

        Raises:
            ValueError: If CTE parsing fails or exceeds depth limits
        """
        if not sql or not isinstance(sql, str):
            raise ValueError("Invalid SQL input: must be a non-empty string")

        if "WITH" not in sql.upper():
            return []  # No CTEs to parse

        try:
            ctes = []

            # Find all WITH clauses and parse them
            with_clauses = self._find_with_clauses(sql)

            if not with_clauses:
                return []  # No WITH clauses found

            for clause_info in with_clauses:
                cte_steps = self._parse_single_cte(clause_info, sql)
                ctes.extend(cte_steps)

            return ctes

        except Exception as e:
            # Handle different types of exceptions with better error messages
            error_type = type(e).__name__

            if isinstance(e, RecursionError):
                raise ValueError(
                    f"CTE nesting too deep (max: {self.max_nesting_depth} levels). "
                    "Consider simplifying the query or splitting into multiple functions."
                ) from e
            else:
                # For all other exceptions, provide detailed context
                raise ValueError(
                    f"Failed to parse CTE: {str(e)}\n"
                    f"Error type: {error_type}\n"
                    f"SQL context: {sql[:300]}..."
                ) from e

    def _find_with_clauses(self, sql: str) -> List[Dict[str, Any]]:
        """
        Find all WITH clauses in the SQL

        Returns list of dicts with 'start_pos', 'keyword', 'content_start'
        """
        clauses = []

        # Find all WITH keywords (case insensitive)
        with_pattern = r"\bWITH\b"
        matches = list(re.finditer(with_pattern, sql, re.IGNORECASE))

        for match in matches:
            start_pos = match.start()
            # Check if this is followed by RECURSIVE
            after_with = sql[start_pos : start_pos + 50]  # Look ahead
            is_recursive = "RECURSIVE" in after_with.upper()

            clauses.append(
                {"start_pos": start_pos, "is_recursive": is_recursive, "content_start": match.end()}
            )

        return clauses

    def _parse_single_cte(self, clause_info: Dict[str, Any], sql: str) -> List[ActionStep]:
        """Parse a single CTE clause"""
        ctes = []
        pos = clause_info["content_start"]

        # Skip RECURSIVE if present
        if clause_info["is_recursive"]:
            recursive_match = re.search(r"\bRECURSIVE\b", sql[pos : pos + 20], re.IGNORECASE)
            if recursive_match:
                pos += recursive_match.end()

        # Parse CTE definitions until we hit the main query
        while pos < len(sql):
            # Look for cte_name AS (
            cte_match = re.search(r"(\w+)\s+AS\s*\(", sql[pos:], re.IGNORECASE)
            if not cte_match:
                break

            cte_name = cte_match.group(1)
            cte_start = pos + cte_match.end() - 1  # Position after "AS ("

            # Find matching closing parenthesis
            query_content, end_pos = self._extract_parenthesized_content(sql, cte_start)
            if query_content is None:
                break

            # Check for nested CTEs
            if "WITH" in query_content.upper():
                # Parse nested CTEs recursively
                nested_ctes = self.parse(query_content)
                ctes.extend(nested_ctes)

            # Create CTE step
            ctes.append(ActionStep(type="cte", cte_name=cte_name, cte_query=query_content.strip()))

            pos = end_pos

            # Check for comma (more CTEs) or end of WITH clause
            remaining = sql[pos:].strip()
            if remaining.startswith(","):
                pos += remaining.find(",") + 1
            elif (
                remaining.upper().startswith("SELECT")
                or remaining.upper().startswith("INSERT")
                or remaining.upper().startswith("UPDATE")
            ):
                # End of WITH clause, main query starts
                break
            else:
                # Unexpected content
                break

        return ctes

    def _extract_parenthesized_content(self, sql: str, start_pos: int) -> tuple[Optional[str], int]:
        """
        Extract content within matching parentheses

        Returns:
            (content, end_position) or (None, -1) if no matching parens
        """
        if start_pos >= len(sql) or sql[start_pos] != "(":
            return None, -1

        paren_depth = 0
        content_start = start_pos + 1  # Skip opening paren

        for i in range(start_pos, len(sql)):
            if sql[i] == "(":
                paren_depth += 1
            elif sql[i] == ")":
                paren_depth -= 1
                if paren_depth == 0:
                    # Found matching closing paren
                    content = sql[content_start:i]
                    return content, i + 1

        # No matching closing paren found
        return None, -1

    def detect_patterns(self, ctes: List[ActionStep]) -> List[str]:
        """
        Detect patterns in parsed CTEs

        Args:
            ctes: List of CTE ActionSteps

        Returns:
            List of detected pattern names
        """
        patterns = []

        for cte in ctes:
            if not hasattr(cte, "cte_query") or not cte.cte_query:
                continue

            query = cte.cte_query.upper()

            # Recursive hierarchy pattern
            if "UNION" in query and any(kw in query for kw in ["PARENT", "CHILD", "LEVEL"]):
                if "recursive_hierarchy" not in patterns:
                    patterns.append("recursive_hierarchy")

            # Tree traversal pattern
            if "CONNECT BY" in query or ("START WITH" in query and "CONNECT BY" in query):
                if "tree_traversal" not in patterns:
                    patterns.append("tree_traversal")

            # Materialized path pattern
            if "PATH" in query and ("CONCAT" in query or "||" in query):
                if "materialized_path" not in patterns:
                    patterns.append("materialized_path")

        return patterns
