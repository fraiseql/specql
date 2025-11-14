# Migrating Spring Boot Projects to SpecQL

## Overview

This guide helps you migrate existing Spring Boot/JPA projects to SpecQL, enabling:
- Declarative entity definitions in YAML
- Cross-language code generation
- Automatic API generation
- Simplified maintenance

## Migration Process

### Step 1: Analyze Your Project

```bash
# Run analysis tool
uv run specql analyze-project ./src/main/java/com/example

# Output:
# Found 47 entities
# Found 12 repositories
# Found 8 services with custom logic
# Migration complexity: Medium
```

### Step 2: Reverse Engineer Entities

```bash
# Convert all entities to SpecQL YAML
uv run specql reverse-engineer \
  --source ./src/main/java/com/example \
  --output ./entities/

# Output:
# ✅ Generated Product.yaml
# ✅ Generated Customer.yaml
# ✅ Generated Order.yaml
# ...
```

### Step 3: Review Generated YAML

Review each generated YAML file and make adjustments:

**Before (Java)**:
```java
@Entity
@Table(name = "tb_product")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    private Integer price;
}
```

**After (SpecQL YAML)**:
```yaml
entity: Product
schema: ecommerce
fields:
  name: text!
  price: integer
```

Much cleaner!

### Step 4: Add Business Logic as Actions

Extract business logic from services into actions:

**Before (Java Service)**:
```java
@Service
public class OrderService {
    public Order shipOrder(Long orderId) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow();

        if (!order.getStatus().equals(OrderStatus.PENDING)) {
            throw new IllegalStateException("Order not pending");
        }

        order.setStatus(OrderStatus.SHIPPED);
        order.setShippedAt(LocalDateTime.now());

        return orderRepository.save(order);
    }
}
```

**After (SpecQL Action)**:
```yaml
actions:
  - name: ship_order
    steps:
      - validate: status = 'pending'
      - update: Order SET status = 'shipped', shipped_at = NOW()
```

### Step 5: Generate Code in Multiple Languages

Now you can generate code for any supported language:

```bash
# Generate Java/Spring Boot
uv run specql generate java entities/ --output-dir=generated/java

# Generate Python/Django
uv run specql generate python entities/ --output-dir=generated/python

# Generate Rust/Diesel
uv run specql generate rust entities/ --output-dir=generated/rust

# Generate TypeScript/Prisma
uv run specql generate typescript entities/ --output-dir=generated/ts
```

### Step 6: Integration Testing

Test that generated code works correctly:

```bash
# Run integration tests
uv run pytest tests/integration/

# Compare original vs generated behavior
uv run specql test-equivalence \
  --original ./src/main/java \
  --generated ./generated/java
```

### Step 7: Gradual Migration

You don't have to migrate everything at once:

1. **Start small**: Migrate 1-2 simple entities
2. **Test thoroughly**: Validate behavior matches
3. **Expand gradually**: Migrate more entities
4. **Run in parallel**: Keep both versions during transition
5. **Full cutover**: Once confident, switch completely

## Best Practices

### DO:
- ✅ Start with simple entities
- ✅ Review all generated code
- ✅ Add comprehensive tests
- ✅ Document custom business logic
- ✅ Use version control for YAML files

### DON'T:
- ❌ Modify generated code directly
- ❌ Skip testing phase
- ❌ Migrate complex entities first
- ❌ Forget to backup original code
- ❌ Rush the migration

## Common Issues

### Issue: Custom repository methods not migrated

**Solution**: Document custom queries in SpecQL actions or keep as manual extensions

### Issue: Complex inheritance hierarchies

**Solution**: Flatten to composition where possible, or maintain as custom code

### Issue: Native SQL queries

**Solution**: Convert to SpecQL expressions or keep as extensions

## Getting Help

- Documentation: https://specql.dev/docs
- Examples: https://github.com/specql/examples
- Community: https://discord.gg/specql
- Issues: https://github.com/specql/specql/issues