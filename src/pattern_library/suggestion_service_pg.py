"""
Pattern Suggestion Service using PostgreSQL

Manages the human-in-the-loop workflow for pattern discovery and approval.
"""

import os
from typing import Dict, List, Optional
import psycopg
from pgvector.psycopg import register_vector


class PatternSuggestionService:
    """
    Service for managing pattern suggestions in PostgreSQL.

    Handles the workflow:
    1. Create suggestions from reverse engineering
    2. List pending suggestions for review
    3. Approve/reject suggestions
    4. Move approved patterns to domain_patterns table
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize suggestion service.

        Args:
            connection_string: PostgreSQL connection string (or uses SPECQL_DB_URL env)
        """
        self.conn_string = connection_string or os.getenv('SPECQL_DB_URL')
        if not self.conn_string:
            raise ValueError("No connection string provided and SPECQL_DB_URL not set")

        self.conn = psycopg.connect(self.conn_string)
        register_vector(self.conn)

        print("✓ Pattern suggestion service ready (PostgreSQL + pgvector)")

    def create_suggestion(
        self,
        suggested_name: str,
        suggested_category: str,
        description: str,
        parameters: Optional[Dict] = None,
        implementation: Optional[Dict] = None,
        source_type: str = 'manual',
        source_sql: Optional[str] = None,
        source_description: Optional[str] = None,
        source_function_id: Optional[str] = None,
        complexity_score: Optional[float] = None,
        confidence_score: Optional[float] = None,
        trigger_reason: Optional[str] = None
    ) -> Optional[int]:
        """
        Create a new pattern suggestion.

        Args:
            suggested_name: Proposed pattern name
            suggested_category: Proposed category
            description: Pattern description
            parameters: JSON schema for parameters
            implementation: SpecQL implementation structure
            source_type: How this suggestion was created
            source_sql: Original SQL that triggered discovery
            source_description: Additional context
            source_function_id: Function that triggered discovery
            complexity_score: Complexity score (0-1)
            confidence_score: Confidence in suggestion (0-1)
            trigger_reason: Why this was suggested

        Returns:
            Suggestion ID if created successfully, None otherwise
        """
        try:
            cursor = self.conn.execute(
                """
                INSERT INTO pattern_library.pattern_suggestions (
                    suggested_name, suggested_category, description,
                    parameters, implementation, source_type, source_sql,
                    source_description, source_function_id,
                    complexity_score, confidence_score, trigger_reason
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    suggested_name, suggested_category, description,
                    parameters or {}, implementation or {},
                    source_type, source_sql, source_description, source_function_id,
                    complexity_score, confidence_score, trigger_reason
                )
            )

            result = cursor.fetchone()
            self.conn.commit()

            if result:
                suggestion_id = result[0]
                print(f"✓ Created pattern suggestion #{suggestion_id}: {suggested_name}")
                return suggestion_id

        except Exception as e:
            print(f"❌ Failed to create pattern suggestion: {e}")
            self.conn.rollback()

        return None

    def list_pending(self, limit: int = 50) -> List[Dict]:
        """
        List pending pattern suggestions for review.

        Args:
            limit: Maximum number of suggestions to return

        Returns:
            List of pending suggestions
        """
        try:
            cursor = self.conn.execute(
                """
                SELECT
                    id, suggested_name, suggested_category, description,
                    confidence_score, complexity_score, source_type,
                    created_at, hours_pending
                FROM pattern_library.pending_reviews
                ORDER BY confidence_score DESC, created_at ASC
                LIMIT %s
                """,
                (limit,)
            )

            suggestions = []
            for row in cursor:
                suggestions.append({
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'description': row[3],
                    'confidence': float(row[4]) if row[4] else None,
                    'complexity': float(row[5]) if row[5] else None,
                    'source_type': row[6],
                    'created_at': row[7],
                    'hours_pending': float(row[8]) if row[8] else 0
                })

            return suggestions

        except Exception as e:
            print(f"❌ Failed to list pending suggestions: {e}")
            return []

    def get_suggestion(self, suggestion_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific suggestion.

        Args:
            suggestion_id: Suggestion ID

        Returns:
            Suggestion details or None if not found
        """
        try:
            cursor = self.conn.execute(
                """
                SELECT
                    id, suggested_name, suggested_category, description,
                    parameters, implementation, source_type, source_sql,
                    source_description, source_function_id,
                    complexity_score, confidence_score, trigger_reason,
                    status, created_at
                FROM pattern_library.pattern_suggestions
                WHERE id = %s
                """,
                (suggestion_id,)
            )

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'description': row[3],
                'parameters': row[4],
                'implementation': row[5],
                'source_type': row[6],
                'source_sql': row[7],
                'source_description': row[8],
                'source_function_id': row[9],
                'complexity_score': float(row[10]) if row[10] else None,
                'confidence_score': float(row[11]) if row[11] else None,
                'trigger_reason': row[12],
                'status': row[13],
                'created_at': row[14]
            }

        except Exception as e:
            print(f"❌ Failed to get suggestion {suggestion_id}: {e}")
            return None

    def approve_suggestion(self, suggestion_id: int, reviewer: str = 'system') -> bool:
        """
        Approve a pattern suggestion and move it to domain_patterns.

        Args:
            suggestion_id: Suggestion to approve
            reviewer: Who approved it

        Returns:
            True if approved successfully
        """
        try:
            # Get suggestion details
            suggestion = self.get_suggestion(suggestion_id)
            if not suggestion:
                print(f"❌ Suggestion {suggestion_id} not found")
                return False

            if suggestion['status'] != 'pending':
                print(f"❌ Suggestion {suggestion_id} is not pending (status: {suggestion['status']})")
                return False

            # Move to domain_patterns
            cursor = self.conn.execute(
                """
                INSERT INTO pattern_library.domain_patterns (
                    name, category, description, parameters, implementation,
                    source_type, complexity_score
                )
                VALUES (%s, %s, %s, %s, %s, 'discovered', %s)
                RETURNING id
                """,
                (
                    suggestion['name'],
                    suggestion['category'],
                    suggestion['description'],
                    suggestion['parameters'],
                    suggestion['implementation'],
                    suggestion['complexity_score']
                )
            )

            result = cursor.fetchone()
            if not result:
                raise Exception("Failed to insert into domain_patterns")

            pattern_id = result[0]

            # Update suggestion status
            self.conn.execute(
                """
                UPDATE pattern_library.pattern_suggestions
                SET status = 'approved',
                    reviewed_by = %s,
                    reviewed_at = now(),
                    merged_into_pattern_id = %s
                WHERE id = %s
                """,
                (reviewer, pattern_id, suggestion_id)
            )

            self.conn.commit()

            print(f"✓ Approved suggestion #{suggestion_id} → pattern #{pattern_id}: {suggestion['name']}")
            return True

        except Exception as e:
            print(f"❌ Failed to approve suggestion {suggestion_id}: {e}")
            self.conn.rollback()
            return False

    def reject_suggestion(self, suggestion_id: int, reason: str, reviewer: str = 'system') -> bool:
        """
        Reject a pattern suggestion.

        Args:
            suggestion_id: Suggestion to reject
            reason: Reason for rejection
            reviewer: Who rejected it

        Returns:
            True if rejected successfully
        """
        try:
            # Update suggestion status
            cursor = self.conn.execute(
                """
                UPDATE pattern_library.pattern_suggestions
                SET status = 'rejected',
                    reviewed_by = %s,
                    reviewed_at = now(),
                    review_feedback = %s
                WHERE id = %s
                RETURNING id
                """,
                (reviewer, reason, suggestion_id)
            )

            result = cursor.fetchone()
            if result:
                self.conn.commit()
                print(f"✓ Rejected suggestion #{suggestion_id}: {reason}")
                return True
            else:
                print(f"❌ Suggestion {suggestion_id} not found")
                return False

        except Exception as e:
            print(f"❌ Failed to reject suggestion {suggestion_id}: {e}")
            self.conn.rollback()
            return False

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about pattern suggestions.

        Returns:
            Dictionary with counts by status
        """
        try:
            cursor = self.conn.execute(
                """
                SELECT status, COUNT(*) as count
                FROM pattern_library.pattern_suggestions
                GROUP BY status
                """
            )

            stats = {'total': 0}
            for row in cursor:
                status, count = row
                stats[status] = count
                stats['total'] += count

            # Add pending if not present
            if 'pending' not in stats:
                stats['pending'] = 0

            return stats

        except Exception as e:
            print(f"❌ Failed to get suggestion stats: {e}")
            return {'total': 0, 'pending': 0}

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()