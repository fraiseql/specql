"""
Trinity Pattern Detector

Detects SpecQL Trinity pattern fields (id, pk_*, identifier) and classifies
business fields vs. technical fields.
"""

from dataclasses import dataclass

from .table_parser import ParsedTable


@dataclass
class TrinityDetectionResult:
    """Result of Trinity pattern detection."""

    has_trinity_pattern: bool
    id_field: str | None  # INTEGER IDENTITY field
    pk_field: str | None  # UUID pk_* field
    identifier_field: str | None  # TEXT identifier field
    audit_fields: list[str]  # created_at, updated_at, etc.
    business_fields: list[str]  # Everything else


class TrinityPatternDetector:
    """Detects Trinity pattern in parsed tables."""

    AUDIT_FIELDS = {
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "deleted_at",
        "deleted_by",
    }

    def detect(self, parsed_table: ParsedTable) -> TrinityDetectionResult:
        """Detect Trinity pattern fields in a parsed table."""
        # Detect id field (INTEGER PRIMARY KEY)
        id_field = self._detect_id_field(parsed_table)

        # Detect pk_* field (UUID with pk_ prefix)
        pk_field = self._detect_pk_field(parsed_table)

        # Detect identifier field (TEXT, often unique)
        identifier_field = self._detect_identifier_field(parsed_table)

        # Detect audit fields
        audit_fields = self._detect_audit_fields(parsed_table)

        # Classify remaining fields as business fields
        business_fields = self._get_business_fields(
            parsed_table, id_field, pk_field, identifier_field, audit_fields
        )

        has_trinity_pattern = (
            id_field is not None or pk_field is not None or identifier_field is not None
        )

        return TrinityDetectionResult(
            has_trinity_pattern=has_trinity_pattern,
            id_field=id_field,
            pk_field=pk_field,
            identifier_field=identifier_field,
            audit_fields=audit_fields,
            business_fields=business_fields,
        )

    def _detect_id_field(self, table: ParsedTable) -> str | None:
        """Detect INTEGER IDENTITY PRIMARY KEY field."""
        for column in table.columns:
            if column.type == "INTEGER" and table.primary_key and column.name in table.primary_key:
                return column.name
        return None

    def _detect_pk_field(self, table: ParsedTable) -> str | None:
        """Detect UUID field with pk_ prefix."""
        for column in table.columns:
            if column.type == "UUID" and column.name.startswith("pk_"):
                return column.name
        return None

    def _detect_identifier_field(self, table: ParsedTable) -> str | None:
        """Detect TEXT identifier field (often unique)."""
        for column in table.columns:
            if column.type == "TEXT" and column.name == "identifier":
                return column.name
        return None

    def _detect_audit_fields(self, table: ParsedTable) -> list[str]:
        """Detect audit trail fields."""
        audit_fields = []
        for column in table.columns:
            if column.name in self.AUDIT_FIELDS:
                audit_fields.append(column.name)
        return audit_fields

    def _get_business_fields(
        self,
        table: ParsedTable,
        id_field: str | None,
        pk_field: str | None,
        identifier_field: str | None,
        audit_fields: list[str],
    ) -> list[str]:
        """Get business domain fields (excluding Trinity and audit fields)."""
        exclude_fields = set()
        if id_field:
            exclude_fields.add(id_field)
        if pk_field:
            exclude_fields.add(pk_field)
        if identifier_field:
            exclude_fields.add(identifier_field)
        exclude_fields.update(audit_fields)

        business_fields = []
        for column in table.columns:
            if column.name not in exclude_fields:
                business_fields.append(column.name)

        return business_fields
