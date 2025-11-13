"""Tests for automatic pipeline optimization"""

import pytest
from unittest.mock import patch
from src.cicd.pipeline_optimizer import PipelineOptimizer
from src.cicd.universal_pipeline_schema import UniversalPipeline, Stage, Job, Step, StepType, Runtime


class TestPipelineOptimizer:
    """Test automatic pipeline optimization suggestions"""

    @pytest.fixture
    def optimizer(self):
        """Create pipeline optimizer instance"""
        return PipelineOptimizer()

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
                        ),
                        Job(
                            name="test",
                            runtime=Runtime(language="python", version="3.11"),
                            steps=[
                                Step(name="Checkout", type=StepType.CHECKOUT),
                                Step(name="Install deps", type=StepType.INSTALL_DEPS, command="pip install -r requirements.txt"),
                                Step(name="Run tests", type=StepType.RUN_TESTS, command="pytest")
                            ]
                        )
                    ]
                )
            ]
        )

    def test_detect_caching_opportunities(self, optimizer, sample_pipeline):
        """Test detection of caching opportunities"""
        opportunities = optimizer.detect_caching_opportunities(sample_pipeline)

        assert len(opportunities) > 0
        assert any("pip cache" in opp["description"].lower() for opp in opportunities)
        assert all("impact" in opp for opp in opportunities)
        assert all("effort" in opp for opp in opportunities)

    def test_detect_parallelization_opportunities(self, optimizer, sample_pipeline):
        """Test detection of parallelization opportunities"""
        opportunities = optimizer.detect_parallelization_opportunities(sample_pipeline)

        assert len(opportunities) > 0
        assert any("parallel" in opp["description"].lower() for opp in opportunities)

    def test_detect_security_improvements(self, optimizer, sample_pipeline):
        """Test detection of security improvements"""
        improvements = optimizer.detect_security_improvements(sample_pipeline)

        assert isinstance(improvements, list)
        # May be empty for basic pipeline, but should be a valid list

    def test_detect_performance_optimizations(self, optimizer, sample_pipeline):
        """Test detection of performance optimizations"""
        optimizations = optimizer.detect_performance_optimizations(sample_pipeline)

        assert isinstance(optimizations, list)

    def test_calculate_optimization_score(self, optimizer, sample_pipeline):
        """Test calculation of optimization score"""
        score = optimizer.calculate_optimization_score(sample_pipeline)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_get_all_optimizations(self, optimizer, sample_pipeline):
        """Test getting all optimization suggestions"""
        all_opts = optimizer.get_all_optimizations(sample_pipeline)

        assert "caching" in all_opts
        assert "parallelization" in all_opts
        assert "security" in all_opts
        assert "performance" in all_opts
        assert "score" in all_opts

        assert isinstance(all_opts["caching"], list)
        assert isinstance(all_opts["parallelization"], list)
        assert isinstance(all_opts["security"], list)
        assert isinstance(all_opts["performance"], list)
        assert isinstance(all_opts["score"], float)

    def test_optimize_with_llm_integration(self, optimizer, sample_pipeline):
        """Test optimization with LLM integration"""
        # Mock the LLM response
        mock_response = [
            {
                "type": "caching",
                "description": "Add pip cache to speed up dependency installation",
                "impact": "high",
                "effort": "low"
            }
        ]

        with patch.object(optimizer.llm, 'optimize_pipeline', return_value=mock_response):
            optimizations = optimizer.optimize_with_llm(sample_pipeline)

            assert isinstance(optimizations, list)
            assert len(optimizations) == 1
            assert optimizations[0]["type"] == "caching"

    def test_empty_pipeline_handling(self, optimizer):
        """Test handling of empty pipelines"""
        empty_pipeline = UniversalPipeline(name="empty")

        score = optimizer.calculate_optimization_score(empty_pipeline)
        assert score == 0.0

        all_opts = optimizer.get_all_optimizations(empty_pipeline)
        assert all_opts["score"] == 0.0

    def test_complex_pipeline_analysis(self, optimizer):
        """Test analysis of complex pipeline with multiple stages"""
        complex_pipeline = UniversalPipeline(
            name="complex_pipeline",
            language="python",
            stages=[
                Stage(name="lint", jobs=[Job(name="lint", steps=[])]),
                Stage(name="test", jobs=[Job(name="unit", steps=[]), Job(name="integration", steps=[])]),
                Stage(name="build", jobs=[Job(name="build", steps=[])]),
                Stage(name="deploy", jobs=[Job(name="deploy", steps=[])])
            ]
        )

        opportunities = optimizer.detect_parallelization_opportunities(complex_pipeline)

        # Should detect that unit and integration tests could run in parallel
        assert len(opportunities) > 0