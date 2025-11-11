# src/adapters/__init__.py
"""
Framework Adapters Package

This package contains adapters that convert Universal AST entities
into framework-specific code (PostgreSQL, Django, Rails, etc.)
"""

from .base_adapter import FrameworkAdapter, GeneratedCode, FrameworkConventions

__all__ = ["FrameworkAdapter", "GeneratedCode", "FrameworkConventions"]
