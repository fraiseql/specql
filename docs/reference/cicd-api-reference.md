# CI/CD API Reference

This document provides comprehensive API reference for SpecQL's CI/CD pipeline system. It covers all public classes, methods, and functions available for programmatic use of the CI/CD features.

## 📦 Core Modules

### `src.cicd.universal_pipeline_schema`

The core data models for universal CI/CD pipelines.

#### UniversalPipeline

Main pipeline representation with conversion methods.

```python
class UniversalPipeline:
    """Universal CI/CD Pipeline Definition"""

    def __init__(
        self,
        name: str,
        description: str = "",
        language: str = "python",
        framework: Optional[str] = None,
        triggers: List[Trigger] = None,
        stages: List[Stage] = None,
        global_environment: Dict[str, str] = None,
        cache_paths: List[str] = None,
        pattern_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: List[str] = None,
        embedding: Optional[List[float]] = None
    ):
        """Initialize universal pipeline.

        Args:
            name: Pipeline name
            description: Human-readable description
            language: Programming language (python, node, go, rust, java)
            framework: Framework name (fastapi, django, express, react)
            triggers: List of pipeline triggers
            stages: List of pipeline stages
            global_environment: Global environment variables
            cache_paths: Paths to cache between runs
            pattern_id: Associated pattern identifier
            category: Pipeline category
            tags: Search tags
            embedding: Semantic search embedding
        """

    def to_github_actions(self) -> str:
        """Convert to GitHub Actions YAML.

        Returns:
            GitHub Actions workflow YAML string
        """

    def to_gitlab_ci(self) -> str:
        """Convert to GitLab CI YAML.

        Returns:
            GitLab CI pipeline YAML string
        """

    def to_circleci(self) -> str:
        """Convert to CircleCI YAML.

        Returns:
            CircleCI configuration YAML string
        """

    def to_jenkins(self) -> str:
        """Convert to Jenkins Pipeline.

        Returns:
            Jenkins Pipeline Groovy script
        """

    def to_azure(self) -> str:
        """Convert to Azure DevOps YAML.

        Returns:
            Azure DevOps pipeline YAML string
        """

    @classmethod
    def from_github_actions(cls, yaml_content: str) -> 'UniversalPipeline':
        """Parse GitHub Actions YAML to universal format.

        Args:
            yaml_content: GitHub Actions workflow YAML

        Returns:
            UniversalPipeline instance
        """

    @classmethod
    def from_gitlab_ci(cls, yaml_content: str) -> 'UniversalPipeline':
        """Parse GitLab CI YAML to universal format.

        Args:
            yaml_content: GitLab CI pipeline YAML

        Returns:
            UniversalPipeline instance
        """

    @classmethod
    def from_circleci(cls, yaml_content: str) -> 'UniversalPipeline':
        """Parse CircleCI YAML to universal format.

        Args:
            yaml_content: CircleCI configuration YAML

        Returns:
            UniversalPipeline instance
        """

    @classmethod
    def from_jenkins(cls, groovy_content: str) -> 'UniversalPipeline':
        """Parse Jenkins Pipeline to universal format.

        Args:
            groovy_content: Jenkins Pipeline Groovy script

        Returns:
            UniversalPipeline instance
        """

    @classmethod
    def from_azure(cls, yaml_content: str) -> 'UniversalPipeline':
        """Parse Azure DevOps YAML to universal format.

        Args:
            yaml_content: Azure DevOps pipeline YAML

        Returns:
            UniversalPipeline instance
        """
```

#### Trigger

Pipeline trigger configuration.

```python
class Trigger:
    """Pipeline trigger configuration"""

    def __init__(
        self,
        type: TriggerType,
        branches: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        paths: Optional[List[str]] = None,
        schedule: Optional[str] = None
    ):
        """Initialize trigger.

        Args:
            type: Trigger type (push, pull_request, schedule, etc.)
            branches: Branch filters
            tags: Tag filters
            paths: File path filters
            schedule: Cron schedule expression
        """
```

#### TriggerType

Enumeration of supported trigger types.

```python
class TriggerType(str, Enum):
    """Universal trigger types"""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    TAG = "tag"
    WEBHOOK = "webhook"
```

#### Stage

Pipeline stage containing jobs.

```python
class Stage:
    """Pipeline stage (logical grouping of jobs)"""

    def __init__(
        self,
        name: str,
        jobs: List[Job],
        approval_required: bool = False,
        environment: Optional[str] = None
    ):
        """Initialize stage.

        Args:
            name: Stage name
            jobs: List of jobs in this stage
            approval_required: Whether manual approval is required
            environment: Target environment (production, staging, etc.)
        """
```

#### Job

Individual pipeline job.

```python
class Job:
    """Pipeline job (collection of steps)"""

    def __init__(
        self,
        name: str,
        steps: List[Step],
        runtime: Optional[Runtime] = None,
        services: List[Service] = None,
        environment: Dict[str, str] = None,
        needs: List[str] = None,
        if_condition: Optional[str] = None,
        timeout_minutes: int = 60,
        matrix: Optional[Dict[str, List[str]]] = None
    ):
        """Initialize job.

        Args:
            name: Job name
            steps: List of steps to execute
            runtime: Runtime environment configuration
            services: External services (databases, etc.)
            environment: Job-specific environment variables
            needs: Job dependencies
            if_condition: Conditional execution expression
            timeout_minutes: Job timeout
            matrix: Matrix build configuration
        """
```

#### Step

Individual pipeline step.

```python
class Step:
    """Pipeline step (atomic action)"""

    def __init__(
        self,
        name: str,
        type: StepType,
        command: Optional[str] = None,
        with_params: Dict[str, Any] = None,
        environment: Dict[str, str] = None,
        working_directory: Optional[str] = None,
        continue_on_error: bool = False,
        timeout_minutes: Optional[int] = None
    ):
        """Initialize step.

        Args:
            name: Step name
            type: Step type
            command: Shell command to execute
            with_params: Platform-specific parameters
            environment: Step-specific environment variables
            working_directory: Working directory for step
            continue_on_error: Continue pipeline on step failure
            timeout_minutes: Step timeout
        """
```

#### StepType

Enumeration of supported step types.

```python
class StepType(str, Enum):
    """Universal step types"""
    RUN = "run"
    CHECKOUT = "checkout"
    SETUP_RUNTIME = "setup_runtime"
    INSTALL_DEPS = "install_dependencies"
    RUN_TESTS = "run_tests"
    LINT = "lint"
    BUILD = "build"
    DEPLOY = "deploy"
    UPLOAD_ARTIFACT = "upload_artifact"
    DOWNLOAD_ARTIFACT = "download_artifact"
    CACHE_SAVE = "cache_save"
    CACHE_RESTORE = "cache_restore"
```

#### Runtime

Runtime environment configuration.

```python
class Runtime:
    """Runtime environment configuration"""

    def __init__(
        self,
        language: str,
        version: str,
        package_manager: Optional[str] = None
    ):
        """Initialize runtime.

        Args:
            language: Programming language
            version: Language version
            package_manager: Package manager (pip, poetry, uv, npm, yarn)
        """
```

#### Service

External service configuration.

```python
class Service:
    """External service (database, cache, etc.)"""

    def __init__(
        self,
        name: str,
        version: str,
        environment: Dict[str, str] = None,
        ports: List[int] = None
    ):
        """Initialize service.

        Args:
            name: Service name (postgres, redis, mongodb)
            version: Service version
            environment: Service environment variables
            ports: Exposed ports
        """
```

## 🔄 Parsers

### `src.cicd.parsers.parser_factory`

Factory for auto-detecting and using correct parsers.

```python
class ParserFactory:
    """Factory for auto-detecting platform and parsing"""

    @staticmethod
    def parse_file(file_path: Path) -> UniversalPipeline:
        """Auto-detect platform and parse file.

        Args:
            file_path: Path to CI/CD config file

        Returns:
            UniversalPipeline instance

        Raises:
            ValueError: If platform cannot be detected or file is invalid
        """

    @staticmethod
    def detect_platform(content: str) -> str:
        """Detect platform from YAML content.

        Args:
            content: YAML content to analyze

        Returns:
            Platform identifier (github-actions, gitlab-ci, etc.)
        """
```

### Platform-Specific Parsers

#### GitHubActionsParser

```python
class GitHubActionsParser:
    """Parse GitHub Actions workflows to universal format"""

    def parse(self, yaml_content: str) -> UniversalPipeline:
        """Parse GitHub Actions YAML to UniversalPipeline.

        Args:
            yaml_content: GitHub Actions workflow YAML

        Returns:
            UniversalPipeline instance
        """
```

#### GitLabCIParser

```python
class GitLabCIParser:
    """Parse GitLab CI pipelines to universal format"""

    def parse(self, yaml_content: str) -> UniversalPipeline:
        """Parse GitLab CI YAML to UniversalPipeline.

        Args:
            yaml_content: GitLab CI pipeline YAML

        Returns:
            UniversalPipeline instance
        """
```

#### CircleCIParser

```python
class CircleCIParser:
    """Parse CircleCI configurations to universal format"""

    def parse(self, yaml_content: str) -> UniversalPipeline:
        """Parse CircleCI YAML to UniversalPipeline.

        Args:
            yaml_content: CircleCI configuration YAML

        Returns:
            UniversalPipeline instance
        """
```

#### JenkinsParser

```python
class JenkinsParser:
    """Parse Jenkins Pipelines to universal format"""

    def parse(self, groovy_content: str) -> UniversalPipeline:
        """Parse Jenkins Pipeline to UniversalPipeline.

        Args:
            groovy_content: Jenkins Pipeline Groovy script

        Returns:
            UniversalPipeline instance
        """
```

#### AzureParser

```python
class AzureParser:
    """Parse Azure DevOps pipelines to universal format"""

    def parse(self, yaml_content: str) -> UniversalPipeline:
        """Parse Azure DevOps YAML to UniversalPipeline.

        Args:
            yaml_content: Azure DevOps pipeline YAML

        Returns:
            UniversalPipeline instance
        """
```

## ⚙️ Generators

### Platform-Specific Generators

#### GitHubActionsGenerator

```python
class GitHubActionsGenerator:
    """Generate GitHub Actions workflows from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize generator.

        Args:
            template_dir: Custom template directory
        """

    def generate(self, pipeline: UniversalPipeline) -> str:
        """Generate GitHub Actions YAML from universal pipeline.

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            GitHub Actions workflow YAML string
        """
```

#### GitLabCIGenerator

```python
class GitLabCIGenerator:
    """Generate GitLab CI pipelines from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize generator.

        Args:
            template_dir: Custom template directory
        """

    def generate(self, pipeline: UniversalPipeline) -> str:
        """Generate GitLab CI YAML from universal pipeline.

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            GitLab CI pipeline YAML string
        """
```

#### CircleCIGenerator

```python
class CircleCIGenerator:
    """Generate CircleCI configurations from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize generator.

        Args:
            template_dir: Custom template directory
        """

    def generate(self, pipeline: UniversalPipeline) -> str:
        """Generate CircleCI YAML from universal pipeline.

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            CircleCI configuration YAML string
        """
```

#### JenkinsGenerator

```python
class JenkinsGenerator:
    """Generate Jenkins Pipelines from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize generator.

        Args:
            template_dir: Custom template directory
        """

    def generate(self, pipeline: UniversalPipeline) -> str:
        """Generate Jenkins Pipeline from universal pipeline.

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            Jenkins Pipeline Groovy script
        """
```

#### AzureGenerator

```python
class AzureGenerator:
    """Generate Azure DevOps pipelines from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize generator.

        Args:
            template_dir: Custom template directory
        """

    def generate(self, pipeline: UniversalPipeline) -> str:
        """Generate Azure DevOps YAML from universal pipeline.

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            Azure DevOps pipeline YAML string
        """
```

## 📚 Pattern Repository

### `src.cicd.pattern_repository`

Pattern storage and semantic search system.

```python
class PipelinePattern:
    """Reusable CI/CD pipeline pattern"""

    def __init__(
        self,
        pattern_id: str,
        name: str,
        description: str,
        category: str,
        pipeline: UniversalPipeline,
        tags: List[str] = None,
        language: str = "python",
        framework: Optional[str] = None,
        usage_count: int = 0,
        success_rate: float = 1.0,
        embedding: Optional[List[float]] = None,
        avg_duration_minutes: Optional[int] = None,
        reliability_score: float = 1.0
    ):
        """Initialize pipeline pattern.

        Args:
            pattern_id: Unique pattern identifier
            name: Human-readable name
            description: Pattern description
            category: Pattern category
            pipeline: Universal pipeline definition
            tags: Search tags
            language: Programming language
            framework: Framework name
            usage_count: Number of times used
            success_rate: Success rate (0.0-1.0)
            embedding: Semantic search embedding
            avg_duration_minutes: Average execution time
            reliability_score: Reliability score (0.0-1.0)
        """
```

```python
class PipelinePatternRepository(Protocol):
    """Protocol for pattern storage"""

    def store_pattern(self, pattern: PipelinePattern) -> None:
        """Store pipeline pattern.

        Args:
            pattern: Pattern to store
        """

    def find_by_id(self, pattern_id: str) -> Optional[PipelinePattern]:
        """Find pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            PipelinePattern if found, None otherwise
        """

    def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10
    ) -> List[PipelinePattern]:
        """Semantic search for similar patterns.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum results to return

        Returns:
            List of similar patterns
        """

    def search_by_tags(self, tags: List[str]) -> List[PipelinePattern]:
        """Find patterns by tags.

        Args:
            tags: List of tags to search for

        Returns:
            List of matching patterns
        """

    def search_by_category(self, category: str) -> List[PipelinePattern]:
        """Find patterns by category.

        Args:
            category: Category to search in

        Returns:
            List of patterns in category
        """

    def get_popular_patterns(self, limit: int = 10) -> List[PipelinePattern]:
        """Get most popular patterns.

        Args:
            limit: Maximum results to return

        Returns:
            List of popular patterns
        """

    def get_recommended_patterns(
        self,
        language: str,
        framework: Optional[str] = None,
        limit: int = 5
    ) -> List[PipelinePattern]:
        """Get recommended patterns for technology stack.

        Args:
            language: Programming language
            framework: Framework name
            limit: Maximum results to return

        Returns:
            List of recommended patterns
        """
```

## 🤖 LLM Recommendations

### `src.cicd.llm_recommendations`

AI-powered pipeline recommendations and optimization.

```python
class PipelineRecommender:
    """AI-powered pipeline recommendations"""

    def __init__(self, model: str = "llama3.1", temperature: float = 0.7):
        """Initialize recommender.

        Args:
            model: LLM model to use
            temperature: Generation temperature
        """

    def recommend_for_project(
        self,
        language: str,
        framework: Optional[str] = None,
        database: Optional[str] = None,
        deployment: Optional[str] = None
    ) -> List[Recommendation]:
        """Get recommendations for project type.

        Args:
            language: Programming language
            framework: Framework name
            database: Database type
            deployment: Deployment target

        Returns:
            List of recommendations
        """

    def analyze_pipeline(self, pipeline: UniversalPipeline) -> AnalysisResult:
        """Analyze existing pipeline for improvements.

        Args:
            pipeline: Pipeline to analyze

        Returns:
            Analysis results with suggestions
        """

    def suggest_optimizations(
        self,
        pipeline: UniversalPipeline,
        focus_areas: List[str] = None
    ) -> List[Optimization]:
        """Suggest pipeline optimizations.

        Args:
            pipeline: Pipeline to optimize
            focus_areas: Areas to focus on (caching, parallelization, etc.)

        Returns:
            List of optimization suggestions
        """

    def generate_pattern_from_description(
        self,
        description: str,
        language: str,
        framework: Optional[str] = None
    ) -> UniversalPipeline:
        """Generate pipeline from natural language description.

        Args:
            description: Natural language pipeline description
            language: Programming language
            framework: Framework name

        Returns:
            Generated universal pipeline
        """
```

```python
class Recommendation:
    """Pipeline recommendation"""

    def __init__(
        self,
        title: str,
        description: str,
        confidence: float,
        pattern_id: Optional[str] = None,
        customizations: Dict[str, Any] = None
    ):
        """Initialize recommendation.

        Args:
            title: Recommendation title
            description: Detailed description
            confidence: Confidence score (0.0-1.0)
            pattern_id: Recommended pattern ID
            customizations: Pattern customizations
        """
```

## ⚡ Performance Benchmarking

### `src.cicd.performance_benchmark`

Automated pipeline performance testing and analysis.

```python
class PipelineBenchmarker:
    """Pipeline performance benchmarking"""

    def __init__(self, iterations: int = 5, timeout_minutes: int = 30):
        """Initialize benchmarker.

        Args:
            iterations: Number of benchmark iterations
            timeout_minutes: Timeout per benchmark
        """

    def benchmark_execution(
        self,
        pipeline: UniversalPipeline,
        platforms: List[str] = None
    ) -> BenchmarkResult:
        """Benchmark pipeline execution time.

        Args:
            pipeline: Pipeline to benchmark
            platforms: Platforms to test (default: all)

        Returns:
            Benchmark results
        """

    def benchmark_resources(
        self,
        pipeline: UniversalPipeline,
        platforms: List[str] = None
    ) -> ResourceBenchmarkResult:
        """Benchmark resource usage.

        Args:
            pipeline: Pipeline to benchmark
            platforms: Platforms to test

        Returns:
            Resource usage results
        """

    def compare_platforms(
        self,
        pipeline: UniversalPipeline,
        platforms: List[str]
    ) -> PlatformComparison:
        """Compare performance across platforms.

        Args:
            pipeline: Pipeline to test
            platforms: Platforms to compare

        Returns:
            Platform comparison results
        """

    def benchmark_reliability(
        self,
        pipeline: UniversalPipeline,
        runs: int = 10
    ) -> ReliabilityResult:
        """Test pipeline reliability.

        Args:
            pipeline: Pipeline to test
            runs: Number of test runs

        Returns:
            Reliability metrics
        """
```

```python
class BenchmarkResult:
    """Benchmark execution results"""

    def __init__(
        self,
        pipeline_name: str,
        platform: str,
        execution_times: List[float],
        avg_time: float,
        min_time: float,
        max_time: float,
        success_rate: float,
        timestamp: datetime
    ):
        """Initialize benchmark result.

        Args:
            pipeline_name: Name of benchmarked pipeline
            platform: Target platform
            execution_times: Individual execution times
            avg_time: Average execution time
            min_time: Minimum execution time
            max_time: Maximum execution time
            success_rate: Success rate (0.0-1.0)
            timestamp: Benchmark timestamp
        """
```

## 🔧 Pipeline Optimizer

### `src.cicd.pipeline_optimizer`

Automatic pipeline optimization and improvement.

```python
class PipelineOptimizer:
    """Automatic pipeline optimization"""

    def __init__(self, llm_model: str = "llama3.1"):
        """Initialize optimizer.

        Args:
            llm_model: LLM model for recommendations
        """

    def optimize_pipeline(
        self,
        pipeline: UniversalPipeline,
        optimizations: List[str] = None
    ) -> OptimizationResult:
        """Optimize pipeline automatically.

        Args:
            pipeline: Pipeline to optimize
            optimizations: Specific optimizations to apply

        Returns:
            Optimization results
        """

    def add_caching(self, pipeline: UniversalPipeline) -> UniversalPipeline:
        """Add intelligent caching strategies.

        Args:
            pipeline: Pipeline to enhance

        Returns:
            Pipeline with caching optimizations
        """

    def optimize_parallelization(
        self,
        pipeline: UniversalPipeline
    ) -> UniversalPipeline:
        """Optimize job parallelization.

        Args:
            pipeline: Pipeline to optimize

        Returns:
            Pipeline with parallelization improvements
        """

    def add_security_scanning(
        self,
        pipeline: UniversalPipeline
    ) -> UniversalPipeline:
        """Add security scanning steps.

        Args:
            pipeline: Pipeline to enhance

        Returns:
            Pipeline with security scanning
        """

    def optimize_for_platform(
        self,
        pipeline: UniversalPipeline,
        platform: str
    ) -> UniversalPipeline:
        """Optimize pipeline for specific platform.

        Args:
            pipeline: Pipeline to optimize
            platform: Target platform

        Returns:
            Platform-optimized pipeline
        """
```

## 📊 Exceptions

### CICDError

Base exception for CI/CD operations.

```python
class CICDError(Exception):
    """Base exception for CI/CD operations"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize error.

        Args:
            message: Error message
            details: Additional error details
        """
```

### ValidationError

Pipeline validation errors.

```python
class ValidationError(CICDError):
    """Pipeline validation error"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
        """
```

### ConversionError

Pipeline conversion errors.

```python
class ConversionError(CICDError):
    """Pipeline conversion error"""

    def __init__(
        self,
        message: str,
        source_platform: Optional[str] = None,
        target_platform: Optional[str] = None,
        step: Optional[str] = None
    ):
        """Initialize conversion error.

        Args:
            message: Error message
            source_platform: Source platform
            target_platform: Target platform
            step: Conversion step that failed
        """
```

### PatternNotFoundError

Pattern lookup errors.

```python
class PatternNotFoundError(CICDError):
    """Pattern not found error"""

    def __init__(self, pattern_id: str, search_terms: Optional[List[str]] = None):
        """Initialize pattern error.

        Args:
            pattern_id: Pattern identifier that was not found
            search_terms: Search terms that were used
        """
```

## 🔧 Utility Functions

### Pipeline Validation

```python
def validate_pipeline(pipeline: UniversalPipeline) -> ValidationResult:
    """Validate universal pipeline.

    Args:
        pipeline: Pipeline to validate

    Returns:
        Validation results
    """

def validate_pipeline_yaml(yaml_content: str) -> ValidationResult:
    """Validate pipeline YAML content.

    Args:
        yaml_content: YAML content to validate

    Returns:
        Validation results
    """
```

### Platform Detection

```python
def detect_platform_from_file(file_path: Path) -> str:
    """Detect CI/CD platform from file path and content.

    Args:
        file_path: Path to CI/CD configuration file

    Returns:
        Platform identifier
    """

def detect_platform_from_content(content: str) -> str:
    """Detect CI/CD platform from content.

    Args:
        content: File content to analyze

    Returns:
        Platform identifier
    """
```

### Pattern Utilities

```python
def create_pattern_from_pipeline(
    pipeline: UniversalPipeline,
    pattern_id: str,
    name: str,
    description: str,
    category: str
) -> PipelinePattern:
    """Create pattern from pipeline.

    Args:
        pipeline: Universal pipeline
        pattern_id: Pattern identifier
        name: Pattern name
        description: Pattern description
        category: Pattern category

    Returns:
        PipelinePattern instance
    """

def generate_pattern_embedding(pattern: PipelinePattern) -> List[float]:
    """Generate semantic embedding for pattern.

    Args:
        pattern: Pattern to embed

    Returns:
        Embedding vector
    """
```

## 📋 Type Definitions

```python
from typing import List, Dict, Any, Optional, Protocol
from pathlib import Path
from datetime import datetime
from enum import Enum

# Core types
PipelineDict = Dict[str, Any]
ValidationResult = Dict[str, Any]
BenchmarkResult = Dict[str, Any]
OptimizationResult = Dict[str, Any]
AnalysisResult = Dict[str, Any]

# Protocol for pattern repositories
class PatternRepositoryProtocol(Protocol):
    def store_pattern(self, pattern: PipelinePattern) -> None: ...
    def find_by_id(self, pattern_id: str) -> Optional[PipelinePattern]: ...
    def search_by_similarity(self, embedding: List[float], limit: int = 10) -> List[PipelinePattern]: ...
```

## 🎯 Usage Examples

### Basic Pipeline Creation

```python
from src.cicd.universal_pipeline_schema import UniversalPipeline, Trigger, TriggerType, Stage, Job, Step, StepType

# Create a simple pipeline
pipeline = UniversalPipeline(
    name="my_app",
    language="python",
    framework="fastapi",
    triggers=[
        Trigger(type=TriggerType.PUSH, branches=["main"]),
        Trigger(type=TriggerType.PULL_REQUEST)
    ],
    stages=[
        Stage(
            name="test",
            jobs=[
                Job(
                    name="test",
                    steps=[
                        Step(name="Checkout", type=StepType.CHECKOUT),
                        Step(name="Setup Python", type=StepType.SETUP_RUNTIME),
                        Step(name="Install deps", type=StepType.INSTALL_DEPS,
                             command="pip install -e .[dev]"),
                        Step(name="Run tests", type=StepType.RUN_TESTS,
                             command="pytest")
                    ]
                )
            ]
        )
    ]
)

# Convert to GitHub Actions
github_yaml = pipeline.to_github_actions()
print(github_yaml)
```

### Pattern Usage

```python
from src.cicd.pattern_repository import PipelinePatternRepository

# Initialize repository
repo = PipelinePatternRepository()

# Search for patterns
patterns = repo.search_by_tags(["python", "fastapi"])
recommended = repo.get_recommended_patterns("python", "fastapi")

# Use a pattern
pattern = repo.find_by_id("python_fastapi_backend")
if pattern:
    # Customize the pattern
    custom_pipeline = pattern.pipeline
    # Modify as needed
    github_yaml = custom_pipeline.to_github_actions()
```

### Reverse Engineering

```python
from src.cicd.parsers.parser_factory import ParserFactory
from pathlib import Path

# Parse existing pipeline
existing_pipeline = ParserFactory.parse_file(Path(".github/workflows/ci.yml"))

# Convert to different platform
gitlab_yaml = existing_pipeline.to_gitlab_ci()
circle_yaml = existing_pipeline.to_circleci()
```

### Performance Benchmarking

```python
from src.cicd.performance_benchmark import PipelineBenchmarker

benchmarker = PipelineBenchmarker(iterations=5)

# Benchmark pipeline
results = benchmarker.benchmark_execution(pipeline, platforms=["github-actions", "gitlab-ci"])

# Print results
for result in results:
    print(f"{result.platform}: {result.avg_time:.2f}s avg, {result.success_rate:.1%} success")
```

This API reference covers all public interfaces for programmatic use of SpecQL's CI/CD features. For CLI usage, see the [CLI Commands Reference](../reference/cli_commands.md).