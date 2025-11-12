"""Temporal pattern utilities for query building and validation."""

from typing import Dict, Optional


class TemporalQueryBuilder:
    """Utilities for building temporal queries"""

    def build_validity_range(
        self, start_field: str, end_field: Optional[str] = None, range_type: str = "[)"
    ) -> str:
        """Generate tsrange expression"""
        if end_field:
            return f"tsrange({start_field}, {end_field}, '{range_type}')"
        else:
            # Use LEAD for auto-computed end dates
            return f"""tsrange(
                {start_field},
                LEAD({start_field}) OVER (PARTITION BY pk ORDER BY {start_field}),
                '{range_type}'
            )"""

    def build_point_in_time_filter(
        self, validity_field: str, target_date: str = "CURRENT_DATE"
    ) -> str:
        """Generate point-in-time filter"""
        return f"{validity_field} @> {target_date}::date"

    def build_temporal_join(
        self,
        left_table: str,
        right_table: str,
        left_validity: str,
        right_validity: str,
        join_type: str = "INNER",
    ) -> str:
        """Generate temporal join condition"""
        return f"""
        {join_type} JOIN {right_table}
            ON {left_table}.fk = {right_table}.pk
            AND {left_validity} && {right_validity}  -- Overlapping ranges
        """


class TemporalValidator:
    """Validate temporal pattern configurations"""

    def validate_temporal_fields(self, entity: Dict, config: Dict) -> list[str]:
        """Validate that temporal fields exist in entity"""
        errors = []
        effective_field = config.get("effective_date_field")
        end_field = config.get("end_date_field")

        # Check if effective_date_field exists
        if effective_field:
            # This would need entity field metadata to fully validate
            # For now, just check it's a string
            if not isinstance(effective_field, str):
                errors.append("effective_date_field must be a string")

        if end_field and not isinstance(end_field, str):
            errors.append("end_date_field must be a string")

        return errors

    def validate_snapshot_config(self, config: Dict) -> list[str]:
        """Validate snapshot pattern configuration"""
        errors = []

        required_fields = ["effective_date_field"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Validate snapshot_mode
        valid_modes = ["point_in_time", "full_history", "current_only"]
        mode = config.get("snapshot_mode", "point_in_time")
        if mode not in valid_modes:
            errors.append(f"Invalid snapshot_mode: {mode}. Must be one of {valid_modes}")

        return errors


class PointInTimeQuery:
    """Helper for building point-in-time queries"""

    def __init__(self, view_name: str, pk_field: str = "pk"):
        self.view_name = view_name
        self.pk_field = pk_field

    def as_of_date(self, target_date: str) -> str:
        """Query for state as of specific date"""
        return f"""
        SELECT *
        FROM {self.view_name}
        WHERE valid_period @> '{target_date}'::date
        ORDER BY {self.pk_field}, version_effective_date DESC
        """

    def current_state(self) -> str:
        """Query for current state only"""
        return f"""
        SELECT *
        FROM {self.view_name}
        WHERE is_current = true
        ORDER BY {self.pk_field}
        """

    def version_history(self, entity_id: int) -> str:
        """Query complete version history for an entity"""
        return f"""
        SELECT *
        FROM {self.view_name}
        WHERE {self.pk_field} = {entity_id}
        ORDER BY version_effective_date DESC
        """

    def changes_between_dates(self, start_date: str, end_date: str) -> str:
        """Query entities that changed between two dates"""
        return f"""
        SELECT DISTINCT {self.pk_field}
        FROM {self.view_name}
        WHERE version_effective_date BETWEEN '{start_date}'::date AND '{end_date}'::date
        """


class AuditTrailGenerator:
    """Generate audit infrastructure"""

    def generate_audit_table(self, entity: Dict, audit_table: str) -> str:
        """Generate audit table DDL"""
        pk_field = entity.get("pk_field", "id")
        return f"""
        -- Auto-create audit table if it doesn't exist
        CREATE TABLE IF NOT EXISTS {{ schema }}.{audit_table} (
            audit_id BIGSERIAL PRIMARY KEY,
            {pk_field} INTEGER NOT NULL,
            operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
            changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            changed_by UUID,
            transaction_id BIGINT DEFAULT txid_current(),
            application_name TEXT DEFAULT CURRENT_SETTING('application_name'),
            client_addr INET DEFAULT INET_CLIENT_ADDR(),
            old_values JSONB,
            new_values JSONB
        );
        """

    def generate_audit_trigger(self, entity: Dict, audit_table: str) -> str:
        """Generate audit trigger function"""
        pk_field = entity.get("pk_field", "id")
        table = entity.get("table", f"tb_{entity.get('name', '').lower()}")
        return f"""
        -- Audit trigger function
        CREATE OR REPLACE FUNCTION {{ schema }}.{table}_audit_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                INSERT INTO {{ schema }}.{audit_table} (
                    {pk_field}, operation, changed_by, new_values
                ) VALUES (
                    NEW.{pk_field},
                    'INSERT',
                    NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::uuid,
                    to_jsonb(NEW)
                );
                RETURN NEW;
            ELSIF TG_OP = 'UPDATE' THEN
                INSERT INTO {{ schema }}.{audit_table} (
                    {pk_field}, operation, changed_by, old_values, new_values
                ) VALUES (
                    NEW.{pk_field},
                    'UPDATE',
                    NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::uuid,
                    to_jsonb(OLD),
                    to_jsonb(NEW)
                );
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                INSERT INTO {{ schema }}.{audit_table} (
                    {pk_field}, operation, changed_by, old_values
                ) VALUES (
                    OLD.{pk_field},
                    'DELETE',
                    NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::uuid,
                    to_jsonb(OLD)
                );
                RETURN OLD;
            END IF;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;

        -- Attach trigger
        CREATE TRIGGER trg_{table}_audit
        AFTER INSERT OR UPDATE OR DELETE ON {{ schema }}.{table}
        FOR EACH ROW EXECUTE FUNCTION {{ schema }}.{table}_audit_trigger();
        """

    def generate_audit_view(self, entity: Dict, config: Dict) -> str:
        """Generate audit trail view"""
        # This is already implemented in the SQL template
        return ""

    def generate_retention_policy(self, audit_table: str, retention_period: str) -> str:
        """Generate audit data retention policy"""
        return f"""
        -- Automated audit cleanup
        CREATE OR REPLACE FUNCTION cleanup_old_audit_records()
        RETURNS void AS $$
        BEGIN
            DELETE FROM {audit_table}
            WHERE changed_at < CURRENT_DATE - INTERVAL '{retention_period}';
        END;
        $$ LANGUAGE plpgsql;

        -- Schedule cleanup (requires pg_cron)
        SELECT cron.schedule('cleanup_audit', '0 2 * * 0', 'SELECT cleanup_old_audit_records()');
        """
