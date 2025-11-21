# Content Triage Analysis
## **Keep, Kill, or Merge: 180+ Documentation Files**

*Triaged: 2025-11-19 | Based on user journeys and information architecture*

---

## Executive Summary

**Total Files**: ~180 markdown files
**Action**: Archive 60%, Rewrite 30%, Keep 10%
**Rationale**: Most docs are historical artifacts from development phases

---

## Triage Categories

### 🗂️ **KEEP** (High-value, current documentation)
Files that serve user needs and are still accurate.

### 🔄 **REWRITE** (Good content, wrong format/structure)
Content is valuable but needs restructuring for new architecture.

### 📦 **MERGE** (Related content scattered across files)
Consolidate related concepts into coherent guides.

### 🗑️ **ARCHIVE** (Historical/obsolete)
Move to `/archive/legacy-docs/` with explanatory README.

---

## Detailed Triage by Directory

### docs/guides/ (11 files) - **MIXED**

| File | Decision | Rationale | New Location |
|------|----------|-----------|--------------|
| `FRAISEQL_ANNOTATION_LAYERS.md` | **ARCHIVE** | Internal implementation detail | `/archive/legacy-docs/` |
| `action-syntax.md` | **REWRITE** | Good content, needs user-focused restructure | `05_guides/your-first-action.md` |
| `actions-guide.md` | **MERGE** | Split into multiple guides | `03_core-concepts/actions.md` + `05_guides/` |
| `graphql-integration.md` | **KEEP** | User-focused, still relevant | `05_guides/graphql-integration.md` |
| `multi-tenancy.md` | **KEEP** | Core enterprise feature | `05_guides/multi-tenancy.md` |
| `reverse-engineering-guide.md` | **REWRITE** | Only covers SQL, missing 4 languages | `02_migration/reverse-engineering/sql.md` |
| `rich-types-guide.md` | **REWRITE** | Good intro, needs expansion | `03_core-concepts/rich-types.md` |
| `security-best-practices.md` | **MERGE** | Combine with other security content | `07_advanced/security-hardening.md` |
| `stdlib-usage.md` | **REWRITE** | Basic intro, needs entity details | `04_stdlib/index.md` |
| `troubleshooting-actions.md` | **MERGE** | Combine with error handling | `05_guides/error-handling.md` |

### docs/architecture/ (25 files) - **ARCHIVE 80%**

| File | Decision | Rationale | New Location |
|------|----------|-----------|--------------|
| `APP_CORE_FUNCTION_PATTERN.md` | **ARCHIVE** | Implementation detail | `/archive/legacy-docs/` |
| `CQRS_*` files (3) | **MERGE** | Consolidate CQRS explanation | `03_core-concepts/trinity-pattern.md` |
| `FRAISEQL_*` files (4) | **MERGE** | Core concept explanation | `03_core-concepts/fraiseql.md` |
| `IDENTIFIER_*` files (2) | **MERGE** | Trinity pattern foundation | `03_core-concepts/trinity-pattern.md` |
| `MUTATION_IMPACT_METADATA.md` | **MERGE** | Action system explanation | `03_core-concepts/actions.md` |
| `SCHEMA_*` files (3) | **ARCHIVE** | Historical implementation | `/archive/legacy-docs/` |
| `TEAM_C_RETURN_TRACKING.md` | **ARCHIVE** | Internal team communication | `/archive/legacy-docs/` |
| All others | **ARCHIVE** | Implementation phase artifacts | `/archive/legacy-docs/` |

**Exception**: `IMPLEMENTATION_PLAN.md` → **MERGE** into `08_contributing/architecture.md`

### docs/getting-started/ (1 file) - **REWRITE**

| File | Decision | Rationale | New Location |
|------|----------|-----------|--------------|
| `your-first-action.md` | **MERGE** | Good content, expand to full flow | `01_getting-started/first-action.md` |

### docs/actions/ (10 files) - **MERGE**

| File | Decision | Rationale | New Location |
|------|----------|-----------|--------------|
| All action step docs | **MERGE** | Reference material for action steps | `06_reference/action-steps.md` |

### docs/post_beta_plan/ (17 files) - **ARCHIVE**

| Files | Decision | Rationale | New Location |
|-------|----------|-----------|--------------|
| All weekly reports | **ARCHIVE** | Historical development tracking | `/archive/legacy-docs/post-beta/` |

### docs/implementation-plans/ (2 files) - **ARCHIVE**

| Files | Decision | Rationale | New Location |
|-------|----------|-----------|--------------|
| CTO reviews, database decisions | **ARCHIVE** | Historical planning docs | `/archive/legacy-docs/` |

### docs/qa-reports/ (2 files) - **ARCHIVE**

| Files | Decision | Rationale | New Location |
|-------|----------|-----------|--------------|
| QA reports | **ARCHIVE** | Historical testing reports | `/archive/legacy-docs/` |

### docs/migration/ (4 files) - **MIXED**

| File | Decision | Rationale | New Location |
|------|----------|-----------|--------------|
| `PATTERN_*` files (3) | **MERGE** | Pattern implementation guidance | `02_migration/patterns/` |
| `SEPARATOR_MIGRATION_GUIDE.md` | **ARCHIVE** | Obsolete migration | `/archive/legacy-docs/` |

### docs/reverse_engineering/ (2 files) - **MERGE**

| File | Decision | Rationale | New Location |
|------|----------|-----------|--------------|
| `CAPABILITIES_INVENTORY.md` | **MERGE** | Assessment content | `02_migration/assess-legacy.md` |
| `PARSER_COORDINATOR_DESIGN.md` | **ARCHIVE** | Internal design | `/archive/legacy-docs/` |

### Root docs/ files (15+ files) - **MIXED**

| File | Decision | Rationale | New Location |
|------|----------|-----------|--------------|
| `README.md` | **REWRITE** | Good content, needs persona routing | `docs/README.md` (new router) |
| `WHY_SPECQL.md` | **MERGE** | Value proposition | `docs/03_core-concepts/business-yaml.md` |
| `FRAMEWORK_INTEGRATION.md` | **MERGE** | Reverse engineering overview | `02_migration/index.md` |
| `RUST_*` files (3) | **MERGE** | Language-specific guides | `02_migration/reverse-engineering/rust.md` |
| `TREE_SITTER_*` files (2) | **ARCHIVE** | Implementation detail | `/archive/legacy-docs/` |
| `PYTHON_3.13_SETUP.md` | **DELETE** | Obsolete workarounds | Remove entirely |
| `CLEANUP_AND_ENHANCEMENT_PLAN.md` | **ARCHIVE** | Historical planning | `/archive/legacy-docs/` |
| `PROJECT_STATUS.md` | **ARCHIVE** | Status updates | `/archive/legacy-docs/` |
| All test/planning docs | **ARCHIVE** | Development artifacts | `/archive/legacy-docs/` |

---

## Content Gems Extraction

### High-Value Content to Preserve

**From architecture/**:
- Trinity pattern explanations (3 files) → Extract best examples
- FraiseQL integration concepts → Core concept foundation
- Schema organization strategies → Advanced guides

**From guides/**:
- Action syntax examples → Practical guides
- Multi-tenancy setup → Enterprise guide
- GraphQL integration steps → Frontend guide

**From root docs/**:
- Framework integration details → Migration guides
- Rich type explanations → Core concepts

### Extraction Process
1. **Identify gems**: Best explanations of each concept
2. **Save to `/content-gems/`**: Organized by topic
3. **Reference in rewrites**: Link to source for attribution

---

## Archive Strategy

### `/archive/legacy-docs/` Structure
```
archive/legacy-docs/
├── README.md (Explains why archived, how to find current docs)
├── post-beta/ (Weekly development reports)
├── implementation/ (Planning documents)
├── qa-reports/ (Testing reports)
├── architecture/ (Technical design docs)
└── migration/ (Obsolete migration guides)
```

### Archive README Content
```markdown
# Archived Documentation

These documents represent SpecQL's development history from [start date] to [archive date].

## Why Archived
- **Outdated**: Information no longer reflects current SpecQL capabilities
- **Historical**: Development phase artifacts, not user documentation
- **Replaced**: Content rewritten for new information architecture

## Current Documentation
All current user-facing documentation is in `/docs/` with this new structure:
- [Getting Started](/docs/01_getting-started/)
- [Migration Guides](/docs/02_migration/)
- [Core Concepts](/docs/03_core-concepts/)
- etc.

## Finding What You Need
If you're looking for [specific topic], check [new location].
```

---

## Implementation Timeline

### Week 1 (Current): Triage & Planning ✅
- [x] Analyze all 180+ files
- [x] Create triage decisions
- [x] Design archive structure

### Week 2: Content Extraction
- [ ] Extract content gems to `/content-gems/`
- [ ] Create archive directory structure
- [ ] Move archived files with README

### Week 3: Migration & Cleanup
- [ ] Update all internal links
- [ ] Remove obsolete references
- [ ] Validate no broken links

---

## Success Metrics

- **Archive completeness**: 100% of decided files moved
- **Content preservation**: All valuable content extracted
- **Link integrity**: 0 broken references
- **User impact**: No disruption to existing workflows

This triage transforms documentation chaos into structured clarity, preserving value while removing noise.

---

*Content triage complete. Ready to extract gems and archive obsolete files.*</content>
</xai:function_call
