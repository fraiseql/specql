# CLI Commands Reference

Complete reference for all SpecQL CLI commands.

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `init` | Create new project from template | `specql init blog myblog` |
| `generate` | Generate code from entities | `specql generate entities/*.yaml` |
| `validate` | Validate entity definitions | `specql validate entities/` |
| `examples` | Show built-in examples | `specql examples --list` |
| `reverse` | Import existing code | `specql reverse postgresql schema.sql` |

---

## specql init

Create a new SpecQL project from a template.

### Syntax

```bash
specql init [OPTIONS] TEMPLATE PROJECT_NAME
```

### Arguments

- `TEMPLATE` - Template to use (minimal, blog, crm)
- `PROJECT_NAME` - Name of project directory to create

### Options

- `--output-dir PATH` - Parent directory for project (default: current directory)
- `--force` - Overwrite existing directory
- `--help` - Show help message

### Templates

#### minimal
Basic project with single example entity.

**Contains:**
- `entities/example/contact.yaml` - Simple contact entity
- `README.md` - Getting started guide
- `.gitignore` - Ignores output directory

**Use when:** Learning SpecQL or starting a small project

#### blog
Complete blog platform with posts, authors, and comments.

**Contains:**
- `entities/blog/author.yaml` - Author entity with unique username
- `entities/blog/post.yaml` - Post with publish action
- `entities/blog/comment.yaml` - Comments with relationships
- Example of relationships and actions

**Use when:** Building content management systems

#### crm (coming soon)
Customer relationship management system.

### Examples

Create minimal project:
```bash
specql init minimal myproject
cd myproject
specql generate entities/**/*.yaml
```

Create blog in specific directory:
```bash
specql init blog myblog --output-dir ~/projects
cd ~/projects/myblog
```

---

## specql generate

Generate multi-language code from entity definitions.

### Syntax

```bash
specql generate [OPTIONS] FILES...
```

### Arguments

- `FILES...` - One or more YAML entity files or glob patterns

### Options

- `--output-dir PATH` - Output directory (default: ./output)
- `--target [all|postgresql|java|rust|typescript]` - Target language (default: all)
- `--dry-run` - Show what would be generated without writing files
- `--hierarchical` - Use hierarchical identifiers (a.b.c)
- `--help` - Show help message

### Targets

- `all` - Generate all supported languages
- `postgresql` - PostgreSQL tables and PL/pgSQL functions
- `java` - Java/Spring Boot entities and repositories
- `rust` - Rust/Diesel models and queries
- `typescript` - TypeScript/Prisma schema and types

### Examples

Generate all languages:
```bash
specql generate entities/**/*.yaml
```

Preview before generating:
```bash
specql generate entities/**/*.yaml --dry-run
```

Generate only PostgreSQL:
```bash
specql generate contact.yaml --target postgresql
```

Custom output directory:
```bash
specql generate entities/ --output-dir ../generated
```

---

## specql validate

Validate entity definitions without generating code.

### Syntax

```bash
specql validate [OPTIONS] FILES...
```

### Arguments

- `FILES...` - Entity files to validate

### Options

- `--strict` - Fail on warnings (not just errors)
- `--check-references` - Verify all entity references exist
- `--format [text|json]` - Output format (default: text)
- `--output FILE` - Write results to file
- `--help` - Show help message

### Exit Codes

- `0` - All files valid
- `1` - Validation errors found
- `2` - Warnings found (with --strict)

### Examples

Basic validation:
```bash
specql validate entities/*.yaml
```

Strict mode (fail on warnings):
```bash
specql validate entities/ --strict
```

JSON output for CI:
```bash
specql validate entities/ --format json --output validation.json
```

### CI Integration

Use in GitHub Actions:

```yaml
- name: Validate SpecQL entities
  run: specql validate entities/**/*.yaml --strict --format json
```

---

## specql examples

Show built-in example entity definitions.

### Syntax

```bash
specql examples [OPTIONS] [NAME]
```

### Arguments

- `NAME` - Name of example to show (optional)

### Options

- `--list` - List all available examples
- `--help` - Show help message

### Available Examples

| Name | Description |
|------|-------------|
| `simple-entity` | Basic entity with text fields |
| `with-relationships` | Entity with foreign key relationships |
| `with-actions` | Entity with business logic actions |
| `with-enums` | Enumerated fields |
| `with-timestamps` | Timestamp and date fields |
| `with-json` | JSON metadata fields |
| `blog-post` | Complete blog post example |
| `ecommerce-order` | E-commerce order with actions |

### Examples

List all examples:
```bash
specql examples --list
```

View specific example:
```bash
specql examples with-actions
```

Save example to file:
```bash
specql examples blog-post > post.yaml
specql generate post.yaml
```

---

## Tips & Tricks

### Workflow: New Project

1. Start from template:
   ```bash
   specql init blog myblog && cd myblog
   ```

2. Review and modify entities:
   ```bash
   cat entities/blog/post.yaml
   # Edit as needed
   ```

3. Validate before generating:
   ```bash
   specql validate entities/**/*.yaml
   ```

4. Preview output:
   ```bash
   specql generate entities/**/*.yaml --dry-run
   ```

5. Generate code:
   ```bash
   specql generate entities/**/*.yaml
   ```

### Workflow: Adding to Existing Project

1. Check example:
   ```bash
   specql examples with-actions
   ```

2. Create new entity:
   ```bash
   vim entities/myentity.yaml
   ```

3. Validate:
   ```bash
   specql validate entities/myentity.yaml
   ```

4. Generate:
   ```bash
   specql generate entities/myentity.yaml
   ```

### Error Handling

SpecQL provides helpful error messages:

```
❌ Invalid field type: 'string'
  File: contact.yaml | Entity: Contact | Field: email
  💡 Suggestion: Did you mean: text?
  📚 Docs: https://github.com/fraiseql/specql/.../FIELD_TYPES.md
```

If you get an error:
1. Read the error message (includes suggestions)
2. Check the docs link
3. Use `specql examples` to see correct syntax
4. Use `specql validate` to check before generating

---

See also:
- [Quickstart Guide](../00_getting_started/QUICKSTART.md)
- [Field Types Reference](../03_reference/FIELD_TYPES.md)
- [Troubleshooting](../08_troubleshooting/TROUBLESHOOTING.md)