"""
Universal Pattern Detector - Detect common patterns across all languages

Your responsibility: Implement Patterns 1-3
- State Machine
- Soft Delete
- Audit Trail
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class DetectedPattern:
    """Represents a detected pattern"""

    name: str
    confidence: float
    evidence: List[str]
    language: str
    suggested_stdlib: str


class UniversalPatternDetector:
    """Detect patterns across all languages"""

    def __init__(self):
        self.patterns = {
            "state_machine": StateMachinePattern(),  # YOUR PATTERN
            "soft_delete": SoftDeletePattern(),  # YOUR PATTERN
            "audit_trail": AuditTrailPattern(),  # YOUR PATTERN
            "multi_tenant": None,  # Engineer B will implement
            "hierarchical": None,  # Engineer B will implement
            "versioning": None,  # Engineer B will implement
        }

    def detect(self, code: str, language: str) -> List[DetectedPattern]:
        """Detect all patterns in code"""
        detected = []

        for pattern_name, pattern_detector in self.patterns.items():
            if pattern_detector and pattern_detector.matches(code, language):
                detected.append(
                    DetectedPattern(
                        name=pattern_name,
                        confidence=pattern_detector.confidence,
                        evidence=pattern_detector.evidence,
                        language=language,
                        suggested_stdlib=pattern_detector.get_stdlib_pattern(),
                    )
                )

        return detected


class StateMachinePattern:
    """
    Detect state machine pattern

    Indicators:
    - Status/state field (enum or text)
    - Multiple transition methods (2+)
    - Status validation before transition
    - Status update in method

    Target Confidence: 85%+
    """

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        """Check if code implements state machine"""
        self.evidence = []
        self.confidence = 0.0

        indicators = self._get_indicators(language)

        # 1. Check for status/state field (30 points)
        has_status_field = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in indicators["field_patterns"]
        )

        if has_status_field:
            self.evidence.append("Has status/state field")
            self.confidence += 0.30

        # 2. Check for transition methods (40 points for 2+, 50 for 4+)
        transition_count = 0
        for pattern in indicators["transition_patterns"]:
            matches = re.findall(pattern, code, re.IGNORECASE | re.DOTALL)
            transition_count += len(matches)

        if transition_count >= 2:
            self.evidence.append(f"Found {transition_count} status transitions")
            self.confidence += 0.40
            if transition_count >= 4:
                self.confidence += 0.10

        # 3. Check for validation (20 points)
        has_validation = any(pattern in code for pattern in indicators["validation_patterns"])

        if has_validation:
            self.evidence.append("Has status validation before transitions")
            self.confidence += 0.20

        # Must have at least field + transitions to be considered state machine
        return self.confidence >= 0.60

    def _get_indicators(self, language: str) -> Dict[str, List[str]]:
        """Get language-specific indicators"""
        indicators = {
            "rust": {
                "field_patterns": [
                    r"status:\s*\w*Status",
                    r"state:\s*\w*State",
                    r"status:\s*String",
                ],
                "transition_patterns": [
                    r"self\.status\s*=\s*",
                ],
                "validation_patterns": [
                    "self.status !=",
                    "self.status ==",
                    "if self.status",
                ],
            },
            "python": {
                "field_patterns": [
                    r"self\.status\s*=",
                    r"status:\s*str",
                    r"status:\s*Status",
                ],
                "transition_patterns": [
                    r'self\.status\s*=\s*["\']',
                    r"self\.status\s*=\s*Status\.",
                    r"self\.status\s*=\s*\w+\.",
                ],
                "validation_patterns": [
                    "if self.status",
                    "self.status !=",
                    "self.status ==",
                    "self.status not in",
                ],
            },
            "java": {
                "field_patterns": [
                    r"private\s+String\s+status",
                    r"private\s+\w*Status\s+status",
                ],
                "transition_patterns": [
                    r"this\.status\s*=\s*",
                    r"setStatus\(",
                ],
                "validation_patterns": [
                    "if (status",
                    "if (this.status",
                    '.equals("',
                ],
            },
            "sql": {
                "field_patterns": [
                    r"status\s+TEXT",
                    r"status\s+VARCHAR",
                ],
                "transition_patterns": [
                    r"UPDATE\s+\w+\s+SET\s+status\s*=",
                ],
                "validation_patterns": [
                    "SELECT status",
                    "WHERE status =",
                    "WHERE status !=",
                    "IF v_status",
                ],
            },
        }

        return indicators.get(
            language,
            {
                "field_patterns": [r"status", r"state"],
                "transition_patterns": [r"status\s*="],
                "validation_patterns": ["status", "state"],
            },
        )

    def get_stdlib_pattern(self) -> str:
        return "state_machine/transition"


class SoftDeletePattern:
    """
    Detect soft delete pattern

    Indicators:
    - deleted_at timestamp field (50 points)
    - UPDATE instead of DELETE (30 points)
    - Filter deleted records (20 points)

    Target Confidence: 94%+
    """

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        """Check if code uses soft delete"""
        self.evidence = []
        self.confidence = 0.0

        # 1. Check for deleted_at field (50 points - CRITICAL)
        deleted_patterns = [
            r"deleted_at.*timestamp",
            r"deleted_at.*DateTime",
            r"deleted_at.*Option",
            r"deleted_at.*Optional",
            r"deleted_at\s*TIMESTAMPTZ",
            r"deleted_at:\s*datetime",
        ]

        has_deleted_field = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in deleted_patterns
        )

        if has_deleted_field:
            self.evidence.append("Has deleted_at timestamp field")
            self.confidence += 0.50

        # 2. Check for soft delete implementation (30 points)
        soft_delete_patterns = [
            r"UPDATE.*SET\s+deleted_at",
            r"deleted_at\s*=.*now\(\)",
            r"deleted_at\s*=.*NOW",
            r"\.deleted_at\s*=\s*",
            r"set.*deleted_at.*Some",
        ]

        has_soft_delete = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in soft_delete_patterns
        )

        if has_soft_delete:
            self.evidence.append("Updates deleted_at instead of hard delete")
            self.confidence += 0.30

        # 3. Check for filtering deleted records (20 points)
        filter_patterns = [
            r"WHERE.*deleted_at\s+IS\s+NULL",
            r"filter.*deleted_at.*is_null",
            r"deleted_at\.is_\(None\)",
            r"deleted_at\s+IS\s+NULL",
        ]

        has_filter = any(re.search(pattern, code, re.IGNORECASE) for pattern in filter_patterns)

        if has_filter:
            self.evidence.append("Filters out deleted records in queries")
            self.confidence += 0.20

        # Check for restore functionality (bonus)
        restore_patterns = [
            r"deleted_at\s*=\s*NULL",
            r"deleted_at\s*=\s*None",
            r"restore",
        ]

        has_restore = any(re.search(pattern, code, re.IGNORECASE) for pattern in restore_patterns)

        if has_restore:
            self.evidence.append("Has restore/undelete functionality")
            self.confidence = min(0.95, self.confidence + 0.05)

        # Deleted field is mandatory
        return has_deleted_field and self.confidence >= 0.50

    def get_stdlib_pattern(self) -> str:
        return "crud/soft_delete"


class AuditTrailPattern:
    """
    Detect audit trail pattern

    Indicators:
    - created_at, created_by (25 points each)
    - updated_at, updated_by (25 points each)

    Target Confidence: 89%+
    """

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        """Check if code has audit trail"""
        self.evidence = []
        self.confidence = 0.0

        # Check for each audit field (25 points each)
        audit_fields = {
            "created_at": [r"\bcreated_at\b", r"createdAt"],
            "created_by": [r"\bcreated_by\b", r"createdBy"],
            "updated_at": [r"\bupdated_at\b", r"updatedAt"],
            "updated_by": [r"\bupdated_by\b", r"updatedBy"],
        }

        found_fields = []

        for field_name, patterns in audit_fields.items():
            if any(re.search(pattern, code, re.IGNORECASE) for pattern in patterns):
                found_fields.append(field_name)
                self.confidence += 0.25

        if found_fields:
            self.evidence.append(f"Has audit fields: {', '.join(found_fields)}")

        # Check for automatic timestamp updates (bonus)
        auto_update_patterns = [
            r"DEFAULT NOW\(\)",
            r"updated_at\s*=\s*NOW\(\)",
            r"updated_at\s*=.*now\(\)",
            r"TRIGGER.*updated_at",
        ]

        if any(re.search(pattern, code, re.IGNORECASE) for pattern in auto_update_patterns):
            self.evidence.append("Has automatic timestamp updates")
            self.confidence = min(0.95, self.confidence + 0.10)

        # Need at least 2 audit fields
        return len(found_fields) >= 2 and self.confidence >= 0.50

    def get_stdlib_pattern(self) -> str:
        return "audit/full_trail"
