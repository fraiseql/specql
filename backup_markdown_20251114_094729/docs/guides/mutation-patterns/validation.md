# Validation Pattern

The **validation** pattern enforces data integrity and business rules. It provides declarative validation rules that are automatically enforced across create, update, and other operations.

## 🎯 What You'll Learn

- Validation pattern concepts and benefits
- Configuring validation rules
- Built-in vs custom validators
- Error handling and reporting
- Testing validation logic

## 📋 Prerequisites

- [Pattern basics](getting-started.md)
- Understanding of business rules
- Knowledge of data constraints

## 💡 Validation Concepts

### What Is Data Validation?

**Validation** ensures data meets business requirements:

```yaml
patterns:
  - name: validation
    description: "User data integrity rules"
    rules:
      - name: email_format
        field: email
        rule: "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'"
        message: "Email must be in valid format"

      - name: age_positive
        field: age
        rule: "age > 0 AND age < 150"
        message: "Age must be between 1 and 149"

      - name: unique_email_active
        field: email
        rule: "UNIQUE(email) WHERE status = 'active'"
        message: "Active user with this email already exists"
```

**Benefits:**
- **Consistency** - Same rules everywhere
- **Early feedback** - Catch errors before they cause issues
- **Maintainability** - Declarative rule definition
- **Testing** - Automatic validation test generation

### Types of Validation

| Type | Purpose | Example |
|------|---------|---------|
| **Field Validation** | Single field rules | Email format, age range |
| **Cross-field Validation** | Multi-field rules | End date after start date |
| **Uniqueness** | Unique constraints | Unique email per active user |
| **Referential** | Foreign key checks | Valid category ID |
| **Business Rules** | Complex logic | Credit limit not exceeded |

## 🏗️ Basic Validation

### Field-Level Validation

```yaml
# entities/user.yaml
name: user
fields:
  id: uuid
  email: string
  first_name: string
  last_name: string
  age: integer?
  status: string

patterns:
  - name: validation
    description: "User data validation rules"
    rules:
      # Required field validation
      - name: email_required
        field: email
        rule: "email IS NOT NULL"
        message: "Email is required"

      # Format validation
      - name: email_format
        field: email
        rule: "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'"
        message: "Email must be in valid format"

      # Range validation
      - name: age_range
        field: age
        rule: "age IS NULL OR (age >= 13 AND age <= 120)"
        message: "Age must be between 13 and 120"

      # String length validation
      - name: name_length
        field: first_name
        rule: "LENGTH(first_name) >= 2 AND LENGTH(first_name) <= 50"
        message: "First name must be 2-50 characters"

      # Status enum validation
      - name: valid_status
        field: status
        rule: "status IN ('active', 'inactive', 'suspended')"
        message: "Status must be active, inactive, or suspended"
```

### Generated Constraints

```sql
-- Generated check constraints
ALTER TABLE user ADD CONSTRAINT check_email_required
  CHECK (email IS NOT NULL);

ALTER TABLE user ADD CONSTRAINT check_email_format
  CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

ALTER TABLE user ADD CONSTRAINT check_age_range
  CHECK (age IS NULL OR (age >= 13 AND age <= 120));

-- Generated validation function
CREATE FUNCTION validate_user_data()
RETURNS TRIGGER AS $$
BEGIN
  -- Email format validation
  IF NEW.email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
    RAISE EXCEPTION 'Email must be in valid format';
  END IF;

  -- Age range validation
  IF NEW.age IS NOT NULL AND (NEW.age < 13 OR NEW.age > 120) THEN
    RAISE EXCEPTION 'Age must be between 13 and 120';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger
CREATE TRIGGER validate_user_data_trigger
  BEFORE INSERT OR UPDATE ON user
  FOR EACH ROW EXECUTE FUNCTION validate_user_data();
```

## ⚙️ Advanced Validation

### Cross-Field Validation

```yaml
patterns:
  - name: validation
    description: "Complex business rules"
    rules:
      # Date range validation
      - name: end_after_start
        fields: [start_date, end_date]
        rule: "end_date IS NULL OR start_date IS NULL OR end_date > start_date"
        message: "End date must be after start date"

      # Conditional validation
      - name: credit_limit_required
        fields: [account_type, credit_limit]
        rule: |
          account_type != 'premium' OR
          (account_type = 'premium' AND credit_limit IS NOT NULL AND credit_limit > 0)
        message: "Premium accounts require a credit limit"

      # Complex business logic
      - name: shipping_address_required
        fields: [requires_shipping, shipping_address]
        rule: |
          requires_shipping = false OR
          (requires_shipping = true AND shipping_address IS NOT NULL)
        message: "Shipping address required when shipping is needed"
```

### Uniqueness Constraints

```yaml
patterns:
  - name: validation
    description: "Uniqueness and exclusion rules"
    rules:
      # Simple uniqueness
      - name: unique_email
        field: email
        rule: "UNIQUE(email)"
        message: "Email must be unique"

      # Conditional uniqueness
      - name: unique_email_active
        field: email
        rule: "UNIQUE(email) WHERE status = 'active'"
        message: "Active user with this email already exists"

      # Composite uniqueness
      - name: unique_name_per_category
        fields: [name, category_id]
        rule: "UNIQUE(name, category_id)"
        message: "Name must be unique within category"

      # Exclusion constraints
      - name: no_overlapping_dates
        fields: [start_date, end_date]
        rule: "EXCLUDE (start_date WITH =, end_date WITH =) WHERE (status = 'active')"
        message: "Date ranges cannot overlap for active records"
```

### Custom Validation Functions

```yaml
patterns:
  - name: validation
    description: "Custom validation logic"
    rules:
      # External service validation
      - name: valid_postal_code
        field: postal_code
        rule: "validate_postal_code(postal_code, country)"
        message: "Invalid postal code for selected country"

      # Complex business rules
      - name: sufficient_balance
        fields: [amount, account_id]
        rule: "check_account_balance(account_id, amount)"
        message: "Insufficient account balance"

      # Cross-entity validation
      - name: valid_product_category
        fields: [product_id, category_id]
        rule: "product_belongs_to_category(product_id, category_id)"
        message: "Product does not belong to selected category"
```

## 🔧 Validation Triggers

### When Validation Runs

```yaml
patterns:
  - name: validation
    description: "Validation trigger configuration"
    rules:
      - name: email_validation
        field: email
        rule: "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'"
        message: "Invalid email format"

    # Trigger configuration
    triggers:
      - events: [insert, update]
        timing: before
        granularity: row
        when: "NEW.email IS DISTINCT FROM OLD.email"  # Only when email changes

      - events: [delete]
        timing: before
        granularity: row
        actions: [log_deletion]  # Custom actions on delete
```

### Conditional Validation

```yaml
patterns:
  - name: validation
    description: "Conditional validation rules"
    rules:
      # Only validate for active records
      - name: active_record_validation
        field: email
        rule: "status != 'active' OR email IS NOT NULL"
        message: "Active records must have email"
        condition: "status = 'active'"  # Only apply when status is active

      # Skip validation for admin users
      - name: admin_override
        field: credit_limit
        rule: "user_is_admin() OR credit_limit <= 10000"
        message: "Credit limit cannot exceed $10,000"
        condition: "NOT user_is_admin()"  # Skip for admins
```

## 📊 Error Handling and Reporting

### Custom Error Messages

```yaml
patterns:
  - name: validation
    description: "User-friendly error messages"
    rules:
      - name: password_strength
        field: password_hash
        rule: "LENGTH(password_hash) >= 8 AND password_hash ~ '[A-Z]' AND password_hash ~ '[0-9]'"
        message: "Password must be at least 8 characters with uppercase letter and number"
        error_code: "WEAK_PASSWORD"

      - name: account_balance
        fields: [amount, account_id]
        rule: "get_account_balance(account_id) >= amount"
        message: "Insufficient funds: available balance $%s, requested $%s"
        message_args: ["get_account_balance(account_id)", "amount"]
        error_code: "INSUFFICIENT_FUNDS"
```

### Validation Result Handling

```yaml
patterns:
  - name: validation
    description: "Validation result configuration"
    rules:
      - name: age_validation
        field: age
        rule: "age >= 18"
        message: "Must be 18 or older"

    # Result handling
    on_validation_failure:
      - action: log_validation_error
        level: warning
      - action: send_notification
        to: "compliance@company.com"
        template: "validation_failure"

    # Strictness level
    validation_mode: strict  # 'strict', 'warning', 'permissive'
    fail_on_first_error: false  # Collect all errors
```

## 🧪 Testing Validation

### Generated Tests

```bash
# Generate comprehensive tests
specql generate tests entities/user.yaml

# Run tests
specql test run entities/user.yaml
```

**Test Coverage:**
- ✅ **Valid data** - Correct data passes validation
- ✅ **Invalid data** - Incorrect data fails with proper messages
- ✅ **Boundary conditions** - Edge cases and limits
- ✅ **Cross-field validation** - Multi-field rules work
- ✅ **Conditional validation** - Rules apply in correct contexts
- ✅ **Error messages** - Clear, helpful error messages

### Manual Testing

```sql
-- Test valid data
INSERT INTO user (email, first_name, age, status)
VALUES ('john@example.com', 'John', 25, 'active');

-- Test invalid email
INSERT INTO user (email, first_name, age, status)
VALUES ('invalid-email', 'John', 25, 'active');
-- Should fail: "Email must be in valid format"

-- Test age validation
INSERT INTO user (email, first_name, age, status)
VALUES ('jane@example.com', 'Jane', 10, 'active');
-- Should fail: "Age must be between 13 and 120"

-- Test cross-field validation
INSERT INTO event (start_date, end_date)
VALUES ('2024-01-15', '2024-01-10');
-- Should fail: "End date must be after start date"
```

## 🚀 Common Use Cases

### User Registration

```yaml
patterns:
  - name: validation
    description: "User registration validation"
    rules:
      - name: email_required
        field: email
        rule: "email IS NOT NULL"
        message: "Email is required"

      - name: email_unique
        field: email
        rule: "UNIQUE(email)"
        message: "Email already registered"

      - name: password_strength
        field: password_hash
        rule: "LENGTH(password_hash) >= 8"
        message: "Password must be at least 8 characters"

      - name: age_verification
        field: date_of_birth
        rule: "date_of_birth IS NULL OR date_of_birth <= CURRENT_DATE - INTERVAL '13 years'"
        message: "Must be 13 or older to register"

      - name: terms_accepted
        field: terms_accepted
        rule: "terms_accepted = true"
        message: "Terms of service must be accepted"
```

### E-commerce Product

```yaml
patterns:
  - name: validation
    description: "Product data validation"
    rules:
      - name: name_required
        field: name
        rule: "name IS NOT NULL AND LENGTH(TRIM(name)) > 0"
        message: "Product name is required"

      - name: price_positive
        field: price
        rule: "price > 0"
        message: "Price must be greater than zero"

      - name: sku_unique
        field: sku
        rule: "UNIQUE(sku)"
        message: "SKU must be unique"

      - name: category_exists
        field: category_id
        rule: "EXISTS(SELECT 1 FROM category WHERE id = category_id)"
        message: "Selected category does not exist"

      - name: inventory_non_negative
        field: inventory_count
        rule: "inventory_count >= 0"
        message: "Inventory count cannot be negative"

      - name: weight_reasonable
        field: weight_kg
        rule: "weight_kg IS NULL OR (weight_kg > 0 AND weight_kg < 1000)"
        message: "Weight must be between 0 and 1000 kg"
```

### Financial Transaction

```yaml
patterns:
  - name: validation
    description: "Financial transaction validation"
    rules:
      - name: amount_positive
        field: amount
        rule: "amount > 0"
        message: "Transaction amount must be positive"

      - name: sufficient_balance
        fields: [amount, account_id]
        rule: "get_account_balance(account_id) >= amount"
        message: "Insufficient account balance"

      - name: valid_account
        field: account_id
        rule: "EXISTS(SELECT 1 FROM account WHERE id = account_id AND status = 'active')"
        message: "Account not found or inactive"

      - name: currency_match
        fields: [currency, account_id]
        rule: "get_account_currency(account_id) = currency"
        message: "Transaction currency must match account currency"

      - name: daily_limit
        fields: [amount, account_id]
        rule: "get_today_transaction_total(account_id) + amount <= get_daily_limit(account_id)"
        message: "Transaction would exceed daily limit"

      - name: fraud_check
        fields: [amount, account_id, merchant_id]
        rule: "NOT is_suspicious_transaction(amount, account_id, merchant_id)"
        message: "Transaction flagged for fraud review"
```

## 🎯 Best Practices

### Rule Design
- **Clear messages** - Explain what's wrong and how to fix
- **Progressive validation** - Basic checks first, complex checks later
- **Consistent naming** - Descriptive rule names
- **Modular rules** - One rule per concept

### Performance
- **Index validated fields** - Speed up constraint checks
- **Cache reference data** - Avoid repeated lookups
- **Batch validation** - Validate multiple records together
- **Lazy validation** - Only validate when necessary

### Error Handling
- **User-friendly messages** - Technical but understandable
- **Actionable guidance** - Tell users how to fix issues
- **Error codes** - Consistent error identification
- **Logging** - Track validation failures for analysis

### Maintenance
- **Version validation rules** - Track rule changes
- **Test rule changes** - Ensure updates don't break existing data
- **Document business rules** - Explain why rules exist
- **Review periodically** - Update rules as business changes

## 🆘 Troubleshooting

### "Validation rule not enforced"
```sql
-- Check if constraint exists
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'user'::regclass;

-- Check trigger exists
SELECT tgname, pg_get_triggerdef(oid)
FROM pg_trigger
WHERE tgrelid = 'user'::regclass;
```

### "False positive validation errors"
```yaml
# Check rule logic
patterns:
  - name: validation
    rules:
      - name: age_check
        field: age
        rule: "age IS NULL OR age >= 18"  # Allow NULL values
```

### "Performance issues with validation"
```yaml
# Add indexes for validation rules
indexes:
  - fields: [email]              # For email uniqueness
  - fields: [status, email]      # For conditional uniqueness
  - fields: [start_date, end_date]  # For date range checks
```

### "Complex validation rules slow"
```yaml
# Simplify or optimize rules
patterns:
  - name: validation
    rules:
      - name: optimized_check
        field: status
        rule: "status IN ('active', 'inactive')"  # Simple IN check
        # Instead of complex CASE statement
```

## 🎉 Summary

Validation patterns provide:
- ✅ **Data integrity** - Enforce business rules automatically
- ✅ **Clear error messages** - Helpful feedback for users
- ✅ **Consistent validation** - Same rules across all operations
- ✅ **Comprehensive testing** - Full validation coverage
- ✅ **Flexible configuration** - Adapt to complex business needs

## 🚀 What's Next?

- **[Composing Patterns](composing-patterns.md)** - Combining multiple patterns
- **[State Machines](state-machines.md)** - Entity lifecycle management
- **[Multi-Entity Operations](multi-entity.md)** - Cross-table transactions
- **[Examples](../../examples/)** - Real-world validation patterns

**Ready to ensure data quality? Let's continue! 🚀**