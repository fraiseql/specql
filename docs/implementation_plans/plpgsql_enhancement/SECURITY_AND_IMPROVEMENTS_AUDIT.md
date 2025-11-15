# PL/pgSQL Security & Improvements Audit

**Date**: 2025-01-15
**Status**: 🔍 **AUDIT COMPLETE**
**Scope**: PL/pgSQL parser, generator, and action compilers

---

## Executive Summary

Comprehensive security audit of PL/pgSQL implementation reveals:
- ✅ **Parser**: SECURE - All database queries use parameterized queries
- ⚠️ **Action Compilers**: HIGH SEVERITY SQL injection vulnerabilities found
- ⚠️ **Error Handling**: MEDIUM SEVERITY information disclosure in error messages
- 💡 **FK Naming**: Inconsistency between `fk_entity` and `{entity}_id` patterns

---

## 🚨 HIGH SEVERITY: SQL Injection Vulnerabilities

### Issue 1: Unsafe String Formatting in Insert Compiler

**Location**: `src/generators/actions/step_compilers/insert_compiler.py:88-98`

**Vulnerable Code**:
```python
def _format_value(self, value: Any) -> str:
    """Format value for SQL"""
    if isinstance(value, str):
        if value.startswith("$"):
            # Variable reference
            return f"v_{value[1:]}"
        else:
            # String literal - VULNERABLE!
            return f"'{value}'"  # ❌ NO ESCAPING
    else:
        return str(value)
```

**Vulnerability**:
- String values are directly wrapped in single quotes without escaping
- Allows SQL injection via user input containing single quotes
- Example exploit: `value = "test'; DROP TABLE users; --"`

**Impact**:
- **CRITICAL** - Full SQL injection
- Allows arbitrary SQL execution
- Data exfiltration, modification, or destruction possible

**Fix Required**:
```python
def _format_value(self, value: Any) -> str:
    """Format value for SQL"""
    if isinstance(value, str):
        if value.startswith("$"):
            # Variable reference
            return f"v_{value[1:]}"
        else:
            # String literal - FIXED with proper escaping
            from src.generators.sql_utils import SQLUtils
            escaped = SQLUtils.escape_string_literal(value)
            return f"'{escaped}'"
    else:
        return str(value)
```

**Timeline**: ⏰ **IMMEDIATE**
**Effort**: 2 hours
**Priority**: 🔥 **CRITICAL**

---

### Issue 2: Unsafe String Formatting in Database Operation Compiler

**Location**: `src/generators/actions/database_operation_compiler.py:152-157`

**Vulnerable Code**:
```python
def _format_value(self, value: str) -> str:
    """Format value for SQL SET clause"""
    # If it's a string literal, wrap in quotes
    if isinstance(value, str) and not value.startswith("'"):
        return f"'{value}'"  # ❌ NO ESCAPING
    return str(value)
```

**Vulnerability**: Same as Issue 1 - no escaping of single quotes

**Impact**: **CRITICAL** - SQL injection in UPDATE/SET clauses

**Fix Required**:
```python
def _format_value(self, value: str) -> str:
    """Format value for SQL SET clause"""
    if isinstance(value, str) and not value.startswith("'"):
        from src.generators.sql_utils import SQLUtils
        escaped = SQLUtils.escape_string_literal(value)
        return f"'{escaped}'"
    return str(value)
```

**Timeline**: ⏰ **IMMEDIATE**
**Effort**: 2 hours
**Priority**: 🔥 **CRITICAL**

---

## ⚠️ MEDIUM SEVERITY: Information Disclosure in Error Messages

### Issue 3: Error Messages Expose Internal Details

**Location**: `templates/sql/app_wrapper.sql.j2:40-49`

**Vulnerable Code**:
```sql
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)  -- ❌ EXPOSING INTERNALS
        )::{{ composite_type_name }};
```

**Vulnerability**:
- `SQLERRM` and `SQLSTATE` exposed to end users
- Reveals internal database structure, table names, column names
- Aids attackers in reconnaissance and exploitation

**Impact**:
- **MEDIUM** - Information disclosure
- Assists in SQL injection attacks
- Reveals implementation details
- May expose sensitive data in error messages

**Fix Required**:
```sql
EXCEPTION
    WHEN OTHERS THEN
        -- Log detailed error server-side
        RAISE WARNING 'Unexpected error in %: % (SQLSTATE: %)',
            '{{ core_function_name }}', SQLERRM, SQLSTATE;

        -- Return generic error to client
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred. Please contact support.',
            NULL::JSONB,
            jsonb_build_object('error_id', gen_random_uuid())  -- ✅ Safe error ID for tracking
        )::{{ composite_type_name }};
```

**Additional Recommendation**: Implement server-side error logging with correlation IDs

**Timeline**: ⏰ **Within 1 week**
**Effort**: 8 hours (includes testing and error tracking implementation)
**Priority**: ⚠️ **HIGH**

---

## 💡 IMPROVEMENT: FK Naming Convention Inconsistency

### Issue 4: Mixed Foreign Key Naming Patterns

**Locations**:
- `src/parsers/plpgsql/type_mapper.py:107-125`
- `src/parsers/plpgsql/pattern_detector.py:177-185`

**Current Behavior**:
The parser supports BOTH naming conventions:
1. `fk_entity` (explicit foreign key prefix)
2. `entity_id` (implicit foreign key suffix)

**Example Inconsistency**:
```sql
-- Pattern 1: fk_ prefix
CREATE TABLE tb_order (
    pk_order SERIAL PRIMARY KEY,
    fk_customer INTEGER REFERENCES tb_customer(pk_customer)
);

-- Pattern 2: _id suffix
CREATE TABLE tb_order (
    pk_order SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES tb_customer(pk_customer)
);
```

**Current Code**:
```python
def _is_foreign_key(self, column_name: str) -> bool:
    """Detect if column is likely a foreign key"""
    column_lower = column_name.lower()

    # fk_ prefix ✅
    if column_lower.startswith("fk_"):
        return True

    # *_id suffix (but not just 'id') ✅
    if column_lower.endswith("_id") and column_lower != "id":
        return True

    return False
```

**Analysis**:
- Parser correctly handles BOTH patterns ✅
- Generator should be consistent in what it produces
- Documentation should clarify preferred pattern

**Recommendation**:
1. **Keep parser flexible** - accept both `fk_entity` and `entity_id`
2. **Standardize generator output** - choose ONE pattern for consistency
3. **Document preferred pattern** in style guide

**Proposed Standard**: `fk_entity` (more explicit, clearer intent)

**Rationale**:
- More explicit about foreign key relationship
- Distinguishes from regular ID fields
- Aligns with `pk_entity` pattern for consistency
- Pattern: `pk_*` for primary keys, `fk_*` for foreign keys

**Timeline**: ⏰ **Within 2 weeks**
**Effort**: 12 hours (includes generator updates, tests, documentation)
**Priority**: 💡 **MEDIUM** (Improvement, not security issue)

---

## ✅ SECURE: PL/pgSQL Parser Implementation

### Parser Security Validation

**All database queries use parameterized queries** - ✅ SECURE

**Examples from `src/parsers/plpgsql/plpgsql_parser.py`**:

```python
# Line 114-129: Safe parameterized query
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = %s
    AND table_type = 'BASE TABLE'
""", (schema,))  # ✅ SAFE - parameterized

# Line 191: Safe parameterized query
cursor.execute(
    query,
    (schema, table_name),  # ✅ SAFE - parameterized
)

# Line 316-338: Safe parameterized query for foreign keys
cursor.execute(
    query,
    (schema, table_name),  # ✅ SAFE - parameterized
)
```

**Validation**:
- ✅ All cursor.execute() calls use tuple parameters
- ✅ No string interpolation in SQL queries
- ✅ No f-strings or .format() in SQL
- ✅ Follows PostgreSQL best practices

---

## 📋 Summary of Required Actions

| Issue | Severity | Location | Timeline | Effort |
|-------|----------|----------|----------|--------|
| SQL Injection - Insert Compiler | 🔥 CRITICAL | insert_compiler.py:96 | IMMEDIATE | 2h |
| SQL Injection - DB Operation Compiler | 🔥 CRITICAL | database_operation_compiler.py:154 | IMMEDIATE | 2h |
| Information Disclosure - Error Messages | ⚠️ HIGH | app_wrapper.sql.j2:40 | 1 week | 8h |
| FK Naming Convention | 💡 MEDIUM | Generator standardization | 2 weeks | 12h |

**Total Effort**: 24 hours (3 days)
**Critical Path**: SQL injection fixes (IMMEDIATE)

---

## 🔧 Implementation Plan

### Phase 1: Critical Security Fixes (Day 1)

**Hour 1-2: Fix Insert Compiler SQL Injection**
- Update `insert_compiler.py` to use `SQLUtils.escape_string_literal()`
- Add unit tests for SQL injection attempts
- Verify existing tests still pass

**Hour 3-4: Fix Database Operation Compiler SQL Injection**
- Update `database_operation_compiler.py` to use `SQLUtils.escape_string_literal()`
- Add unit tests for SQL injection attempts
- Verify existing tests still pass

**Deliverables**:
- Updated compilers with proper escaping
- New security test suite
- All existing tests passing

---

### Phase 2: Error Message Sanitization (Days 2-3)

**Day 2 (8 hours): Implement Safe Error Handling**

**Hour 1-3: Update Error Handling**
- Modify `app_wrapper.sql.j2` to sanitize errors
- Implement server-side error logging
- Add error correlation IDs

**Hour 4-6: Create Error Tracking System**
- Set up server-side error log table
- Create error lookup function
- Implement error reporting utilities

**Hour 7-8: Testing and Documentation**
- Test error scenarios
- Verify no sensitive data in client errors
- Document error handling approach

**Deliverables**:
- Sanitized error messages
- Server-side error logging
- Error tracking documentation

---

### Phase 3: FK Naming Standardization (Week 2)

**Day 1 (8 hours): Generator Standardization**

**Hour 1-3: Update Schema Generator**
- Standardize on `fk_entity` pattern
- Update `schema_generator.py`
- Add configuration option for FK pattern preference

**Hour 4-6: Update Tests**
- Update test expectations
- Add tests for both FK patterns (parser should accept both)
- Verify round-trip preservation

**Hour 7-8: Documentation**
- Document FK naming convention
- Add migration guide for existing schemas
- Update coding standards

**Deliverables**:
- Standardized FK generation
- Flexible FK parsing
- Comprehensive documentation

---

## 🧪 Security Test Suite Requirements

### New Tests Required

**File**: `tests/security/test_sql_injection_prevention.py`

```python
"""
Security tests for SQL injection prevention
"""

def test_insert_compiler_prevents_sql_injection():
    """Verify insert compiler escapes malicious input"""
    malicious_values = [
        "test'; DROP TABLE users; --",
        "'; SELECT * FROM users WHERE '1'='1",
        "O'Reilly",  # Legitimate apostrophe
        "It's a trap!",
    ]

    for value in malicious_values:
        # Compile insert with malicious value
        compiled_sql = insert_compiler.compile(value)

        # Verify value is properly escaped
        assert "DROP TABLE" not in compiled_sql
        assert "SELECT * FROM" not in compiled_sql
        # Verify apostrophes are doubled
        if "'" in value:
            assert "''" in compiled_sql

def test_database_operation_compiler_prevents_sql_injection():
    """Verify database operation compiler escapes malicious input"""
    # Similar tests for UPDATE statements
    pass

def test_error_messages_do_not_expose_internals():
    """Verify error messages don't leak sensitive information"""
    # Trigger various error conditions
    # Verify SQLERRM/SQLSTATE not in client response
    pass
```

**Timeline**: Create alongside fixes
**Effort**: 4 hours

---

## 📊 Impact Assessment

### Before Fixes

**Security Posture**: ⚠️ **VULNERABLE**
- 2 critical SQL injection vulnerabilities
- Information disclosure in error messages
- Potential for data breach or destruction

**Risk Level**: 🔥 **HIGH**
- Exploitable by attackers with basic SQL knowledge
- Could lead to complete database compromise

### After Fixes

**Security Posture**: ✅ **SECURE**
- All SQL injections patched
- Error messages sanitized
- Proper input validation throughout

**Risk Level**: ✅ **LOW**
- Defense in depth implemented
- Best practices followed
- Comprehensive test coverage

---

## 🎯 Recommendations

### Immediate Actions (This Week)
1. ✅ Fix SQL injection vulnerabilities in compilers
2. ✅ Add security test suite
3. ✅ Review all other generators for similar issues

### Short Term (2 Weeks)
1. ✅ Sanitize error messages
2. ✅ Implement error tracking system
3. ✅ Standardize FK naming convention
4. ✅ Document security practices

### Long Term (1 Month)
1. ✅ Security code review of entire codebase
2. ✅ Automated security scanning in CI/CD
3. ✅ Penetration testing of generated code
4. ✅ Security training for development team

---

## 📝 Additional Notes

### SQLUtils Already Provides Escaping

The `SQLUtils.escape_string_literal()` function is already implemented correctly:

```python
@staticmethod
def escape_string_literal(value: str) -> str:
    """Escape string for SQL literal"""
    # Escape single quotes by doubling them
    return value.replace("'", "''")
```

**This is the correct PostgreSQL escaping method** ✅

All fixes just need to **USE THIS EXISTING FUNCTION** - no new code needed!

---

## ✅ Conclusion

The PL/pgSQL **parser is secure**, but the **action compilers have critical vulnerabilities** that require immediate attention.

**Priority Order**:
1. 🔥 **FIX SQL INJECTIONS** (Immediate - 4 hours)
2. ⚠️ **SANITIZE ERRORS** (1 week - 8 hours)
3. 💡 **STANDARDIZE FK NAMING** (2 weeks - 12 hours)

**Total remediation time**: ~3 days of focused work

Once fixed, the PL/pgSQL implementation will have **production-grade security** suitable for enterprise deployments.

---

**Last Updated**: 2025-01-15
**Auditor**: Security Review Team
**Status**: Recommendations ready for implementation
