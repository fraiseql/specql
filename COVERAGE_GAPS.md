# Coverage Gaps Analysis

## service_generator.py (85% → 95%)

**Missing Lines**:
- Lines 181-184: Error handling for invalid action steps
- Lines 191: Validation step without expression
- Lines 210: Update step without fields
- Lines 224-236: IF step generation logic
- Lines 246: Default condition handling in expression parsing
- Lines 258: Expression parsing fallback
- Lines 269-270: Enum value formatting in complex cases
- Lines 272-275: Boolean and other value formatting
- Lines 284: Pascal case conversion

**Tests to Add**:
1. test_service_with_invalid_action_step
2. test_service_with_validation_without_expression
3. test_service_with_update_without_fields
4. test_service_with_if_step
5. test_service_expression_parsing_edge_cases
6. test_service_value_formatting_edge_cases

## repository_generator.py (91% → 95%)

**Missing Lines**:
- Lines 84-88: Unique field query methods generation
- Lines 156-160: Reference field type mapping error handling

**Tests to Add**:
1. test_repository_with_unique_fields
2. test_repository_reference_field_error_handling

## entity_generator.py (96% → 98%)

**Missing Lines**:
- Lines 93: Reference field validation error
- Lines 188: Reference field type mapping error
- Lines 203: Text field default value formatting
- Lines 207: Other field default value formatting

**Tests to Add**:
1. test_entity_reference_field_validation
2. test_entity_default_value_formatting

## enum_generator.py (94% → 98%)

**Missing Lines**:
- Lines 13: Non-enum field validation

**Tests to Add**:
1. test_enum_generator_with_non_enum_field

## spring_boot_parser.py (80% → 90%)

**Missing Lines**:
- Lines 66-68: File parsing exception handling
- Lines 85: Class parsing error
- Lines 184-212: Field conversion logic (old format compatibility)

**Tests to Add**:
1. test_parser_file_exception_handling
2. test_parser_missing_class_error
3. test_parser_field_conversion_compatibility

## Summary

**Current Coverage**: 91%
**Target Coverage**: 95%+
**Missing Tests**: ~12 tests needed
**Estimated Effort**: 4-6 hours

### Priority Order:
1. service_generator.py (most complex, 21 missing lines)
2. spring_boot_parser.py (parser reliability, 17 missing lines)
3. repository_generator.py (6 missing lines)
4. entity_generator.py (4 missing lines)
5. enum_generator.py (1 missing line)