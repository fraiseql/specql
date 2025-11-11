/**
 * Job Monitoring UI Components
 *
 * Example React components demonstrating how to use the generated
 * job monitoring hooks and types for building job monitoring dashboards.
 */

import React, { useState } from 'react';
import {
  useJobStatus,
  useJobsByExecutionType,
  useJobMonitoringDashboard,
  useCancelJob,
  useRetryJob,
} from './job-monitoring-hooks';
import {
  JobRecord,
  JobStatus,
  ExecutionType,
  JobMonitoringDashboard,
} from './job-monitoring-types';

// Job Status Badge Component
interface JobStatusBadgeProps {
  status: JobStatus;
  className?: string;
}

export const JobStatusBadge: React.FC<JobStatusBadgeProps> = ({ status, className = '' }) => {
  const getStatusColor = (status: JobStatus): string => {
    switch (status) {
      case JobStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800';
      case JobStatus.RUNNING:
        return 'bg-blue-100 text-blue-800';
      case JobStatus.COMPLETED:
        return 'bg-green-100 text-green-800';
      case JobStatus.FAILED:
        return 'bg-red-100 text-red-800';
      case JobStatus.CANCELLED:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(status)} ${className}`}>
      {status.toUpperCase()}
    </span>
  );
};

// Execution Type Badge Component
interface ExecutionTypeBadgeProps {
  executionType: ExecutionType;
  className?: string;
}

export const ExecutionTypeBadge: React.FC<ExecutionTypeBadgeProps> = ({ executionType, className = '' }) => {
  const getTypeColor = (type: ExecutionType): string => {
    switch (type) {
      case ExecutionType.HTTP:
        return 'bg-purple-100 text-purple-800';
      case ExecutionType.SHELL:
        return 'bg-orange-100 text-orange-800';
      case ExecutionType.DOCKER:
        return 'bg-blue-100 text-blue-800';
      case ExecutionType.SERVERLESS:
        return 'bg-indigo-100 text-indigo-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(executionType)} ${className}`}>
      {executionType.toUpperCase()}
    </span>
  );
};

// Individual Job Status Monitor
interface JobStatusMonitorProps {
  jobId: string;
}

export const JobStatusMonitor: React.FC<JobStatusMonitorProps> = ({ jobId }) => {
  const { data, loading, error } = useJobStatus(jobId);
  const [cancelJob] = useCancelJob();
  const [retryJob] = useRetryJob();

  if (loading) return <div className="animate-pulse">Loading job status...</div>;
  if (error) return <div className="text-red-600">Error loading job: {error.message}</div>;
  if (!data?.job) return <div className="text-gray-500">Job not found</div>;

  const job = data.job;

  const handleCancel = async () => {
    if (window.confirm('Are you sure you want to cancel this job?')) {
      await cancelJob({
        variables: {
          input: { id: job.id, reason: 'Cancelled by user' }
        }
      });
    }
  };

  const handleRetry = async () => {
    if (window.confirm('Are you sure you want to retry this job?')) {
      await retryJob({
        variables: { id: job.id }
      });
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Job {job.identifier}
        </h3>
        <div className="flex space-x-2">
          <JobStatusBadge status={job.status} />
          <ExecutionTypeBadge executionType={job.execution_type} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <span className="text-sm font-medium text-gray-500">Service</span>
          <p className="text-sm text-gray-900">{job.service_name}.{job.operation}</p>
        </div>
        <div>
          <span className="text-sm font-medium text-gray-500">Attempts</span>
          <p className="text-sm text-gray-900">{job.attempts} / {job.max_attempts}</p>
        </div>
        <div>
          <span className="text-sm font-medium text-gray-500">Created</span>
          <p className="text-sm text-gray-900">{new Date(job.created_at).toLocaleString()}</p>
        </div>
        <div>
          <span className="text-sm font-medium text-gray-500">Duration</span>
          <p className="text-sm text-gray-900">
            {job.started_at && job.completed_at
              ? `${Math.round((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000)}s`
              : job.started_at
                ? `${Math.round((Date.now() - new Date(job.started_at).getTime()) / 1000)}s (running)`
                : 'Not started'
            }
          </p>
        </div>
      </div>

      {job.error_message && (
        <div className="mb-4">
          <span className="text-sm font-medium text-gray-500">Error</span>
          <p className="text-sm text-red-600 bg-red-50 p-2 rounded mt-1">{job.error_message}</p>
        </div>
      )}

      {job.resource_usage && (
        <div className="mb-4">
          <span className="text-sm font-medium text-gray-500">Resource Usage</span>
          <div className="text-sm text-gray-900 mt-1">
            {job.resource_usage.cpu_usage_percent && (
              <span>CPU: {job.resource_usage.cpu_usage_percent.toFixed(1)}% </span>
            )}
            {job.resource_usage.memory_mb && (
              <span>Memory: {job.resource_usage.memory_mb}MB </span>
            )}
            {job.resource_usage.duration_seconds && (
              <span>Duration: {job.resource_usage.duration_seconds.toFixed(1)}s</span>
            )}
          </div>
        </div>
      )}

      <div className="flex space-x-2">
        {(job.status === JobStatus.PENDING || job.status === JobStatus.RUNNING) && (
          <button
            onClick={handleCancel}
            className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
          >
            Cancel Job
          </button>
        )}
        {job.status === JobStatus.FAILED && job.attempts < job.max_attempts && (
          <button
            onClick={handleRetry}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry Job
          </button>
        )}
      </div>
    </div>
  );
};

// Jobs List by Execution Type
interface JobsByExecutionTypeProps {
  executionType: ExecutionType;
  limit?: number;
}

export const JobsByExecutionType: React.FC<JobsByExecutionTypeProps> = ({
  executionType,
  limit = 20
}) => {
  const { data, loading, error } = useJobsByExecutionType(executionType, {}, { limit });

  if (loading) return <div className="animate-pulse">Loading jobs...</div>;
  if (error) return <div className="text-red-600">Error loading jobs: {error.message}</div>;

  const jobs = data?.jobsByExecutionType.jobs || [];

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        {executionType.toUpperCase()} Jobs
      </h3>

      {jobs.length === 0 ? (
        <p className="text-gray-500">No jobs found</p>
      ) : (
        <div className="space-y-2">
          {jobs.map((job) => (
            <div key={job.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-gray-900">{job.identifier}</span>
                  <JobStatusBadge status={job.status} />
                </div>
                <p className="text-sm text-gray-600">
                  {job.service_name}.{job.operation}
                </p>
              </div>
              <div className="text-right text-sm text-gray-500">
                <div>{new Date(job.created_at).toLocaleString()}</div>
                {job.error_message && (
                  <div className="text-red-600 text-xs mt-1 truncate max-w-xs">
                    {job.error_message}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Job Monitoring Dashboard
export const JobMonitoringDashboard: React.FC = () => {
  const { data, loading, error } = useJobMonitoringDashboard();
  const [selectedExecutionType, setSelectedExecutionType] = useState<ExecutionType | null>(null);

  if (loading) return <div className="animate-pulse">Loading dashboard...</div>;
  if (error) return <div className="text-red-600">Error loading dashboard: {error.message}</div>;

  const dashboard: JobMonitoringDashboard | undefined = data?.jobMonitoringDashboard;

  if (!dashboard) return <div className="text-gray-500">No dashboard data available</div>;

  return (
    <div className="space-y-6">
      {/* Statistics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-2xl font-bold text-gray-900">{dashboard.statistics.total_jobs}</div>
          <div className="text-sm text-gray-500">Total Jobs</div>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">{dashboard.statistics.running_jobs}</div>
          <div className="text-sm text-gray-500">Running</div>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">{dashboard.statistics.completed_jobs}</div>
          <div className="text-sm text-gray-500">Completed</div>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-2xl font-bold text-red-600">{dashboard.statistics.failed_jobs}</div>
          <div className="text-sm text-gray-500">Failed</div>
        </div>
      </div>

      {/* Execution Type Breakdown */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Execution Types</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {dashboard.execution_breakdown.map((breakdown) => (
            <div
              key={breakdown.execution_type}
              className="cursor-pointer p-4 border rounded-lg hover:bg-gray-50"
              onClick={() => setSelectedExecutionType(breakdown.execution_type)}
            >
              <div className="flex items-center justify-between mb-2">
                <ExecutionTypeBadge executionType={breakdown.execution_type} />
                <span className="text-sm text-gray-500">{breakdown.total_jobs}</span>
              </div>
              <div className="text-sm text-gray-600">
                Success: {breakdown.successful_jobs}/{breakdown.total_jobs}
              </div>
              {breakdown.average_duration_seconds && (
                <div className="text-sm text-gray-600">
                  Avg: {breakdown.average_duration_seconds.toFixed(1)}s
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Jobs</h3>
        <div className="space-y-2">
          {dashboard.recent_jobs.map((job) => (
            <div key={job.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center space-x-3">
                <JobStatusBadge status={job.status} />
                <ExecutionTypeBadge executionType={job.execution_type} />
                <span className="font-medium text-gray-900">{job.service_name}.{job.operation}</span>
              </div>
              <div className="text-sm text-gray-500">
                {new Date(job.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Execution Type Details */}
      {selectedExecutionType && (
        <JobsByExecutionType executionType={selectedExecutionType} />
      )}
    </div>
  );
};

// Job Search and Filter Component
interface JobSearchProps {
  onJobSelect: (jobId: string) => void;
}

export const JobSearch: React.FC<JobSearchProps> = ({ onJobSelect }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [executionType, setExecutionType] = useState<ExecutionType | ''>('');
  const [status, setStatus] = useState<JobStatus | ''>('');

  const { data, loading } = useJobsByExecutionType(
    executionType as ExecutionType || ExecutionType.HTTP,
    {
      service_name: searchTerm ? undefined : undefined, // Could add more filters
    },
    { limit: 50 }
  );

  const jobs = data?.jobsByExecutionType.jobs || [];

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Search Jobs</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <input
          type="text"
          placeholder="Search by service name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <select
          value={executionType}
          onChange={(e) => setExecutionType(e.target.value as ExecutionType)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Execution Types</option>
          {Object.values(ExecutionType).map((type) => (
            <option key={type} value={type}>{type.toUpperCase()}</option>
          ))}
        </select>

        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as JobStatus)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          {Object.values(JobStatus).map((status) => (
            <option key={status} value={status}>{status.toUpperCase()}</option>
          ))}
        </select>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {loading ? (
          <div className="animate-pulse">Searching...</div>
        ) : jobs.length === 0 ? (
          <p className="text-gray-500">No jobs found</p>
        ) : (
          jobs
            .filter((job) => !status || job.status === status)
            .filter((job) => !searchTerm || job.service_name.includes(searchTerm))
            .map((job) => (
              <div
                key={job.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded cursor-pointer hover:bg-gray-100"
                onClick={() => onJobSelect(job.id)}
              >
                <div className="flex items-center space-x-3">
                  <JobStatusBadge status={job.status} />
                  <ExecutionTypeBadge executionType={job.execution_type} />
                  <div>
                    <div className="font-medium text-gray-900">{job.identifier}</div>
                    <div className="text-sm text-gray-600">{job.service_name}.{job.operation}</div>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(job.created_at).toLocaleString()}
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  );
};