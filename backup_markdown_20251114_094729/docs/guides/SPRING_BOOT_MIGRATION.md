# Spring Boot to SpecQL Migration Guide

## Overview

This guide provides a step-by-step process for migrating Spring Boot applications with JPA entities to SpecQL-generated schemas. The migration leverages SpecQL's Java reverse engineering capabilities to automatically convert your existing JPA entities.

## Prerequisites

### System Requirements
- **Java**: JDK 11+ for JDT parsing
- **SpecQL**: Latest version with Java support
- **Python**: 3.11+ with required dependencies

### Installation
```bash
# Install SpecQL with Java support
pip install specql[java]

# Verify Java installation
java -version  # Should be 11+

# Verify SpecQL Java support
specql reverse --help | grep java
```

## Migration Process

### Step 1: Analyze Your Spring Boot Project

**Identify Entity Classes**
```bash
# Find all JPA entities in your project
find src/main/java -name "*.java" -exec grep -l "@Entity" {} \;
```

**Common Spring Boot Entity Patterns**
```java
// Standard JPA Entity
@Entity
@Table(name = "users")
public class User {
    @Id @GeneratedValue
    private Long id;

    @Column(nullable = false)
    private String email;

    @ManyToOne
    private Company company;
}

// With Validation
@Entity
public class Product {
    @NotNull @Size(max = 100)
    private String name;

    @DecimalMin("0.0")
    private BigDecimal price;
}
```

### Step 2: Extract SpecQL Schemas

**Single Entity Migration**
```bash
# Extract single entity
specql reverse java User.java --output-dir schemas/

# Preview before migration
specql reverse java User.java --preview
```

**Batch Entity Migration**
```bash
# Extract all entities from package
specql reverse java src/main/java/com/example/domain/ --output-dir schemas/

# Extract from entire model package
find src/main/java -path "*/model/*" -name "*.java" | \
  xargs specql reverse java --output-dir schemas/
```

**Generated SpecQL YAML**
```yaml
# schemas/User.yaml
entity: User
schema: public
table: users
fields:
  email:
    type: text
    nullable: false
  company:
    type: ref(Company)
```

### Step 3: Handle Relationships

**Many-to-One Relationships**
```java
// Spring Boot
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "company_id")
private Company company;
```

```yaml
# SpecQL
company:
  type: ref(Company)
```

**One-to-Many Relationships**
```java
// Spring Boot
@OneToMany(mappedBy = "company", cascade = CascadeType.ALL)
private List<Employee> employees;
```

```yaml
# SpecQL
employees:
  type: list(Employee)
```

**Many-to-Many Relationships**
```java
// Spring Boot
@ManyToMany
@JoinTable(
    name = "user_roles",
    joinColumns = @JoinColumn(name = "user_id"),
    inverseJoinColumns = @JoinColumn(name = "role_id")
)
private Set<Role> roles;
```

```yaml
# SpecQL (simplified to list for now)
roles:
  type: list(Role)
```

### Step 4: Handle Enums

**String Enums**
```java
// Spring Boot
@Enumerated(EnumType.STRING)
private UserStatus status;

public enum UserStatus {
    ACTIVE, INACTIVE, SUSPENDED
}
```

```yaml
# SpecQL
status:
  type: enum(active, inactive, suspended)
```

**Ordinal Enums**
```java
// Spring Boot
@Enumerated(EnumType.ORDINAL)  // Default
private Priority priority;
```

```yaml
# SpecQL (converted to string enum)
priority:
  type: enum(low, medium, high)
```

### Step 5: Handle Embedded Objects

**Embedded Entities**
```java
// Spring Boot
@Embedded
private Address address;

@Embeddable
public class Address {
    private String street;
    private String city;
    @Column(name = "postal_code")
    private String postalCode;
}
```

```yaml
# SpecQL (flattened)
street:
  type: text
city:
  type: text
postal_code:
  type: text
```

### Step 6: Custom Type Mappings

**Common Spring Boot Types**
```java
// Date/Time Types
private LocalDate birthDate;           // → date
private LocalDateTime createdAt;       // → timestamp
private Instant lastLogin;             // → timestamp

// Numeric Types
private BigDecimal salary;             // → decimal
private Integer age;                   // → integer

// Collections
private List<String> tags;             // → list(text)
private Set<String> categories;        // → list(text)
```

**Custom Types (Manual Mapping)**
```java
// Custom type requiring manual mapping
@Type(type = "jsonb")
private JsonNode metadata;             // → json

// PostgreSQL specific
@Column(columnDefinition = "uuid")
private UUID externalId;               // → uuid
```

### Step 7: Validation & Constraints

**Bean Validation Annotations**
```java
// Spring Boot
@Column(nullable = false, length = 100)
@NotNull @Size(max = 100)
private String name;

@Column(unique = true)
@Email
private String email;
```

```yaml
# SpecQL
name:
  type: text
  nullable: false
email:
  type: text
  unique: true
```

### Step 8: Inheritance Strategies

**Single Table Inheritance**
```java
// Spring Boot
@Entity
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@DiscriminatorColumn(name = "vehicle_type")
public abstract class Vehicle {
    @Id private Long id;
    private String manufacturer;
}

@Entity
@DiscriminatorValue("CAR")
public class Car extends Vehicle {
    private Integer seats;
}
```

```yaml
# SpecQL (flattened to single table)
vehicle:
  type: text  # discriminator column
manufacturer:
  type: text
seats:
  type: integer
  nullable: true  # only for cars
```

### Step 9: Generate Database Schema

**Create SpecQL Configuration**
```yaml
# specql.yaml
project: myapp
database: postgresql
schemas:
  - schemas/*.yaml
```

**Generate SQL**
```bash
# Generate DDL
specql generate ddl --config specql.yaml --output migrations/

# Generate indexes and constraints
specql generate indexes --config specql.yaml --output migrations/
```

### Step 10: Data Migration

**Export Existing Data**
```sql
-- Export from Spring Boot database
COPY users TO '/tmp/users.csv' WITH CSV HEADER;
COPY companies TO '/tmp/companies.csv' WITH CSV HEADER;
```

**Import to SpecQL Schema**
```sql
-- Import to new SpecQL schema
COPY users FROM '/tmp/users.csv' WITH CSV HEADER;
COPY companies FROM '/tmp/companies.csv' WITH CSV HEADER;
```

**Migration Scripts**
```bash
# Generate migration scripts
specql generate migration --from spring-boot --to specql --output migrations/
```

## Advanced Migration Scenarios

### Microservices Migration

**Service Boundary Analysis**
```bash
# Analyze service dependencies
specql analyze dependencies --java src/main/java/ --output analysis/

# Generate service-specific schemas
specql generate service-schemas --analysis analysis/ --output services/
```

### Legacy Spring Boot (Pre-JPA)

**EJB 2.x to JPA Migration**
```java
// Legacy EJB (not directly supported)
// Use manual conversion or intermediate JPA layer
```

### Complex Relationships

**Composite Keys**
```java
// Spring Boot
@EmbeddedId
private OrderItemId id;

@Embeddable
public class OrderItemId {
    private Long orderId;
    private Long productId;
}
```

```yaml
# SpecQL (composite key support needed)
# Currently requires manual definition
```

## Troubleshooting

### Common Issues

**JDT Parsing Errors**
```
Error: JDT server connection failed
```
**Solution**:
```bash
# Check Java installation
java -version

# Restart SpecQL with debug
export JAVA_PARSER_DEBUG=1
specql reverse java --verbose
```

**Annotation Not Recognized**
```
Warning: Unknown annotation @CustomValidation
```
**Solution**: Custom annotations are ignored - remove or replace with standard JPA

**Type Mapping Failures**
```
Warning: Could not map type 'CustomType'
```
**Solution**: Add custom type mapping or use `text` fallback

**Relationship Resolution**
```
Warning: Could not resolve target entity 'UnknownEntity'
```
**Solution**: Ensure all related entities are included in migration scope

### Performance Issues

**Large Codebases**
```bash
# Process in batches
find src/main/java -name "*.java" | split -l 50 - batches_
for batch in batches_*; do
    xargs specql reverse java --output-dir schemas/ < $batch
done
```

**Memory Optimization**
```bash
# Increase Java heap for large projects
export JAVA_OPTS="-Xmx2g"
specql reverse java large_project/ --output-dir schemas/
```

## Validation & Testing

### Schema Validation
```bash
# Validate generated schemas
specql validate schemas/ --config specql.yaml

# Check for inconsistencies
specql analyze schemas/ --output validation_report/
```

### Data Integrity Checks
```sql
-- Compare row counts
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'companies', COUNT(*) FROM companies;

-- Spot check data integrity
SELECT u.name, c.name
FROM users u
LEFT JOIN companies c ON u.company_id = c.id
WHERE u.company_id IS NOT NULL
LIMIT 10;
```

### Application Testing
```java
// Update Spring Boot application
@SpringBootApplication
@EnableJpaRepositories  // Keep for gradual migration
public class Application {
    // Test with both old and new schemas
}
```

## Rollback Strategy

### Database Rollback
```sql
-- Create backup before migration
CREATE SCHEMA backup;
-- Copy all tables to backup schema

-- Rollback if needed
DROP SCHEMA public CASCADE;
ALTER SCHEMA backup RENAME TO public;
```

### Application Rollback
```xml
<!-- Maven: keep both dependencies during transition -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>com.specql</groupId>
    <artifactId>specql-spring-integration</artifactId>
</dependency>
```

## Best Practices

### Migration Planning
1. **Start Small**: Migrate one bounded context at a time
2. **Test Thoroughly**: Validate data integrity at each step
3. **Gradual Rollout**: Use feature flags for gradual migration
4. **Backup Everything**: Multiple backup strategies

### Code Organization
1. **Separate Concerns**: Keep migration scripts separate from application code
2. **Version Control**: Commit migration steps incrementally
3. **Documentation**: Document each migration decision

### Performance Considerations
1. **Batch Processing**: Process large codebases in batches
2. **Parallel Processing**: Use multiple SpecQL instances for large projects
3. **Memory Management**: Monitor memory usage for large projects

## Success Metrics

### Migration Completeness
- [ ] All entities migrated
- [ ] All relationships preserved
- [ ] All constraints maintained
- [ ] Data integrity verified

### Performance Benchmarks
- [ ] Query performance maintained or improved
- [ ] Application startup time acceptable
- [ ] Memory usage within limits

### Code Quality
- [ ] SpecQL schemas well-documented
- [ ] Migration scripts tested
- [ ] Rollback procedures documented

## Support & Resources

### Getting Help
- **Documentation**: [Java AST Parsing Architecture](../reverse_engineering/JAVA_AST_PARSING.md)
- **API Reference**: [Java Reverse Engineering API](JAVA_REVERSE_ENGINEERING_API.md)
- **Examples**: [Java Examples Directory](../../examples/java/)
- **Issues**: [GitHub Issues](https://github.com/specql/specql/issues)

### Community Resources
- **Forum**: SpecQL Community Discussions
- **Slack**: #java-migration channel
- **Blog**: Migration Case Studies

---

## Quick Reference

### Command Summary
```bash
# Analyze project
find . -name "*.java" -exec grep -l "@Entity" {} \;

# Extract schemas
specql reverse java src/main/java/ --output-dir schemas/

# Validate schemas
specql validate schemas/

# Generate DDL
specql generate ddl --config specql.yaml
```

### Common Conversions
| Spring Boot | SpecQL |
|-------------|--------|
| `@Entity` | `entity: Name` |
| `@Table(name="x")` | `table: x` |
| `@Column(nullable=false)` | `nullable: false` |
| `@ManyToOne` | `type: ref(Entity)` |
| `@OneToMany` | `type: list(Entity)` |
| `@Enumerated` | `type: enum(...)` |

### File Structure After Migration
```
project/
├── schemas/           # SpecQL YAML files
│   ├── User.yaml
│   ├── Company.yaml
│   └── Product.yaml
├── migrations/        # Generated SQL
│   ├── 001_initial.sql
│   └── 002_indexes.sql
├── specql.yaml        # SpecQL configuration
└── backup/           # Data backups
```