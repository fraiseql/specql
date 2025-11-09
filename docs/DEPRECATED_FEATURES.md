# Deprecated Features

This document tracks features that have been deprecated and removed.

## Hierarchical Identifier Underscore Separator

**Deprecated**: 2024-Q4
**Removed**: 2025-11-09
**Reason**: Dot separator is more readable and standard

**Old Format**:
```
tenant_ACME_location_NYC
```

**New Format**:
```
tenant.ACME.location.NYC
```

**Migration**: No migration needed - new entities use dot separator by default.

## Strip Tenant Prefix

**Status**: Never implemented
**Removed**: 2025-11-09
**Reason**: Feature was planned but never needed

**Original Idea**: Strip redundant tenant prefixes from composite identifiers
**Decision**: Not needed - identifiers work fine with tenant prefix

## Test Files Archived

The following test files have been moved to `tests/archived/`:
- `test_backward_compatibility.py` - Underscore separator tests
- `test_identifier_hierarchical_dot.py` - Hierarchical dot separator tests
- `test_strip_tenant_prefix.py` - Strip tenant prefix tests

These can be permanently deleted after 6 months (2025-05-09).