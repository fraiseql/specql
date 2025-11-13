"""
CI/CD Performance Benchmarking System

Measures and tracks performance metrics for CI/CD pipelines and patterns,
providing insights into execution times, bottlenecks, and optimization opportunities.
"""

import time
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.cicd.universal_pipeline_schema import UniversalPipeline, Step, StepType


@dataclass
class BenchmarkResult:
    """Result of a pipeline benchmark execution"""

    pipeline_name: str
    total_time: float  # Total execution time in seconds
    stage_count: int
    job_count: int
    step_count: int
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkResult':
        """Create from dictionary"""
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'BenchmarkResult':
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))


class PerformanceBenchmark:
    """
    CI/CD Performance Benchmarking System

    Measures pipeline execution performance, tracks trends, and provides
    insights for optimization.
    """

    def __init__(self, results_dir: Optional[Path] = None):
        """
        Initialize performance benchmark system.

        Args:
            results_dir: Directory to store benchmark results
        """
        self.results_dir = results_dir or Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)

    def benchmark_pipeline_execution(self, pipeline: UniversalPipeline) -> BenchmarkResult:
        """
        Benchmark the execution time of a pipeline.

        Note: This is a simulation - in real usage, this would execute the actual pipeline
        or measure execution time from CI/CD platform APIs.

        Args:
            pipeline: Pipeline to benchmark

        Returns:
            BenchmarkResult with execution metrics
        """
        start_time = time.time()

        # Simulate pipeline execution by sleeping based on complexity
        execution_time = self._simulate_pipeline_execution(pipeline)

        total_time = time.time() - start_time + execution_time

        result = BenchmarkResult(
            pipeline_name=pipeline.name,
            total_time=total_time,
            stage_count=len(pipeline.stages),
            job_count=sum(len(stage.jobs) for stage in pipeline.stages),
            step_count=sum(len(job.steps) for stage in pipeline.stages for job in stage.jobs),
            timestamp=time.time()
        )

        # Save result
        self._save_result(result)

        return result

    def measure_step_performance(self, step: Step) -> Dict[str, Any]:
        """
        Measure performance of individual pipeline step.

        Args:
            step: Step to measure

        Returns:
            Performance metrics for the step
        """
        start_time = time.time()

        # Simulate step execution
        execution_time = self._simulate_step_execution(step)

        duration = time.time() - start_time + execution_time

        return {
            "step_name": step.name,
            "step_type": step.type.value if hasattr(step.type, 'value') else str(step.type),
            "duration": duration,
            "timestamp": time.time(),
            "command": step.command
        }

    def compare_pipeline_performance(
        self,
        pipeline1: UniversalPipeline,
        pipeline2: UniversalPipeline
    ) -> Dict[str, Any]:
        """
        Compare performance between two pipelines.

        Args:
            pipeline1: First pipeline
            pipeline2: Second pipeline

        Returns:
            Comparison analysis
        """
        result1 = self.benchmark_pipeline_execution(pipeline1)
        result2 = self.benchmark_pipeline_execution(pipeline2)

        improvement = ((result1.total_time - result2.total_time) / result1.total_time) * 100

        recommendations = []
        if improvement > 10:
            recommendations.append("Pipeline 2 shows significant performance improvement")
        elif improvement < -10:
            recommendations.append("Pipeline 2 is slower - consider optimization")

        return {
            "pipeline1": {
                "name": result1.pipeline_name,
                "total_time": result1.total_time,
                "stage_count": result1.stage_count,
                "job_count": result1.job_count,
                "step_count": result1.step_count
            },
            "pipeline2": {
                "name": result2.pipeline_name,
                "total_time": result2.total_time,
                "stage_count": result2.stage_count,
                "job_count": result2.job_count,
                "step_count": result2.step_count
            },
            "improvement_percentage": improvement,
            "faster_pipeline": result1.pipeline_name if result1.total_time < result2.total_time else result2.pipeline_name,
            "recommendations": recommendations
        }

    def track_performance_trends(
        self,
        pipeline_name: str,
        historical_results: List[BenchmarkResult]
    ) -> Dict[str, Any]:
        """
        Track performance trends over time.

        Args:
            pipeline_name: Name of the pipeline
            historical_results: List of historical benchmark results

        Returns:
            Trend analysis
        """
        if not historical_results:
            return {
                "pipeline_name": pipeline_name,
                "total_runs": 0,
                "average_time": 0,
                "best_time": 0,
                "worst_time": 0,
                "trend": "no_data"
            }

        times = [r.total_time for r in historical_results]
        avg_time = sum(times) / len(times)

        # Determine trend (simplified)
        if len(times) >= 3:
            recent_avg = sum(times[-3:]) / 3
            older_avg = sum(times[:-3]) / len(times[:-3]) if times[:-3] else recent_avg

            if recent_avg < older_avg * 0.95:
                trend = "improving"
            elif recent_avg > older_avg * 1.05:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "pipeline_name": pipeline_name,
            "total_runs": len(historical_results),
            "average_time": avg_time,
            "best_time": min(times),
            "worst_time": max(times),
            "trend": trend,
            "recent_times": times[-5:]  # Last 5 runs
        }

    def generate_performance_report(self, pipeline: UniversalPipeline) -> Dict[str, Any]:
        """
        Generate comprehensive performance report for a pipeline.

        Args:
            pipeline: Pipeline to analyze

        Returns:
            Comprehensive performance report
        """
        benchmark_result = self.benchmark_pipeline_execution(pipeline)

        # Analyze stages
        stages_analysis = []
        for stage in pipeline.stages:
            stage_time = self._estimate_stage_time(stage)
            stages_analysis.append({
                "name": stage.name,
                "job_count": len(stage.jobs),
                "estimated_time": stage_time,
                "percentage": (stage_time / benchmark_result.total_time) * 100 if benchmark_result.total_time > 0 else 0
            })

        # Analyze jobs
        jobs_analysis = []
        for stage in pipeline.stages:
            for job in stage.jobs:
                job_time = self._estimate_job_time(job)
                jobs_analysis.append({
                    "name": job.name,
                    "stage": stage.name,
                    "step_count": len(job.steps),
                    "estimated_time": job_time,
                    "has_dependencies": bool(job.needs)
                })

        # Generate recommendations
        recommendations = self._generate_performance_recommendations(pipeline, benchmark_result)

        return {
            "pipeline_name": pipeline.name,
            "execution_time": benchmark_result.total_time,
            "timestamp": benchmark_result.timestamp,
            "stages": stages_analysis,
            "jobs": jobs_analysis,
            "summary": {
                "total_stages": benchmark_result.stage_count,
                "total_jobs": benchmark_result.job_count,
                "total_steps": benchmark_result.step_count,
                "avg_time_per_stage": benchmark_result.total_time / benchmark_result.stage_count if benchmark_result.stage_count > 0 else 0
            },
            "recommendations": recommendations
        }

    def check_performance_thresholds(self, result: BenchmarkResult) -> List[str]:
        """
        Check if performance meets predefined thresholds.

        Args:
            result: Benchmark result to check

        Returns:
            List of warnings/issues
        """
        warnings = []

        # Define thresholds
        MAX_TOTAL_TIME = 600  # 10 minutes
        MAX_TIME_PER_JOB = 300  # 5 minutes

        if result.total_time > MAX_TOTAL_TIME:
            warnings.append(f"Pipeline execution time ({result.total_time:.1f}s) exceeds threshold ({MAX_TOTAL_TIME}s)")

        avg_time_per_job = result.total_time / result.job_count if result.job_count > 0 else 0
        if avg_time_per_job > MAX_TIME_PER_JOB:
            warnings.append(f"Average time per job ({avg_time_per_job:.1f}s) exceeds threshold ({MAX_TIME_PER_JOB}s)")

        if result.step_count > 50:
            warnings.append(f"High step count ({result.step_count}) - consider consolidating steps")

        return warnings

    def _simulate_pipeline_execution(self, pipeline: UniversalPipeline) -> float:
        """Simulate pipeline execution time based on complexity."""
        base_time = 10  # Base execution time

        # Add time based on stages, jobs, and steps
        stage_time = len(pipeline.stages) * 5
        job_time = sum(len(stage.jobs) for stage in pipeline.stages) * 2
        step_time = sum(len(job.steps) for stage in pipeline.stages for job in stage.jobs) * 0.5

        # Add language-specific overhead
        language_multiplier = {
            "python": 1.0,
            "node": 1.2,
            "go": 0.8,
            "rust": 1.5,
            "java": 2.0
        }.get(pipeline.language, 1.0)

        return (base_time + stage_time + job_time + step_time) * language_multiplier

    def _simulate_step_execution(self, step: Step) -> float:
        """Simulate step execution time."""
        step_times = {
            StepType.CHECKOUT: 2.0,
            StepType.SETUP_RUNTIME: 3.0,
            StepType.INSTALL_DEPS: 5.0,
            StepType.RUN_TESTS: 8.0,
            StepType.LINT: 4.0,
            StepType.BUILD: 6.0,
            StepType.DEPLOY: 10.0,
        }

        return step_times.get(step.type, 1.0)

    def _estimate_stage_time(self, stage) -> float:
        """Estimate execution time for a stage."""
        return sum(self._estimate_job_time(job) for job in stage.jobs)

    def _estimate_job_time(self, job) -> float:
        """Estimate execution time for a job."""
        return sum(self._simulate_step_execution(step) for step in job.steps)

    def _generate_performance_recommendations(
        self,
        pipeline: UniversalPipeline,
        result: BenchmarkResult
    ) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []

        # Check for parallelization opportunities
        total_jobs = sum(len(stage.jobs) for stage in pipeline.stages)
        if total_jobs > 3:
            recommendations.append("Consider parallelizing independent jobs to reduce execution time")

        # Check for caching opportunities
        has_install_steps = any(
            step.type == StepType.INSTALL_DEPS
            for stage in pipeline.stages
            for job in stage.jobs
            for step in job.steps
        )
        if has_install_steps and result.total_time > 60:
            recommendations.append("Add dependency caching to improve build times")

        # Check for long-running jobs
        if result.total_time > 300:  # 5 minutes
            recommendations.append("Pipeline execution is slow - consider optimizing long-running steps")

        return recommendations

    def _save_result(self, result: BenchmarkResult) -> None:
        """Save benchmark result to file."""
        filename = f"{result.pipeline_name}_{int(result.timestamp)}.json"
        filepath = self.results_dir / filename

        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

    def load_historical_results(self, pipeline_name: str) -> List[BenchmarkResult]:
        """
        Load historical benchmark results for a pipeline.

        Args:
            pipeline_name: Name of the pipeline

        Returns:
            List of historical benchmark results
        """
        results = []
        pattern = f"{pipeline_name}_*.json"

        for filepath in self.results_dir.glob(pattern):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    results.append(BenchmarkResult.from_dict(data))
            except Exception:
                continue  # Skip corrupted files

        return sorted(results, key=lambda r: r.timestamp)