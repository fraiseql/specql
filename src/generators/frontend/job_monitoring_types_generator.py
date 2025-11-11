"""
Job Monitoring Types Generator

Generates TypeScript types for job monitoring and execution tracking.
Creates interfaces for job status, execution types, and monitoring queries.

Output: job-monitoring-types.ts
"""

from pathlib import Path


class JobMonitoringTypesGenerator:
    """
    Generates TypeScript types for job monitoring functionality.

    This generator creates:
    - Job execution status types
    - Execution type enums
    - Resource usage tracking types
    - Job monitoring query types
    - Performance metrics types
    """

    def __init__(self, output_dir: Path):
        """
        Initialize the generator.

        Args:
            output_dir: Directory to write the job-monitoring-types.ts file
        """
        self.output_dir = output_dir
        self.types: list[str] = []

    def generate_types(self) -> None:
        """
        Generate TypeScript types for job monitoring.
        """
        self.types = []

        # Add header
        self._add_header()

        # Generate execution types
        self._generate_execution_types()

        # Generate job status types
        self._generate_job_status_types()

        # Generate resource usage types
        self._generate_resource_usage_types()

        # Generate monitoring query types
        self._generate_monitoring_query_types()

        # Generate performance metrics types
        self._generate_performance_metrics_types()

        # Write to file
        output_file = self.output_dir / "job-monitoring-types.ts"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.types))

    def _add_header(self) -> None:
        """Add file header with imports and base types."""
        header = """/**
 * Auto-generated TypeScript types for job monitoring
 *
 * Generated for multi-execution-type call service framework
 * Do not edit manually - regenerate when job schema changes
 */

import { gql } from '@apollo/client';

// Re-export base types
export type { UUID, DateTime, JSONValue } from './types';

// Job execution status enum
export enum JobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// Execution type enum
export enum ExecutionType {
  HTTP = 'http',
  SHELL = 'shell',
  DOCKER = 'docker',
  SERVERLESS = 'serverless',
}

"""
        self.types.append(header)

    def _generate_execution_types(self) -> None:
        """Generate execution type related types."""
        execution_types = """
// Execution type metadata
export interface ExecutionTypeMetadata {
  displayName: string;
  requiresNetwork: boolean;
  supportsStreaming: boolean;
  defaultTimeout: number; // seconds
}

export const EXECUTION_TYPE_METADATA: Record<ExecutionType, ExecutionTypeMetadata> = {
  [ExecutionType.HTTP]: {
    displayName: 'HTTP API',
    requiresNetwork: true,
    supportsStreaming: false,
    defaultTimeout: 300,
  },
  [ExecutionType.SHELL]: {
    displayName: 'Shell Script',
    requiresNetwork: false,
    supportsStreaming: true,
    defaultTimeout: 600,
  },
  [ExecutionType.DOCKER]: {
    displayName: 'Docker Container',
    requiresNetwork: false,
    supportsStreaming: true,
    defaultTimeout: 1800,
  },
  [ExecutionType.SERVERLESS]: {
    displayName: 'Serverless Function',
    requiresNetwork: true,
    supportsStreaming: false,
    defaultTimeout: 900,
  },
};

// Runner configuration types
export interface HTTPRunnerConfig {
  base_url: string;
  auth_type?: 'bearer' | 'basic' | 'api_key';
  headers?: Record<string, string>;
  timeout?: number;
}

export interface ShellRunnerConfig {
  allowed_commands: string[];
  working_directory?: string;
  environment?: Record<string, string>;
  resource_limits?: {
    cpu?: number;
    memory_mb?: number;
    timeout?: number;
  };
}

export interface DockerRunnerConfig {
  image: string;
  command?: string[];
  volumes?: Record<string, string>;
  environment?: Record<string, string>;
  resource_limits?: {
    cpu?: number;
    memory_mb?: number;
    timeout?: number;
  };
}

export interface ServerlessRunnerConfig {
  function_name: string;
  runtime?: string;
  memory_mb?: number;
  timeout?: number;
  environment?: Record<string, string>;
}

export type RunnerConfig =
  | HTTPRunnerConfig
  | ShellRunnerConfig
  | DockerRunnerConfig
  | ServerlessRunnerConfig;

"""
        self.types.append(execution_types)

    def _generate_job_status_types(self) -> None:
        """Generate job status and lifecycle types."""
        job_status_types = """
// Job record interface (matches jobs.tb_job_run table)
export interface JobRecord {
  id: UUID;
  identifier: string;
  idempotency_key?: string;
  service_name: string;
  operation: string;
  execution_type: ExecutionType;
  runner_config?: RunnerConfig;
  resource_usage?: ResourceUsage;
  security_context?: SecurityContext;
  input_data: JSONValue;
  output_data?: JSONValue;
  error_message?: string;
  status: JobStatus;
  attempts: number;
  max_attempts: number;
  timeout_seconds?: number;
  tenant_id?: UUID;
  triggered_by?: UUID;
  correlation_id?: string;
  entity_type?: string;
  entity_pk?: string;
  created_at: DateTime;
  started_at?: DateTime;
  completed_at?: DateTime;
  updated_at: DateTime;
}

// Job status summary
export interface JobStatusSummary {
  id: UUID;
  service_name: string;
  operation: string;
  execution_type: ExecutionType;
  status: JobStatus;
  attempts: number;
  max_attempts: number;
  created_at: DateTime;
  started_at?: DateTime;
  completed_at?: DateTime;
  duration_seconds?: number;
  error_message?: string;
}

// Job creation input
export interface CreateJobInput {
  service_name: string;
  operation: string;
  input_data: JSONValue;
  execution_type?: ExecutionType;
  runner_config?: RunnerConfig;
  timeout_seconds?: number;
  max_attempts?: number;
  idempotency_key?: string;
  correlation_id?: string;
  entity_type?: string;
  entity_pk?: string;
}

// Job update input
export interface UpdateJobInput {
  id: UUID;
  status?: JobStatus;
  output_data?: JSONValue;
  error_message?: string;
  resource_usage?: ResourceUsage;
}

// Job cancellation input
export interface CancelJobInput {
  id: UUID;
  reason?: string;
}

"""
        self.types.append(job_status_types)

    def _generate_resource_usage_types(self) -> None:
        """Generate resource usage tracking types."""
        resource_types = """
// Resource usage tracking
export interface ResourceUsage {
  cpu_usage_percent?: number;
  memory_mb?: number;
  peak_memory_mb?: number;
  disk_mb?: number;
  network_bytes?: number;
  duration_seconds?: number;
  exit_code?: number;
  container_id?: string;
  function_invocation_id?: string;
}

// Security context for audit trail
export interface SecurityContext {
  tenant_id_ref?: string; // Reference to tenant_id variable
  triggered_by_ref?: string; // Reference to user_id variable
  policy: {
    allowed_commands?: string[];
    allowed_images?: string[];
    allowed_functions?: string[];
    resource_limits?: {
      cpu_cores?: number;
      memory_mb?: number;
      disk_mb?: number;
      timeout_seconds?: number;
    };
    network_access?: boolean;
    file_access?: string[]; // Allowed file paths
  };
}

// Resource requirements for job scheduling
export interface ResourceRequirements {
  cpu_cores: number;
  memory_mb: number;
  disk_mb: number;
  timeout_seconds: number;
  network_access?: boolean;
  gpu_required?: boolean;
}

"""
        self.types.append(resource_types)

    def _generate_monitoring_query_types(self) -> None:
        """Generate types for monitoring queries."""
        monitoring_types = """
// Job monitoring query inputs
export interface JobFilter {
  id?: UUID;
  service_name?: string;
  operation?: string;
  execution_type?: ExecutionType;
  status?: JobStatus;
  tenant_id?: UUID;
  correlation_id?: string;
  entity_type?: string;
  entity_pk?: string;
  created_after?: DateTime;
  created_before?: DateTime;
  updated_after?: DateTime;
  updated_before?: DateTime;
}

export interface JobPaginationInput {
  limit?: number;
  offset?: number;
  orderBy?: 'created_at' | 'updated_at' | 'started_at' | 'completed_at';
  orderDirection?: 'ASC' | 'DESC';
}

// Job monitoring query results
export interface JobQueryResult {
  jobs: JobRecord[];
  totalCount: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

// Job statistics
export interface JobStatistics {
  total_jobs: number;
  pending_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cancelled_jobs: number;
  average_duration_seconds?: number;
  success_rate_percent: number;
}

// Execution type breakdown
export interface ExecutionTypeBreakdown {
  execution_type: ExecutionType;
  total_jobs: number;
  successful_jobs: number;
  failed_jobs: number;
  average_duration_seconds?: number;
  average_resource_usage?: ResourceUsage;
}

"""
        self.types.append(monitoring_types)

    def _generate_performance_metrics_types(self) -> None:
        """Generate performance metrics and analytics types."""
        performance_types = """
// Performance metrics from observability views
export interface ExecutionPerformanceMetrics {
  execution_type: ExecutionType;
  service_name: string;
  operation: string;
  total_jobs: number;
  successful_jobs: number;
  failed_jobs: number;
  average_duration_sec?: number;
  p95_duration_sec?: number;
  p99_duration_sec?: number;
}

export interface ResourceUsageMetrics {
  execution_type: ExecutionType;
  service_name: string;
  operation: string;
  total_jobs: number;
  avg_cpu_percent?: number;
  avg_memory_mb?: number;
  avg_duration_sec?: number;
  max_memory_mb?: number;
}

export interface FailurePatternMetrics {
  execution_type: ExecutionType;
  service_name: string;
  operation: string;
  failure_count: number;
  error_types: string[];
  avg_attempts_before_failure?: number;
  last_failure: DateTime;
}

// Dashboard data
export interface JobMonitoringDashboard {
  statistics: JobStatistics;
  execution_breakdown: ExecutionTypeBreakdown[];
  recent_jobs: JobRecord[];
  performance_metrics: ExecutionPerformanceMetrics[];
  failure_patterns: FailurePatternMetrics[];
  resource_usage: ResourceUsageMetrics[];
}

// Real-time job status subscription
export interface JobStatusUpdate {
  job_id: UUID;
  previous_status: JobStatus;
  new_status: JobStatus;
  timestamp: DateTime;
  error_message?: string;
  output_data?: JSONValue;
  resource_usage?: ResourceUsage;
}

"""
        self.types.append(performance_types)
