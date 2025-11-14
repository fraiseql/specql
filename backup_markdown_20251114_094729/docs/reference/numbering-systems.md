# SpecQL Numbering Systems Guide

**Choose the right file organization system for your project** 📁

## Quick Decision Guide

**Just starting out?** → Use **Decimal System** (default, simple)
**Enterprise project (100+ entities)?** → Consider **Hexadecimal System** (scalable)

## Overview

SpecQL supports **two numbering systems** for organizing generated DDL files. Both are production-ready and can coexist in the same codebase.

### System Comparison

| Feature | Decimal (Simple) | Hexadecimal (Registry) |
|---------|------------------|------------------------|
| **Complexity** | ⭐⭐⭐ Simple | ⭐⭐⭐⭐⭐ Advanced |
| **Setup** | Automatic (default) | Requires registry configuration |
| **Scaling** | Up to 50 entities | 1000+ entities |
| **Structure** | Flat directories | Deep hierarchy |
| **Use Case** | Most projects | Enterprise-scale |
| **Migration** | Easy (later) | Complex (initial setup) |

## System 1: Decimal System (Recommended for Most Users) ⭐

### When to Use

✅ **New projects**
✅ **Simple to medium complexity** (< 50 entities)
✅ **Fast iteration and development**
✅ **Human-readable structure**
✅ **Confiture integration**

### Directory Structure

```
db/schema/
├── 00_foundation/           # App types and extensions
│   ├── 00_extensions.sql
│   └── 01_types.sql
├── 10_tables/               # Table definitions
│   ├── contact.sql
│   └── organization.sql
├── 20_helpers/              # Trinity helper functions
│   ├── contact_helpers.sql
│   └── organization_helpers.sql
└── 30_functions/            # Business logic functions
    ├── create_contact.sql
    ├── update_contact.sql
    └── qualify_lead.sql
```

### How It Works

- **Numbers**: Multiples of 10 (00, 10, 20, 30)
- **Depth**: Single level (flat)
- **Naming**: `{entity_name}.sql` or `{action_name}.sql`
- **Order**: Executed in numerical order by Confiture

### Example Output

```bash
# Generate with decimal system (default)
specql generate entities/contact.yaml

# Creates:
db/schema/10_tables/contact.sql
db/schema/20_helpers/contact_helpers.sql
db/schema/30_functions/create_contact.sql
db/schema/30_functions/qualify_lead.sql
```

### Activation

**Automatic** - This is the default system:

```python
# Default CLI orchestrator uses decimal system
orchestrator = CLIOrchestrator()

# Or explicitly
orchestrator = CLIOrchestrator(output_format="confiture")
```

## System 2: Hexadecimal System (Enterprise-Scale)

### When to Use

✅ **Enterprise-scale projects** (100+ entities)
✅ **Multiple domains and subdomains**
✅ **Strict naming conventions required**
✅ **Large team coordination**
✅ **Registry-based organization**

### Table Code Format

**6-character hexadecimal code**: `SSDGGE`

| Position | Component | Range | Description | Example |
|----------|-----------|-------|-------------|---------|
| **0-1** | Schema layer | 01-03 | Write side, read side, analytics | `01` = write_side |
| **2** | Domain | 0-F | Business domain | `3` = catalog |
| **3** | Entity group | 0-F | Related entities | `2` = manufacturer group |
| **4** | Entity | 0-F | Specific entity | `1` = manufacturer |
| **5** | File sequence | 0-F | File within entity | `1` = first file |

### Directory Structure

```
db/schema/
├── 01_write_side/                           # Schema layer (01)
│   ├── 011_core/                            # Domain 1 (11)
│   │   └── 0111_user/                       # Group 1 (111)
│   │       └── 01111_user/                  # Entity 1 (1111)
│   │           └── 011111_tb_user.sql       # File 1 (11111)
│   └── 013_catalog/                         # Domain 3 (13)
│       └── 0132_manufacturer/               # Group 2 (132)
│           └── 01321_manufacturer/          # Entity 1 (1321)
│               ├── 013211_tb_manufacturer.sql
│               ├── 013212_fn_manufacturer.sql
│               └── 013213_vw_manufacturer.sql
├── 02_read_side/                            # Read models (02)
└── 03_analytics/                            # Analytics (03)
```

### Registry Configuration

Requires a domain registry file:

```yaml
# registry/domain_registry.yaml
domains:
  core:
    code: "1"
    description: "Core business entities"
    groups:
      user:
        code: "1"
        entities:
          user:
            code: "1"
            description: "User account"

  catalog:
    code: "3"
    description: "Product catalog"
    groups:
      manufacturer:
        code: "2"
        entities:
          manufacturer:
            code: "1"
            description: "Product manufacturer"
```

### Activation

Requires explicit registry mode:

```python
# Use registry-based hexadecimal system
orchestrator = CLIOrchestrator(use_registry=True)
```

## Migration Between Systems

### From Decimal to Hexadecimal

**When**: Project grows beyond 50 entities

**Steps**:
1. Create domain registry (`registry/domain_registry.yaml`)
2. Assign codes to existing entities
3. Regenerate with `use_registry=True`
4. Update Confiture migration scripts

**Migration preserves**:
- ✅ All business logic
- ✅ Data integrity
- ✅ Function signatures
- ❌ File paths (new structure)

### From Hexadecimal to Decimal

**When**: Simplifying enterprise project

**Steps**:
1. Switch orchestrator to default mode
2. Regenerate all entities
3. Update migration scripts
4. Remove registry configuration

## Code Examples

### Decimal System (Default)

```python
from specql.cli.orchestrator import CLIOrchestrator

# Simple decimal system
orchestrator = CLIOrchestrator()

# Generate contact entity
orchestrator.generate_entity({
    'entity': 'Contact',
    'schema': 'crm',
    'fields': {
        'email': 'email!',
        'name': 'text!'
    }
})

# Output structure:
# db/schema/10_tables/contact.sql
# db/schema/20_helpers/contact_helpers.sql
# db/schema/30_functions/create_contact.sql
```

### Hexadecimal System (Registry)

```python
from specql.cli.orchestrator import CLIOrchestrator

# Registry-based hexadecimal system
orchestrator = CLIOrchestrator(use_registry=True)

# Requires registry configuration
registry = {
    'domains': {
        'crm': {
            'code': '1',
            'groups': {
                'contact': {
                    'code': '1',
                    'entities': {
                        'contact': {'code': '1'}
                    }
                }
            }
        }
    }
}

orchestrator.generate_entity({
    'entity': 'Contact',
    'schema': 'crm',
    'fields': {
        'email': 'email!',
        'name': 'text!'
    }
}, registry=registry)

# Output structure:
# db/schema/01_write_side/011_crm/0111_contact/01111_contact/011111_tb_contact.sql
```

## File Naming Conventions

### Decimal System

| Directory | Pattern | Example |
|-----------|---------|---------|
| `00_foundation/` | `{number}_{description}.sql` | `00_extensions.sql` |
| `10_tables/` | `{entity}.sql` | `contact.sql` |
| `20_helpers/` | `{entity}_helpers.sql` | `contact_helpers.sql` |
| `30_functions/` | `{action}.sql` | `create_contact.sql` |

### Hexadecimal System

| Directory | Pattern | Example |
|-----------|---------|---------|
| All | `{full_code}_{type}_{name}.sql` | `011111_tb_contact.sql` |

**Code components**:
- `011111` = Full 6-character code
- `tb` = Type (tb=table, fn=function, vw=view)
- `contact` = Entity name

## Performance Considerations

### Decimal System
- **Fast generation**: Simple directory structure
- **Quick navigation**: Flat hierarchy
- **Confiture optimized**: Native migration support

### Hexadecimal System
- **Scalable**: Supports thousands of entities
- **Organized**: Domain-driven structure
- **Registry overhead**: Additional configuration management

## Best Practices

### Choosing Your System

**Start with Decimal** if:
- Project has < 50 entities
- Team prefers simplicity
- Using Confiture for migrations
- Fast prototyping needed

**Use Hexadecimal** if:
- Project will exceed 100 entities
- Multiple business domains
- Strict governance required
- Large distributed team

### Migration Timing

**Migrate early** when:
- Entity count approaches 50
- Multiple domains emerge
- Governance requirements increase

**Consider migration** when:
- File organization becomes confusing
- Team coordination suffers
- New domain additions needed

### Registry Management

**For Hexadecimal systems**:
- Maintain registry as code
- Version control registry changes
- Document code assignment strategy
- Plan for domain growth

## Troubleshooting

### "Registry not found" Error

```python
# Ensure registry exists for hexadecimal mode
orchestrator = CLIOrchestrator(use_registry=True)
# Requires: registry/domain_registry.yaml
```

### Code Conflicts

```yaml
# Avoid duplicate codes in registry
domains:
  crm:
    code: "1"    # ✅ Unique
  sales:
    code: "1"    # ❌ Conflict!
```

### Migration Issues

```bash
# When switching systems, regenerate all
rm -rf db/schema/
specql generate entities/*.yaml

# Update Confiture configuration
# (System-specific migration scripts)
```

## Complete Examples

### Simple CRM (Decimal System)

**Registry**: None (default)

**Structure**:
```
db/schema/
├── 00_foundation/
├── 10_tables/
│   ├── contact.sql
│   └── organization.sql
├── 20_helpers/
└── 30_functions/
```

**Configuration**:
```bash
# Just generate - uses decimal by default
specql generate entities/crm/*.yaml
```

### Enterprise Platform (Hexadecimal System)

**Registry**:
```yaml
domains:
  identity:
    code: "1"
    groups:
      user:
        code: "1"
        entities:
          user: {code: "1"}
          profile: {code: "2"}

  commerce:
    code: "2"
    groups:
      product:
        code: "1"
        entities:
          product: {code: "1"}
          category: {code: "2"}
```

**Structure**:
```
db/schema/
├── 01_write_side/
│   ├── 011_identity/
│   │   └── 0111_user/
│   │       ├── 01111_user/
│   │       └── 01112_profile/
│   └── 012_commerce/
│       └── 0121_product/
└── 02_read_side/
```

## Technical Details

### Implementation Files

- **Decimal**: `src/cli/orchestrator.py` (lines 197-283)
- **Hexadecimal**: `src/numbering/registry.py`
- **Tests**: `tests/unit/cli/test_numbering_systems.py` (21 tests)

### Verification Status

- ✅ **Decimal System**: 111 tests passing
- ✅ **Hexadecimal System**: 111 tests passing
- ✅ **Coexistence**: Both systems tested together
- ✅ **Migration**: Verified conversion paths

## Next Steps

- **Read Architecture Verification**: Technical details in `docs/architecture/NUMBERING_SYSTEMS_VERIFICATION.md`
- **Check Generated Patterns**: File structures in `docs/reference/generated-patterns.md`
- **Browse Examples**: See both systems in `examples/`
- **Generate Code**: Try `specql generate --help` for options

---

**Two systems, one codebase. Choose what fits your scale.** ⚖️