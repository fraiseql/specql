"""Unit tests for security data masking pattern."""

from src.patterns.pattern_registry import PatternRegistry


class TestDataMaskingPattern:
    """Test security data masking pattern generation."""

    def test_data_masking_partial(self):
        """Test: Generate data masking with partial masking"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/data_masking")

        # This should fail initially - pattern doesn't exist yet
        assert pattern is not None

        entity = {
            "name": "Contact",
            "schema": "tenant",
            "table": "tb_contact",
            "pk_field": "pk_contact",
            "alias": "c",
            "fields": [
                {"name": "pk_contact", "type": "uuid"},
                {"name": "email", "type": "text"},
                {"name": "phone", "type": "text"},
                {"name": "first_name", "type": "text"},
            ],
        }

        config = {
            "name": "v_contact_masked",
            "schema": "tenant",
            "pattern": "security/data_masking",
            "config": {
                "base_entity": entity,
                "masked_fields": [
                    {
                        "field": "email",
                        "mask_type": "partial",
                        "unmasked_roles": ["admin", "hr_manager"],
                        "partial_config": {"show_first": 2, "show_last": 0, "mask_char": "*"},
                    }
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Validate SQL structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "security/data_masking" in sql
        assert "CASE" in sql  # Conditional masking logic
        assert "SUBSTRING" in sql  # Partial masking
        assert "REPEAT" in sql  # Mask character repetition

    def test_data_masking_hash(self):
        """Test: Generate data masking with hash masking"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/data_masking")

        entity = {
            "name": "Contact",
            "schema": "tenant",
            "table": "tb_contact",
            "pk_field": "pk_contact",
            "alias": "c",
            "fields": [
                {"name": "pk_contact", "type": "uuid"},
                {"name": "ssn", "type": "text"},
                {"name": "first_name", "type": "text"},
            ],
        }

        config = {
            "name": "v_contact_secure",
            "schema": "tenant",
            "pattern": "security/data_masking",
            "config": {
                "base_entity": entity,
                "masked_fields": [
                    {"field": "ssn", "mask_type": "hash", "unmasked_roles": ["admin"]}
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Validate hash masking
        assert "MD5(" in sql
        assert "tb_user_role" in sql  # Role checking
        assert "admin" in sql

    def test_data_masking_redact(self):
        """Test: Generate data masking with full redaction"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/data_masking")

        entity = {
            "name": "Contact",
            "schema": "tenant",
            "table": "tb_contact",
            "pk_field": "pk_contact",
            "alias": "c",
            "fields": [
                {"name": "pk_contact", "type": "uuid"},
                {"name": "salary", "type": "numeric"},
                {"name": "first_name", "type": "text"},
            ],
        }

        config = {
            "name": "v_contact_redacted",
            "schema": "tenant",
            "pattern": "security/data_masking",
            "config": {
                "base_entity": entity,
                "masked_fields": [
                    {
                        "field": "salary",
                        "mask_type": "redact",
                        "unmasked_roles": ["admin", "finance"],
                    }
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Validate redaction
        assert "'[REDACTED]'" in sql
        assert "finance" in sql

    def test_data_masking_null(self):
        """Test: Generate data masking with NULL masking"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/data_masking")

        entity = {
            "name": "Contact",
            "schema": "tenant",
            "table": "tb_contact",
            "pk_field": "pk_contact",
            "alias": "c",
            "fields": [
                {"name": "pk_contact", "type": "uuid"},
                {"name": "internal_notes", "type": "text"},
                {"name": "first_name", "type": "text"},
            ],
        }

        config = {
            "name": "v_contact_clean",
            "schema": "tenant",
            "pattern": "security/data_masking",
            "config": {
                "base_entity": entity,
                "masked_fields": [{"field": "internal_notes", "mask_type": "null"}],
            },
        }

        sql = pattern.generate(entity, config)

        # Validate NULL masking
        assert "ELSE NULL" in sql

    def test_data_masking_multiple_fields(self):
        """Test: Generate data masking with multiple masked fields"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/data_masking")

        entity = {
            "name": "Contact",
            "schema": "tenant",
            "table": "tb_contact",
            "pk_field": "pk_contact",
            "alias": "c",
            "fields": [
                {"name": "pk_contact", "type": "uuid"},
                {"name": "email", "type": "text"},
                {"name": "phone", "type": "text"},
                {"name": "ssn", "type": "text"},
                {"name": "first_name", "type": "text"},
            ],
        }

        config = {
            "name": "v_contact_multi_masked",
            "schema": "tenant",
            "pattern": "security/data_masking",
            "config": {
                "base_entity": entity,
                "masked_fields": [
                    {
                        "field": "email",
                        "mask_type": "partial",
                        "partial_config": {"show_first": 2, "show_last": 0, "mask_char": "*"},
                    },
                    {
                        "field": "phone",
                        "mask_type": "partial",
                        "partial_config": {"show_first": 0, "show_last": 4, "mask_char": "*"},
                    },
                    {"field": "ssn", "mask_type": "hash", "unmasked_roles": ["admin"]},
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Validate multiple masking types
        assert sql.count("CASE") >= 3  # One CASE per masked field
        assert sql.count("SUBSTRING") >= 2  # Two partial masks
        assert "MD5(" in sql  # One hash mask
