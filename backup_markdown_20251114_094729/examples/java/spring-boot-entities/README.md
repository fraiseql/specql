# Spring Boot JPA Entity Examples

This directory contains example Java JPA entities that demonstrate various patterns and annotations supported by SpecQL's Java reverse engineering.

## Overview

These examples showcase real-world Spring Boot entity patterns that can be automatically converted to SpecQL YAML schemas using the `specql reverse java` command.

## Entity Examples

### User.java
**Purpose**: Core user entity with authentication and profile information

**Key Features**:
- Basic JPA annotations (`@Entity`, `@Table`, `@Column`)
- Validation annotations (`@NotBlank`, `@Email`, `@Size`)
- Enum fields (`@Enumerated`)
- Relationships (`@ManyToOne`, `@OneToMany`)
- Lifecycle callbacks (`@PrePersist`, `@PreUpdate`)
- Database indexes

**SpecQL Output**:
```yaml
entity: User
schema: public
table: users
fields:
  firstName:
    type: text
    nullable: false
  lastName:
    type: text
    nullable: false
  email:
    type: text
    nullable: false
    unique: true
  phone:
    type: text
  status:
    type: enum(active, inactive, suspended, pending)
  createdAt:
    type: timestamp
  updatedAt:
    type: timestamp
  company:
    type: ref(Company)
  roles:
    type: list(UserRole)
```

### Company.java
**Purpose**: Organization entity with embedded address information

**Key Features**:
- Embedded objects (`@Embedded`)
- Complex validation rules
- One-to-many relationships
- Enum fields with business logic

**SpecQL Output**:
```yaml
entity: Company
schema: public
table: companies
fields:
  name:
    type: text
    nullable: false
  description:
    type: text
  websiteUrl:
    type: text
  streetAddress:
    type: text
  city:
    type: text
  state:
    type: text
  postalCode:
    type: text
  country:
    type: text
  employeeCount:
    type: integer
  size:
    type: enum(startup, small, medium, large, enterprise)
  createdAt:
    type: timestamp
  updatedAt:
    type: timestamp
  employees:
    type: list(User)
```

### UserRole.java
**Purpose**: Many-to-many relationship entity

**Key Features**:
- Junction table pattern
- Composite relationships
- Audit fields

**SpecQL Output**:
```yaml
entity: UserRole
schema: public
table: user_roles
fields:
  user:
    type: ref(User)
  role:
    type: enum(admin, manager, user, guest)
  assignedAt:
    type: timestamp
  assignedBy:
    type: text
```

## Running the Examples

### Prerequisites
```bash
# Ensure Java 11+ is installed
java -version

# Install SpecQL with Java support
pip install specql[java]
```

### Extract Schemas
```bash
# Process all entities in this directory
specql reverse java . --output-dir schemas/

# Preview extraction without writing files
specql reverse java . --preview

# Process individual files
specql reverse java User.java --output-dir schemas/
```

### Expected Output
The reverse engineering should generate the following SpecQL YAML files:
- `schemas/User.yaml`
- `schemas/Company.yaml`
- `schemas/UserRole.yaml`
- `schemas/UserStatus.yaml` (enum extraction)
- `schemas/CompanySize.yaml` (enum extraction)
- `schemas/Role.yaml` (enum extraction)

## Testing the Extraction

### Unit Test
```python
from src.reverse_engineering.java.java_parser import JavaParser

def test_entity_extraction():
    parser = JavaParser()
    result = parser.parse_file("User.java")

    assert len(result.entities) == 1
    user_entity = result.entities[0]

    assert user_entity.name == "User"
    assert user_entity.table == "users"
    assert "email" in user_entity.fields
    assert "company" in user_entity.fields

    # Check relationships
    company_field = user_entity.fields["company"]
    assert company_field.type_name == "ref(Company)"
```

### Integration Test
```bash
# Run the extraction
specql reverse java . --output-dir test_output/

# Validate generated schemas
specql validate test_output/

# Generate DDL from schemas
specql generate ddl --config specql.yaml --output migrations/
```

## Common Patterns Demonstrated

### 1. Basic Entity Structure
```java
@Entity
@Table(name = "table_name")
public class EntityName {
    @Id @GeneratedValue
    private Long id;

    @Column(nullable = false)
    private String fieldName;
}
```

### 2. Relationships
```java
// Many-to-One
@ManyToOne
@JoinColumn(name = "foreign_key_id")
private RelatedEntity related;

// One-to-Many
@OneToMany(mappedBy = "parent")
private List<ChildEntity> children;
```

### 3. Embedded Objects
```java
@Embedded
private Address address;

@Embeddable
public class Address {
    private String street;
    private String city;
}
```

### 4. Enums
```java
@Enumerated(EnumType.STRING)
private Status status;

public enum Status {
    ACTIVE, INACTIVE
}
```

### 5. Validation
```java
@Column(nullable = false, length = 100)
@NotBlank @Size(max = 100)
private String validatedField;
```

### 6. Indexes and Constraints
```java
@Table(indexes = {
    @Index(name = "idx_field", columnList = "field"),
    @Index(name = "idx_composite", columnList = "field1, field2", unique = true)
})
```

## Troubleshooting

### JDT Connection Issues
```
Error: JDT server connection failed
```
**Solution**: Ensure Java 11+ is available and JDT JARs are in the classpath.

### Annotation Not Recognized
```
Warning: Unknown annotation @CustomAnnotation
```
**Solution**: Only standard JPA annotations are supported. Custom annotations are ignored.

### Type Mapping Issues
```
Warning: Could not map type 'CustomType'
```
**Solution**: Add custom type mapping or use basic types (String, Long, etc.).

## Migration Workflow

1. **Analyze**: Review entities for compatibility
2. **Extract**: Run `specql reverse java` on entity files
3. **Validate**: Check generated schemas with `specql validate`
4. **Generate**: Create DDL with `specql generate ddl`
5. **Migrate**: Apply DDL to database and migrate data

## Related Documentation

- [Java AST Parsing Architecture](../../reverse_engineering/JAVA_AST_PARSING.md)
- [Spring Boot Migration Guide](../../guides/SPRING_BOOT_MIGRATION.md)
- [Java Reverse Engineering API](../../api/JAVA_REVERSE_ENGINEERING_API.md)