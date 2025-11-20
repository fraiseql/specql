# Schema Registry Reference

> **Status**: 🚧 Documentation in Progress

## Overview

Reference for the schema registry configuration (registry/domain_registry.yaml).

## Coming Soon

- Registry YAML format
- Multi-tenant schema configuration
- Shared schema patterns
- Schema organization best practices

## Quick Example

```yaml
# registry/domain_registry.yaml
schemas:
  multi_tenant:
    - crm
    - projects
  shared:
    - catalog
    - analytics
```

## Related Documentation

### Guides
- [Multi-Tenancy Guide](../05_guides/multi-tenancy.md) - Schema tier configuration
- [Relationships Guide](../05_guides/relationships.md) - Cross-schema relationships
- [Migration Guide](../02_migration/index.md) - Schema migration patterns

### Core Concepts
- [Business YAML](../03_core-concepts/business-yaml.md) - Schema definition syntax
- [Trinity Pattern](../03_core-concepts/trinity-pattern.md) - Schema naming conventions

### Reference
- [YAML Syntax](yaml-syntax.md) - Complete schema syntax
- [CLI Commands](cli-commands.md) - Schema management commands

### Advanced
- [Security Hardening](../07_advanced/security-hardening.md) - Schema security
- [Performance Tuning](../07_advanced/performance-tuning.md) - Schema optimization

---

*Last Updated*: 2025-11-20
