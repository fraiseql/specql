# Implementation Agent Prompt: PostgreSQL + Grok Pattern Library

## Role & Mission

You are a senior Python/PostgreSQL engineer implementing the SpecQL Pattern Library enhancement system.

**Your task**: Implement the complete pattern library system following the detailed implementation plan in `docs/implementation_plans/POSTGRESQL_GROK_IMPLEMENTATION_PLAN.md`.

---

## Context

**Project**: SpecQL - Business YAML → Production PostgreSQL code generator
**Goal**: Add intelligent pattern library with LLM-powered discovery and natural language generation
**Timeline**: 8 weeks, 4 phases
**Cost**: $0 (free Grok LLM + local PostgreSQL)

### Technical Stack

- **Database**: PostgreSQL 17.6 + pgvector extension (already installed)
- **LLM**: OpenCode Grok Code Fast 1 (FREE, tested working: `opencode run --model opencode/grok-code`)
- **Embeddings**: sentence-transformers (CPU-friendly, ~50ms)
- **Language**: Python 3.11+, psycopg, pgvector
- **Hardware**: Lenovo X270 (no GPU needed)

### Key Architecture Decisions

1. **PostgreSQL + pgvector** for native vector search (100x faster than SQLite)
2. **Same database** as SpecQL-generated schemas (critical for integration)
3. **OpenCode Grok** via subprocess for LLM calls (no API keys needed)
4. **HNSW index** for fast approximate nearest neighbor search (<50ms for 1000 patterns)

---

## Implementation Plan Location

**READ THIS FIRST**: `docs/implementation_plans/POSTGRESQL_GROK_IMPLEMENTATION_PLAN.md`

This 50-page document contains:
- Complete PostgreSQL schema with pgvector
- Full Python code samples
- Setup scripts
- Testing strategy
- 4 phases with detailed tasks

---

## Your Tasks

### Phase 0: Setup (Week 1) - START HERE

**Goal**: Get PostgreSQL + pgvector working with seed patterns

**Tasks**:
1. Create setup script: `scripts/setup_database.sh`
   - Create database `specql_patterns`
   - Create user `specql_user`
   - Install extensions: `vector`, `pg_trgm`
   - Set environment variable `SPECQL_DB_URL`

2. Create schema: `database/pattern_library_schema.sql`
   - Pattern tables with native `vector(384)` columns
   - HNSW indexes for fast vector search
   - GIN indexes for JSONB queries
   - Full-text search with tsvector
   - Utility functions and views
   - **COPY FROM**: Implementation plan has complete schema

3. Seed patterns: `database/seed_patterns.sql`
   - 5 baseline patterns (audit_trail, soft_delete, state_machine, approval_workflow, validation_chain)

4. Python dependencies in `pyproject.toml`:
   - Add `patterns` extra with: psycopg, pgvector, sentence-transformers, numpy, rich

5. Verify setup:
   ```bash
   # Test pgvector
   psql $SPECQL_DB_URL -c "SELECT vector '[1,2,3]' <=> vector '[4,5,6]';"

   # Test patterns loaded
   psql $SPECQL_DB_URL -c "SELECT COUNT(*) FROM pattern_library.domain_patterns;"

   # Test Python
   uv run python -c "from sentence_transformers import SentenceTransformer; print('OK')"
   ```

**Deliverables**:
- [ ] `scripts/setup_database.sh` (executable)
- [ ] `database/pattern_library_schema.sql` (complete schema)
- [ ] `database/seed_patterns.sql` (5 patterns)
- [ ] `pyproject.toml` updated
- [ ] All verification tests pass

---

### Phase 1: Pattern Embeddings + RAG (Weeks 2-3)

**Goal**: Generate embeddings for patterns, implement pgvector-based retrieval

**Tasks**:
1. Implement `src/pattern_library/embeddings_pg.py`:
   - `PatternEmbeddingService` class
   - `embed_pattern()` - Generate 384-dim embeddings
   - `generate_all_embeddings()` - Batch process
   - `retrieve_similar()` - Native pgvector query
   - `hybrid_search()` - Vector + text + filters
   - **COPY FROM**: Implementation plan has complete code

2. Implement `src/reverse_engineering/grok_provider.py`:
   - `GrokProvider` class
   - `call()` - Subprocess to OpenCode CLI
   - `call_json()` - Parse JSON with retries
   - Log to PostgreSQL (`grok_call_logs` table)
   - **COPY FROM**: Implementation plan has complete code

3. CLI commands in `src/cli/embeddings.py`:
   - `specql embeddings generate` - Generate all embeddings
   - `specql embeddings test-retrieval <query>` - Test similarity search

4. Generate embeddings for seed patterns

**Deliverables**:
- [ ] `src/pattern_library/embeddings_pg.py`
- [ ] `src/reverse_engineering/grok_provider.py`
- [ ] `src/cli/embeddings.py`
- [ ] All 5 seed patterns have embeddings
- [ ] Tests: `tests/unit/pattern_library/test_embeddings_pg.py`
- [ ] Benchmark: <50ms retrieval for 100 patterns

---

### Phase 2: Pattern Discovery (Weeks 4-5)

**Goal**: Auto-suggest patterns from legacy SQL, human review workflow

**Tasks**:
1. Extend `src/reverse_engineering/ai_enhancer.py`:
   - `discover_pattern()` - Analyze SQL for novel patterns
   - Trigger criteria: low similarity (<0.7), high complexity
   - Grok prompt for pattern extraction
   - Create pattern suggestions in DB

2. Implement `src/pattern_library/suggestion_service_pg.py`:
   - `PatternSuggestionService` class
   - `create_suggestion()`, `list_pending()`, `get_suggestion()`
   - `approve_suggestion()` - Move to domain_patterns
   - `reject_suggestion()` - Mark rejected

3. CLI commands in `src/cli/patterns.py`:
   - `specql patterns review-suggestions` - List pending
   - `specql patterns show <id>` - Show details
   - `specql patterns approve <id>` - Approve
   - `specql patterns reject <id> --reason "..."` - Reject

4. Integration: `specql reverse --discover-patterns` flag

**Deliverables**:
- [ ] Pattern discovery in `ai_enhancer.py`
- [ ] `src/pattern_library/suggestion_service_pg.py`
- [ ] CLI commands in `src/cli/patterns.py`
- [ ] Integration with `specql reverse`
- [ ] Tests: `tests/integration/test_pattern_discovery.py`

---

### Phase 3: Natural Language Generation (Weeks 6-7)

**Goal**: Generate patterns from text descriptions

**Tasks**:
1. Implement `src/pattern_library/nl_generator.py`:
   - `NLPatternGenerator` class
   - `generate()` - LLM prompt for NL → pattern
   - `_validate_pattern()` - JSON schema, SpecQL syntax, naming conventions
   - `_score_confidence()` - Quality scoring

2. CLI command:
   - `specql patterns create-from-description --description "..." --category workflow`

3. Grok prompts in `src/reverse_engineering/prompts/`:
   - `nl_pattern_generation.jinja2` - NL to pattern prompt
   - Include SpecQL conventions, output format, examples

**Deliverables**:
- [ ] `src/pattern_library/nl_generator.py`
- [ ] CLI command implemented
- [ ] Prompt template
- [ ] Tests: `tests/unit/pattern_library/test_nl_generator.py`
- [ ] Manual validation: Generate 10 patterns, measure quality

---

### Phase 4: Testing & Documentation (Week 8)

**Goal**: Production-ready system

**Tasks**:
1. Integration tests: `tests/integration/test_e2e_pattern_library.py`
   - Full workflow: SQL → discovery → approval → reuse
   - NL → pattern → validation → usage

2. Performance benchmarks: `tests/performance/`
   - Embedding generation speed
   - pgvector retrieval latency (HNSW index)
   - Grok response times
   - End-to-end reverse engineering

3. Documentation:
   - `docs/pattern_library/USER_GUIDE.md` - How to use
   - `docs/pattern_library/DEVELOPER_GUIDE.md` - How to extend
   - `README.md` update with pattern library features

4. Demo: `demo/pattern_library_demo.sh`

**Deliverables**:
- [ ] All integration tests passing
- [ ] Performance benchmarks documented
- [ ] User + developer documentation
- [ ] Demo script

---

## Key Files to Create

### Database
- `scripts/setup_database.sh` - Automated setup
- `database/pattern_library_schema.sql` - Complete schema
- `database/seed_patterns.sql` - Baseline patterns

### Python Core
- `src/pattern_library/embeddings_pg.py` - Embeddings + pgvector
- `src/reverse_engineering/grok_provider.py` - Grok LLM
- `src/pattern_library/suggestion_service_pg.py` - Suggestions
- `src/pattern_library/nl_generator.py` - NL generation

### CLI
- `src/cli/embeddings.py` - Embedding commands
- `src/cli/patterns.py` - Pattern management commands

### Tests
- `tests/unit/pattern_library/test_embeddings_pg.py`
- `tests/unit/pattern_library/test_nl_generator.py`
- `tests/integration/test_pattern_discovery.py`
- `tests/integration/test_e2e_pattern_library.py`

---

## Important Constraints

### SpecQL Conventions (MANDATORY)
- **Trinity Pattern**: All entities have `pk_*` (INTEGER), `id` (UUID), `identifier` (TEXT)
- **Naming**: `tb_*` (tables), `fk_*` (foreign keys), `idx_*` (indexes)
- **Audit Fields**: `created_at`, `updated_at`, `deleted_at`
- **Schema Organization**: Framework schemas (common, app, core) vs user schemas (crm, sales, etc.)

### PostgreSQL Requirements
- Use `vector(384)` type for embeddings (pgvector)
- Create HNSW index: `USING hnsw (embedding vector_cosine_ops)`
- Use JSONB for pattern definitions (not JSON)
- Use GIN indexes for JSONB: `USING gin (parameters jsonb_path_ops)`
- Use tsvector for full-text search

### Grok Integration
- Call via subprocess: `opencode run --model opencode/grok-code`
- Always request JSON output
- Retry parsing if JSON extraction fails
- Log all calls to `grok_call_logs` table

### Code Quality
- Follow existing SpecQL patterns (check `src/generators/`, `src/cli/`)
- Use `psycopg` (NOT psycopg2) with pgvector integration
- Type hints for all functions
- Comprehensive docstrings
- Error handling with clear messages

---

## Testing Strategy

### Unit Tests
```bash
# Test embeddings
uv run pytest tests/unit/pattern_library/test_embeddings_pg.py -v

# Test Grok provider
uv run pytest tests/unit/reverse_engineering/test_grok_provider.py -v
```

### Integration Tests
```bash
# End-to-end pattern discovery
uv run pytest tests/integration/test_pattern_discovery.py -v

# Full workflow
uv run pytest tests/integration/test_e2e_pattern_library.py -v
```

### Manual Validation
```bash
# Generate embeddings
specql embeddings generate

# Test retrieval
specql embeddings test-retrieval "approval workflow"

# Test pattern discovery
specql reverse demo/sql/complex_function.sql --discover-patterns

# Review suggestions
specql patterns review-suggestions
specql patterns show 1
specql patterns approve 1

# NL generation
specql patterns create-from-description \
  --description "Two-stage approval with email notifications" \
  --category workflow
```

---

## Success Criteria

### Technical
- [ ] PostgreSQL + pgvector working with HNSW index
- [ ] All 4 phases implemented
- [ ] All tests passing (unit + integration)
- [ ] Performance targets met (<50ms retrieval)

### Quality
- [ ] Pattern retrieval accuracy >75% (manual validation)
- [ ] Pattern discovery rate 5-10% of functions
- [ ] NL pattern generation >70% valid first try
- [ ] Zero LLM costs (Grok is free)

### Production-Ready
- [ ] Documentation complete (user + developer guides)
- [ ] Demo working
- [ ] Multi-user capable (PostgreSQL MVCC)
- [ ] Monitoring in place (pg_stat views, grok_call_logs)

---

## How to Use This Prompt

1. **Start with Phase 0** - Get PostgreSQL + pgvector working
2. **Follow the plan** - Each phase builds on previous
3. **Copy code samples** - Implementation plan has complete, tested code
4. **Test continuously** - Run tests after each component
5. **Ask questions** - If anything unclear, ask for clarification

---

## Quick Start Commands

```bash
# Read the full plan
cat docs/implementation_plans/POSTGRESQL_GROK_IMPLEMENTATION_PLAN.md

# Phase 0: Setup (START HERE)
./scripts/setup_database.sh
psql $SPECQL_DB_URL -f database/pattern_library_schema.sql
psql $SPECQL_DB_URL -f database/seed_patterns.sql
uv sync --extra patterns

# Phase 1: Generate embeddings
specql embeddings generate
specql embeddings test-retrieval "approval workflow"

# Verify Grok works
echo "What is 2+2?" | opencode run --model opencode/grok-code
```

---

## Resources

- **Implementation Plan**: `docs/implementation_plans/POSTGRESQL_GROK_IMPLEMENTATION_PLAN.md` (READ THIS!)
- **SQLite vs PostgreSQL Analysis**: `docs/analysis/SQLITE_VS_POSTGRESQL_PATTERNS.md`
- **Existing Code**: `src/generators/`, `src/cli/`, `src/reverse_engineering/`
- **Tests**: `tests/unit/`, `tests/integration/`

---

## Contact

If you encounter issues:
1. Check the implementation plan for detailed code samples
2. Verify PostgreSQL + pgvector setup
3. Test Grok: `echo "test" | opencode run --model opencode/grok-code`
4. Check existing SpecQL code for patterns

---

**Start with Phase 0 and work sequentially through the phases. The implementation plan has all the code you need - follow it carefully!**

Good luck! 🚀
