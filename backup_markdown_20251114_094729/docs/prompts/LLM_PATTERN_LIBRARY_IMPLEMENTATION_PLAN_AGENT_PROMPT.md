# Implementation Plan Agent Prompt: LLM-Enhanced Pattern Library System

## Role & Mission

You are a senior ML/Software architect and technical project lead familiar with the SpecQL codebase.

Your task is to produce a **concrete, phased implementation plan** for enhancing SpecQL's existing reverse engineering and pattern library infrastructure with advanced LLM capabilities.

**Goal**: Minimize dependence on cloud LLMs while maximizing pattern library utility through:
1. Intelligent pattern discovery and matching during SQL→SpecQL reverse engineering
2. Natural language pattern generation for the pattern library
3. Incremental pattern library enrichment from legacy code analysis
4. Multi-language code optimization using domain patterns

---

## Context: What Already Exists in SpecQL

### ✅ Phase D: Working Reverse Engineering Pipeline

SpecQL **already has** a complete SQL→SpecQL reverse engineering system (`src/reverse_engineering/`):

**Components**:
- **Algorithmic Parser** (`algorithmic_parser.py`, `sql_ast_parser.py`, `ast_to_specql_mapper.py`)
  - Uses `pglast` library for SQL AST parsing
  - Converts PL/pgSQL → SpecQL primitives (85% confidence)
  - Handles: DECLARE, IF/THEN/ELSE, CTEs, RETURN, loops, complex expressions

- **Heuristic Enhancer** (`heuristic_enhancer.py`)
  - Pattern detection: state_machine, audit_trail, soft_delete, validation_chain
  - Variable purpose inference: total, count, flag, temp, accumulator
  - Raises confidence to 90%

- **AI Enhancer** (`ai_enhancer.py`)
  - **Local LLM**: Llama 3.1 8B via `llama-cpp-python`
    - Model path: `~/.specql/models/llama-3.1-8b.gguf`
    - GPU acceleration support
    - Context: 4096 tokens
  - **Cloud Fallback**: Anthropic Claude (Haiku)
  - Tasks: Intent inference, variable naming, pattern suggestions, business logic extraction
  - Raises confidence to 95%

- **CLI Interface** (`src/cli/reverse.py`)
  - Command: `specql reverse <sql_file> [--batch] [--use-cloud]`
  - Batch processing support
  - Optional cloud escalation

**Test Coverage**:
- Unit tests: `tests/unit/reverse_engineering/`
- Integration: `tests/integration/test_e2e_legacy_migration.py`
- All passing ✅

### ✅ Pattern Library Infrastructure (3-Tier Architecture)

**Database Schema** (`src/pattern_library/schema.sql`):

**TIER 1: Universal Primitives**
- `patterns` - Universal code patterns (declare, if, query, insert, update, etc.)
- `languages` - Target languages (PostgreSQL, Python, TypeScript, Django, SQLAlchemy, Ruby)
- `pattern_implementations` - Language-specific Jinja2 templates
- `universal_types` - SpecQL type system
- `type_mappings` - Cross-language type translations
- `expression_patterns` - Operators and functions per language
- `language_capabilities` - Feature support matrix

**TIER 2: Domain Patterns**
- `domain_patterns` - Reusable business logic patterns
  - Categories: state_machine, workflow, hierarchy, audit, validation, soft_delete, approval, notification
  - JSON parameters and implementation
  - Popularity scoring (`times_instantiated`)
  - Usage tracking and metrics

**TIER 3: Entity Templates**
- `entity_templates` - Complete entity blueprints
  - Namespaces: crm, ecommerce, healthcare, finance, etc.
  - Default fields, patterns, actions
  - Configuration options
- `pattern_instantiations` - Track usage per entity
- `entity_template_dependencies` - Template relationships

**Python API** (`src/pattern_library/api.py`):
```python
class PatternLibrary:
    # Pattern management
    add_pattern(name, category, abstract_syntax, description)
    compile_pattern(pattern_name, language_name, context) -> str

    # Domain patterns (Tier 2)
    add_domain_pattern(name, category, description, parameters, implementation)
    instantiate_domain_pattern(pattern_name, entity_name, parameters)
    compose_patterns(entity_name, patterns) -> Dict
    validate_pattern_composition(patterns) -> Dict

    # Entity templates (Tier 3)
    add_entity_template(template_name, namespace, default_fields, default_patterns)
    instantiate_entity_template(template_name, entity_name, custom_fields)

    # Retrieval and search
    get_pattern(name) -> Dict
    search_patterns(category=None, language=None) -> List[Dict]
```

**Existing Seed Data**:
- `seed_domain_patterns.py` - Pre-built domain patterns
- `seed_entity_templates.py` - Pre-built entity templates
- `postgresql_patterns.py` - PostgreSQL-specific patterns
- `django_patterns.py`, `sqlalchemy_patterns.py` - ORM patterns

**Test Coverage**:
- 63+ tests in `tests/unit/pattern_library/`
- Pattern composition, validation, multi-language compilation
- All passing ✅

### ✅ Generation Pipeline Architecture

**Schema Generators** (`src/generators/schema/`):
- `schema_orchestrator.py` - Orchestrates all schema generation
- `table_generator.py` - DDL with Trinity pattern (pk_*, id, identifier)
- `hierarchical_file_writer.py` - Protocol-based file writing
- `write_side_path_generator.py`, `read_side_path_generator.py` - Path generation

**Action Generators** (`src/generators/actions/`):
- `action_orchestrator.py` - Action compilation orchestration
- `core_logic_generator.py` - Business logic PL/pgSQL functions
- `step_compilers/` - Individual step compilers

**CLI Orchestrator** (`src/cli/orchestrator.py`):
- `CLIOrchestrator.generate_from_files()` - Main entry point
- Registry integration for hierarchical numbering
- Hooks for pre/post-generation

**FileSpec Protocol**:
```python
@dataclass
class FileSpec:
    code: str      # 6-digit hierarchical code (SSDSEX)
    name: str      # Filename without extension
    content: str   # Complete file content
    layer: str     # "write_side" or "read_side"
```

### ✅ Domain Registry System

**Registry** (`registry/domain_registry.yaml`):
- Hierarchical 6-digit numbering: SSDSEX
  - SS = Schema layer (01=write, 02=read, 03=functions) - 2 digits
  - D = Domain (1-9) - 1 digit
  - S = Subdomain (0-9) - 1 digit
  - E = Entity sequence (0-9) - 1 digit
  - X = File sequence (0-9) - 1 digit
- Domain definitions: CRM, Sales, Finance, HR, etc.
- Multi-tenant vs shared schema classification

**API** (`src/registry/domain_registry.py`):
- `get_code(domain, subdomain, entity)` - Get hierarchical code
- `get_domain_info(domain_name)` - Domain metadata

### ✅ SpecQL Conventions (Non-Negotiable)

**Trinity Pattern** (ALWAYS applied):
- `pk_{entity}` - INTEGER PRIMARY KEY
- `id` - UUID UNIQUE NOT NULL
- `identifier` - TEXT UNIQUE NOT NULL

**Naming Conventions**:
- Tables: `tb_{entity}`
- Views: `tv_{entity}`, `v_{entity}`, `mv_{entity}`
- Functions: `fn_{schema}_{action}`
- Foreign keys: `fk_{entity}`
- Indexes: `idx_tb_{entity}_{field}` (tables), `idx_tv_{entity}_{field}` (views)

**Audit Fields** (ALWAYS added):
- `created_at TIMESTAMPTZ DEFAULT now()`
- `updated_at TIMESTAMPTZ DEFAULT now()`
- `deleted_at TIMESTAMPTZ` (soft delete support)

**Schema Organization** (3 tiers):
1. **Framework Schemas**: common, app, core
2. **Multi-Tenant**: crm, projects (auto-add `tenant_id UUID NOT NULL`)
3. **Shared**: catalog, analytics (no tenant_id)

---

## Key Strategic Gaps to Address

### 🎯 GAP 1: Pattern Discovery & Enrichment from Legacy Code

**Current State**:
- Heuristic enhancer detects basic patterns (state_machine, audit_trail)
- Pattern detection is regex/heuristic-based
- No systematic pattern library enrichment from reverse engineering

**Opportunity**:
- Use LLM to identify **novel/complex** patterns in legacy SQL
- Automatically suggest new domain patterns for pattern library
- Learn from "interesting" functions (low confidence, frequent corrections, complex logic)

**Example Workflow**:
```
Legacy SQL → Algorithmic Parser → Heuristic Enhancer → AI Enhancer
                                                            ↓
                                      ❓ "Is this a new pattern?"
                                                            ↓
                                      🧠 LLM Analysis: "This is a
                                         three-stage approval workflow
                                         with email notifications"
                                                            ↓
                                      ✅ Suggest new domain_pattern entry
                                                            ↓
                                      👤 Human review & approve
                                                            ↓
                                      💾 Add to pattern library
                                                            ↓
                                      🔄 Reuse in future conversions
```

### 🎯 GAP 2: Natural Language Pattern Generation

**Current State**:
- Domain patterns manually created via `PatternLibrary.add_domain_pattern()`
- Entity templates manually seeded
- No natural language interface

**Opportunity**:
- Users describe patterns in natural language
- LLM generates structured pattern definitions
- Automatic Jinja2 template generation for multi-language support

**Example Use Case**:
```
User: "Create a pattern for a three-stage approval workflow with email notifications"

LLM generates:
{
    "pattern_name": "three_stage_approval_with_notification",
    "category": "workflow",
    "description": "Three-stage approval (pending → reviewed → approved) with email notifications",
    "parameters": {
        "entity": {"type": "string", "required": true},
        "stages": {"type": "array", "default": ["pending", "reviewed", "approved"]},
        "notify_on": {"type": "array", "default": ["stage_change", "final_approval"]}
    },
    "implementation": {
        "fields": [
            {"name": "status", "type": "enum", "values": "{{stages}}"},
            {"name": "current_stage", "type": "integer", "default": 0},
            {"name": "approved_by", "type": "ref(User)"},
            {"name": "approved_at", "type": "timestamp"},
            {"name": "rejection_reason", "type": "text"}
        ],
        "actions": [
            {
                "name": "advance_approval_stage",
                "steps": [
                    {"validate": "status = stages[current_stage]"},
                    {"update": "{{entity}} SET current_stage = current_stage + 1, status = stages[current_stage + 1]"},
                    {"notify": "approvers", "template": "approval_stage_changed"}
                ]
            },
            {
                "name": "reject",
                "steps": [
                    {"update": "{{entity}} SET status = 'rejected', rejection_reason = :reason"},
                    {"notify": "submitter", "template": "approval_rejected"}
                ]
            }
        ]
    },
    "jinja2_templates": {
        "postgresql": "...",
        "django": "...",
        "sqlalchemy": "..."
    }
}

System validates, adds to pattern library, makes available for reuse.
```

### 🎯 GAP 3: Intelligent Pattern Matching with RAG

**Current State**:
- No pattern retrieval during reverse engineering
- AI enhancer doesn't consult pattern library
- Pattern suggestions are generic

**Opportunity**:
- Retrieve relevant patterns from library during reverse engineering
- Use embedding-based similarity search (vector DB)
- Feed patterns to LLM as context for better analysis

**Enhanced AI Enhancer Flow**:
```
SQL Function → Embeddings → Top-K Pattern Retrieval → LLM Context
                                                            ↓
                                        "Given these existing patterns:
                                         1. state_machine (80% match)
                                         2. audit_trail (65% match)
                                         3. soft_delete (45% match)

                                         Analyze this function..."
                                                            ↓
                                        Enhanced pattern detection,
                                        better variable naming,
                                        pattern-aware refactoring
```

### 🎯 GAP 4: Multi-Language Optimization

**Current State**:
- Pattern implementations use Jinja2 templates
- Templates are manually written
- No idiomatic optimization per language

**Opportunity**:
- LLM-optimized code generation per target language
- Idiomatic patterns (e.g., Django ORM best practices vs SQLAlchemy vs raw SQL)
- Performance optimization suggestions

**Example**:
```
PostgreSQL pattern:
CREATE INDEX idx_user_email ON users(lower(email));

Django (LLM-optimized):
class User(models.Model):
    email = models.EmailField(db_index=True)

    class Meta:
        indexes = [
            models.Index(Lower('email'), name='idx_user_email_lower')
        ]

    # Idiomatic: Override save() for case-insensitive email uniqueness
    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)
```

### 🎯 GAP 5: QA & Confidence Boosting

**Current State**:
- Confidence scores are heuristic (85% → 90% → 95%)
- No ML-based validation
- No "needs human review" classifier

**Opportunity**:
- Train lightweight TensorFlow models on historical data:
  - **Pattern validation classifier**: Does detected pattern actually apply?
  - **Needs review classifier**: Should human review this conversion?
  - **Confidence calibration**: Adjust confidence scores based on historical accuracy
  - **Naming quality scorer**: Rate variable name quality

**Example ML Pipeline**:
```
Function Analysis → Feature Extraction → TF Model → Confidence Boost
                                                            ↓
                                        High confidence (>95%) → Auto-accept
                                        Medium (80-95%) → Flag for spot check
                                        Low (<80%) → Mandatory human review
```

---

## Your Implementation Plan Requirements

Produce a **detailed, phased implementation plan** that addresses the gaps above while **leveraging existing SpecQL infrastructure**.

### 1. High-Level Architecture

Design a system architecture that:
- **Integrates with existing components**: `ai_enhancer.py`, `PatternLibrary API`, `CLIOrchestrator`
- **Adds new capabilities**: Pattern discovery, NL pattern generation, RAG-based matching, ML validation
- **Maintains conventions**: Trinity pattern, hierarchical numbering, protocol-based design

**Show**:
- Component diagram with existing + new components
- Data flow for:
  - **Reverse Engineering with Pattern Enrichment**: SQL → Parser → Pattern Retrieval → LLM → Pattern Suggestion → Human Review → Library Update
  - **Natural Language Pattern Creation**: User description → LLM → Pattern generation → Validation → Library insertion
  - **Pattern-Aware Code Generation**: SpecQL → Pattern matching → Multi-language compilation

### 2. Enhanced Pattern Library Schema

**Extend existing schema** (`src/pattern_library/schema.sql`) to support:

**Pattern Metadata for ML**:
- Pattern embeddings for similarity search
- Pattern complexity scoring
- Pattern co-occurrence tracking (which patterns are often used together?)
- Pattern source tracking (manually created, LLM-generated, extracted from legacy code)

**Pattern Evolution Tracking**:
- Pattern versions
- Pattern deprecation/replacement
- Pattern refinement history

**Pattern Quality Metrics**:
- Usage frequency (`times_instantiated` already exists)
- Success rate (how often is pattern accepted without modification?)
- Review flags (patterns that frequently need human correction)

**Suggest concrete SQL schema additions** (new tables/columns).

### 3. Local LLM Integration Strategy

**Enhance existing `ai_enhancer.py`** to support:

**New LLM Tasks**:
1. **Pattern Discovery**: "Is this SQL function implementing a novel pattern?"
2. **Pattern Generation**: "Generate a domain pattern from this description"
3. **Pattern Validation**: "Does this function match the state_machine pattern?"
4. **Template Generation**: "Generate Jinja2 templates for this pattern in PostgreSQL, Django, SQLAlchemy"

**Prompt Engineering**:
- Design structured prompts for each task
- Include few-shot examples
- Enforce JSON/YAML output format
- Provide retrieved patterns as context (RAG)

**Model Considerations**:
- Llama 3.1 8B (current) vs larger models (13B, 70B)
- Quantization strategies (4-bit, 8-bit)
- GPU memory requirements
- Batching strategies for multiple functions

**Cloud Escalation Policy**:
- When to use cloud LLM (Claude Sonnet/Opus) vs local
- Cost optimization strategies

### 4. Pattern Retrieval & RAG System

Design a **retrieval-augmented generation (RAG)** system for pattern matching:

**Embedding Strategy**:
- What to embed: Pattern descriptions? SpecQL snippets? SQL implementations? All of the above?
- Embedding model: sentence-transformers (e.g., `all-MiniLM-L6-v2`), OpenAI embeddings, or custom?
- Where to store embeddings: Add to SQLite schema? Separate vector DB (ChromaDB, Qdrant, FAISS)?

**Retrieval Logic**:
- Top-K retrieval (K=5? K=10?)
- Hybrid search: Embedding similarity + keyword matching + category filtering
- Re-ranking strategies

**Integration Points**:
- When to retrieve patterns: During algorithmic parsing? Heuristic enhancement? AI enhancement?
- How to feed patterns to LLM: Full pattern JSON? Summarized descriptions? Just names?

**Example Workflow**:
```python
# In ai_enhancer.py
def enhance_with_patterns(self, specql_ast, sql_function):
    # 1. Generate embeddings for SQL function
    function_embedding = self.embed_function(sql_function)

    # 2. Retrieve top-K relevant patterns
    relevant_patterns = self.pattern_library.retrieve_similar_patterns(
        embedding=function_embedding,
        top_k=5,
        category_filter=["workflow", "validation", "state_machine"]
    )

    # 3. Build prompt with patterns as context
    prompt = self.build_prompt_with_patterns(specql_ast, relevant_patterns)

    # 4. LLM analysis
    response = self.local_llm(prompt)

    # 5. Parse response and apply patterns
    return self.apply_pattern_enhancements(specql_ast, response)
```

### 5. Pattern Discovery & Enrichment Pipeline

Design a **feedback loop** for continuous pattern library improvement:

**Trigger Criteria** (when to suggest new pattern):
- Low confidence score after AI enhancement (<80%)
- Function complexity metrics (cyclomatic complexity, LOC, nesting depth)
- Frequent human corrections to this function type
- Keyword presence (tax, refund, credit, payout, approval, reconciliation)
- No existing pattern matches above threshold (e.g., <50% similarity)

**Pattern Extraction Process**:
1. **Automatic Analysis**: LLM analyzes "interesting" function
   - Extract business intent
   - Identify reusable structure
   - Suggest pattern category
   - Generate pattern parameters
   - Propose implementation template

2. **Human Review Workflow**:
   - Review UI/CLI showing:
     - Original SQL
     - Generated SpecQL
     - Suggested pattern definition
     - Similar existing patterns (if any)
   - Actions: Accept, Modify, Reject, Merge with existing

3. **Pattern Insertion**:
   - Add to `domain_patterns` table
   - Generate embeddings
   - Create multi-language templates (via LLM)
   - Mark as "pending_validation" until N successful uses

4. **Pattern Validation**:
   - Track usage and success rate
   - Promote to "validated" after threshold met
   - Deprecate if low success rate

**Integration with Reverse Engineering CLI**:
```bash
# Normal reverse engineering
specql reverse legacy_function.sql

# With pattern discovery enabled
specql reverse legacy_function.sql --discover-patterns

# Review suggested patterns
specql patterns review-suggestions

# Approve/reject pattern
specql patterns approve <pattern_id>
specql patterns reject <pattern_id> --reason "Too specific"
```

### 6. Natural Language Pattern Generation

Design a **user-facing interface** for creating patterns from descriptions:

**CLI Command**:
```bash
specql patterns create-from-description \
  --description "Three-stage approval workflow with email notifications" \
  --category workflow \
  --namespace crm \
  --review
```

**LLM Prompt Structure**:
```
System: You are a SpecQL pattern architect. Generate a domain pattern from user descriptions.

Output JSON schema:
{
  "pattern_name": "snake_case_name",
  "category": "workflow|validation|audit|...",
  "description": "Clear description",
  "parameters": {
    "param_name": {
      "type": "string|array|integer|...",
      "required": true|false,
      "default": value,
      "description": "..."
    }
  },
  "implementation": {
    "fields": [...],
    "actions": [...]
  }
}

User description: {{user_input}}

Constraints:
- Follow SpecQL conventions (Trinity pattern, naming)
- Make patterns reusable with parameters
- Include comprehensive validation steps
- Consider multi-tenant scenarios if applicable
```

**Validation Steps**:
1. LLM generates pattern JSON
2. Validate JSON schema
3. Check for pattern name conflicts
4. Validate SpecQL syntax in implementation
5. Generate preview of instantiated pattern
6. User review and approval
7. Generate multi-language templates (via LLM or manual)
8. Insert into pattern library

**Integration with Pattern Library API**:
```python
# New method in PatternLibrary class
def create_pattern_from_nl(
    self,
    description: str,
    category: str,
    namespace: Optional[str] = None,
    llm_service: Optional[LLMService] = None
) -> Dict:
    """
    Generate domain pattern from natural language description.

    Returns:
        {
            "pattern": {...},  # Generated pattern definition
            "preview": "...",  # Preview of instantiated pattern
            "validation": {...}  # Validation results
        }
    """
```

### 7. ML-Based QA & Triage System

Design **lightweight TensorFlow models** for quality assurance:

**Model 1: Pattern Validation Classifier**
- **Input**: Function features (complexity, keywords, structure) + Detected pattern
- **Output**: Probability that pattern correctly applies (0-1)
- **Training Data**: Historical reverse engineering results (accepted vs corrected patterns)
- **Features**:
  - Function LOC, cyclomatic complexity, nesting depth
  - Keyword presence (TF-IDF vectors)
  - SpecQL primitive counts (IF, VALIDATE, UPDATE, etc.)
  - Pattern-specific features (state field presence, audit field presence, etc.)

**Model 2: Needs-Review Classifier**
- **Input**: Function features + AI enhancer output
- **Output**: Probability function needs human review (0-1)
- **Threshold**: >0.7 = mandatory review, 0.3-0.7 = spot check, <0.3 = auto-accept
- **Training Data**: Functions flagged by humans during review

**Model 3: Confidence Calibration Regressor**
- **Input**: Function features + AI enhancer confidence score
- **Output**: Calibrated confidence score
- **Purpose**: Adjust heuristic confidence scores based on historical accuracy

**Model 4: Naming Quality Scorer**
- **Input**: Variable name + Variable purpose + Context
- **Output**: Quality score (0-1)
- **Purpose**: Validate LLM-suggested variable names

**Training Data Collection**:
- Log all reverse engineering results
- Track human corrections and feedback
- Store accepted vs rejected patterns
- Track time spent reviewing (proxy for complexity)

**Model Serving**:
```python
# New module: src/reverse_engineering/ml_triage.py

class MLTriageService:
    def __init__(self, model_dir: Path):
        self.pattern_validator = load_model(model_dir / "pattern_validator.keras")
        self.needs_review_clf = load_model(model_dir / "needs_review.keras")
        self.confidence_calibrator = load_model(model_dir / "confidence_calibrator.keras")

    def validate_pattern(self, function_features, detected_pattern) -> float:
        """Returns probability pattern is correct (0-1)"""

    def should_review(self, function_features, ai_output) -> Tuple[bool, float]:
        """Returns (needs_review, confidence)"""

    def calibrate_confidence(self, function_features, raw_confidence) -> float:
        """Returns calibrated confidence score"""
```

**Integration with Reverse Engineering Pipeline**:
```python
# Enhanced ai_enhancer.py
def enhance_function(self, specql_ast, sql_function):
    # Existing enhancement
    enhanced = self.perform_ai_enhancement(specql_ast)

    # NEW: ML-based QA
    if self.ml_triage:
        features = extract_features(sql_function)

        # Validate detected patterns
        for pattern in enhanced.detected_patterns:
            valid_prob = self.ml_triage.validate_pattern(features, pattern)
            if valid_prob < 0.5:
                enhanced.warnings.append(f"Low confidence in {pattern} (p={valid_prob:.2f})")

        # Adjust confidence
        enhanced.confidence = self.ml_triage.calibrate_confidence(
            features, enhanced.confidence
        )

        # Triage decision
        needs_review, review_conf = self.ml_triage.should_review(features, enhanced)
        enhanced.needs_review = needs_review
        enhanced.review_confidence = review_conf

    return enhanced
```

### 8. Human Review Workflow

Design a **review interface** for:
1. Approving/rejecting reverse engineering results
2. Creating new patterns from suggestions
3. Validating LLM-generated patterns

**CLI Commands**:
```bash
# Review pending reverse engineering results
specql review list --status pending
specql review show <function_id>
specql review approve <function_id>
specql review reject <function_id> --feedback "Variable names unclear"

# Review pattern suggestions
specql patterns review-suggestions
specql patterns approve <pattern_id>
specql patterns reject <pattern_id> --reason "Too specific"
specql patterns edit <pattern_id>  # Opens editor

# Review metrics dashboard
specql review stats
# Output:
# - Pending reviews: 23
# - Auto-accepted (high confidence): 156
# - Flagged for review: 12
# - Average time per review: 3.2 min
```

**Web UI (Optional Future Enhancement)**:
- Side-by-side comparison: SQL ↔ SpecQL
- Pattern matching visualization
- Inline editing of SpecQL
- Pattern library browser

**Feedback Loop Integration**:
```python
# New module: src/cli/review.py

class ReviewService:
    def approve_result(self, function_id: str, feedback: Optional[str] = None):
        """
        Approve reverse engineering result.

        Side effects:
        - Mark result as accepted
        - Log to training data (for ML models)
        - Update pattern usage statistics
        """

    def reject_result(self, function_id: str, feedback: str, corrected_specql: Optional[str] = None):
        """
        Reject result and provide feedback.

        Side effects:
        - Log rejection reason (for ML training)
        - If corrected_specql provided, compute diff and learn
        - Flag patterns that were incorrectly detected
        - Lower pattern confidence scores if applicable
        """
```

### 9. Technology Stack & Integration Points

Specify **concrete technologies** that integrate with existing SpecQL stack:

**Current Stack**:
- **Language**: Python 3.11+
- **Build Tool**: `uv` (fast Python package manager)
- **CLI Framework**: `click`
- **Database**: SQLite (pattern library)
- **SQL Parsing**: `pglast`
- **Templating**: Jinja2
- **Testing**: pytest
- **LLM**: `llama-cpp-python` (local), `anthropic` (cloud)

**New Technologies to Add**:

**Embeddings & Vector Search**:
- **Option A**: Extend SQLite with `sqlite-vss` extension (vector similarity search)
- **Option B**: Separate vector DB (ChromaDB, Qdrant, FAISS)
- **Embedding Model**: `sentence-transformers` (e.g., `all-MiniLM-L6-v2`, `all-mpnet-base-v2`)

**ML Framework**:
- **TensorFlow/Keras**: Lightweight models for classification/regression
- **scikit-learn**: Feature extraction, baseline models, evaluation
- **MLflow** (optional): Experiment tracking

**Prompt Management**:
- **LangChain** or **LlamaIndex** (optional): If using RAG extensively
- **Custom prompt templates**: Jinja2 (consistent with existing stack)

**Monitoring & Metrics**:
- **SQLite tables**: Log LLM calls, review actions, pattern usage
- **Prometheus + Grafana** (optional): Real-time metrics dashboard

**Suggest specific integration points** in existing codebase:
```python
# src/pattern_library/embeddings.py (NEW)
class PatternEmbeddingService:
    def embed_pattern(self, pattern: Dict) -> np.ndarray: ...
    def embed_function(self, sql: str, specql: Dict) -> np.ndarray: ...
    def find_similar_patterns(self, embedding: np.ndarray, top_k: int) -> List[Dict]: ...

# src/pattern_library/api.py (EXTEND)
class PatternLibrary:
    # NEW METHODS
    def retrieve_similar_patterns(self, embedding, top_k, category_filter) -> List[Dict]: ...
    def create_pattern_from_nl(self, description, category, llm_service) -> Dict: ...
    def suggest_pattern_from_function(self, sql, specql, llm_service) -> Dict: ...

# src/reverse_engineering/ai_enhancer.py (EXTEND)
class AIEnhancer:
    def __init__(self, ..., pattern_library: PatternLibrary, ml_triage: Optional[MLTriageService]):
        self.pattern_library = pattern_library
        self.ml_triage = ml_triage

    # NEW METHOD
    def enhance_with_pattern_context(self, specql_ast, sql_function) -> EnhancedResult: ...

# src/reverse_engineering/ml_triage.py (NEW)
class MLTriageService:
    def validate_pattern(self, features, pattern) -> float: ...
    def should_review(self, features, ai_output) -> Tuple[bool, float]: ...
    def calibrate_confidence(self, features, confidence) -> float: ...

# src/cli/review.py (NEW)
class ReviewService:
    def list_pending_reviews(self) -> List[Dict]: ...
    def approve_result(self, function_id, feedback) -> None: ...
    def reject_result(self, function_id, feedback, corrected_specql) -> None: ...
```

### 10. Phased Implementation Roadmap

Break the implementation into **clear phases** with dependencies, milestones, and success criteria.

**For each phase, specify**:
1. **Goals**: What does this phase achieve?
2. **Main Tasks**: Specific implementation tasks (be concrete!)
3. **Success Criteria**: How do we know this phase is complete?
4. **Dependencies**: What must be completed first?
5. **Estimated Effort**: Rough timeline (e.g., "1-2 weeks for 1 engineer")
6. **Integration Points**: Which existing modules are modified?
7. **Testing Strategy**: Unit tests, integration tests, manual validation

**Example Phase Structure**:

#### Phase 1: Pattern Embeddings & Retrieval (MVP)
**Goals**:
- Enable similarity-based pattern retrieval
- Integrate pattern retrieval into AI enhancer

**Main Tasks**:
1. Implement `PatternEmbeddingService`
   - Choose embedding model (e.g., `all-MiniLM-L6-v2`)
   - Create embeddings for existing patterns in library
   - Store embeddings in new `pattern_embeddings` table
2. Add similarity search to `PatternLibrary.retrieve_similar_patterns()`
3. Extend `ai_enhancer.py` to retrieve patterns before LLM call
4. Update prompts to include retrieved patterns as context

**Success Criteria**:
- All existing patterns have embeddings
- Retrieval returns relevant patterns (manual inspection of top-5)
- Reverse engineering with pattern context shows improved accuracy (A/B test)

**Dependencies**: None (builds on existing code)

**Estimated Effort**: 1 week (1 engineer)

**Integration Points**:
- `src/pattern_library/api.py` (extend)
- `src/reverse_engineering/ai_enhancer.py` (extend)
- `src/pattern_library/schema.sql` (add `pattern_embeddings` table)

**Testing**:
- Unit tests for embedding generation
- Integration test: Reverse engineer function, verify retrieved patterns
- Manual validation: Check pattern relevance

---

#### Phase 2: Pattern Discovery Pipeline
**Goals**:
- Automatically suggest new patterns from legacy code
- Human-in-the-loop workflow for pattern approval

**Main Tasks**:
1. Implement pattern suggestion logic in `ai_enhancer.py`
   - Trigger criteria (low confidence, complexity, keywords)
   - LLM prompt for pattern extraction
2. Create `pattern_suggestions` table
3. Implement `specql patterns review-suggestions` CLI command
4. Implement `specql patterns approve/reject` CLI commands
5. Update `PatternLibrary.add_domain_pattern()` to handle suggested patterns

**Success Criteria**:
- Reverse engineering flags 5% of functions as "pattern candidates"
- Human can review and approve suggested patterns via CLI
- Approved patterns are added to library and reused

**Dependencies**: Phase 1 (pattern retrieval)

**Estimated Effort**: 1.5 weeks (1 engineer)

**Integration Points**:
- `src/reverse_engineering/ai_enhancer.py` (extend)
- `src/cli/reverse.py` (extend)
- `src/cli/review.py` (NEW)
- `src/pattern_library/schema.sql` (add `pattern_suggestions` table)

**Testing**:
- Unit tests for pattern suggestion logic
- Integration test: Process legacy function, verify suggestion created
- Manual validation: Review UI/UX of approval workflow

---

#### Phase 3: Natural Language Pattern Creation
**Goals**:
- Users can create patterns from text descriptions
- LLM generates structured pattern definitions

**Main Tasks**:
1. Implement `PatternLibrary.create_pattern_from_nl()`
2. Design LLM prompt for pattern generation
3. Implement validation (JSON schema, SpecQL syntax, naming conventions)
4. Create `specql patterns create-from-description` CLI command
5. Add preview and approval workflow

**Success Criteria**:
- Users can create patterns from descriptions via CLI
- Generated patterns follow SpecQL conventions
- Patterns are valid and can be instantiated

**Dependencies**: Phase 1 (pattern infrastructure)

**Estimated Effort**: 2 weeks (1 engineer)

**Integration Points**:
- `src/pattern_library/api.py` (extend)
- `src/cli/patterns.py` (NEW)
- `src/reverse_engineering/ai_enhancer.py` (reuse prompt engineering)

**Testing**:
- Unit tests for pattern generation
- Integration test: Generate pattern, validate, instantiate
- Manual validation: Create real-world patterns, check quality

---

#### Phase 4: ML-Based QA & Triage
**Goals**:
- Train lightweight ML models for pattern validation and review triage
- Reduce human review burden for high-confidence results

**Main Tasks**:
1. Implement logging infrastructure for training data
   - Log all reverse engineering results
   - Track human approvals/rejections
   - Extract features from functions
2. Implement `MLTriageService` with initial models:
   - Pattern validation classifier
   - Needs-review classifier
3. Collect initial training data (process historical conversions)
4. Train baseline models (scikit-learn)
5. Integrate into `ai_enhancer.py`
6. Implement auto-accept logic based on triage scores

**Success Criteria**:
- Models achieve >80% accuracy on validation set
- Auto-accept rate increases by 30%
- False positive rate for auto-accept <5%

**Dependencies**: Phase 2 (need human feedback data)

**Estimated Effort**: 3 weeks (1 ML engineer)

**Integration Points**:
- `src/reverse_engineering/ml_triage.py` (NEW)
- `src/reverse_engineering/ai_enhancer.py` (extend)
- `src/cli/review.py` (extend for feedback logging)

**Testing**:
- Unit tests for feature extraction
- Model evaluation on holdout set
- A/B test: Measure auto-accept accuracy

---

#### Phase 5: Multi-Language Template Generation
**Goals**:
- LLM generates idiomatic templates for each target language
- Pattern library supports optimized code generation per language

**Main Tasks**:
1. Design LLM prompts for template generation (PostgreSQL, Django, SQLAlchemy)
2. Extend `PatternLibrary.add_domain_pattern()` to generate templates
3. Implement template validation (syntax checking per language)
4. Add `--generate-templates` flag to pattern creation workflows

**Success Criteria**:
- Patterns automatically have templates for all supported languages
- Generated code is idiomatic and passes linters
- Manual review confirms quality

**Dependencies**: Phase 3 (NL pattern creation)

**Estimated Effort**: 2 weeks (1 engineer)

**Integration Points**:
- `src/pattern_library/api.py` (extend)
- `src/generators/pattern_based_compiler.py` (integrate templates)

**Testing**:
- Unit tests for template generation
- Integration test: Create pattern, generate templates, compile to code
- Manual validation: Check generated Django/SQLAlchemy code

---

#### Phase 6: Feedback Loops & Continuous Improvement
**Goals**:
- Automated retraining of ML models
- Pattern library analytics and optimization
- Performance monitoring

**Main Tasks**:
1. Implement pattern usage analytics
   - Track which patterns are used most
   - Track which patterns are frequently corrected
   - Deprecate low-quality patterns
2. Implement automated model retraining pipeline
   - Weekly retraining on new data
   - A/B testing for model updates
3. Create metrics dashboard
   - Pattern library growth
   - Auto-accept rates
   - Human review time
4. Implement pattern versioning and migration

**Success Criteria**:
- Models improve over time (monitored accuracy)
- Low-quality patterns are deprecated
- Metrics dashboard shows key KPIs

**Dependencies**: Phase 4 (ML models)

**Estimated Effort**: 2 weeks (1 engineer)

**Integration Points**:
- `src/pattern_library/analytics.py` (NEW)
- `src/reverse_engineering/ml_triage.py` (extend)
- `src/cli/stats.py` (NEW)

**Testing**:
- Unit tests for analytics
- Integration test: Simulate usage, verify metrics
- Manual validation: Review dashboard

---

### 11. Risks, Trade-offs, and Mitigation Strategies

Identify **key risks** and suggest **concrete mitigation strategies**:

#### Risk 1: Pattern Library Growth Becomes Unmanageable
**Symptoms**: Too many patterns, duplicates, inconsistencies, hard to search

**Mitigation**:
- Implement pattern deduplication (embedding similarity threshold)
- Periodic human review of library (monthly "pattern pruning")
- Pattern categorization and tagging
- Pattern popularity-based ranking (show most-used first)
- Pattern deprecation workflow

#### Risk 2: LLM Hallucinations in Pattern Generation
**Symptoms**: Generated patterns are invalid, don't follow conventions, produce broken code

**Mitigation**:
- **Strict validation**: JSON schema, SpecQL syntax checker, dry-run instantiation
- **Human approval required** for all LLM-generated patterns before library insertion
- **Few-shot prompting**: Include exemplar patterns in prompts
- **Iterative refinement**: LLM generates → Validation fails → LLM fixes → Repeat

#### Risk 3: Vector Search Returns Irrelevant Patterns
**Symptoms**: Retrieved patterns don't match function semantics, mislead LLM

**Mitigation**:
- **Hybrid search**: Combine embeddings + keyword + category filters
- **Re-ranking**: Use LLM to re-rank top-K candidates
- **Feedback loop**: Track which retrieved patterns were actually used → Improve retrieval
- **Manual pattern tagging**: Add semantic tags to patterns for better filtering

#### Risk 4: ML Models Overfit or Drift
**Symptoms**: Model accuracy degrades over time, biased toward specific patterns

**Mitigation**:
- **Holdout evaluation set**: Never train on this data, monitor accuracy
- **Regular retraining**: Weekly or monthly with fresh data
- **A/B testing**: New model vs old model, compare metrics before deploying
- **Drift detection**: Monitor feature distributions over time

#### Risk 5: Local LLM Performance Bottleneck
**Symptoms**: Reverse engineering is slow, GPU memory issues, batch processing fails

**Mitigation**:
- **Model quantization**: 4-bit or 8-bit quantization (minimal accuracy loss)
- **Batching**: Process multiple functions in parallel
- **Cloud escalation**: Expensive functions → Use cloud LLM
- **Caching**: Cache LLM responses for identical/similar functions
- **Hardware upgrade**: Invest in better GPU (e.g., RTX 4090 → A6000)

#### Risk 6: Human Review Fatigue
**Symptoms**: Backlog of pending reviews, reviewers approve without careful inspection

**Mitigation**:
- **Prioritization**: High-risk functions (tax, payment, refund) → Mandatory review; low-risk → Auto-accept
- **Review quotas**: Limit daily reviews per person
- **Gamification**: Track review metrics, reward high-quality feedback
- **Automated summaries**: LLM generates summary of changes for quick review

### 12. Future Extensions & Vision

Suggest **future enhancements** beyond the initial implementation:

#### Extension 1: Community Pattern Marketplace
- Public pattern library (GitHub repo or web portal)
- Users share domain-specific patterns (e-commerce, healthcare, finance)
- Rating and review system
- Pattern discovery and recommendation

#### Extension 2: Interactive Pattern Builder UI
- Web-based UI for creating patterns (vs CLI)
- Visual workflow designer for actions
- Drag-and-drop field editor
- Live preview of generated code

#### Extension 3: Cross-Language Pattern Migration
- Automatically migrate patterns between languages
- "I have this Django pattern, generate the SQLAlchemy equivalent"
- Support for more languages (Ruby on Rails, Java/Hibernate, etc.)

#### Extension 4: Advanced ML Models
- **Transformer-based models**: Fine-tune CodeBERT/GraphCodeBERT for pattern detection
- **Sequence-to-sequence**: SQL → SpecQL as seq2seq translation
- **Anomaly detection**: Identify truly novel patterns vs noise

#### Extension 5: Integration with CI/CD
- Reverse engineer SQL changes in PRs automatically
- Pattern compliance checking (enforces use of approved patterns)
- Auto-generate migration scripts (SpecQL diff → Flyway/Liquibase migrations)

#### Extension 6: Multi-Tenant Pattern Libraries
- Per-organization pattern libraries
- Private patterns vs public patterns
- Pattern sharing across teams

---

## Output Format

Produce your implementation plan as a **structured Markdown document** with:

1. **Executive Summary** (1 page)
   - High-level architecture diagram (ASCII or mermaid)
   - Key components and integration points
   - Success metrics

2. **Detailed Design** (10-15 pages)
   - Section-by-section addressing requirements 1-11 above
   - Clear headings and subheadings
   - Code snippets and schema examples where helpful
   - Concrete technology choices with justifications

3. **Phased Roadmap** (2-3 pages)
   - Timeline (weeks/months)
   - Dependencies and critical path
   - Resource requirements (engineers, GPU hardware)
   - Milestones and deliverables

4. **Risk Analysis** (1-2 pages)
   - Risk matrix (likelihood × impact)
   - Mitigation strategies
   - Contingency plans

5. **Appendices**
   - Detailed SQL schema changes
   - Example prompts for LLM tasks
   - Sample pattern definitions
   - Evaluation metrics definitions

---

## Key Constraints

1. **Leverage Existing Infrastructure**: Reuse `PatternLibrary API`, `ai_enhancer.py`, `CLIOrchestrator`, hierarchical file generation, etc.

2. **Follow SpecQL Conventions**: Trinity pattern, naming conventions, audit fields, 6-digit hierarchical numbering (SSDSEX), protocol-based design

3. **Maintain Test Coverage**: All new code must have unit + integration tests

4. **Pragmatic Trade-offs**: Prefer simple solutions over perfect solutions; iterate and improve

5. **Hardware Constraints**: Single workstation with RTX 4090 (24 GB VRAM) for local LLM

6. **User Experience**: CLI-first, intuitive commands, clear feedback, minimal friction

7. **Production-Ready**: Code quality, error handling, logging, monitoring from Day 1

---

## Success Criteria for Your Implementation Plan

A successful plan should enable a **small engineering team (2-3 engineers)** to:
- Understand the architecture without needing clarification
- Create JIRA/GitHub tickets directly from your plan
- Estimate effort and timeline with confidence
- Implement phases sequentially with clear milestones
- Integrate new components into existing SpecQL infrastructure seamlessly

**After reading your plan, the team should know**:
- Exactly what to build
- How to build it
- Where it fits in the existing codebase
- How to test it
- When it's done

---

## Example Section (for reference only)

Here's an example of the level of detail expected:

### 4.2 Pattern Retrieval Implementation

**File**: `src/pattern_library/embeddings.py` (NEW)

**Class**: `PatternEmbeddingService`

**Dependencies**:
```python
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
```

**Schema Change** (`src/pattern_library/schema.sql`):
```sql
CREATE TABLE pattern_embeddings (
    pattern_id INTEGER PRIMARY KEY REFERENCES domain_patterns(id),
    embedding BLOB NOT NULL,  -- Numpy array serialized via pickle
    model_name TEXT NOT NULL,  -- e.g., "all-MiniLM-L6-v2"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pattern_embeddings_model ON pattern_embeddings(model_name);
```

**Implementation**:
```python
class PatternEmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def embed_pattern(self, pattern: Dict) -> np.ndarray:
        """
        Generate embedding for a domain pattern.

        Combines:
        - Pattern description
        - Category
        - Field names
        - Action names

        Returns 384-dim vector (for all-MiniLM-L6-v2)
        """
        text = self._pattern_to_text(pattern)
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def _pattern_to_text(self, pattern: Dict) -> str:
        """Convert pattern to searchable text."""
        parts = [
            pattern["description"],
            f"Category: {pattern['category']}",
        ]

        # Add field names
        if "fields" in pattern.get("implementation", {}):
            field_names = [f["name"] for f in pattern["implementation"]["fields"]]
            parts.append(f"Fields: {', '.join(field_names)}")

        # Add action names
        if "actions" in pattern.get("implementation", {}):
            action_names = [a["name"] for a in pattern["implementation"]["actions"]]
            parts.append(f"Actions: {', '.join(action_names)}")

        return " | ".join(parts)
```

**Integration with PatternLibrary API** (`src/pattern_library/api.py`):
```python
class PatternLibrary:
    def __init__(self, db_path: Path):
        self.db = sqlite3.connect(db_path)
        self.embedding_service = PatternEmbeddingService()  # NEW

    def add_domain_pattern(self, name, category, description, parameters, implementation):
        """Existing method - EXTEND to generate embedding"""
        # ... existing code ...

        # NEW: Generate and store embedding
        pattern = {
            "name": name,
            "category": category,
            "description": description,
            "parameters": parameters,
            "implementation": implementation
        }
        embedding = self.embedding_service.embed_pattern(pattern)
        self._store_embedding(pattern_id, embedding)

    def retrieve_similar_patterns(
        self,
        embedding: np.ndarray,
        top_k: int = 5,
        category_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        NEW METHOD: Retrieve top-K similar patterns via cosine similarity.
        """
        # Load all pattern embeddings from DB
        query = "SELECT pattern_id, embedding FROM pattern_embeddings WHERE model_name = ?"
        cursor = self.db.execute(query, (self.embedding_service.model_name,))

        # Compute cosine similarities
        similarities = []
        for row in cursor:
            pattern_id, embedding_blob = row
            pattern_embedding = pickle.loads(embedding_blob)
            similarity = self._cosine_similarity(embedding, pattern_embedding)
            similarities.append((pattern_id, similarity))

        # Sort by similarity and take top-K
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_pattern_ids = [pid for pid, _ in similarities[:top_k]]

        # Load full pattern objects
        patterns = [self.get_domain_pattern(pid) for pid in top_pattern_ids]

        # Filter by category if specified
        if category_filter:
            patterns = [p for p in patterns if p["category"] in category_filter]

        return patterns[:top_k]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _store_embedding(self, pattern_id: int, embedding: np.ndarray):
        embedding_blob = pickle.dumps(embedding)
        self.db.execute(
            "INSERT INTO pattern_embeddings (pattern_id, embedding, model_name) VALUES (?, ?, ?)",
            (pattern_id, embedding_blob, self.embedding_service.model_name)
        )
        self.db.commit()
```

**Testing** (`tests/unit/pattern_library/test_embeddings.py`):
```python
def test_embed_pattern():
    service = PatternEmbeddingService()
    pattern = {
        "name": "audit_trail",
        "category": "audit",
        "description": "Track created_at, updated_at, deleted_at",
        "implementation": {
            "fields": [
                {"name": "created_at", "type": "timestamp"},
                {"name": "updated_at", "type": "timestamp"}
            ]
        }
    }

    embedding = service.embed_pattern(pattern)

    assert embedding.shape == (384,)  # all-MiniLM-L6-v2 dimension
    assert embedding.dtype == np.float32


def test_retrieve_similar_patterns(pattern_library_with_embeddings):
    lib = pattern_library_with_embeddings

    # Create query embedding
    query_pattern = {
        "description": "Track changes to records",
        "category": "audit"
    }
    query_embedding = lib.embedding_service.embed_pattern(query_pattern)

    # Retrieve similar patterns
    results = lib.retrieve_similar_patterns(query_embedding, top_k=3)

    assert len(results) == 3
    assert results[0]["category"] == "audit"  # Most similar should be audit-related
```

**Integration Test** (`tests/integration/test_pattern_retrieval_in_reverse_engineering.py`):
```python
def test_reverse_engineer_with_pattern_context():
    """Test that pattern retrieval improves reverse engineering."""

    # SQL function with clear audit trail pattern
    sql = """
    CREATE FUNCTION update_customer(p_id INTEGER, p_name TEXT) RETURNS void AS $$
    BEGIN
        UPDATE customers
        SET name = p_name,
            updated_at = now(),
            updated_by = current_user
        WHERE id = p_id;
    END;
    $$ LANGUAGE plpgsql;
    """

    # Reverse engineer with pattern retrieval enabled
    enhancer = AIEnhancer(
        use_local=True,
        pattern_library=PatternLibrary("test.db")
    )

    result = enhancer.enhance_function_with_patterns(sql)

    # Should detect audit_trail pattern
    assert "audit_trail" in result.detected_patterns

    # Should suggest proper variable names based on pattern
    assert result.variable_mapping["updated_at"] == "updated_timestamp"
```

**Estimated Effort**:
- Implementation: 3 days
- Testing: 1 day
- Integration: 1 day
- **Total**: 5 days (1 engineer)

---

**Now, produce your comprehensive implementation plan following this structure and level of detail.**
