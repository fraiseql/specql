"""
PostgreSQL Table Generator (Team B)
Generates DDL for Trinity pattern tables from Entity AST
"""

from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import EntityDefinition
from src.generators.comment_generator import CommentGenerator
from src.generators.constraint_generator import ConstraintGenerator
from src.generators.index_generator import IndexGenerator
from src.generators.schema.schema_registry import SchemaRegistry
from src.utils.safe_slug import safe_slug, safe_table_name


class TableGenerator:
    """Generates PostgreSQL DDL for Trinity pattern tables"""

    # Field type mappings: SpecQL → PostgreSQL
    TYPE_MAPPINGS = {
        "text": "TEXT",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "date": "DATE",
        "timestamp": "TIMESTAMPTZ",
        "uuid": "UUID",
        "json": "JSONB",
        "decimal": "DECIMAL",
    }

    def __init__(self, schema_registry: SchemaRegistry, templates_dir: str = "templates/sql"):
        """Initialize with Jinja2 templates and schema registry"""
        self.schema_registry = schema_registry
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
        )
        self.constraint_generator = ConstraintGenerator()
        self.comment_generator = CommentGenerator()
        self.index_generator = IndexGenerator()

    def generate_table_ddl(self, entity: EntityDefinition) -> str:
        """
        Generate complete CREATE TABLE DDL for entity

        Args:
            entity: Parsed Entity AST from Team A parser

        Returns:
            Complete PostgreSQL DDL as string
        """
        # Prepare template context
        context = self._prepare_template_context(entity)

        # Load and render template
        template = self.env.get_template("table.sql.j2")
        return template.render(**context)

    def _prepare_template_context(self, entity: EntityDefinition) -> dict[str, Any]:
        """Prepare context dictionary for Jinja2 template"""

        # Determine multi-tenancy requirements based on schema
        is_tenant_specific = self._is_tenant_specific_schema(entity.schema)

        # Convert fields to template format (dict format expected by template)
        business_fields = {}
        foreign_keys = {}
        table_constraints = []

        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"

        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                # Foreign key field - add to FK dict
                fk_name = f"fk_{field_name}"
                target_entity_lower = field_def.reference_entity.lower()
                references = f"{entity.schema}.tb_{target_entity_lower}"
                foreign_keys[fk_name] = {
                    "name": fk_name,
                    "references": references,
                    "on": f"pk_{target_entity_lower}",
                    "nullable": field_def.nullable,
                    "description": f"Reference to {field_def.reference_entity}",
                }
            elif field_def.type_name == "enum" and field_def.values:
                # Enum field - add CHECK constraint
                enum_values = ", ".join(f"'{v}'" for v in field_def.values)
                constraint_name = self.constraint_generator._generate_constraint_name(
                    table_name, field_name, "enum"
                )
                table_constraints.append(
                    f"CONSTRAINT {constraint_name} CHECK ({field_name} IN ({enum_values}))"
                )
                business_fields[field_name] = {
                    "name": field_name,
                    "type": "TEXT",
                    "nullable": field_def.nullable,
                    "description": f"Enum field: {field_name}",
                }
            else:
                # Regular field (including rich types)
                sql_type = field_def.get_postgres_type()
                field_dict = {
                    "name": field_name,
                    "type": sql_type,
                    "nullable": field_def.nullable,
                }

                # Generate named constraints for rich types
                constraint = self.constraint_generator.generate_constraint(field_def, table_name)
                if constraint:
                    table_constraints.append(constraint)

                business_fields[field_name] = field_dict

        # Process patterns
        pattern_extensions = self._process_patterns(entity)

        # Build context
        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_code": entity.organization.table_code
                if entity.organization
                else entity.name[:3].upper(),
                "description": entity.description or f"{entity.name} entity",
                "fields": business_fields,
                "foreign_keys": foreign_keys,
                "constraints": table_constraints,
                "multi_tenant": is_tenant_specific,
                "translations": {
                    "enabled": entity.translations.enabled if entity.translations else False,
                    "table_name": (
                        entity.translations.table_name
                        if entity.translations and entity.translations.table_name
                        else f"tl_{entity.name.lower()}"  # Default to tl_ prefix
                    ),
                    "fields": entity.translations.fields if entity.translations else [],
                },
                "patterns": pattern_extensions,
            }
        }

        return context

    def _process_patterns(self, entity: EntityDefinition) -> dict[str, Any]:
        """Process entity patterns and return extensions for template"""
        extensions = {
            "computed_columns": [],
            "indexes": [],
            "exclusion_constraints": [],
            "aggregate_views": [],
            "aggregate_view_indexes": [],
            "scd_fields": [],
            "scd_indexes": [],
            "scd_functions": [],
            "template_inheritance_fields": [],
            "template_inheritance_functions": [],
            "template_inheritance_triggers": [],
            "template_inheritance_indexes": [],
            "metadata": [],
        }

        for pattern in entity.patterns:
            pattern_type = pattern.get("type")
            if pattern_type == "temporal_non_overlapping_daterange":
                self._process_temporal_daterange_pattern(entity, pattern, extensions)
            elif pattern_type == "recursive_dependency_validator":
                self._process_recursive_dependency_validator_pattern(entity, pattern, extensions)
            elif pattern_type == "aggregate_view":
                self._process_aggregate_view_pattern(entity, pattern, extensions)
            elif pattern_type == "scd_type2_helper":
                self._process_scd_type2_helper_pattern(entity, pattern, extensions)
            elif pattern_type == "template_inheritance":
                self._process_template_inheritance_pattern(entity, pattern, extensions)
            elif pattern_type == "computed_column":
                self._process_computed_column_pattern(entity, pattern, extensions)

        return extensions

    def _process_temporal_daterange_pattern(
        self, entity: EntityDefinition, pattern: dict[str, Any], extensions: dict[str, Any]
    ) -> None:
        """Process temporal_non_overlapping_daterange pattern"""
        pattern_type = pattern.get("type")
        params = pattern.get("params", {})
        scope_fields = params.get("scope_fields", [])
        start_field = params.get("start_date_field", "start_date")
        end_field = params.get("end_date_field", "end_date")
        check_mode = params.get("check_mode", "strict")
        allow_adjacent = params.get("allow_adjacent", True)

        table_name = f"{entity.schema}.tb_{entity.name.lower()}"
        range_column_name = f"{start_field}_{end_field}_range"

        # Add computed daterange column
        extensions["computed_columns"].append(
            {
                "name": range_column_name,
                "type": "DATERANGE",
                "expression": f"daterange({start_field}, {end_field}, '[]')",
                "stored": True,
                "comment": "Computed daterange for overlap detection",
            }
        )

        # Add GIST index
        extensions["indexes"].append(
            {
                "name": f"idx_tb_{entity.name.lower()}_daterange",
                "fields": [range_column_name],
                "using": "gist",
                "comment": "GIST index for efficient overlap detection",
            }
        )

        # Add exclusion constraint (only in strict mode)
        if check_mode == "strict":
            columns = []
            for field in scope_fields:
                columns.append(
                    {
                        "field": field,
                        "operator": "=",
                    }
                )
            columns.append(
                {
                    "field": range_column_name,
                    "operator": "&&" if allow_adjacent else "&&",
                }
            )

            extensions["exclusion_constraints"].append(
                {
                    "name": f"excl_{entity.name.lower()}_no_overlap",
                    "using": "gist",
                    "columns": columns,
                    "condition": "deleted_at IS NULL",
                    "comment": "Prevent overlapping date ranges within same scope",
                }
            )

        # Add pattern metadata
        extensions["metadata"].append(f"@fraiseql:pattern:{pattern_type}")

    def _process_aggregate_view_pattern(
        self, entity: EntityDefinition, pattern: dict[str, Any], extensions: dict[str, Any]
    ) -> None:
        """Process aggregate_view pattern"""
        pattern_type = pattern.get("type")
        params = pattern.get("params", {})

        # Extract pattern parameters
        group_by = params.get("group_by", [])
        aggregates = params.get("aggregates", [])
        refresh_mode = params.get("refresh_mode", "manual")

        # Generate materialized view name
        view_name = f"mv_{entity.name.lower()}_agg"

        # Build SELECT clause
        select_parts = []

        # Add group by columns
        for col in group_by:
            select_parts.append(col)

        # Add aggregate functions
        for agg in aggregates:
            field = agg.get("field")
            function = agg.get("function", "count").upper()
            alias = agg.get("alias", f"{function.lower()}_{field}")

            if function == "COUNT":
                select_parts.append(f"{function}({field}) AS {alias}")
            else:
                select_parts.append(f"{function}({field}) AS {alias}")

        # Build the materialized view DDL
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"
        view_full_name = f"{entity.schema}.{view_name}"

        select_clause = ", ".join(select_parts)
        group_by_clause = ", ".join(group_by)

        mv_ddl = f"""CREATE MATERIALIZED VIEW {view_full_name} AS
SELECT
    {select_clause}
FROM {table_name}
GROUP BY {group_by_clause};"""

        # Add refresh triggers for auto mode
        if refresh_mode == "auto":
            trigger_name = f"trg_refresh_{view_name}"
            trigger_ddl = f"""CREATE OR REPLACE FUNCTION refresh_{view_name}()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW {view_full_name};
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER {trigger_name}
    AFTER INSERT OR UPDATE OR DELETE ON {table_name}
    FOR EACH STATEMENT
    EXECUTE FUNCTION refresh_{view_name}();"""

            extensions["aggregate_views"].append(
                {
                    "ddl": mv_ddl,
                    "trigger_ddl": trigger_ddl,
                    "name": view_name,
                    "refresh_mode": refresh_mode,
                }
            )
        else:
            extensions["aggregate_views"].append(
                {
                    "ddl": mv_ddl,
                    "trigger_ddl": None,
                    "name": view_name,
                    "refresh_mode": refresh_mode,
                }
            )

        # Add indexes on the materialized view
        view_indexes = []
        for col in group_by:
            idx_name = f"idx_{view_name}_{col}"
            view_indexes.append(f"CREATE INDEX {idx_name} ON {view_full_name}({col});")

        extensions["aggregate_view_indexes"] = view_indexes

        # Add pattern metadata
        extensions["metadata"].append(f"@fraiseql:pattern:{pattern_type}")

    def _process_scd_type2_helper_pattern(
        self, entity: EntityDefinition, pattern: dict[str, Any], extensions: dict[str, Any]
    ) -> None:
        """Process SCD Type 2 helper pattern"""
        pattern_type = pattern.get("type")
        params = pattern.get("params", {})

        # Extract pattern parameters
        natural_key = params.get("natural_key")
        tracked_fields = params.get("tracked_fields", [])
        effective_from_field = params.get("effective_from_field", "effective_from")
        effective_to_field = params.get("effective_to_field", "effective_to")
        is_current_field = params.get("is_current_field", "is_current")

        # Add SCD tracking fields
        scd_fields = [
            {
                "name": effective_from_field,
                "type": "TIMESTAMPTZ",
                "nullable": False,
                "default": "now()",
                "description": "Start of validity period for this dimension record",
            },
            {
                "name": effective_to_field,
                "type": "TIMESTAMPTZ",
                "nullable": True,
                "description": "End of validity period for this dimension record (NULL for current)",
            },
            {
                "name": is_current_field,
                "type": "BOOLEAN",
                "nullable": False,
                "default": "true",
                "description": "Flag indicating if this is the current active record",
            },
        ]

        extensions["scd_fields"] = scd_fields

        # Add unique constraint for current records on natural key
        if natural_key:
            constraint_name = f"uk_{entity.name.lower()}_{natural_key}_current"
            constraint = f"CONSTRAINT {constraint_name} UNIQUE ({natural_key}) WHERE ({is_current_field} = true)"
            extensions["constraints"] = extensions.get("constraints", [])
            extensions["constraints"].append(constraint)

        # Add indexes for SCD queries
        scd_indexes = []

        # Index on natural key for lookups
        if natural_key:
            idx_name = f"idx_{entity.name.lower()}_{natural_key}"
            scd_indexes.append({"name": idx_name, "fields": [natural_key], "using": None})

        # Index on is_current for filtering current records
        idx_name = f"idx_{entity.name.lower()}_{is_current_field}"
        scd_indexes.append({"name": idx_name, "fields": [is_current_field], "using": None})

        # Composite index for effective date range queries
        idx_name = f"idx_{entity.name.lower()}_{effective_from_field}_{effective_to_field}"
        scd_indexes.append(
            {"name": idx_name, "fields": [effective_from_field, effective_to_field], "using": None}
        )

        # Composite index for natural key + effective dates
        if natural_key:
            idx_name = f"idx_{entity.name.lower()}_{natural_key}_{effective_from_field}_{effective_to_field}"
            scd_indexes.append(
                {
                    "name": idx_name,
                    "fields": [natural_key, effective_from_field, effective_to_field],
                    "using": None,
                }
            )

        extensions["scd_indexes"] = scd_indexes

        # Create SCD update function
        function_name = f"update_scd_{entity.name.lower()}"
        schema_name = entity.schema

        # Build function parameters
        params = [f"p_{natural_key} TEXT"]
        for field in tracked_fields:
            params.append(f"p_{field} TEXT")

        update_function = f"""
CREATE OR REPLACE FUNCTION {schema_name}.{function_name}(
    {", ".join(params)}
)
RETURNS VOID AS $$
DECLARE
    v_current_record RECORD;
    v_new_effective_from TIMESTAMPTZ := now();
BEGIN
    -- Find current active record
    SELECT * INTO v_current_record
    FROM {schema_name}.tb_{entity.name.lower()}
    WHERE {natural_key} = p_{natural_key} AND {is_current_field} = true;

    -- Check if any tracked fields have changed
    IF v_current_record IS NOT NULL AND (
        {" OR ".join([f"v_current_record.{field} != p_{field}" for field in tracked_fields])}
    ) THEN
        -- End the current record
        UPDATE {schema_name}.tb_{entity.name.lower()}
        SET {effective_to_field} = v_new_effective_from,
            {is_current_field} = false
        WHERE pk_{entity.name.lower()} = v_current_record.pk_{entity.name.lower()};

        -- Insert new current record
        INSERT INTO {schema_name}.tb_{entity.name.lower()} (
            {natural_key},
            {", ".join(tracked_fields)},
            {effective_from_field},
            {effective_to_field},
            {is_current_field}
        ) VALUES (
            p_{natural_key},
            {", ".join([f"p_{field}" for field in tracked_fields])},
            v_new_effective_from,
            NULL,
            true
        );
    ELSIF v_current_record IS NULL THEN
        -- No current record exists, insert new one
        INSERT INTO {schema_name}.tb_{entity.name.lower()} (
            {natural_key},
            {", ".join(tracked_fields)},
            {effective_from_field},
            {effective_to_field},
            {is_current_field}
        ) VALUES (
            p_{natural_key},
            {", ".join([f"p_{field}" for field in tracked_fields])},
            v_new_effective_from,
            NULL,
            true
        );
    END IF;
END;
$$ LANGUAGE plpgsql;"""

        extensions["scd_functions"] = [update_function]

        # Add pattern metadata
        extensions["metadata"].append(f"@fraiseql:pattern:{pattern_type}")

    def _process_template_inheritance_pattern(
        self, entity: EntityDefinition, pattern: dict[str, Any], extensions: dict[str, Any]
    ) -> None:
        """Process template inheritance pattern"""
        pattern_type = pattern.get("type")
        params = pattern.get("params", {})

        # Extract pattern parameters
        template_field = params.get("template_field", "template_id")
        inherited_fields = params.get("inherited_fields", [])
        allow_override = params.get("allow_override", True)
        max_depth = params.get("max_depth", 10)

        # Add template reference field
        template_ref_field = {
            "name": template_field,
            "type": "INTEGER",
            "nullable": True,
            "description": f"Reference to template entity for inheritance",
        }
        extensions["template_inheritance_fields"].append(template_ref_field)

        # Add foreign key constraint to template table (assuming self-referencing for simplicity)
        template_fk = {
            "name": f"fk_{entity.name.lower()}_{template_field}",
            "references": f"{entity.schema}.tb_{entity.name.lower()}",
            "on": f"pk_{entity.name.lower()}",
            "nullable": True,
            "description": f"Foreign key to template {entity.name}",
        }
        extensions["template_inheritance_fields"].append({"fk": template_fk})

        # Create inheritance resolution function
        function_name = f"resolve_inheritance_{entity.name.lower()}"
        schema_name = entity.schema

        # Build function return types
        return_types = [f"{field} TEXT" for field in inherited_fields]

        resolve_function = f"""
CREATE OR REPLACE FUNCTION {schema_name}.{function_name}(
    p_{entity.name.lower()}_id INTEGER
)
RETURNS TABLE (
    {", ".join(return_types)}
) AS $$
DECLARE
    v_current_id INTEGER := p_{entity.name.lower()}_id;
    v_depth INTEGER := 0;
    v_result RECORD;
BEGIN
    -- Traverse inheritance chain up to max depth
    WHILE v_current_id IS NOT NULL AND v_depth < {max_depth} LOOP
        -- Get values from current level
        SELECT {", ".join(inherited_fields)} INTO v_result
        FROM {schema_name}.tb_{entity.name.lower()}
        WHERE pk_{entity.name.lower()} = v_current_id;

        -- Return values if found at this level
        IF v_result IS NOT NULL THEN
            RETURN QUERY SELECT {", ".join([f"v_result.{field}" for field in inherited_fields])};
            RETURN;
        END IF;

        -- Move up the inheritance chain
        SELECT {template_field} INTO v_current_id
        FROM {schema_name}.tb_{entity.name.lower()}
        WHERE pk_{entity.name.lower()} = v_current_id;

        v_depth := v_depth + 1;
    END WHILE;

    -- Return NULL values if nothing found
    RETURN QUERY SELECT {", ".join(["NULL" for _ in inherited_fields])};
END;
$$ LANGUAGE plpgsql;"""

        extensions["template_inheritance_functions"].append(resolve_function)

        # Create trigger for inheritance validation
        trigger_name = f"trg_validate_inheritance_{entity.name.lower()}"
        validation_trigger = f"""
CREATE OR REPLACE FUNCTION {schema_name}.validate_inheritance_{entity.name.lower()}()
RETURNS TRIGGER AS $$
DECLARE
    v_current_id INTEGER;
    v_depth INTEGER := 0;
BEGIN
    -- Prevent circular references
    v_current_id := NEW.{template_field};
    WHILE v_current_id IS NOT NULL AND v_depth < {max_depth} LOOP
        IF v_current_id = NEW.pk_{entity.name.lower()} THEN
            RAISE EXCEPTION 'Circular inheritance reference detected';
        END IF;

        SELECT {template_field} INTO v_current_id
        FROM {schema_name}.tb_{entity.name.lower()}
        WHERE pk_{entity.name.lower()} = v_current_id;

        v_depth := v_depth + 1;
    END LOOP;

    -- Check depth limit
    IF v_depth >= {max_depth} THEN
        RAISE EXCEPTION 'Inheritance depth limit ({max_depth}) exceeded';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER {trigger_name}
    BEFORE INSERT OR UPDATE ON {schema_name}.tb_{entity.name.lower()}
    FOR EACH ROW
    EXECUTE FUNCTION {schema_name}.validate_inheritance_{entity.name.lower()}();"""

        extensions["template_inheritance_triggers"].append(validation_trigger)

        # Add indexes for inheritance queries
        inheritance_indexes = []

        # Index on template field for inheritance traversal
        idx_name = f"idx_{entity.name.lower()}_{template_field}"
        inheritance_indexes.append({"name": idx_name, "fields": [template_field], "using": None})

        extensions["template_inheritance_indexes"] = inheritance_indexes

        # Add pattern metadata
        extensions["metadata"].append(f"@fraiseql:pattern:{pattern_type}")

    def _process_computed_column_pattern(
        self, entity: EntityDefinition, pattern: dict[str, Any], extensions: dict[str, Any]
    ) -> None:
        """Process computed column pattern"""
        pattern_type = pattern.get("type")
        params = pattern.get("params", {})

        # Extract pattern parameters
        name = params.get("name")
        expression = params.get("expression")
        column_type = params.get("type", "TEXT")
        nullable = params.get("nullable", True)

        if name and expression:
            # Create computed column definition
            computed_col = {
                "name": name,
                "type": column_type.upper(),
                "expression": expression,
                "nullable": nullable,
            }
            extensions["computed_columns"].append(computed_col)

        # Add pattern metadata
        extensions["metadata"].append(f"@fraiseql:pattern:{pattern_type}")

    def _process_recursive_dependency_validator_pattern(
        self, entity: EntityDefinition, pattern: dict[str, Any], extensions: dict[str, Any]
    ) -> None:
        """Process recursive_dependency_validator pattern"""
        pattern_type = pattern.get("type")
        params = pattern.get("params", {})

        # Extract pattern parameters
        parent_field = params.get("parent_field", "parent_id")
        max_depth = params.get("max_depth", 10)
        cycle_detection = params.get("cycle_detection", True)

        # Add computed column for depth
        depth_column = {
            "name": "depth",
            "type": "INTEGER",
            "expression": f"calculate_depth({parent_field})",
        }
        extensions["computed_columns"].append(depth_column)

        # Add constraint for max depth
        constraint_name = f"chk_{entity.name.lower()}_max_depth"
        constraint = f"CONSTRAINT {constraint_name} CHECK (depth <= {max_depth})"
        extensions["constraints"] = extensions.get("constraints", [])
        extensions["constraints"].append(constraint)

        # Add index for parent field
        parent_index = {
            "name": f"idx_{entity.name.lower()}_{parent_field}",
            "fields": [parent_field],
            "using": None,
        }
        extensions["indexes"].append(parent_index)

        # Add pattern metadata
        extensions["metadata"].append(f"@fraiseql:pattern:{pattern_type}")

    def _is_tenant_specific_schema(self, schema: str) -> bool:
        """
        Determine if schema is tenant-specific (needs tenant_id) or common (shared)

        Uses domain registry to check multi_tenant flag
        """
        return self.schema_registry.is_multi_tenant(schema)

    def generate_foreign_keys_ddl(self, entity: EntityDefinition) -> str:
        """
        Generate ALTER TABLE statements for foreign keys

        Args:
            entity: Parsed Entity AST

        Returns:
            Foreign key DDL statements
        """
        if not entity.fields:
            return ""

        fk_statements = []

        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                fk_name = f"fk_{field_name}"
                entity_name_lower = entity.name.lower()
                target_entity_lower = field_def.reference_entity.lower()
                table_name = f"{entity.schema}.tb_{entity_name_lower}"
                ref_table = f"{entity.schema}.tb_{target_entity_lower}"
                ref_column = f"pk_{target_entity_lower}"

                fk_sql = f"""ALTER TABLE ONLY {table_name}
    ADD CONSTRAINT tb_{entity_name_lower}_{field_name}_fkey
    FOREIGN KEY ({fk_name}) REFERENCES {ref_table}({ref_column});"""

                fk_statements.append(fk_sql)

        return "\n\n".join(fk_statements)

    def generate_indexes_ddl(self, entity: EntityDefinition) -> str:
        """Generate CREATE INDEX statements"""
        # Implementation would go here
        return ""

    def generate_field_comments(self, entity: EntityDefinition) -> list[str]:
        """Generate COMMENT ON COLUMN statements"""
        # Implementation would go here
        return []

    def generate_indexes_for_rich_types(self, entity: EntityDefinition) -> list[str]:
        """Generate indexes for rich type fields"""
        # Implementation would go here
        return []

    def generate_complete_ddl(self, entity: EntityDefinition) -> str:
        """Generate complete DDL including table, indexes, and comments"""

        ddl_parts = []

        # 1. CREATE TABLE
        ddl_parts.append(self.generate_table_ddl(entity))

        # 2. CREATE INDEX statements (standard indexes)
        indexes = self.generate_indexes_ddl(entity)
        if indexes:
            ddl_parts.append(indexes)

        # 3. CREATE INDEX statements (rich type indexes)
        rich_type_indexes = self.generate_indexes_for_rich_types(entity)
        if rich_type_indexes:
            ddl_parts.append("\n\n".join(rich_type_indexes))

        # 4. COMMENT ON statements
        comments = self.comment_generator.generate_all_field_comments(entity)
        if comments:
            ddl_parts.extend(comments)

        # 5. Table comment
        table_comment = self.comment_generator.generate_table_comment(entity)
        ddl_parts.append(table_comment)

        return "\n\n".join(ddl_parts)
