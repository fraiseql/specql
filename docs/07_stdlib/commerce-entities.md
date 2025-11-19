# Commerce Entities: E-Commerce & Transaction Management

> **3 production-ready entities for pricing, orders, and contracts—ISO 4217 currency support and time-based pricing**

## Overview

SpecQL's Commerce stdlib provides **production-ready entities** for e-commerce, SaaS billing, and transaction management. These entities handle multi-currency pricing, order lifecycles, and contract management with built-in best practices.

**Standards-Based**:
- ISO 4217 currency codes
- Time-based pricing (validity periods)
- Tax calculation support
- Multi-currency handling

**Origin**: Extracted from PrintOptim production system (B2B commerce platform)

---

## Price Entity

### Purpose

Time-based pricing for products, services, and contracts with:
- Multi-currency support
- Validity periods (start/end dates)
- Customer-specific pricing
- Contract-based pricing
- Price revision history

### Schema Location

**Shared**: `management` schema

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `price_identifier` | text | **Yes** | Unique price identifier |
| `amount` | money | **Yes** | Price amount with currency semantics |
| `start_date` | date | No | Effective from date |
| `end_date` | date | No | Valid until date |

### Relationships

| Field | References | Description |
|-------|------------|-------------|
| `customer_org` | Organization | Customer-specific pricing |
| `contract` | Contract | Associated contract |
| `contract_item` | ContractItem | Specific contract line item |
| `currency` | Currency | ISO 4217 currency (USD, EUR, etc.) |

### Pre-built Actions

```yaml
# CRUD Operations
- create_price
- update_price
- delete_price

# Business Logic
- activate_price              # Enable price
- deactivate_price            # Disable price
- change_amount               # Update pricing
- extend_validity             # Extend date range
- create_price_revision       # Create versioned copy
- apply_bulk_price_change     # Batch price updates
```

### Usage Example

#### Simple Product Pricing

```yaml
from: stdlib/commerce/price.yaml
from: stdlib/i18n/currency.yaml

action: create_product_price
  steps:
    - insert: Price
      values:
        price_identifier: "prod-123-base"
        amount: 99.99
        currency: ref(Currency[code='USD'])
        start_date: '2025-01-01'
```

#### Customer-Specific Pricing

```yaml
action: create_vip_pricing
  entity: Price
  steps:
    - insert: Price
      values:
        price_identifier: "prod-123-vip"
        amount: 79.99  # 20% discount
        currency: ref(Currency[code='USD'])
        customer_org: ref(Organization[identifier='acme-corp'])
        start_date: '2025-01-01'
        end_date: '2025-12-31'
```

#### Time-Based Promotions

```yaml
action: create_holiday_pricing
  entity: Price
  steps:
    - insert: Price
      values:
        price_identifier: "prod-123-holiday"
        amount: 49.99  # 50% off
        currency: ref(Currency[code='USD'])
        start_date: '2025-11-25'  # Black Friday
        end_date: '2025-11-30'    # Cyber Monday
```

#### Multi-Currency Pricing

```yaml
action: create_international_pricing
  entity: Price
  steps:
    - insert: Price VALUES (
        price_identifier: 'prod-123-usd',
        amount: 99.99,
        currency: ref(Currency[code='USD'])
      )
    - insert: Price VALUES (
        price_identifier: 'prod-123-eur',
        amount: 89.99,
        currency: ref(Currency[code='EUR'])
      )
    - insert: Price VALUES (
        price_identifier: 'prod-123-gbp',
        amount: 79.99,
        currency: ref(Currency[code='GBP'])
      )
```

#### Price Revision Management

```yaml
action: increase_prices_10_percent
  entity: Price
  steps:
    # Create new price revision
    - foreach: active_prices
      - call: create_price_revision
        params:
          original_price: $price_id
          new_amount: $current_amount * 1.10
          effective_date: '2025-01-01'
```

### Generated SQL

```sql
CREATE TABLE management.tb_price (
  pk_price            INTEGER PRIMARY KEY,
  id                  UUID UNIQUE,
  identifier          TEXT UNIQUE,
  price_identifier    TEXT NOT NULL,
  amount              NUMERIC(15,2) NOT NULL,  -- Money type
  start_date          DATE,
  end_date            DATE,
  customer_org        INTEGER REFERENCES management.tb_organization,
  contract            INTEGER REFERENCES management.tb_contract,
  contract_item       INTEGER REFERENCES management.tb_contract_item,
  currency            INTEGER REFERENCES common.tb_currency,
  created_at          TIMESTAMP,
  updated_at          TIMESTAMP,
  deleted_at          TIMESTAMP,

  -- Validity constraint
  CONSTRAINT check_price_dates CHECK (
    start_date IS NULL OR end_date IS NULL OR start_date <= end_date
  )
);

-- Query active prices for a customer
CREATE FUNCTION management.get_active_price(
  p_customer_org INTEGER,
  p_product_id TEXT,
  p_date DATE DEFAULT CURRENT_DATE
) RETURNS NUMERIC AS $$
  SELECT amount
  FROM management.tb_price
  WHERE customer_org = p_customer_org
    AND price_identifier LIKE p_product_id || '%'
    AND (start_date IS NULL OR start_date <= p_date)
    AND (end_date IS NULL OR end_date >= p_date)
    AND deleted_at IS NULL
  ORDER BY start_date DESC NULLS LAST
  LIMIT 1;
$$ LANGUAGE sql STABLE;
```

---

## Order Entity

### Purpose

Order lifecycle management with:
- Order status tracking (pending → shipped → delivered)
- Line items management
- Payment tracking
- Fulfillment workflow

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `order_number` | text | Unique order identifier |
| `order_date` | date | Order placement date |
| `status` | enum | pending, paid, shipped, delivered, cancelled |
| `total_amount` | money | Order total |
| `shipping_cost` | money | Shipping charges |
| `tax_amount` | money | Tax charges |

### Relationships

| Field | References | Description |
|-------|------------|-------------|
| `customer` | Contact | Customer placing order |
| `shipping_address` | PublicAddress | Delivery address |
| `billing_address` | PublicAddress | Billing address |
| `currency` | Currency | Order currency |

### Usage Example

```yaml
from: stdlib/commerce/order.yaml
from: stdlib/crm/contact.yaml
from: stdlib/geo/public_address.yaml

action: create_order
  steps:
    - insert: Order
      values:
        order_number: "ORD-2025-00123"
        order_date: NOW()
        status: 'pending'
        customer: ref(Contact[email='john@acme.com'])
        shipping_address: $address_id
        currency: ref(Currency[code='USD'])

action: process_payment
  entity: Order
  steps:
    - validate: status = 'pending'
    - call: charge_payment_method($total_amount)
    - update: Order SET status = 'paid', paid_at = NOW()

action: ship_order
  entity: Order
  steps:
    - validate: status = 'paid'
    - update: Order SET status = 'shipped', shipped_at = NOW()
    - notify: customer
```

---

## Contract Entity

### Purpose

Business contract management with:
- Contract terms and conditions
- Multi-party agreements
- Renewal tracking
- Associated pricing

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `contract_number` | text | Unique contract ID |
| `start_date` | date | Contract effective date |
| `end_date` | date | Contract expiry date |
| `renewal_date` | date | Next renewal date |
| `status` | enum | draft, active, expired, terminated |

### Usage Example

```yaml
from: stdlib/commerce/contract.yaml
from: stdlib/crm/organization.yaml

action: create_annual_contract
  steps:
    - insert: Contract
      values:
        contract_number: "CTR-2025-00001"
        customer_org: ref(Organization[identifier='acme'])
        start_date: '2025-01-01'
        end_date: '2025-12-31'
        renewal_date: '2025-12-01'
        status: 'active'

action: renew_contract
  entity: Contract
  steps:
    - validate: status = 'active'
    - validate: NOW() >= renewal_date
    - update: Contract
      SET start_date = end_date + INTERVAL '1 day',
          end_date = end_date + INTERVAL '1 year',
          renewal_date = renewal_date + INTERVAL '1 year'
```

---

## Complete E-Commerce Example

### Scenario: Multi-Currency Online Store

```yaml
# File: entities/online_store.yaml

# Import commerce entities
from: stdlib/commerce/price.yaml
from: stdlib/commerce/order.yaml
from: stdlib/commerce/contract.yaml

# Import supporting entities
from: stdlib/crm/contact.yaml
from: stdlib/geo/public_address.yaml
from: stdlib/i18n/currency.yaml
from: stdlib/i18n/country.yaml

# Extend Order with custom fields
extend: Order
  custom_fields:
    discount_code: text
    discount_amount: money
    loyalty_points_earned: integer
    estimated_delivery: date
    tracking_number: text

# Extend Price with inventory
extend: Price
  custom_fields:
    inventory_count: integer(0, 999999)
    low_stock_threshold: integer(0, 1000)

# Custom actions
action: apply_discount_code
  entity: Order
  steps:
    - validate: discount_code IS NOT NULL
    - query: SELECT discount_percent FROM discount_codes WHERE code = $discount_code
      result: $discount
    - update: Order
      SET discount_amount = total_amount * ($discount / 100.0),
          total_amount = total_amount * (1 - $discount / 100.0)

action: calculate_loyalty_points
  entity: Order
  steps:
    - if: total_amount >= 100
      - update: Order SET loyalty_points_earned = FLOOR(total_amount)
    - if: total_amount < 100
      - update: Order SET loyalty_points_earned = FLOOR(total_amount * 0.5)

action: complete_order
  entity: Order
  steps:
    - validate: status = 'pending'
    - call: process_payment($total_amount)
    - update: Order SET status = 'paid', paid_at = NOW()
    - call: calculate_loyalty_points
    - call: allocate_inventory
    - notify: customer
```

### Generated Output

```bash
specql generate entities/online_store.yaml --output db/schema/

# Generated:
# - tb_price (15 fields)
# - tb_order (25 fields)
# - tb_contract (12 fields)
# - 8 business logic functions
# - GraphQL mutations
# - TypeScript types

# Total: ~1,200 lines generated from 50 lines YAML
```

---

## Integration Examples

### Commerce + CRM

```yaml
from: stdlib/commerce/order.yaml
from: stdlib/crm/contact.yaml
from: stdlib/crm/organization.yaml

# Track customer lifetime value
action: calculate_ltv
  entity: Contact
  steps:
    - query: SUM(total_amount) FROM Order WHERE customer = $contact_id
      result: $lifetime_value
    - update: Contact SET lifetime_value = $lifetime_value
```

---

### Commerce + Geo

```yaml
from: stdlib/commerce/order.yaml
from: stdlib/geo/public_address.yaml
from: stdlib/geo/location.yaml

# Shipping cost calculation
action: calculate_shipping
  entity: Order
  steps:
    - call: find_nearest_warehouse($shipping_address)
      result: $warehouse
    - call: calculate_distance($warehouse, $shipping_address)
      result: $distance_km
    - if: $distance_km < 50
      - update: Order SET shipping_cost = 5.00
```

---

## Performance Best Practices

### Indexing

```sql
-- Auto-generated indexes
CREATE INDEX idx_tb_price_customer ON management.tb_price(customer_org);
CREATE INDEX idx_tb_price_currency ON management.tb_price(currency);
CREATE INDEX idx_tb_price_dates ON management.tb_price(start_date, end_date);

CREATE INDEX idx_tb_order_customer ON tenant.tb_order(customer);
CREATE INDEX idx_tb_order_status ON tenant.tb_order(status);
CREATE INDEX idx_tb_order_date ON tenant.tb_order(order_date);
```

### Query Optimization

```sql
-- Efficient price lookup
SELECT amount
FROM management.tb_price
WHERE customer_org = organization_pk('acme')
  AND price_identifier = 'prod-123'
  AND (start_date IS NULL OR start_date <= CURRENT_DATE)
  AND (end_date IS NULL OR end_date >= CURRENT_DATE)
  AND deleted_at IS NULL
ORDER BY start_date DESC
LIMIT 1;
```

---

## Security: Tenant Isolation

Orders are **tenant-isolated**:

```sql
CREATE POLICY tenant_isolation ON tenant.tb_order
  USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

Prices are **shared** (management schema) for cross-tenant price lists.

---

## Key Takeaways

1. **Multi-Currency Support**: ISO 4217 currencies built-in
2. **Time-Based Pricing**: Validity periods, promotions, revisions
3. **Flexible Pricing**: Customer-specific, contract-based, volume tiers
4. **Order Lifecycle**: Complete state machine from cart to delivery
5. **Production-Tested**: Real B2B commerce platform extraction

**Build e-commerce backends in hours, not weeks.** 💰

---

*Last updated: 2025-11-19*
