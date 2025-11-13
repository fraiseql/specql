"""Pattern deduplication service"""
from typing import List, Tuple, Dict, Any
import numpy as np

from src.application.services.pattern_service import PatternService
from src.domain.entities.pattern import Pattern
from src.infrastructure.services.embedding_service import get_embedding_service


class PatternDeduplicator:
    """
    Detects and merges duplicate patterns

    Uses semantic similarity (embeddings) + name similarity
    to find potential duplicates
    """

    def __init__(self, service: PatternService):
        self.service = service
        self.embedding_service = get_embedding_service()

    def find_duplicates(
        self,
        similarity_threshold: float = 0.9
    ) -> List[List[Pattern]]:
        """
        Find groups of duplicate patterns

        Args:
            similarity_threshold: Minimum similarity to consider duplicates (0.9 = 90%)

        Returns:
            List of duplicate groups, each group contains 2+ similar patterns
        """
        all_patterns = self.service.repository.list_all()

        # Filter out deprecated patterns
        active_patterns = [p for p in all_patterns if not p.deprecated]

        # Build similarity matrix
        duplicate_groups = []
        processed = set()

        for i, pattern1 in enumerate(active_patterns):
            if pattern1.id in processed:
                continue

            # Find similar patterns
            similar = [pattern1]

            for j, pattern2 in enumerate(active_patterns[i+1:], start=i+1):
                if pattern2.id in processed:
                    continue

                similarity = self.calculate_similarity(pattern1, pattern2)

                if similarity >= similarity_threshold:
                    similar.append(pattern2)
                    processed.add(pattern2.id)

            # If found duplicates, add group
            if len(similar) > 1:
                duplicate_groups.append(similar)
                processed.add(pattern1.id)

        return duplicate_groups

    def calculate_similarity(
        self,
        pattern1: Pattern,
        pattern2: Pattern
    ) -> float:
        """
        Calculate similarity between two patterns

        Combines:
        - Semantic similarity (embeddings)
        - Name similarity (Levenshtein distance)
        - Category match

        Returns:
            Similarity score 0.0-1.0
        """
        signals = []

        # Signal 1: Embedding similarity (70% weight)
        if pattern1.embedding and pattern2.embedding:
            emb1 = np.array(pattern1.embedding)
            emb2 = np.array(pattern2.embedding)
            semantic_sim = self.embedding_service.cosine_similarity(emb1, emb2)
            signals.append(("semantic", semantic_sim, 0.7))

        # Signal 2: Name similarity (20% weight)
        name_sim = self._name_similarity(pattern1.name, pattern2.name)
        signals.append(("name", name_sim, 0.2))

        # Signal 3: Category match (10% weight)
        category_match = 1.0 if pattern1.category == pattern2.category else 0.0
        signals.append(("category", category_match, 0.1))

        # Weighted average
        if not signals:
            return 0.0

        total_weight = sum(weight for _, _, weight in signals)
        weighted_sum = sum(score * weight for _, score, weight in signals)

        return weighted_sum / total_weight

    def suggest_merge(
        self,
        duplicate_group: List[Pattern],
        strategy: str = "most_used"
    ) -> Dict[str, Any]:
        """
        Suggest which pattern to keep and which to merge

        Args:
            duplicate_group: Group of duplicate patterns
            strategy: Merge strategy ("most_used", "oldest", "newest")

        Returns:
            {
                "keep": Pattern to keep,
                "merge": [Patterns to merge into kept pattern],
                "reason": Explanation
            }
        """
        if len(duplicate_group) < 2:
            raise ValueError("Need at least 2 patterns to merge")

        if strategy == "most_used":
            # Keep pattern with most instantiations
            sorted_patterns = sorted(
                duplicate_group,
                key=lambda p: p.times_instantiated,
                reverse=True
            )
            keep = sorted_patterns[0]
            merge = sorted_patterns[1:]
            reason = f"Kept most used pattern ({keep.times_instantiated} uses)"

        elif strategy == "oldest":
            # Keep builtin patterns over imported
            builtin = [p for p in duplicate_group if p.source_type.value == "manual"]
            if builtin:
                keep = builtin[0]
                merge = [p for p in duplicate_group if p != keep]
                reason = "Kept original manual pattern"
            else:
                # All imported, keep first
                keep = duplicate_group[0]
                merge = duplicate_group[1:]
                reason = "Kept first imported pattern"

        elif strategy == "newest":
            # Keep most recently created (highest ID)
            sorted_patterns = sorted(
                duplicate_group,
                key=lambda p: p.id if p.id else 0,
                reverse=True
            )
            keep = sorted_patterns[0]
            merge = sorted_patterns[1:]
            reason = "Kept newest pattern"

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        return {
            "keep": keep,
            "merge": merge,
            "reason": reason
        }

    def merge_patterns(
        self,
        keep: Pattern,
        merge: List[Pattern]
    ) -> Pattern:
        """
        Merge duplicate patterns

        - Marks merged patterns as deprecated
        - Points them to the kept pattern
        - Combines usage statistics

        Args:
            keep: Pattern to keep
            merge: Patterns to merge into kept pattern

        Returns:
            Updated kept pattern
        """
        # Sum usage counts
        total_uses = keep.times_instantiated
        for pattern in merge:
            total_uses += pattern.times_instantiated

        # Update kept pattern
        keep.times_instantiated = total_uses

        # Save kept pattern
        self.service.repository.save(keep)

        # Deprecate merged patterns
        for pattern in merge:
            pattern.deprecated = True
            pattern.deprecated_reason = f"Duplicate of {keep.name}"
            pattern.replacement_pattern_id = keep.id
            self.service.repository.save(pattern)

        return keep

    @staticmethod
    def _name_similarity(name1: str, name2: str) -> float:
        """
        Calculate name similarity using Levenshtein distance

        Returns similarity 0.0-1.0
        """
        if name1 == name2:
            return 1.0

        if len(name1) == 0 or len(name2) == 0:
            return 0.0

        # Calculate edit distance
        distance = PatternDeduplicator._levenshtein_distance(name1, name2)

        # Convert to similarity (0-1)
        max_len = max(len(name1), len(name2))
        similarity = 1.0 - (distance / max_len)

        return similarity

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance"""
        if len(s1) < len(s2):
            return PatternDeduplicator._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]

            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]