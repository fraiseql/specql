"""
Pattern Applicator - Apply detected patterns to AST for enhanced SpecQL output
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ASTResult:
    """Mock AST result structure - replace with actual AST types"""

    fields: Dict[str, Any] = None  # type: ignore
    metadata: Dict[str, Any] = None  # type: ignore

    def __post_init__(self):
        if self.fields is None:
            self.fields = {}
        if self.metadata is None:
            self.metadata = {}

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the AST result"""
        if not hasattr(self, "metadata"):
            self.metadata = {}
        self.metadata[key] = value

    def add_field_constraint(self, field_name: str, constraint_type: str, value: Any):
        """Add constraint to a field"""
        if field_name in self.fields:
            if not hasattr(self.fields[field_name], "constraints"):
                self.fields[field_name].constraints = {}
            self.fields[field_name].constraints[constraint_type] = value


def apply_patterns_to_ast(ast_result: Any, detected_patterns: Dict[str, Dict]) -> Any:
    """Apply detected patterns to AST to enrich SpecQL output

    Args:
        ast_result: The parsed AST result from reverse engineering
        detected_patterns: Dictionary of detected patterns with confidence scores

    Returns:
        Enhanced AST result with pattern metadata
    """

    # Ensure we have an AST result structure
    if not hasattr(ast_result, "metadata"):
        ast_result.metadata = {}
    if not hasattr(ast_result, "fields"):
        ast_result.fields = {}

    for pattern_name, pattern_data in detected_patterns.items():
        if pattern_data["confidence"] < 0.75:
            continue

        if pattern_name == "soft_delete":
            # Ensure deleted_at field is marked properly
            ast_result.add_metadata("soft_delete", True)
            if "deleted_at" in ast_result.fields:
                ast_result.add_field_constraint("deleted_at", "index", True)
                ast_result.add_field_constraint("deleted_at", "nullable", True)

        elif pattern_name == "audit_trail":
            # Mark audit fields as auto-managed
            audit_fields = ["created_at", "updated_at", "created_by", "updated_by"]
            for field_name in audit_fields:
                if field_name in ast_result.fields:
                    ast_result.add_field_constraint(field_name, "auto_managed", True)
                    ast_result.add_field_constraint(field_name, "nullable", False)

        elif pattern_name == "multi_tenant":
            # Add tenant isolation metadata
            ast_result.add_metadata("multi_tenant", True)
            if "tenant_id" in ast_result.fields:
                ast_result.add_field_constraint("tenant_id", "required", True)
                ast_result.add_field_constraint("tenant_id", "index", True)

        elif pattern_name == "state_machine":
            # Add state machine metadata
            ast_result.add_metadata("state_machine", True)
            # Look for status/state field
            status_fields = ["status", "state", "status_code"]
            for field_name in status_fields:
                if field_name in ast_result.fields:
                    ast_result.add_field_constraint(field_name, "enum", True)
                    break

        elif pattern_name == "hierarchical":
            # Add hierarchical metadata
            ast_result.add_metadata("hierarchical", True)
            if "parent_id" in ast_result.fields:
                ast_result.add_field_constraint("parent_id", "self_reference", True)
                ast_result.add_field_constraint("parent_id", "nullable", True)

        elif pattern_name == "versioning":
            # Add versioning metadata
            ast_result.add_metadata("versioning", True)
            if "version" in ast_result.fields:
                ast_result.add_field_constraint("version", "auto_increment", True)

        elif pattern_name == "event_sourcing":
            # Add event sourcing metadata
            ast_result.add_metadata("event_sourcing", True)

        elif pattern_name == "sharding":
            # Add sharding metadata
            ast_result.add_metadata("sharding", True)
            if "shard_key" in ast_result.fields:
                ast_result.add_field_constraint("shard_key", "shard_key", True)

        elif pattern_name == "cache_invalidation":
            # Add cache invalidation metadata
            ast_result.add_metadata("cache_invalidation", True)

        elif pattern_name == "rate_limiting":
            # Add rate limiting metadata
            ast_result.add_metadata("rate_limiting", True)

    return ast_result
