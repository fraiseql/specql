# Universal SQL Expression: Expanding SpecQL to Express Any SQL Function

**Date**: 2025-11-12
**Vision**: Expand Team A's action vocabulary to express SQL's full computational power
**Status**: Design Phase

---

## 🎯 Core Insight

> "SQL is a complete programming language with variables, conditionals, loops, and queries. If we expand SpecQL's action vocabulary to match SQL's expressiveness, we can reverse engineer ANY SQL function into a universal DSL."

**Feasibility After Expansion: 9/10** (up from 3/10)

---

## 📊 Current State: What SpecQL Can Express

### Existing Step Types (15 types)
```yaml
# Current vocabulary:
- validate: expression          # IF checks
- if: condition                 # Conditionals (basic)
- insert: Entity SET fields     # INSERT
- update: Entity SET fields     # UPDATE
- delete: Entity WHERE clause   # DELETE (soft)
- call: function_name           # Function calls (limited)
- foreach: collection           # Loops (basic)
- notify: recipient             # NOTIFY
- call_service: service.op      # External services
- refresh_table_view: entity    # Materialized view refresh
- duplicate_check: fields       # Uniqueness validation
- find: Entity WHERE clause     # SELECT (basic)
```

### Coverage Analysis
**Current SpecQL can express**:
- ✅ Simple CRUD (21% of reference SQL)
- ✅ Basic conditionals (IF/THEN/ELSE)
- ✅ Simple loops (FOREACH)
- ✅ Validation checks

**Current SpecQL CANNOT express**:
- ❌ Variable declarations and assignments (DECLARE, :=)
- ❌ Complex queries (WITH, CTE, recursive)
- ❌ Multi-way conditionals (ELSIF, CASE)
- ❌ Cursor operations
- ❌ Complex expressions (COALESCE, string functions, JSON operations)
- ❌ Aggregate operations (array_agg, jsonb_build_object)
- ❌ Table-returning functions (RETURNS TABLE)
- ❌ Dynamic SQL (EXECUTE)

---

## 🚀 Proposed Expansion: Universal SQL DSL

### Design Principles

1. **SQL Parity**: Every SQL construct has a SpecQL equivalent
2. **Declarative First**: Prefer declarative syntax over imperative when possible
3. **Type Safety**: Leverage SpecQL's type system
4. **Readability**: YAML should be as clear as SQL comments
5. **Framework Agnostic**: Steps compile to any backend (PostgreSQL, Django, Rails)

---

## 📋 Expansion Roadmap: 20 New Step Types

### Tier 1: Variables & Expressions (CRITICAL)

#### 1. `declare` - Variable Declaration
```yaml
actions:
  - name: format_address
    steps:
      - declare:
          ancestor_map: jsonb              # Type inference
          format_inline: text
          locale_lang: uuid
      - declare:
          total_count: integer = 0         # With initialization
          is_valid: boolean = true
```

**SQL Equivalent**:
```sql
DECLARE
    ancestor_map JSONB;
    format_inline TEXT;
    locale_lang UUID;
    total_count INTEGER := 0;
    is_valid BOOLEAN := TRUE;
```

**Compiler**: `declare_compiler.py`

---

#### 2. `assign` - Variable Assignment
```yaml
steps:
  - assign:
      locale_lang: $input.locale_id
      total_count: $existing_count + 1
      format_inline: replace($template, '{city}', $address.city)
```

**SQL Equivalent**:
```sql
locale_lang := input.locale_id;
total_count := existing_count + 1;
format_inline := replace(template, '{city}', address.city);
```

**Compiler**: `assign_compiler.py`

---

#### 3. `let` - Expression Evaluation (Immutable)
```yaml
steps:
  - let:
      full_name: concat($first_name, ' ', $last_name)
      is_premium: $annual_revenue > 100000
      formatted_date: to_char($created_at, 'YYYY-MM-DD')
```

**SQL Equivalent**: Inline expressions or variable assignments

**Compiler**: `let_compiler.py`

---

### Tier 2: Query Steps (HIGH PRIORITY)

#### 4. `query` - SELECT with Variable Assignment
```yaml
steps:
  - query:
      into: [locale_lang, fallback_lang]
      select: fk_language, default_fallback
      from: tb_locale
      where: pk_locale = $input.locale_id
      single: true  # Expect single row

  - query:
      into: address_details
      select: "*"
      from: tb_public_address
      joins:
        - type: inner
          table: tb_country
          on: tb_country.pk_country = tb_public_address.fk_country
        - type: left
          table: tb_postal_code
          on: tb_postal_code.pk_postal_code = tb_public_address.fk_postal_code
      where: pk_public_address = $input.address_id
```

**SQL Equivalent**:
```sql
SELECT fk_language, default_fallback
INTO locale_lang, fallback_lang
FROM tb_locale
WHERE pk_locale = input.locale_id;

SELECT *
INTO address_details
FROM tb_public_address
INNER JOIN tb_country ON ...
LEFT JOIN tb_postal_code ON ...
WHERE pk_public_address = input.address_id;
```

**Compiler**: `query_compiler.py`

---

#### 5. `cte` - Common Table Expression (WITH clause)
```yaml
steps:
  - cte:
      name: hierarchy
      recursive: true
      columns: [pk_unit, parent_unit, level, name]
      base:
        select:
          - pk_administrative_unit: pk_unit
          - fk_parent_administrative_unit: parent_unit
          - "0 as level"
          - name
        from: tb_administrative_unit
        where: pk_administrative_unit = $start_unit
      recursive_part:
        select:
          - parent.pk_administrative_unit: pk_unit
          - parent.fk_parent_administrative_unit: parent_unit
          - "h.level + 1 as level"
          - parent.name
        from: tb_administrative_unit parent
        join:
          table: hierarchy h
          on: parent.pk_administrative_unit = h.parent_unit

  - query:
      into: all_ancestors
      select: "*"
      from: hierarchy
      order_by: level DESC
```

**SQL Equivalent**:
```sql
WITH RECURSIVE hierarchy AS (
  SELECT
    pk_administrative_unit AS pk_unit,
    fk_parent_administrative_unit AS parent_unit,
    0 AS level,
    name
  FROM tb_administrative_unit
  WHERE pk_administrative_unit = start_unit

  UNION ALL

  SELECT
    parent.pk_administrative_unit,
    parent.fk_parent_administrative_unit,
    h.level + 1,
    parent.name
  FROM tb_administrative_unit parent
  JOIN hierarchy h ON parent.pk_administrative_unit = h.parent_unit
)
SELECT * FROM hierarchy ORDER BY level DESC;
```

**Compiler**: `cte_compiler.py`

---

#### 6. `aggregate` - Aggregation Operations
```yaml
steps:
  - aggregate:
      into: product_counts
      select:
        - fk_category
        - "COUNT(*) as product_count"
        - "array_agg(product_name) as products"
      from: tb_product
      where: fk_model = $model_id
      group_by: [fk_category]
      having: COUNT(*) > $category_limit
```

**SQL Equivalent**:
```sql
SELECT
  fk_category,
  COUNT(*) as product_count,
  array_agg(product_name) as products
INTO product_counts
FROM tb_product
WHERE fk_model = model_id
GROUP BY fk_category
HAVING COUNT(*) > category_limit;
```

**Compiler**: `aggregate_compiler.py`

---

### Tier 3: Advanced Control Flow (MEDIUM PRIORITY)

#### 7. `switch` - Multi-way Branching (CASE/ELSIF)
```yaml
steps:
  - switch:
      expression: $input.operation_type
      cases:
        'CREATE':
          - insert: Product SET name, category
          - assign: result_message = 'Product created'
        'UPDATE':
          - update: Product SET name WHERE id = $input.product_id
          - assign: result_message = 'Product updated'
        'DELETE':
          - delete: Product WHERE id = $input.product_id
          - assign: result_message = 'Product deleted'
      default:
        - assign: result_message = 'Unknown operation'
        - return:
            status: 'failed:invalid_operation'
```

**SQL Equivalent**:
```sql
CASE input.operation_type
  WHEN 'CREATE' THEN
    INSERT INTO tb_product ...;
    result_message := 'Product created';
  WHEN 'UPDATE' THEN
    UPDATE tb_product ...;
    result_message := 'Product updated';
  WHEN 'DELETE' THEN
    DELETE FROM tb_product ...;
    result_message := 'Product deleted';
  ELSE
    result_message := 'Unknown operation';
    RETURN ('failed:invalid_operation', ...);
END CASE;
```

**Compiler**: `switch_compiler.py` (expand existing `if_compiler.py`)

---

#### 8. `while` - Loop with Condition
```yaml
steps:
  - while:
      condition: $current_level < $max_depth AND $has_parent
      steps:
        - query:
            into: parent_unit
            select: "*"
            from: tb_administrative_unit
            where: pk_administrative_unit = $current_parent_id
        - if:
            condition: parent_unit IS NULL
            then:
              - assign: has_parent = false
            else:
              - assign: current_level = $current_level + 1
              - assign: current_parent_id = $parent_unit.fk_parent
```

**SQL Equivalent**:
```sql
WHILE current_level < max_depth AND has_parent LOOP
  SELECT * INTO parent_unit
  FROM tb_administrative_unit
  WHERE pk_administrative_unit = current_parent_id;

  IF parent_unit IS NULL THEN
    has_parent := FALSE;
  ELSE
    current_level := current_level + 1;
    current_parent_id := parent_unit.fk_parent;
  END IF;
END LOOP;
```

**Compiler**: `while_compiler.py`

---

#### 9. `for_query` - Loop Over Query Results
```yaml
steps:
  - for_query:
      iterator: accessory
      query:
        select: "*"
        from: tb_product
        where: fk_parent_product = $model_id
      steps:
        - query:
            into: dependency_count
            select: COUNT(*)
            from: tb_product_dependency
            where: fk_product_source = $accessory.pk_product
        - if:
            condition: $dependency_count > 0
            then:
              - assign: has_dependencies = true
              - call: validate_dependencies
                args:
                  product_id: $accessory.pk_product
```

**SQL Equivalent**:
```sql
FOR accessory IN
  SELECT * FROM tb_product WHERE fk_parent_product = model_id
LOOP
  SELECT COUNT(*) INTO dependency_count
  FROM tb_product_dependency
  WHERE fk_product_source = accessory.pk_product;

  IF dependency_count > 0 THEN
    has_dependencies := TRUE;
    PERFORM validate_dependencies(accessory.pk_product);
  END IF;
END LOOP;
```

**Compiler**: `for_query_compiler.py`

---

### Tier 4: Function Composition (HIGH VALUE)

#### 10. `call_function` - Call Domain Function
```yaml
steps:
  - call_function:
      function: catalog.validate_category_limits
      args:
        model_id: $input.model_id
        accessories: $selected_accessories
      into: category_validation

  - call_function:
      function: catalog.resolve_dependencies_recursive
      args:
        model_id: $input.model_id
        accessories: $selected_accessories
        max_depth: 8
      into: dependency_validation

  - assign:
      is_valid: $category_validation.is_valid AND $dependency_validation.is_valid
```

**SQL Equivalent**:
```sql
category_validation := catalog.validate_category_limits(
  input.model_id,
  selected_accessories
);

dependency_validation := catalog.resolve_dependencies_recursive(
  input.model_id,
  selected_accessories,
  8
);

is_valid := category_validation.is_valid AND dependency_validation.is_valid;
```

**Compiler**: `call_function_compiler.py`

---

#### 11. `return_early` - Early Return
```yaml
steps:
  - validate: $input.street_name IS NOT NULL
    error: 'street_name_required'

  - if:
      condition: TRIM($input.street_name) = ''
      then:
        - return_early:
            status: 'validation:field_required'
            message: 'Street name cannot be empty'
            metadata:
              field: 'street_name'

  # Continue with normal flow
  - insert: PublicAddress SET street_name, city
```

**SQL Equivalent**:
```sql
IF input.street_name IS NULL THEN
  RETURN ('validation_error', 'street_name is required', ...);
END IF;

IF TRIM(input.street_name) = '' THEN
  RETURN (
    '00000000-0000-0000-0000-000000000000',
    ARRAY[]::TEXT[],
    'validation:field_required',
    'Street name cannot be empty',
    NULL,
    jsonb_build_object('field', 'street_name')
  )::app.mutation_result;
END IF;

-- Continue...
INSERT INTO ...;
```

**Compiler**: `return_compiler.py`

---

### Tier 5: Complex Data Operations (MEDIUM PRIORITY)

#### 12. `json_build` - JSON/JSONB Construction
```yaml
steps:
  - json_build:
      into: result_object
      type: object  # or array
      fields:
        isValid: $is_valid
        categoryLimitViolations: $category_violations
        missingDependencies:
          - json_build:
              type: array
              items: $missing_deps
              transform:
                sourceProductId: item.source_id
                requiredProductId: item.required_id
                message: concat('Missing: ', item.required_name)
```

**SQL Equivalent**:
```sql
result_object := jsonb_build_object(
  'isValid', is_valid,
  'categoryLimitViolations', category_violations,
  'missingDependencies', (
    SELECT jsonb_agg(
      jsonb_build_object(
        'sourceProductId', source_id,
        'requiredProductId', required_id,
        'message', 'Missing: ' || required_name
      )
    )
    FROM unnest(missing_deps)
  )
);
```

**Compiler**: `json_build_compiler.py`

---

#### 13. `array_build` - Array Construction & Manipulation
```yaml
steps:
  - array_build:
      into: violation_list
      items:
        - source: $category_violations
          filter: severity = 'HIGH'
        - source: $dependency_violations
          filter: is_blocking = true

  - array_build:
      into: field_names
      from_query:
        select: field_name
        from: information_schema.columns
        where: table_name = 'tb_product'
```

**SQL Equivalent**:
```sql
violation_list := (
  SELECT array_agg(v)
  FROM (
    SELECT * FROM unnest(category_violations) AS v WHERE v.severity = 'HIGH'
    UNION ALL
    SELECT * FROM unnest(dependency_violations) AS v WHERE v.is_blocking = TRUE
  ) combined
);

field_names := ARRAY(
  SELECT field_name
  FROM information_schema.columns
  WHERE table_name = 'tb_product'
);
```

**Compiler**: `array_build_compiler.py`

---

#### 14. `transform` - Data Transformation Pipeline
```yaml
steps:
  - transform:
      source: $raw_address_data
      into: formatted_address
      operations:
        - replace:
            field: street_name
            pattern: '{street_number}'
            with: $address.street_number
        - replace:
            field: street_name
            pattern: '{street_type}'
            with: $address.street_type
        - coalesce:
            field: city
            fallback: 'Unknown'
        - trim:
            fields: [street_name, city, postal_code]
```

**SQL Equivalent**:
```sql
formatted_address := raw_address_data;
formatted_address := replace(formatted_address, '{street_number}', address.street_number);
formatted_address := replace(formatted_address, '{street_type}', address.street_type);
city := COALESCE(city, 'Unknown');
street_name := TRIM(street_name);
city := TRIM(city);
postal_code := TRIM(postal_code);
```

**Compiler**: `transform_compiler.py`

---

### Tier 6: Advanced Query Patterns (LOW PRIORITY)

#### 15. `subquery` - Correlated Subqueries
```yaml
steps:
  - update:
      entity: Product
      set:
        total_accessories: |
          (SELECT COUNT(*)
           FROM tb_product accessories
           WHERE accessories.fk_parent_product = Product.pk_product)
      where: fk_model = $model_id
```

**Compiler**: Extended `update_compiler.py`

---

#### 16. `upsert` - INSERT ... ON CONFLICT
```yaml
steps:
  - upsert:
      entity: ProductPrice
      set:
        fk_product: $product_id
        amount: $new_price
        currency: 'USD'
      conflict_target: [fk_product, currency]
      on_conflict:
        update:
          - amount: $new_price
          - updated_at: now()
```

**SQL Equivalent**:
```sql
INSERT INTO tb_product_price (fk_product, amount, currency)
VALUES (product_id, new_price, 'USD')
ON CONFLICT (fk_product, currency)
DO UPDATE SET
  amount = new_price,
  updated_at = now();
```

**Compiler**: `upsert_compiler.py`

---

#### 17. `batch_operation` - Bulk Operations
```yaml
steps:
  - batch_operation:
      type: insert
      entity: Notification
      items: $notification_list
      batch_size: 100  # Insert 100 at a time
      fields: [recipient_id, message, type]
```

**SQL Equivalent**:
```sql
INSERT INTO tb_notification (recipient_id, message, type)
SELECT recipient_id, message, type
FROM unnest(notification_list);
```

**Compiler**: `batch_compiler.py`

---

### Tier 7: Table-Returning & Advanced Functions (SPECIALIZED)

#### 18. `return_table` - Table-Returning Functions
```yaml
entity: AddressFormat
schema: core
functions:
  - name: format_address_all_modes
    returns: table
    columns:
      format_inline: text
      format_multiline: text
      format_web: text
    steps:
      - declare:
          ancestor_map: jsonb
      # ... complex logic ...
      - return_table:
          rows:
            - format_inline: $inline_result
              format_multiline: $multiline_result
              format_web: $web_result
```

**SQL Equivalent**:
```sql
CREATE FUNCTION format_address_all_modes(...)
RETURNS TABLE (
  format_inline TEXT,
  format_multiline TEXT,
  format_web TEXT
) AS $$
BEGIN
  -- logic --
  RETURN QUERY SELECT inline_result, multiline_result, web_result;
END;
$$;
```

**Compiler**: `return_table_compiler.py`

---

#### 19. `cursor` - Cursor Operations
```yaml
steps:
  - cursor:
      name: product_cursor
      query:
        select: "*"
        from: tb_product
        where: needs_update = true

  - foreach_cursor:
      cursor: product_cursor
      iterator: product
      steps:
        - call_function:
            function: calculate_price
            args:
              product_id: $product.pk_product
        - update:
            entity: Product
            set:
              calculated_price: $calculated_price
            where: pk_product = $product.pk_product
```

**SQL Equivalent**:
```sql
DECLARE product_cursor CURSOR FOR
  SELECT * FROM tb_product WHERE needs_update = TRUE;

FOR product IN product_cursor LOOP
  calculated_price := calculate_price(product.pk_product);
  UPDATE tb_product
  SET calculated_price = calculated_price
  WHERE pk_product = product.pk_product;
END LOOP;
```

**Compiler**: `cursor_compiler.py`

---

#### 20. `exception_handling` - Try/Catch Blocks
```yaml
steps:
  - try:
      steps:
        - call_function:
            function: risky_operation
            args:
              data: $input
      catch:
        - exception_type: 'foreign_key_violation'
          steps:
            - return_early:
                status: 'failed:invalid_reference'
                message: 'Referenced entity does not exist'
        - exception_type: 'unique_violation'
          steps:
            - return_early:
                status: 'failed:duplicate'
                message: 'Record already exists'
        - default:
            - return_early:
                status: 'failed:unexpected_error'
                message: $exception.message
```

**SQL Equivalent**:
```sql
BEGIN
  PERFORM risky_operation(input);
EXCEPTION
  WHEN foreign_key_violation THEN
    RETURN ('failed:invalid_reference', ...);
  WHEN unique_violation THEN
    RETURN ('failed:duplicate', ...);
  WHEN OTHERS THEN
    RETURN ('failed:unexpected_error', SQLERRM, ...);
END;
```

**Compiler**: `exception_compiler.py`

---

## 🎯 Coverage After Expansion

| SQL Feature | Current Support | After Expansion | Gap |
|-------------|-----------------|-----------------|-----|
| **Variables** | ❌ None | ✅ Full | Declare, assign, let |
| **Queries** | ⚠️ Basic | ✅ Full | CTE, joins, aggregates |
| **Conditionals** | ⚠️ IF/THEN | ✅ Full | ELSIF, CASE, switch |
| **Loops** | ⚠️ FOREACH | ✅ Full | WHILE, FOR query |
| **Functions** | ⚠️ Limited | ✅ Full | Call, return, table-returning |
| **Data Ops** | ⚠️ CRUD | ✅ Full | JSON, arrays, transforms |
| **Error Handling** | ❌ None | ✅ Full | Try/catch, early return |

### Updated Feasibility

| Scenario | Before | After Expansion | Improvement |
|----------|--------|-----------------|-------------|
| **Simple CRUD** | 8/10 | 9/10 | +1 |
| **Complex Validation** | 3/10 | 8/10 | +5 |
| **Function Composition** | 2/10 | 9/10 | +7 |
| **Recursive Queries** | 0/10 | 9/10 | +9 |
| **Template Logic** | 0/10 | 8/10 | +8 |
| **Overall Reference SQL** | 3/10 | **9/10** | +6 |

---

## 📋 Phased Implementation Plan

### Phase A1: Core Expansion (CRITICAL - 3 weeks)
**Steps**: declare, assign, let, query, call_function
**Coverage Improvement**: 3/10 → 6/10
**Unlocks**: 60% of reference SQL

### Phase A2: Control Flow (HIGH - 2 weeks)
**Steps**: switch, while, for_query, return_early
**Coverage Improvement**: 6/10 → 7/10
**Unlocks**: 15% more reference SQL

### Phase A3: Advanced Queries (HIGH - 2 weeks)
**Steps**: cte, aggregate, subquery
**Coverage Improvement**: 7/10 → 8/10
**Unlocks**: Recursive patterns, complex joins

### Phase A4: Data Operations (MEDIUM - 2 weeks)
**Steps**: json_build, array_build, transform, upsert
**Coverage Improvement**: 8/10 → 9/10
**Unlocks**: Complex data manipulation

### Phase A5: Specialized (LOW - 2 weeks)
**Steps**: cursor, exception_handling, return_table, batch_operation
**Coverage Improvement**: 9/10 → 9.5/10
**Unlocks**: Edge cases and optimizations

**Total Effort**: 11 weeks for full expansion
**Recommended Priority**: Phase A1-A3 (7 weeks for 8/10 coverage)

---

## 🔄 Example: Full Reference Function in SpecQL

### Before (Reference SQL - Not Expressible)
```sql
-- 90 lines of custom logic
CREATE FUNCTION catalog.validate_product_configuration(...)
RETURNS JSONB AS $$
DECLARE
  v_category_validation JSONB;
  v_dependency_validation JSONB;
BEGIN
  -- Validate model exists
  -- Call sub-functions
  -- Merge results
END;
$$;
```

**SpecQL Coverage**: 20% (basic structure only)

---

### After (Fully Expressible in SpecQL)
```yaml
entity: ProductConfiguration
schema: catalog
functions:
  - name: validate_product_configuration
    returns: jsonb
    inputs:
      model_id: uuid
      accessory_ids: list(uuid)
    steps:
      # Handle empty input
      - if:
          condition: $accessory_ids IS NULL OR array_length($accessory_ids) = 0
          then:
            - return_early:
                value:
                  isValid: true
                  categoryLimitViolations: []
                  missingDependencies: []

      # Validate model exists
      - query:
          into: model_exists
          select: COUNT(*)
          from: tb_product
          where: pk_product = $model_id AND fk_model IS NOT NULL

      - if:
          condition: $model_exists = 0
          then:
            - return_early:
                error: 'Invalid model_product_id'

      # Call validation functions
      - call_function:
          function: catalog.validate_category_limits
          args:
            model_id: $model_id
            accessories: $accessory_ids
          into: category_validation

      - call_function:
          function: catalog.resolve_dependencies_recursive
          args:
            model_id: $model_id
            accessories: $accessory_ids
            max_depth: 8
          into: dependency_validation

      # Combine results
      - assign:
          overall_valid: $category_validation.isValid AND $dependency_validation.isValid

      - json_build:
          into: result
          type: object
          fields:
            isValid: $overall_valid
            categoryLimitViolations: $category_validation.violations
            missingDependencies: $dependency_validation.missingDependencies
            missingGroups: $dependency_validation.missingGroups
            conflicts: $dependency_validation.conflicts

      - return: result
```

**SpecQL Coverage**: 95% (fully expressible!)

---

## 🎓 Benefits of Universal Expression

### 1. Perfect Reverse Engineering (9/10 feasibility)
- ✅ Parse ANY SQL function
- ✅ Express in universal SpecQL DSL
- ✅ Round-trip: SQL → YAML → SQL

### 2. Framework Portability
```yaml
# Same YAML generates code for ANY backend
entity: Contact
actions:
  - name: validate_and_create
    steps:
      - declare: [is_valid: boolean]
      - call_function:
          function: check_email_format
          args: {email: $input.email}
          into: is_valid
      - if:
          condition: NOT $is_valid
          then: [return_early: {error: 'invalid_email'}]
      - insert: Contact SET email, name
```

**Compiles to**:
- PostgreSQL PL/pgSQL ✅
- Django ORM Python ✅
- Rails ActiveRecord Ruby ✅
- Prisma TypeScript ✅

### 3. AI-Friendly
- Clear, declarative syntax
- Predictable patterns
- Easy to generate/modify

### 4. Migration Path
- Convert legacy SQL → SpecQL YAML
- Modernize gradually
- Maintain in YAML, generate SQL

---

## 🚨 Challenges & Mitigations

### Challenge 1: YAML Verbosity
**Problem**: Complex functions → long YAML files

**Mitigation**:
- Add YAML anchors/references
- Support inline SQL for edge cases
- Create macro system for common patterns

```yaml
# Macro definition
macros:
  validate_not_empty:
    params: [field_name, error_code]
    steps:
      - if:
          condition: TRIM($field_name) = ''
          then:
            - return_early:
                error: $error_code

# Usage
steps:
  - use_macro: validate_not_empty
    args:
      field_name: $input.street_name
      error_code: 'street_name_empty'
```

---

### Challenge 2: Performance
**Problem**: Declarative DSL might generate suboptimal SQL

**Mitigation**:
- Smart compiler optimizations
- Query plan analysis
- Allow SQL hints in YAML

```yaml
steps:
  - query:
      hint: "/*+ INDEX(tb_product idx_product_category) */"
      select: "*"
      from: tb_product
      where: fk_category = $category_id
```

---

### Challenge 3: Debugging
**Problem**: YAML errors harder to debug than SQL

**Mitigation**:
- Generate SQL with source maps (YAML line → SQL line)
- Rich error messages with YAML context
- Debug mode: show generated SQL

```yaml
# Error message:
❌ Error in entities/product.yaml:45
   Step: call_function.catalog.validate_dependencies

   Generated SQL (line 123):
   v_result := catalog.validate_dependencies(product_id, accessories);

   PostgreSQL Error: function catalog.validate_dependencies does not exist

   💡 Did you mean: catalog.resolve_dependencies_recursive?
```

---

## 📊 ROI Analysis

### Development Effort
- **Phase A1-A3**: 7 weeks (8/10 coverage)
- **Phase A4-A5**: 4 weeks (9.5/10 coverage)
- **Total**: 11 weeks

### Value Delivered
- ✅ **95% of reference SQL** expressible in SpecQL
- ✅ **Perfect reverse engineering** (SQL ↔ YAML)
- ✅ **Multi-framework portability** (1 YAML → N backends)
- ✅ **Migration path** for legacy codebases
- ✅ **AI-first DSL** for code generation

### Comparison

| Approach | Feasibility | Effort | Coverage |
|----------|-------------|--------|----------|
| **Track 1: SpecQL round-trip only** | 8/10 | 6 weeks | 21% of ref SQL |
| **Track 2: Gap analyzer only** | 7/10 | 3 weeks | Discovery tool |
| **Universal Expansion (THIS)** | 9/10 | 11 weeks | 95% of ref SQL |

**Recommendation**: Universal Expansion delivers 5x more value for 2x effort

---

## ✅ Recommendation

**PROCEED with Universal SQL Expression Expansion**

**Priority**:
1. **Phase A1** (3 weeks): Variables, queries, function calls → 6/10 coverage
2. **Phase A2** (2 weeks): Control flow → 7/10 coverage
3. **Phase A3** (2 weeks): Advanced queries → 8/10 coverage
4. **Evaluate**: After 7 weeks, reassess A4-A5 based on remaining gaps

**Expected Outcome**:
- SpecQL becomes universal SQL expression language
- Any PostgreSQL function expressible in YAML
- Perfect reverse engineering capability
- Foundation for multi-framework code generation

---

**Last Updated**: 2025-11-12
**Status**: Design Complete - Ready for Implementation
**Overall Feasibility**: 9/10 with expanded DSL
**Total Effort**: 7-11 weeks depending on coverage target
