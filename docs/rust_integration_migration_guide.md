# Rust Integration Migration Guide

## Overview

This guide provides step-by-step instructions for migrating existing Diesel-based Rust projects to use SpecQL's reverse engineering capabilities.

## Prerequisites

- Rust 1.70+
- Diesel ORM with PostgreSQL
- SpecQL CLI installed
- Existing Diesel project with `schema.rs` and model files

## Step 1: Project Structure Analysis

### Current Diesel Project Structure
```
my_project/
├── src/
│   ├── models/
│   │   ├── user.rs
│   │   ├── post.rs
│   │   └── mod.rs
│   ├── schema.rs
│   └── main.rs
└── Cargo.toml
```

### Required Structure for SpecQL
Ensure your project follows this structure:
- Models in `src/models/` directory
- Single `schema.rs` file in `src/`
- Models use standard Diesel derive macros

## Step 2: Validate Diesel Code

Ensure your models use supported Diesel patterns:

### ✅ Supported Patterns

```rust
// Basic model with derives
#[derive(Queryable, Identifiable, Debug, Clone)]
#[table_name = "users"]
pub struct User {
    pub id: i32,
    pub name: String,
    pub email: String,
    pub created_at: chrono::NaiveDateTime,
}

// Insertable struct
#[derive(Insertable)]
#[table_name = "users"]
pub struct NewUser<'a> {
    pub name: &'a str,
    pub email: &'a str,
}

// Relationships
#[derive(Queryable, Associations, Identifiable, Debug)]
#[belongs_to(User)]
#[table_name = "posts"]
pub struct Post {
    pub id: i32,
    pub user_id: i32,
    pub title: String,
    pub content: String,
}
```

### ❌ Unsupported Patterns (for now)

```rust
// Custom table names without #[table_name]
#[derive(Queryable)]
#[diesel(table_name = users)]  // Use #[table_name = "users"] instead
pub struct User { ... }

// Complex custom derives
#[derive(MyCustomDerive, Queryable)]  // May not be recognized
pub struct User { ... }
```

## Step 3: Run SpecQL Reverse Engineering

### Basic Usage

```bash
# Navigate to your Rust project root
cd my_project

# Run reverse engineering on models directory
specql reverse-engineer rust \
  --models-dir src/models \
  --schema-file src/schema.rs \
  --output entities/
```

### Advanced Options

```bash
# With custom output format
specql reverse-engineer rust \
  --models-dir src/models \
  --schema-file src/schema.rs \
  --output entities/ \
  --format yaml \
  --include-relationships \
  --verbose
```

### Command Line Options

- `--models-dir`: Directory containing model .rs files (default: `src/models`)
- `--schema-file`: Path to schema.rs file (default: `src/schema.rs`)
- `--output`: Output directory for generated entities (default: `entities`)
- `--format`: Output format - `yaml` or `json` (default: `yaml`)
- `--include-relationships`: Include foreign key relationships (default: true)
- `--verbose`: Enable detailed logging

## Step 4: Review Generated Entities

SpecQL will generate entity files for each model:

### Example Generated Entity (YAML)

```yaml
name: User
schema: public
table: users
description: "Diesel model User"
fields:
  id:
    name: id
    type_name: integer
    nullable: false
    description: "Primary key field id"
  name:
    name: name
    type_name: text
    nullable: false
    description: "User name field"
  email:
    name: email
    type_name: text
    nullable: false
    description: "User email field"
  created_at:
    name: created_at
    type_name: timestamp
    nullable: false
    description: "Creation timestamp"

relationships:
  - name: posts
    type: has_many
    target_entity: Post
    foreign_key: user_id
```

## Step 5: Validate and Customize

### Validation Checklist

- [ ] All models were discovered
- [ ] Field types mapped correctly
- [ ] Relationships detected properly
- [ ] Primary keys identified
- [ ] Nullable fields marked correctly

### Common Customizations

```yaml
# Add descriptions
description: "User account with authentication"

# Add validation rules
fields:
  email:
    validation_pattern: "^[^@]+@[^@]+\\.[^@]+$"

# Add business logic
actions:
  - name: send_welcome_email
    type: create
    description: "Send welcome email after user creation"
```

## Step 6: Generate Application Code

Once entities are validated, generate your application:

```bash
# Generate full application
specql generate \
  --entities entities/ \
  --output generated/ \
  --language rust \
  --framework axum \
  --database postgres
```

## Troubleshooting

### Common Issues

#### "No models found" Error
- Check that models use `#[derive(Queryable)]`
- Ensure models are in the specified `--models-dir`
- Verify file permissions

#### "Schema parsing failed" Error
- Check `schema.rs` syntax
- Ensure all table! macros are properly formatted
- Verify foreign key relationships are defined

#### "Type mapping failed" Warning
- Some Rust types may not have direct SQL equivalents
- Check the generated entity for `type_name` field
- Custom types may need manual mapping

### Debug Mode

Enable verbose logging for detailed error information:

```bash
specql reverse-engineer rust --verbose --debug
```

### Performance Considerations

For large projects (>50 models):
- Parsing may take several seconds
- Consider splitting into smaller directories
- Use `--include-relationships false` for faster initial parsing

## Migration Examples

### From Diesel CLI

If migrating from `diesel print-schema`:

1. Run `diesel print-schema > src/schema.rs`
2. Ensure models use consistent naming
3. Run SpecQL reverse engineering
4. Compare generated entities with existing code

### From Hand-Written Schemas

For projects with hand-written schemas:

1. Ensure schema.rs follows Diesel conventions
2. Add missing table! macro definitions
3. Run reverse engineering
4. Manually adjust type mappings if needed

## Next Steps

After successful migration:

1. **Test Generated Code**: Run your application with generated entities
2. **API Generation**: Use SpecQL to generate REST APIs
3. **Database Migration**: Apply any schema changes
4. **Integration Testing**: Validate end-to-end functionality

## Support

For issues or questions:
- Check the [troubleshooting guide](./troubleshooting.md)
- Review [integration test examples](../examples/rust_integration_examples.py)
- File issues on GitHub with your project structure</content>
</xai:function_call">Test handling of malformed Rust files and edge cases.