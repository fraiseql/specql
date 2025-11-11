"""Generator for jobs schema and related database objects."""

from typing import List  # TODO: Replace with list when Python 3.8 support is dropped


class JobsSchemaGenerator:
    """Generates PostgreSQL schema for job queue functionality."""

    def generate(self) -> str:
        """Generate complete jobs schema"""
        sections = [
            self._generate_schema(),
            self._generate_job_run_table(),
            self._generate_indexes(),
            self._generate_helper_functions(),
            self._generate_observability_views(),
        ]
        return "\n\n".join(filter(None, sections))  # Remove empty sections

    def _generate_schema(self) -> str:
        """Generate jobs schema creation"""
        return "CREATE SCHEMA IF NOT EXISTS jobs;"

    def _generate_job_run_table(self) -> str:
        """Generate tb_job_run table with all required columns"""
        columns = [
            "id UUID PRIMARY KEY DEFAULT gen_random_uuid()",
            "identifier TEXT NOT NULL UNIQUE",
            "idempotency_key TEXT",
            "service_name TEXT NOT NULL",
            "operation TEXT NOT NULL",
            # Execution type support (NEW)
            "execution_type TEXT NOT NULL DEFAULT 'http' CHECK (execution_type IN ('http', 'shell', 'docker', 'serverless'))",
            "runner_config JSONB",
            "resource_usage JSONB",
            "security_context JSONB",
            # Input/output/error (existing)
            "input_data JSONB",
            "output_data JSONB",
            "error_message TEXT",
            # Status and retry (existing)
            "status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))",
            "attempts INTEGER DEFAULT 0",
            "max_attempts INTEGER DEFAULT 3",
            "timeout_seconds INTEGER",
            # Context (existing)
            "tenant_id UUID",
            "triggered_by UUID",
            "correlation_id TEXT",
            "entity_type TEXT",
            "entity_pk TEXT",
            # Timestamps (existing)
            "created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
            "started_at TIMESTAMP WITH TIME ZONE",
            "completed_at TIMESTAMP WITH TIME ZONE",
            "updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        ]

        return f"""
CREATE TABLE jobs.tb_job_run (
    {self._format_columns(columns)}
);
"""

    def _generate_indexes(self) -> str:
        """Generate indexes for efficient job polling and querying"""
        indexes = [
            self._create_index(
                "idx_tb_job_run_pending",
                "jobs.tb_job_run (status, created_at)",
                "WHERE status = 'pending'",
            ),
            self._create_index(
                "idx_tb_job_run_retry",
                "jobs.tb_job_run (status, attempts, max_attempts, updated_at)",
                "WHERE status IN ('failed', 'running')",
            ),
            self._create_index(
                "idx_tb_job_run_correlation",
                "jobs.tb_job_run (correlation_id)",
                "WHERE correlation_id IS NOT NULL",
            ),
            self._create_index(
                "idx_tb_job_run_idempotency",
                "jobs.tb_job_run (idempotency_key)",
                "WHERE idempotency_key IS NOT NULL",
            ),
            # NEW: Execution type index
            self._create_index(
                "idx_tb_job_run_execution_type",
                "jobs.tb_job_run (execution_type, status, created_at)",
            ),
            # NEW: Resource usage JSONB index
            "CREATE INDEX idx_tb_job_run_resource_usage ON jobs.tb_job_run USING gin (resource_usage);",
        ]

        return "\n\n".join(indexes)

    def _generate_helper_functions(self) -> str:
        """Generate helper functions for job lifecycle management"""
        functions = [
            self._create_function(
                "mark_job_started",
                ["job_id UUID"],
                "void",
                """
BEGIN
    UPDATE jobs.tb_job_run
    SET status = 'running', started_at = NOW(), updated_at = NOW(), attempts = attempts + 1
    WHERE id = job_id AND status = 'pending';
END;
""",
            ),
            self._create_function(
                "complete_job_successfully",
                ["job_id UUID", "output JSONB"],
                "void",
                """
BEGIN
    UPDATE jobs.tb_job_run
    SET status = 'completed', output_data = output, completed_at = NOW(), updated_at = NOW()
    WHERE id = job_id AND status = 'running';
END;
""",
            ),
            self._create_function(
                "fail_job",
                ["job_id UUID", "error_text TEXT"],
                "void",
                """
BEGIN
    UPDATE jobs.tb_job_run
    SET status = 'failed', error_message = error_text, updated_at = NOW()
    WHERE id = job_id AND status = 'running';
END;
""",
            ),
        ]

        return "\n\n".join(functions)

    def _generate_observability_views(self) -> str:
        """Generate observability views for monitoring job execution"""
        views = [
            self._create_view(
                "v_job_stats",
                """
SELECT
    service_name,
    operation,
    status,
    COUNT(*) as total_jobs,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))::numeric(10,2) as avg_duration_sec,
    PERCENTILE_CONT(0.95) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))
    )::numeric(10,2) as p95_duration_sec
FROM jobs.tb_job_run
WHERE started_at IS NOT NULL
GROUP BY service_name, operation, status;
""",
            ),
            self._create_view(
                "v_failing_services",
                """
SELECT
    service_name,
    operation,
    COUNT(*) as failure_count,
    MAX(updated_at) as last_failure,
    ARRAY_AGG(error_message) FILTER (WHERE error_message IS NOT NULL) as recent_errors
FROM jobs.tb_job_run
WHERE status = 'failed'
    AND attempts >= max_attempts
    AND updated_at > now() - interval '1 hour'
GROUP BY service_name, operation
HAVING COUNT(*) > 10;
""",
            ),
            self._create_view(
                "v_job_queue_health",
                """
SELECT
    service_name,
    operation,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_jobs,
    COUNT(*) FILTER (WHERE status = 'running') as running_jobs,
    COUNT(*) FILTER (WHERE status = 'failed' AND attempts < max_attempts) as retryable_failures,
    COUNT(*) FILTER (WHERE status = 'failed' AND attempts >= max_attempts) as permanent_failures,
    AVG(EXTRACT(EPOCH FROM (now() - created_at))) FILTER (WHERE status = 'pending')::numeric(10,2) as avg_queue_age_sec,
    MAX(EXTRACT(EPOCH FROM (now() - created_at))) FILTER (WHERE status = 'pending')::numeric(10,2) as max_queue_age_sec
FROM jobs.tb_job_run
WHERE created_at > now() - interval '1 hour'
GROUP BY service_name, operation;
""",
            ),
            self._create_view(
                "v_job_retry_patterns",
                """
SELECT
    service_name,
    operation,
    attempts,
    COUNT(*) as jobs_at_attempt,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))::numeric(10,2) as avg_duration_at_attempt,
    COUNT(*) FILTER (WHERE status = 'completed') as successes_at_attempt,
    COUNT(*) FILTER (WHERE status = 'failed') as failures_at_attempt
FROM jobs.tb_job_run
WHERE attempts > 0
    AND started_at IS NOT NULL
    AND updated_at > now() - interval '24 hours'
GROUP BY service_name, operation, attempts
ORDER BY service_name, operation, attempts;
""",
            ),
            self._create_view(
                "v_service_reliability",
                """
SELECT
    service_name,
    operation,
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_jobs,
    COUNT(*) FILTER (WHERE status = 'failed' AND attempts >= max_attempts) as failed_jobs,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'completed')::numeric /
        NULLIF(COUNT(*), 0) * 100, 2
    ) as success_rate_percent,
    AVG(attempts) FILTER (WHERE status = 'completed')::numeric(10,2) as avg_attempts_for_success,
    MAX(updated_at) as last_job_at
FROM jobs.tb_job_run
WHERE created_at > now() - interval '7 days'
GROUP BY service_name, operation
HAVING COUNT(*) > 100
ORDER BY success_rate_percent ASC;
""",
            ),
            # NEW: Execution performance by type
            self._create_view(
                "v_execution_performance_by_type",
                """
SELECT
    execution_type,
    service_name,
    operation,
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_jobs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))::numeric(10,2) as avg_duration_sec,
    PERCENTILE_CONT(0.95) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))
    )::numeric(10,2) as p95_duration_sec,
    PERCENTILE_CONT(0.99) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))
    )::numeric(10,2) as p99_duration_sec
FROM jobs.tb_job_run
WHERE started_at IS NOT NULL
    AND created_at > now() - interval '7 days'
GROUP BY execution_type, service_name, operation
ORDER BY total_jobs DESC;
""",
            ),
            # NEW: Resource usage by runner
            self._create_view(
                "v_resource_usage_by_runner",
                """
SELECT
    execution_type,
    service_name,
    operation,
    COUNT(*) as total_jobs,
    AVG((resource_usage->>'cpu_usage_percent')::numeric)::numeric(10,2) as avg_cpu_percent,
    AVG((resource_usage->>'memory_mb')::numeric)::numeric(10,2) as avg_memory_mb,
    AVG((resource_usage->>'duration_seconds')::numeric)::numeric(10,2) as avg_duration_sec,
    MAX((resource_usage->>'peak_memory_mb')::numeric)::numeric(10,2) as max_memory_mb
FROM jobs.tb_job_run
WHERE resource_usage IS NOT NULL
    AND created_at > now() - interval '24 hours'
GROUP BY execution_type, service_name, operation
ORDER BY avg_memory_mb DESC;
""",
            ),
            # NEW: Runner failure patterns
            self._create_view(
                "v_runner_failure_patterns",
                """
SELECT
    execution_type,
    service_name,
    operation,
    COUNT(*) as failure_count,
    ARRAY_AGG(DISTINCT error_message) as error_types,
    AVG(attempts)::numeric(10,2) as avg_attempts_before_failure,
    MAX(updated_at) as last_failure
FROM jobs.tb_job_run
WHERE status = 'failed'
    AND attempts >= max_attempts
    AND created_at > now() - interval '24 hours'
GROUP BY execution_type, service_name, operation
ORDER BY failure_count DESC;
""",
            ),
        ]

        return "\n\n".join(views)

    def _format_columns(self, columns: List[str]) -> str:
        """Format column definitions with proper indentation"""
        return ",\n    ".join(columns)

    def _create_index(self, name: str, on_clause: str, where_clause: str = "") -> str:
        """Create a formatted CREATE INDEX statement"""
        where_part = f"\n    {where_clause}" if where_clause else ""
        return f"-- Index for {name.split('_', 2)[-1].replace('_', ' ')}\nCREATE INDEX {name} ON {on_clause}{where_part};"

    def _create_function(self, name: str, params: List[str], return_type: str, body: str) -> str:
        """Create a formatted CREATE FUNCTION statement"""
        param_str = ", ".join(params)
        return f"-- Function to {name.replace('_', ' ')}\nCREATE OR REPLACE FUNCTION jobs.{name}({param_str}) RETURNS {return_type} AS $$\n{body}$$\n LANGUAGE plpgsql;"

    def _create_view(self, name: str, query: str) -> str:
        """Create a formatted CREATE VIEW statement"""
        return f"-- {name.replace('v_', '').replace('_', ' ').title()} view\nCREATE VIEW jobs.{name} AS\n{query}"
