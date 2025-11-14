# Composing Patterns

**Pattern composition** combines multiple mutation patterns to create complex business logic. Learn how to effectively combine patterns like state machines, validation, and multi-entity operations for comprehensive solutions.

## 🎯 What You'll Learn

- Pattern composition concepts and strategies
- Combining multiple patterns effectively
- Pattern interaction and conflict resolution
- Complex business logic implementation
- Testing composed patterns

## 📋 Prerequisites

- [Pattern basics](getting-started.md)
- Understanding of individual patterns
- Knowledge of business process modeling

## 💡 Composition Concepts

### Why Compose Patterns?

**Individual patterns** solve specific problems:
- State machines manage status transitions
- Validation enforces data rules
- Multi-entity handles cross-table operations

**Pattern composition** creates complete solutions:

```yaml
# Complex order processing combining multiple patterns
patterns:
  # State management
  - name: state_machine
    states: [pending, confirmed, shipped, delivered]

  # Data validation
  - name: validation
    rules:
      - name: valid_shipping
        rule: "shipping_address IS NOT NULL OR digital_delivery = true"

  # Cross-table operations
  - name: multi_entity
    operation: process_order_fulfillment
    entities: [order, order_item, inventory, shipment]
```

**Benefits:**
- **Holistic solutions** - Address complete business processes
- **Consistency** - Unified rules across operations
- **Maintainability** - Declarative complex logic
- **Testing** - Comprehensive coverage of interactions

### Composition Strategies

| Strategy | Purpose | Example |
|----------|---------|---------|
| **Sequential** | Step-by-step workflow | Order: validate → confirm → ship |
| **Parallel** | Independent validations | User: email format + age check + uniqueness |
| **Conditional** | Context-dependent logic | Premium users get different validation |
| **Hierarchical** | Nested operations | Order contains line items with their own patterns |

## 🏗️ Basic Composition

### Order Processing Example

```yaml
# entities/order.yaml
name: order
fields:
  id: uuid
  customer_id: uuid
  status: string
  total_amount: decimal
  shipping_address: text?
  digital_delivery: boolean

patterns:
  # 1. State Machine - Order lifecycle
  - name: state_machine
    description: "Order processing workflow"
    initial_state: pending
    states: [pending, confirmed, processing, shipped, delivered, cancelled]

    transitions:
      - from: pending
        to: confirmed
        trigger: confirm_order
        guard: "total_amount > 0"
        action: "send_order_confirmation"

      - from: confirmed
        to: processing
        trigger: start_processing
        action: "reserve_inventory"

      - from: processing
        to: shipped
        trigger: ship_order
        guard: "shipping_address IS NOT NULL OR digital_delivery = true"
        action: "create_shipment"

      - from: shipped
        to: delivered
        trigger: mark_delivered
        action: "send_delivery_notification"

  # 2. Validation - Business rules
  - name: validation
    description: "Order data integrity"
    rules:
      - name: positive_total
        field: total_amount
        rule: "total_amount > 0"
        message: "Order total must be positive"

      - name: shipping_required
        fields: [shipping_address, digital_delivery]
        rule: "digital_delivery = true OR shipping_address IS NOT NULL"
        message: "Shipping address required for physical delivery"

      - name: customer_exists
        field: customer_id
        rule: "EXISTS(SELECT 1 FROM customer WHERE id = customer_id)"
        message: "Customer not found"

  # 3. Multi-Entity - Complex operations
  - name: multi_entity
    description: "Complete order fulfillment"
    operation: fulfill_order
    entities: [order, order_item, inventory, shipment]

    steps:
      - validate: order
        condition: "status = 'confirmed'"

      - update: order
        data:
          status: processing
        where: "id = :order_id"

      - update: order_item
        data:
          status: processing
        where: "order_id = :order_id"

      - update: inventory
        for_each: "SELECT product_id, quantity FROM order_item WHERE order_id = :order_id"
        data:
          quantity: "quantity - :item.quantity"
        where: "product_id = :item.product_id"

      - create: shipment
        condition: "NOT :digital_delivery"
        data:
          order_id: :order_id
          status: pending
          address: :shipping_address
```

## ⚙️ Advanced Composition

### Conditional Pattern Application

```yaml
patterns:
  # Base validation for all orders
  - name: validation
    description: "Basic order validation"
    rules:
      - name: total_positive
        field: total_amount
        rule: "total_amount > 0"

  # Additional validation for premium customers
  - name: validation
    description: "Premium customer validation"
    condition: "is_premium_customer(customer_id)"  # Only apply if true
    rules:
      - name: credit_check
        fields: [customer_id, total_amount]
        rule: "get_customer_credit_limit(customer_id) >= total_amount"
        message: "Order exceeds credit limit"

  # Different processing for digital vs physical
  - name: state_machine
    description: "Digital order workflow"
    condition: "digital_delivery = true"
    states: [pending, confirmed, delivered]
    transitions:
      - from: pending
        to: confirmed
        trigger: confirm
      - from: confirmed
        to: delivered
        trigger: deliver_digital
        action: "send_download_link"

  - name: state_machine
    description: "Physical order workflow"
    condition: "digital_delivery = false"
    states: [pending, confirmed, processing, shipped, delivered]
    transitions:
      - from: pending
        to: confirmed
        trigger: confirm
      - from: confirmed
        to: processing
        trigger: process
      - from: processing
        to: shipped
        trigger: ship
      - from: shipped
        to: delivered
        trigger: deliver
```

### Pattern Dependencies

```yaml
patterns:
  # 1. Validation runs first
  - name: validation
    description: "Pre-checks"
    priority: 1
    rules:
      - name: basic_checks
        rule: "data_is_valid()"

  # 2. State machine depends on validation
  - name: state_machine
    description: "Status transitions"
    priority: 2
    depends_on: [validation]  # Must pass validation first
    transitions:
      - from: pending
        to: approved
        guard: "validation_passed = true"

  # 3. Multi-entity runs after state change
  - name: multi_entity
    description: "Business operations"
    priority: 3
    depends_on: [state_machine]
    steps:
      - condition: "status = 'approved'"  # Only if approved
```

### Cross-Pattern Data Flow

```yaml
patterns:
  # Validation collects metadata
  - name: validation
    description: "Data quality checks"
    collect_metadata: true
    rules:
      - name: quality_score
        field: data_quality
        rule: "calculate_quality_score(ALL_FIELDS) > 0.8"

  # State machine uses validation results
  - name: state_machine
    description: "Quality-based routing"
    transitions:
      - from: pending
        to: approved
        guard: "validation_metadata.quality_score > 0.9"
      - from: pending
        to: review
        guard: "validation_metadata.quality_score BETWEEN 0.7 AND 0.9"
      - from: pending
        to: rejected
        guard: "validation_metadata.quality_score < 0.7"

  # Multi-entity operation varies by path
  - name: multi_entity
    description: "Path-specific processing"
    steps:
      - condition: "status = 'approved'"
        then:
          - action: process_high_quality_order
      - condition: "status = 'review'"
        then:
          - action: queue_for_manual_review
      - condition: "status = 'rejected'"
        then:
          - action: send_rejection_notification
```

## 🔄 Pattern Interaction Patterns

### State Machine + Validation

```yaml
patterns:
  - name: state_machine
    description: "Application approval process"
    states: [draft, submitted, under_review, approved, rejected]

    transitions:
      - from: draft
        to: submitted
        trigger: submit
        # Validation runs automatically before transition
        validations: [required_fields, business_rules]

      - from: submitted
        to: under_review
        trigger: start_review
        validations: [compliance_check]

      - from: under_review
        to: approved
        trigger: approve
        validations: [final_approval_check]

  - name: validation
    description: "Application validation rules"
    rules:
      - name: required_fields
        rule: "application_is_complete()"
        message: "All required fields must be filled"

      - name: business_rules
        rule: "meets_business_criteria()"
        message: "Application does not meet business requirements"

      - name: compliance_check
        rule: "passes_compliance_review()"
        message: "Application failed compliance review"
```

### Multi-Entity + State Machine

```yaml
patterns:
  - name: state_machine
    description: "Order fulfillment states"
    states: [confirmed, processing, shipped, delivered]

    transitions:
      - from: confirmed
        to: processing
        trigger: start_processing
        # Triggers multi-entity operation
        action: fulfill_order

      - from: processing
        to: shipped
        trigger: mark_shipped
        action: update_shipping_status

  - name: multi_entity
    description: "Order fulfillment process"
    operation: fulfill_order
    entities: [order, order_item, inventory, shipment]

    steps:
      # Update order status
      - update: order
        data:
          status: processing
        where: "id = :order_id"

      # Process each item
      - for_each: order_items
        do:
          - update: inventory
            data:
              quantity: "quantity - :item.quantity"
            where: "product_id = :item.product_id"

      # Create shipment
      - create: shipment
        data:
          order_id: :order_id
          items: :order_items
          status: pending
```

### Validation + Multi-Entity

```yaml
patterns:
  - name: validation
    description: "Pre-operation validation"
    rules:
      - name: inventory_available
        rule: "all_items_in_stock(:order_items)"
        message: "Some items are out of stock"

      - name: payment_cleared
        rule: "payment_is_cleared(:payment_id)"
        message: "Payment has not cleared"

      - name: shipping_possible
        rule: "shipping_address_valid(:shipping_address)"
        message: "Shipping address is invalid"

  - name: multi_entity
    description: "Order placement"
    operation: place_order
    entities: [order, order_item, payment, shipment]
    # Validation runs before any changes
    precondition_validations: [inventory_available, payment_cleared, shipping_possible]

    steps:
      - create: order
        data:
          customer_id: :customer_id
          total: :total
          status: confirmed

      - create: order_item
        for_each: :items
        data:
          order_id: :order.id
          product_id: :item.product_id
          quantity: :item.quantity

      - update: payment
        data:
          status: captured
        where: "id = :payment_id"

      - create: shipment
        data:
          order_id: :order.id
          address: :shipping_address
          status: pending
```

## 🧪 Testing Composed Patterns

### Integration Testing

```bash
# Generate tests for all patterns
specql generate tests entities/order.yaml

# Run comprehensive test suite
specql test run entities/order.yaml

# Run specific pattern tests
specql test run --pattern state_machine entities/order.yaml
specql test run --pattern validation entities/order.yaml
specql test run --pattern multi_entity entities/order.yaml
```

**Test Coverage:**
- ✅ **Pattern interactions** - How patterns work together
- ✅ **Data flow** - Information passing between patterns
- ✅ **Conflict resolution** - When patterns have conflicting rules
- ✅ **Error propagation** - How errors flow through composed patterns
- ✅ **Performance** - Impact of multiple patterns

### Manual Integration Testing

```sql
-- Test complete order workflow
SELECT place_order(
  customer_id := 'customer-uuid'::UUID,
  items := '[
    {"product_id": "prod-1", "quantity": 2},
    {"product_id": "prod-2", "quantity": 1}
  ]'::JSONB,
  payment_id := 'payment-uuid'::UUID,
  shipping_address := '123 Main St'
);

-- Verify state machine progression
SELECT status FROM order WHERE customer_id = 'customer-uuid';

-- Verify validation rules applied
-- (Should fail if invalid data provided)

-- Verify multi-entity operation completed
SELECT * FROM order_item WHERE order_id IN (
  SELECT id FROM order WHERE customer_id = 'customer-uuid'
);
```

## 🚀 Real-World Examples

### E-commerce Order Management

```yaml
patterns:
  # State machine for order lifecycle
  - name: state_machine
    states: [cart, pending, confirmed, processing, shipped, delivered, cancelled, refunded]

  # Validation for business rules
  - name: validation
    rules:
      - name: inventory_check
        rule: "all_items_available(order_items)"
      - name: payment_validation
        rule: "payment_amount_matches_order_total(payment, order)"
      - name: shipping_validation
        rule: "shipping_address_complete(order)"

  # Multi-entity for order fulfillment
  - name: multi_entity
    operation: fulfill_order
    entities: [order, order_item, inventory, shipment, payment]

  # Audit trail for compliance
  - name: audit_trail
    track_fields: [status, total_amount]
    track_changes: true
```

### User Onboarding Process

```yaml
patterns:
  # State machine for onboarding steps
  - name: state_machine
    states: [registered, email_verified, profile_complete, payment_setup, active]

  # Validation at each step
  - name: validation
    rules:
      - name: email_verification
        condition: "status = 'registered'"
        rule: "email_verified = true"
      - name: profile_completion
        condition: "status = 'email_verified'"
        rule: "profile_is_complete(user_profile)"
      - name: payment_setup
        condition: "status = 'profile_complete'"
        rule: "payment_method_configured(user)"

  # Multi-entity for account setup
  - name: multi_entity
    operation: complete_onboarding
    entities: [user, user_profile, payment_method, notification_settings]
```

### Content Publishing Workflow

```yaml
patterns:
  # State machine for content states
  - name: state_machine
    states: [draft, review, approved, published, archived]

  # Validation for content quality
  - name: validation
    rules:
      - name: content_quality
        rule: "content_meets_quality Standards(title, body, tags)"
      - name: editorial_approval
        condition: "status = 'review'"
        rule: "editorial_review_passed(content)"

  # Multi-entity for publishing process
  - name: multi_entity
    operation: publish_content
    entities: [content, content_version, author, category, tags]

  # Versioning for content history
  - name: versioning
    track_changes: true
    keep_versions: 10
```

## 🎯 Best Practices

### Composition Design
- **Start simple** - Add patterns incrementally
- **Clear separation** - Each pattern has single responsibility
- **Explicit dependencies** - Define pattern execution order
- **Test interactions** - Verify pattern combinations work

### Conflict Resolution
- **Priority system** - Higher priority patterns override lower ones
- **Condition scoping** - Apply patterns only when relevant
- **Override mechanisms** - Allow specific pattern customization
- **Documentation** - Explain why patterns are combined

### Performance Considerations
- **Execution order** - Fast validations first
- **Caching** - Cache expensive validation results
- **Batch operations** - Group similar validations
- **Lazy evaluation** - Only run patterns when needed

### Maintenance
- **Modular patterns** - Easy to add/remove patterns
- **Version compatibility** - Track pattern version compatibility
- **Rollback planning** - Know how to undo complex operations
- **Monitoring** - Track pattern performance and errors

## 🆘 Troubleshooting

### "Pattern conflicts"
```yaml
# Use conditions to avoid conflicts
patterns:
  - name: validation
    condition: "user_type = 'regular'"
    rules: [...]
  - name: validation
    condition: "user_type = 'admin'"
    rules: [...]  # Different rules for admins
```

### "Performance degradation"
```yaml
# Optimize execution order
patterns:
  - name: validation
    priority: 1  # Fast checks first
    rules: [...]
  - name: multi_entity
    priority: 2  # Complex operations later
    steps: [...]
```

### "Unexpected validation failures"
```bash
# Debug pattern interactions
specql validate entities/order.yaml --verbose --debug-patterns

# Check pattern execution order
specql generate schema entities/order.yaml --show-pattern-order
```

### "State machine not progressing"
```sql
-- Check guard conditions
SELECT
  status,
  total_amount > 0 as valid_total,
  payment_received = true as payment_cleared
FROM order WHERE id = 'order-id';

-- Check validation status
SELECT * FROM validation_results
WHERE entity_id = 'order-id';
```

## 🎉 Summary

Pattern composition enables:
- ✅ **Complex business logic** - Combine simple patterns into sophisticated workflows
- ✅ **Consistent behavior** - Unified rules across all operations
- ✅ **Maintainable code** - Declarative approach to complex processes
- ✅ **Comprehensive testing** - Full coverage of pattern interactions
- ✅ **Flexible architecture** - Adapt to changing business needs

## 🚀 What's Next?

- **[Examples](../../examples/)** - Real-world composed pattern implementations
- **[Custom Patterns](custom-patterns.md)** - Create your own patterns
- **[Performance Tuning](../best-practices/performance.md)** - Optimize pattern execution
- **[Troubleshooting](../troubleshooting/)** - Debug pattern issues

**Ready to build complex business systems? Let's continue! 🚀**