"""
CI/CD Pattern Repository

Stores reusable pipeline patterns with semantic search capabilities.
Same architecture as domain pattern library.
"""

from dataclasses import dataclass
from typing import List, Optional, Protocol
from src.cicd.universal_pipeline_schema import UniversalPipeline


@dataclass
class PipelinePattern:
    """Reusable CI/CD pipeline pattern"""
    pattern_id: str
    name: str
    description: str
    category: str  # backend, frontend, fullstack, data, mobile

    # Pattern definition
    pipeline: UniversalPipeline

    # Metadata
    tags: List[str]
    language: str
    framework: Optional[str] = None

    # Usage statistics
    usage_count: int = 0
    success_rate: float = 1.0

    # Semantic search
    embedding: Optional[List[float]] = None

    # Quality metrics
    avg_duration_minutes: Optional[int] = None
    reliability_score: float = 1.0


class PipelinePatternRepository(Protocol):
    """Protocol for pattern storage"""

    def store_pattern(self, pattern: PipelinePattern) -> None:
        """Store pipeline pattern"""
        ...

    def find_by_id(self, pattern_id: str) -> Optional[PipelinePattern]:
        """Find pattern by ID"""
        ...

    def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10
    ) -> List[PipelinePattern]:
        """Semantic search for similar patterns"""
        ...

    def search_by_tags(self, tags: List[str]) -> List[PipelinePattern]:
        """Find patterns by tags"""
        ...

    def search_by_category(self, category: str) -> List[PipelinePattern]:
        """Find patterns by category"""
        ...