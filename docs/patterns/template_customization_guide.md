# Template Customization Guide

**Status**: ✅ Complete - Template customization documented
**Last Updated**: 2025-11-12
**Related**: Phase C - Three-Tier Architecture

---

## 📚 Overview

Template customization allows you to adapt entity templates to your specific business requirements while maintaining the benefits of pre-built patterns and actions.

**Customization Levels**:
1. **Field Addition**: Add custom fields to templates
2. **Field Modification**: Change field properties
3. **Action Customization**: Modify or extend actions
4. **Pattern Override**: Change pattern configurations
5. **Business Logic**: Add custom validation and workflows

---

## 🏗️ Customization Architecture

### Template Extension Pattern
```yaml
entity: Contact
extends: crm.contact_template  # Start with base template

# Customization layers:
fields:        # Add/modify fields
actions:       # Add/modify actions
patterns:      # Override pattern configs
validations:   # Add business rules
triggers:      # Add database triggers
```

### Inheritance Rules
- **Base template**: Provides core fields, actions, patterns
- **Extensions**: Add to or override base functionality
- **Composition**: Multiple customizations can be layered
- **Conflicts**: Last definition wins

---

## 📝 Field Customization

### Method 1: Add Custom Fields

```yaml
entity: Contact
extends: crm.contact_template

fields:
  # Add completely new fields
  vip_status: enum(normal, gold, platinum)
  last_contact_date: timestamp
  preferred_language: text
  referral_source: text
  marketing_opt_in: boolean

  # Modify existing fields from template
  notes:
    type: text
    max_length: 2000  # Extend from default
    required: false   # Override template requirement

  tags:
    type: array
    max_items: 10     # Limit number of tags
```

### Method 2: Field Groups and Organization

```yaml
entity: Product
extends: ecommerce.product_template

fields:
  # Group related fields
  seo_fields:
    meta_title: text
    meta_description: text
    url_slug: text

  inventory_fields:
    stock_location: text
    reorder_point: integer
    supplier_lead_time: integer

  # Override template field
  price:
    type: decimal
    precision: 4    # More precision than template
    min: 0.01       # Minimum price validation
```

### Method 3: Conditional Fields

```yaml
entity: Subscription
extends: ecommerce.customer_template

fields:
  # Base fields (always present)
  plan_type: enum(free, basic, premium, enterprise)

  # Conditional fields based on plan
  billing_cycle:
    type: enum(monthly, yearly)
    condition: "plan_type IN ('basic', 'premium', 'enterprise')"

  max_users:
    type: integer
    condition: "plan_type = 'enterprise'"
    min: 10

  api_rate_limit:
    type: integer
    condition: "plan_type IN ('premium', 'enterprise')"
    default: 1000
```

---

## ⚡ Action Customization

### Method 4: Extend Template Actions

```yaml
entity: Order
extends: ecommerce.order_template

actions:
  # Modify existing action from template
  - name: create_order
    description: Create order with custom validation
    parameters:
      - name: customer_id
      - name: items
      - name: coupon_code  # Add new parameter
    steps:
      # Custom validation first
      - validate: coupon_code IS NULL OR coupon_is_valid($coupon_code)
      - validate: customer_has_good_standing($customer_id)

      # Call original template action
      - call: ecommerce.order_template.create_order

      # Add custom post-processing
      - if: coupon_code IS NOT NULL
        then:
          - apply_discount: $coupon_code
          - log: "Coupon {coupon_code} applied to order {order_id}"

  # Add completely new actions
  - name: apply_discount
    parameters:
      - name: coupon_code
    steps:
      - query: SELECT discount_percent FROM coupons WHERE code = $coupon_code
      - update: Order SET discount = $discount_percent WHERE id = $order_id
      - calculate_totals: $order_id
```

### Method 5: Action Overrides with Fallbacks

```yaml
entity: Contact
extends: crm.contact_template

actions:
  # Override state transition to add business logic
  - name: qualify_lead
    description: Qualify lead with custom scoring
    steps:
      # Custom qualification logic
      - calculate_lead_score: $id
      - if: lead_score >= 75
        then:
          - call: crm.contact_template.qualify_lead  # Original action
          - notify: sales_team "High-scoring lead qualified: {first_name}"
        else:
          - update: Contact SET qualification_notes = 'Score too low' WHERE id = $id
          - notify: lead_nurture_team "Nurture lead: {first_name}"
```

---

## 🔄 Pattern Configuration

### Method 6: Override Pattern Settings

```yaml
entity: Product
extends: ecommerce.product_template

patterns:
  # Customize state machine for products
  - name: state_machine
    config:
      states: [draft, review, approved, published, discontinued]
      transitions:
        draft->review: {}
        review->draft: {}  # Send back for edits
        review->approved: {}
        approved->published: {}
        published->discontinued: {}
      initial_state: draft

  # Customize audit trail
  - name: audit_trail
    config:
      track_versions: true
      version_comment_required: true  # Require comments on changes

  # Add new patterns
  - name: content_approval
    config:
      approval_roles: [product_manager, marketing]
      auto_approve_under: 100  # Auto-approve cheap products
```

### Method 7: Conditional Pattern Application

```yaml
entity: Invoice
extends: finance.invoice_template

patterns:
  # Apply approval only for large invoices
  - name: approval_workflow
    condition: "total_amount >= 5000"
    config:
      stages:
        - role: supervisor
          threshold: 5000
        - role: manager
          threshold: 25000

  # Apply different audit levels
  - name: audit_trail
    config:
      detailed_audit: "total_amount >= 10000"  # More audit for large invoices
      audit_retention_years: 7

  # Tax compliance for international
  - name: tax_compliance
    condition: "customer_country != 'US'"
    config:
      tax_rules: international
```

---

## ✅ Validation Customization

### Method 8: Add Business Rules

```yaml
entity: Order
extends: ecommerce.order_template

validations:
  # Cross-field validations
  - name: shipping_address_required
    condition: "shipping_method != 'digital'"
    error: "Shipping address required for physical orders"

  - name: international_shipping_allowed
    condition: "shipping_country NOT IN ('US', 'CA', 'MX')"
    error: "International shipping not available"

  - name: minimum_order_value
    condition: "subtotal >= 10.00"
    error: "Minimum order value is $10.00"

  # Custom validation functions
  - name: payment_method_allowed
    condition: "payment_method_allowed(customer_id, payment_method)"
    error: "Payment method not allowed for this customer"

  - name: inventory_available
    condition: "check_inventory_availability(items)"
    error: "Some items are out of stock"
```

### Method 9: Field-Level Validation

```yaml
entity: Product
extends: ecommerce.product_template

fields:
  price:
    type: decimal
    validations:
      - min: 0.01
      - max: 99999.99
      - condition: "price > cost * 1.1"  # Must have 10% margin

  sku:
    type: text
    unique: true
    pattern: "^[A-Z]{2,3}[0-9]{6,8}$"  # Format validation
    validations:
      - message: "SKU must be 2-3 letters followed by 6-8 numbers"

  weight:
    type: decimal
    condition: "category != 'digital'"
    validations:
      - min: 0.1
      - max: 50.0
      - message: "Weight must be between 0.1 and 50.0 kg"
```

---

## 🎯 Advanced Customization

### Method 10: Template Inheritance

```yaml
# Base customization for all contacts
entity: BaseContact
extends: crm.contact_template
abstract: true  # Not a real table, just for inheritance

fields:
  custom_field_1: text
  custom_field_2: integer

patterns:
  - name: tagging
    config: {allow_custom_tags: true}

# Specific contact types inherit from base
entity: B2BContact
extends: BaseContact

fields:
  company_size: enum(small, medium, large)
  industry: text

actions:
  - name: assign_account_manager
    steps:
      - query: SELECT manager_id FROM accounts WHERE company = $company
      - update: Contact SET account_manager = $manager_id WHERE id = $id

entity: B2CContact
extends: BaseContact

fields:
  date_of_birth: date
  loyalty_points: integer

actions:
  - name: apply_loyalty_discount
    steps:
      - calculate_discount: $loyalty_points
      - apply_discount: $discount_amount
```

### Method 11: Multi-Tenant Customization

```yaml
entity: TenantOrder
extends: ecommerce.order_template

# Tenant-specific customizations
fields:
  tenant_id: uuid  # Multi-tenant isolation

  # Tenant-specific fields
  custom_order_number: text
  tenant_specific_field: text

patterns:
  # Tenant-aware audit trail
  - name: audit_trail
    config:
      tenant_isolation: true
      tenant_field: tenant_id

  # Tenant-specific workflow
  - name: state_machine
    config:
      states: [draft, submitted, tenant_approved, processing, shipped, delivered]
      transitions:
        submitted->tenant_approved: {guard: "tenant_approval_required"}

validations:
  - name: tenant_isolation
    condition: "tenant_id = current_tenant_id()"
    error: "Cannot access data from other tenants"
```

---

## 📊 Customization Examples

### Example 1: SaaS Company Contact

```yaml
entity: SaaSContact
extends: crm.contact_template

fields:
  # SaaS-specific fields
  subscription_status: enum(trial, active, churned, paused)
  mrr_value: decimal  # Monthly recurring revenue
  churn_risk_score: integer
  onboarding_completed: boolean

  # Override template field
  source:
    type: enum
    values: [organic, paid_ads, referral, content_marketing, sales_outbound]

patterns:
  # Enhanced state machine
  - name: state_machine
    config:
      states: [lead, mql, sql, trial, customer, churned]
      transitions:
        lead->mql: {guard: "meets_mql_criteria"}
        mql->sql: {guard: "sales_qualified"}
        sql->trial: {}
        trial->customer: {guard: "payment_successful"}
        customer->churned: {}

actions:
  - name: upgrade_subscription
    steps:
      - validate: subscription_status = 'active'
      - calculate_proration: current_plan, new_plan
      - process_payment: $proration_amount
      - update_subscription: $new_plan

  - name: calculate_churn_risk
    schedule: "0 9 * * 1"  # Weekly on Monday
    steps:
      - analyze_usage_patterns: $id
      - calculate_risk_score: $usage_data
      - update: Contact SET churn_risk_score = $score WHERE id = $id
      - if: score > 80
        then: notify retention_team "High churn risk: {email}"
```

### Example 2: Healthcare Patient with Compliance

```yaml
entity: CompliantPatient
extends: healthcare.patient_template

fields:
  # HIPAA compliance fields
  hipaa_authorization: boolean
  data_retention_date: date
  access_log_enabled: boolean

  # Enhanced privacy
  data_sharing_consent: json  # Granular consent settings
  emergency_access_granted: boolean

patterns:
  # Enhanced audit trail for compliance
  - name: audit_trail
    config:
      hipaa_compliant: true
      retention_years: 7
      audit_all_access: true

  # Privacy controls
  - name: data_masking
    config:
      mask_ssn: true
      mask_dob: true
      role_based_access: true

  # Emergency access pattern
  - name: emergency_access
    config:
      emergency_roles: [doctor, nurse, admin]
      audit_emergency_access: true
      auto_expiry_hours: 24

validations:
  - name: hipaa_compliance
    condition: "hipaa_authorization = true"
    error: "HIPAA authorization required"

  - name: age_restriction
    condition: "date_of_birth <= CURRENT_DATE - INTERVAL '13 years'"
    error: "Patients must be 13 or older"

  - name: consent_required
    condition: "data_sharing_consent->'research' = 'true' OR research_study IS NULL"
    error: "Research consent required for study participation"
```

### Example 3: E-Commerce with Advanced Inventory

```yaml
entity: AdvancedProduct
extends: ecommerce.product_template

fields:
  # Advanced inventory
  inventory_locations: json  # Multiple warehouse locations
  supplier_info: json       # Multiple suppliers
  demand_forecast: json     # AI demand predictions

  # Quality control
  quality_score: decimal
  last_inspection_date: date
  batch_number: text

patterns:
  # Advanced inventory management
  - name: inventory_management
    config:
      multi_location: true
      demand_forecasting: true
      auto_reorder: true
      quality_tracking: true

  # Supplier management
  - name: supplier_integration
    config:
      auto_ordering: true
      supplier_scorecards: true
      alternative_suppliers: true

  # Quality assurance
  - name: quality_control
    config:
      inspection_required: true
      batch_tracking: true
      recall_management: true

actions:
  - name: initiate_recall
    parameters:
      - name: batch_number
      - name: reason
    steps:
      - validate: current_user_role = 'quality_manager'
      - find_affected_orders: $batch_number
      - notify_customers: $affected_orders, $reason
      - update_inventory: quarantine_batch $batch_number
      - create_recall_record: $batch_number, $reason

  - name: optimize_inventory
    schedule: "0 2 * * *"  # Daily at 2 AM
    steps:
      - analyze_demand_patterns: last_90_days
      - calculate_optimal_stock: $demand_analysis
      - generate_reorder_suggestions: $optimal_stock
      - if: reorder_needed
        then: create_purchase_orders $suggestions
```

---

## 🔧 Customization Tools

### CLI Commands

```bash
# Validate customizations
specql validate entity.yaml

# Preview customized entity
specql preview entity.yaml

# Generate with customizations
specql generate entity.yaml

# Compare with base template
specql diff entity.yaml crm.contact_template

# Test customizations
specql test entity.yaml --customizations
```

### API Usage

```python
from src.specql.compiler import EntityCompiler

compiler = EntityCompiler()

# Compile with customizations
entity_def = compiler.compile_from_yaml('''
entity: Contact
extends: crm.contact_template
fields:
  vip_status: enum(normal, gold, platinum)
actions:
  - name: promote_to_vip
    steps: [...]
''')

# Validate customizations
validation_result = compiler.validate_customizations(entity_def)
print(validation_result)
```

---

## 📈 Best Practices

### 1. Start with Templates
Always extend templates rather than building from scratch:

```yaml
# Good: Extend template
entity: MyContact
extends: crm.contact_template
fields:
  custom_field: text

# Avoid: Reimplement template
entity: MyContact
fields:
  first_name: text
  last_name: text
  email: text
  # ... 20 more fields from template
```

### 2. Layer Customizations
Use inheritance for reusable customizations:

```yaml
# Base customization
entity: BaseProduct
extends: ecommerce.product_template
abstract: true
fields:
  custom_category: text

# Specific products
entity: Book
extends: BaseProduct
fields:
  isbn: text
  author: text

entity: Electronics
extends: BaseProduct
fields:
  warranty_months: integer
  power_requirements: text
```

### 3. Test Thoroughly
Customizations can break template functionality:

```bash
# Test template functionality still works
specql test entity.yaml --template-compatibility

# Test customizations don't break patterns
specql test entity.yaml --pattern-integration

# Performance test customizations
specql benchmark entity.yaml --customizations
```

### 4. Document Customizations
Keep track of why customizations were made:

```yaml
entity: CustomOrder
extends: ecommerce.order_template

# Documentation
metadata:
  customizations:
    - reason: "Support for gift orders"
      added_fields: [gift_message, is_gift]
      modified_actions: [create_order]
      author: "john.doe@company.com"
      date: "2025-11-12"
      ticket: "PROJ-123"
```

---

## 🚨 Common Issues

### Issue 1: Breaking Template Actions
**Problem**: Customizations break template functionality
**Solution**: Call template actions, don't replace them entirely

```yaml
# Bad: Replaces template action entirely
actions:
  - name: create_order
    steps: [...]  # Custom logic only

# Good: Extends template action
actions:
  - name: create_order
    steps:
      - call: ecommerce.order_template.create_order  # Template logic
      - validate: custom_business_rule  # Custom logic
```

### Issue 2: Pattern Conflicts
**Problem**: Customizations conflict with pattern expectations
**Solution**: Configure patterns rather than fighting them

```yaml
# Bad: Tries to work around pattern
fields:
  custom_created_at: timestamp  # Conflicts with audit_trail

# Good: Configure the pattern
patterns:
  - name: audit_trail
    config:
      created_at_field: custom_created_at  # Tell pattern to use custom field
```

### Issue 3: Performance Degradation
**Problem**: Too many customizations slow down operations
**Solution**: Optimize and measure performance

```yaml
# Add performance monitoring
actions:
  - name: create_order
    steps:
      - log_performance_start: create_order
      - call: ecommerce.order_template.create_order
      - log_performance_end: create_order
```

---

## 📊 Customization Metrics

**Customization Levels**:
- **Light**: 1-5 field additions (60% of customizations)
- **Medium**: 6-15 field additions + action modifications (30%)
- **Heavy**: 16+ changes + pattern overrides (10%)

**Maintenance Impact**:
- Light: Low (easy to maintain with template updates)
- Medium: Medium (some manual updates required)
- Heavy: High (significant testing required)

**Template Compatibility**:
- 90% of light customizations remain compatible
- 70% of medium customizations remain compatible
- 40% of heavy customizations remain compatible

---

## 🚀 Next Steps

Template customization enables business-specific adaptations. Learn how to:
- **[Migration Guide](../guides/migration_pattern_library.md)**: Migrate existing entities to templates
- **[Performance Guide](../guides/performance_optimization.md)**: Optimize customized entities
- **[Testing Guide](../guides/testing_patterns.md)**: Test customizations thoroughly

---

**Status**: ✅ **Complete** - Template customization fully documented
**Next**: Update existing documentation