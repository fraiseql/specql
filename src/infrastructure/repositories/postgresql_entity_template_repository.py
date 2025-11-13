"""PostgreSQL implementation of EntityTemplateRepository"""
import psycopg
from typing import Optional, List
import json

from src.domain.entities.entity_template import EntityTemplate, TemplateField
from src.domain.value_objects import DomainNumber


class PostgreSQLEntityTemplateRepository:
    """PostgreSQL repository for EntityTemplate aggregate"""

    def __init__(self, db_url: str):
        self.db_url = db_url

    def save(self, template: EntityTemplate) -> None:
        """Save or update entity template"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Convert fields to JSONB
                fields_json = json.dumps([
                    {
                        "field_name": f.field_name,
                        "field_type": f.field_type,
                        "required": f.required,
                        "description": f.description,
                        "composite_type": f.composite_type,
                        "ref_entity": f.ref_entity,
                        "enum_values": f.enum_values,
                        "default_value": f.default_value,
                        "validation_rules": f.validation_rules
                    }
                    for f in template.fields
                ])

                cur.execute("""
                    INSERT INTO pattern_library.entity_templates (
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (template_id) DO UPDATE SET
                        template_name = EXCLUDED.template_name,
                        description = EXCLUDED.description,
                        domain_number = EXCLUDED.domain_number,
                        base_entity_name = EXCLUDED.base_entity_name,
                        fields = EXCLUDED.fields,
                        included_patterns = EXCLUDED.included_patterns,
                        composed_from = EXCLUDED.composed_from,
                        version = EXCLUDED.version,
                        previous_version = EXCLUDED.previous_version,
                        changelog = EXCLUDED.changelog,
                        updated_at = EXCLUDED.updated_at,
                        times_instantiated = EXCLUDED.times_instantiated,
                        is_public = EXCLUDED.is_public,
                        author = EXCLUDED.author
                """, (
                    template.template_id,
                    template.template_name,
                    template.description,
                    str(template.domain_number.value),
                    template.base_entity_name,
                    fields_json,
                    template.included_patterns,
                    template.composed_from,
                    template.version,
                    template.previous_version,
                    template.changelog,
                    template.created_at,
                    template.updated_at,
                    template.times_instantiated,
                    template.is_public,
                    template.author
                ))
                conn.commit()

    def find_by_id(self, template_id: str) -> Optional[EntityTemplate]:
        """Find template by ID"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    FROM pattern_library.entity_templates
                    WHERE template_id = %s
                """, (template_id,))

                row = cur.fetchone()
                if not row:
                    return None

                return self._row_to_template(row)

    def find_by_name(self, template_name: str) -> Optional[EntityTemplate]:
        """Find template by name"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    FROM pattern_library.entity_templates
                    WHERE template_name = %s
                """, (template_name,))

                row = cur.fetchone()
                if not row:
                    return None

                return self._row_to_template(row)

    def find_by_domain(self, domain_number: str) -> List[EntityTemplate]:
        """Find all templates for a domain"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    FROM pattern_library.entity_templates
                    WHERE domain_number = %s
                    ORDER BY template_name
                """, (domain_number,))

                return [self._row_to_template(row) for row in cur.fetchall()]

    def find_all_public(self) -> List[EntityTemplate]:
        """Find all public templates"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    FROM pattern_library.entity_templates
                    WHERE is_public = true
                    ORDER BY times_instantiated DESC, template_name
                """)

                return [self._row_to_template(row) for row in cur.fetchall()]

    def delete(self, template_id: str) -> None:
        """Delete a template"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM pattern_library.entity_templates
                    WHERE template_id = %s
                """, (template_id,))
                conn.commit()

    def increment_usage(self, template_id: str) -> None:
        """Increment times_instantiated counter"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE pattern_library.entity_templates
                    SET times_instantiated = times_instantiated + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE template_id = %s
                """, (template_id,))
                conn.commit()

    def _row_to_template(self, row) -> EntityTemplate:
        """Convert database row to EntityTemplate"""
        (
            template_id, template_name, description, domain_number,
            base_entity_name, fields_json, included_patterns, composed_from,
            version, previous_version, changelog, created_at, updated_at,
            times_instantiated, is_public, author
        ) = row

        # Parse fields from JSONB
        fields_data = json.loads(fields_json) if isinstance(fields_json, str) else fields_json
        fields = [
            TemplateField(
                field_name=f["field_name"],
                field_type=f["field_type"],
                required=f.get("required", False),
                description=f.get("description", ""),
                composite_type=f.get("composite_type"),
                ref_entity=f.get("ref_entity"),
                enum_values=f.get("enum_values"),
                default_value=f.get("default_value"),
                validation_rules=f.get("validation_rules", [])
            )
            for f in fields_data
        ]

        return EntityTemplate(
            template_id=template_id,
            template_name=template_name,
            description=description,
            domain_number=DomainNumber(domain_number),
            base_entity_name=base_entity_name,
            fields=fields,
            included_patterns=list(included_patterns) if included_patterns else [],
            composed_from=list(composed_from) if composed_from else [],
            version=version,
            previous_version=previous_version,
            changelog=changelog,
            created_at=created_at,
            updated_at=updated_at,
            times_instantiated=times_instantiated,
            is_public=is_public,
            author=author
        )