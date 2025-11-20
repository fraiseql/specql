# Validation Guide

> **Status**: 🚧 Documentation in Progress

## Overview

Complete guide to data validation in SpecQL, from field-level to action-level validation.

## Coming Soon

- Field validation with rich types
- Custom validation rules
- Action validation steps
- Error messages and user feedback

## Quick Reference

```yaml
# Field validation
entity: Contact
fields:
  email: email!  # Built-in validation

# Action validation
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
        error: "Only leads can be qualified"
```

## Related Documentation

### Core Concepts
- [Rich Types](../03_core-concepts/rich-types.md) - Built-in validation types
- [Actions](../03_core-concepts/actions.md) - Declarative business logic with validation
- [Business YAML](../03_core-concepts/business-yaml.md) - Validation in YAML syntax

### Guides
- [Error Handling](error-handling.md) - User-friendly error messages
- [Your First Action](../01_getting-started/first-action.md) - Validation in practice
- [Multi-Tenancy](multi-tenancy.md) - Validation across tenants

### Reference
- [Rich Types Reference](../06_reference/rich-types-reference.md) - All validation types
- [Action Steps Reference](../06_reference/action-steps-reference.md) - Validation steps
- [YAML Syntax](../06_reference/yaml-syntax.md) - Validation syntax

### Advanced
- [Custom Patterns](../07_advanced/custom-patterns.md) - Reusable validation patterns
- [Security Hardening](../07_advanced/security-hardening.md) - Input validation security

---

*Last Updated*: 2025-11-20
