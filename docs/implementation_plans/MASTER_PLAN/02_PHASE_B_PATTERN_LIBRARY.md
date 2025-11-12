# Track B: Pattern Library - Implementation Plan

**Duration**: 8 weeks (reduced from 10, focusing on PostgreSQL + Python only)
**Objective**: Build database-driven multi-language compilation system
**Team**: Team B (Schema Generator) + Team C (Action Compiler)
**Output**: 1 YAML → PostgreSQL + Python (Django/SQLAlchemy)

---

## 🎯 Vision

Transform SpecQL from hard-coded PostgreSQL-only generation to a database-driven pattern library that:
- Stores pattern implementations for multiple target languages
- Enables 1 SpecQL YAML → N language outputs
- Allows community contributions of new language backends
- Provides consistent patterns across different ecosystems

**Focus**: PostgreSQL + Python (Django ORM, SQLAlchemy)
**Future**: TypeScript, Ruby, etc. (community-driven)

---

## 📊 Current State

**Hard-Coded Generation**:
- PostgreSQL PL/pgSQL: ✅ Fully implemented
- Python: ❌ Not implemented
- TypeScript: ❌ Not implemented
- Ruby: ❌ Not implemented

**Limitations**:
- Adding new language = rewrite all compilers
- No standardized pattern definitions
- Can't query available patterns
- No pattern dependency tracking
- No community contribution path

---

## 🚀 Target State

**Database-Driven Architecture**:
- SQLite pattern library with 9 core tables
- Python API for pattern compilation
- PostgreSQL implementations for all 35 primitives
- Python (Django) implementations for all 35 primitives
- Python (SQLAlchemy) implementations for all 35 primitives
- Extensible to new languages via database inserts

**Benefits**:
- Query patterns by capability
- Track pattern dependencies
- Version pattern implementations
- Community contributions via SQL inserts
- Consistent compilation across languages

---

## 📅 8-Week Timeline (PostgreSQL + Python Focus)

### Phase 1: Database Schema & API (Weeks 1-2)
**Goal**: Foundation for pattern storage and retrieval
- Design SQLite schema (9 tables)
- Implement Python API (`PatternLibrary` class)
- Seed with initial 5 pattern definitions
- Test pattern storage/retrieval

### Phase 2: PostgreSQL Patterns (Weeks 3-4)
**Goal**: Migrate existing PostgreSQL generation to pattern library
- Convert 35 primitive actions → pattern templates
- Store in pattern library database
- Test pattern-based PostgreSQL generation
- Validate against existing tests

### Phase 3: Python/Django Patterns (Weeks 5-6)
**Goal**: Add Django ORM as second target language
- Design Django ORM pattern templates
- Implement 35 primitive actions for Django
- Test Django code generation
- E2E test with Django project

### Phase 4: Python/SQLAlchemy Patterns (Week 7)
**Goal**: Add SQLAlchemy as third target
- Design SQLAlchemy pattern templates
- Implement core 15 primitives (focus on most used)
- Test SQLAlchemy generation

### Phase 5: Integration & Testing (Week 8)
**Goal**: Full system integration
- Multi-language test suite
- Documentation
- Migration path from hard-coded
- Performance benchmarks

---

## 🗄️ Database Schema

### Core Tables (9 total)

```sql
-- Table 1: Patterns (Universal primitives)
CREATE TABLE patterns (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name TEXT NOT NULL UNIQUE,
    pattern_category TEXT NOT NULL, -- primitive, control_flow, query, data_transform
    abstract_syntax TEXT NOT NULL, -- JSON schema for pattern structure
    description TEXT,
    complexity_score INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Languages (Target languages)
CREATE TABLE languages (
    language_id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_name TEXT NOT NULL UNIQUE,
    ecosystem TEXT, -- postgresql, python, typescript, ruby
    paradigm TEXT, -- declarative, imperative, functional
    version TEXT, -- e.g., "14+", "3.11+", "5.0+"
    supported BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Table 3: Pattern Implementations (Language-specific code)
CREATE TABLE pattern_implementations (
    implementation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    implementation_template TEXT NOT NULL, -- Jinja2 template
    supported BOOLEAN DEFAULT TRUE,
    performance_notes TEXT,
    version TEXT DEFAULT '1.0.0',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES patterns(pattern_id),
    FOREIGN KEY (language_id) REFERENCES languages(language_id),
    UNIQUE(pattern_id, language_id)
);

-- Table 4: Universal Types (SpecQL type system)
CREATE TABLE universal_types (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    type_category TEXT NOT NULL, -- scalar, composite, collection
    description TEXT,
    json_schema TEXT -- JSON schema definition
);

-- Table 5: Type Mappings (SpecQL types → Language types)
CREATE TABLE type_mappings (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    universal_type_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    language_type TEXT NOT NULL,
    import_statement TEXT, -- e.g., "from decimal import Decimal"
    validation_rules TEXT, -- JSON with validation logic
    FOREIGN KEY (universal_type_id) REFERENCES universal_types(type_id),
    FOREIGN KEY (language_id) REFERENCES languages(language_id),
    UNIQUE(universal_type_id, language_id)
);

-- Table 6: Expression Patterns (Operators, functions)
CREATE TABLE expression_patterns (
    expression_id INTEGER PRIMARY KEY AUTOINCREMENT,
    expression_name TEXT NOT NULL UNIQUE,
    expression_category TEXT NOT NULL, -- operator, function, aggregate
    arity INTEGER, -- number of arguments
    description TEXT
);

-- Table 7: Expression Implementations (Language-specific operators)
CREATE TABLE expression_implementations (
    expr_implementation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    expression_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    implementation_syntax TEXT NOT NULL,
    example TEXT,
    FOREIGN KEY (expression_id) REFERENCES expression_patterns(expression_id),
    FOREIGN KEY (language_id) REFERENCES languages(language_id),
    UNIQUE(expression_id, language_id)
);

-- Table 8: Language Capabilities (Feature support matrix)
CREATE TABLE language_capabilities (
    capability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_id INTEGER NOT NULL,
    capability_name TEXT NOT NULL,
    supported BOOLEAN DEFAULT TRUE,
    workaround_notes TEXT,
    FOREIGN KEY (language_id) REFERENCES languages(language_id),
    UNIQUE(language_id, capability_name)
);

-- Table 9: Pattern Dependencies (Pattern relationships)
CREATE TABLE pattern_dependencies (
    dependency_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    depends_on_pattern_id INTEGER NOT NULL,
    dependency_type TEXT NOT NULL, -- requires, suggests, conflicts_with
    FOREIGN KEY (pattern_id) REFERENCES patterns(pattern_id),
    FOREIGN KEY (depends_on_pattern_id) REFERENCES patterns(pattern_id),
    UNIQUE(pattern_id, depends_on_pattern_id)
);

-- Indexes
CREATE INDEX idx_patterns_category ON patterns(pattern_category);
CREATE INDEX idx_implementations_pattern ON pattern_implementations(pattern_id);
CREATE INDEX idx_implementations_language ON pattern_implementations(language_id);
CREATE INDEX idx_type_mappings_type ON type_mappings(universal_type_id);
CREATE INDEX idx_type_mappings_language ON type_mappings(language_id);
```

---

## 🔄 TDD Methodology

Same RED → GREEN → REFACTOR → QA cycle for each phase.

---

## WEEK 1-2: Database Schema & Python API

### Objective
Create SQLite database and Python API for pattern storage/retrieval.

---

### 🔴 RED Phase (Days 1-2): Write Failing Tests

#### Test 1: Database Schema
**File**: `tests/unit/pattern_library/test_database_schema.py`

```python
import sqlite3
from pathlib import Path

def test_database_schema_creation():
    """Test that schema creates all required tables"""
    db_path = Path("test_pattern_library.db")

    # Create schema
    conn = sqlite3.connect(db_path)
    with open("src/pattern_library/schema.sql") as f:
        conn.executescript(f.read())

    # Verify tables exist
    cursor = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = [
        "patterns",
        "languages",
        "pattern_implementations",
        "universal_types",
        "type_mappings",
        "expression_patterns",
        "expression_implementations",
        "language_capabilities",
        "pattern_dependencies"
    ]

    for table in expected_tables:
        assert table in tables, f"Missing table: {table}"

    conn.close()
    db_path.unlink()

def test_pattern_insert():
    """Test inserting a pattern"""
    db_path = Path("test_pattern_library.db")
    conn = sqlite3.connect(db_path)

    # Should fail - schema not created yet
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("""
            INSERT INTO patterns (pattern_name, pattern_category, abstract_syntax)
            VALUES ('declare', 'primitive', '{}')
        """)

    conn.close()
```

#### Test 2: Python API
**File**: `tests/unit/pattern_library/test_pattern_library_api.py`

```python
from src.pattern_library.api import PatternLibrary

def test_pattern_library_initialization():
    """Test PatternLibrary initialization"""
    library = PatternLibrary(db_path=":memory:")

    # Should initialize schema
    assert library.db is not None
    assert library.get_all_patterns() == []

def test_add_pattern():
    """Test adding a pattern to library"""
    library = PatternLibrary(db_path=":memory:")

    pattern_id = library.add_pattern(
        name="declare",
        category="primitive",
        abstract_syntax={
            "type": "declare",
            "fields": ["variable_name", "variable_type", "default_value"]
        },
        description="Declare a variable"
    )

    assert pattern_id > 0

    # Verify retrieval
    pattern = library.get_pattern("declare")
    assert pattern is not None
    assert pattern["pattern_name"] == "declare"
    assert pattern["pattern_category"] == "primitive"

def test_add_language():
    """Test adding a target language"""
    library = PatternLibrary(db_path=":memory:")

    lang_id = library.add_language(
        name="postgresql",
        ecosystem="postgresql",
        paradigm="declarative",
        version="14+"
    )

    assert lang_id > 0

    languages = library.get_all_languages()
    assert len(languages) == 1
    assert languages[0]["language_name"] == "postgresql"

def test_add_pattern_implementation():
    """Test adding pattern implementation for a language"""
    library = PatternLibrary(db_path=":memory:")

    # Add pattern
    pattern_id = library.add_pattern(
        name="declare",
        category="primitive",
        abstract_syntax={}
    )

    # Add language
    lang_id = library.add_language(
        name="postgresql",
        ecosystem="postgresql",
        paradigm="declarative"
    )

    # Add implementation
    impl_id = library.add_implementation(
        pattern_name="declare",
        language_name="postgresql",
        template="""{{ variable_name }} {{ variable_type }}{% if default_value %} := {{ default_value }}{% endif %};"""
    )

    assert impl_id > 0

    # Retrieve implementation
    impl = library.get_implementation("declare", "postgresql")
    assert impl is not None
    assert "{{ variable_name }}" in impl["implementation_template"]

def test_compile_pattern():
    """Test compiling a pattern to target language"""
    library = PatternLibrary(db_path=":memory:")

    # Setup
    library.add_pattern(name="declare", category="primitive", abstract_syntax={})
    library.add_language(name="postgresql", ecosystem="postgresql", paradigm="declarative")
    library.add_implementation(
        pattern_name="declare",
        language_name="postgresql",
        template="""{{ variable_name }} {{ variable_type }}{% if default_value %} := {{ default_value }}{% endif %};"""
    )

    # Compile
    result = library.compile_pattern(
        pattern_name="declare",
        language_name="postgresql",
        context={
            "variable_name": "total",
            "variable_type": "NUMERIC",
            "default_value": "0"
        }
    )

    assert result == "total NUMERIC := 0;"
```

**Expected Output**: All tests FAIL (not implemented)

```bash
uv run pytest tests/unit/pattern_library/test_database_schema.py -v
# FAILED: schema.sql not found

uv run pytest tests/unit/pattern_library/test_pattern_library_api.py -v
# FAILED: PatternLibrary class not found
```

---

### 🟢 GREEN Phase (Days 3-6): Minimal Implementation

#### Step 1: Create Database Schema
**File**: `src/pattern_library/schema.sql`

```sql
-- [Include full schema from above]
-- 9 tables + indexes
```

#### Step 2: Implement Python API
**File**: `src/pattern_library/api.py`

```python
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
        return cursor.lastrowid

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
        return cursor.lastrowid

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
        return cursor.lastrowid

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
        return cursor.lastrowid

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
        return cursor.lastrowid

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
```

#### Step 3: Seed Initial Data
**File**: `src/pattern_library/seed_data.py`

```python
"""Seed pattern library with initial data"""

from src.pattern_library.api import PatternLibrary


def seed_initial_data(library: PatternLibrary):
    """Seed library with initial patterns and languages"""

    # Add languages
    library.add_language(
        name="postgresql",
        ecosystem="postgresql",
        paradigm="declarative",
        version="14+"
    )

    library.add_language(
        name="python_django",
        ecosystem="python",
        paradigm="imperative",
        version="3.11+"
    )

    library.add_language(
        name="python_sqlalchemy",
        ecosystem="python",
        paradigm="imperative",
        version="3.11+"
    )

    # Add universal types
    types_to_add = [
        ("text", "scalar", "Text string"),
        ("integer", "scalar", "Integer number"),
        ("numeric", "scalar", "Decimal number"),
        ("boolean", "scalar", "Boolean value"),
        ("uuid", "scalar", "UUID identifier"),
        ("timestamp", "scalar", "Timestamp with timezone"),
        ("json", "composite", "JSON object"),
        ("array", "collection", "Array of values"),
    ]

    for type_name, type_category, description in types_to_add:
        library.add_universal_type(type_name, type_category, description)

    # Add type mappings - PostgreSQL
    pg_mappings = [
        ("text", "postgresql", "TEXT"),
        ("integer", "postgresql", "INTEGER"),
        ("numeric", "postgresql", "NUMERIC"),
        ("boolean", "postgresql", "BOOLEAN"),
        ("uuid", "postgresql", "UUID"),
        ("timestamp", "postgresql", "TIMESTAMPTZ"),
        ("json", "postgresql", "JSONB"),
        ("array", "postgresql", "ARRAY"),
    ]

    for universal_type, language, lang_type in pg_mappings:
        library.add_type_mapping(universal_type, language, lang_type)

    # Add type mappings - Python
    python_mappings = [
        ("text", "python_django", "str", None),
        ("integer", "python_django", "int", None),
        ("numeric", "python_django", "Decimal", "from decimal import Decimal"),
        ("boolean", "python_django", "bool", None),
        ("uuid", "python_django", "UUID", "from uuid import UUID"),
        ("timestamp", "python_django", "datetime", "from datetime import datetime"),
        ("json", "python_django", "dict", None),
        ("array", "python_django", "list", None),
    ]

    for universal_type, language, lang_type, import_stmt in python_mappings:
        library.add_type_mapping(universal_type, language, lang_type, import_stmt)

    # Add 5 initial patterns
    library.add_pattern(
        name="declare",
        category="primitive",
        abstract_syntax={
            "type": "declare",
            "fields": ["variable_name", "variable_type", "default_value"]
        },
        description="Declare a variable with optional default value"
    )

    library.add_pattern(
        name="assign",
        category="primitive",
        abstract_syntax={
            "type": "assign",
            "fields": ["variable_name", "expression"]
        },
        description="Assign value to a variable"
    )

    library.add_pattern(
        name="if",
        category="control_flow",
        abstract_syntax={
            "type": "if",
            "fields": ["condition", "then_steps", "else_steps"]
        },
        description="Conditional branching"
    )

    library.add_pattern(
        name="query",
        category="query",
        abstract_syntax={
            "type": "query",
            "fields": ["sql", "into_variable"]
        },
        description="Execute query and store result"
    )

    library.add_pattern(
        name="return",
        category="primitive",
        abstract_syntax={
            "type": "return",
            "fields": ["expression"]
        },
        description="Return value from function"
    )

    print("✅ Seeded initial data")
    print(f"  - Languages: {len(library.get_all_languages())}")
    print(f"  - Patterns: {len(library.get_all_patterns())}")
    print(f"  - Universal types: 8")


if __name__ == "__main__":
    library = PatternLibrary("pattern_library.db")
    seed_initial_data(library)
    library.close()
```

**Run Tests**:
```bash
# First seed the database
python src/pattern_library/seed_data.py

# Then run tests
uv run pytest tests/unit/pattern_library/ -v
# All PASSED
```

---

### 🔧 REFACTOR Phase (Days 7-8): Clean & Optimize

**Refactorings**:
1. Add caching for frequently accessed patterns
2. Optimize query performance with prepared statements
3. Add batch insert methods
4. Create migration utilities

---

### ✅ QA Phase (Days 9-10): Verification

**QA Checklist**:
- [ ] All 8 tests passing
- [ ] Database schema validated
- [ ] Seed data successful
- [ ] API documentation complete
- [ ] Type hints with mypy

---

## WEEK 3-4: PostgreSQL Pattern Implementations

### Objective
Convert existing hard-coded PostgreSQL generation to pattern library templates.

**Work**:
1. Extract 35 pattern templates from existing compilers
2. Store in pattern library
3. Test pattern-based compilation
4. Validate against 120+ existing tests
5. Performance comparison

**Deliverable**: All existing PostgreSQL generation works via pattern library

---

## WEEK 5-6: Python/Django Pattern Implementations

### Objective
Add Django ORM as second target language.

**Example Pattern: `declare` in Django**

PostgreSQL:
```sql
total NUMERIC := 0;
```

Django:
```python
total: Decimal = Decimal('0')
```

**Pattern Template**:
```python
library.add_implementation(
    pattern_name="declare",
    language_name="python_django",
    template="""{{ variable_name }}: {{ variable_type }}{% if default_value %} = {{ default_value }}{% endif %}"""
)
```

**Work**:
1. Design Django ORM patterns for 35 primitives
2. Implement action → Django function conversion
3. Test with Django project
4. E2E integration test

**Deliverable**: Generate Django views/models from SpecQL YAML

---

## WEEK 7: Python/SQLAlchemy Pattern Implementations

### Objective
Add SQLAlchemy as third target.

**Focus**: Core 15 most-used primitives only (not all 35)

**Work**:
1. Design SQLAlchemy patterns
2. Implement core primitives
3. Test with SQLAlchemy project

**Deliverable**: Generate SQLAlchemy models/queries from SpecQL YAML

---

## WEEK 8: Integration & Testing

### Objective
Full system integration and testing.

**Work**:
1. Multi-language test suite
2. Performance benchmarks
3. Documentation
4. Migration guide from hard-coded
5. CLI updates (`specql generate --target=django`)

**Deliverable**: Production-ready pattern library

---

## 📊 Track B Summary (8 Weeks)

### Deliverables

**Database**:
- ✅ SQLite schema (9 tables)
- ✅ Seed data with 35 patterns
- ✅ PostgreSQL implementations (35 patterns)
- ✅ Django implementations (35 patterns)
- ✅ SQLAlchemy implementations (15 patterns)

**Code**:
- ✅ `PatternLibrary` Python API
- ✅ Pattern-based compilers
- ✅ Type mapping system
- ✅ Migration utilities

**Tests**:
- ✅ 30+ unit tests
- ✅ 20+ integration tests
- ✅ E2E tests (PostgreSQL, Django, SQLAlchemy)
- ✅ Performance benchmarks

**Documentation**:
- ✅ Pattern library guide
- ✅ Adding new languages guide
- ✅ Pattern template reference
- ✅ Migration guide

### Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Target Languages** | 1 (PostgreSQL) | 3 (PostgreSQL, Django, SQLAlchemy) | +2 |
| **Pattern Implementations** | 0 (hard-coded) | 85 (35 PG + 35 Django + 15 SA) | +85 |
| **Extensibility** | Hard to add language | SQL INSERT to add language | ∞ |
| **Community Path** | None | Database contributions | ✅ |

### Success Criteria

- [x] Pattern library database functional
- [x] All existing PostgreSQL tests still pass
- [x] Django code generation working
- [x] SQLAlchemy core patterns working
- [x] Performance acceptable (<10% overhead)
- [x] Documentation complete

---

## 🔄 Integration with Track A

**Dependencies**:
- Track B needs Track A Week 1-3 primitives (declare, cte, aggregate, etc.) to store in library
- Track B Week 3-4 must wait for Track A Week 3 completion

**Parallel Work**:
- Track B Week 1-2 (Database) can happen in parallel with Track A Week 1-2
- Track B Week 5-8 (Django, SQLAlchemy) can happen in parallel with Track A Week 4-7

---

## 🚀 Future Extensions (Community-Driven)

After Track B completion, community can add:
- TypeScript/Prisma patterns
- Ruby/Rails patterns
- Go/GORM patterns
- Rust/Diesel patterns

All via SQL inserts - no code changes needed!

---

**Last Updated**: 2025-11-12
**Status**: Ready for Implementation
**Next**: Week 1 - Database Schema & API (RED phase)
**Focus**: PostgreSQL + Python (Django + SQLAlchemy) only
