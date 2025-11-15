"""
LLM-powered CI/CD Pipeline Recommendations

Uses LLM to provide intelligent recommendations for CI/CD pipelines including:
- Pattern suggestions based on project characteristics
- Optimization suggestions for existing pipelines
- Quality analysis and improvement recommendations
- Pipeline generation from natural language descriptions
"""

import json
import os
import requests
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from src.cicd.universal_pipeline_schema import UniversalPipeline


class LLMRecommendations:
    """
    LLM-powered CI/CD pipeline recommendations and analysis.

    Provides intelligent suggestions for pipeline improvements, pattern matching,
    and optimization using large language models.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize LLM recommendations service.

        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: LLM model to use (default: gpt-4)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable required for LLM recommendations. "
                "Set it or disable LLM features with --no-llm flag."
            )
        self.model = model
        self.api_base = "https://api.openai.com/v1/chat/completions"

    def recommend_patterns(
        self, pipeline: UniversalPipeline, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend similar pipeline patterns based on current pipeline characteristics.

        Args:
            pipeline: Universal pipeline to analyze
            limit: Maximum number of recommendations to return

        Returns:
            List of pattern recommendations with confidence scores
        """
        prompt = self._build_pattern_recommendation_prompt(pipeline, limit)

        response = self._call_llm(prompt)
        return response.get("recommendations", [])

    def optimize_pipeline(self, pipeline: UniversalPipeline) -> List[Dict[str, Any]]:
        """
        Analyze pipeline and suggest optimizations.

        Args:
            pipeline: Pipeline to optimize

        Returns:
            List of optimization suggestions
        """
        prompt = self._build_optimization_prompt(pipeline)

        response = self._call_llm(prompt)
        return response.get("optimizations", [])

    def analyze_quality(self, pipeline: UniversalPipeline) -> Dict[str, Any]:
        """
        Analyze pipeline quality and provide feedback.

        Args:
            pipeline: Pipeline to analyze

        Returns:
            Quality analysis with score, issues, and strengths
        """
        prompt = self._build_quality_analysis_prompt(pipeline)

        response = self._call_llm(prompt)
        return response

    def generate_from_description(self, description: str) -> UniversalPipeline:
        """
        Generate a pipeline from natural language description.

        Args:
            description: Natural language description of desired pipeline

        Returns:
            Generated universal pipeline
        """
        prompt = self._build_generation_prompt(description)

        response = self._call_llm(prompt)
        pipeline_data = response.get("pipeline", {})

        return self._parse_pipeline_from_response(pipeline_data)

    def compare_pipelines(
        self, pipeline1: UniversalPipeline, pipeline2: UniversalPipeline
    ) -> Dict[str, Any]:
        """
        Compare two pipelines and provide insights.

        Args:
            pipeline1: First pipeline to compare
            pipeline2: Second pipeline to compare

        Returns:
            Comparison analysis with similarities and differences
        """
        prompt = self._build_comparison_prompt(pipeline1, pipeline2)

        response = self._call_llm(prompt)
        return response.get("comparison", {})

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Call LLM API with prompt and return parsed JSON response.

        Args:
            prompt: Prompt to send to LLM

        Returns:
            Parsed JSON response from LLM
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert CI/CD pipeline consultant. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        try:
            response = requests.post(self.api_base, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Extract JSON from response (LLM might add extra text)
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            else:
                raise ValueError("No JSON found in LLM response")

        except Exception as e:
            # For testing purposes, return mock response
            # In production, this should raise the exception
            raise e

    def _build_pattern_recommendation_prompt(
        self, pipeline: UniversalPipeline, limit: int
    ) -> str:
        """Build prompt for pattern recommendations."""
        pipeline_info = self._pipeline_to_dict(pipeline)

        return f"""
Analyze this CI/CD pipeline and recommend similar patterns from our library:

Pipeline Information:
{json.dumps(pipeline_info, indent=2)}

Please recommend up to {limit} pipeline patterns that would be suitable for this project.
Consider the language, framework, database, and deployment requirements.

Respond with JSON in this format:
{{
  "recommendations": [
    {{
      "pattern_id": "pattern_name_v1",
      "confidence": 0.95,
      "reasoning": "Detailed explanation of why this pattern fits"
    }}
  ]
}}
"""

    def _build_optimization_prompt(self, pipeline: UniversalPipeline) -> str:
        """Build prompt for pipeline optimization."""
        pipeline_info = self._pipeline_to_dict(pipeline)

        return f"""
Analyze this CI/CD pipeline and suggest optimizations to improve performance, reliability, and maintainability:

Pipeline Information:
{json.dumps(pipeline_info, indent=2)}

Focus on:
- Caching strategies
- Parallel execution opportunities
- Security improvements
- Performance optimizations
- Best practices compliance

Respond with JSON in this format:
{{
  "optimizations": [
    {{
      "type": "caching|parallelization|security|performance|reliability",
      "description": "Detailed description of the optimization",
      "impact": "high|medium|low",
      "effort": "high|medium|low"
    }}
  ]
}}
"""

    def _build_quality_analysis_prompt(self, pipeline: UniversalPipeline) -> str:
        """Build prompt for quality analysis."""
        pipeline_info = self._pipeline_to_dict(pipeline)

        return f"""
Analyze the quality of this CI/CD pipeline and provide a comprehensive assessment:

Pipeline Information:
{json.dumps(pipeline_info, indent=2)}

Evaluate:
- Best practices compliance
- Security considerations
- Performance characteristics
- Maintainability
- Reliability

Provide a score from 1-10 and detailed feedback.

Respond with JSON in this format:
{{
  "quality_score": 8.5,
  "issues": [
    {{
      "severity": "high|medium|low",
      "category": "security|performance|maintainability|reliability",
      "description": "Detailed description of the issue"
    }}
  ],
  "strengths": [
    "Strength description 1",
    "Strength description 2"
  ]
}}
"""

    def _build_generation_prompt(self, description: str) -> str:
        """Build prompt for pipeline generation from description."""
        return f"""
Generate a CI/CD pipeline based on this natural language description:

"{description}"

Create a complete universal pipeline that addresses all the requirements mentioned.
Consider appropriate stages, jobs, steps, and best practices for the described use case.

Respond with JSON in this format:
{{
  "pipeline": {{
    "name": "generated_pipeline_name",
    "language": "detected_language",
    "framework": "detected_framework",
    "stages": [
      {{
        "name": "stage_name",
        "jobs": [
          {{
            "name": "job_name",
            "runtime": {{"language": "python", "version": "3.11"}},
            "steps": [
              {{"type": "checkout"}},
              {{"type": "setup_runtime"}},
              {{"type": "install_dependencies", "command": "pip install -r requirements.txt"}},
              {{"type": "run_tests", "command": "pytest"}}
            ]
          }}
        ]
      }}
    ]
  }}
}}
"""

    def _build_comparison_prompt(
        self, pipeline1: UniversalPipeline, pipeline2: UniversalPipeline
    ) -> str:
        """Build prompt for pipeline comparison."""
        pipeline1_info = self._pipeline_to_dict(pipeline1)
        pipeline2_info = self._pipeline_to_dict(pipeline2)

        return f"""
Compare these two CI/CD pipelines and provide insights:

Pipeline 1:
{json.dumps(pipeline1_info, indent=2)}

Pipeline 2:
{json.dumps(pipeline2_info, indent=2)}

Analyze similarities, differences, and provide recommendations.

Respond with JSON in this format:
{{
  "comparison": {{
    "similarity_score": 0.8,
    "differences": [
      "Difference description 1",
      "Difference description 2"
    ],
    "recommendations": [
      "Recommendation based on comparison"
    ]
  }}
}}
"""

    def _pipeline_to_dict(self, pipeline: UniversalPipeline) -> Dict[str, Any]:
        """Convert pipeline to dictionary for LLM consumption."""
        return {
            "name": pipeline.name,
            "description": pipeline.description,
            "language": pipeline.language,
            "framework": pipeline.framework,
            "stages": [
                {
                    "name": stage.name,
                    "jobs": [
                        {
                            "name": job.name,
                            "runtime": asdict(job.runtime) if job.runtime else None,
                            "services": [asdict(service) for service in job.services],
                            "steps": [
                                {
                                    "name": step.name,
                                    "type": step.type.value
                                    if hasattr(step.type, "value")
                                    else str(step.type),
                                    "command": step.command,
                                }
                                for step in job.steps
                            ],
                        }
                        for job in stage.jobs
                    ],
                }
                for stage in pipeline.stages
            ],
        }

    def _parse_pipeline_from_response(
        self, pipeline_data: Dict[str, Any]
    ) -> UniversalPipeline:
        """Parse pipeline data from LLM response into UniversalPipeline object."""
        # This is a simplified parser - in production, this would be more robust
        from src.cicd.universal_pipeline_schema import (
            Stage,
            Job,
            Step,
            StepType,
            Runtime,
        )

        stages = []
        for stage_data in pipeline_data.get("stages", []):
            jobs = []
            for job_data in stage_data.get("jobs", []):
                runtime = None
                if job_data.get("runtime"):
                    runtime = Runtime(**job_data["runtime"])

                steps = []
                for step_data in job_data.get("steps", []):
                    step_type = (
                        StepType(step_data["type"])
                        if "type" in step_data
                        else StepType.RUN
                    )
                    steps.append(
                        Step(
                            name=step_data.get("name", "Unnamed step"),
                            type=step_type,
                            command=step_data.get("command"),
                        )
                    )

                jobs.append(Job(name=job_data["name"], steps=steps, runtime=runtime))

            stages.append(Stage(name=stage_data["name"], jobs=jobs))

        return UniversalPipeline(
            name=pipeline_data.get("name", "generated_pipeline"),
            description="Generated from natural language description",
            language=pipeline_data.get("language", "python"),
            framework=pipeline_data.get("framework"),
            stages=stages,
        )
