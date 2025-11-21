"""
Audit Trail Detector

Detects audit trail patterns (created_at/updated_at/deleted_at) and soft delete patterns.
"""

from dataclasses import dataclass
from typing import List

from .table_parser import ParsedTable


@dataclass
class AuditTrailResult:
    """Result of audit trail detection."""

    has_audit_trail: bool
    has_soft_delete: bool
    audit_fields: List[str]
    confidence: float


class AuditTrailDetector:
    """Detects audit trail patterns in tables."""

    AUDIT_PATTERNS = {
        "created_at": ["created_at", "created_date", "create_time"],
        "created_by": ["created_by", "creator_id", "created_by_user"],
        "updated_at": ["updated_at", "modified_at", "last_modified"],
        "updated_by": ["updated_by", "modifier_id", "modified_by_user"],
        "deleted_at": ["deleted_at", "removed_at", "deletion_time"],
        "deleted_by": ["deleted_by", "deleter_id", "deleted_by_user"],
    }

    def detect(self, table: ParsedTable) -> AuditTrailResult:
        """Detect audit trail patterns in a table."""
        audit_fields = []
        confidence = 0.0

        # Check for each audit field pattern
        for canonical_name, patterns in self.AUDIT_PATTERNS.items():
            for column in table.columns:
                if column.name in patterns:
                    audit_fields.append(column.name)
                    break

        # Calculate confidence based on fields present
        total_possible_fields = len(self.AUDIT_PATTERNS)
        fields_present = len(set(audit_fields))
        confidence = fields_present / total_possible_fields

        # Determine if we have a full audit trail
        has_audit_trail = confidence >= 0.5  # At least 3 out of 6 fields

        # Check for soft delete (deleted_at field)
        has_soft_delete = any(
            col.name in self.AUDIT_PATTERNS["deleted_at"] for col in table.columns
        )

        return AuditTrailResult(
            has_audit_trail=has_audit_trail,
            has_soft_delete=has_soft_delete,
            audit_fields=audit_fields,
            confidence=confidence,
        )
