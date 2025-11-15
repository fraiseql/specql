"""
Pattern Detector

Detect SpecQL patterns in parsed entities:
- Trinity Pattern (pk_*, id, identifier)
- Audit Fields (created_at, updated_at, deleted_at)
- Deduplication Pattern (dedup_key, dedup_hash, is_unique)
- Hierarchical Entities (parent references)
"""

from typing import Dict, Any
from src.core.universal_ast import UniversalEntity, UniversalField


class PatternDetector:
    """Detect SpecQL patterns in entities"""

    def detect_patterns_from_ddl(self, ddl: str) -> Dict[str, Any]:
        """
        Detect patterns directly from DDL before parsing

        This allows pattern detection on raw columns before filtering
        """
        # Extract column names from DDL
        import re

        pattern = r"CREATE\s+TABLE\s+[^(]+\((.*)\)"
        match = re.search(pattern, ddl, re.IGNORECASE | re.DOTALL)

        if not match:
            return {"confidence": 0.0}

        columns_section = match.group(1)
        column_names = []

        # Simple extraction of column names
        for line in columns_section.split(","):
            line = line.strip()
            if line and not line.upper().startswith(
                ("PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "CONSTRAINT")
            ):
                parts = line.split()
                if parts:
                    column_names.append(parts[0].lower())

        # Create mock entity for pattern detection
        from src.core.universal_ast import UniversalEntity, FieldType

        mock_entity = UniversalEntity(
            name="temp",
            schema="temp",
            fields=[
                UniversalField(name=name, type=FieldType.TEXT) for name in column_names
            ],
            actions=[],
        )

        return self.detect_patterns(mock_entity)

    def detect_patterns(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect all patterns in an entity

        Returns:
            Dict with pattern detection results and confidence score
        """
        patterns = {
            "trinity": self._detect_trinity_pattern(entity),
            "audit": self._detect_audit_fields(entity),
            "deduplication": self._detect_deduplication(entity),
            "hierarchical": self._detect_hierarchical(entity),
            "soft_delete": self._detect_soft_delete(entity),
        }

        # Calculate overall confidence
        confidence = self._calculate_confidence(patterns)
        patterns["confidence"] = confidence

        return patterns

    def _detect_trinity_pattern(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect Trinity Pattern fields

        Trinity Pattern:
            - pk_* (INTEGER PRIMARY KEY)
            - id (UUID)
            - identifier (TEXT)
        """
        field_names = [f.name.lower() for f in entity.fields]

        # Look for pk_* field
        has_pk = any(name.startswith("pk_") for name in field_names)

        # Look for id field
        has_id = "id" in field_names

        # Look for identifier field
        has_identifier = "identifier" in field_names

        # Trinity is complete if has all three
        is_complete = has_pk and has_id and has_identifier

        # Confidence based on how many parts present
        confidence = sum([has_pk, has_id, has_identifier]) / 3.0

        return {
            "detected": is_complete,
            "has_pk": has_pk,
            "has_id": has_id,
            "has_identifier": has_identifier,
            "confidence": confidence,
        }

    def _detect_audit_fields(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect audit fields

        Audit Fields:
            - created_at (TIMESTAMPTZ)
            - updated_at (TIMESTAMPTZ)
            - deleted_at (TIMESTAMPTZ, nullable)
        """
        field_names = [f.name.lower() for f in entity.fields]

        has_created_at = "created_at" in field_names
        has_updated_at = "updated_at" in field_names
        has_deleted_at = "deleted_at" in field_names

        # Audit is complete if has created_at and updated_at
        # deleted_at is optional (soft delete)
        is_complete = has_created_at and has_updated_at

        # Confidence
        confidence = sum([has_created_at, has_updated_at]) / 2.0

        return {
            "detected": is_complete,
            "has_created_at": has_created_at,
            "has_updated_at": has_updated_at,
            "has_deleted_at": has_deleted_at,
            "confidence": confidence,
        }

    def _detect_deduplication(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect deduplication pattern

        Deduplication Fields:
            - dedup_key (TEXT)
            - dedup_hash (TEXT)
            - is_unique (BOOLEAN)
        """
        field_names = [f.name.lower() for f in entity.fields]

        has_dedup_key = "dedup_key" in field_names
        has_dedup_hash = "dedup_hash" in field_names
        has_is_unique = "is_unique" in field_names

        is_complete = has_dedup_key and has_dedup_hash and has_is_unique

        confidence = sum([has_dedup_key, has_dedup_hash, has_is_unique]) / 3.0

        return {
            "detected": is_complete,
            "has_dedup_key": has_dedup_key,
            "has_dedup_hash": has_dedup_hash,
            "has_is_unique": has_is_unique,
            "confidence": confidence,
        }

    def _detect_hierarchical(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect hierarchical entity (self-referential)

        Looks for:
            - fk_parent, parent_id, or similar field
            - Reference to same entity
        """
        # Look for self-reference fields
        parent_field_patterns = [
            "fk_parent",
            "parent_id",
            f"fk_{entity.name.lower()}_parent",
        ]

        field_names = [f.name.lower() for f in entity.fields]

        has_parent_field = any(
            pattern in field_names for pattern in parent_field_patterns
        )

        return {
            "detected": has_parent_field,
            "parent_field": next(
                (name for name in field_names if name in parent_field_patterns), None
            ),
            "confidence": 1.0 if has_parent_field else 0.0,
        }

    def _detect_soft_delete(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect soft delete pattern

        Soft Delete:
            - deleted_at field (nullable timestamp)
        """
        field_names = [f.name.lower() for f in entity.fields]

        has_deleted_at = "deleted_at" in field_names

        return {
            "detected": has_deleted_at,
            "confidence": 1.0 if has_deleted_at else 0.0,
        }

    def _calculate_confidence(self, patterns: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score

        Weighted average of pattern confidences:
            - Trinity: 40% weight (most important)
            - Audit: 30% weight
            - Deduplication: 15% weight
            - Hierarchical: 10% weight
            - Soft Delete: 5% weight
        """
        weights = {
            "trinity": 0.40,
            "audit": 0.30,
            "deduplication": 0.15,
            "hierarchical": 0.10,
            "soft_delete": 0.05,
        }

        weighted_sum = 0.0
        for pattern_name, weight in weights.items():
            pattern_data = patterns.get(pattern_name, {})
            pattern_confidence = pattern_data.get("confidence", 0.0)
            weighted_sum += weight * pattern_confidence

        return weighted_sum
