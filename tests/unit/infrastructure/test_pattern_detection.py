"""Test pattern detection on Django models"""

import textwrap

from infrastructure.pattern_detector import PatternDetector


def test_audit_trail_pattern_detection():
    """Test audit trail pattern is detected"""
    source_code = textwrap.dedent(
        """
        from django.db import models

        class Article(models.Model):
            title = models.CharField(max_length=255)
            created_at = models.DateTimeField(auto_now_add=True)
            updated_at = models.DateTimeField(auto_now=True)
    """
    )

    detector = PatternDetector()
    patterns = detector.detect(source_code)

    # Should detect audit trail
    assert len(patterns) > 0
    assert any(p.name == "audit-trail" for p in patterns)

    audit_pattern = next(p for p in patterns if p.name == "audit-trail")
    assert audit_pattern.confidence >= 0.9  # High confidence


def test_soft_delete_pattern_detection():
    """Test soft delete pattern is detected"""
    source_code = textwrap.dedent(
        """
        from django.db import models

        class Document(models.Model):
            title = models.CharField(max_length=255)
            deleted_at = models.DateTimeField(null=True, blank=True)
            is_deleted = models.BooleanField(default=False)
    """
    )

    detector = PatternDetector()
    patterns = detector.detect(source_code)

    assert any(p.name == "soft-delete" for p in patterns)


def test_state_machine_pattern_detection():
    """Test state machine pattern is detected"""
    source_code = textwrap.dedent(
        """
        from django.db import models

        class Order(models.Model):
            status = models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('shipped', 'Shipped'),
                    ('delivered', 'Delivered'),
                ],
                default='pending'
            )
    """
    )

    detector = PatternDetector()
    patterns = detector.detect(source_code)

    assert any(p.name == "state-machine" for p in patterns)


def test_no_false_positives():
    """Test no patterns detected for simple model"""
    source_code = textwrap.dedent(
        """
        from django.db import models

        class SimpleModel(models.Model):
            name = models.CharField(max_length=255)
            value = models.IntegerField()
    """
    )

    detector = PatternDetector()
    patterns = detector.detect(source_code, min_confidence=0.5)

    # Should not detect any patterns
    assert len(patterns) == 0
