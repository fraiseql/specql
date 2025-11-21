# Translation Table Generator - Quick Reference

**Full Plan**: [TRANSLATION_TABLE_GENERATOR_PLAN.md](TRANSLATION_TABLE_GENERATOR_PLAN.md)

---

## 🎯 What This Implements

Auto-generate `tl_*` translation tables for i18n support in SpecQL entities.

**Input** (3 lines YAML):
```yaml
translations:
  enabled: true
  fields: [name, description]
```

**Output** (80+ lines SQL):
- Translation table with **Hybrid Trinity Pattern** (2 fields)
- Foreign key constraints
- Composite uniqueness (parent + locale)
- Translation field lookup helpers with locale fallback

---

## ✅ Key Requirements

### 1. **Hybrid Trinity Pattern** (CRITICAL!)
Translation tables use a **simplified 2-field pattern** (not full 3-field Trinity):

```sql
CREATE TABLE catalog.tl_manufacturer (
    -- Hybrid Trinity Pattern (2 fields)
    pk_manufacturer_translation INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    -- NO identifier field (computed virtually when needed)
    ...
);
```

**Why Hybrid?**
- Translation tables are **detail records**, not top-level entities
- Composite `(fk_parent, fk_locale)` already provides business uniqueness
- Identifier can be **computed** when needed for debugging
- Simpler schema, better matches PrintOptim

### 2. **Translation Field Helpers**
One helper per translatable field:

```sql
-- Returns translated name with locale fallback
CREATE FUNCTION catalog.get_manufacturer_name(
    p_manufacturer_pk UUID,
    p_locale_pk UUID DEFAULT NULL
) RETURNS TEXT AS $$ ... $$;
```

---

## 📊 6-Phase Implementation

| Phase | Description | Effort | Key Output |
|-------|-------------|--------|------------|
| **1** | Translation Table Generator | 3.5h | DDL with Hybrid Trinity |
| **2** | Helper Functions | 3.5h | `get_{entity}_{field}()` |
| **3** | Schema Orchestration | 4h | E2E integration |
| **4** | PrintOptim Compatibility | 3h | Pattern matching |
| **5** | Edge Cases & Polish | 5h | Validation, errors |

**Total**: ~19 hours (5 days @ 4h/day)

---

## 🚨 Common Pitfalls

### ❌ WRONG: UUID Primary Key
```sql
-- Wrong: UUID as PK (slow joins)
CREATE TABLE tl_manufacturer (
    pk_manufacturer_translation UUID PRIMARY KEY,  -- ❌ Should be INTEGER
    ...
);
```

### ❌ WRONG: Including Identifier Field
```sql
-- Wrong: Storing identifier (redundant!)
CREATE TABLE tl_manufacturer (
    pk_manufacturer_translation INTEGER PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,  -- ❌ Don't store, compute it!
    ...
);
```

### ✅ CORRECT: Hybrid Trinity Pattern
```sql
-- Correct: INTEGER PK + UUID (no identifier)
CREATE TABLE tl_manufacturer (
    pk_manufacturer_translation INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    -- No identifier field ✅
    fk_manufacturer UUID NOT NULL,
    fk_locale UUID NOT NULL,
    ...
    CONSTRAINT tl_manufacturer_uniq UNIQUE (fk_manufacturer, fk_locale)
);
```

### ✅ CORRECT: Virtual Identifier (when needed)
```sql
-- For debugging: compute identifier via JOIN
SELECT
    t.pk_manufacturer_translation,
    parent.identifier || '.' || locale.code as virtual_identifier,
    t.name
FROM tl_manufacturer t
JOIN tb_manufacturer parent ON t.fk_manufacturer = parent.pk_manufacturer
JOIN tb_locale locale ON t.fk_locale = locale.pk_locale;
```

---

## 📝 Test Checklist

```python
def test_translation_table_hybrid_trinity():
    """CRITICAL: Verify Hybrid Trinity pattern (2 fields, no identifier)"""
    ddl = generator.generate(entity)

    # Must have INTEGER PK + UUID
    assert "pk_manufacturer_translation INTEGER PRIMARY KEY" in ddl
    assert "id UUID UNIQUE NOT NULL" in ddl

    # Must NOT have identifier field
    assert "identifier TEXT" not in ddl

    # Must have composite uniqueness
    assert "CONSTRAINT tl_manufacturer_uniq UNIQUE (fk_manufacturer, fk_locale)" in ddl

def test_translation_field_helpers():
    """CRITICAL: Verify translation field helpers exist"""
    helpers = generator.generate(entity)

    # Must generate field lookup helpers
    assert "CREATE FUNCTION catalog.get_manufacturer_name" in helpers
    assert "COALESCE(p_locale_pk, catalog.get_default_locale())" in helpers
    assert "FROM catalog.tl_manufacturer" in helpers
```

---

## 🎯 Success Metrics

- ✅ Hybrid Trinity (2 fields: INTEGER PK + UUID)
- ✅ No identifier field (neither stored nor virtual)
- ✅ Translation field helpers use locale fallback
- ✅ Compatible with existing SpecQL patterns
- ✅ Simpler than PrintOptim (INTEGER PK vs UUID)
- ✅ Minimal complexity (no extra helper functions)
- ✅ 100% test coverage
- ✅ No breaking changes

---

## 📚 Related Documentation

- [Trinity Pattern](../03_core-concepts/trinity-pattern.md) - Why 3 identities?
- [Translation Table Plan](TRANSLATION_TABLE_GENERATOR_PLAN.md) - Full implementation
- [SpecQL YAML Syntax](../06_reference/yaml-syntax.md) - translations config

---

**Last Updated**: 2025-11-21
**Status**: Ready for Implementation
**Approach**: Hybrid Trinity Pattern (2 fields only - no identifier at all)
**Estimated Completion**: 19 hours over 5 days
