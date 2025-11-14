# Interactive CLI Guide

## Overview

The SpecQL Interactive CLI provides a visual, real-time development experience with live preview and pattern suggestions.

## Launch

```bash
specql interactive
```

## Interface Layout

```
┌─────────────────────────────────────────────────────────┐
│ SpecQL Interactive Builder                              │
├─────────────────────────────────────────────────────────┤
│ 📝 YAML Editor        │ 🔍 Live Preview (PostgreSQL)   │
│                       │                                 │
│ entity: Contact       │ CREATE TABLE crm.tb_contact (  │
│ schema: crm           │   pk_contact INTEGER PRIMARY... │
│ fields:               │   id UUID NOT NULL DEFAULT...   │
│   email: text         │   email TEXT NOT NULL,          │
│   status: enum        │   status TEXT CHECK (...),      │
│     - lead            │   created_at TIMESTAMPTZ...     │
│     - qualified       │ );                              │
│                       │                                 │
│ ✅ Valid SpecQL       │ Generated: 45 lines             │
├─────────────────────────────────────────────────────────┤
│ 🎯 Patterns: audit_trail (100%), state_machine (80%)   │
├─────────────────────────────────────────────────────────┤
│ [💾 Save] [🚀 Generate] [🎨 Pattern] [🤖 AI] [📤 Export]│
└─────────────────────────────────────────────────────────┘
```

## Features

### 1. Real-Time Preview

As you type YAML, the preview updates automatically showing:
- PostgreSQL DDL (schema mode)
- PL/pgSQL functions (actions mode)
- FraiseQL metadata (fraiseql mode)

**Toggle preview mode**: `Ctrl+P`

### 2. Syntax Highlighting

Custom SpecQL syntax highlighting with:
- Entity keywords (blue)
- Field types (green)
- Step keywords (orange)
- Patterns (purple)
- Strings and values (yellow)

### 3. Auto-Completion

Press `Tab` or `Ctrl+Space` for context-aware suggestions:

**In fields section**:
- Field types: `text`, `integer`, `ref`, `enum`
- Type templates with examples

**In actions section**:
- Step types: `validate`, `update`, `insert`
- Complete step templates

**Example**:
```yaml
fields:
  email: <Tab>

# Shows:
# - text
# - integer
# - ref(Entity)
# - enum (with values template)
```

### 4. Pattern Detection

Automatically detects patterns as you type:
- `audit_trail` - Timestamp and user tracking
- `soft_delete` - Soft deletion with deleted_at
- `state_machine` - Status field with transitions
- `multi_tenant` - Tenant isolation

**Apply pattern**: Click `🎨 Apply Pattern` or `Ctrl+K`

### 5. AI Assistance

Lightweight AI help for:
- Entity generation from description
- Field suggestions

## Keyboard Shortcuts

- `Ctrl+S` - Save YAML to file
- `Ctrl+G` - Generate schema
- `Ctrl+P` - Toggle preview mode (Schema/Actions/FraiseQL)
- `Ctrl+Q` - Quit
- `Ctrl+H` - Show help
- `Tab` - Auto-completion
- `Ctrl+Space` - Auto-completion
- `Ctrl+K` - Pattern search

## Preview Modes

### Schema Mode
Shows PostgreSQL DDL including:
- Table definitions
- Primary keys
- Foreign keys
- Indexes
- Constraints

### Actions Mode
Shows PL/pgSQL functions for:
- Business logic actions
- Validation rules
- Data transformations

### FraiseQL Mode
Shows GraphQL metadata annotations for:
- Type definitions
- Field mappings
- Resolver hints

## Pattern Library Integration

The interactive CLI integrates with the SpecQL pattern library to:
- Detect common patterns in your entities
- Suggest similar patterns from the library
- Apply patterns with one click
- Learn from community patterns

## AI Features

When an Anthropic API key is configured, the CLI provides:
- Natural language entity generation
- Intelligent field suggestions
- Action optimization
- Pattern recommendations

## Export Options

- **Save**: Export current YAML to file
- **Generate**: Create full schema migration
- **Export**: Export generated SQL files
- **Screenshot**: Save TUI screenshot (SVG)

## Getting Started

1. Launch: `specql interactive`
2. Start typing a SpecQL entity
3. Watch the live preview update
4. Use auto-completion for faster editing
5. Apply detected patterns
6. Generate your schema

The interactive CLI makes SpecQL development fast, visual, and enjoyable!