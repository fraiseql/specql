# Migration Guide: Underscore to Dot Hierarchy Separator

## Summary

Default hierarchy separator changed from `_` to `.` in version X.Y.Z.

## Impact

**Low** - Explicit override available, existing data unaffected.

## For Existing Entities

### Option 1: Keep Underscore (Explicit Override)

```yaml
identifier:
  separator: "_"  # Maintain old behavior
```

### Option 2: Migrate to Dot (Recommended)

1. Update SpecQL YAML (remove explicit `separator: "_"`)
2. Regenerate functions
3. Run identifier recalculation
4. Update any hardcoded identifier strings

## For New Entities

No action needed - dot separator is now default.

## Examples

**Before**:
```
acme-corp|warehouse_floor1_room101
```

**After**:
```
acme-corp|warehouse.floor1.room101
```
