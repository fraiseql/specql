"""Pattern Aggregate Root"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class PatternCategory(Enum):
    """Valid pattern categories"""
    WORKFLOW = "workflow"
    VALIDATION = "validation"
    AUDIT = "audit"
    HIERARCHY = "hierarchy"
    STATE_MACHINE = "state_machine"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    CALCULATION = "calculation"
    SOFT_DELETE = "soft_delete"


class SourceType(Enum):
    """Pattern source types"""
    MANUAL = "manual"
    LLM_GENERATED = "llm_generated"
    DISCOVERED = "discovered"
    MIGRATED = "migrated"


@dataclass
class Pattern:
    """Pattern Aggregate Root - Domain pattern with business logic"""

    id: Optional[int]
    name: str
    category: PatternCategory
    description: str

    # Pattern definition
    parameters: Dict[str, Any] = field(default_factory=dict)
    implementation: Dict[str, Any] = field(default_factory=dict)

    # Vector embedding for similarity search
    embedding: Optional[List[float]] = None

    # Metadata
    times_instantiated: int = 0
    source_type: SourceType = SourceType.MANUAL
    complexity_score: Optional[float] = None
    deprecated: bool = False
    deprecated_reason: Optional[str] = None
    replacement_pattern_id: Optional[int] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate pattern data"""
        if not self.name or not self.name.strip():
            raise ValueError("Pattern name cannot be empty")

        if len(self.name) > 100:
            raise ValueError("Pattern name cannot exceed 100 characters")

        if not self.description or not self.description.strip():
            raise ValueError("Pattern description cannot be empty")

        if self.complexity_score is not None and (self.complexity_score < 0 or self.complexity_score > 10):
            raise ValueError("Complexity score must be between 0 and 10")

        if self.embedding is not None and len(self.embedding) != 384:
            raise ValueError("Embedding must be 384-dimensional vector")

    def mark_deprecated(self, reason: str, replacement_pattern_id: Optional[int] = None) -> None:
        """Mark pattern as deprecated with reason"""
        if not reason or not reason.strip():
            raise ValueError("Deprecation reason cannot be empty")

        self.deprecated = True
        self.deprecated_reason = reason
        self.replacement_pattern_id = replacement_pattern_id
        self.updated_at = datetime.now()

    def increment_usage(self) -> None:
        """Increment usage counter when pattern is instantiated"""
        self.times_instantiated += 1
        self.updated_at = datetime.now()

    def update_embedding(self, embedding: List[float]) -> None:
        """Update vector embedding for similarity search"""
        if len(embedding) != 384:
            raise ValueError("Embedding must be 384-dimensional vector")

        self.embedding = embedding
        self.updated_at = datetime.now()

    def is_similar_to(self, other_embedding: List[float], threshold: float = 0.7) -> bool:
        """Check if this pattern is similar to another based on embeddings"""
        if self.embedding is None or other_embedding is None:
            return False

        if len(self.embedding) != len(other_embedding):
            return False

        # Cosine similarity
        import math
        dot_product = sum(a * b for a, b in zip(self.embedding, other_embedding))
        magnitude_a = math.sqrt(sum(a * a for a in self.embedding))
        magnitude_b = math.sqrt(sum(b * b for b in other_embedding))

        if magnitude_a == 0 or magnitude_b == 0:
            return False

        similarity = dot_product / (magnitude_a * magnitude_b)
        return similarity >= threshold

    def can_be_used_for(self, context: Dict[str, Any]) -> bool:
        """Check if pattern can be used in given context"""
        if self.deprecated:
            return False

        # Check if required parameters are available in context
        required_params = self.parameters.get('required', [])
        for param in required_params:
            if param not in context:
                return False

        return True

    @property
    def is_active(self) -> bool:
        """Check if pattern is active (not deprecated)"""
        return not self.deprecated

    @property
    def has_embedding(self) -> bool:
        """Check if pattern has vector embedding"""
        return self.embedding is not None