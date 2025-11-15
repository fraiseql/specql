"""
Job Monitoring Hooks Generator

Generates Apollo Client React hooks for job monitoring and status tracking.
Creates useJobStatus, useJobsByExecutionType, and other monitoring hooks.

Output: job-monitoring-hooks.ts
"""

from pathlib import Path


class JobMonitoringHooksGenerator:
    """
    Generates Apollo Client React hooks for job monitoring.

    This generator creates:
    - useJobStatus: Monitor individual job status
    - useJobsByExecutionType: Query jobs by execution type
    - useJobStatistics: Get job statistics dashboard
    - useJobSubscription: Real-time job status updates
    - useCancelJob: Cancel running jobs
    """

    def __init__(self, output_dir: Path):
        """
        Initialize the generator.

        Args:
            output_dir: Directory to write the job-monitoring-hooks.ts file
        """
        self.output_dir = output_dir
        self.hooks: list[str] = []

    def generate_hooks(self) -> None:
        """
        Generate Apollo hooks for job monitoring.
        """
        self.hooks = []

        # Add header
        self._add_header()

        # Generate job status hooks
        self._generate_job_status_hooks()

        # Generate job query hooks
        self._generate_job_query_hooks()

        # Generate job mutation hooks
        self._generate_job_mutation_hooks()

        # Generate subscription hooks
        self._generate_subscription_hooks()

        # Generate dashboard hooks
        self._generate_dashboard_hooks()

        # Write to file
        output_file = self.output_dir / "job-monitoring-hooks.ts"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.hooks))

    def _add_header(self) -> None:
        """Add file header with imports."""
        header = """/**
 * Auto-generated Apollo Client React hooks for job monitoring
 *
 * Generated for multi-execution-type call service framework
 * Do not edit manually - regenerate when job monitoring needs change
 */

import { useQuery, useMutation, useSubscription, gql } from '@apollo/client';
import {
  JobRecord,
  JobStatus,
  ExecutionType,
  JobFilter,
  JobPaginationInput,
  JobQueryResult,
  JobStatistics,
  ExecutionTypeBreakdown,
  JobStatusUpdate,
  JobMonitoringDashboard,
  CreateJobInput,
  UpdateJobInput,
  CancelJobInput,
} from './job-monitoring-types';

"""
        self.hooks.append(header)

    def _generate_job_status_hooks(self) -> None:
        """Generate hooks for monitoring individual job status."""
        job_status_hooks = """
// Job status monitoring hooks

export const GET_JOB_STATUS_QUERY = gql`
  query GetJobStatus($id: UUID!) {
    job(id: $id) {
      id
      status
      attempts
      max_attempts
      created_at
      started_at
      completed_at
      error_message
      execution_type
      service_name
      operation
      resource_usage
      output_data
    }
  }
`;

export const useJobStatus = (jobId: string) => {
  return useQuery<{ job: JobRecord }>(GET_JOB_STATUS_QUERY, {
    variables: { id: jobId },
    pollInterval: 2000, // Poll every 2 seconds for running jobs
    skip: !jobId,
  });
};

export const GET_JOB_BY_IDENTIFIER_QUERY = gql`
  query GetJobByIdentifier($identifier: String!) {
    jobByIdentifier(identifier: $identifier) {
      id
      status
      attempts
      max_attempts
      created_at
      started_at
      completed_at
      error_message
      execution_type
      service_name
      operation
      resource_usage
      output_data
    }
  }
`;

export const useJobByIdentifier = (identifier: string) => {
  return useQuery<{ jobByIdentifier: JobRecord }>(GET_JOB_BY_IDENTIFIER_QUERY, {
    variables: { identifier },
    pollInterval: 2000,
    skip: !identifier,
  });
};

"""
        self.hooks.append(job_status_hooks)

    def _generate_job_query_hooks(self) -> None:
        """Generate hooks for querying jobs with filters."""
        job_query_hooks = """
// Job query hooks

export const GET_JOBS_QUERY = gql`
  query GetJobs($filter: JobFilter, $pagination: JobPaginationInput) {
    jobs(filter: $filter, pagination: $pagination) {
      jobs {
        id
        identifier
        service_name
        operation
        execution_type
        status
        attempts
        max_attempts
        created_at
        started_at
        completed_at
        error_message
        tenant_id
        correlation_id
        entity_type
        entity_pk
      }
      totalCount
      hasNextPage
      hasPreviousPage
    }
  }
`;

export const useJobs = (filter?: JobFilter, pagination?: JobPaginationInput) => {
  return useQuery<{ jobs: JobQueryResult }>(GET_JOBS_QUERY, {
    variables: { filter, pagination },
  });
};

export const GET_JOBS_BY_EXECUTION_TYPE_QUERY = gql`
  query GetJobsByExecutionType($executionType: String!, $filter: JobFilter, $pagination: JobPaginationInput) {
    jobsByExecutionType(executionType: $executionType, filter: $filter, pagination: $pagination) {
      jobs {
        id
        identifier
        service_name
        operation
        execution_type
        status
        attempts
        max_attempts
        created_at
        started_at
        completed_at
        error_message
        resource_usage
        tenant_id
        correlation_id
      }
      totalCount
      hasNextPage
      hasPreviousPage
    }
  }
`;

export const useJobsByExecutionType = (
  executionType: ExecutionType,
  filter?: JobFilter,
  pagination?: JobPaginationInput
) => {
  return useQuery<{ jobsByExecutionType: JobQueryResult }>(GET_JOBS_BY_EXECUTION_TYPE_QUERY, {
    variables: { executionType, filter, pagination },
  });
};

export const GET_PENDING_JOBS_QUERY = gql`
  query GetPendingJobs($limit: Int) {
    pendingJobs(limit: $limit) {
      id
      identifier
      service_name
      operation
      execution_type
      created_at
      tenant_id
      correlation_id
      entity_type
      entity_pk
      input_data
      runner_config
      security_context
    }
  }
`;

export const usePendingJobs = (limit: number = 50) => {
  return useQuery<{ pendingJobs: JobRecord[] }>(GET_PENDING_JOBS_QUERY, {
    variables: { limit },
    pollInterval: 5000, // Poll every 5 seconds for new jobs
  });
};

"""
        self.hooks.append(job_query_hooks)

    def _generate_job_mutation_hooks(self) -> None:
        """Generate hooks for job mutations (create, update, cancel)."""
        job_mutation_hooks = """
// Job mutation hooks

export const CREATE_JOB_MUTATION = gql`
  mutation CreateJob($input: CreateJobInput!) {
    createJob(input: $input) {
      success
      data {
        job {
          id
          identifier
          status
          execution_type
          service_name
          operation
          created_at
        }
      }
      error
      code
    }
  }
`;

export const useCreateJob = () => {
  return useMutation<
    { createJob: { success: boolean; data?: { job: JobRecord }; error?: string; code?: string } },
    { input: CreateJobInput }
  >(CREATE_JOB_MUTATION, {
    onCompleted: (data) => {
      if (data.createJob.success) {
        // console.log('Job created:', data.createJob.data?.job.id);
      }
    },
    onError: (error) => {
      console.error('Failed to create job:', error);
    },
  });
};

export const UPDATE_JOB_MUTATION = gql`
  mutation UpdateJob($input: UpdateJobInput!) {
    updateJob(input: $input) {
      success
      data {
        job {
          id
          status
          output_data
          error_message
          resource_usage
          updated_at
        }
      }
      error
      code
    }
  }
`;

export const useUpdateJob = () => {
  return useMutation<
    { updateJob: { success: boolean; data?: { job: JobRecord }; error?: string; code?: string } },
    { input: UpdateJobInput }
  >(UPDATE_JOB_MUTATION, {
    onCompleted: (data) => {
      if (data.updateJob.success) {
        // console.log('Job updated:', data.updateJob.data?.job.id);
      }
    },
  });
};

export const CANCEL_JOB_MUTATION = gql`
  mutation CancelJob($input: CancelJobInput!) {
    cancelJob(input: $input) {
      success
      data {
        job {
          id
          status
          error_message
          updated_at
        }
      }
      error
      code
    }
  }
`;

export const useCancelJob = () => {
  return useMutation<
    { cancelJob: { success: boolean; data?: { job: JobRecord }; error?: string; code?: string } },
    { input: CancelJobInput }
  >(CANCEL_JOB_MUTATION, {
    onCompleted: (data) => {
      if (data.cancelJob.success) {
        // console.log('Job cancelled:', data.cancelJob.data?.job.id);
      }
    },
    onError: (error) => {
      console.error('Failed to cancel job:', error);
    },
  });
};

export const RETRY_JOB_MUTATION = gql`
  mutation RetryJob($id: UUID!) {
    retryJob(id: $id) {
      success
      data {
        job {
          id
          status
          attempts
          updated_at
        }
      }
      error
      code
    }
  }
`;

export const useRetryJob = () => {
  return useMutation<
    { retryJob: { success: boolean; data?: { job: JobRecord }; error?: string; code?: string } },
    { id: string }
  >(RETRY_JOB_MUTATION, {
    onCompleted: (data) => {
      if (data.retryJob.success) {
        // console.log('Job retry initiated:', data.retryJob.data?.job.id);
      }
    },
  });
};

"""
        self.hooks.append(job_mutation_hooks)

    def _generate_subscription_hooks(self) -> None:
        """Generate hooks for real-time job status subscriptions."""
        subscription_hooks = """
// Real-time job monitoring hooks

export const JOB_STATUS_UPDATES_SUBSCRIPTION = gql`
  subscription JobStatusUpdates($jobIds: [UUID!]) {
    jobStatusUpdates(jobIds: $jobIds) {
      job_id
      previous_status
      new_status
      timestamp
      error_message
      output_data
      resource_usage
    }
  }
`;

export const useJobStatusUpdates = (jobIds?: string[]) => {
  return useSubscription<{ jobStatusUpdates: JobStatusUpdate }>(
    JOB_STATUS_UPDATES_SUBSCRIPTION,
    {
      variables: { jobIds },
      skip: !jobIds || jobIds.length === 0,
    }
  );
};

export const JOB_EXECUTION_EVENTS_SUBSCRIPTION = gql`
  subscription JobExecutionEvents($executionTypes: [String!], $tenantId: UUID) {
    jobExecutionEvents(executionTypes: $executionTypes, tenantId: $tenantId) {
      job_id
      execution_type
      event_type
      timestamp
      details
    }
  }
`;

export const useJobExecutionEvents = (executionTypes?: ExecutionType[], tenantId?: string) => {
  return useSubscription(
    JOB_EXECUTION_EVENTS_SUBSCRIPTION,
    {
      variables: {
        executionTypes: executionTypes?.map(et => et.toString()),
        tenantId
      },
      skip: !executionTypes || executionTypes.length === 0,
    }
  );
};

"""
        self.hooks.append(subscription_hooks)

    def _generate_dashboard_hooks(self) -> None:
        """Generate hooks for job monitoring dashboard data."""
        dashboard_hooks = """
// Job monitoring dashboard hooks

export const GET_JOB_STATISTICS_QUERY = gql`
  query GetJobStatistics($tenantId: UUID, $since: DateTime) {
    jobStatistics(tenantId: $tenantId, since: $since) {
      total_jobs
      pending_jobs
      running_jobs
      completed_jobs
      failed_jobs
      cancelled_jobs
      average_duration_seconds
      success_rate_percent
    }
  }
`;

export const useJobStatistics = (tenantId?: string, since?: string) => {
  return useQuery<{ jobStatistics: JobStatistics }>(GET_JOB_STATISTICS_QUERY, {
    variables: { tenantId, since },
  });
};

export const GET_EXECUTION_TYPE_BREAKDOWN_QUERY = gql`
  query GetExecutionTypeBreakdown($tenantId: UUID, $since: DateTime) {
    executionTypeBreakdown(tenantId: $tenantId, since: $since) {
      execution_type
      total_jobs
      successful_jobs
      failed_jobs
      average_duration_seconds
      average_resource_usage
    }
  }
`;

export const useExecutionTypeBreakdown = (tenantId?: string, since?: string) => {
  return useQuery<{ executionTypeBreakdown: ExecutionTypeBreakdown[] }>(
    GET_EXECUTION_TYPE_BREAKDOWN_QUERY,
    {
      variables: { tenantId, since },
    }
  );
};

export const GET_JOB_MONITORING_DASHBOARD_QUERY = gql`
  query GetJobMonitoringDashboard($tenantId: UUID, $since: DateTime, $limit: Int) {
    jobMonitoringDashboard(tenantId: $tenantId, since: $since, limit: $limit) {
      statistics {
        total_jobs
        pending_jobs
        running_jobs
        completed_jobs
        failed_jobs
        cancelled_jobs
        average_duration_seconds
        success_rate_percent
      }
      execution_breakdown {
        execution_type
        total_jobs
        successful_jobs
        failed_jobs
        average_duration_seconds
        average_resource_usage
      }
      recent_jobs {
        id
        service_name
        operation
        execution_type
        status
        created_at
        started_at
        completed_at
        error_message
      }
      performance_metrics {
        execution_type
        service_name
        operation
        total_jobs
        successful_jobs
        failed_jobs
        average_duration_sec
        p95_duration_sec
        p99_duration_sec
      }
      failure_patterns {
        execution_type
        service_name
        operation
        failure_count
        error_types
        avg_attempts_before_failure
        last_failure
      }
      resource_usage {
        execution_type
        service_name
        operation
        total_jobs
        avg_cpu_percent
        avg_memory_mb
        avg_duration_sec
        max_memory_mb
      }
    }
  }
`;

export const useJobMonitoringDashboard = (
  tenantId?: string,
  since?: string,
  limit: number = 20
) => {
  return useQuery<{ jobMonitoringDashboard: JobMonitoringDashboard }>(
    GET_JOB_MONITORING_DASHBOARD_QUERY,
    {
      variables: { tenantId, since, limit },
      pollInterval: 30000, // Refresh every 30 seconds
    }
  );
};

"""
        self.hooks.append(dashboard_hooks)
