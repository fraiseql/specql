# Validation

> **Status**: 🚧 Documentation in Progress
>
> This page is planned but not yet complete. Check back soon!

## Overview

This guide will explain how SpecQL handles data validation, including field-level constraints, business rule validation in actions, and custom validation logic.

## Coming Soon

This documentation will cover:
- [ ] Field-level validation (email, phone, URL formats)
- [ ] Rich type validation (money, dimensions, etc.)
- [ ] Enum and constraint validation
- [ ] Action-level validation with `validate:` steps
- [ ] Custom validation functions
- [ ] Error messages and user feedback
- [ ] Multi-field validation rules

## Related Documentation

- [Rich Types](../03_core-concepts/rich-types.md) - Built-in validation types
- [Actions](../03_core-concepts/actions.md) - Action validation steps
- [Error Handling](../05_guides/error-handling.md) - Handling validation errors

## Quick Reference (Interim)

### Field Validation

SpecQL provides automatic validation for rich types:

```yaml
entity: Contact
fields:
  email: email!           # Auto-validates email format (RFC 5322)
  phone: phoneNumber      # Auto-validates E.164 format
  website: url            # Auto-validates URL format
  age: integer!           # Auto-validates integer type
```

### Action Validation

Use the `validate:` step in actions for business rules:

```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
        error: "Only leads can be qualified"

      - validate: email IS NOT NULL
        error: "Email required for qualification"

      - update: Contact SET status = 'qualified'
```

### Enum Validation

Enums are automatically validated at the database level:

```yaml
fields:
  status: enum(lead, qualified, customer) = 'lead'
```

This generates:
```sql
CONSTRAINT chk_contact_status
  CHECK (status IN ('lead', 'qualified', 'customer'))
```

## Questions?

If you need this documentation urgently, please:
- Check [Rich Types](../03_core-concepts/rich-types.md) for validation types
- Check [Actions](../03_core-concepts/actions.md) for validation steps
- Check [Error Handling](../05_guides/error-handling.md) for error patterns
- Open an issue on GitHub

---

*Last Updated*: 2025-11-20
