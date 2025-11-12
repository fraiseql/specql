# X270 + Grok Code Fast 1: POC Implementation Plan

**Project**: SpecQL Pattern Library Enhancement - Proof of Concept
**Hardware**: Lenovo X270 (Intel i5/i7, 8-16GB RAM, no GPU)
**LLM**: OpenCode Grok Code Fast 1 (FREE)
**Version**: 1.0 (POC)
**Date**: 2025-11-12
**Status**: Ready to Execute

---

## Executive Summary

### Vision

Build a **zero-cost proof of concept** for SpecQL's pattern library enhancement using OpenCode's free Grok Code Fast 1 model, running on a standard laptop (X270) with no GPU requirements.

### Why This POC Works

**✅ Perfect Match**:
- **No GPU needed** - Grok runs on OpenCode's infrastructure
- **Zero cost** - Grok Code Fast 1 is free
- **Fast responses** - 1-3 seconds per call (tested!)
- **Good quality** - Produces valid JSON, understands SQL/code
- **X270 handles everything else** - Embeddings, ML models, CLI all CPU-friendly

### POC Scope (8 Weeks)

Focus on **high-value, low-hardware-requirement** components:

✅ **Phase 1**: Pattern Embeddings & Retrieval (Weeks 1-2)
✅ **Phase 2**: Pattern Discovery Pipeline (Weeks 3-4)
✅ **Phase 3**: NL Pattern Generation (Weeks 5-6)
✅ **Phase 4**: Integration & Testing (Weeks 7-8)

❌ **Defer to Production**: ML Triage, Multi-Language Templates, Advanced Analytics

### Architecture (POC Simplified)

```
┌─────────────────────────────────────────────────────────┐
│                    X270 POC Architecture                 │
└─────────────────────────────────────────────────────────┘

┌──────────────────┐
│  User (CLI)      │
│  specql reverse  │
│  specql patterns │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         SpecQL CLI (Python)             │
│  • reverse.py                           │
│  • patterns.py                          │
│  • review.py                            │
└────────┬────────────────────────────────┘
         │
    ┌────┴────┬────────────┬──────────┐
    ▼         ▼            ▼          ▼
┌─────────┐ ┌──────┐ ┌─────────┐ ┌────────┐
│Pattern  │ │ RAG  │ │ Grok    │ │Review  │
│Library  │ │(CPU) │ │(Remote) │ │Service │
│(SQLite) │ └──────┘ └─────────┘ └────────┘
└─────────┘
    │
    ▼
sentence-transformers
(all-MiniLM-L6-v2)
384-dim embeddings
~50ms/pattern (CPU)
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **LLM** | OpenCode Grok Code Fast 1 | ✅ Free, fast, no GPU needed |
| **Hardware** | X270 (CPU-only) | ✅ Sufficient for embeddings + SQLite |
| **Embeddings** | sentence-transformers (CPU) | ✅ Fast on CPU (~50ms/pattern) |
| **Vector DB** | SQLite BLOB storage | ✅ Simple, no extra dependencies |
| **ML Models** | Defer to later | ⏸️ Need training data first |
| **Scope** | Phases 1-3 only | ✅ Core value, feasible in 8 weeks |

### Success Metrics (POC)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Setup Time** | < 2 hours | Time from clone to first run |
| **Pattern Retrieval Accuracy** | > 70% Top-5 relevant | Manual review of 20 queries |
| **Pattern Discovery Rate** | 5-10% of functions | Auto-tracking |
| **NL Pattern Quality** | > 60% valid first try | Validation pass rate |
| **Response Time** | < 5s per function | 95th percentile |
| **Cost** | $0 | No API charges |

---

## Prerequisites & Setup (30 minutes)

### Step 1: Verify OpenCode Grok Access (5 min)

```bash
# Test that Grok is working
echo "What is 2+2?" | opencode run --model opencode/grok-code

# Expected output: 4

# Test JSON output
cat << 'EOF' | opencode run --model opencode/grok-code
Output valid JSON only: {"test": "value"}
EOF

# Expected: {"test": "value"}
```

✅ **Verified**: Grok works, produces JSON, responds in 1-3 seconds

### Step 2: Install Dependencies (15 min)

```bash
cd ~/code/specql

# Add new dependencies for POC
cat >> pyproject.toml << 'EOF'

# POC Dependencies (Grok + Embeddings)
[project.optional-dependencies]
poc = [
    "sentence-transformers>=2.2.0",  # Pattern embeddings (CPU-friendly)
    "rich>=13.0.0",                  # CLI formatting
    "numpy>=1.24.0",                 # Embeddings math
]
EOF

# Install POC dependencies
uv sync --extra poc

# Verify installation
uv run python -c "from sentence_transformers import SentenceTransformer; print('✓ embeddings ready')"
uv run python -c "from rich.console import Console; print('✓ rich ready')"
```

### Step 3: Database Schema Setup (10 min)

```bash
# Create POC pattern library database
mkdir -p ~/.specql
sqlite3 ~/.specql/patterns_poc.db < src/pattern_library/schema.sql

# Add POC-specific tables (simplified schema)
sqlite3 ~/.specql/patterns_poc.db << 'EOF'
-- Pattern embeddings (Phase 1)
CREATE TABLE IF NOT EXISTS pattern_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,
    model_name TEXT NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pattern_id, model_name)
);

-- Pattern suggestions (Phase 2)
CREATE TABLE IF NOT EXISTS pattern_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggested_name TEXT NOT NULL,
    suggested_category TEXT NOT NULL,
    description TEXT NOT NULL,
    implementation JSON,
    source_sql TEXT,
    confidence_score REAL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grok call logging (for metrics)
CREATE TABLE IF NOT EXISTS grok_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    prompt_length INTEGER,
    response_length INTEGER,
    latency_ms INTEGER,
    success BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

echo "✓ Database setup complete"
```

---

## Phase 1: Pattern Embeddings & Retrieval (Weeks 1-2)

### Goals
- Generate embeddings for patterns (CPU-friendly)
- Implement similarity search
- Integrate RAG into reverse engineering

### Architecture

```
SQL Function → Embed (CPU, ~50ms) → Retrieve Top-5 Patterns → Context for Grok
                                              ↓
                                      [pattern_embeddings]
                                         SQLite BLOB
```

### Implementation

#### 1.1 Pattern Embedding Service (NEW)

**File**: `src/pattern_library/embeddings.py`

```python
"""Pattern embedding service using sentence-transformers (CPU-optimized)."""

from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, List
import sqlite3

class PatternEmbeddingService:
    """Generate and manage pattern embeddings for RAG."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", db_path: Path = None):
        """
        Initialize embedding service.

        Args:
            model_name: Sentence transformer model (384-dim, fast on CPU)
            db_path: Path to pattern library database
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.db_path = db_path or Path.home() / ".specql" / "patterns_poc.db"
        self.db = sqlite3.connect(str(self.db_path))

        print(f"✓ Embedding service ready ({model_name}, CPU mode)")

    def embed_pattern(self, pattern: Dict) -> np.ndarray:
        """
        Generate embedding for a domain pattern.

        Combines:
        - Pattern name and description
        - Category
        - Field names
        - Action names

        Returns:
            384-dim numpy array
        """
        text = self._pattern_to_text(pattern)
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.astype(np.float32)

    def embed_function(self, sql: str, description: str = "") -> np.ndarray:
        """Generate embedding for SQL function."""
        text = f"{description}\n{sql}" if description else sql
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.astype(np.float32)

    def store_embedding(self, pattern_id: int, embedding: np.ndarray):
        """Store embedding in database."""
        embedding_blob = pickle.dumps(embedding)

        self.db.execute(
            """
            INSERT OR REPLACE INTO pattern_embeddings
            (pattern_id, embedding, model_name)
            VALUES (?, ?, ?)
            """,
            (pattern_id, embedding_blob, self.model_name)
        )
        self.db.commit()

    def retrieve_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Retrieve top-K similar patterns using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of {pattern_id, similarity, pattern_name, ...}
        """
        cursor = self.db.execute(
            """
            SELECT pe.pattern_id, pe.embedding, dp.name, dp.category, dp.description
            FROM pattern_embeddings pe
            JOIN domain_patterns dp ON pe.pattern_id = dp.id
            WHERE pe.model_name = ?
            """,
            (self.model_name,)
        )

        results = []
        for row in cursor:
            pattern_id, embedding_blob, name, category, description = row
            pattern_embedding = pickle.loads(embedding_blob)

            # Cosine similarity
            similarity = self._cosine_similarity(query_embedding, pattern_embedding)

            if similarity >= threshold:
                results.append({
                    'pattern_id': pattern_id,
                    'name': name,
                    'category': category,
                    'description': description,
                    'similarity': float(similarity)
                })

        # Sort by similarity and return top-K
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

    def _pattern_to_text(self, pattern: Dict) -> str:
        """Convert pattern to searchable text."""
        parts = [
            f"Pattern: {pattern.get('name', '')}",
            f"Category: {pattern.get('category', '')}",
            f"Description: {pattern.get('description', '')}"
        ]

        # Add field names if available
        impl = pattern.get('implementation', {})
        if 'fields' in impl:
            field_names = [f.get('name', '') for f in impl['fields']]
            parts.append(f"Fields: {', '.join(field_names)}")

        # Add action names
        if 'actions' in impl:
            action_names = [a.get('name', '') for a in impl['actions']]
            parts.append(f"Actions: {', '.join(action_names)}")

        return " | ".join(parts)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def generate_all_embeddings(self):
        """Batch generate embeddings for all patterns."""
        cursor = self.db.execute("SELECT id, name, category, description FROM domain_patterns")
        patterns = [
            {'id': row[0], 'name': row[1], 'category': row[2], 'description': row[3]}
            for row in cursor
        ]

        print(f"Generating embeddings for {len(patterns)} patterns...")

        for i, pattern in enumerate(patterns, 1):
            embedding = self.embed_pattern(pattern)
            self.store_embedding(pattern['id'], embedding)

            if i % 10 == 0:
                print(f"  {i}/{len(patterns)} complete")

        print(f"✓ {len(patterns)} embeddings generated")
```

#### 1.2 Grok LLM Provider (NEW)

**File**: `src/reverse_engineering/grok_provider.py`

```python
"""Grok LLM provider using OpenCode CLI."""

import subprocess
import json
import time
from pathlib import Path
from typing import Optional
import tempfile

class GrokProvider:
    """
    Grok Code Fast 1 provider via OpenCode CLI.

    Uses subprocess to call: opencode run --model opencode/grok-code
    """

    def __init__(self, log_calls: bool = True):
        """
        Initialize Grok provider.

        Args:
            log_calls: Whether to log calls to database for metrics
        """
        self.model = "opencode/grok-code"
        self.log_calls = log_calls

        # Verify opencode is available
        try:
            result = subprocess.run(
                ["which", "opencode"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("opencode not found in PATH")
        except Exception as e:
            raise RuntimeError(f"Failed to verify opencode: {e}")

        print(f"✓ Grok provider ready (model: {self.model}, FREE)")

    def call(
        self,
        prompt: str,
        task_type: str = "general",
        timeout: int = 30
    ) -> str:
        """
        Call Grok via OpenCode CLI.

        Args:
            prompt: Prompt to send to Grok
            task_type: Type of task (for logging)
            timeout: Timeout in seconds

        Returns:
            Grok's response as string
        """
        start_time = time.time()

        try:
            # Write prompt to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(prompt)
                prompt_file = f.name

            # Call opencode
            result = subprocess.run(
                ["opencode", "run", "--model", self.model],
                stdin=open(prompt_file),
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Clean up
            Path(prompt_file).unlink()

            if result.returncode != 0:
                raise RuntimeError(f"Grok call failed: {result.stderr}")

            response = result.stdout.strip()
            latency_ms = int((time.time() - start_time) * 1000)

            # Log call
            if self.log_calls:
                self._log_call(
                    task_type=task_type,
                    prompt_length=len(prompt),
                    response_length=len(response),
                    latency_ms=latency_ms,
                    success=True
                )

            return response

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Grok call timed out after {timeout}s")
        except Exception as e:
            # Log failure
            if self.log_calls:
                self._log_call(
                    task_type=task_type,
                    prompt_length=len(prompt),
                    response_length=0,
                    latency_ms=int((time.time() - start_time) * 1000),
                    success=False
                )
            raise RuntimeError(f"Grok call failed: {e}")

    def call_json(
        self,
        prompt: str,
        task_type: str = "general",
        max_retries: int = 2
    ) -> dict:
        """
        Call Grok and parse JSON response.

        Retries if JSON parsing fails.
        """
        for attempt in range(max_retries):
            response = self.call(prompt, task_type)

            try:
                # Try to parse as JSON
                return json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass

                # If last attempt, raise error
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to parse JSON from Grok response: {response[:200]}")

                # Retry with more explicit instructions
                prompt = f"{prompt}\n\nIMPORTANT: Output ONLY valid JSON, no markdown, no explanations."

        raise ValueError("Failed to get valid JSON from Grok")

    def _log_call(
        self,
        task_type: str,
        prompt_length: int,
        response_length: int,
        latency_ms: int,
        success: bool
    ):
        """Log Grok call to database for metrics."""
        try:
            import sqlite3
            db_path = Path.home() / ".specql" / "patterns_poc.db"
            db = sqlite3.connect(str(db_path))

            db.execute(
                """
                INSERT INTO grok_calls
                (task_type, prompt_length, response_length, latency_ms, success)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_type, prompt_length, response_length, latency_ms, success)
            )
            db.commit()
            db.close()
        except Exception:
            # Don't fail on logging errors
            pass
```

#### 1.3 Enhanced AI Enhancer with RAG (EXTEND)

**File**: `src/reverse_engineering/ai_enhancer.py`

Add RAG integration:

```python
# Add to existing AIEnhancer class

from .grok_provider import GrokProvider
from ..pattern_library.embeddings import PatternEmbeddingService

class AIEnhancer:
    def __init__(
        self,
        use_local: bool = False,  # Ignored in POC, always use Grok
        pattern_library_path: Optional[Path] = None
    ):
        """Initialize AI enhancer with Grok + pattern retrieval."""

        # Always use Grok for POC
        self.grok = GrokProvider(log_calls=True)

        # Pattern retrieval (if pattern library available)
        self.embedding_service = None
        if pattern_library_path:
            self.embedding_service = PatternEmbeddingService(
                db_path=pattern_library_path
            )

        print("✓ AI Enhancer ready (Grok + RAG)")

    def enhance_with_patterns(
        self,
        sql_function: str,
        specql_ast: Dict
    ) -> Dict:
        """
        Enhanced version with pattern retrieval.

        Flow:
        1. Generate embedding for SQL function
        2. Retrieve top-5 similar patterns
        3. Call Grok with pattern context
        4. Return enhanced result
        """
        # Step 1: Retrieve relevant patterns
        retrieved_patterns = []
        if self.embedding_service:
            query_embedding = self.embedding_service.embed_function(sql_function)
            retrieved_patterns = self.embedding_service.retrieve_similar(
                query_embedding,
                top_k=5,
                threshold=0.5
            )

        # Step 2: Build prompt with patterns
        prompt = self._build_prompt_with_patterns(
            sql_function,
            specql_ast,
            retrieved_patterns
        )

        # Step 3: Call Grok
        response = self.grok.call_json(prompt, task_type="enhance_with_patterns")

        # Step 4: Return result
        return {
            'enhanced_specql': response.get('enhanced_specql', specql_ast),
            'detected_patterns': response.get('detected_patterns', []),
            'confidence': response.get('confidence', 0.8),
            'retrieved_patterns': [p['name'] for p in retrieved_patterns]
        }

    def _build_prompt_with_patterns(
        self,
        sql: str,
        specql_ast: Dict,
        patterns: List[Dict]
    ) -> str:
        """Build prompt with retrieved patterns as context."""

        prompt_parts = [
            "You are a SpecQL code analyst. Analyze this SQL function using relevant patterns.",
            "",
            "## Retrieved Patterns (Most Similar)"
        ]

        for i, pattern in enumerate(patterns, 1):
            prompt_parts.append(
                f"{i}. **{pattern['name']}** ({pattern['category']}) - "
                f"Similarity: {pattern['similarity']:.2f}\n"
                f"   {pattern['description']}"
            )

        prompt_parts.extend([
            "",
            "## SQL Function",
            "```sql",
            sql,
            "```",
            "",
            "## Current SpecQL AST",
            "```json",
            json.dumps(specql_ast, indent=2),
            "```",
            "",
            "## Your Task",
            "1. Determine which patterns apply (can be multiple)",
            "2. Enhance variable names based on pattern conventions",
            "3. Identify missing logic (validations, audit fields, etc.)",
            "",
            "## Output Format (JSON only)",
            "```json",
            "{",
            '  "detected_patterns": [{"name": "...", "confidence": 0.95, "evidence": "..."}],',
            '  "enhanced_specql": {...},',
            '  "confidence": 0.92',
            "}",
            "```"
        ])

        return "\n".join(prompt_parts)
```

#### 1.4 CLI Integration

**File**: `src/cli/reverse.py` (EXTEND)

Add `--with-patterns` flag:

```python
@click.command()
@click.argument('sql_file', type=click.Path(exists=True))
@click.option('--with-patterns', is_flag=True, help='Use pattern retrieval for enhancement')
@click.option('--pattern-db', type=click.Path(), help='Pattern library database path')
def reverse(sql_file: str, with_patterns: bool, pattern_db: Optional[str]):
    """Reverse engineer SQL to SpecQL."""

    from rich.console import Console
    console = Console()

    # Read SQL
    sql = Path(sql_file).read_text()

    # Initialize enhancer
    pattern_lib_path = Path(pattern_db) if pattern_db else None
    enhancer = AIEnhancer(pattern_library_path=pattern_lib_path)

    # Parse SQL (existing logic)
    specql_ast = parse_sql_to_specql(sql)

    # Enhance with patterns
    if with_patterns:
        console.print("[cyan]Retrieving similar patterns...[/cyan]")
        result = enhancer.enhance_with_patterns(sql, specql_ast)

        console.print(f"[green]✓[/green] Patterns detected: {', '.join([p['name'] for p in result['detected_patterns']])}")
        console.print(f"[green]✓[/green] Confidence: {result['confidence']:.2%}")
    else:
        result = enhancer.enhance_basic(specql_ast)

    # Output SpecQL
    console.print("\n[bold]Generated SpecQL:[/bold]")
    console.print(json.dumps(result['enhanced_specql'], indent=2))
```

#### 1.5 Testing

**File**: `tests/integration/test_phase1_rag.py`

```python
"""Integration tests for Phase 1: Pattern Retrieval."""

import pytest
from pathlib import Path
from src.pattern_library.embeddings import PatternEmbeddingService
from src.reverse_engineering.grok_provider import GrokProvider

def test_embedding_generation():
    """Test that embeddings are generated correctly."""
    service = PatternEmbeddingService()

    pattern = {
        'name': 'audit_trail',
        'category': 'audit',
        'description': 'Track created_at, updated_at, deleted_at'
    }

    embedding = service.embed_pattern(pattern)

    assert embedding.shape == (384,)
    assert embedding.dtype == 'float32'


def test_grok_basic_call():
    """Test that Grok responds correctly."""
    grok = GrokProvider(log_calls=False)

    response = grok.call("What is 2+2? Reply with just the number.")

    assert "4" in response


def test_grok_json_output():
    """Test that Grok can produce structured JSON."""
    grok = GrokProvider(log_calls=False)

    prompt = """
    Output valid JSON only:
    {
        "test": "value",
        "number": 42
    }
    """

    result = grok.call_json(prompt)

    assert result['test'] == 'value'
    assert result['number'] == 42


def test_pattern_retrieval():
    """Test end-to-end pattern retrieval."""
    service = PatternEmbeddingService()

    # Generate embeddings for a few test patterns
    patterns = [
        {'id': 1, 'name': 'audit_trail', 'category': 'audit', 'description': 'Track changes'},
        {'id': 2, 'name': 'soft_delete', 'category': 'audit', 'description': 'Soft delete support'},
        {'id': 3, 'name': 'state_machine', 'category': 'workflow', 'description': 'State transitions'}
    ]

    for pattern in patterns:
        embedding = service.embed_pattern(pattern)
        service.store_embedding(pattern['id'], embedding)

    # Query for audit-related patterns
    query = "Track when records are created and deleted"
    query_embedding = service.embed_function(query)

    results = service.retrieve_similar(query_embedding, top_k=2)

    assert len(results) == 2
    assert results[0]['category'] == 'audit'
    assert results[0]['similarity'] > 0.6
```

### Week 1 Deliverables

- [ ] `src/pattern_library/embeddings.py` - Pattern embedding service
- [ ] `src/reverse_engineering/grok_provider.py` - Grok LLM provider
- [ ] Tests for embedding generation
- [ ] Tests for Grok calls
- [ ] Batch script to generate embeddings for existing patterns

### Week 2 Deliverables

- [ ] Enhanced `ai_enhancer.py` with RAG integration
- [ ] CLI flag `--with-patterns` in `specql reverse`
- [ ] Integration tests for end-to-end retrieval
- [ ] Documentation for Phase 1 usage
- [ ] Benchmark: Measure retrieval accuracy on 20 sample functions

---

## Phase 2: Pattern Discovery Pipeline (Weeks 3-4)

### Goals
- Automatically suggest new patterns from legacy SQL
- Human-in-the-loop review workflow
- Track suggestions for pattern library growth

### Architecture

```
SQL Function → Low Pattern Match? → Grok Analysis → Pattern Suggestion
                    ↓                      ↓                ↓
              (complexity >0.7)    (prompt: discover)  [pattern_suggestions]
                                                            ↓
                                                    Human Review (CLI)
                                                            ↓
                                                    Approve → [domain_patterns]
```

### Implementation

#### 2.1 Pattern Discovery Logic (EXTEND)

**File**: `src/reverse_engineering/ai_enhancer.py`

Add pattern discovery:

```python
def discover_pattern(
    self,
    sql_function: str,
    specql_ast: Dict,
    existing_patterns: List[Dict],
    complexity_score: float
) -> Optional[Dict]:
    """
    Determine if SQL function warrants a new pattern.

    Trigger criteria:
    - Low pattern match (<0.7 similarity)
    - High complexity (>0.7)
    - Business keywords present

    Returns:
        Pattern suggestion dict or None
    """
    # Check trigger criteria
    if not self._should_suggest_pattern(existing_patterns, complexity_score):
        return None

    # Build discovery prompt
    prompt = self._build_discovery_prompt(sql_function, specql_ast, existing_patterns)

    # Call Grok
    response = self.grok.call_json(prompt, task_type="pattern_discovery")

    if not response.get('is_new_pattern', False):
        return None

    # Return suggestion
    return {
        'suggested_name': response['suggested_pattern']['name'],
        'suggested_category': response['suggested_pattern']['category'],
        'description': response['suggested_pattern']['description'],
        'implementation': response['suggested_pattern']['implementation'],
        'confidence_score': response['confidence'],
        'source_sql': sql_function
    }

def _should_suggest_pattern(
    self,
    existing_patterns: List[Dict],
    complexity_score: float
) -> bool:
    """Check if pattern discovery should be triggered."""

    # Criterion 1: Low pattern match
    if existing_patterns:
        best_match = max(p['similarity'] for p in existing_patterns)
        if best_match < 0.7:
            return True

    # Criterion 2: High complexity
    if complexity_score > 0.7:
        return True

    return False

def _build_discovery_prompt(
    self,
    sql: str,
    specql: Dict,
    existing_patterns: List[Dict]
) -> str:
    """Build pattern discovery prompt."""

    prompt = f"""
You are a SpecQL pattern architect. Analyze this SQL function to determine if it represents a novel, reusable pattern.

## Existing Patterns (for reference)
{chr(10).join([f"- {p['name']} ({p['category']}): {p['description']}" for p in existing_patterns[:10]])}

## SQL Function
```sql
{sql}
```

## Parsed SpecQL
```json
{json.dumps(specql, indent=2)}
```

## Criteria for New Pattern
1. Novel: Doesn't match existing patterns well (<70% similarity)
2. Reusable: Can apply to multiple entities/domains
3. Non-trivial: Complex enough to warrant abstraction
4. Generalizable: Can be parameterized

## Output Format (JSON only)
{{
    "is_new_pattern": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Why this is/isn't a new pattern",
    "suggested_pattern": {{
        "name": "snake_case_name",
        "category": "workflow|validation|audit|...",
        "description": "Clear description",
        "implementation": {{
            "fields": [...],
            "actions": [...]
        }}
    }}
}}
"""
    return prompt
```

#### 2.2 Pattern Suggestion Service (NEW)

**File**: `src/pattern_library/suggestion_service.py`

```python
"""Pattern suggestion management."""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional

class PatternSuggestionService:
    """Manage pattern suggestions awaiting review."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path.home() / ".specql" / "patterns_poc.db"
        self.db = sqlite3.connect(str(self.db_path))

    def create_suggestion(self, suggestion: Dict) -> int:
        """Create new pattern suggestion."""
        cursor = self.db.execute(
            """
            INSERT INTO pattern_suggestions
            (suggested_name, suggested_category, description,
             implementation, source_sql, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                suggestion['suggested_name'],
                suggestion['suggested_category'],
                suggestion['description'],
                json.dumps(suggestion.get('implementation', {})),
                suggestion.get('source_sql', ''),
                suggestion.get('confidence_score', 0.8)
            )
        )
        self.db.commit()
        return cursor.lastrowid

    def list_pending(self) -> List[Dict]:
        """List all pending suggestions."""
        cursor = self.db.execute(
            """
            SELECT id, suggested_name, suggested_category,
                   description, confidence_score, created_at
            FROM pattern_suggestions
            WHERE status = 'pending'
            ORDER BY confidence_score DESC, created_at DESC
            """
        )

        return [
            {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'description': row[3],
                'confidence': row[4],
                'created_at': row[5]
            }
            for row in cursor
        ]

    def get_suggestion(self, suggestion_id: int) -> Dict:
        """Get full suggestion details."""
        cursor = self.db.execute(
            """
            SELECT suggested_name, suggested_category, description,
                   implementation, source_sql, confidence_score, status
            FROM pattern_suggestions
            WHERE id = ?
            """,
            (suggestion_id,)
        )

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Suggestion {suggestion_id} not found")

        return {
            'id': suggestion_id,
            'name': row[0],
            'category': row[1],
            'description': row[2],
            'implementation': json.loads(row[3]),
            'source_sql': row[4],
            'confidence': row[5],
            'status': row[6]
        }

    def approve_suggestion(self, suggestion_id: int) -> int:
        """Approve suggestion and add to pattern library."""
        suggestion = self.get_suggestion(suggestion_id)

        # Add to domain_patterns table
        cursor = self.db.execute(
            """
            INSERT INTO domain_patterns
            (name, category, description, implementation)
            VALUES (?, ?, ?, ?)
            """,
            (
                suggestion['name'],
                suggestion['category'],
                suggestion['description'],
                json.dumps(suggestion['implementation'])
            )
        )
        pattern_id = cursor.lastrowid

        # Mark suggestion as approved
        self.db.execute(
            "UPDATE pattern_suggestions SET status = 'approved' WHERE id = ?",
            (suggestion_id,)
        )
        self.db.commit()

        return pattern_id

    def reject_suggestion(self, suggestion_id: int, reason: str):
        """Reject suggestion."""
        self.db.execute(
            "UPDATE pattern_suggestions SET status = 'rejected' WHERE id = ?",
            (suggestion_id,)
        )
        self.db.commit()
```

#### 2.3 CLI Commands (NEW)

**File**: `src/cli/patterns.py`

```python
"""Pattern library CLI commands."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import json
from pathlib import Path

console = Console()

@click.group(name="patterns")
def patterns_cli():
    """Pattern library management."""
    pass

@patterns_cli.command(name="review-suggestions")
def review_suggestions():
    """List pending pattern suggestions."""
    from src.pattern_library.suggestion_service import PatternSuggestionService

    service = PatternSuggestionService()
    suggestions = service.list_pending()

    if not suggestions:
        console.print("[yellow]No pending suggestions.[/yellow]")
        return

    table = Table(title="Pending Pattern Suggestions")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Category", style="magenta")
    table.add_column("Confidence", style="yellow")

    for s in suggestions:
        table.add_row(
            str(s['id']),
            s['name'],
            s['category'],
            f"{s['confidence']:.2f}"
        )

    console.print(table)
    console.print(f"\n[cyan]Review: specql patterns show {suggestions[0]['id']}[/cyan]")

@patterns_cli.command(name="show")
@click.argument("suggestion_id", type=int)
def show_suggestion(suggestion_id: int):
    """Show detailed suggestion."""
    from src.pattern_library.suggestion_service import PatternSuggestionService

    service = PatternSuggestionService()
    suggestion = service.get_suggestion(suggestion_id)

    # Header
    console.print(Panel(
        f"[bold]{suggestion['name']}[/bold] ({suggestion['category']})\n"
        f"{suggestion['description']}\n\n"
        f"Confidence: {suggestion['confidence']:.2f}",
        title="Pattern Suggestion"
    ))

    # Source SQL
    if suggestion['source_sql']:
        console.print("\n[bold]Source SQL:[/bold]")
        syntax = Syntax(suggestion['source_sql'], "sql", theme="monokai")
        console.print(syntax)

    # Implementation
    console.print("\n[bold]Implementation:[/bold]")
    console.print(json.dumps(suggestion['implementation'], indent=2))

    # Actions
    console.print("\n[bold]Actions:[/bold]")
    console.print(f"[green]specql patterns approve {suggestion_id}[/green]")
    console.print(f"[red]specql patterns reject {suggestion_id} --reason \"...\"[/red]")

@patterns_cli.command(name="approve")
@click.argument("suggestion_id", type=int)
def approve_suggestion(suggestion_id: int):
    """Approve and add pattern to library."""
    from src.pattern_library.suggestion_service import PatternSuggestionService
    from src.pattern_library.embeddings import PatternEmbeddingService

    suggestion_service = PatternSuggestionService()
    pattern_id = suggestion_service.approve_suggestion(suggestion_id)

    # Generate embedding for new pattern
    embedding_service = PatternEmbeddingService()
    suggestion = suggestion_service.get_suggestion(suggestion_id)
    embedding = embedding_service.embed_pattern(suggestion)
    embedding_service.store_embedding(pattern_id, embedding)

    console.print(f"[green]✓[/green] Approved and added as pattern ID {pattern_id}")

@patterns_cli.command(name="reject")
@click.argument("suggestion_id", type=int)
@click.option("--reason", required=True)
def reject_suggestion(suggestion_id: int, reason: str):
    """Reject suggestion."""
    from src.pattern_library.suggestion_service import PatternSuggestionService

    service = PatternSuggestionService()
    service.reject_suggestion(suggestion_id, reason)

    console.print(f"[red]✗[/red] Rejected: {reason}")
```

#### 2.4 Integration with Reverse Engineering

**File**: `src/cli/reverse.py` (EXTEND)

Add `--discover-patterns` flag:

```python
@click.option('--discover-patterns', is_flag=True, help='Enable pattern discovery')
def reverse(sql_file: str, with_patterns: bool, discover_patterns: bool, pattern_db: Optional[str]):
    """Reverse engineer SQL to SpecQL."""

    # ... existing code ...

    # Pattern discovery
    if discover_patterns and with_patterns:
        console.print("[cyan]Checking for novel patterns...[/cyan]")

        complexity = calculate_complexity(sql)
        suggestion = enhancer.discover_pattern(
            sql, result['enhanced_specql'],
            result.get('retrieved_patterns', []),
            complexity
        )

        if suggestion:
            from src.pattern_library.suggestion_service import PatternSuggestionService
            service = PatternSuggestionService()
            suggestion_id = service.create_suggestion(suggestion)

            console.print(f"[yellow]💡 New pattern suggested: {suggestion['suggested_name']}[/yellow]")
            console.print(f"[yellow]   Review: specql patterns show {suggestion_id}[/yellow]")
```

### Week 3 Deliverables

- [ ] Pattern discovery logic in `ai_enhancer.py`
- [ ] Pattern suggestion service
- [ ] Grok prompt for pattern discovery
- [ ] Tests for discovery triggers

### Week 4 Deliverables

- [ ] CLI commands (`patterns review-suggestions`, `show`, `approve`, `reject`)
- [ ] Integration with `specql reverse --discover-patterns`
- [ ] End-to-end test: SQL → suggestion → approval → library
- [ ] Documentation for pattern discovery workflow

---

## Phase 3: Natural Language Pattern Generation (Weeks 5-6)

### Goals
- Users create patterns from text descriptions
- Grok generates structured pattern definitions
- Validation ensures quality

### Architecture

```
User Description → Grok (NL → Pattern) → Validation → [pattern_suggestions]
                         ↓                    ↓              ↓
                  (structured prompt)  (JSON schema,   Human Review
                                        SpecQL syntax)
```

### Implementation

#### 3.1 NL Pattern Generator (NEW)

**File**: `src/pattern_library/nl_generator.py`

```python
"""Natural language to pattern generator."""

import json
from typing import Dict
from src.reverse_engineering.grok_provider import GrokProvider

class NLPatternGenerator:
    """Generate patterns from natural language descriptions."""

    def __init__(self):
        self.grok = GrokProvider(log_calls=True)

    def generate(
        self,
        description: str,
        category: str,
        namespace: str = None
    ) -> Dict:
        """
        Generate pattern from description.

        Args:
            description: User's natural language description
            category: Pattern category (workflow, validation, etc.)
            namespace: Optional namespace (crm, ecommerce, etc.)

        Returns:
            {
                'pattern': {...},      # Generated pattern
                'validation': {...},   # Validation results
                'confidence': 0.8
            }
        """
        # Build prompt
        prompt = self._build_generation_prompt(description, category, namespace)

        # Call Grok
        response = self.grok.call_json(prompt, task_type="nl_pattern_generation")

        # Validate
        validation = self._validate_pattern(response)

        # Score confidence
        confidence = self._score_confidence(response, validation)

        return {
            'pattern': response,
            'validation': validation,
            'confidence': confidence
        }

    def _build_generation_prompt(
        self,
        description: str,
        category: str,
        namespace: str = None
    ) -> str:
        """Build NL generation prompt."""

        prompt = f"""
You are a SpecQL pattern architect. Generate a reusable domain pattern from this description.

## User Description
{description}

## Target Category
{category}

{f"## Namespace\n{namespace}" if namespace else ""}

## SpecQL Conventions (MANDATORY)
1. **Trinity Pattern**: All entities have pk_*, id (UUID), identifier (TEXT)
2. **Audit Fields**: created_at, updated_at, deleted_at
3. **Naming**: Snake_case for everything
4. **Multi-Tenant**: Add tenant_id if applicable

## Output Format (JSON only)
{{
    "pattern_name": "snake_case_name",
    "category": "{category}",
    "description": "Clear, reusable description",
    "parameters": {{
        "entity": {{"type": "string", "required": true, "description": "Target entity"}},
        "stages": {{"type": "array", "default": ["pending", "approved"], "description": "Workflow stages"}}
    }},
    "implementation": {{
        "fields": [
            {{"name": "status", "type": "enum({{{{stages}}}})", "description": "Current status"}},
            {{"name": "approved_at", "type": "timestamp", "description": "Approval time"}}
        ],
        "actions": [
            {{
                "name": "approve",
                "description": "Approve entity",
                "steps": [
                    {{"validate": "status = 'pending'"}},
                    {{"update": "{{{{entity}}}} SET status = 'approved', approved_at = now()"}}
                ]
            }}
        ]
    }},
    "multi_tenant": true/false,
    "examples": [
        {{
            "entity": "Invoice",
            "description": "How this applies to invoices"
        }}
    ]
}}

IMPORTANT: Output ONLY valid JSON, follow SpecQL conventions exactly.
"""
        return prompt

    def _validate_pattern(self, pattern: Dict) -> Dict:
        """Validate generated pattern."""
        errors = []
        warnings = []

        # Check required fields
        required = ['pattern_name', 'category', 'description', 'parameters', 'implementation']
        for field in required:
            if field not in pattern:
                errors.append(f"Missing required field: {field}")

        # Check naming convention
        if 'pattern_name' in pattern:
            name = pattern['pattern_name']
            if not name.islower() or not name.replace('_', '').isalnum():
                errors.append("Pattern name must be snake_case")

        # Check implementation
        if 'implementation' in pattern:
            impl = pattern['implementation']

            if 'fields' not in impl:
                warnings.append("No fields defined")

            if 'actions' not in impl:
                warnings.append("No actions defined")

            # Check for audit fields
            field_names = [f.get('name') for f in impl.get('fields', [])]
            if 'created_at' not in field_names:
                warnings.append("Missing created_at audit field")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _score_confidence(self, pattern: Dict, validation: Dict) -> float:
        """Score confidence in generated pattern."""
        score = 1.0

        # Penalize errors/warnings
        score -= len(validation['errors']) * 0.2
        score -= len(validation['warnings']) * 0.05

        # Bonus for completeness
        if 'examples' in pattern:
            score += 0.1

        if 'parameters' in pattern and len(pattern['parameters']) > 1:
            score += 0.05

        return max(0.0, min(1.0, score))
```

#### 3.2 CLI Command (NEW)

**File**: `src/cli/patterns.py` (EXTEND)

```python
@patterns_cli.command(name="create-from-description")
@click.option("--description", required=True, help="Natural language description")
@click.option("--category", required=True, help="Pattern category")
@click.option("--namespace", help="Namespace (crm, ecommerce, etc.)")
@click.option("--review", is_flag=True, default=True, help="Review before adding")
def create_from_description(
    description: str,
    category: str,
    namespace: str,
    review: bool
):
    """Generate pattern from description."""
    console.print("[cyan]Generating pattern from description...[/cyan]")

    from src.pattern_library.nl_generator import NLPatternGenerator
    from src.pattern_library.suggestion_service import PatternSuggestionService

    generator = NLPatternGenerator()
    result = generator.generate(description, category, namespace)

    # Show result
    console.print("\n[bold]Generated Pattern:[/bold]")
    console.print(json.dumps(result['pattern'], indent=2))

    console.print(f"\n[bold]Validation:[/bold]")
    console.print(f"  Valid: {result['validation']['valid']}")
    console.print(f"  Errors: {len(result['validation']['errors'])}")
    console.print(f"  Warnings: {len(result['validation']['warnings'])}")
    console.print(f"  Confidence: {result['confidence']:.2%}")

    if result['validation']['errors']:
        console.print("\n[red]Errors:[/red]")
        for error in result['validation']['errors']:
            console.print(f"  • {error}")

    if result['validation']['warnings']:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result['validation']['warnings']:
            console.print(f"  • {warning}")

    # Create suggestion if valid
    if result['validation']['valid']:
        if review:
            service = PatternSuggestionService()
            suggestion_id = service.create_suggestion({
                'suggested_name': result['pattern']['pattern_name'],
                'suggested_category': result['pattern']['category'],
                'description': result['pattern']['description'],
                'implementation': result['pattern']['implementation'],
                'confidence_score': result['confidence']
            })

            console.print(f"\n[yellow]Created suggestion ID {suggestion_id} for review[/yellow]")
            console.print(f"[cyan]Review: specql patterns show {suggestion_id}[/cyan]")
        else:
            # Add directly (not recommended for POC)
            console.print("\n[yellow]Direct add not recommended in POC. Use --review.[/yellow]")
    else:
        console.print("\n[red]Pattern has errors. Cannot create suggestion.[/red]")
```

### Week 5 Deliverables

- [ ] NL pattern generator
- [ ] Pattern validation logic
- [ ] Grok prompt for NL generation
- [ ] Tests for validation

### Week 6 Deliverables

- [ ] CLI command `patterns create-from-description`
- [ ] Integration tests: Description → Pattern → Validation
- [ ] Manual validation: Generate 10 real patterns, measure quality
- [ ] Documentation for NL pattern creation

---

## Phase 4: Integration & Testing (Weeks 7-8)

### Goals
- End-to-end testing of all components
- Performance benchmarking
- Documentation
- POC demo preparation

### Week 7: Testing & Benchmarking

#### 4.1 End-to-End Tests

```python
# tests/integration/test_e2e_poc.py

def test_full_workflow():
    """
    Test complete workflow:
    1. Reverse engineer SQL
    2. Pattern discovery triggers
    3. Human approves suggestion
    4. Pattern used in next conversion
    """
    # ... implementation ...

def test_nl_to_pattern_to_usage():
    """
    Test NL pattern creation workflow:
    1. User describes pattern
    2. Grok generates definition
    3. Validation passes
    4. Pattern added to library
    5. Pattern used in reverse engineering
    """
    # ... implementation ...
```

#### 4.2 Performance Benchmarks

```python
# tests/performance/test_poc_performance.py

def test_embedding_performance():
    """Measure embedding generation speed on X270."""
    # Target: <100ms per pattern on CPU
    pass

def test_grok_latency():
    """Measure Grok response times."""
    # Target: <5s per call (95th percentile)
    pass

def test_retrieval_performance():
    """Measure pattern retrieval speed."""
    # Target: <200ms for top-5 from 100 patterns
    pass
```

#### 4.3 Quality Metrics

```bash
# Generate quality report
specql poc-report

# Output:
# ========================================
# SpecQL POC Quality Report
# ========================================
# Pattern Library Size: 45 patterns
# Pattern Retrieval Accuracy: 73% (Top-5 relevant)
# Pattern Discovery Rate: 7.2% (12/167 functions)
# NL Pattern Quality: 65% (13/20 valid first try)
# Average Grok Latency: 2.3s (95th: 4.1s)
# Total Cost: $0.00
# ========================================
```

### Week 8: Documentation & Demo

#### 4.4 User Documentation

Create `docs/POC_USER_GUIDE.md`:

```markdown
# SpecQL Pattern Library POC: User Guide

## Setup (2 hours)

1. Clone repository
2. Install dependencies: `uv sync --extra poc`
3. Setup database: [instructions]
4. Verify Grok: `echo "test" | opencode run --model opencode/grok-code`

## Usage

### Reverse Engineering with Patterns

```bash
# Basic
specql reverse legacy_function.sql

# With pattern retrieval
specql reverse legacy_function.sql --with-patterns

# With pattern discovery
specql reverse legacy_function.sql --with-patterns --discover-patterns
```

### Managing Pattern Suggestions

```bash
# List pending
specql patterns review-suggestions

# Show details
specql patterns show 1

# Approve
specql patterns approve 1

# Reject
specql patterns reject 1 --reason "Too specific"
```

### Creating Patterns from Descriptions

```bash
specql patterns create-from-description \
  --description "Three-stage approval: pending → reviewed → approved" \
  --category workflow \
  --review
```

## Troubleshooting

[Common issues and solutions]
```

#### 4.5 Demo Preparation

Create demo script:

```bash
# demo/poc_demo.sh

#!/bin/bash
set -e

echo "========================================="
echo "SpecQL Pattern Library POC Demo"
echo "========================================="
echo ""

# Demo 1: Pattern Retrieval
echo "Demo 1: Pattern Retrieval"
echo "SQL function with audit trail..."
specql reverse demo/sql/audit_trail_example.sql --with-patterns

# Demo 2: Pattern Discovery
echo ""
echo "Demo 2: Pattern Discovery"
echo "Complex approval workflow..."
specql reverse demo/sql/approval_workflow.sql --with-patterns --discover-patterns

# Demo 3: Review Suggestion
echo ""
echo "Demo 3: Review Suggestion"
specql patterns review-suggestions
specql patterns show 1

# Demo 4: NL Pattern Creation
echo ""
echo "Demo 4: Create Pattern from Description"
specql patterns create-from-description \
  --description "Two-stage approval with email notifications" \
  --category workflow

echo ""
echo "========================================="
echo "Demo Complete!"
echo "========================================="
```

---

## Cost & Performance Targets

### Cost (POC - 8 Weeks)

| Item | Cost |
|------|------|
| OpenCode Grok | **$0** (free) |
| Hardware | $0 (existing X270) |
| Dependencies | $0 (open source) |
| **Total** | **$0** ✅ |

### Performance Targets (X270)

| Operation | Target | Typical |
|-----------|--------|---------|
| Embedding generation | <100ms | 50-80ms |
| Pattern retrieval (Top-5) | <200ms | 100-150ms |
| Grok call (simple) | <5s | 2-3s |
| Grok call (complex) | <10s | 5-8s |
| End-to-end reverse engineering | <15s | 8-12s |

---

## Success Criteria (POC)

### Technical Success

- [ ] All Phase 1-3 features implemented
- [ ] Tests passing (unit + integration)
- [ ] Performance targets met
- [ ] Zero cost ($0 spent)

### Quality Success

- [ ] Pattern retrieval accuracy >70% (manual validation)
- [ ] Pattern discovery rate 5-10%
- [ ] NL pattern quality >60% valid first try
- [ ] No critical bugs

### Usability Success

- [ ] Setup time <2 hours
- [ ] Documentation complete
- [ ] Demo runs successfully
- [ ] 2+ external users can replicate POC

---

## Risk Mitigation (POC-Specific)

### Risk 1: Grok Quality Insufficient

**Mitigation**:
- Week 1: Validate Grok quality on 10 sample functions
- If <50% accuracy → Add fallback to Claude API (limited budget)
- If 50-70% → Improve prompts, continue POC
- If >70% → Proceed as planned

### Risk 2: X270 Performance Bottleneck

**Mitigation**:
- Batch embedding generation (do once, not per query)
- Cache Grok responses for identical queries
- Use SQLite indexes aggressively
- If still slow → Profile and optimize hot paths

### Risk 3: Insufficient Training Data for Future ML

**Mitigation**:
- Log ALL reverse engineering results
- Track ALL human reviews
- By end of POC: Aim for 50+ labeled examples
- Defer ML models to production phase (not POC scope)

---

## Next Steps After POC

### If POC Succeeds (Quality >70%)

**Option 1: Production Deployment** (Continue with Grok)
- Deploy to team (5-10 users)
- Collect 200+ labeled examples
- Implement Phase 4 (ML models)
- Add Phase 5 (multi-language templates)

**Option 2: Upgrade Hardware** (Better LLM)
- Purchase GPU (RTX 4070/4090)
- Switch to Llama 3.1 8B local
- Reduce cloud dependency to <5%
- Continue as planned in original implementation plan

### If POC Partially Succeeds (Quality 50-70%)

- Identify weak areas (retrieval? generation? validation?)
- Improve prompts
- Add Claude API fallback for complex cases
- 2-week iteration, re-evaluate

### If POC Fails (Quality <50%)

- Analyze root causes
- Consider alternative approaches:
  - Manual pattern curation (no LLM)
  - Rule-based pattern matching
  - Wait for better models

---

## Deliverables

### Code
- [ ] `src/pattern_library/embeddings.py`
- [ ] `src/reverse_engineering/grok_provider.py`
- [ ] `src/pattern_library/suggestion_service.py`
- [ ] `src/pattern_library/nl_generator.py`
- [ ] `src/cli/patterns.py`
- [ ] Extended `src/reverse_engineering/ai_enhancer.py`
- [ ] Extended `src/cli/reverse.py`

### Tests
- [ ] `tests/unit/pattern_library/test_embeddings.py`
- [ ] `tests/unit/reverse_engineering/test_grok_provider.py`
- [ ] `tests/integration/test_phase1_rag.py`
- [ ] `tests/integration/test_phase2_discovery.py`
- [ ] `tests/integration/test_phase3_nl_generation.py`
- [ ] `tests/integration/test_e2e_poc.py`

### Documentation
- [ ] `docs/POC_USER_GUIDE.md`
- [ ] `docs/POC_ARCHITECTURE.md`
- [ ] `docs/POC_RESULTS.md` (after completion)
- [ ] `README_POC.md` (quick start)

### Demo
- [ ] `demo/poc_demo.sh`
- [ ] `demo/sql/` (sample SQL functions)
- [ ] `demo/VIDEO.md` (recorded demo walkthrough)

---

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Phase 1.1 | Embeddings + Grok provider |
| 2 | Phase 1.2 | RAG integration + CLI |
| 3 | Phase 2.1 | Pattern discovery logic |
| 4 | Phase 2.2 | Discovery CLI + review workflow |
| 5 | Phase 3.1 | NL generator + validation |
| 6 | Phase 3.2 | NL CLI + testing |
| 7 | Phase 4.1 | Integration tests + benchmarks |
| 8 | Phase 4.2 | Documentation + demo |

**Total**: 8 weeks, $0 cost, X270-compatible ✅

---

## Conclusion

This POC demonstrates that **advanced pattern library enhancement is feasible with zero cost and minimal hardware** by leveraging:

1. ✅ **OpenCode Grok** (free, fast, good quality)
2. ✅ **CPU-friendly embeddings** (sentence-transformers)
3. ✅ **SQLite** (simple, powerful, local)
4. ✅ **X270 laptop** (sufficient for all operations)

The POC focuses on **high-value, low-hardware-requirement** features (Phases 1-3), deferring ML models and advanced analytics to production deployment with more data.

**Success means**: 70%+ pattern retrieval accuracy, 5-10% discovery rate, 60%+ NL quality, all at $0 cost on a standard laptop.

---

**Document Version**: 1.0 (POC)
**Hardware**: Lenovo X270
**LLM**: OpenCode Grok Code Fast 1 (FREE)
**Status**: Ready to Execute
**Last Updated**: 2025-11-12
