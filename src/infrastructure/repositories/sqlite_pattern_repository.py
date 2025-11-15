"""SQLite-backed Pattern Repository (Legacy)"""
import sqlite3
import json
from pathlib import Path
from typing import List
from src.domain.repositories.pattern_repository import PatternRepository
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType


class SQLitePatternRepository(PatternRepository):
    """SQLite-backed repository for Pattern aggregate (legacy compatibility)"""

    def __init__(self, db_path: str = "pattern_library.db"):
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        """Create SQLite schema if it doesn't exist"""
        schema_path = Path(__file__).parent.parent.parent / "pattern_library" / "schema.sql"

        # For in-memory databases or when schema file doesn't exist, use minimal schema
        if self.db_path == ":memory:" or not schema_path.exists():
            # Create minimal schema for testing
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS patterns (
                        pattern_name TEXT PRIMARY KEY,
                        pattern_category TEXT NOT NULL,
                        abstract_syntax TEXT,
                        description TEXT,
                        complexity_score INTEGER DEFAULT 1
                    )
                """)
                conn.commit()
            return

        # Use existing schema
        with sqlite3.connect(self.db_path) as conn:
            with open(schema_path) as f:
                conn.executescript(f.read())
            conn.commit()

    def get(self, pattern_name: str) -> Pattern:
        """Get pattern by name from SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT pattern_name, pattern_category, abstract_syntax, description, complexity_score
                FROM patterns WHERE pattern_name = ?
            """, (pattern_name,))

            row = cur.fetchone()
            if not row:
                raise ValueError(f"Pattern {pattern_name} not found")

            return Pattern(
                id=None,  # SQLite doesn't have auto-incrementing IDs in this schema
                name=row['pattern_name'],
                category=PatternCategory(row['pattern_category']),
                description=row['description'] or "",
                parameters=json.loads(row['abstract_syntax'] or '{}'),
                implementation={},  # Not stored in legacy schema
                source_type=SourceType.MANUAL,
                complexity_score=float(row['complexity_score'] or 1)
            )

    def find_by_category(self, category: str) -> List[Pattern]:
        """Find patterns by category"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT pattern_name, pattern_category, abstract_syntax, description, complexity_score
                FROM patterns WHERE pattern_category = ?
                ORDER BY pattern_name
            """, (category,))

            patterns = []
            for row in cur.fetchall():
                patterns.append(Pattern(
                    id=None,
                    name=row['pattern_name'],
                    category=PatternCategory(row['pattern_category']),
                    description=row['description'] or "",
                    parameters=json.loads(row['abstract_syntax'] or '{}'),
                    implementation={},
                    source_type=SourceType.MANUAL,
                    complexity_score=float(row['complexity_score'] or 1)
                ))

            return patterns

    def save(self, pattern: Pattern) -> None:
        """Save pattern to SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            # Convert pattern to legacy schema format
            abstract_syntax = json.dumps(pattern.parameters)

            cur.execute("""
                INSERT OR REPLACE INTO patterns
                (pattern_name, pattern_category, abstract_syntax, description, complexity_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                pattern.name,
                pattern.category.value,
                abstract_syntax,
                pattern.description,
                int(pattern.complexity_score or 1)
            ))

            conn.commit()

    def list_all(self) -> List[Pattern]:
        """List all patterns"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT pattern_name, pattern_category, abstract_syntax, description, complexity_score
                FROM patterns
                ORDER BY pattern_name
            """)

            patterns = []
            for row in cur.fetchall():
                patterns.append(Pattern(
                    id=None,
                    name=row['pattern_name'],
                    category=PatternCategory(row['pattern_category']),
                    description=row['description'] or "",
                    parameters=json.loads(row['abstract_syntax'] or '{}'),
                    implementation={},
                    source_type=SourceType.MANUAL,
                    complexity_score=float(row['complexity_score'] or 1)
                ))

            return patterns