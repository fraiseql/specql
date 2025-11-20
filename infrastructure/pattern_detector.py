"""
Pattern Detector - Detect common patterns in Django models
"""

import ast
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Represents a detected pattern"""

    name: str
    confidence: float
    fields: List[str]
    explanation: str = ""


class PatternDetector:
    """Detect patterns in Django model code"""

    def detect(self, source_code: str, min_confidence: float = 0.7) -> List[Pattern]:
        """Detect patterns in Django model code"""
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            logger.warning("Failed to parse source code as Python AST")
            return []

        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Extract field information
                fields = self._extract_field_info(node)

                # Check for patterns
                patterns.extend(self._detect_audit_trail(fields))
                patterns.extend(self._detect_soft_delete(fields))
                patterns.extend(self._detect_state_machine(fields))

        # Filter by confidence
        return [p for p in patterns if p.confidence >= min_confidence]

    def _detect_audit_trail(self, fields: List[dict]) -> List[Pattern]:
        """Detect audit trail pattern"""
        field_names = [f["name"] for f in fields]

        # Pattern: created_at + updated_at
        has_created = any(name in ["created_at", "created", "date_created"] for name in field_names)
        has_updated = any(
            name in ["updated_at", "updated", "date_updated", "modified_at"] for name in field_names
        )

        if has_created and has_updated:
            return [
                Pattern(
                    name="audit-trail",
                    confidence=1.0,
                    fields=["created_at", "updated_at"],
                    explanation="Detected created_at and updated_at fields indicating audit trail pattern",
                )
            ]

        # Partial match - only created_at
        if has_created:
            return [
                Pattern(
                    name="audit-trail",
                    confidence=0.6,
                    fields=["created_at"],
                    explanation="Detected created_at field, may be part of audit trail pattern",
                )
            ]

        return []

    def _detect_soft_delete(self, fields: List[dict]) -> List[Pattern]:
        """Detect soft delete pattern"""
        field_names = [f["name"] for f in fields]

        # Pattern: deleted_at or is_deleted
        has_deleted_at = "deleted_at" in field_names
        has_is_deleted = "is_deleted" in field_names

        if has_deleted_at or has_is_deleted:
            confidence = 1.0 if has_deleted_at else 0.8
            fields_found = [name for name in ["deleted_at", "is_deleted"] if name in field_names]
            return [
                Pattern(
                    name="soft-delete",
                    confidence=confidence,
                    fields=fields_found,
                    explanation=f"Detected {', '.join(fields_found)} indicating soft delete pattern",
                )
            ]

        return []

    def _detect_state_machine(self, fields: List[dict]) -> List[Pattern]:
        """Detect state machine pattern"""
        for field in fields:
            # Look for CharField with choices
            if field.get("type") == "CharField" and field.get("choices"):
                num_states = len(field["choices"])

                # State machine if 3+ states
                if num_states >= 3:
                    confidence = 0.9
                    return [
                        Pattern(
                            name="state-machine",
                            confidence=confidence,
                            fields=[field["name"]],
                            explanation=f"Detected {field['name']} with {num_states} choices indicating state machine pattern",
                        )
                    ]

        return []

    def _extract_field_info(self, class_node: ast.ClassDef) -> List[dict]:
        """Extract field information for pattern detection"""
        fields = []

        for node in class_node.body:
            if isinstance(node, ast.Assign):
                field_info = self._parse_field(node)
                if field_info:
                    fields.append(field_info)

        return fields

    def _parse_field(self, assign_node: ast.Assign) -> Optional[dict]:
        """Parse field assignment to extract metadata"""
        # Extract field name
        if not assign_node.targets:
            return None

        target = assign_node.targets[0]
        if not isinstance(target, ast.Name):
            return None

        field_name = target.id

        # Extract field type and options
        if isinstance(assign_node.value, ast.Call):
            field_type = self._get_field_type(assign_node.value)
            choices = self._extract_choices(assign_node.value)

            return {"name": field_name, "type": field_type, "choices": choices}

        return None

    def _get_field_type(self, call_node: ast.Call) -> str:
        """Get Django field type from call node"""
        if isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        elif isinstance(call_node.func, ast.Name):
            return call_node.func.id
        return "Unknown"

    def _extract_choices(self, call_node: ast.Call) -> Optional[List]:
        """Extract choices from CharField"""
        for keyword in call_node.keywords:
            if keyword.arg == "choices":
                # Parse choices list
                if isinstance(keyword.value, ast.List):
                    return keyword.value.elts
        return None
