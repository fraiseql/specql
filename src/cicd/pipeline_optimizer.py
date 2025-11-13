"""
Automatic Pipeline Optimization

Analyzes CI/CD pipelines and provides specific optimization suggestions
for performance, reliability, security, and maintainability improvements.
"""

from typing import List, Dict, Any, Optional
from src.cicd.universal_pipeline_schema import UniversalPipeline, StepType
from src.cicd.llm_recommendations import LLMRecommendations


class PipelineOptimizer:
    """
    Automatic pipeline optimization engine.

    Analyzes pipelines and provides actionable optimization suggestions
    across multiple categories: caching, parallelization, security, performance.
    """

    def __init__(self, llm_recommendations: Optional[LLMRecommendations] = None):
        """
        Initialize pipeline optimizer.

        Args:
            llm_recommendations: Optional LLM service for enhanced recommendations
        """
        self.llm = llm_recommendations or LLMRecommendations()

    def detect_caching_opportunities(self, pipeline: UniversalPipeline) -> List[Dict[str, Any]]:
        """
        Detect opportunities for caching to improve build performance.

        Args:
            pipeline: Pipeline to analyze

        Returns:
            List of caching optimization suggestions
        """
        opportunities = []

        # Check for dependency installation without caching
        has_python_deps = any(
            step.type == StepType.INSTALL_DEPS and "pip" in (step.command or "")
            for stage in pipeline.stages
            for job in stage.jobs
            for step in job.steps
        )

        if has_python_deps and not self._has_cache_step(pipeline):
            opportunities.append({
                "type": "caching",
                "description": "Add pip cache to speed up dependency installation",
                "impact": "high",
                "effort": "low",
                "category": "performance"
            })

        # Check for Node.js dependencies
        has_nodejs_deps = any(
            step.type == StepType.INSTALL_DEPS and ("npm" in (step.command or "") or "yarn" in (step.command or ""))
            for stage in pipeline.stages
            for job in stage.jobs
            for step in job.steps
        )

        if has_nodejs_deps and not self._has_cache_step(pipeline):
            opportunities.append({
                "type": "caching",
                "description": "Add npm/yarn cache to speed up dependency installation",
                "impact": "high",
                "effort": "low",
                "category": "performance"
            })

        return opportunities

    def detect_parallelization_opportunities(self, pipeline: UniversalPipeline) -> List[Dict[str, Any]]:
        """
        Detect opportunities for parallel execution to reduce build time.

        Args:
            pipeline: Pipeline to analyze

        Returns:
            List of parallelization optimization suggestions
        """
        opportunities = []

        # Check if multiple jobs in same stage could run in parallel
        for stage in pipeline.stages:
            if len(stage.jobs) > 1:
                # Check if jobs have dependencies
                independent_jobs = [job for job in stage.jobs if not job.needs]
                if len(independent_jobs) > 1:
                    opportunities.append({
                        "type": "parallelization",
                        "description": f"Run {len(independent_jobs)} independent jobs in parallel in '{stage.name}' stage",
                        "impact": "high",
                        "effort": "medium",
                        "category": "performance"
                    })

        # Check for matrix builds that could be expanded
        for stage in pipeline.stages:
            for job in stage.jobs:
                if job.matrix and len(job.matrix) == 1:
                    # Single dimension matrix, could add more dimensions
                    opportunities.append({
                        "type": "parallelization",
                        "description": f"Expand matrix build in '{job.name}' to test multiple combinations",
                        "impact": "medium",
                        "effort": "medium",
                        "category": "coverage"
                    })

        return opportunities

    def detect_security_improvements(self, pipeline: UniversalPipeline) -> List[Dict[str, Any]]:
        """
        Detect security improvements and best practices.

        Args:
            pipeline: Pipeline to analyze

        Returns:
            List of security improvement suggestions
        """
        improvements = []

        # Check for security scanning
        has_security_scan = any(
            "security" in (step.command or "").lower() or
            "scan" in (step.command or "").lower() or
            "sast" in (step.command or "").lower() or
            "dast" in (step.command or "").lower()
            for stage in pipeline.stages
            for job in stage.jobs
            for step in job.steps
        )

        if not has_security_scan:
            improvements.append({
                "type": "security",
                "description": "Add security scanning (SAST/DAST) to identify vulnerabilities",
                "impact": "high",
                "effort": "medium",
                "category": "security"
            })

        # Check for dependency vulnerability scanning
        has_dependency_scan = any(
            "audit" in (step.command or "").lower() or
            "check" in (step.command or "").lower() and ("vulnerability" in (step.command or "").lower() or "security" in (step.command or "").lower())
            for stage in pipeline.stages
            for job in stage.jobs
            for step in job.steps
        )

        if not has_dependency_scan:
            improvements.append({
                "type": "security",
                "description": "Add dependency vulnerability scanning",
                "impact": "medium",
                "effort": "low",
                "category": "security"
            })

        return improvements

    def detect_performance_optimizations(self, pipeline: UniversalPipeline) -> List[Dict[str, Any]]:
        """
        Detect performance optimization opportunities.

        Args:
            pipeline: Pipeline to analyze

        Returns:
            List of performance optimization suggestions
        """
        optimizations = []

        # Check for long-running jobs without timeout
        for stage in pipeline.stages:
            for job in stage.jobs:
                if job.timeout_minutes > 60:  # Default is 60
                    optimizations.append({
                        "type": "performance",
                        "description": f"Job '{job.name}' has long timeout ({job.timeout_minutes}min), consider optimizing or reducing",
                        "impact": "medium",
                        "effort": "high",
                        "category": "performance"
                    })

        # Check for redundant checkouts
        checkout_count = sum(
            1 for stage in pipeline.stages
            for job in stage.jobs
            for step in job.steps
            if step.type == StepType.CHECKOUT
        )

        if checkout_count > len(pipeline.stages):
            optimizations.append({
                "type": "performance",
                "description": "Multiple repository checkouts detected, consider using workspace sharing",
                "impact": "low",
                "effort": "medium",
                "category": "performance"
            })

        return optimizations

    def calculate_optimization_score(self, pipeline: UniversalPipeline) -> float:
        """
        Calculate an overall optimization score for the pipeline (0.0 to 1.0).

        Args:
            pipeline: Pipeline to score

        Returns:
            Optimization score (higher is better)
        """
        if not pipeline.stages:
            return 0.0

        score = 0.0
        max_score = 0.0

        # Caching score (0-0.2)
        max_score += 0.2
        if self._has_cache_step(pipeline):
            score += 0.2
        elif self.detect_caching_opportunities(pipeline):
            score += 0.1  # Partial credit for having dependencies that could be cached

        # Parallelization score (0-0.2)
        max_score += 0.2
        parallel_ops = self.detect_parallelization_opportunities(pipeline)
        if parallel_ops:
            score += 0.1  # Some parallelization possible
        else:
            score += 0.2  # Already well parallelized

        # Security score (0-0.3)
        max_score += 0.3
        security_improvements = self.detect_security_improvements(pipeline)
        security_score = max(0, 0.3 - (len(security_improvements) * 0.1))
        score += security_score

        # Performance score (0-0.3)
        max_score += 0.3
        perf_optimizations = self.detect_performance_optimizations(pipeline)
        perf_score = max(0, 0.3 - (len(perf_optimizations) * 0.1))
        score += perf_score

        return min(1.0, score / max_score) if max_score > 0 else 0.0

    def get_all_optimizations(self, pipeline: UniversalPipeline) -> Dict[str, Any]:
        """
        Get comprehensive optimization analysis.

        Args:
            pipeline: Pipeline to analyze

        Returns:
            Dictionary with all optimization categories and overall score
        """
        return {
            "caching": self.detect_caching_opportunities(pipeline),
            "parallelization": self.detect_parallelization_opportunities(pipeline),
            "security": self.detect_security_improvements(pipeline),
            "performance": self.detect_performance_optimizations(pipeline),
            "score": self.calculate_optimization_score(pipeline)
        }

    def optimize_with_llm(self, pipeline: UniversalPipeline) -> List[Dict[str, Any]]:
        """
        Get LLM-powered optimization suggestions.

        Args:
            pipeline: Pipeline to optimize

        Returns:
            LLM-generated optimization suggestions
        """
        return self.llm.optimize_pipeline(pipeline)

    def _has_cache_step(self, pipeline: UniversalPipeline) -> bool:
        """Check if pipeline already has caching steps."""
        return any(
            step.type in [StepType.CACHE_SAVE, StepType.CACHE_RESTORE]
            for stage in pipeline.stages
            for job in stage.jobs
            for step in job.steps
        )