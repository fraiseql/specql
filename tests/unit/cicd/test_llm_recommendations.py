"""Tests for LLM-powered CI/CD pattern recommendations"""

import pytest
from unittest.mock import patch
from src.cicd.llm_recommendations import LLMRecommendations
from src.cicd.universal_pipeline_schema import UniversalPipeline


class TestLLMRecommendations:
    """Test LLM-powered pipeline recommendations"""

    @pytest.fixture
    def llm_recommendations(self):
        """Create LLM recommendations instance"""
        return LLMRecommendations()

    @pytest.fixture
    def sample_pipeline(self):
        """Create sample pipeline for testing"""
        return UniversalPipeline(
            name="test_pipeline",
            description="FastAPI backend with PostgreSQL",
            language="python",
            framework="fastapi",
            stages=[]
        )

    def test_recommend_patterns_for_pipeline(self, llm_recommendations, sample_pipeline):
        """Test recommending patterns for a pipeline"""
        # Mock LLM response
        mock_response = {
            "recommendations": [
                {
                    "pattern_id": "python_fastapi_backend_v1",
                    "confidence": 0.95,
                    "reasoning": "Perfect match for FastAPI + PostgreSQL stack"
                },
                {
                    "pattern_id": "python_django_fullstack_v1",
                    "confidence": 0.75,
                    "reasoning": "Alternative Python web framework"
                }
            ]
        }

        with patch.object(llm_recommendations, '_call_llm', return_value=mock_response):
            recommendations = llm_recommendations.recommend_patterns(sample_pipeline)

            assert len(recommendations) == 2
            assert recommendations[0]["pattern_id"] == "python_fastapi_backend_v1"
            assert recommendations[0]["confidence"] == 0.95
            assert "FastAPI" in recommendations[0]["reasoning"]

    def test_optimize_pipeline(self, llm_recommendations, sample_pipeline):
        """Test pipeline optimization suggestions"""
        mock_response = {
            "optimizations": [
                {
                    "type": "caching",
                    "description": "Add pip cache to speed up dependency installation",
                    "impact": "high",
                    "effort": "low"
                },
                {
                    "type": "parallelization",
                    "description": "Run linting and testing in parallel",
                    "impact": "medium",
                    "effort": "medium"
                }
            ]
        }

        with patch.object(llm_recommendations, '_call_llm', return_value=mock_response):
            optimizations = llm_recommendations.optimize_pipeline(sample_pipeline)

            assert len(optimizations) == 2
            assert optimizations[0]["type"] == "caching"
            assert optimizations[0]["impact"] == "high"
            assert "pip cache" in optimizations[0]["description"]

    def test_analyze_pipeline_quality(self, llm_recommendations, sample_pipeline):
        """Test pipeline quality analysis"""
        mock_response = {
            "quality_score": 8.5,
            "issues": [
                {
                    "severity": "medium",
                    "category": "security",
                    "description": "Consider adding security scanning step"
                }
            ],
            "strengths": [
                "Good separation of concerns",
                "Clear stage definitions"
            ]
        }

        with patch.object(llm_recommendations, '_call_llm', return_value=mock_response):
            analysis = llm_recommendations.analyze_quality(sample_pipeline)

            assert analysis["quality_score"] == 8.5
            assert len(analysis["issues"]) == 1
            assert analysis["issues"][0]["severity"] == "medium"
            assert len(analysis["strengths"]) == 2

    def test_generate_pipeline_from_description(self, llm_recommendations):
        """Test generating pipeline from natural language description"""
        description = "I need a CI/CD pipeline for a Node.js React app with TypeScript"

        mock_response = {
            "pipeline": {
                "name": "react_typescript_pipeline",
                "language": "node",
                "framework": "react",
                "stages": [
                    {
                        "name": "test",
                        "jobs": [
                            {
                                "name": "lint_and_test",
                                "runtime": {"language": "node", "version": "18"},
                                "steps": [
                                    {"type": "checkout"},
                                    {"type": "setup_runtime"},
                                    {"type": "install_dependencies", "command": "npm ci"},
                                    {"type": "lint", "command": "npm run lint"},
                                    {"type": "run_tests", "command": "npm test"}
                                ]
                            }
                        ]
                    }
                ]
            }
        }

        with patch.object(llm_recommendations, '_call_llm', return_value=mock_response):
            pipeline = llm_recommendations.generate_from_description(description)

            assert pipeline.name == "react_typescript_pipeline"
            assert pipeline.language == "node"
            assert pipeline.framework == "react"
            assert len(pipeline.stages) == 1
            assert pipeline.stages[0].name == "test"

    def test_compare_pipelines(self, llm_recommendations, sample_pipeline):
        """Test comparing two pipelines"""
        pipeline2 = UniversalPipeline(
            name="comparison_pipeline",
            language="python",
            framework="django"
        )

        mock_response = {
            "comparison": {
                "similarity_score": 0.7,
                "differences": [
                    "Different frameworks (FastAPI vs Django)",
                    "Similar language and structure"
                ],
                "recommendations": [
                    "Consider migrating to FastAPI for better performance"
                ]
            }
        }

        with patch.object(llm_recommendations, '_call_llm', return_value=mock_response):
            comparison = llm_recommendations.compare_pipelines(sample_pipeline, pipeline2)

            assert comparison["similarity_score"] == 0.7
            assert len(comparison["differences"]) == 2
            assert len(comparison["recommendations"]) == 1

    @patch('src.cicd.llm_recommendations.requests.post')
    def test_call_llm_api_error_handling(self, mock_post, llm_recommendations):
        """Test error handling when LLM API fails"""
        mock_post.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            llm_recommendations._call_llm("test prompt")

    def test_empty_pipeline_handling(self, llm_recommendations):
        """Test handling of empty or minimal pipelines"""
        empty_pipeline = UniversalPipeline(name="empty")

        mock_response = {
            "recommendations": [
                {
                    "pattern_id": "basic_pipeline_v1",
                    "confidence": 0.8,
                    "reasoning": "Basic pipeline template for getting started"
                }
            ]
        }

        with patch.object(llm_recommendations, '_call_llm', return_value=mock_response):
            recommendations = llm_recommendations.recommend_patterns(empty_pipeline)

            assert len(recommendations) == 1
            assert recommendations[0]["pattern_id"] == "basic_pipeline_v1"