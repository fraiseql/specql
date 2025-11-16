"""
Tests for JobMonitoringTypesGenerator
"""

from pathlib import Path
from src.generators.frontend.job_monitoring_types_generator import (
    JobMonitoringTypesGenerator,
)


class TestJobMonitoringTypesGenerator:
    """Test the job monitoring types generator."""

    def test_generate_types_creates_file(self, tmp_path: Path):
        """Test that generate_types creates the expected file."""
        generator = JobMonitoringTypesGenerator(tmp_path)
        generator.generate_types()

        output_file = tmp_path / "job-monitoring-types.ts"
        assert output_file.exists()

        content = output_file.read_text()
        assert "export enum JobStatus" in content
        assert "export enum ExecutionType" in content
        assert "export interface JobRecord" in content
        assert "export interface ResourceUsage" in content
        assert "export interface SecurityContext" in content

    def test_generated_types_include_all_execution_types(self, tmp_path: Path):
        """Test that all execution types are included in generated types."""
        generator = JobMonitoringTypesGenerator(tmp_path)
        generator.generate_types()

        content = (tmp_path / "job-monitoring-types.ts").read_text()

        # Check execution types
        assert "HTTP = 'http'" in content
        assert "SHELL = 'shell'" in content
        assert "DOCKER = 'docker'" in content
        assert "SERVERLESS = 'serverless'" in content

    def test_generated_types_include_job_statuses(self, tmp_path: Path):
        """Test that all job statuses are included."""
        generator = JobMonitoringTypesGenerator(tmp_path)
        generator.generate_types()

        content = (tmp_path / "job-monitoring-types.ts").read_text()

        # Check job statuses
        assert "PENDING = 'pending'" in content
        assert "RUNNING = 'running'" in content
        assert "COMPLETED = 'completed'" in content
        assert "FAILED = 'failed'" in content
        assert "CANCELLED = 'cancelled'" in content

    def test_generated_types_include_runner_configs(self, tmp_path: Path):
        """Test that runner configuration types are included."""
        generator = JobMonitoringTypesGenerator(tmp_path)
        generator.generate_types()

        content = (tmp_path / "job-monitoring-types.ts").read_text()

        # Check runner config types
        assert "export interface HTTPRunnerConfig" in content
        assert "export interface ShellRunnerConfig" in content
        assert "export interface DockerRunnerConfig" in content
        assert "export interface ServerlessRunnerConfig" in content
        assert "export type RunnerConfig =" in content

    def test_generated_types_include_monitoring_interfaces(self, tmp_path: Path):
        """Test that monitoring query types are included."""
        generator = JobMonitoringTypesGenerator(tmp_path)
        generator.generate_types()

        content = (tmp_path / "job-monitoring-types.ts").read_text()

        # Check monitoring types
        assert "export interface JobFilter" in content
        assert "export interface JobQueryResult" in content
        assert "export interface JobStatistics" in content
        assert "export interface JobMonitoringDashboard" in content

    def test_generated_types_include_performance_metrics(self, tmp_path: Path):
        """Test that performance metrics types are included."""
        generator = JobMonitoringTypesGenerator(tmp_path)
        generator.generate_types()

        content = (tmp_path / "job-monitoring-types.ts").read_text()

        # Check performance types
        assert "export interface ExecutionPerformanceMetrics" in content
        assert "export interface ResourceUsageMetrics" in content
        assert "export interface FailurePatternMetrics" in content
