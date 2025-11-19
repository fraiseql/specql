# Framework Integration

SpecQL provides deep integration with popular ORM frameworks, automatically detecting framework-specific patterns and applying appropriate optimizations during reverse engineering.

## Supported Frameworks

### Rust Frameworks

#### Diesel
```bash
specql reverse src/models/ --framework diesel --with-patterns
```

**Auto-detected patterns:**
- `soft_delete`: `deleted_at` fields with `Option<DateTime>`
- `audit_trail`: `created_at`/`updated_at` fields
- `multi_tenant`: `tenant_id` fields with foreign key constraints

**Generated SpecQL:**
```yaml
Contact:
  fields:
    id: Uuid
    email: String
    deleted_at: DateTime?
    created_at: DateTime
    updated_at: DateTime

  patterns:
    soft_delete: true
    audit_trail: true

  constraints:
    deleted_at:
      index: true
      nullable: true
    created_at:
      auto_managed: true
```

#### SeaORM
```bash
specql reverse src/entities/ --framework seaorm --with-patterns
```

**Additional patterns:**
- `multi_tenant`: Enhanced tenant isolation
- `hierarchical`: Self-referencing relationships
- `versioning`: Optimistic locking

### Python Frameworks

#### SQLAlchemy
```bash
specql reverse src/models/ --framework sqlalchemy --with-patterns
```

**Auto-detected patterns:**
- `soft_delete`: `deleted_at` columns
- `audit_trail`: `created_at`/`updated_at` columns
- `versioning`: `version` columns for optimistic locking

#### Django
```bash
specql reverse myapp/models/ --framework django --with-patterns
```

**Framework-specific features:**
- Auto-detection of Django model Meta options
- Foreign key relationship inference
- Custom field type mapping

### TypeScript Frameworks

#### Prisma
```bash
specql reverse prisma/schema.prisma --framework prisma --with-patterns
```

**Auto-detected patterns:**
- `soft_delete`: `deletedAt` fields
- `audit_trail`: `createdAt`/`updatedAt` fields
- `multi_tenant`: `tenantId` fields

### Java Frameworks

#### Hibernate/JPA
```bash
specql reverse src/main/java/ --framework hibernate --with-patterns
```

**Auto-detected patterns:**
- `audit_trail`: `@CreatedDate`/`@LastModifiedDate` annotations
- `versioning`: `@Version` annotation
- `soft_delete`: Custom soft delete annotations

#### Spring Data
```bash
specql reverse src/main/java/ --framework spring --with-patterns
```

**Framework-specific features:**
- Repository pattern detection
- Validation annotation mapping
- Custom converter detection

## Framework Auto-Detection

SpecQL can automatically detect frameworks from project structure:

```bash
# Auto-detects Diesel from Cargo.toml and file patterns
specql reverse src/ --with-patterns

# Auto-detects SQLAlchemy from imports and structure
specql reverse src/ --with-patterns

# Explicit framework specification
specql reverse src/ --framework diesel --with-patterns
```

### Detection Logic

**Rust Projects:**
- `Cargo.toml` contains `diesel` → `diesel` framework
- `Cargo.toml` contains `sea-orm` → `seaorm` framework
- `.rs` files with `use diesel::` → `diesel` framework

**Python Projects:**
- Files contain `from sqlalchemy` → `sqlalchemy` framework
- Files contain `from django.db` → `django` framework
- `requirements.txt` or `pyproject.toml` dependencies

**TypeScript Projects:**
- `package.json` contains `prisma` → `prisma` framework
- Files contain `import { PrismaClient }` → `prisma` framework

**Java Projects:**
- Files contain `@Entity` and `javax.persistence` → `hibernate` framework
- Files contain `@Entity` and `jakarta.persistence` → `spring` framework

## Pattern Enhancement

When `--with-patterns` is used, frameworks receive pattern-specific enhancements:

### Soft Delete Enhancement
```yaml
# Framework-aware soft delete
Contact:
  patterns:
    soft_delete: true

  actions:
    delete:
      # Framework-specific delete implementation
      sql: "UPDATE contacts SET deleted_at = NOW() WHERE id = ?"
      params: [id]

    restore:
      # Framework-specific restore implementation
      sql: "UPDATE contacts SET deleted_at = NULL WHERE id = ?"
      params: [id]
```

### Audit Trail Enhancement
```yaml
# Framework-aware audit trails
Contact:
  patterns:
    audit_trail: true

  hooks:
    before_insert:
      # Framework-specific timestamp setting
      set_created_at: "NOW()"
      set_updated_at: "NOW()"

    before_update:
      # Framework-specific update tracking
      set_updated_at: "NOW()"
```

### Multi-Tenant Enhancement
```yaml
# Framework-aware tenant isolation
Contact:
  patterns:
    multi_tenant: true

  constraints:
    tenant_id:
      required: true
      foreign_key: "tenants.id"

  # Automatic tenant filtering in queries
  query_filters:
    - "tenant_id = :current_tenant"
```

## Project-Level Processing

Process entire projects with framework-aware batch processing:

```bash
# Process Rust Diesel project
specql reverse src/ --framework diesel --with-patterns --output entities/

# Exclude test files and migrations
specql reverse src/ --framework diesel --with-patterns \
  --exclude "*/tests/*" \
  --exclude "*/migrations/*" \
  --output entities/

# Preview mode (no files written)
specql reverse src/ --framework diesel --with-patterns --preview
```

### Progress Reporting

Large projects show progress with rich formatting:

```
📂 Discovered 25 source files
Processing files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:02
✅ Processed 25 files successfully
```

## Framework Registry

SpecQL maintains a registry of supported frameworks with their capabilities:

```python
FRAMEWORK_REGISTRY = {
    'diesel': {
        'language': 'rust',
        'file_extensions': ['.rs'],
        'pattern_enhancers': ['soft_delete', 'audit_trail']
    },
    'seaorm': {
        'language': 'rust',
        'file_extensions': ['.rs'],
        'pattern_enhancers': ['soft_delete', 'audit_trail', 'multi_tenant']
    },
    # ... more frameworks
}
```

## Custom Framework Support

Extend SpecQL with custom frameworks:

```python
from src.cli.framework_registry import FrameworkRegistry, FrameworkConfig

# Register custom framework
custom_config = FrameworkConfig(
    name='custom_orm',
    language='rust',
    file_extensions=['.rs'],
    parser_class=CustomParser,
    pattern_enhancers=['soft_delete', 'audit_trail']
)

FrameworkRegistry.FRAMEWORKS['custom_orm'] = custom_config
```

## Examples

### Complete Rust Diesel Project
```bash
# Project structure
myapp/
├── src/
│   ├── models/
│   │   ├── contact.rs
│   │   ├── company.rs
│   │   └── user.rs
│   └── main.rs
├── migrations/
└── Cargo.toml

# Reverse engineer entire project
specql reverse myapp/src/ --framework diesel --with-patterns --output entities/

# Result: entities/Contact.yaml, entities/Company.yaml, entities/User.yaml
```

### Python SQLAlchemy Project
```bash
# Reverse engineer with framework detection
specql reverse src/models/ --framework sqlalchemy --with-patterns

# Generated YAML includes SQLAlchemy-specific metadata
Contact:
  framework:
    sqlalchemy:
      table_name: contacts
      mixins: [TimestampMixin, SoftDeleteMixin]

  patterns:
    soft_delete: true
    audit_trail: true
```

## Troubleshooting

### Framework Not Detected
- Check file extensions match framework expectations
- Verify framework imports/dependencies are present
- Use explicit `--framework` flag

### Incorrect Pattern Detection
- Some frameworks have unique pattern implementations
- Check framework-specific documentation
- Use `--min-confidence` to filter results

### Performance Issues
- Large projects may take time with pattern detection
- Use `--exclude` to skip irrelevant directories
- Consider processing in smaller batches

## See Also

- [Pattern Detection CLI](CLI_PATTERN_DETECTION.md) - Pattern detection commands
- [Reverse Engineering Guide](../guides/reverse_engineering.md) - Complete workflow
- [Framework Registry](../src/cli/framework_registry.py) - Supported frameworks