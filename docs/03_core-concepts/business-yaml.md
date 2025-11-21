# Business YAML: Define Your Domain, Not Your Infrastructure

> **Why SpecQL uses YAML for business logic and code for infrastructure**

## Overview

SpecQL inverts the traditional development approach: **you define business domains in YAML, SpecQL generates all the technical infrastructure**. This separation enables you to focus on what matters—your business logic—while SpecQL handles the complexity of production systems.

## The Traditional Problem

Most development frameworks force you to write infrastructure code alongside business logic:

```python
# Traditional: Business + Infrastructure mixed
class Contact(models.Model):
    # Business fields
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # Infrastructure concerns
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Business methods mixed with infrastructure
    def save(self, *args, **kwargs):
        # Business logic
        self.full_name = f"{self.first_name} {self.last_name}"
        # Infrastructure concerns
        super().save(*args, **kwargs)

    # More infrastructure
    class Meta:
        db_table = 'contacts'
        indexes = [models.Index(fields=['email'])]
```

**Result**: 80% infrastructure, 20% business logic. Hard to maintain, hard to change.

## The SpecQL Solution

**Separate concerns completely**: Business domain in YAML, infrastructure generated automatically.

```yaml
# Business domain only - what your system does
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: email!              # Business validation rules
  first_name: text!
  last_name: text!

actions:
  - name: create_contact     # Business operations
  - name: update_contact
```

**Result**: 100% business focus. Infrastructure is generated and invisible.

## Why YAML for Business Logic?

### 1. **Business-Friendly Syntax**

YAML is readable by non-developers. Product managers, business analysts, and domain experts can understand and contribute to the schema.

```yaml
# Business stakeholders can read this!
entity: Customer
description: "Someone who buys our products"

fields:
  loyalty_tier: enum(gold, silver, bronze)  # Business concept
  lifetime_value: money                     # Business metric
  preferred_contact_method: enum(email, phone, mail)
```

### 2. **Validation Over Implementation**

YAML focuses on **what** should be valid, not **how** to implement it:

```yaml
fields:
  email: email!          # "Must be valid email" - not "regex validation"
  age: integer(13, 120)  # "Age between 13-120" - not "if age < 13 error"
  status: enum(active, inactive, suspended)  # "One of these values" - not "check constraint"
```

### 3. **Declarative, Not Imperative**

Describe the desired state, not the steps to achieve it:

```yaml
# Declarative: What the system should do
actions:
  - name: process_order
    description: "Process customer order with payment and inventory"
    steps:
      - validate: inventory_available = true
      - update: Order SET status = 'processing'
      - call: process_payment
      - update: Inventory REDUCE quantity

# vs Imperative (traditional code)
def process_order(order_id):
    order = Order.objects.get(id=order_id)
    if not order.inventory_available:
        raise ValidationError("Out of stock")
    order.status = 'processing'
    order.save()
    payment_result = process_payment(order)
    if payment_result.success:
        reduce_inventory(order.items)
    # ... lots more error handling, transactions, etc
```

### 4. **Framework Agnostic**

Your business logic doesn't depend on PostgreSQL, GraphQL, or any specific technology. Change the underlying infrastructure without touching business rules.

## The Philosophy: Business Domain First

SpecQL's core philosophy: **Your business domain is the source of truth, not your code**.

### Business Domain Defines:
- **Entities**: What things exist in your business
- **Relationships**: How things connect
- **Rules**: What is valid and what isn't
- **Operations**: What actions can be performed

### Technology Implements:
- **Storage**: PostgreSQL tables, indexes, constraints
- **API**: GraphQL schema, resolvers, mutations
- **Types**: TypeScript interfaces, validation
- **Infrastructure**: Migrations, security, performance

## Real-World Benefits

### Faster Development

**Traditional**: 2 weeks per entity (design + code + test + deploy)
**SpecQL**: 30 minutes per entity (YAML + generate + deploy)

### Easier Maintenance

**Traditional**: Change requires touching multiple layers
```python
# Change in Django model
class Contact(models.Model):
    email = models.EmailField(unique=True)  # Change here
    # ... then update forms, serializers, views, templates...

# Change in GraphQL
type Contact {
  email: String!  # Change here too
  # ... then update resolvers, frontend types...
}
```

**SpecQL**: Change in one place
```yaml
fields:
  email: email!  # Change here only - everything else updates
```

### Better Collaboration

**Traditional**: Developers translate business requirements into code
**SpecQL**: Business experts define requirements directly in YAML

### Future-Proof Architecture

**Traditional**: Tied to specific framework choices
**SpecQL**: Business logic survives technology changes

## How It Works

1. **Define Business Domain** in YAML (what your system does)
2. **SpecQL Generates** all technical implementation (how it works)
3. **Deploy & Iterate** on business logic, not infrastructure

```yaml
# Step 1: Business domain (your focus)
entity: Product
fields:
  name: text!
  price: money!
  category: ref(Category)
  tags: text[]

actions:
  - name: create_product
  - name: update_price
  - name: add_to_category
```

```sql
-- Step 2: Generated infrastructure (SpecQL's job)
CREATE TABLE commerce.tb_product (
    pk_product INTEGER PRIMARY KEY,
    id UUID NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC(19,4) NOT NULL,
    fk_category INTEGER,
    tags TEXT[],
    -- ... audit fields, constraints, indexes
);
```

## Common Questions

### "Isn't YAML just another DSL?"

No. YAML is a data format that happens to be human-readable. SpecQL's "DSL" is actually your business domain expressed in data. The real DSL is the generated PL/pgSQL, GraphQL, and TypeScript.

### "What about complex business logic?"

Complex logic belongs in actions, which are still declarative:

```yaml
actions:
  - name: process_subscription
    steps:
      - validate: payment_method_valid = true
      - validate: account_balance >= subscription_cost
      - update: Account DEDUCT subscription_cost
      - update: Subscription ACTIVATE
      - call: send_welcome_email
      - return: "Subscription activated"
```

### "How do I handle edge cases?"

Edge cases become validation rules or conditional logic in actions. The infrastructure handles the complexity.

## Next Steps

- [Learn about the Trinity Pattern](trinity-pattern.md) - how SpecQL structures data
- [Explore Rich Types](rich-types.md) - 49 built-in validations
- [Create your first entity](../01_getting-started/first-entity.md)

---

**The key insight**: By separating business domain from technical implementation, SpecQL lets you focus on what makes your business unique while handling all the commodity infrastructure automatically.</content>
</xai:function_call
