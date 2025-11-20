"""Generate PostgreSQL JSONB helper functions."""


class JSONBHelpersGenerator:
    """Generate JSONB utility functions for patterns."""

    @staticmethod
    def generate_deep_merge() -> str:
        """Generate jsonb_deep_merge aggregate function."""
        return """
-- Deep merge JSONB objects (child overrides parent)
CREATE OR REPLACE FUNCTION jsonb_deep_merge(jsonb, jsonb)
RETURNS jsonb
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT
    jsonb_object_agg(
      key,
      CASE
        WHEN jsonb_typeof($1->key) = 'object' AND jsonb_typeof($2->key) = 'object'
        THEN jsonb_deep_merge($1->key, $2->key)
        ELSE coalesce($2->key, $1->key)
      END
    )
  FROM (
    SELECT key FROM jsonb_object_keys($1)
    UNION
    SELECT key FROM jsonb_object_keys($2)
  ) keys;
$$;

-- Aggregate function for multiple JSONB objects
CREATE OR REPLACE AGGREGATE jsonb_deep_merge_agg(jsonb) (
  SFUNC = jsonb_deep_merge,
  STYPE = jsonb,
  INITCOND = '{}'
);
"""

    @staticmethod
    def generate_append_recursive() -> str:
        """Generate jsonb_append_recursive for array concatenation."""
        return """
-- Append arrays, merge objects recursively
CREATE OR REPLACE FUNCTION jsonb_append_recursive(jsonb, jsonb)
RETURNS jsonb
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT
    CASE
      WHEN jsonb_typeof($1) = 'array' AND jsonb_typeof($2) = 'array'
      THEN $1 || $2

      WHEN jsonb_typeof($1) = 'object' AND jsonb_typeof($2) = 'object'
      THEN jsonb_deep_merge($1, $2)

      ELSE coalesce($2, $1)
    END;
$$;
"""
