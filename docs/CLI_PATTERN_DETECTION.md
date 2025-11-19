# Pattern Detection CLI

The SpecQL CLI includes powerful pattern detection capabilities that automatically identify common architectural patterns in your source code.

## Quick Start

```bash
# Detect patterns in a single file
specql detect-patterns src/models/user.rs

# Detect patterns in multiple files
specql detect-patterns src/models/*.rs

# Filter by confidence threshold
specql detect-patterns src/models/user.rs --min-confidence 0.9

# Detect specific patterns only
specql detect-patterns src/models/user.rs --patterns soft-delete audit-trail

# Output in different formats
specql detect-patterns src/models/user.rs --format json
specql detect-patterns src/models/user.rs --format yaml
```

## Supported Patterns

### Core Patterns

- **soft-delete**: Soft deletion with `deleted_at` timestamps
- **audit-trail**: Automatic `created_at`/`updated_at` tracking
- **multi-tenant**: Tenant isolation with `tenant_id` fields
- **state-machine**: Status transitions with validation
- **hierarchical**: Self-referencing parent-child relationships
- **versioning**: Optimistic locking with version fields

### Advanced Patterns

- **event-sourcing**: Event-driven state changes
- **sharding**: Data partitioning strategies
- **cache-invalidation**: Cache management patterns
- **rate-limiting**: Request throttling mechanisms

## Pattern Detection in Reverse Engineering

Pattern detection is automatically integrated with reverse engineering:

```bash
# Reverse engineer with automatic pattern application
specql reverse src/models/ --framework diesel --with-patterns

# Process entire project with patterns
specql reverse /path/to/rust/project --framework diesel --with-patterns --output entities/
```

When `--with-patterns` is used, detected patterns are automatically applied to enrich the generated SpecQL YAML with metadata and constraints.

## Output Formats

### Text (Default)
```
📁 Analyzing src/models/user.rs...
   Detected language: rust
   ✓ Found 2 patterns:
      • soft_delete: 94% confidence
        - Line 15: deleted_at: Option<DateTime<Utc>>,
        - Line 16: #[serde(skip_serializing_if = "Option::is_none")]
      • audit_trail: 89% confidence
        - Line 12: created_at: DateTime<Utc>,
        - Line 13: updated_at: DateTime<Utc>,
```

### JSON
```json
[
  {
    "file": "src/models/user.rs",
    "language": "rust",
    "patterns": {
      "soft_delete": {
        "confidence": 0.94,
        "evidence": ["Line 15: deleted_at: Option<DateTime<Utc>>,"]
      },
      "audit_trail": {
        "confidence": 0.89,
        "evidence": ["Line 12: created_at: DateTime<Utc>,"]
      }
    }
  }
]
```

### YAML
```yaml
- file: src/models/user.rs
  language: rust
  patterns:
    soft_delete:
      confidence: 0.94
      evidence:
      - Line 15: deleted_at: Option<DateTime<Utc>>,
    audit_trail:
      confidence: 0.89
      evidence:
      - Line 12: created_at: DateTime<Utc>,
```

## Language Support

Pattern detection works across multiple languages:

- **Rust**: Diesel, SeaORM frameworks
- **Python**: SQLAlchemy, Django frameworks
- **TypeScript**: Prisma framework
- **Java**: Hibernate, Spring frameworks
- **SQL**: Raw SQL with triggers and constraints

## Confidence Scoring

Patterns are assigned confidence scores from 0.0 to 1.0:

- **0.0-0.3**: Low confidence, likely false positive
- **0.3-0.7**: Medium confidence, needs verification
- **0.7-0.9**: High confidence, probably correct
- **0.9-1.0**: Very high confidence, almost certain

Use `--min-confidence` to filter results by confidence level.

## Integration with SpecQL

Detected patterns automatically enhance SpecQL entity definitions:

```yaml
# Generated with --with-patterns
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
      nullable: false
```

## Examples

### Rust with Diesel
```rust
#[derive(Queryable, Insertable)]
#[table_name = "contacts"]
pub struct Contact {
    pub id: Uuid,
    pub email: String,
    pub deleted_at: Option<DateTime<Utc>>,  // soft_delete pattern
    pub created_at: DateTime<Utc>,          // audit_trail pattern
    pub updated_at: DateTime<Utc>,          // audit_trail pattern
    pub tenant_id: Uuid,                    // multi_tenant pattern
}
```

### Python with SQLAlchemy
```python
class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(UUID, primary_key=True)
    email = Column(String)
    deleted_at = Column(DateTime, nullable=True)  # soft_delete
    created_at = Column(DateTime)                  # audit_trail
    updated_at = Column(DateTime)                  # audit_trail
    tenant_id = Column(UUID)                       # multi_tenant
```

## Troubleshooting

### No Patterns Detected
- Try lowering `--min-confidence` threshold
- Check that the file contains supported patterns
- Verify the language is correctly detected

### Incorrect Language Detection
- Use `--language` flag to override auto-detection
- Supported languages: rust, python, typescript, java, sql

### Performance Issues
- Pattern detection is fast for individual files
- For large projects, use project-level processing with `--exclude` patterns
- Consider using `--min-confidence` to reduce output

## See Also

- [Framework Integration](FRAMEWORK_INTEGRATION.md) - Framework-specific features
- [Reverse Engineering Guide](../guides/reverse_engineering.md) - Complete reverse engineering workflow
- [Pattern Library](../stdlib/patterns/) - Available pattern implementations