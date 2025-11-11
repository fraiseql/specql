"""Tests for schema orchestrator integration with jobs schema."""

import pytest
from src.generators.schema_orchestrator import SchemaOrchestrator


def test_orchestrator_includes_jobs_schema():
    """Schema orchestrator includes jobs schema"""
    orchestrator = SchemaOrchestrator(entities=[], actions=[])
    sql = orchestrator.generate_full_schema()
    assert "CREATE SCHEMA IF NOT EXISTS jobs" in sql
    assert "CREATE TABLE jobs.tb_job_run" in sql
