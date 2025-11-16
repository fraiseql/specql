# Coverage Analysis Example

## Command

```bash
specql reverse-tests generated_tests/test_contact_*.sql --analyze-coverage --preview
```

## Output

```bash
📊 Coverage Analysis for Contact Entity

✅ Well Covered (90-100%):
  • Table structure (100%) - 5/5 scenarios
  • Basic CRUD operations (95%) - 18/19 scenarios
  • Primary key constraints (100%) - 3/3 scenarios
  • qualify_lead action happy path (100%) - 4/4 scenarios

⚠️ Partially Covered (50-89%):
  • Error handling (60%) - 7/10 scenarios
    Missing: Invalid email format test
    Missing: Null email test
  • State transitions (70%) - 3/5 scenarios
    Missing: Reverse transition tests

❌ Not Covered (0-49%):
  • Concurrent updates - 0/5 scenarios
  • Bulk operations - 0/3 scenarios
  • Permission edge cases - 0/4 scenarios

📝 Suggested Tests:
  1. test_create_contact_invalid_email
  2. test_create_contact_null_email
  3. test_qualify_already_qualified_contact
  4. test_concurrent_contact_updates
  5. test_bulk_contact_creation

Coverage Score: 78% (43/55 potential scenarios)
```

## Detailed Analysis

### Coverage Matrix

| Category | pgTAP Tests | pytest Tests | Total | % |
|----------|-------------|--------------|-------|---|
| Structure | 10/10 | 0/10 | 10/10 | 100% |
| CRUD Create | 5/7 | 2/7 | 7/7 | 100% |
| CRUD Read | 2/3 | 1/3 | 3/3 | 100% |
| CRUD Update | 3/5 | 1/5 | 4/5 | 80% |
| CRUD Delete | 3/4 | 1/4 | 4/4 | 100% |
| Actions | 9/11 | 2/11 | 11/11 | 100% |
| Edge Cases | 2/8 | 1/8 | 3/8 | 38% |
| Integration | 0/5 | 3/5 | 3/5 | 60% |
| **Total** | **34/53** | **11/53** | **45/53** | **85%** |

### Gap Analysis

#### Critical Gaps (High Priority)

##### 1. Error Handling - Invalid Email Format
**Impact**: High - Data integrity
**Current**: 0 tests
**Recommended**: 3 tests
- `test_create_contact_invalid_email_format`
- `test_create_contact_malformed_email`
- `test_update_contact_email_validation`

**Example test**:
```sql
SELECT throws_ok(
    $$SELECT app.create_contact(
        '01232122-0000-0000-2000-000000000001'::UUID,
        '01232122-0000-0000-2000-000000000002'::UUID,
        '{"email": "not-an-email", "first_name": "Test", "last_name": "User", "status": "lead"}'::JSONB
    )$$,
    'invalid_email',
    'Invalid email should be rejected'
);
```

##### 2. Concurrent Update Handling
**Impact**: High - Data consistency
**Current**: 0 tests
**Recommended**: 2 tests
- `test_concurrent_contact_updates`
- `test_optimistic_locking`

##### 3. Permission Validation
**Impact**: Medium - Security
**Current**: 1/4 tests
**Recommended**: 3 tests
- `test_cross_tenant_access_denied`
- `test_insufficient_permissions`
- `test_admin_override`

#### Medium Priority Gaps

##### 4. Bulk Operations
**Impact**: Medium - Performance
**Current**: 0 tests
**Recommended**: 2 tests
- `test_bulk_contact_import`
- `test_bulk_contact_update`

##### 5. Edge Cases
**Impact**: Low - Robustness
**Current**: 2/8 tests
**Recommended**: 6 tests
- `test_contact_with_minimum_data`
- `test_contact_with_all_fields`
- `test_unicode_characters`
- `test_special_characters`
- `test_max_length_fields`
- `test_timezone_handling`

### Recommendations

#### Immediate Actions (Next Sprint)
1. **Add email validation tests** - Critical for data integrity
2. **Implement concurrent update tests** - Prevents race conditions
3. **Add permission tests** - Security compliance

#### Medium-term Improvements
1. **Bulk operation tests** - Performance validation
2. **Edge case coverage** - Robustness improvements
3. **Integration test expansion** - End-to-end coverage

#### Long-term Goals
1. **100% coverage target** - Comprehensive test suite
2. **Performance benchmarking** - Load testing
3. **Security audit tests** - Compliance validation

### Test Generation Suggestions

Based on the gaps identified, here are the recommended tests to generate:

```bash
# Generate missing validation tests
specql generate-tests entities/contact.yaml \
    --focus validation \
    --output-dir tests/validation/

# Generate concurrent update tests
specql generate-tests entities/contact.yaml \
    --focus concurrency \
    --output-dir tests/concurrency/

# Generate permission tests
specql generate-tests entities/contact.yaml \
    --focus security \
    --output-dir tests/security/
```

### Coverage Trends

```
Current Coverage: 78%
Target Coverage:  95%

Month 1: 78% → 85% (Add validation tests)
Month 2: 85% → 90% (Add concurrency tests)
Month 3: 90% → 95% (Add bulk operation tests)
```

### Quality Metrics

- **Test Density**: 55 tests / 380 lines = 0.14 tests per line
- **Coverage Efficiency**: 78% coverage / 55 tests = 1.4% coverage per test
- **Gap Density**: 12 missing scenarios / 55 total scenarios = 22% gaps

### Next Steps

1. **Prioritize gaps** by business impact
2. **Generate missing tests** using SpecQL
3. **Review and merge** generated tests
4. **Re-run analysis** to verify improvements
5. **Set up monitoring** for coverage regression

---

*Analysis generated: 2025-11-20 | SpecQL v0.5.0-beta*