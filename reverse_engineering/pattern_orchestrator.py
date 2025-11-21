"""
Pattern Detection Orchestrator

Coordinates all pattern detectors to provide comprehensive pattern analysis.
"""

from dataclasses import dataclass
from typing import List

from .table_parser import ParsedTable
from .trinity_detector import TrinityPatternDetector
from .audit_detector import AuditTrailDetector
from .translation_detector import TranslationTableDetector


@dataclass
class PatternDetectionResult:
    """Result of comprehensive pattern detection."""

    patterns: List[str]
    confidence: float


class PatternDetectionOrchestrator:
    """Orchestrates all pattern detectors for comprehensive analysis."""

    def __init__(self):
        self.trinity_detector = TrinityPatternDetector()
        self.audit_detector = AuditTrailDetector()
        self.translation_detector = TranslationTableDetector()

    def detect_all(self, table: ParsedTable) -> PatternDetectionResult:
        """Run all pattern detectors and aggregate results."""
        patterns = []
        confidence_scores = []

        # Detect Trinity pattern
        trinity_result = self.trinity_detector.detect(table)
        if trinity_result.has_trinity_pattern:
            patterns.append("trinity")
            confidence_scores.append(0.9)  # High confidence for Trinity detection

        # Detect audit trail
        audit_result = self.audit_detector.detect(table)
        if audit_result.has_audit_trail:
            patterns.append("audit_trail")
            confidence_scores.append(audit_result.confidence)

        if audit_result.has_soft_delete:
            patterns.append("soft_delete")
            confidence_scores.append(0.8)  # Soft delete is a subset of audit

        # Detect translation table
        translation_result = self.translation_detector.detect(table)
        if translation_result.is_translation_table:
            patterns.append("translation")
            confidence_scores.append(0.95)  # High confidence for translation detection

        # Calculate overall confidence
        if confidence_scores:
            overall_confidence = sum(confidence_scores) / len(confidence_scores)
        else:
            overall_confidence = 0.0

        return PatternDetectionResult(patterns=patterns, confidence=overall_confidence)
