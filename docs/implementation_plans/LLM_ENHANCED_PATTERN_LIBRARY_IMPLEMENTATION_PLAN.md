# LLM-Enhanced Pattern Library System: Implementation Plan

**Project**: SpecQL Pattern Library Enhancement with Advanced LLM Capabilities
**Version**: 1.0
**Date**: 2025-11-12
**Status**: Planning Phase

---

## Executive Summary

### Vision

Enhance SpecQL's existing reverse engineering and pattern library infrastructure with advanced LLM capabilities to minimize cloud LLM dependence while maximizing pattern library utility through intelligent pattern discovery, natural language generation, and multi-language optimization.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SpecQL Enhancement Architecture                  │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  User Interactions   │
│  - CLI Commands      │
│  - NL Descriptions   │
│  - Legacy SQL        │
└──────────┬───────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────┐
│                    Enhanced CLI Layer                          │
│  • specql reverse --discover-patterns                          │
│  • specql patterns create-from-description                     │
│  • specql patterns review-suggestions                          │
│  • specql review {list|approve|reject}                        │
└────────────┬──────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬────────────────┬────────────────┐
    ▼                 ▼                ▼                ▼
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Reverse │    │ Pattern  │    │   ML     │    │  Review  │
│  Eng.   │◄──►│ Library  │◄──►│  Triage  │◄──►│  Service │
│ Pipeline│    │   API    │    │  Service │    │          │
└────┬────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │              │               │               │
     │         ┌────┴─────┐         │               │
     │         ▼          ▼         ▼               │
     │    ┌─────────┐ ┌──────────────────┐         │
     │    │ Pattern │ │   Embedding      │         │
     │    │   DB    │ │   Service (RAG)  │         │
     │    │ (SQLite)│ │  • Similarity    │         │
     │    └─────────┘ │  • Top-K         │         │
     │                │  • Hybrid Search │         │
     │                └──────────────────┘         │
     │                                             │
     └──────────────┬──────────────────────────────┘
                    ▼
        ┌────────────────────────┐
        │   AI Enhancement       │
        │   • Local LLM          │
        │     (Llama 3.1 8B)     │
        │   • Cloud Fallback     │
        │     (Claude Haiku)     │
        │   • Prompt Engineering │
        │   • Context Injection  │
        └────────────────────────┘
```

### Key Components

**Existing (✅) - Leverage**:
- Reverse Engineering Pipeline (`src/reverse_engineering/`)
- Pattern Library 3-Tier Architecture (`src/pattern_library/`)
- AI Enhancer with Local LLM (`ai_enhancer.py`)
- CLI Orchestration (`src/cli/`)
- SQLite Schema (`pattern_library/schema.sql`)

**New (🆕) - Build**:
- Pattern Embedding Service (RAG)
- Pattern Discovery Pipeline
- Natural Language Pattern Generator
- ML Triage Service
- Human Review Workflow
- Multi-Language Template Generator

### Success Metrics

| Metric | Baseline | Target (6 months) |
|--------|----------|-------------------|
| Pattern Library Size | ~30 manual patterns | 200+ patterns (80% auto-discovered) |
| Reverse Engineering Confidence | 95% (with LLM) | 98% (with patterns + ML) |
| Auto-Accept Rate | 0% (all manual review) | 70% (ML-validated) |
| Human Review Time | 5 min/function | 2 min/function |
| Cloud LLM Cost | $0.50/function | $0.10/function (80% reduction) |
| Pattern Reuse Rate | 20% | 60% |

### Resource Requirements

**Team**:
- 1 Senior Engineer (Architecture, Phases 1-3)
- 1 ML Engineer (Phase 4)
- 1 Full-Stack Engineer (Phases 5-6)

**Hardware**:
- RTX 4090 (24 GB VRAM) - already available
- Optional: A6000 (48 GB) for larger models

**Timeline**: 14-16 weeks (3.5-4 months)

---

## 1. Enhanced Pattern Library Schema

### 1.1 Schema Extensions

Extend existing `src/pattern_library/schema.sql` to support ML, embeddings, and pattern evolution.

#### New Tables

```sql
-- ============================================================================
-- Pattern Embeddings for RAG (Tier 2 Enhancement)
-- ============================================================================

CREATE TABLE pattern_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL REFERENCES domain_patterns(id) ON DELETE CASCADE,
    embedding BLOB NOT NULL,              -- Numpy array serialized (pickle/msgpack)
    embedding_model TEXT NOT NULL,        -- e.g., "all-MiniLM-L6-v2"
    embedding_dim INTEGER NOT NULL,       -- 384, 768, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(pattern_id, embedding_model)
);

CREATE INDEX idx_pattern_embeddings_model ON pattern_embeddings(embedding_model);


-- ============================================================================
-- Pattern Suggestions (Human-in-the-Loop Discovery)
-- ============================================================================

CREATE TABLE pattern_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggested_name TEXT NOT NULL,
    suggested_category TEXT NOT NULL,
    description TEXT NOT NULL,
    parameters JSON,                      -- Suggested parameters
    implementation JSON,                  -- Suggested SpecQL implementation

    -- Source tracking
    source_type TEXT NOT NULL,            -- 'reverse_engineering', 'user_nl', 'manual'
    source_sql TEXT,                      -- Original SQL if from reverse engineering
    source_description TEXT,              -- User description if from NL generation
    source_function_id TEXT,              -- Reference to processed function

    -- Metadata
    complexity_score REAL,                -- 0-1 (function complexity)
    confidence_score REAL,                -- 0-1 (LLM confidence)
    trigger_reason TEXT,                  -- Why was this suggested?

    -- Review tracking
    status TEXT DEFAULT 'pending',        -- 'pending', 'approved', 'rejected', 'merged'
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    review_feedback TEXT,
    merged_into_pattern_id INTEGER REFERENCES domain_patterns(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (status IN ('pending', 'approved', 'rejected', 'merged')),
    CHECK (source_type IN ('reverse_engineering', 'user_nl', 'manual'))
);

CREATE INDEX idx_pattern_suggestions_status ON pattern_suggestions(status);
CREATE INDEX idx_pattern_suggestions_category ON pattern_suggestions(suggested_category);
CREATE INDEX idx_pattern_suggestions_created ON pattern_suggestions(created_at DESC);


-- ============================================================================
-- Pattern Versions (Evolution Tracking)
-- ============================================================================

CREATE TABLE pattern_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL REFERENCES domain_patterns(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,

    -- Snapshot of pattern at this version
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    parameters JSON,
    implementation JSON,

    -- Change tracking
    changed_by TEXT,
    change_reason TEXT,
    change_type TEXT,                     -- 'created', 'modified', 'deprecated'
    deprecated BOOLEAN DEFAULT FALSE,
    deprecated_reason TEXT,
    replacement_pattern_id INTEGER REFERENCES domain_patterns(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(pattern_id, version_number),
    CHECK (change_type IN ('created', 'modified', 'deprecated'))
);

CREATE INDEX idx_pattern_versions_pattern ON pattern_versions(pattern_id);
CREATE INDEX idx_pattern_versions_deprecated ON pattern_versions(deprecated);


-- ============================================================================
-- Pattern Quality Metrics
-- ============================================================================

CREATE TABLE pattern_quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL REFERENCES domain_patterns(id) ON DELETE CASCADE,

    -- Usage metrics (already have times_instantiated in domain_patterns)
    success_count INTEGER DEFAULT 0,      -- Times accepted without modification
    failure_count INTEGER DEFAULT 0,      -- Times rejected/modified
    review_required_count INTEGER DEFAULT 0,  -- Times flagged for review

    -- Quality scores (updated periodically)
    success_rate REAL,                    -- success / (success + failure)
    avg_review_time_seconds REAL,        -- Average time to review uses
    complexity_score REAL,                -- Derived from implementation complexity
    reusability_score REAL,               -- How often reused vs similar patterns

    -- Confidence tracking
    avg_confidence_score REAL,            -- Average confidence when detected
    confidence_calibration_factor REAL,   -- Adjustment for calibration

    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(pattern_id)
);

CREATE INDEX idx_pattern_quality_success_rate ON pattern_quality_metrics(success_rate);


-- ============================================================================
-- Pattern Co-occurrence (Which patterns are used together?)
-- ============================================================================

CREATE TABLE pattern_cooccurrence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_a_id INTEGER NOT NULL REFERENCES domain_patterns(id) ON DELETE CASCADE,
    pattern_b_id INTEGER NOT NULL REFERENCES domain_patterns(id) ON DELETE CASCADE,
    cooccurrence_count INTEGER DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(pattern_a_id, pattern_b_id),
    CHECK (pattern_a_id < pattern_b_id)  -- Enforce ordering to prevent duplicates
);

CREATE INDEX idx_pattern_cooccurrence_a ON pattern_cooccurrence(pattern_a_id);
CREATE INDEX idx_pattern_cooccurrence_b ON pattern_cooccurrence(pattern_b_id);


-- ============================================================================
-- Reverse Engineering Results (Training Data for ML)
-- ============================================================================

CREATE TABLE reverse_engineering_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    function_id TEXT NOT NULL UNIQUE,     -- Hash of SQL function

    -- Input
    source_sql TEXT NOT NULL,
    source_file TEXT,

    -- Output
    generated_specql JSON NOT NULL,
    detected_patterns JSON,               -- List of pattern names detected

    -- Confidence scores
    algorithmic_confidence REAL,
    heuristic_confidence REAL,
    ai_confidence REAL,
    ml_confidence REAL,                   -- From ML triage (if available)
    final_confidence REAL,

    -- ML triage
    ml_needs_review BOOLEAN,
    ml_review_confidence REAL,
    ml_pattern_validations JSON,          -- Per-pattern validation scores

    -- Features (for ML training)
    features JSON,                        -- Extracted features (LOC, complexity, etc.)

    -- Human review
    reviewed BOOLEAN DEFAULT FALSE,
    review_status TEXT,                   -- 'approved', 'rejected', 'modified'
    review_feedback TEXT,
    corrected_specql JSON,                -- If modified
    review_time_seconds INTEGER,
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,

    -- Pattern suggestions
    suggested_pattern BOOLEAN DEFAULT FALSE,
    suggestion_id INTEGER REFERENCES pattern_suggestions(id),

    processing_time_ms INTEGER,
    llm_calls INTEGER,                    -- Number of LLM calls made
    cloud_llm_used BOOLEAN,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (review_status IN ('approved', 'rejected', 'modified') OR review_status IS NULL)
);

CREATE INDEX idx_re_results_reviewed ON reverse_engineering_results(reviewed);
CREATE INDEX idx_re_results_confidence ON reverse_engineering_results(final_confidence);
CREATE INDEX idx_re_results_created ON reverse_engineering_results(created_at DESC);


-- ============================================================================
-- ML Model Metadata
-- ============================================================================

CREATE TABLE ml_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_type TEXT NOT NULL,             -- 'pattern_validator', 'needs_review', 'confidence_calibration', 'naming_quality'
    model_version TEXT NOT NULL,

    -- Model files
    model_path TEXT NOT NULL,             -- Path to .keras file
    config JSON,                          -- Model hyperparameters

    -- Training info
    training_samples INTEGER,
    validation_accuracy REAL,
    test_accuracy REAL,
    training_date TIMESTAMP,

    -- Deployment
    status TEXT DEFAULT 'training',       -- 'training', 'deployed', 'deprecated'
    deployed_at TIMESTAMP,
    deprecated_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(model_name, model_version),
    CHECK (status IN ('training', 'deployed', 'deprecated')),
    CHECK (model_type IN ('pattern_validator', 'needs_review', 'confidence_calibration', 'naming_quality'))
);

CREATE INDEX idx_ml_models_status ON ml_models(status);
CREATE INDEX idx_ml_models_type ON ml_models(model_type);


-- ============================================================================
-- LLM Call Logging (Cost & Performance Tracking)
-- ============================================================================

CREATE TABLE llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT NOT NULL UNIQUE,

    -- LLM details
    model_name TEXT NOT NULL,             -- 'llama-3.1-8b', 'claude-haiku', etc.
    is_local BOOLEAN NOT NULL,

    -- Task
    task_type TEXT NOT NULL,              -- 'reverse_engineering', 'pattern_discovery', 'pattern_generation', 'template_generation'
    task_context JSON,                    -- Additional context

    -- Prompt & response
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    prompt_text TEXT,                     -- Optional: for debugging
    response_text TEXT,

    -- Performance
    latency_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,

    -- Cost (for cloud)
    cost_usd REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (task_type IN ('reverse_engineering', 'pattern_discovery', 'pattern_generation', 'template_generation', 'pattern_validation'))
);

CREATE INDEX idx_llm_calls_model ON llm_calls(model_name);
CREATE INDEX idx_llm_calls_task ON llm_calls(task_type);
CREATE INDEX idx_llm_calls_created ON llm_calls(created_at DESC);
```

#### Schema Modifications to Existing Tables

```sql
-- Add source tracking to domain_patterns
ALTER TABLE domain_patterns ADD COLUMN source_type TEXT DEFAULT 'manual';
ALTER TABLE domain_patterns ADD COLUMN source_suggestion_id INTEGER REFERENCES pattern_suggestions(id);
ALTER TABLE domain_patterns ADD COLUMN complexity_score REAL;
ALTER TABLE domain_patterns ADD COLUMN deprecated BOOLEAN DEFAULT FALSE;
ALTER TABLE domain_patterns ADD COLUMN deprecated_reason TEXT;
ALTER TABLE domain_patterns ADD COLUMN replacement_pattern_id INTEGER REFERENCES domain_patterns(id);

-- Add quality metrics reference
ALTER TABLE domain_patterns ADD COLUMN quality_metric_id INTEGER REFERENCES pattern_quality_metrics(id);
```

---

## 2. Local LLM Integration Strategy

### 2.1 Current State Analysis

**Existing (`src/reverse_engineering/ai_enhancer.py`)**:
- Llama 3.1 8B (Q4 quantized) via `llama-cpp-python`
- Model: `~/.specql/models/llama-3.1-8b.gguf`
- GPU acceleration (CUDA/Metal)
- Context: 4096 tokens
- Tasks: Intent inference, variable naming, pattern suggestions

### 2.2 New LLM Tasks

Extend `AIEnhancer` to support additional tasks:

| Task | Input | Output | Model Size | Cloud Escalation? |
|------|-------|--------|------------|-------------------|
| **Pattern Discovery** | SQL function, existing patterns | New pattern suggestion JSON | 8B (local) | If >2000 LOC |
| **Pattern Generation** | Natural language description | Pattern definition JSON | 8B (local) | If ambiguous |
| **Pattern Validation** | SQL function, detected pattern | Validation score (0-1) | 8B (local) | Never (use ML) |
| **Template Generation** | Pattern definition, target lang | Jinja2 template | 13B (cloud) | Always (complex) |
| **Pattern Matching** | SQL function, top-K patterns | Best match + reasoning | 8B (local) | If low confidence |

### 2.3 Prompt Engineering Strategy

#### 2.3.1 Pattern Discovery Prompt

**File**: `src/reverse_engineering/prompts/pattern_discovery.jinja2`

```jinja2
You are a SpecQL pattern architect analyzing legacy SQL functions to discover reusable patterns.

## Task
Determine if this SQL function implements a novel pattern worth adding to the pattern library.

## Context
**Existing Patterns** (for reference):
{% for pattern in existing_patterns %}
- **{{ pattern.name }}** ({{ pattern.category }}): {{ pattern.description }}
{% endfor %}

**SQL Function**:
```sql
{{ sql_function }}
```

**Parsed SpecQL** (current understanding):
```yaml
{{ specql_ast | toyaml }}
```

**Complexity Metrics**:
- Lines of Code: {{ metrics.loc }}
- Cyclomatic Complexity: {{ metrics.complexity }}
- Pattern Match Confidence: {{ metrics.pattern_confidence }}

## Criteria for New Pattern
1. **Novel**: Doesn't match existing patterns well (<70% similarity)
2. **Reusable**: Can be applied to multiple entities/domains
3. **Non-Trivial**: Complex enough to warrant abstraction
4. **Generalizable**: Can be parameterized for different contexts

## Output Format (JSON)
{
    "is_new_pattern": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Explanation of why this is/isn't a new pattern",
    "suggested_pattern": {
        "name": "snake_case_name",
        "category": "workflow|validation|audit|hierarchy|state_machine|approval|notification|calculation",
        "description": "Clear, concise description",
        "parameters": {
            "param_name": {
                "type": "string|integer|array|boolean",
                "required": true/false,
                "default": "value",
                "description": "What this parameter controls"
            }
        },
        "implementation": {
            "fields": [
                {"name": "field_name", "type": "text|integer|ref(...)|enum(...)", "description": "Purpose"}
            ],
            "actions": [
                {
                    "name": "action_name",
                    "steps": [
                        {"validate": "condition"},
                        {"update": "Entity SET field = value"},
                        {"notify": "target", "template": "template_name"}
                    ]
                }
            ]
        }
    },
    "similar_patterns": ["pattern_name_1", "pattern_name_2"],
    "merge_recommendation": "If this should be merged with an existing pattern, suggest how"
}

## Important Constraints
- Follow SpecQL conventions (Trinity pattern, audit fields)
- Avoid patterns that are too specific (e.g., "invoice_approval" → use generic "multi_stage_approval")
- Make patterns parameterizable
- Consider multi-tenant scenarios (add tenant_id if applicable)

Now analyze the function and respond with JSON ONLY (no markdown, no explanation outside JSON):
```

#### 2.3.2 Natural Language Pattern Generation Prompt

**File**: `src/reverse_engineering/prompts/nl_pattern_generation.jinja2`

```jinja2
You are a SpecQL pattern architect. Generate a reusable domain pattern from a natural language description.

## User Description
{{ user_description }}

## Target Category
{{ category }}  {# workflow, validation, audit, etc. #}

## SpecQL Conventions (MANDATORY)
1. **Trinity Pattern**: All entities have pk_*, id (UUID), identifier (TEXT)
2. **Audit Fields**: created_at, updated_at, deleted_at
3. **Naming**: tb_{entity}, fk_{entity}, idx_tb_{entity}_{field}
4. **Multi-Tenant**: Add tenant_id if applicable

## Output Format (JSON)
{
    "pattern_name": "snake_case_name",
    "category": "{{ category }}",
    "description": "Clear, reusable description",
    "parameters": {
        "entity": {"type": "string", "required": true, "description": "Target entity name"},
        "stages": {"type": "array", "required": false, "default": ["pending", "approved"], "description": "Workflow stages"},
        // Add more parameters as needed
    },
    "implementation": {
        "fields": [
            {"name": "status", "type": "enum({{ '{{' }}stages{{ '}}' }})", "description": "Current status"},
            // Add more fields
        ],
        "actions": [
            {
                "name": "action_name",
                "description": "What this action does",
                "steps": [
                    {"validate": "condition"},
                    {"update": "{{ '{{' }}entity{{ '}}' }} SET field = value"},
                    {"notify": "user_group", "template": "notification_template"}
                ]
            }
        ]
    },
    "multi_tenant": true/false,
    "dependencies": ["other_pattern_name"],  // If this pattern builds on others
    "examples": [
        {
            "entity": "Invoice",
            "description": "How this pattern applies to Invoice entity",
            "instantiated_fields": ["status", "approval_stage"],
            "instantiated_actions": ["submit_for_approval", "approve", "reject"]
        }
    ]
}

## Validation Rules
- Pattern name must be unique and descriptive
- All parameters must have types and descriptions
- Implementation must be valid SpecQL syntax
- Actions must use SpecQL steps (validate, if, insert, update, call, notify, foreach)
- Consider error cases (what if validation fails?)

Now generate the pattern definition as JSON ONLY:
```

#### 2.3.3 Pattern-Aware Reverse Engineering Prompt

**File**: `src/reverse_engineering/prompts/enhance_with_patterns.jinja2`

```jinja2
You are a SpecQL code analyst. Analyze this SQL function using relevant patterns from the library.

## Retrieved Patterns (RAG - Top-K Similar)
{% for pattern in retrieved_patterns %}
### {{ pattern.name }} ({{ pattern.category }}) - Similarity: {{ pattern.similarity }}
**Description**: {{ pattern.description }}
**Typical Fields**: {{ pattern.implementation.fields | map(attribute='name') | join(', ') }}
**Typical Actions**: {{ pattern.implementation.actions | map(attribute='name') | join(', ') }}
{% endfor %}

## SQL Function to Analyze
```sql
{{ sql_function }}
```

## Parsed SpecQL (Algorithmic + Heuristic)
```yaml
{{ specql_ast | toyaml }}
```

## Your Tasks
1. **Pattern Matching**: Which retrieved patterns apply? (Can be multiple)
2. **Variable Naming**: Improve variable names based on pattern conventions
3. **Missing Logic**: Identify missing steps (e.g., audit fields not updated, validations missing)
4. **Confidence**: Rate confidence in the conversion (0.0-1.0)

## Output Format (JSON)
{
    "detected_patterns": [
        {
            "pattern_name": "audit_trail",
            "confidence": 0.95,
            "evidence": "Function updates updated_at field",
            "missing_elements": ["Should also track updated_by"]
        }
    ],
    "variable_mapping": {
        "v_status": "current_status",
        "v_flag": "is_approved"
    },
    "enhanced_specql": {
        // Enhanced version of SpecQL AST
    },
    "confidence": 0.92,
    "warnings": ["Missing validation for status transition"],
    "suggestions": ["Consider adding soft delete support"]
}

Respond with JSON ONLY:
```

### 2.4 Model Considerations

#### Local Model Sizing

| Model | Size (GGUF) | VRAM | Speed | Use Case |
|-------|-------------|------|-------|----------|
| Llama 3.1 8B (Q4) | 4.5 GB | 6 GB | 30 tokens/s | Current default |
| Llama 3.1 8B (Q8) | 8.5 GB | 10 GB | 25 tokens/s | Better accuracy |
| Llama 3.1 13B (Q4) | 7.5 GB | 9 GB | 20 tokens/s | Complex patterns |
| Llama 3.1 70B (Q4) | 38 GB | 40 GB | N/A | Not feasible |

**Recommendation**: Stick with **8B Q4** for initial phases, upgrade to **8B Q8** or **13B Q4** if accuracy issues arise.

#### Cloud Escalation Policy

```python
# src/reverse_engineering/escalation_policy.py

class CloudEscalationPolicy:
    """Determine when to use cloud LLM vs local."""

    def should_escalate(
        self,
        task_type: str,
        complexity_metrics: Dict,
        local_confidence: Optional[float] = None
    ) -> bool:
        """
        Escalation criteria:
        1. Pattern Generation: If user description is ambiguous (contains questions, multiple interpretations)
        2. Reverse Engineering: If function >2000 LOC or local_confidence <0.5
        3. Template Generation: Always escalate (needs deep language knowledge)
        4. Pattern Discovery: If complexity score >0.8 and local_confidence <0.6
        """
        if task_type == "template_generation":
            return True  # Always use cloud for template generation

        if task_type == "pattern_generation":
            # Check for ambiguity markers
            description = complexity_metrics.get("description", "")
            ambiguity_markers = ["?", "or", "maybe", "either", "multiple"]
            if any(marker in description.lower() for marker in ambiguity_markers):
                return True

        if task_type == "reverse_engineering":
            loc = complexity_metrics.get("loc", 0)
            if loc > 2000:
                return True
            if local_confidence and local_confidence < 0.5:
                return True

        if task_type == "pattern_discovery":
            complexity = complexity_metrics.get("complexity_score", 0)
            if complexity > 0.8 and local_confidence and local_confidence < 0.6:
                return True

        return False

    def get_cloud_model(self, task_type: str) -> str:
        """Select appropriate cloud model for task."""
        if task_type == "template_generation":
            return "claude-sonnet-3-5"  # Needs strong reasoning
        else:
            return "claude-haiku"  # Fast and cheap for other tasks
```

---

## 3. Pattern Retrieval & RAG System

### 3.1 Embedding Strategy

#### 3.1.1 What to Embed

**Pattern Embeddings** (generate once per pattern):
```python
pattern_text = f"""
Pattern: {pattern_name}
Category: {category}
Description: {description}
Fields: {', '.join(field_names)}
Actions: {', '.join(action_names)}
Keywords: {', '.join(extracted_keywords)}
"""
```

**Function Embeddings** (generate during reverse engineering):
```python
function_text = f"""
Function: {function_name}
SQL Keywords: {', '.join(sql_keywords)}  # SELECT, UPDATE, INSERT, etc.
Variables: {', '.join(variable_names)}
Complexity: {complexity_score}
Description: {inferred_purpose}
"""
```

#### 3.1.2 Embedding Model Selection

**Options**:
1. **all-MiniLM-L6-v2** (Sentence Transformers)
   - Dim: 384
   - Speed: Very fast (10ms/doc)
   - Quality: Good for general similarity
   - **Recommendation**: Use for MVP

2. **all-mpnet-base-v2** (Sentence Transformers)
   - Dim: 768
   - Speed: Moderate (30ms/doc)
   - Quality: Better than MiniLM
   - **Recommendation**: Upgrade if MiniLM insufficient

3. **text-embedding-3-small** (OpenAI)
   - Dim: 1536
   - Speed: API call (100ms)
   - Quality: Excellent
   - **Recommendation**: Only if local models fail

**Decision**: Start with **all-MiniLM-L6-v2** for Phase 1.

#### 3.1.3 Vector Storage

**Option A: SQLite with `sqlite-vss` Extension** ✅ **RECOMMENDED**
- Pros: Single database, simple deployment, no extra dependencies
- Cons: Slower than dedicated vector DBs for large scale (>10k patterns)
- Implementation: Store embeddings as BLOB, use custom cosine similarity

**Option B: ChromaDB**
- Pros: Purpose-built for embeddings, fast similarity search
- Cons: Extra dependency, separate database
- Implementation: Separate ChromaDB instance

**Option C: FAISS**
- Pros: Extremely fast for large-scale (>100k patterns)
- Cons: In-memory only, complex persistence
- Implementation: Load FAISS index on startup

**Decision**: Use **SQLite BLOB storage** for Phase 1 (simple, sufficient for <1000 patterns). Consider ChromaDB for Phase 6 if library grows significantly.

### 3.2 Retrieval Logic

#### 3.2.1 Hybrid Search Strategy

```python
# src/pattern_library/retrieval.py

class HybridPatternRetrieval:
    """Combines embedding similarity, keyword matching, and category filtering."""

    def retrieve_patterns(
        self,
        query_embedding: np.ndarray,
        query_text: str,
        category_filter: Optional[List[str]] = None,
        top_k: int = 5,
        rerank: bool = True
    ) -> List[Dict]:
        """
        Hybrid retrieval strategy:
        1. Embedding similarity (cosine) → Top-20 candidates
        2. Keyword matching (BM25) → Boost scores
        3. Category filtering → Remove irrelevant
        4. Re-ranking (optional) → LLM judges relevance
        5. Return Top-K
        """
        # Step 1: Embedding similarity
        candidates = self._embedding_search(query_embedding, top_k=20)

        # Step 2: Keyword boosting
        keywords = self._extract_keywords(query_text)
        for candidate in candidates:
            keyword_score = self._keyword_match_score(candidate, keywords)
            candidate['score'] = (
                0.7 * candidate['similarity'] +  # Embedding weight
                0.3 * keyword_score                # Keyword weight
            )

        # Step 3: Category filtering
        if category_filter:
            candidates = [
                c for c in candidates
                if c['category'] in category_filter
            ]

        # Step 4: Sort by combined score
        candidates.sort(key=lambda x: x['score'], reverse=True)

        # Step 5: Re-ranking (optional, uses LLM)
        if rerank and len(candidates) > top_k:
            candidates = self._llm_rerank(query_text, candidates[:top_k * 2])

        return candidates[:top_k]

    def _embedding_search(
        self, query_embedding: np.ndarray, top_k: int
    ) -> List[Dict]:
        """Pure embedding-based search."""
        # Load all pattern embeddings from DB
        query = """
            SELECT p.id, p.name, p.category, p.description, pe.embedding
            FROM domain_patterns p
            JOIN pattern_embeddings pe ON p.id = pe.pattern_id
            WHERE pe.embedding_model = ?
            AND p.deprecated = FALSE
        """
        cursor = self.db.execute(query, (self.embedding_model,))

        candidates = []
        for row in cursor:
            pattern_id, name, category, description, embedding_blob = row
            pattern_embedding = pickle.loads(embedding_blob)
            similarity = self._cosine_similarity(query_embedding, pattern_embedding)

            candidates.append({
                'pattern_id': pattern_id,
                'name': name,
                'category': category,
                'description': description,
                'similarity': similarity,
                'score': similarity  # Initial score
            })

        candidates.sort(key=lambda x: x['similarity'], reverse=True)
        return candidates[:top_k]

    def _keyword_match_score(self, candidate: Dict, keywords: List[str]) -> float:
        """BM25-like keyword matching."""
        text = f"{candidate['name']} {candidate['description']}".lower()
        matches = sum(1 for kw in keywords if kw.lower() in text)
        return matches / len(keywords) if keywords else 0.0

    def _llm_rerank(self, query_text: str, candidates: List[Dict]) -> List[Dict]:
        """Use LLM to re-rank candidates by relevance."""
        # Simplified: Use local LLM to rate relevance
        prompt = f"""
        Query: {query_text}

        Rank these patterns by relevance (1-5 scale):
        {json.dumps([{'name': c['name'], 'description': c['description']} for c in candidates], indent=2)}

        Output JSON: {{"rankings": [{{"name": "...", "relevance": 1-5}}]}}
        """

        response = self.llm_service.call(prompt, task_type="reranking")
        rankings = json.loads(response)['rankings']

        # Update scores based on LLM relevance
        for candidate in candidates:
            relevance = next(
                (r['relevance'] for r in rankings if r['name'] == candidate['name']),
                3  # Default to medium
            )
            candidate['score'] = (
                0.5 * candidate['score'] +
                0.5 * (relevance / 5.0)
            )

        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates
```

### 3.3 Integration Points

#### 3.3.1 Enhanced AI Enhancer

```python
# src/reverse_engineering/ai_enhancer.py (EXTEND)

class AIEnhancer:
    def __init__(
        self,
        use_local: bool = True,
        pattern_library: Optional[PatternLibrary] = None,
        ml_triage: Optional[MLTriageService] = None,
        enable_pattern_discovery: bool = False
    ):
        self.use_local = use_local
        self.pattern_library = pattern_library
        self.ml_triage = ml_triage
        self.enable_pattern_discovery = enable_pattern_discovery

        # Existing initialization
        self.local_llm = self._init_local_llm() if use_local else None
        self.cloud_client = self._init_cloud_client()

        # NEW: Retrieval service
        if pattern_library:
            self.retrieval = HybridPatternRetrieval(
                pattern_library=pattern_library,
                embedding_service=pattern_library.embedding_service,
                llm_service=self
            )

    def enhance_function(
        self, specql_ast: Dict, sql_function: str
    ) -> EnhancedResult:
        """
        Enhanced version with pattern context.

        Flow:
        1. Extract features from SQL
        2. Retrieve relevant patterns (RAG)
        3. Call LLM with pattern context
        4. Apply pattern enhancements
        5. ML validation (if available)
        6. Pattern discovery (if enabled)
        """
        # Step 1: Extract features
        features = self._extract_features(sql_function, specql_ast)

        # Step 2: Retrieve relevant patterns
        patterns = []
        if self.pattern_library:
            # Generate query embedding
            query_embedding = self.pattern_library.embedding_service.embed_function(
                sql=sql_function,
                specql=specql_ast
            )

            # Retrieve top-K patterns
            patterns = self.retrieval.retrieve_patterns(
                query_embedding=query_embedding,
                query_text=sql_function,
                category_filter=None,  # Auto-detect
                top_k=5,
                rerank=True
            )

        # Step 3: LLM enhancement with patterns
        enhanced = self._enhance_with_patterns(
            specql_ast, sql_function, patterns, features
        )

        # Step 4: ML validation
        if self.ml_triage:
            enhanced = self._apply_ml_validation(enhanced, features, patterns)

        # Step 5: Pattern discovery
        if self.enable_pattern_discovery:
            suggestion = self._discover_new_pattern(
                sql_function, specql_ast, enhanced, patterns, features
            )
            if suggestion:
                enhanced.pattern_suggestion = suggestion

        return enhanced

    def _enhance_with_patterns(
        self,
        specql_ast: Dict,
        sql_function: str,
        patterns: List[Dict],
        features: Dict
    ) -> EnhancedResult:
        """Call LLM with pattern context."""
        prompt = self._render_prompt(
            template="enhance_with_patterns.jinja2",
            specql_ast=specql_ast,
            sql_function=sql_function,
            retrieved_patterns=patterns,
            features=features
        )

        response = self._call_llm(prompt, task_type="reverse_engineering")
        result = json.loads(response)

        return EnhancedResult(
            enhanced_specql=result['enhanced_specql'],
            detected_patterns=result['detected_patterns'],
            variable_mapping=result['variable_mapping'],
            confidence=result['confidence'],
            warnings=result.get('warnings', []),
            suggestions=result.get('suggestions', [])
        )

    def _discover_new_pattern(
        self,
        sql_function: str,
        specql_ast: Dict,
        enhanced: EnhancedResult,
        existing_patterns: List[Dict],
        features: Dict
    ) -> Optional[PatternSuggestion]:
        """Determine if this function warrants a new pattern."""
        # Trigger criteria
        if not self._should_suggest_pattern(enhanced, existing_patterns, features):
            return None

        # Generate pattern suggestion
        prompt = self._render_prompt(
            template="pattern_discovery.jinja2",
            sql_function=sql_function,
            specql_ast=specql_ast,
            existing_patterns=existing_patterns,
            metrics=features
        )

        response = self._call_llm(prompt, task_type="pattern_discovery")
        suggestion_data = json.loads(response)

        if not suggestion_data['is_new_pattern']:
            return None

        # Create pattern suggestion
        return PatternSuggestion(
            suggested_name=suggestion_data['suggested_pattern']['name'],
            suggested_category=suggestion_data['suggested_pattern']['category'],
            description=suggestion_data['suggested_pattern']['description'],
            parameters=suggestion_data['suggested_pattern']['parameters'],
            implementation=suggestion_data['suggested_pattern']['implementation'],
            confidence=suggestion_data['confidence'],
            reasoning=suggestion_data['reasoning'],
            source_sql=sql_function,
            source_specql=specql_ast,
            trigger_reason=f"Low pattern match ({max([p['similarity'] for p in existing_patterns])})"
        )

    def _should_suggest_pattern(
        self,
        enhanced: EnhancedResult,
        existing_patterns: List[Dict],
        features: Dict
    ) -> bool:
        """Trigger criteria for pattern suggestion."""
        # Criterion 1: Low pattern match confidence
        if existing_patterns:
            best_match = max(p['similarity'] for p in existing_patterns)
            if best_match < 0.7:
                return True

        # Criterion 2: High complexity
        if features.get('complexity_score', 0) > 0.75:
            return True

        # Criterion 3: Low overall confidence
        if enhanced.confidence < 0.8:
            return True

        # Criterion 4: Specific keywords
        business_keywords = [
            'approval', 'workflow', 'refund', 'tax', 'credit',
            'reconciliation', 'settlement', 'commission'
        ]
        sql_lower = features.get('sql_text', '').lower()
        if any(kw in sql_lower for kw in business_keywords):
            return True

        return False
```

---

## 4. Pattern Discovery & Enrichment Pipeline

### 4.1 Architecture

```
SQL Function → Reverse Engineering Pipeline → Pattern Discovery Check
                                                        │
                                    ┌───────────────────┴─────────────────────┐
                                    │ Trigger Criteria Met?                   │
                                    │ - Low pattern match (<70%)               │
                                    │ - High complexity (>0.75)                │
                                    │ - Low confidence (<0.8)                  │
                                    │ - Business keywords detected             │
                                    └───────────────────┬─────────────────────┘
                                                        ▼
                                            LLM Pattern Analysis
                                            (pattern_discovery prompt)
                                                        │
                                    ┌───────────────────┴─────────────────────┐
                                    │ Is New Pattern? (LLM Decision)           │
                                    └───────────────────┬─────────────────────┘
                                                        ▼
                                            Create Pattern Suggestion
                                            (pattern_suggestions table)
                                                        │
                                                        ▼
                                            Human Review Workflow
                                            (CLI: specql patterns review)
                                                        │
                                    ┌───────────────────┴─────────────────────┐
                                    ▼                                         ▼
                                Approve                                   Reject
                                    │                                         │
                        Add to domain_patterns                    Log feedback
                        Generate embeddings                       (ML training data)
                        Mark as 'pending_validation'
                        Track usage for promotion
```

### 4.2 Implementation

#### 4.2.1 Pattern Suggestion Service

**File**: `src/pattern_library/suggestion_service.py` (NEW)

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from pathlib import Path

@dataclass
class PatternSuggestion:
    """Represents a suggested pattern awaiting review."""
    suggested_name: str
    suggested_category: str
    description: str
    parameters: Dict
    implementation: Dict

    # Source
    source_type: str  # 'reverse_engineering', 'user_nl'
    source_sql: Optional[str] = None
    source_description: Optional[str] = None
    source_function_id: Optional[str] = None

    # Metadata
    complexity_score: float = 0.0
    confidence_score: float = 0.0
    trigger_reason: str = ""

    # Similar patterns
    similar_patterns: List[str] = None
    merge_recommendation: Optional[str] = None


class PatternSuggestionService:
    """Manages pattern suggestions and review workflow."""

    def __init__(self, db_path: Path):
        self.db = sqlite3.connect(db_path)

    def create_suggestion(
        self, suggestion: PatternSuggestion
    ) -> int:
        """Create a new pattern suggestion."""
        cursor = self.db.execute(
            """
            INSERT INTO pattern_suggestions (
                suggested_name, suggested_category, description,
                parameters, implementation,
                source_type, source_sql, source_description, source_function_id,
                complexity_score, confidence_score, trigger_reason,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                suggestion.suggested_name,
                suggestion.suggested_category,
                suggestion.description,
                json.dumps(suggestion.parameters),
                json.dumps(suggestion.implementation),
                suggestion.source_type,
                suggestion.source_sql,
                suggestion.source_description,
                suggestion.source_function_id,
                suggestion.complexity_score,
                suggestion.confidence_score,
                suggestion.trigger_reason
            )
        )
        self.db.commit()
        return cursor.lastrowid

    def list_pending_suggestions(
        self, category: Optional[str] = None
    ) -> List[Dict]:
        """List all pending pattern suggestions."""
        query = """
            SELECT id, suggested_name, suggested_category, description,
                   confidence_score, complexity_score, created_at
            FROM pattern_suggestions
            WHERE status = 'pending'
        """
        params = []

        if category:
            query += " AND suggested_category = ?"
            params.append(category)

        query += " ORDER BY confidence_score DESC, created_at DESC"

        cursor = self.db.execute(query, params)
        return [
            {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'description': row[3],
                'confidence': row[4],
                'complexity': row[5],
                'created_at': row[6]
            }
            for row in cursor
        ]

    def get_suggestion(self, suggestion_id: int) -> Dict:
        """Get full suggestion details."""
        cursor = self.db.execute(
            """
            SELECT suggested_name, suggested_category, description,
                   parameters, implementation,
                   source_type, source_sql, source_description,
                   complexity_score, confidence_score, trigger_reason,
                   status, reviewed_by, reviewed_at, review_feedback
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
            'parameters': json.loads(row[3]),
            'implementation': json.loads(row[4]),
            'source_type': row[5],
            'source_sql': row[6],
            'source_description': row[7],
            'complexity_score': row[8],
            'confidence_score': row[9],
            'trigger_reason': row[10],
            'status': row[11],
            'reviewed_by': row[12],
            'reviewed_at': row[13],
            'review_feedback': row[14]
        }

    def approve_suggestion(
        self,
        suggestion_id: int,
        reviewed_by: str,
        feedback: Optional[str] = None,
        modifications: Optional[Dict] = None
    ) -> int:
        """Approve a suggestion and add to pattern library."""
        # Get suggestion
        suggestion = self.get_suggestion(suggestion_id)

        # Apply modifications if provided
        if modifications:
            suggestion['name'] = modifications.get('name', suggestion['name'])
            suggestion['description'] = modifications.get('description', suggestion['description'])
            suggestion['parameters'] = modifications.get('parameters', suggestion['parameters'])
            suggestion['implementation'] = modifications.get('implementation', suggestion['implementation'])

        # Add to domain_patterns
        cursor = self.db.execute(
            """
            INSERT INTO domain_patterns (
                name, category, description, parameters, implementation,
                source_type, source_suggestion_id, complexity_score
            ) VALUES (?, ?, ?, ?, ?, 'suggestion', ?, ?)
            """,
            (
                suggestion['name'],
                suggestion['category'],
                suggestion['description'],
                json.dumps(suggestion['parameters']),
                json.dumps(suggestion['implementation']),
                suggestion_id,
                suggestion['complexity_score']
            )
        )
        pattern_id = cursor.lastrowid

        # Mark suggestion as approved
        self.db.execute(
            """
            UPDATE pattern_suggestions
            SET status = 'approved',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                review_feedback = ?,
                merged_into_pattern_id = ?
            WHERE id = ?
            """,
            (reviewed_by, feedback, pattern_id, suggestion_id)
        )

        self.db.commit()
        return pattern_id

    def reject_suggestion(
        self,
        suggestion_id: int,
        reviewed_by: str,
        feedback: str
    ):
        """Reject a suggestion."""
        self.db.execute(
            """
            UPDATE pattern_suggestions
            SET status = 'rejected',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                review_feedback = ?
            WHERE id = ?
            """,
            (reviewed_by, feedback, suggestion_id)
        )
        self.db.commit()

    def merge_suggestion(
        self,
        suggestion_id: int,
        target_pattern_id: int,
        reviewed_by: str,
        feedback: str
    ):
        """Merge suggestion into existing pattern."""
        self.db.execute(
            """
            UPDATE pattern_suggestions
            SET status = 'merged',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                review_feedback = ?,
                merged_into_pattern_id = ?
            WHERE id = ?
            """,
            (reviewed_by, feedback, target_pattern_id, suggestion_id)
        )
        self.db.commit()
```

#### 4.2.2 CLI Integration

**File**: `src/cli/patterns.py` (NEW)

```python
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import json

console = Console()

@click.group(name="patterns")
def patterns_cli():
    """Pattern library management commands."""
    pass

@patterns_cli.command(name="review-suggestions")
@click.option("--category", help="Filter by category")
def review_suggestions(category: Optional[str]):
    """List pending pattern suggestions for review."""
    from src.pattern_library.suggestion_service import PatternSuggestionService

    service = PatternSuggestionService(db_path=Path("~/.specql/patterns.db").expanduser())
    suggestions = service.list_pending_suggestions(category=category)

    if not suggestions:
        console.print("[yellow]No pending suggestions found.[/yellow]")
        return

    table = Table(title="Pending Pattern Suggestions")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Category", style="magenta")
    table.add_column("Confidence", style="yellow")
    table.add_column("Created", style="dim")

    for s in suggestions:
        table.add_row(
            str(s['id']),
            s['name'],
            s['category'],
            f"{s['confidence']:.2f}",
            s['created_at'][:10]
        )

    console.print(table)
    console.print(f"\nReview a suggestion: [cyan]specql patterns show {suggestions[0]['id']}[/cyan]")


@patterns_cli.command(name="show")
@click.argument("suggestion_id", type=int)
def show_suggestion(suggestion_id: int):
    """Show detailed suggestion."""
    from src.pattern_library.suggestion_service import PatternSuggestionService

    service = PatternSuggestionService(db_path=Path("~/.specql/patterns.db").expanduser())
    suggestion = service.get_suggestion(suggestion_id)

    # Header
    console.print(Panel(
        f"[bold]{suggestion['name']}[/bold] ({suggestion['category']})\n"
        f"{suggestion['description']}\n\n"
        f"Confidence: {suggestion['confidence_score']:.2f} | "
        f"Complexity: {suggestion['complexity_score']:.2f}\n"
        f"Trigger: {suggestion['trigger_reason']}",
        title="Pattern Suggestion"
    ))

    # Source SQL
    if suggestion['source_sql']:
        console.print("\n[bold]Source SQL:[/bold]")
        syntax = Syntax(suggestion['source_sql'], "sql", theme="monokai", line_numbers=True)
        console.print(syntax)

    # Parameters
    console.print("\n[bold]Parameters:[/bold]")
    console.print(json.dumps(suggestion['parameters'], indent=2))

    # Implementation
    console.print("\n[bold]Implementation:[/bold]")
    console.print(json.dumps(suggestion['implementation'], indent=2))

    # Actions
    console.print("\n[bold]Actions:[/bold]")
    console.print(f"[green]specql patterns approve {suggestion_id}[/green] - Approve and add to library")
    console.print(f"[yellow]specql patterns edit {suggestion_id}[/yellow] - Edit before approving")
    console.print(f"[red]specql patterns reject {suggestion_id} --reason \"...\"[/red] - Reject")


@patterns_cli.command(name="approve")
@click.argument("suggestion_id", type=int)
@click.option("--feedback", help="Approval feedback")
def approve_suggestion(suggestion_id: int, feedback: Optional[str]):
    """Approve a pattern suggestion."""
    from src.pattern_library.suggestion_service import PatternSuggestionService

    service = PatternSuggestionService(db_path=Path("~/.specql/patterns.db").expanduser())

    # Get current user (simplified)
    import getpass
    reviewed_by = getpass.getuser()

    pattern_id = service.approve_suggestion(
        suggestion_id=suggestion_id,
        reviewed_by=reviewed_by,
        feedback=feedback
    )

    console.print(f"[green]✓[/green] Suggestion approved and added as pattern ID {pattern_id}")
    console.print(f"  Generate embeddings: [cyan]specql patterns generate-embeddings {pattern_id}[/cyan]")


@patterns_cli.command(name="reject")
@click.argument("suggestion_id", type=int)
@click.option("--reason", required=True, help="Rejection reason")
def reject_suggestion(suggestion_id: int, reason: str):
    """Reject a pattern suggestion."""
    from src.pattern_library.suggestion_service import PatternSuggestionService

    service = PatternSuggestionService(db_path=Path("~/.specql/patterns.db").expanduser())

    import getpass
    reviewed_by = getpass.getuser()

    service.reject_suggestion(
        suggestion_id=suggestion_id,
        reviewed_by=reviewed_by,
        feedback=reason
    )

    console.print(f"[red]✗[/red] Suggestion rejected: {reason}")


@patterns_cli.command(name="create-from-description")
@click.option("--description", required=True, help="Natural language description")
@click.option("--category", required=True, help="Pattern category")
@click.option("--namespace", help="Namespace (crm, ecommerce, etc.)")
@click.option("--review", is_flag=True, help="Review before adding")
def create_from_description(
    description: str,
    category: str,
    namespace: Optional[str],
    review: bool
):
    """Generate pattern from natural language description."""
    console.print(f"[cyan]Generating pattern from description...[/cyan]")

    from src.pattern_library.api import PatternLibrary
    from src.reverse_engineering.ai_enhancer import AIEnhancer

    lib = PatternLibrary(db_path=Path("~/.specql/patterns.db").expanduser())
    enhancer = AIEnhancer(use_local=True)

    # Generate pattern
    result = lib.create_pattern_from_nl(
        description=description,
        category=category,
        namespace=namespace,
        llm_service=enhancer
    )

    # Show preview
    console.print("\n[bold]Generated Pattern:[/bold]")
    console.print(json.dumps(result['pattern'], indent=2))

    if review:
        # Create suggestion for review
        from src.pattern_library.suggestion_service import PatternSuggestionService, PatternSuggestion

        service = PatternSuggestionService(db_path=Path("~/.specql/patterns.db").expanduser())
        suggestion = PatternSuggestion(
            suggested_name=result['pattern']['pattern_name'],
            suggested_category=result['pattern']['category'],
            description=result['pattern']['description'],
            parameters=result['pattern']['parameters'],
            implementation=result['pattern']['implementation'],
            source_type='user_nl',
            source_description=description,
            confidence_score=result.get('confidence', 0.8)
        )

        suggestion_id = service.create_suggestion(suggestion)
        console.print(f"\n[yellow]Created suggestion ID {suggestion_id} for review[/yellow]")
        console.print(f"Review: [cyan]specql patterns show {suggestion_id}[/cyan]")
    else:
        # Add directly
        pattern_id = lib.add_domain_pattern(
            name=result['pattern']['pattern_name'],
            category=result['pattern']['category'],
            description=result['pattern']['description'],
            parameters=result['pattern']['parameters'],
            implementation=result['pattern']['implementation']
        )
        console.print(f"\n[green]✓[/green] Pattern added as ID {pattern_id}")
```

---

## 5. Natural Language Pattern Generation

### 5.1 Implementation

**File**: `src/pattern_library/api.py` (EXTEND)

```python
class PatternLibrary:
    # ... existing methods ...

    def create_pattern_from_nl(
        self,
        description: str,
        category: str,
        namespace: Optional[str] = None,
        llm_service: Optional[Any] = None
    ) -> Dict:
        """
        Generate domain pattern from natural language description.

        Args:
            description: User's natural language description
            category: Pattern category (workflow, validation, etc.)
            namespace: Optional namespace (crm, ecommerce, etc.)
            llm_service: LLM service for generation (AIEnhancer instance)

        Returns:
            {
                "pattern": {...},      # Generated pattern definition
                "preview": "...",      # Preview of instantiated pattern
                "validation": {...},   # Validation results
                "confidence": 0.0-1.0
            }
        """
        if not llm_service:
            raise ValueError("LLM service required for NL pattern generation")

        # Generate pattern
        prompt = self._render_nl_generation_prompt(
            description=description,
            category=category,
            namespace=namespace
        )

        response = llm_service._call_llm(prompt, task_type="pattern_generation")
        pattern_data = json.loads(response)

        # Validate pattern
        validation = self._validate_pattern_definition(pattern_data)

        # Generate preview
        preview = self._generate_pattern_preview(pattern_data)

        # Confidence scoring
        confidence = self._score_pattern_confidence(pattern_data, validation)

        return {
            'pattern': pattern_data,
            'preview': preview,
            'validation': validation,
            'confidence': confidence
        }

    def _validate_pattern_definition(self, pattern: Dict) -> Dict:
        """
        Validate generated pattern.

        Checks:
        1. Required fields present
        2. SpecQL syntax validity
        3. Naming conventions
        4. Parameter consistency
        5. Implementation completeness
        """
        errors = []
        warnings = []

        # Check required fields
        required_fields = ['pattern_name', 'category', 'description', 'parameters', 'implementation']
        for field in required_fields:
            if field not in pattern:
                errors.append(f"Missing required field: {field}")

        # Check naming conventions
        if 'pattern_name' in pattern:
            if not re.match(r'^[a-z][a-z0-9_]*$', pattern['pattern_name']):
                errors.append("Pattern name must be snake_case")

        # Check SpecQL syntax in implementation
        if 'implementation' in pattern:
            impl = pattern['implementation']

            # Validate fields
            if 'fields' in impl:
                for field in impl['fields']:
                    if 'name' not in field or 'type' not in field:
                        errors.append(f"Field missing name or type: {field}")

            # Validate actions
            if 'actions' in impl:
                for action in impl['actions']:
                    if 'name' not in action or 'steps' not in action:
                        errors.append(f"Action missing name or steps: {action}")

                    # Validate steps
                    for step in action.get('steps', []):
                        valid_steps = ['validate', 'if', 'insert', 'update', 'call', 'notify', 'foreach']
                        if not any(s in step for s in valid_steps):
                            warnings.append(f"Unknown step type: {step}")

        # Check parameter usage in implementation
        if 'parameters' in pattern and 'implementation' in pattern:
            impl_str = json.dumps(pattern['implementation'])
            for param_name in pattern['parameters'].keys():
                if f"{{{{{param_name}}}}}" not in impl_str:
                    warnings.append(f"Parameter '{param_name}' not used in implementation")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _generate_pattern_preview(self, pattern: Dict) -> str:
        """Generate preview of instantiated pattern."""
        # Use example entity
        entity_name = "SampleEntity"

        preview_parts = []
        preview_parts.append(f"# Pattern: {pattern['pattern_name']}")
        preview_parts.append(f"# {pattern['description']}\n")

        # Fields
        if 'fields' in pattern.get('implementation', {}):
            preview_parts.append("## Fields:")
            for field in pattern['implementation']['fields']:
                preview_parts.append(f"- {field['name']}: {field['type']}")

        # Actions
        if 'actions' in pattern.get('implementation', {}):
            preview_parts.append("\n## Actions:")
            for action in pattern['implementation']['actions']:
                preview_parts.append(f"- {action['name']}")
                for i, step in enumerate(action.get('steps', []), 1):
                    step_type = list(step.keys())[0]
                    preview_parts.append(f"  {i}. {step_type}: {step[step_type]}")

        return "\n".join(preview_parts)

    def _score_pattern_confidence(self, pattern: Dict, validation: Dict) -> float:
        """Score confidence in generated pattern."""
        score = 1.0

        # Penalize validation errors
        score -= len(validation['errors']) * 0.2
        score -= len(validation['warnings']) * 0.05

        # Bonus for completeness
        if 'examples' in pattern:
            score += 0.1

        if 'dependencies' in pattern:
            score += 0.05

        # Bonus for parameter usage
        if 'parameters' in pattern:
            param_count = len(pattern['parameters'])
            if 2 <= param_count <= 5:  # Sweet spot
                score += 0.1

        return max(0.0, min(1.0, score))
```

---

## 6. ML-Based QA & Triage System

### 6.1 Model Architecture

#### 6.1.1 Feature Extraction

**File**: `src/reverse_engineering/feature_extraction.py` (NEW)

```python
import re
from typing import Dict
import numpy as np
from collections import Counter

class FeatureExtractor:
    """Extract features from SQL functions for ML models."""

    def extract(self, sql_function: str, specql_ast: Dict) -> Dict:
        """
        Extract comprehensive features for ML models.

        Returns:
            {
                'structural': {...},  # Code structure features
                'semantic': {...},    # Semantic features
                'complexity': {...},  # Complexity metrics
                'patterns': {...}     # Pattern-related features
            }
        """
        return {
            'structural': self._extract_structural_features(sql_function),
            'semantic': self._extract_semantic_features(sql_function),
            'complexity': self._extract_complexity_features(sql_function, specql_ast),
            'patterns': self._extract_pattern_features(specql_ast)
        }

    def _extract_structural_features(self, sql: str) -> Dict:
        """Code structure features."""
        lines = sql.split('\n')

        return {
            'loc': len(lines),
            'blank_lines': sum(1 for line in lines if not line.strip()),
            'comment_lines': sum(1 for line in lines if line.strip().startswith('--')),
            'max_line_length': max(len(line) for line in lines) if lines else 0,
            'avg_line_length': np.mean([len(line) for line in lines]) if lines else 0,
            'indentation_levels': self._count_indentation_levels(sql)
        }

    def _extract_semantic_features(self, sql: str) -> Dict:
        """Semantic features (keywords, variables, etc.)."""
        sql_upper = sql.upper()

        # SQL keywords
        keywords = {
            'SELECT': sql_upper.count('SELECT'),
            'INSERT': sql_upper.count('INSERT'),
            'UPDATE': sql_upper.count('UPDATE'),
            'DELETE': sql_upper.count('DELETE'),
            'IF': sql_upper.count('IF'),
            'WHILE': sql_upper.count('WHILE'),
            'FOR': sql_upper.count('FOR'),
            'CASE': sql_upper.count('CASE'),
            'JOIN': sql_upper.count('JOIN'),
            'WHERE': sql_upper.count('WHERE'),
            'GROUP BY': sql_upper.count('GROUP BY'),
            'HAVING': sql_upper.count('HAVING'),
            'ORDER BY': sql_upper.count('ORDER BY')
        }

        # Variable patterns
        variables = re.findall(r'\b[vp]_\w+\b', sql, re.IGNORECASE)

        # Business keywords
        business_keywords = [
            'approval', 'workflow', 'refund', 'tax', 'credit',
            'reconciliation', 'settlement', 'commission', 'invoice',
            'payment', 'transaction', 'audit', 'status'
        ]
        business_keyword_count = sum(
            1 for kw in business_keywords if kw in sql.lower()
        )

        return {
            **keywords,
            'total_keywords': sum(keywords.values()),
            'unique_variables': len(set(variables)),
            'business_keyword_count': business_keyword_count
        }

    def _extract_complexity_features(self, sql: str, specql_ast: Dict) -> Dict:
        """Complexity metrics."""
        # Cyclomatic complexity (simplified)
        decision_points = (
            sql.upper().count('IF') +
            sql.upper().count('CASE') +
            sql.upper().count('WHILE') +
            sql.upper().count('FOR')
        )
        cyclomatic_complexity = decision_points + 1

        # Nesting depth
        nesting_depth = self._calculate_nesting_depth(sql)

        # SpecQL primitive counts
        specql_primitives = self._count_specql_primitives(specql_ast)

        return {
            'cyclomatic_complexity': cyclomatic_complexity,
            'nesting_depth': nesting_depth,
            **specql_primitives,
            'complexity_score': self._calculate_complexity_score(
                cyclomatic_complexity, nesting_depth, specql_primitives
            )
        }

    def _extract_pattern_features(self, specql_ast: Dict) -> Dict:
        """Pattern-related features."""
        # Check for common pattern indicators
        has_status_field = self._has_field(specql_ast, 'status')
        has_audit_fields = (
            self._has_field(specql_ast, 'created_at') and
            self._has_field(specql_ast, 'updated_at')
        )
        has_soft_delete = self._has_field(specql_ast, 'deleted_at')
        has_approval_field = self._has_field(specql_ast, 'approved')

        return {
            'has_status_field': has_status_field,
            'has_audit_fields': has_audit_fields,
            'has_soft_delete': has_soft_delete,
            'has_approval_field': has_approval_field,
            'action_count': len(specql_ast.get('actions', [])),
            'field_count': len(specql_ast.get('fields', []))
        }

    def to_vector(self, features: Dict) -> np.ndarray:
        """Convert feature dict to numpy vector for ML models."""
        # Flatten all features
        flat_features = []

        for category in ['structural', 'semantic', 'complexity', 'patterns']:
            for key, value in features[category].items():
                if isinstance(value, bool):
                    flat_features.append(1.0 if value else 0.0)
                elif isinstance(value, (int, float)):
                    flat_features.append(float(value))

        return np.array(flat_features, dtype=np.float32)

    # Helper methods
    def _count_indentation_levels(self, sql: str) -> int:
        max_indent = 0
        for line in sql.split('\n'):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent // 4)  # Assume 4-space indent
        return max_indent

    def _calculate_nesting_depth(self, sql: str) -> int:
        depth = 0
        max_depth = 0
        for char in sql.upper():
            if char == '(':
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == ')':
                depth -= 1
        return max_depth

    def _count_specql_primitives(self, specql_ast: Dict) -> Dict:
        """Count SpecQL primitive usage."""
        primitives = {
            'validate_steps': 0,
            'if_steps': 0,
            'insert_steps': 0,
            'update_steps': 0,
            'call_steps': 0,
            'notify_steps': 0,
            'foreach_steps': 0
        }

        for action in specql_ast.get('actions', []):
            for step in action.get('steps', []):
                for step_type in primitives.keys():
                    key = step_type.replace('_steps', '')
                    if key in step:
                        primitives[step_type] += 1

        return primitives

    def _calculate_complexity_score(
        self, cyclomatic: int, nesting: int, primitives: Dict
    ) -> float:
        """Overall complexity score (0-1)."""
        # Normalize components
        cyclomatic_norm = min(cyclomatic / 20.0, 1.0)  # Cap at 20
        nesting_norm = min(nesting / 10.0, 1.0)        # Cap at 10
        primitive_count = sum(primitives.values())
        primitive_norm = min(primitive_count / 30.0, 1.0)  # Cap at 30

        # Weighted average
        score = (
            0.4 * cyclomatic_norm +
            0.3 * nesting_norm +
            0.3 * primitive_norm
        )

        return score

    def _has_field(self, specql_ast: Dict, field_name: str) -> bool:
        """Check if AST contains field."""
        for field in specql_ast.get('fields', []):
            if field.get('name') == field_name:
                return True
        return False
```

#### 6.1.2 ML Models

**File**: `src/reverse_engineering/ml_triage.py` (NEW)

```python
import tensorflow as tf
from tensorflow import keras
from pathlib import Path
import numpy as np
from typing import Dict, Tuple, Optional
import json

class MLTriageService:
    """ML-based validation and triage for reverse engineering."""

    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.pattern_validator = None
        self.needs_review_clf = None
        self.confidence_calibrator = None

        # Load models if they exist
        self._load_models()

    def _load_models(self):
        """Load trained models from disk."""
        try:
            pattern_val_path = self.model_dir / "pattern_validator.keras"
            if pattern_val_path.exists():
                self.pattern_validator = keras.models.load_model(pattern_val_path)

            needs_review_path = self.model_dir / "needs_review.keras"
            if needs_review_path.exists():
                self.needs_review_clf = keras.models.load_model(needs_review_path)

            confidence_cal_path = self.model_dir / "confidence_calibrator.keras"
            if confidence_cal_path.exists():
                self.confidence_calibrator = keras.models.load_model(confidence_cal_path)
        except Exception as e:
            print(f"Warning: Could not load ML models: {e}")

    def validate_pattern(
        self, features: np.ndarray, detected_pattern: str
    ) -> float:
        """
        Validate if detected pattern actually applies.

        Returns:
            Probability that pattern is correct (0-1)
        """
        if not self.pattern_validator:
            return 0.5  # Neutral if model not available

        # Combine features with pattern one-hot encoding
        pattern_features = self._encode_pattern(detected_pattern)
        combined_features = np.concatenate([features, pattern_features])
        combined_features = combined_features.reshape(1, -1)

        # Predict
        probability = self.pattern_validator.predict(combined_features, verbose=0)[0][0]
        return float(probability)

    def should_review(
        self, features: np.ndarray, ai_output: Dict
    ) -> Tuple[bool, float]:
        """
        Determine if function needs human review.

        Returns:
            (needs_review, confidence)
        """
        if not self.needs_review_clf:
            # Fallback: Review if confidence < 0.9
            conf = ai_output.get('confidence', 0.5)
            return conf < 0.9, 0.5

        # Combine features with AI output metadata
        ai_features = self._encode_ai_output(ai_output)
        combined_features = np.concatenate([features, ai_features])
        combined_features = combined_features.reshape(1, -1)

        # Predict
        review_prob = self.needs_review_clf.predict(combined_features, verbose=0)[0][0]

        # Threshold: >0.7 = needs review
        needs_review = review_prob > 0.7

        return needs_review, float(review_prob)

    def calibrate_confidence(
        self, features: np.ndarray, raw_confidence: float
    ) -> float:
        """
        Calibrate confidence score based on historical accuracy.

        Returns:
            Calibrated confidence (0-1)
        """
        if not self.confidence_calibrator:
            return raw_confidence  # No calibration if model not available

        # Combine features with raw confidence
        combined_features = np.concatenate([features, [raw_confidence]])
        combined_features = combined_features.reshape(1, -1)

        # Predict calibrated confidence
        calibrated = self.confidence_calibrator.predict(combined_features, verbose=0)[0][0]
        return float(np.clip(calibrated, 0.0, 1.0))

    # Helper methods
    def _encode_pattern(self, pattern_name: str) -> np.ndarray:
        """One-hot encode pattern name."""
        # Known patterns
        patterns = [
            'state_machine', 'audit_trail', 'soft_delete', 'validation_chain',
            'workflow', 'approval', 'hierarchy', 'notification'
        ]

        encoding = np.zeros(len(patterns), dtype=np.float32)
        if pattern_name in patterns:
            idx = patterns.index(pattern_name)
            encoding[idx] = 1.0

        return encoding

    def _encode_ai_output(self, ai_output: Dict) -> np.ndarray:
        """Encode AI output metadata."""
        return np.array([
            ai_output.get('confidence', 0.5),
            len(ai_output.get('detected_patterns', [])),
            len(ai_output.get('warnings', [])),
            len(ai_output.get('variable_mapping', {}))
        ], dtype=np.float32)


# ============================================================================
# Model Training (Separate script)
# ============================================================================

class ModelTrainer:
    """Train ML models from logged data."""

    def __init__(self, db_path: Path):
        self.db = sqlite3.connect(db_path)

    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load training data from reverse_engineering_results table.

        Returns:
            X (features), y (labels)
        """
        query = """
            SELECT features, reviewed, review_status
            FROM reverse_engineering_results
            WHERE reviewed = TRUE
        """

        cursor = self.db.execute(query)

        X = []
        y = []

        for row in cursor:
            features_json, reviewed, review_status = row
            features = json.loads(features_json)

            # Convert features dict to vector
            # (Use FeatureExtractor.to_vector logic)
            feature_vector = self._features_to_vector(features)
            X.append(feature_vector)

            # Label: 1 if approved, 0 if rejected/modified
            label = 1 if review_status == 'approved' else 0
            y.append(label)

        return np.array(X), np.array(y)

    def train_pattern_validator(
        self, X_train: np.ndarray, y_train: np.ndarray
    ) -> keras.Model:
        """Train pattern validation classifier."""
        model = keras.Sequential([
            keras.layers.Input(shape=(X_train.shape[1],)),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )

        model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            verbose=1
        )

        return model

    def train_needs_review_classifier(
        self, X_train: np.ndarray, y_train: np.ndarray
    ) -> keras.Model:
        """Train needs-review classifier."""
        # Similar architecture to pattern_validator
        model = keras.Sequential([
            keras.layers.Input(shape=(X_train.shape[1],)),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            verbose=1
        )

        return model

    def train_confidence_calibrator(
        self, X_train: np.ndarray, y_train: np.ndarray
    ) -> keras.Model:
        """Train confidence calibration regressor."""
        model = keras.Sequential([
            keras.layers.Input(shape=(X_train.shape[1],)),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')  # Output: calibrated confidence
        ])

        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )

        model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            verbose=1
        )

        return model
```

---

## 7. Phased Implementation Roadmap

### Phase 0: Foundation & Planning (Week 1)

**Goals**:
- Finalize architecture decisions
- Set up development environment
- Create tracking infrastructure

**Tasks**:
1. Schema migration for new tables
2. Set up testing infrastructure
3. Create baseline metrics dashboard
4. Document API contracts

**Success Criteria**:
- [ ] All new schema tables created
- [ ] Migration scripts tested
- [ ] Baseline metrics collected

**Deliverables**:
- Schema migration SQL
- Testing framework setup
- Metrics dashboard (simple CLI)

---

### Phase 1: Pattern Embeddings & Retrieval (MVP) (Weeks 2-3)

**Goals**:
- Enable similarity-based pattern retrieval
- Integrate RAG into AI enhancer

**Main Tasks**:

#### Week 2: Embedding Infrastructure
1. **Implement `PatternEmbeddingService`**
   - Choose embedding model (**all-MiniLM-L6-v2**)
   - Implement `embed_pattern()` and `embed_function()`
   - Test embedding generation

2. **Database Integration**
   - Implement embedding storage/retrieval
   - Batch generate embeddings for existing patterns
   - Verify storage efficiency

3. **Unit Tests**
   - Test embedding generation
   - Test storage/retrieval
   - Test similarity computation

#### Week 3: Retrieval Integration
4. **Implement `HybridPatternRetrieval`**
   - Embedding-based search
   - Keyword boosting
   - Category filtering

5. **Extend `AIEnhancer`**
   - Add pattern retrieval before LLM call
   - Update prompts to include retrieved patterns
   - Test end-to-end

6. **Integration Tests**
   - Test reverse engineering with pattern context
   - Measure accuracy improvement
   - A/B test vs baseline

**Success Criteria**:
- [ ] All existing patterns have embeddings
- [ ] Retrieval returns relevant patterns (manual validation of top-5)
- [ ] Reverse engineering with patterns shows measurable accuracy improvement (+5% confidence)
- [ ] All tests passing

**Dependencies**: None

**Estimated Effort**: 2 weeks (1 engineer)

**Integration Points**:
- `src/pattern_library/embeddings.py` (NEW)
- `src/pattern_library/api.py` (EXTEND)
- `src/pattern_library/retrieval.py` (NEW)
- `src/reverse_engineering/ai_enhancer.py` (EXTEND)

**Testing**:
- `tests/unit/pattern_library/test_embeddings.py`
- `tests/unit/pattern_library/test_retrieval.py`
- `tests/integration/test_pattern_retrieval.py`

---

### Phase 2: Pattern Discovery Pipeline (Weeks 4-5)

**Goals**:
- Automatically suggest new patterns from legacy code
- Human-in-the-loop review workflow

**Main Tasks**:

#### Week 4: Discovery Logic
1. **Implement trigger criteria in `AIEnhancer`**
   - Low pattern match detection
   - Complexity threshold
   - Business keyword detection

2. **Pattern Discovery Prompt**
   - Design LLM prompt
   - Test on sample functions
   - Iterate on output quality

3. **Implement `PatternSuggestionService`**
   - Create suggestion
   - List pending
   - Get details

#### Week 5: Review Workflow
4. **CLI Commands**
   - `specql patterns review-suggestions`
   - `specql patterns show <id>`
   - `specql patterns approve <id>`
   - `specql patterns reject <id>`

5. **Integration with Reverse Engineering**
   - Add `--discover-patterns` flag
   - Log suggestions to database
   - Test end-to-end workflow

6. **Testing & Validation**
   - Unit tests for suggestion service
   - Integration test: Full discovery workflow
   - Manual validation with real legacy SQL

**Success Criteria**:
- [ ] 5-10% of functions trigger pattern suggestions
- [ ] Suggested patterns are valid SpecQL
- [ ] Human can review and approve via CLI
- [ ] Approved patterns reused in subsequent conversions
- [ ] All tests passing

**Dependencies**: Phase 1 (pattern retrieval)

**Estimated Effort**: 2 weeks (1 engineer)

**Integration Points**:
- `src/pattern_library/suggestion_service.py` (NEW)
- `src/reverse_engineering/ai_enhancer.py` (EXTEND)
- `src/cli/patterns.py` (NEW)
- `src/cli/reverse.py` (EXTEND)

**Testing**:
- `tests/unit/pattern_library/test_suggestion_service.py`
- `tests/integration/test_pattern_discovery.py`

---

### Phase 3: Natural Language Pattern Generation (Weeks 6-7)

**Goals**:
- Users can create patterns from text descriptions
- LLM generates structured pattern definitions

**Main Tasks**:

#### Week 6: Pattern Generation
1. **Design NL Generation Prompt**
   - Few-shot examples
   - SpecQL convention enforcement
   - Output validation

2. **Implement `create_pattern_from_nl()` in PatternLibrary**
   - LLM integration
   - Pattern validation
   - Preview generation

3. **Validation Logic**
   - JSON schema validation
   - SpecQL syntax checking
   - Naming convention enforcement

#### Week 7: CLI & Testing
4. **CLI Command**
   - `specql patterns create-from-description`
   - Interactive preview
   - Approval workflow

5. **Testing**
   - Unit tests for pattern generation
   - Test validation logic
   - Integration test: End-to-end generation

6. **Manual Validation**
   - Create 10 real-world patterns
   - Evaluate quality
   - Iterate on prompt

**Success Criteria**:
- [ ] Users can create patterns from descriptions
- [ ] Generated patterns follow SpecQL conventions
- [ ] 80%+ of generated patterns valid on first try
- [ ] Patterns can be instantiated successfully
- [ ] All tests passing

**Dependencies**: Phase 1 (pattern infrastructure)

**Estimated Effort**: 2 weeks (1 engineer)

**Integration Points**:
- `src/pattern_library/api.py` (EXTEND)
- `src/cli/patterns.py` (EXTEND)
- `src/reverse_engineering/prompts/nl_pattern_generation.jinja2` (NEW)

**Testing**:
- `tests/unit/pattern_library/test_nl_generation.py`
- `tests/integration/test_pattern_from_description.py`

---

### Phase 4: ML-Based QA & Triage (Weeks 8-10)

**Goals**:
- Train ML models for pattern validation and review triage
- Reduce human review burden

**Main Tasks**:

#### Week 8: Feature Engineering & Data Collection
1. **Implement `FeatureExtractor`**
   - Structural features
   - Semantic features
   - Complexity metrics
   - Pattern features

2. **Log Training Data**
   - Update reverse engineering pipeline to log results
   - Collect features for each function
   - Track human review decisions

3. **Process Historical Data**
   - Extract features from past conversions
   - Label data based on review outcomes
   - Create train/validation/test splits

#### Week 9: Model Development
4. **Train Baseline Models**
   - Pattern validation classifier
   - Needs-review classifier
   - Confidence calibration regressor

5. **Model Evaluation**
   - Measure accuracy, precision, recall
   - Cross-validation
   - Feature importance analysis

6. **Hyperparameter Tuning**
   - Grid search for optimal parameters
   - Ensemble methods if needed
   - Select best models

#### Week 10: Integration & Testing
7. **Implement `MLTriageService`**
   - Load models
   - Inference logic
   - Batch prediction support

8. **Integrate into `AIEnhancer`**
   - Pattern validation
   - Review triage
   - Confidence calibration

9. **A/B Testing**
   - Compare with/without ML triage
   - Measure auto-accept rate
   - Measure false positive rate
   - Monitor review time reduction

**Success Criteria**:
- [ ] Models achieve >80% accuracy on validation set
- [ ] Auto-accept rate increases by 30%
- [ ] False positive rate for auto-accept <5%
- [ ] Average review time reduced by 40%
- [ ] All tests passing

**Dependencies**: Phase 2 (need human feedback data)

**Estimated Effort**: 3 weeks (1 ML engineer)

**Integration Points**:
- `src/reverse_engineering/feature_extraction.py` (NEW)
- `src/reverse_engineering/ml_triage.py` (NEW)
- `src/reverse_engineering/ai_enhancer.py` (EXTEND)
- `src/cli/train_models.py` (NEW)

**Testing**:
- `tests/unit/reverse_engineering/test_feature_extraction.py`
- `tests/unit/reverse_engineering/test_ml_triage.py`
- `tests/integration/test_ml_validation.py`

---

### Phase 5: Multi-Language Template Generation (Weeks 11-12)

**Goals**:
- LLM generates idiomatic templates for each target language
- Pattern library supports optimized code per language

**Main Tasks**:

#### Week 11: Template Generation
1. **Design Template Generation Prompts**
   - PostgreSQL
   - Django ORM
   - SQLAlchemy
   - Language-specific idioms

2. **Implement Template Generator**
   - LLM integration
   - Jinja2 template output
   - Syntax validation per language

3. **Extend `PatternLibrary`**
   - Auto-generate templates on pattern creation
   - Store templates in `pattern_implementations`
   - Version templates

#### Week 12: Integration & Testing
4. **CLI Support**
   - `specql patterns generate-templates <pattern_id>`
   - Batch generation for all patterns
   - Template preview

5. **Testing**
   - Unit tests for template generation
   - Validate generated code per language
   - Integration test: Pattern → Template → Code

6. **Manual Validation**
   - Generate templates for 20 patterns
   - Review Django/SQLAlchemy code quality
   - Run linters on generated code

**Success Criteria**:
- [ ] Patterns automatically have templates for all languages
- [ ] Generated code is idiomatic and passes linters
- [ ] Manual review confirms quality (90%+ approval)
- [ ] All tests passing

**Dependencies**: Phase 3 (NL pattern creation)

**Estimated Effort**: 2 weeks (1 engineer)

**Integration Points**:
- `src/pattern_library/template_generator.py` (NEW)
- `src/pattern_library/api.py` (EXTEND)
- `src/reverse_engineering/prompts/template_generation.jinja2` (NEW)

**Testing**:
- `tests/unit/pattern_library/test_template_generation.py`
- `tests/integration/test_multi_language_generation.py`

---

### Phase 6: Feedback Loops & Continuous Improvement (Weeks 13-14)

**Goals**:
- Automated retraining of ML models
- Pattern library analytics and optimization
- Performance monitoring

**Main Tasks**:

#### Week 13: Analytics & Monitoring
1. **Pattern Usage Analytics**
   - Track which patterns are used most
   - Track success/failure rates
   - Identify low-quality patterns
   - Deprecation workflow

2. **Metrics Dashboard**
   - Pattern library growth
   - Auto-accept rates over time
   - Human review time trends
   - LLM cost tracking

3. **Automated Reporting**
   - Weekly summary emails
   - Anomaly detection
   - Performance alerts

#### Week 14: Automation & Optimization
4. **Automated Model Retraining**
   - Weekly retraining pipeline
   - A/B testing framework
   - Model versioning and rollback

5. **Pattern Optimization**
   - Deduplication logic
   - Pattern merging suggestions
   - Popularity-based ranking

6. **Documentation & Handoff**
   - Operational runbook
   - Troubleshooting guide
   - Future enhancement roadmap

**Success Criteria**:
- [ ] Models retrain automatically
- [ ] Metrics dashboard shows all KPIs
- [ ] Low-quality patterns deprecated
- [ ] Documentation complete
- [ ] System runs autonomously

**Dependencies**: Phase 4 (ML models)

**Estimated Effort**: 2 weeks (1 engineer)

**Integration Points**:
- `src/pattern_library/analytics.py` (NEW)
- `src/cli/stats.py` (NEW)
- `scripts/retrain_models.py` (NEW)

**Testing**:
- `tests/unit/pattern_library/test_analytics.py`
- `tests/integration/test_retraining_pipeline.py`

---

## 8. Risk Analysis & Mitigation

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation Priority |
|------|------------|--------|---------------------|
| Pattern library becomes unmanageable | High | Medium | HIGH |
| LLM hallucinations in pattern generation | High | High | **CRITICAL** |
| Vector search returns irrelevant patterns | Medium | Medium | MEDIUM |
| ML models overfit or drift | Medium | High | HIGH |
| Local LLM performance bottleneck | Medium | Medium | MEDIUM |
| Human review fatigue | High | Medium | HIGH |
| Insufficient training data for ML | High | High | **CRITICAL** |
| Cloud costs spiral | Low | High | LOW |

### Detailed Mitigation Strategies

#### 1. Pattern Library Growth Becomes Unmanageable

**Symptoms**:
- Duplicates
- Inconsistent quality
- Hard to search
- Conflicting patterns

**Mitigation**:
- **Deduplication**: Run weekly similarity check, flag patterns >90% similar
- **Quality Gates**: Require minimum usage (N=5 instantiations) before promotion from "pending_validation"
- **Deprecation Workflow**: Auto-deprecate patterns with <5% success rate
- **Categorization**: Enforce strict category taxonomy
- **Search Optimization**: Hybrid search with keyword + embedding + category
- **Human Curation**: Monthly "pattern pruning" sessions

**Implementation**:
```python
# src/pattern_library/maintenance.py

class PatternMaintenance:
    def detect_duplicates(self, similarity_threshold=0.9):
        """Find nearly-duplicate patterns."""
        # Compare all pattern embeddings
        # Flag pairs with similarity > threshold

    def deprecate_low_quality(self, success_rate_threshold=0.05):
        """Auto-deprecate patterns with low success rate."""
        # Query pattern_quality_metrics
        # Mark patterns with success_rate < threshold as deprecated

    def promote_validated_patterns(self, min_usage=5):
        """Promote pending patterns with sufficient usage."""
        # Check times_instantiated
        # Change status from 'pending_validation' to 'validated'
```

#### 2. LLM Hallucinations in Pattern Generation ⚠️ **CRITICAL**

**Symptoms**:
- Invalid SpecQL syntax
- Patterns don't follow conventions
- Parameters don't match implementation
- Generated code breaks

**Mitigation**:
- **Strict Validation**: Multi-layer validation before acceptance
  1. JSON schema validation
  2. SpecQL syntax parser
  3. Convention checker (Trinity pattern, naming)
  4. Dry-run instantiation test
- **Human Approval Required**: ALL LLM-generated patterns require human review
- **Few-Shot Prompting**: Include 3-5 exemplar patterns in prompts
- **Iterative Refinement**: If validation fails, send errors back to LLM for correction (max 3 iterations)
- **Confidence Threshold**: Only present suggestions with confidence >0.7

**Implementation**:
```python
# Validation pipeline
def validate_generated_pattern(pattern: Dict) -> Dict:
    errors = []

    # Layer 1: JSON schema
    if not jsonschema_validate(pattern):
        errors.append("Invalid JSON schema")

    # Layer 2: SpecQL syntax
    try:
        parse_specql(pattern['implementation'])
    except SyntaxError as e:
        errors.append(f"SpecQL syntax error: {e}")

    # Layer 3: Conventions
    if not check_naming_conventions(pattern):
        errors.append("Naming conventions violated")

    # Layer 4: Dry-run
    try:
        instantiate_pattern(pattern, entity="TestEntity")
    except Exception as e:
        errors.append(f"Instantiation failed: {e}")

    return {'valid': len(errors) == 0, 'errors': errors}
```

#### 3. ML Models Overfit or Drift

**Mitigation**:
- **Holdout Evaluation**: 20% of data never used for training
- **Cross-Validation**: K-fold CV during training
- **Drift Detection**: Monitor feature distributions weekly
- **A/B Testing**: New model runs in shadow mode for 1 week before deployment
- **Automatic Rollback**: If accuracy drops >5%, revert to previous model
- **Retraining Schedule**: Weekly retraining with fresh data

#### 4. Insufficient Training Data for ML ⚠️ **CRITICAL**

**Symptoms**:
- Models don't converge
- High variance
- Poor generalization

**Mitigation**:
- **Bootstrap Phase**: Manually label 200-300 functions before Phase 4
- **Synthetic Data**: Generate synthetic training examples using LLM
- **Active Learning**: Prioritize labeling of high-uncertainty examples
- **Transfer Learning**: Start with pre-trained CodeBERT features
- **Delay Phase 4**: If <200 labeled examples, postpone ML models to Phase 6+

**Contingency Plan**:
```python
# Check if sufficient data before training
def check_training_data_sufficiency():
    query = "SELECT COUNT(*) FROM reverse_engineering_results WHERE reviewed = TRUE"
    count = db.execute(query).fetchone()[0]

    if count < 200:
        print(f"WARNING: Only {count} labeled examples. Need 200+ for robust training.")
        print("Options:")
        print("1. Delay ML training until more data collected")
        print("2. Use rule-based heuristics for now")
        print("3. Generate synthetic training data")
        return False
    return True
```

#### 5. Human Review Fatigue

**Mitigation**:
- **Prioritization**: High-risk functions (payment, tax, refund) → mandatory review; low-risk → auto-accept
- **Batch Review**: Group similar patterns for efficient review
- **Review Quotas**: Limit to 10-15 reviews per day per person
- **Gamification**: Track review metrics, celebrate high-quality feedback
- **Automated Summaries**: LLM generates "what changed" summary for quick scanning
- **Smart Scheduling**: Notify reviewers only when backlog >10

---

## 9. Technology Stack

### Core Technologies

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Language** | Python | 3.11+ | Existing SpecQL stack |
| **Package Manager** | uv | Latest | Fast, existing choice |
| **CLI Framework** | click | 8.x | Existing CLI framework |
| **Database** | SQLite | 3.x | Existing pattern library DB |
| **SQL Parsing** | pglast | Latest | Existing reverse eng parser |
| **Templating** | Jinja2 | 3.x | Existing for code generation |
| **Testing** | pytest | 7.x | Existing test framework |

### New Dependencies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Embeddings** | sentence-transformers | 2.x | Pattern embeddings |
| **Embedding Model** | all-MiniLM-L6-v2 | Latest | 384-dim embeddings |
| **ML Framework** | TensorFlow/Keras | 2.15+ | ML models |
| **ML Utilities** | scikit-learn | 1.3+ | Feature engineering, baselines |
| **Rich Output** | rich | 13.x | CLI formatting |
| **LLM (existing)** | llama-cpp-python | Latest | Local LLM (already used) |
| **LLM (cloud)** | anthropic | Latest | Cloud fallback (already used) |

### Optional Dependencies

| Component | Technology | Purpose | Phase |
|-----------|------------|---------|-------|
| **Vector DB** | ChromaDB | Large-scale retrieval | Phase 6+ |
| **Monitoring** | Prometheus | Metrics collection | Phase 6 |
| **Dashboards** | Grafana | Visualization | Phase 6 |
| **Experiment Tracking** | MLflow | ML experiment tracking | Phase 4 (optional) |

### Hardware Requirements

**Minimum** (for development):
- CPU: 4+ cores
- RAM: 16 GB
- GPU: RTX 3060 (12 GB VRAM)

**Recommended** (for production):
- CPU: 8+ cores
- RAM: 32 GB
- GPU: RTX 4090 (24 GB VRAM) ✅ **Already available**

**Future** (for larger models):
- GPU: A6000 (48 GB VRAM)

---

## 10. Success Metrics & Evaluation

### Phase-Specific Metrics

| Phase | Metric | Baseline | Target | Measurement |
|-------|--------|----------|--------|-------------|
| **Phase 1** | Pattern retrieval relevance | N/A | 80% Top-5 | Manual review |
| **Phase 1** | Confidence improvement | 95% | 97% | A/B test |
| **Phase 2** | Pattern discovery rate | 0% | 5-10% | Automatic logging |
| **Phase 2** | Suggestion approval rate | N/A | 60% | Review tracking |
| **Phase 3** | NL pattern validity | N/A | 80% | Validation pass rate |
| **Phase 4** | Auto-accept rate | 0% | 70% | ML triage decisions |
| **Phase 4** | False positive rate | N/A | <5% | Manual audit |
| **Phase 5** | Template quality | N/A | 90% approval | Manual review |
| **Phase 6** | Model accuracy | N/A | >85% | Holdout set |

### End-to-End Metrics

| Metric | Baseline (Pre-Implementation) | Target (Post-Implementation) |
|--------|-------------------------------|------------------------------|
| **Pattern Library Size** | 30 patterns | 200+ patterns |
| **Reverse Eng. Confidence** | 95% | 98% |
| **Auto-Accept Rate** | 0% | 70% |
| **Human Review Time** | 5 min/function | 2 min/function |
| **Cloud LLM Cost** | $0.50/function | $0.10/function |
| **Pattern Reuse Rate** | 20% | 60% |
| **Time to Production** | 2 hours (manual) | 30 min (automated) |

### Evaluation Methods

**Quantitative**:
- A/B testing (with/without enhancements)
- Accuracy metrics (precision, recall, F1)
- Performance metrics (latency, throughput)
- Cost tracking (LLM API calls)

**Qualitative**:
- Manual code review (sample 20 functions/week)
- User satisfaction surveys
- Pattern quality assessment
- Developer interviews

---

## 11. Future Extensions & Vision

### Extension 1: Community Pattern Marketplace (Year 2)

**Vision**: Public pattern library for sharing domain-specific patterns

**Features**:
- GitHub-based pattern repository
- Rating and review system
- Pattern discovery and recommendations
- Automated quality checks
- Pattern attribution and licensing
- Namespace isolation per organization

**Example**:
```bash
# Browse community patterns
specql patterns browse --category ecommerce

# Install community pattern
specql patterns install ecommerce/order_fulfillment_workflow

# Publish your pattern
specql patterns publish my_pattern --namespace myorg
```

### Extension 2: Interactive Pattern Builder UI (Year 2)

**Vision**: Web-based UI for visual pattern creation

**Features**:
- Drag-and-drop field editor
- Visual workflow designer for actions
- Live code preview (SpecQL → SQL/Django/etc.)
- Collaborative editing
- Pattern testing sandbox
- Template gallery

### Extension 3: Cross-Language Pattern Migration (Year 2)

**Vision**: Automatically migrate patterns between languages

**Example**:
```bash
# I have a Django pattern, generate SQLAlchemy equivalent
specql patterns migrate django/user_approval --to sqlalchemy

# Bulk migration
specql patterns migrate --from django --to rails --all
```

### Extension 4: Advanced ML Models (Year 2-3)

**Transformer-Based Models**:
- Fine-tune CodeBERT for pattern detection
- Seq2seq models for SQL → SpecQL translation
- Graph neural networks for AST-based reasoning

**Benefits**:
- Higher accuracy (98% → 99.5%)
- Better variable naming
- Semantic understanding of business logic

### Extension 5: CI/CD Integration (Year 2)

**Vision**: Integrate into development workflows

**Features**:
- Reverse engineer SQL changes in PRs automatically
- Pattern compliance checking
- Auto-generate migration scripts
- Detect breaking changes

**Example GitHub Action**:
```yaml
name: SpecQL Pattern Check
on: pull_request

jobs:
  pattern-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: specql/pattern-check-action@v1
        with:
          enforce-patterns: true
          auto-suggest: true
```

### Extension 6: Multi-Tenant Pattern Libraries (Year 3)

**Vision**: Per-organization pattern libraries with sharing

**Features**:
- Private organization patterns
- Selective sharing across teams
- Pattern inheritance and overrides
- Usage analytics per team
- Cost allocation

---

## Appendices

### Appendix A: Example Prompts

See `src/reverse_engineering/prompts/` directory:
- `pattern_discovery.jinja2`
- `nl_pattern_generation.jinja2`
- `enhance_with_patterns.jinja2`
- `template_generation.jinja2`

### Appendix B: Sample Pattern Definitions

#### Example 1: Three-Stage Approval Workflow

```json
{
  "pattern_name": "three_stage_approval",
  "category": "workflow",
  "description": "Three-stage approval workflow (pending → reviewed → approved) with email notifications",
  "parameters": {
    "entity": {
      "type": "string",
      "required": true,
      "description": "Target entity name"
    },
    "stages": {
      "type": "array",
      "required": false,
      "default": ["pending", "reviewed", "approved"],
      "description": "Approval stages"
    },
    "approver_role": {
      "type": "string",
      "required": false,
      "default": "manager",
      "description": "Role required for approval"
    }
  },
  "implementation": {
    "fields": [
      {"name": "status", "type": "enum({{stages}})", "description": "Current approval status"},
      {"name": "current_stage", "type": "integer", "default": 0, "description": "Current stage index"},
      {"name": "approved_by", "type": "ref(User)", "description": "User who approved"},
      {"name": "approved_at", "type": "timestamp", "description": "Approval timestamp"},
      {"name": "rejection_reason", "type": "text", "description": "Reason if rejected"}
    ],
    "actions": [
      {
        "name": "submit_for_approval",
        "description": "Submit entity for approval",
        "steps": [
          {"validate": "status = 'draft'"},
          {"update": "{{entity}} SET status = 'pending', current_stage = 0"},
          {"notify": "approvers", "template": "approval_requested"}
        ]
      },
      {
        "name": "advance_approval_stage",
        "description": "Advance to next stage",
        "steps": [
          {"validate": "status = stages[current_stage]"},
          {"validate": "current_user_has_role('{{approver_role}}')"},
          {"update": "{{entity}} SET current_stage = current_stage + 1, status = stages[current_stage + 1], approved_by = current_user_id, approved_at = now()"},
          {"notify": "submitter", "template": "approval_stage_advanced"}
        ]
      },
      {
        "name": "reject",
        "description": "Reject entity",
        "steps": [
          {"validate": "status != 'approved'"},
          {"validate": "current_user_has_role('{{approver_role}}')"},
          {"update": "{{entity}} SET status = 'rejected', rejection_reason = :reason"},
          {"notify": "submitter", "template": "approval_rejected"}
        ]
      }
    ]
  },
  "multi_tenant": true,
  "examples": [
    {
      "entity": "Invoice",
      "description": "Invoice approval workflow",
      "instantiated_fields": ["status", "current_stage", "approved_by", "approved_at"],
      "instantiated_actions": ["submit_for_approval", "advance_approval_stage", "reject"]
    }
  ]
}
```

### Appendix C: Schema Migration Scripts

See `docs/schema_migrations/` directory:
- `001_pattern_embeddings.sql`
- `002_pattern_suggestions.sql`
- `003_pattern_versions.sql`
- `004_pattern_quality_metrics.sql`
- `005_reverse_engineering_results.sql`
- `006_ml_models.sql`
- `007_llm_calls.sql`

### Appendix D: Performance Benchmarks

**Embedding Generation** (all-MiniLM-L6-v2):
- Pattern embedding: ~10ms
- Function embedding: ~15ms
- Batch (100 patterns): ~1.2s

**Similarity Search** (SQLite, 1000 patterns):
- Pure cosine: ~50ms
- Hybrid search: ~120ms
- With re-ranking (LLM): ~2.5s

**ML Inference** (TensorFlow):
- Pattern validation: ~5ms
- Needs-review: ~5ms
- Confidence calibration: ~3ms

**LLM Calls**:
- Local (Llama 8B Q4): 2-5s (depends on prompt length)
- Cloud (Claude Haiku): 0.5-2s

---

## Conclusion

This implementation plan provides a comprehensive roadmap for enhancing SpecQL's pattern library with advanced LLM capabilities. The phased approach ensures:

1. **Incremental Value**: Each phase delivers tangible benefits
2. **Risk Mitigation**: Critical risks identified and addressed
3. **Practical Execution**: Concrete tasks, clear success criteria
4. **Sustainable Growth**: Feedback loops for continuous improvement

**Key Success Factors**:
- Leverage existing infrastructure (reverse eng, pattern library, AI enhancer)
- Follow SpecQL conventions (Trinity, naming, protocols)
- Maintain test coverage throughout
- Prioritize human-in-the-loop workflows
- Focus on local LLM performance
- Build robust validation layers

**Timeline**: 14-16 weeks (3.5-4 months) for full implementation

**Next Steps**:
1. Review and approve this plan
2. Set up project tracking (GitHub issues/JIRA)
3. Begin Phase 0: Foundation & Planning
4. Start weekly progress reviews

---

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Status**: Ready for Review
