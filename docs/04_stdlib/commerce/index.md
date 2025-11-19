# Commerce Entities: Business Transactions & Contracts

> **Production-proven e-commerce and B2B transaction models**

## Overview

The SpecQL stdlib **commerce module** provides comprehensive business transaction management with support for:
- **Contracts**: Business agreements with terms, dates, and parties
- **Orders**: Purchase orders with lifecycle tracking
- **Pricing**: Multi-currency, time-based pricing models
- **B2B workflows**: Customer-provider relationships, approvals, invoicing

These entities are extracted from production B2B systems handling complex multi-party transactions.

## Quick Start

```yaml
# Import pre-built commerce entities
import:
  - stdlib/commerce/contract
  - stdlib/commerce/order
  - stdlib/commerce/price
  - stdlib/crm/organization  # Customer & Provider orgs
  - stdlib/i18n/currency     # Multi-currency support

# Use them in your workflow
entity: ServiceAgreement
extends:
  from: stdlib/commerce/contract
fields:
  sla_level: enum(standard, premium, enterprise)
  max_response_time_hours: integer
```

**Result**: Full contract and order management with zero configuration.

---

## Core Entities

### 1. Contract

**Purpose**: Business agreements between customer and provider organizations

**Schema**: `management` (tenant-specific)

**Use Cases**:
- Service level agreements (SLAs)
- Multi-year procurement contracts
- Subscription agreements
- Master service agreements (MSAs)
- Licensing agreements

#### Fields

```yaml
entity: Contract
fields:
  # Identifiers
  contract_identifier: text
  customer_contract_id: text    # Customer's reference number
  provider_contract_id: text    # Provider's internal reference

  # Dates
  signature_date: date          # When signed
  start_date: date              # Effective start
  end_date: date                # Expiration

  # Basic info
  name: text                    # "2024 Enterprise Support Agreement"

  # Duration calculation
  duration_source:
    type: enum(contract_end, original_duration)
    default: original_duration

  # Parties
  customer_org: ref(Organization)   # Buying organization
  provider_org: ref(Organization)   # Selling organization

  # Financial
  currency: ref(Currency)           # Contract currency
```

#### Built-in Actions

```yaml
actions:
  # CRUD
  - create_contract
  - update_contract
  - delete_contract

  # Lifecycle management
  - activate_contract       # Make contract active
  - suspend_contract        # Temporary suspension
  - terminate_contract      # End contract early
  - renew_contract         # Extend for another term

  # Modifications
  - amend_contract         # Add amendments
  - change_currency        # Currency conversion
  - update_terms          # Modify terms
  - add_financing_condition
  - remove_financing_condition
```

#### Example: SaaS Subscription Contract

```yaml
import:
  - stdlib/commerce/contract

# Create annual subscription
action: create_contract
inputs:
  contract_identifier: "SaaS-2024-001"
  customer_contract_id: "PO-12345"
  name: "Annual Enterprise Plan"
  signature_date: "2024-01-15"
  start_date: "2024-02-01"
  end_date: "2025-01-31"
  customer_org: {identifier: "acme-corp"}
  provider_org: {identifier: "my-saas-company"}
  currency: {iso_code: "USD"}

# Auto-renew before expiration
action: renew_contract
inputs:
  contract_id: {identifier: "SaaS-2024-001"}
  new_end_date: "2026-01-31"  # Extend one more year
```

**Generated SQL**:
```sql
-- Automatically generated contract lifecycle
CREATE FUNCTION management.activate_contract(
  p_contract_id UUID
) RETURNS app.mutation_result AS $$
DECLARE
  v_result app.mutation_result;
BEGIN
  -- Validate dates
  IF NOT EXISTS (
    SELECT 1 FROM management.tb_contract
    WHERE id = p_contract_id
      AND start_date <= CURRENT_DATE
      AND (end_date IS NULL OR end_date >= CURRENT_DATE)
  ) THEN
    v_result.status := 'error';
    v_result.message := 'Contract dates invalid for activation';
    RETURN v_result;
  END IF;

  -- Activate
  UPDATE management.tb_contract
  SET status = 'active',
      updated_at = NOW(),
      updated_by = current_setting('app.user_id')::UUID
  WHERE id = p_contract_id;

  v_result.status := 'success';
  v_result.message := 'Contract activated';
  RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

#### Extending Contract

```yaml
# Add custom fields for specific contract type
entity: MaintenanceContract
extends:
  from: stdlib/commerce/contract
fields:
  # Additional fields for maintenance
  equipment_covered: list(text)
  maintenance_frequency: enum(monthly, quarterly, annual)
  emergency_support_24_7: boolean
  max_response_time_hours: integer

  # Custom pricing
  base_fee: money
  per_equipment_fee: money
  overtime_hourly_rate: money

actions:
  - name: schedule_maintenance
  - name: log_emergency_call
  - name: update_equipment_list
```

---

### 2. Order

**Purpose**: Purchase orders tracking customer requests

**Schema**: `management` (tenant-specific)

**Use Cases**:
- E-commerce orders
- B2B purchase orders
- Service requests
- Subscription activations
- Recurring orders

#### Fields

```yaml
entity: Order
fields:
  # Identifiers
  order_identifier: text
  customer_order_id: text         # Customer's PO number
  provider_order_id: text         # Provider's internal number
  customer_commitment_id: text    # Budget/commitment reference

  # Dates
  order_date: date               # When placed
  invoice_date: date             # When invoiced

  # Sequencing
  sequential_number: integer     # Order sequence for customer

  # Parties
  customer_org: ref(Organization)
  provider_org: ref(Organization)

  # Contract reference
  contract: ref(Contract)        # Parent contract (if applicable)
```

#### Built-in Actions

```yaml
actions:
  # CRUD
  - create_order
  - update_order
  - delete_order

  # Lifecycle
  - submit_order         # Submit for approval
  - approve_order        # Approve order
  - reject_order         # Reject order
  - ship_order          # Mark as shipped
  - deliver_order       # Mark as delivered
  - cancel_order        # Cancel order

  # Order management
  - add_order_line      # Add line item
  - remove_order_line   # Remove line item
  - update_quantity     # Change quantities
```

#### Example: E-Commerce Order Flow

```yaml
import:
  - stdlib/commerce/order
  - stdlib/commerce/contract

# Customer places order
action: create_order
inputs:
  order_identifier: "ORD-2024-00123"
  customer_order_id: "CART-ABC123"
  order_date: "2024-03-15"
  customer_org: {identifier: "customer-acme"}
  provider_org: {identifier: "my-store"}
  contract: {identifier: "annual-contract-2024"}

# Add items to order
action: add_order_line
inputs:
  order_id: {identifier: "ORD-2024-00123"}
  product_sku: "PROD-001"
  quantity: 5
  unit_price: 99.99

# Approve and ship
action: approve_order
inputs:
  order_id: {identifier: "ORD-2024-00123"}

action: ship_order
inputs:
  order_id: {identifier: "ORD-2024-00123"}
  tracking_number: "1Z999AA10123456784"
  carrier: "UPS"
```

**Generated State Machine**:
```sql
-- Auto-generated order status tracking
CREATE TYPE management.order_status AS ENUM (
  'draft',
  'submitted',
  'approved',
  'rejected',
  'shipped',
  'delivered',
  'cancelled'
);

ALTER TABLE management.tb_order
ADD COLUMN status management.order_status DEFAULT 'draft';

-- Status transition validation
CREATE FUNCTION management.submit_order(p_order_id UUID)
RETURNS app.mutation_result AS $$
DECLARE
  v_current_status management.order_status;
BEGIN
  -- Check current status
  SELECT status INTO v_current_status
  FROM management.tb_order
  WHERE id = p_order_id;

  -- Validate transition: draft → submitted
  IF v_current_status != 'draft' THEN
    RETURN (
      'error',
      'Can only submit orders in draft status',
      NULL,
      NULL
    )::app.mutation_result;
  END IF;

  -- Transition
  UPDATE management.tb_order
  SET status = 'submitted',
      updated_at = NOW()
  WHERE id = p_order_id;

  RETURN (
    'success',
    'Order submitted for approval',
    jsonb_build_object('order_id', p_order_id, 'status', 'submitted'),
    jsonb_build_object('affected_entities', jsonb_build_array('Order'))
  )::app.mutation_result;
END;
$$ LANGUAGE plpgsql;
```

#### Extending Order

```yaml
# Add custom fields for subscription orders
entity: SubscriptionOrder
extends:
  from: stdlib/commerce/order
fields:
  # Subscription-specific
  billing_frequency: enum(monthly, quarterly, annual)
  auto_renew: boolean
  trial_period_days: integer
  next_billing_date: date

  # Usage limits
  max_users: integer
  max_storage_gb: integer

actions:
  - name: start_trial
  - name: convert_to_paid
  - name: upgrade_plan
  - name: downgrade_plan
  - name: pause_subscription
  - name: resume_subscription
```

---

### 3. Price

**Purpose**: Time-based pricing for contract items

**Schema**: `management` (tenant-specific)

**Use Cases**:
- Dynamic pricing
- Promotional pricing
- Volume discounts
- Time-limited offers
- Price revisions

#### Fields

```yaml
entity: Price
fields:
  # Identifier
  price_identifier: text

  # Pricing
  amount:
    type: money
    nullable: false
    description: "Price amount with currency semantics"

  # Validity period
  start_date: date    # Effective from
  end_date: date      # Valid until

  # Relationships
  customer_org: ref(Organization)     # Customer-specific pricing
  contract: ref(Contract)             # Contract pricing
  contract_item: ref(ContractItem)    # Item-level pricing
  currency: ref(Currency)             # Price currency
```

#### Built-in Actions

```yaml
actions:
  # CRUD
  - create_price
  - update_price
  - delete_price

  # Lifecycle
  - activate_price              # Make price active
  - deactivate_price            # Disable price

  # Price management
  - change_amount               # Adjust price amount
  - extend_validity            # Extend end_date
  - create_price_revision      # Create new version
  - apply_bulk_price_change    # Batch updates
```

#### Example: Time-Based Pricing Strategy

```yaml
import:
  - stdlib/commerce/price

# Regular price
action: create_price
inputs:
  price_identifier: "PROD-001-REGULAR"
  amount: {value: 99.99, currency: "USD"}
  start_date: "2024-01-01"
  end_date: null  # No end date = ongoing
  contract_item: {identifier: "item-prod-001"}
  currency: {iso_code: "USD"}

# Black Friday promotion (time-limited)
action: create_price
inputs:
  price_identifier: "PROD-001-BLACK-FRIDAY"
  amount: {value: 69.99, currency: "USD"}
  start_date: "2024-11-24"
  end_date: "2024-11-27"  # 3-day sale
  contract_item: {identifier: "item-prod-001"}
  currency: {iso_code: "USD"}

# Query active price for date
action: get_active_price
inputs:
  contract_item_id: {identifier: "item-prod-001"}
  effective_date: "2024-11-25"  # Returns $69.99 (promo price)
```

**Generated Price Lookup**:
```sql
-- Automatically generated price resolution
CREATE FUNCTION management.get_active_price(
  p_contract_item_id UUID,
  p_effective_date DATE DEFAULT CURRENT_DATE
) RETURNS TABLE(
  price_id UUID,
  amount NUMERIC,
  currency_code TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.amount,
    c.iso_code
  FROM management.tb_price p
  JOIN common.tb_currency c ON p.fk_currency = c.pk_currency
  WHERE p.fk_contract_item = (
          SELECT pk_contract_item
          FROM management.tb_contract_item
          WHERE id = p_contract_item_id
        )
    AND p.start_date <= p_effective_date
    AND (p.end_date IS NULL OR p.end_date >= p_effective_date)
  ORDER BY
    p.start_date DESC,  -- Most recent first
    p.amount ASC        -- Lowest price wins
  LIMIT 1;
END;
$$ LANGUAGE plpgsql;
```

#### Extending Price

```yaml
# Add volume discount tiers
entity: TieredPrice
extends:
  from: stdlib/commerce/price
fields:
  # Volume tiers
  min_quantity: integer
  max_quantity: integer
  discount_percent: decimal

  # Conditional pricing
  customer_tier: enum(bronze, silver, gold, platinum)
  applies_to_new_customers: boolean
  requires_approval: boolean

actions:
  - name: calculate_tiered_price
  - name: apply_volume_discount
  - name: check_tier_eligibility
```

---

## Complete Integration Example

### B2B E-Commerce Platform

```yaml
# Import commerce foundation
import:
  - stdlib/commerce/contract
  - stdlib/commerce/order
  - stdlib/commerce/price
  - stdlib/crm/organization
  - stdlib/crm/contact
  - stdlib/i18n/currency
  - stdlib/geo/public_address

# Extend with product catalog
entity: Product
fields:
  sku: text
  name: text
  description: text
  category: enum(hardware, software, services)

# Extend with order lines
entity: OrderLine
fields:
  order: ref(Order)
  product: ref(Product)
  quantity: integer
  unit_price: money
  line_total: money
  tax_rate: decimal
  tax_amount: money

# Full order workflow
actions:
  - name: create_customer_order
    inputs:
      customer_org_id: uuid
      contract_id: uuid
      items: list(object)
    steps:
      # 1. Create order
      - insert: Order
        fields:
          order_identifier: :auto_generated
          customer_org: :customer_org_id
          contract: :contract_id
          order_date: :current_date

      # 2. Add line items
      - foreach: :items
        steps:
          - query: |
              SELECT amount FROM Price
              WHERE contract_item = :item.product_id
                AND start_date <= CURRENT_DATE
                AND (end_date IS NULL OR end_date >= CURRENT_DATE)

          - insert: OrderLine
            fields:
              order: :order_id
              product: :item.product_id
              quantity: :item.quantity
              unit_price: :queried_price

      # 3. Calculate totals
      - update: Order
        set:
          total_amount: SUM(OrderLine.line_total WHERE order = :order_id)

      # 4. Notify customer
      - notify:
          channel: email
          to: {customer_org_contact_email}
          template: order_confirmation
          data: {order_id: :order_id}

  - name: approve_and_ship_order
    inputs:
      order_id: uuid
      shipping_address_id: uuid
    steps:
      # Validate order status
      - validate: Order.status = 'submitted' WHERE id = :order_id

      # Approve
      - call: management.approve_order(:order_id)

      # Create shipment
      - insert: Shipment
        fields:
          order: :order_id
          shipping_address: :shipping_address_id
          shipped_date: :current_date

      # Update order status
      - call: management.ship_order(:order_id)

      # Notify
      - notify:
          channel: email
          template: order_shipped
```

**Generated Code**: 3000+ lines of PostgreSQL with:
- Contract lifecycle management
- Order state machine
- Price resolution logic
- Foreign key constraints
- Audit trails
- Multi-currency support
- Notification triggers

---

## Database Schema Details

### Generated Tables

```sql
-- Contract table
CREATE TABLE management.tb_contract (
  pk_contract INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  contract_identifier TEXT NOT NULL,
  customer_contract_id TEXT,
  provider_contract_id TEXT,

  signature_date DATE,
  start_date DATE,
  end_date DATE,
  name TEXT NOT NULL,

  duration_source management.contract_duration_source DEFAULT 'original_duration',

  -- Foreign keys
  fk_customer_org INTEGER NOT NULL REFERENCES management.tb_organization(pk_organization),
  fk_provider_org INTEGER NOT NULL REFERENCES management.tb_organization(pk_organization),
  fk_currency INTEGER NOT NULL REFERENCES common.tb_currency(pk_currency),

  tenant_id UUID NOT NULL,

  -- Audit fields
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ,
  created_by UUID,
  updated_by UUID
);

-- Order table
CREATE TABLE management.tb_order (
  pk_order INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  order_identifier TEXT NOT NULL,
  customer_order_id TEXT,
  provider_order_id TEXT,
  customer_commitment_id TEXT,

  order_date DATE,
  invoice_date DATE,
  sequential_number INTEGER,

  -- Foreign keys
  fk_customer_org INTEGER NOT NULL,
  fk_provider_org INTEGER NOT NULL,
  fk_contract INTEGER REFERENCES management.tb_contract(pk_contract),

  tenant_id UUID NOT NULL,

  -- Audit fields
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ
);

-- Price table
CREATE TABLE management.tb_price (
  pk_price INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  price_identifier TEXT NOT NULL,
  amount NUMERIC(19, 4) NOT NULL,

  start_date DATE,
  end_date DATE,

  -- Foreign keys
  fk_customer_org INTEGER,
  fk_contract INTEGER,
  fk_contract_item INTEGER,
  fk_currency INTEGER NOT NULL REFERENCES common.tb_currency(pk_currency),

  tenant_id UUID NOT NULL,

  -- Audit fields
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ
);

-- Indexes for date-based price lookups
CREATE INDEX idx_tb_price_dates
  ON management.tb_price (fk_contract_item, start_date, end_date)
  WHERE deleted_at IS NULL;

-- Unique constraint: one contract per customer-provider pair
CREATE UNIQUE INDEX idx_tb_contract_customer_provider
  ON management.tb_contract (fk_customer_org, fk_provider_org, contract_identifier)
  WHERE deleted_at IS NULL;
```

---

## Best Practices

### ✅ DO

1. **Use contracts for long-term relationships**
   ```yaml
   # Good: Contract defines terms, orders reference it
   contract: annual_support_2024
   orders:
     - order_1 (under annual_support_2024)
     - order_2 (under annual_support_2024)
   ```

2. **Time-bound pricing carefully**
   ```yaml
   # Good: Clear validity periods
   prices:
     - regular: start_date=2024-01-01, end_date=null
     - promotion: start_date=2024-11-24, end_date=2024-11-27
   ```

3. **Track order lifecycle with actions**
   ```yaml
   # Good: Explicit state transitions
   - submit_order
   - approve_order
   - ship_order
   - deliver_order
   ```

### ❌ DON'T

1. **Don't store prices in order lines directly**
   ```yaml
   # ❌ Bad: Hardcoded prices
   entity: OrderLine
   fields:
     price: 99.99

   # ✅ Good: Reference Price entity
   fields:
     price: ref(Price)  # Dynamic, time-based
   ```

2. **Don't skip contract validation**
   ```yaml
   # ❌ Bad: No contract
   action: create_order
   inputs:
     customer: acme
     # Missing contract reference!

   # ✅ Good: Always reference contract
   action: create_order
   inputs:
     customer: acme
     contract: {identifier: "annual-2024"}
   ```

3. **Don't forget multi-currency support**
   ```yaml
   # ❌ Bad: Assume single currency
   fields:
     amount: decimal

   # ✅ Good: Use money type + currency reference
   fields:
     amount: money
     currency: ref(Currency)
   ```

---

## Performance Considerations

### Price Lookups

For high-volume pricing queries, add composite index:

```sql
-- Auto-generated by SpecQL
CREATE INDEX idx_tb_price_effective_dates
  ON management.tb_price (
    fk_contract_item,
    start_date,
    end_date
  )
  WHERE deleted_at IS NULL
    AND end_date IS NOT NULL;  -- Include only time-limited prices
```

### Order Queries

Common order queries benefit from indexes:

```sql
-- Auto-generated by SpecQL
CREATE INDEX idx_tb_order_customer_date
  ON management.tb_order (fk_customer_org, order_date DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_tb_order_status
  ON management.tb_order (status)
  WHERE deleted_at IS NULL;
```

---

## Reference

### Complete Entity List

| Entity | Schema | Key Features |
|--------|--------|--------------|
| **Contract** | management | Agreements, terms, lifecycle management |
| **Order** | management | Purchase orders, state machine, line items |
| **Price** | management | Time-based pricing, multi-currency |

### Related Documentation

- [CRM Entities](../crm/index.md) - Organization and Contact (parties to contracts)
- [i18n Entities](../i18n/index.md) - Currency for pricing
- [Rich Types Reference](../../06_reference/rich-types-reference.md) - money type details
- [Actions Guide](../../05_guides/your-first-action.md) - Building business logic

---

## Next Steps

1. **Try it**: Import commerce entities in your project
2. **Extend it**: Add custom fields for your business model
3. **Deploy it**: Generate PostgreSQL schema with workflows
4. **Test it**: Create end-to-end order flows

**Ready to build B2B commerce? Import and go!** 💰
