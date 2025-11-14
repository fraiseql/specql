# Basic Validation Example

This example demonstrates how to implement business rule validation using SpecQL's validation patterns to ensure data integrity and enforce business constraints.

## Overview

We'll create a `User` entity with comprehensive validation rules for registration, including email format validation, password strength requirements, and uniqueness constraints.

## Entity Definition

Create a file `user.yaml`:

```yaml
entity: User
schema: auth
description: "User account with validation rules"

fields:
  email: text
  username: text
  password_hash: text
  first_name: text
  last_name: text
  age: integer
  email_verified: boolean
  created_at: timestamp
  last_login: timestamp

actions:
  - name: register_user
    pattern: validation/validation_chain
    requires: caller.is_anonymous
    validations:
      # Email validations
      - field: email
        rule: required
        error: "email_required"
      - field: email
        rule: format
        pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        error: "invalid_email_format"
      - field: email
        rule: unique
        table: auth.user
        error: "email_already_exists"

      # Username validations
      - field: username
        rule: required
        error: "username_required"
      - field: username
        rule: length
        min: 3
        max: 20
        error: "username_length_invalid"
      - field: username
        rule: format
        pattern: "^[a-zA-Z0-9_-]+$"
        error: "username_format_invalid"
      - field: username
        rule: unique
        table: auth.user
        error: "username_already_exists"

      # Password validations
      - field: password_hash
        rule: required
        error: "password_required"
      - field: password_hash
        rule: length
        min: 8
        error: "password_too_short"

      # Name validations
      - field: first_name
        rule: required
        error: "first_name_required"
      - field: last_name
        rule: required
        error: "last_name_required"

      # Age validations
      - field: age
        rule: range
        min: 13
        max: 120
        error: "age_out_of_range"

      # Cross-field validations
      - rule: custom
        condition: "age >= 18 OR (first_name IS NOT NULL AND last_name IS NOT NULL)"
        error: "minor_requires_parental_consent"
    steps:
      - insert: User SET email_verified = false, created_at = now()

  - name: update_profile
    pattern: crud/update
    requires: caller.is_self OR caller.can_admin_users
    fields: [first_name, last_name, age]
    validations:
      - field: first_name
        rule: required
        error: "first_name_required"
      - field: last_name
        rule: required
        error: "last_name_required"
      - field: age
        rule: range
        min: 13
        max: 120
        error: "age_out_of_range"
```

## Generated SQL

SpecQL generates validation functions with comprehensive error handling:

```sql
-- Validation function for user registration
CREATE OR REPLACE FUNCTION auth.register_user(
    p_email text,
    p_username text,
    p_password_hash text,
    p_first_name text,
    p_last_name text,
    p_age integer
) RETURNS uuid AS $$
DECLARE
    v_user_id uuid;
BEGIN
    -- Email validations
    IF p_email IS NULL OR p_email = '' THEN
        RAISE EXCEPTION 'Email is required' USING ERRCODE = 'email_required';
    END IF;

    IF NOT (p_email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') THEN
        RAISE EXCEPTION 'Invalid email format' USING ERRCODE = 'invalid_email_format';
    END IF;

    IF EXISTS (SELECT 1 FROM auth.user WHERE email = p_email) THEN
        RAISE EXCEPTION 'Email already exists' USING ERRCODE = 'email_already_exists';
    END IF;

    -- Username validations
    IF p_username IS NULL OR p_username = '' THEN
        RAISE EXCEPTION 'Username is required' USING ERRCODE = 'username_required';
    END IF;

    IF LENGTH(p_username) < 3 OR LENGTH(p_username) > 20 THEN
        RAISE EXCEPTION 'Username must be 3-20 characters' USING ERRCODE = 'username_length_invalid';
    END IF;

    IF NOT (p_username ~ '^[a-zA-Z0-9_-]+$') THEN
        RAISE EXCEPTION 'Username contains invalid characters' USING ERRCODE = 'username_format_invalid';
    END IF;

    IF EXISTS (SELECT 1 FROM auth.user WHERE username = p_username) THEN
        RAISE EXCEPTION 'Username already exists' USING ERRCODE = 'username_already_exists';
    END IF;

    -- Password validations
    IF p_password_hash IS NULL OR p_password_hash = '' THEN
        RAISE EXCEPTION 'Password is required' USING ERRCODE = 'password_required';
    END IF;

    IF LENGTH(p_password_hash) < 8 THEN
        RAISE EXCEPTION 'Password must be at least 8 characters' USING ERRCODE = 'password_too_short';
    END IF;

    -- Name validations
    IF p_first_name IS NULL OR p_first_name = '' THEN
        RAISE EXCEPTION 'First name is required' USING ERRCODE = 'first_name_required';
    END IF;

    IF p_last_name IS NULL OR p_last_name = '' THEN
        RAISE EXCEPTION 'Last name is required' USING ERRCODE = 'last_name_required';
    END IF;

    -- Age validations
    IF p_age < 13 OR p_age > 120 THEN
        RAISE EXCEPTION 'Age must be between 13 and 120' USING ERRCODE = 'age_out_of_range';
    END IF;

    -- Cross-field validation
    IF p_age < 18 AND (p_first_name IS NULL OR p_last_name IS NULL) THEN
        RAISE EXCEPTION 'Minors require parental consent' USING ERRCODE = 'minor_requires_parental_consent';
    END IF;

    -- Insert user
    INSERT INTO auth.user (
        email, username, password_hash, first_name, last_name, age,
        email_verified, created_at
    ) VALUES (
        p_email, p_username, p_password_hash, p_first_name, p_last_name, p_age,
        false, now()
    ) RETURNING id INTO v_user_id;

    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Usage Examples

### Successful User Registration

```sql
-- Register a valid adult user
SELECT auth.register_user(
    'john.doe@example.com',
    'johndoe',
    '$2b$10$hashedpasswordhere', -- bcrypt hash
    'John',
    'Doe',
    25
);

-- Returns: user_id (uuid)
```

### Registration with Validation Errors

```sql
-- Try invalid email
SELECT auth.register_user(
    'invalid-email',
    'johndoe',
    'password123',
    'John',
    'Doe',
    25
);
-- ERROR: Invalid email format

-- Try duplicate email
SELECT auth.register_user(
    'existing@example.com',
    'differentuser',
    'password123',
    'Jane',
    'Smith',
    30
);
-- ERROR: Email already exists

-- Try underage user without proper names
SELECT auth.register_user(
    'young@example.com',
    'younguser',
    'password123',
    NULL,  -- missing first name
    NULL,  -- missing last name
    15
);
-- ERROR: Minors require parental consent
```

### Updating User Profile

```sql
-- Update user profile with validation
SELECT auth.update_profile(
    'user-uuid-here',
    'Johnny',  -- new first name
    'Doe',     -- last name unchanged
    26         -- new age
);
```

## Testing Validation Rules

SpecQL generates comprehensive validation tests:

```sql
-- Run validation tests
SELECT * FROM runtests('auth.user_validation_test');

-- Example test output:
-- ok 1 - register_user validates required email
-- ok 2 - register_user validates email format
-- ok 3 - register_user prevents duplicate emails
-- ok 4 - register_user validates username length
-- ok 5 - register_user validates username format
-- ok 6 - register_user validates password strength
-- ok 7 - register_user validates age range
-- ok 8 - register_user handles cross-field validation
-- ok 9 - update_profile validates required fields
```

## Validation Rule Types

### Field Validations
- **required**: Field must not be null or empty
- **length**: String length constraints (min/max)
- **range**: Numeric range constraints (min/max)
- **format**: Regular expression pattern matching
- **unique**: Value must be unique in table

### Cross-Field Validations
- **custom**: Arbitrary SQL conditions
- **conditional**: Rules that apply based on other field values

### Business Rule Examples
```yaml
validations:
  # Date validations
  - field: end_date
    rule: custom
    condition: "end_date > start_date"
    error: "end_date_before_start"

  # Financial validations
  - field: discount_percentage
    rule: range
    min: 0
    max: 50
    error: "discount_too_high"

  # Status validations
  - rule: custom
    condition: "status = 'shipped' AND tracking_number IS NOT NULL"
    error: "shipped_requires_tracking"
```

## Key Benefits

✅ **Data Integrity**: Validation enforced at database level
✅ **Business Rules**: Complex business logic validation
✅ **Error Handling**: Clear, specific error messages
✅ **Testing**: Comprehensive validation test coverage
✅ **Security**: Prevents invalid data insertion
✅ **Maintainability**: Validation rules defined declaratively

## Next Steps

- Add [state machines](../basic/state-machine.md) for user status (active/inactive)
- Implement [multi-entity operations](../intermediate/multi-entity.md) for user roles
- Use [batch operations](../intermediate/batch-operations.md) for bulk user imports

---

**See Also:**
- [CRUD Example](simple-crud.md)
- [State Machine Example](state-machine.md)
- [Validation Patterns](../../guides/mutation-patterns/validation.md)