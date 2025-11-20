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

## Related

- [Multi-Tenancy Guide](../05_guides/multi-tenancy.md)
- [Business YAML](../03_core-concepts/business-yaml.md)

---

*Last Updated*: 2025-11-20
