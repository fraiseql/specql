"""
Translation Table Detector

Detects translation tables and identifies their relationship to parent tables.
"""

from dataclasses import dataclass

from .table_parser import ParsedTable


@dataclass
class TranslationDetectionResult:
    """Result of translation table detection."""

    is_translation_table: bool
    parent_table: str | None
    fk_column: str | None
    locale_column: str | None
    translatable_fields: list[str]


class TranslationTableDetector:
    """Detects translation table patterns."""

    def detect(self, table: ParsedTable) -> TranslationDetectionResult:
        """Detect if a table is a translation table."""
        # Check naming: *_translation suffix
        if not self._is_translation_table_name(table.table_name):
            return TranslationDetectionResult(
                is_translation_table=False,
                parent_table=None,
                fk_column=None,
                locale_column=None,
                translatable_fields=[],
            )

        # Check structure: fk_* + locale + PRIMARY KEY(fk, locale)
        parent_table = self._extract_parent_table_name(table.table_name)
        fk_column = self._find_fk_column(table)
        locale_column = self._find_locale_column(table)
        translatable_fields = self._find_translatable_fields(table, fk_column, locale_column)

        is_translation = (
            fk_column is not None
            and locale_column is not None
            and table.primary_key is not None
            and len(table.primary_key) == 2
            and fk_column in table.primary_key
            and locale_column in table.primary_key
        )

        return TranslationDetectionResult(
            is_translation_table=is_translation,
            parent_table=parent_table if is_translation else None,
            fk_column=fk_column if is_translation else None,
            locale_column=locale_column if is_translation else None,
            translatable_fields=translatable_fields,
        )

    def _is_translation_table_name(self, table_name: str) -> bool:
        """Check if table name follows translation pattern."""
        return table_name.endswith("_translation")

    def _extract_parent_table_name(self, table_name: str) -> str:
        """Extract parent table name from translation table name."""
        return table_name.replace("_translation", "")

    def _find_fk_column(self, table: ParsedTable) -> str | None:
        """Find the foreign key column (fk_* pattern)."""
        for column in table.columns:
            if column.name.startswith("fk_"):
                return column.name
        return None

    def _find_locale_column(self, table: ParsedTable) -> str | None:
        """Find the locale column."""
        for column in table.columns:
            if column.name in ("locale", "language", "lang_code", "lang"):
                return column.name
        return None

    def _find_translatable_fields(
        self, table: ParsedTable, fk_column: str | None, locale_column: str | None
    ) -> list[str]:
        """Find fields that are translatable (not FK or locale)."""
        exclude_columns = set()
        if fk_column:
            exclude_columns.add(fk_column)
        if locale_column:
            exclude_columns.add(locale_column)

        translatable_fields = []
        for column in table.columns:
            if column.name not in exclude_columns:
                translatable_fields.append(column.name)

        return translatable_fields


class TranslationMerger:
    """Merges translation table fields into parent entity."""

    def merge(self, main_table: ParsedTable, translation_table: ParsedTable) -> dict:
        """Merge translation fields into entity field structure."""
        # Detect translation pattern
        detector = TranslationTableDetector()
        translation_info = detector.detect(translation_table)

        if not translation_info.is_translation_table:
            # Return basic field mapping from main table
            return self._table_to_fields(main_table)

        # Get translatable fields from translation table
        translatable_fields = {}
        for field in translation_info.translatable_fields:
            # Find the field in translation table
            for col in translation_table.columns:
                if col.name == field:
                    translatable_fields[field] = col.specql_type
                    break

        # Create translations nested structure
        translations_structure = {
            "locale": "ref(Locale)",  # Assume Locale entity exists
            **translatable_fields,
        }

        # Get main table fields, excluding translatable ones
        main_fields = {}
        translatable_field_names = set(translation_info.translatable_fields)

        for col in main_table.columns:
            if col.name not in translatable_field_names:
                main_fields[col.name] = col.specql_type

        # Combine main fields with translations
        return {**main_fields, "translations": translations_structure}

    def _table_to_fields(self, table: ParsedTable) -> dict:
        """Convert table columns to field dict."""
        fields = {}
        for col in table.columns:
            fields[col.name] = col.specql_type
        return fields

        # Get translatable fields from translation table
        translatable_fields = {}
        for field in translation_info.translatable_fields:
            # Find the field in translation table
            for col in translation_table.columns:
                if col.name == field:
                    translatable_fields[field] = col.specql_type
                    break

        # Create translations nested structure
        translations_structure = {
            "locale": "ref(Locale)",  # Assume Locale entity exists
            **translatable_fields,
        }

        # Add translations to fields (we'll need to extend ParsedTable for this)
        # For now, return the merged table - the entity generator will handle the YAML structure
        return merged_table
