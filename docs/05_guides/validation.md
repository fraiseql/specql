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

## Related

- [Rich Types](../03_core-concepts/rich-types.md)
- [Actions](../03_core-concepts/actions.md)
- [Error Handling](error-handling.md)

---

*Last Updated*: 2025-11-20
