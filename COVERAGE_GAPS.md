# Coverage Gaps Analysis - Rust Integration

## Current Coverage: 87% (Target: 95%+)

Generated from pytest coverage report on Rust integration tests.

## handler_generator.py (89% → 95%)

**Missing Lines**: 210-212, 217-230 (5 lines)

**Analysis**:
- Lines 210-212: `generate_route_imports()` method - generates Actix Web route imports
- Lines 217-230: `generate_routes_file()` method - generates complete routes.rs file

**Tests to Add**:
1. `test_generate_route_imports` - Test route import generation
2. `test_generate_routes_file` - Test complete routes file generation
3. `test_route_config_with_complex_entity` - Test route config for entities with complex names

## model_generator.py (91% → 95%)

**Missing Lines**: 97, 101, 105, 161, 204-205, 261-262, 280, 389-390, 399 (12 lines)

**Analysis**:
- Line 97: BigDecimal import logic in `_generate_imports()`
- Line 101: serde_json import logic
- Line 105: Serde import logic
- Line 161: Foreign key field name generation in `_generate_field_line()`
- Lines 204-205: Field comment generation
- Lines 261-262: Model struct generation
- Line 280: Insertable struct generation
- Lines 389-390: New struct generation
- Line 399: Update struct generation

**Tests to Add**:
1. `test_imports_with_bigdecimal` - Test BigDecimal import generation
2. `test_imports_with_serde_json` - Test serde_json import generation
3. `test_imports_with_serde` - Test Serde import generation
4. `test_foreign_key_field_naming` - Test FK field name generation
5. `test_field_comments` - Test field comment generation
6. `test_model_struct_generation` - Test complete model struct
7. `test_insertable_struct_generation` - Test Insertable derive
8. `test_new_struct_generation` - Test New* struct generation
9. `test_update_struct_generation` - Test Update* struct generation

## diesel_table_generator.py (94% → 98%)

**Missing Lines**: 119, 221-227 (5 lines)

**Analysis**:
- Line 119: Table name generation logic
- Lines 221-227: Complex table definition generation

**Tests to Add**:
1. `test_table_name_generation` - Test table name generation
2. `test_complex_table_definition` - Test complex table definitions

## diesel_type_mapper.py (85% → 95%)

**Missing Lines**: 64, 92, 182, 190, 196, 202, 230-249, 282 (11 lines)

**Analysis**:
- Line 64: UUID type mapping
- Line 92: Array type mapping
- Line 182: Jsonb type mapping
- Lines 190, 196, 202: Advanced type mappings
- Lines 230-249: Complex type conversion logic
- Line 282: Error handling in type mapping

**Tests to Add**:
1. `test_uuid_type_mapping` - Test UUID field type mapping
2. `test_array_type_mapping` - Test PostgreSQL array types
3. `test_jsonb_type_mapping` - Test JSONB type mapping
4. `test_advanced_type_conversions` - Test complex type conversions
5. `test_type_mapping_error_handling` - Test error handling

## query_generator.py (70% → 90%)

**Missing Lines**: 187-194, 214-221, 241-257, 266-270, 273, 293 (27 lines)

**Analysis**:
- Lines 187-194: Complex query generation
- Lines 214-221: Join query logic
- Lines 241-257: Filter query generation
- Lines 266-270: Sort query logic
- Line 273: Pagination logic
- Line 293: Error handling

**Tests to Add**:
1. `test_complex_query_generation` - Test complex query building
2. `test_join_query_logic` - Test join operations
3. `test_filter_query_generation` - Test filter clauses
4. `test_sort_query_logic` - Test ordering
5. `test_pagination_logic` - Test pagination
6. `test_query_error_handling` - Test error scenarios

## diesel_parser.py (81% → 90%)

**Missing Lines**: 52, 57-59, 63, 98-100, 103, 107-109, 192, 209-219 (21 lines)

**Analysis**:
- Line 52: Error when no Diesel model found
- Lines 57-59: Schema entity matching logic
- Line 63: Schema merging logic
- Lines 98-100: Model parsing logic
- Lines 103, 107-109: Field parsing
- Line 192: Schema parsing
- Lines 209-219: Error recovery and validation

**Tests to Add**:
1. `test_no_diesel_model_error` - Test error when no model found
2. `test_schema_entity_matching` - Test schema/model matching
3. `test_schema_merging` - Test schema information merging
4. `test_model_parsing_edge_cases` - Test model parsing edge cases
5. `test_field_parsing_variations` - Test field parsing variations
6. `test_schema_parsing` - Test schema file parsing
7. `test_parser_error_recovery` - Test error recovery
8. `test_parser_validation` - Test input validation

## Summary

**Total Missing Lines**: 81
**Files to Improve**: 6
**Tests to Add**: ~25-30

**Coverage Improvement Plan**:
1. Add targeted unit tests for missing lines
2. Focus on error paths and edge cases
3. Test advanced type mappings
4. Test complex query generation
5. Test parser error recovery

**Expected Result**: 95%+ coverage across all Rust integration components.