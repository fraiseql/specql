"""
PatternLibrary API for database-driven code generation

Usage:
    library = PatternLibrary(db_path="pattern_library.db")

    # Add pattern
    library.add_pattern(
        name="declare",
        category="primitive",
        abstract_syntax={...}
    )

    # Add implementation
    library.add_implementation(
        pattern_name="declare",
        language_name="postgresql",
        template="..."
    )

    # Compile
    code = library.compile_pattern(
        pattern_name="declare",
        language_name="postgresql",
        context={...}
    )
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from functools import lru_cache
from jinja2 import Template


class PatternLibrary:
    """Database-driven pattern library for multi-language code generation"""

    def __init__(self, db_path: str = "pattern_library.db"):
        """
        Initialize pattern library

        Args:
            db_path: Path to SQLite database (":memory:" for in-memory)
        """
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row  # Return rows as dicts
        self._initialize_schema()

    def _initialize_schema(self):
        """Create database schema if not exists"""
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            # For testing, allow empty initialization
            return

        # Check if tables already exist
        cursor = self.db.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='patterns'
        """)
        if cursor.fetchone():
            # Schema already exists, skip initialization
            return

        with open(schema_path) as f:
            self.db.executescript(f.read())

        self.db.commit()

    # ===== Pattern Management =====

    def add_pattern(
        self,
        name: str,
        category: str,
        abstract_syntax: Dict[str, Any],
        description: str = "",
        complexity_score: int = 1
    ) -> int:
        """Add a pattern to the library"""
        cursor = self.db.execute(
            """
            INSERT INTO patterns (pattern_name, pattern_category, abstract_syntax, description, complexity_score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, category, json.dumps(abstract_syntax), description, complexity_score)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    @lru_cache(maxsize=128)
    def get_pattern(self, name: str) -> Optional[Dict[str, Any]]:
        """Get pattern by name"""
        cursor = self.db.execute(
            "SELECT * FROM patterns WHERE pattern_name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_patterns(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all patterns, optionally filtered by category"""
        if category:
            cursor = self.db.execute(
                "SELECT * FROM patterns WHERE pattern_category = ? ORDER BY pattern_name",
                (category,)
            )
        else:
            cursor = self.db.execute("SELECT * FROM patterns ORDER BY pattern_name")

        return [dict(row) for row in cursor.fetchall()]

    # ===== Language Management =====

    def add_language(
        self,
        name: str,
        ecosystem: str,
        paradigm: str,
        version: str = "",
        supported: bool = True
    ) -> int:
        """Add a target language"""
        cursor = self.db.execute(
            """
            INSERT INTO languages (language_name, ecosystem, paradigm, version, supported)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, ecosystem, paradigm, version, supported)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    @lru_cache(maxsize=32)
    def get_language(self, name: str) -> Optional[Dict[str, Any]]:
        """Get language by name"""
        cursor = self.db.execute(
            "SELECT * FROM languages WHERE language_name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_languages(self, supported_only: bool = True) -> List[Dict[str, Any]]:
        """Get all languages"""
        if supported_only:
            cursor = self.db.execute(
                "SELECT * FROM languages WHERE supported = TRUE ORDER BY language_name"
            )
        else:
            cursor = self.db.execute("SELECT * FROM languages ORDER BY language_name")

        return [dict(row) for row in cursor.fetchall()]

    # ===== Implementation Management =====

    def add_implementation(
        self,
        pattern_name: str,
        language_name: str,
        template: str,
        supported: bool = True,
        version: str = "1.0.0"
    ) -> int:
        """Add pattern implementation for a language"""

        # Get IDs
        pattern = self.get_pattern(pattern_name)
        language = self.get_language(language_name)

        if not pattern:
            raise ValueError(f"Pattern not found: {pattern_name}")
        if not language:
            raise ValueError(f"Language not found: {language_name}")

        cursor = self.db.execute(
            """
            INSERT INTO pattern_implementations
            (pattern_id, language_id, implementation_template, supported, version)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pattern["pattern_id"], language["language_id"], template, supported, version)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    def add_or_update_implementation(
        self,
        pattern_name: str,
        language_name: str,
        template: str,
        supported: bool = True,
        version: str = "1.0.0"
    ) -> int:
        """Add or update pattern implementation for a language"""
        existing = self.get_implementation(pattern_name, language_name)
        if existing:
            # Update existing implementation
            cursor = self.db.execute(
                "UPDATE pattern_implementations SET implementation_template = ?, supported = ?, version = ? WHERE implementation_id = ?",
                (template, supported, version, existing["implementation_id"])
            )
            self.db.commit()
            return existing["implementation_id"]
        else:
            # Add new implementation
            return self.add_implementation(pattern_name, language_name, template, supported, version)

    @lru_cache(maxsize=256)
    def get_implementation(
        self,
        pattern_name: str,
        language_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get implementation for pattern + language"""
        cursor = self.db.execute(
            """
            SELECT pi.*
            FROM pattern_implementations pi
            JOIN patterns p ON pi.pattern_id = p.pattern_id
            JOIN languages l ON pi.language_id = l.language_id
            WHERE p.pattern_name = ? AND l.language_name = ?
            """,
            (pattern_name, language_name)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # ===== Compilation =====

    def compile_pattern(
        self,
        pattern_name: str,
        language_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Compile a pattern to target language code

        Args:
            pattern_name: Name of pattern to compile
            language_name: Target language
            context: Variables to inject into template

        Returns:
            Generated code string

        Raises:
            ValueError: If pattern or implementation not found
        """
        impl = self.get_implementation(pattern_name, language_name)

        if not impl:
            raise ValueError(
                f"No implementation found for pattern '{pattern_name}' in language '{language_name}'"
            )

        template = Template(impl["implementation_template"])
        return template.render(**context)

    # ===== Type Management =====

    def add_universal_type(
        self,
        type_name: str,
        type_category: str,
        description: str = "",
        json_schema: Optional[Dict] = None
    ) -> int:
        """Add universal type to library"""
        cursor = self.db.execute(
            """
            INSERT INTO universal_types (type_name, type_category, description, json_schema)
            VALUES (?, ?, ?, ?)
            """,
            (type_name, type_category, description, json.dumps(json_schema) if json_schema else None)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    def add_type_mapping(
        self,
        universal_type_name: str,
        language_name: str,
        language_type: str,
        import_statement: Optional[str] = None
    ) -> int:
        """Map universal type to language-specific type"""

        # Get IDs
        cursor = self.db.execute(
            "SELECT type_id FROM universal_types WHERE type_name = ?",
            (universal_type_name,)
        )
        type_row = cursor.fetchone()
        if not type_row:
            raise ValueError(f"Universal type not found: {universal_type_name}")

        language = self.get_language(language_name)
        if not language:
            raise ValueError(f"Language not found: {language_name}")

        cursor = self.db.execute(
            """
            INSERT INTO type_mappings (universal_type_id, language_id, language_type, import_statement)
            VALUES (?, ?, ?, ?)
            """,
            (type_row["type_id"], language["language_id"], language_type, import_statement)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    def get_type_mapping(
        self,
        universal_type_name: str,
        language_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get type mapping for universal type in target language"""
        cursor = self.db.execute(
            """
            SELECT tm.*, ut.type_name, l.language_name
            FROM type_mappings tm
            JOIN universal_types ut ON tm.universal_type_id = ut.type_id
            JOIN languages l ON tm.language_id = l.language_id
            WHERE ut.type_name = ? AND l.language_name = ?
            """,
            (universal_type_name, language_name)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # ===== Batch Operations =====

    def batch_add_patterns(self, patterns: List[Dict[str, Any]]) -> List[int]:
        """Batch insert multiple patterns"""
        ids = []
        for pattern in patterns:
            pattern_id = self.add_pattern(
                name=pattern["name"],
                category=pattern["category"],
                abstract_syntax=pattern["abstract_syntax"],
                description=pattern.get("description", ""),
                complexity_score=pattern.get("complexity_score", 1)
            )
            ids.append(pattern_id)
        return ids

    def batch_add_languages(self, languages: List[Dict[str, Any]]) -> List[int]:
        """Batch insert multiple languages"""
        ids = []
        for language in languages:
            lang_id = self.add_language(
                name=language["name"],
                ecosystem=language["ecosystem"],
                paradigm=language["paradigm"],
                version=language.get("version", ""),
                supported=language.get("supported", True)
            )
            ids.append(lang_id)
        return ids

    def batch_add_implementations(self, implementations: List[Dict[str, Any]]) -> List[int]:
        """Batch insert multiple pattern implementations"""
        ids = []
        for impl in implementations:
            impl_id = self.add_implementation(
                pattern_name=impl["pattern_name"],
                language_name=impl["language_name"],
                template=impl["template"],
                supported=impl.get("supported", True),
                version=impl.get("version", "1.0.0")
            )
            ids.append(impl_id)
        return ids

    # ===== Utility Methods =====

    def close(self):
        """Close database connection"""
        self.db.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()