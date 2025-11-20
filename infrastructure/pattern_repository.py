"""
Infrastructure Pattern Repository

Stores reusable infrastructure patterns with semantic search.
"""

from dataclasses import dataclass
from typing import Protocol

from infrastructure.universal_infra_schema import UniversalInfrastructure


@dataclass
class InfrastructurePattern:
    """Reusable infrastructure pattern"""

    pattern_id: str
    name: str
    description: str
    category: str  # web_app, microservices, data_pipeline, ml_infrastructure

    # Pattern definition
    infrastructure: UniversalInfrastructure

    # Metadata
    tags: list[str]
    cloud_provider: str  # aws, gcp, azure, multi-cloud

    # Cost
    estimated_monthly_cost: float
    cost_optimization_tips: list[str]

    # Usage
    usage_count: int = 0
    reliability_score: float = 1.0

    # Semantic search
    embedding: list[float] | None = None


class InfrastructurePatternRepository(Protocol):
    """Protocol for infrastructure pattern storage"""

    def store_pattern(self, pattern: InfrastructurePattern) -> None:
        """Store infrastructure pattern"""
        ...

    def find_by_id(self, pattern_id: str) -> InfrastructurePattern | None:
        """Find pattern by ID"""
        ...

    def search_by_similarity(
        self, query_embedding: list[float], limit: int = 10
    ) -> list[InfrastructurePattern]:
        """Semantic search for similar patterns"""
        ...

    def search_by_cost(self, max_monthly_cost: float) -> list[InfrastructurePattern]:
        """Find patterns within budget"""
        ...
