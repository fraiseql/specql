"""Tests for jobs schema generator."""

from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator


def test_generate_jobs_schema():
    """Generate jobs schema with tb_job_run table"""
    generator = JobsSchemaGenerator()
    sql = generator.generate()
    assert "CREATE SCHEMA IF NOT EXISTS jobs" in sql
    assert "CREATE TABLE jobs.tb_job_run" in sql
    assert "id UUID PRIMARY KEY" in sql
    assert "service_name TEXT NOT NULL" in sql


def test_jobs_schema_indexes():
    """Generate indexes for job polling"""
    generator = JobsSchemaGenerator()
    sql = generator.generate()
    assert "idx_tb_job_run_pending" in sql
    assert "idx_tb_job_run_retry" in sql
    assert "idx_tb_job_run_correlation" in sql
