"""Tests for CI/CD performance benchmarking"""

import pytest
import time
from unittest.mock import patch, MagicMock
from src.cicd.performance_benchmark import PerformanceBenchmark, BenchmarkResult
from src.cicd.universal_pipeline_schema import UniversalPipeline, Stage, Job, Step, StepType, Runtime


class TestPerformanceBenchmark:
    """Test CI/CD performance benchmarking system"""

    @pytest.fixture
    def benchmark(self):
        """Create performance benchmark instance"""
        return PerformanceBenchmark()

    @pytest.fixture
    def sample_pipeline(self):
        """Create sample pipeline for testing"""
        return UniversalPipeline(
            name="test_pipeline",
            language="python",
            framework="fastapi",
            stages=[
                Stage(
                    name="test",
                    jobs=[
                        Job(
                            name="lint",
                            runtime=Runtime(language="python", version="3.11"),
                            steps=[
                                Step(name="Checkout", type=StepType.CHECKOUT),
                                Step(name="Install deps", type=StepType.INSTALL_DEPS, command="pip install -r requirements.txt"),
                                Step(name="Lint", type=StepType.LINT, command="flake8 src/")
                            ]
                        )
                    ]
                )
            ]
        )

    def test_benchmark_pipeline_execution(self, benchmark, sample_pipeline):
        """Test benchmarking pipeline execution time"""
        # Mock the execution time
        with patch.object(benchmark, '_simulate_pipeline_execution', return_value=5.8):
            result = benchmark.benchmark_pipeline_execution(sample_pipeline)

            assert isinstance(result, BenchmarkResult)
            assert abs(result.total_time - 5.8) < 0.1  # Approximately the simulated time
            assert result.stage_count == 1
            assert result.job_count == 1
            assert result.step_count == 3

    def test_measure_step_performance(self, benchmark):
        """Test measuring individual step performance"""
        step = Step(name="Test Step", type=StepType.RUN_TESTS, command="pytest")

        with patch.object(benchmark, '_simulate_step_execution', return_value=2.5):
            result = benchmark.measure_step_performance(step)

            assert result["step_name"] == "Test Step"
            assert result["step_type"] == "run_tests"
            assert abs(result["duration"] - 2.5) < 0.1  # Approximately the simulated time
            assert "timestamp" in result

    def test_compare_pipeline_performance(self, benchmark, sample_pipeline):
        """Test comparing performance between pipelines"""
        pipeline2 = UniversalPipeline(
            name="optimized_pipeline",
            language="python",
            framework="fastapi",
            stages=[
                Stage(
                    name="test",
                    jobs=[
                        Job(
                            name="lint",
                            runtime=Runtime(language="python", version="3.11"),
                            steps=[
                                Step(name="Checkout", type=StepType.CHECKOUT),
                                Step(name="Install deps", type=StepType.INSTALL_DEPS, command="uv pip install -e ."),
                                Step(name="Lint", type=StepType.LINT, command="uv run ruff check src/")
                            ]
                        )
                    ]
                )
            ]
        )

        # Mock benchmark results
        result1 = BenchmarkResult(
            pipeline_name="test_pipeline",
            total_time=10.0,
            stage_count=1,
            job_count=1,
            step_count=3,
            timestamp=time.time()
        )

        result2 = BenchmarkResult(
            pipeline_name="optimized_pipeline",
            total_time=6.0,
            stage_count=1,
            job_count=1,
            step_count=3,
            timestamp=time.time()
        )

        with patch.object(benchmark, 'benchmark_pipeline_execution') as mock_benchmark:
            mock_benchmark.side_effect = [result1, result2]

            comparison = benchmark.compare_pipeline_performance(sample_pipeline, pipeline2)

            assert comparison["pipeline1"]["name"] == "test_pipeline"
            assert comparison["pipeline2"]["name"] == "optimized_pipeline"
            assert comparison["improvement_percentage"] > 0
            assert "recommendations" in comparison

    def test_track_performance_trends(self, benchmark):
        """Test tracking performance trends over time"""
        # Mock historical data
        historical_results = [
            BenchmarkResult("pipeline_v1", 15.0, 1, 1, 3, time.time() - 86400),  # Yesterday
            BenchmarkResult("pipeline_v1", 12.0, 1, 1, 3, time.time() - 43200),  # 12 hours ago
            BenchmarkResult("pipeline_v1", 10.0, 1, 1, 3, time.time()),          # Now
        ]

        trends = benchmark.track_performance_trends("pipeline_v1", historical_results)

        assert trends["pipeline_name"] == "pipeline_v1"
        assert trends["total_runs"] == 3
        assert trends["average_time"] == 12.333333333333334  # (15+12+10)/3
        assert trends["best_time"] == 10.0
        assert trends["worst_time"] == 15.0
        assert trends["trend"] in ["improving", "stable"]  # Times are decreasing or stable

    def test_generate_performance_report(self, benchmark, sample_pipeline):
        """Test generating comprehensive performance report"""
        # Mock benchmark data
        benchmark_result = BenchmarkResult(
            pipeline_name="test_pipeline",
            total_time=8.5,
            stage_count=1,
            job_count=1,
            step_count=3,
            timestamp=time.time()
        )

        with patch.object(benchmark, 'benchmark_pipeline_execution', return_value=benchmark_result):
            report = benchmark.generate_performance_report(sample_pipeline)

            assert report["pipeline_name"] == "test_pipeline"
            assert report["execution_time"] == 8.5
            assert "stages" in report
            assert "jobs" in report
            assert "recommendations" in report

    def test_benchmark_result_serialization(self, benchmark):
        """Test BenchmarkResult serialization"""
        result = BenchmarkResult(
            pipeline_name="test_pipeline",
            total_time=5.5,
            stage_count=2,
            job_count=3,
            step_count=8,
            timestamp=time.time()
        )

        # Test to_dict
        result_dict = result.to_dict()
        assert result_dict["pipeline_name"] == "test_pipeline"
        assert result_dict["total_time"] == 5.5
        assert result_dict["stage_count"] == 2

        # Test from_dict
        result2 = BenchmarkResult.from_dict(result_dict)
        assert result2.pipeline_name == result.pipeline_name
        assert result2.total_time == result.total_time

    def test_empty_pipeline_handling(self, benchmark):
        """Test handling of empty pipelines"""
        empty_pipeline = UniversalPipeline(name="empty")

        result = benchmark.benchmark_pipeline_execution(empty_pipeline)

        assert result.total_time >= 0
        assert result.stage_count == 0
        assert result.job_count == 0
        assert result.step_count == 0

    def test_performance_thresholds(self, benchmark, sample_pipeline):
        """Test performance against predefined thresholds"""
        # Create a result that exceeds thresholds
        slow_result = BenchmarkResult(
            pipeline_name="slow_pipeline",
            total_time=800.0,  # 13+ minutes - exceeds threshold
            stage_count=1,
            job_count=1,
            step_count=60,  # High step count
            timestamp=time.time()
        )

        # Check if warnings are generated for slow performance
        warnings = benchmark.check_performance_thresholds(slow_result)
        assert len(warnings) > 0
        print(f"Warnings: {warnings}")  # Debug output
        assert any("slow" in warning.lower() or "threshold" in warning.lower() or "high" in warning.lower() for warning in warnings)