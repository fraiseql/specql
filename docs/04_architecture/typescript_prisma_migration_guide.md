# TypeScript & Prisma Migration Guide

## Overview

This guide provides step-by-step instructions for migrating existing TypeScript and Prisma projects to use SpecQL's reverse engineering capabilities. The new TypeScript and Prisma parsers can automatically extract entity definitions from your existing codebase.

## Prerequisites

- SpecQL installed with TypeScript/Prisma parser support
- Existing TypeScript project with interfaces
- Existing Prisma schema (optional but recommended)

## Step 1: Install SpecQL with Parser Support

Ensure you have the latest SpecQL version with TypeScript and Prisma parser support:

```bash
# Install or update SpecQL
pip install specql --upgrade

# Verify parser availability
python -c "from src.parsers.typescript import TypeScriptParser, PrismaParser; print('Parsers available')"
```

## Step 2: Prepare Your Project

### For TypeScript Projects

1. **Organize your interfaces**: Ensure your TypeScript interfaces are in `.ts` or `.tsx` files
2. **Recommended structure**:
   ```
   src/
     types/
       entities.ts      # Main entity interfaces
       enums.ts         # Enum definitions
       api.ts          # API-related types
   ```

3. **Example TypeScript interfaces**:
   ```typescript
   // entities.ts
   export interface User {
     id: number;
     email: string;
     name?: string;
     profile?: UserProfile;
     posts: Post[];
     createdAt: Date;
   }

   export interface Post {
     id: number;
     title: string;
     content?: string;
     authorId: number;
     tags: string[];
     published: boolean;
   }

   // enums.ts
   export enum UserRole {
     ADMIN = 'admin',
     MODERATOR = 'moderator',
     USER = 'user'
   }
   ```

### For Prisma Projects

1. **Ensure schema.prisma exists** in your project root
2. **Example Prisma schema**:
   ```prisma
   model User {
     id        Int      @id @default(autoincrement())
     email     String   @unique
     name      String?
     posts     Post[]
     profile   Profile?
     createdAt DateTime @default(now())
   }

   model Post {
     id        Int      @id @default(autoincrement())
     title     String
     content   String?
     authorId  Int
     published Boolean  @default(false)

     author    User     @relation(fields: [authorId], references: [id])
   }
   ```

## Step 3: Run Reverse Engineering

### Option A: Parse TypeScript Files

```bash
# Parse a single TypeScript file
python -c "
from src.parsers.typescript.typescript_parser import TypeScriptParser
parser = TypeScriptParser()
entities = parser.parse_file('src/types/entities.ts')
print(f'Found {len(entities)} entities')
for entity in entities:
    print(f'- {entity.name}: {len(entity.fields)} fields')
"

# Parse an entire project directory
python -c "
from src.parsers.typescript.typescript_parser import TypeScriptParser
parser = TypeScriptParser()
entities = parser.parse_project('./src')
print(f'Found {len(entities)} entities from project')
"
```

### Option B: Parse Prisma Schema

```bash
# Parse Prisma schema
python -c "
from src.parsers.typescript.prisma_parser import PrismaParser
parser = PrismaParser()
entities = parser.parse_schema_file('schema.prisma')
print(f'Found {len(entities)} entities')
for entity in entities:
    print(f'- {entity.name}: {len(entity.fields)} fields')
"
```

### Option C: Combined TypeScript + Prisma

For projects with both TypeScript interfaces and Prisma schemas:

```bash
# Parse both and merge results
python -c "
from src.parsers.typescript import TypeScriptParser, PrismaParser

# Parse Prisma schema
prisma_parser = PrismaParser()
prisma_entities = prisma_parser.parse_schema_file('schema.prisma')

# Parse TypeScript interfaces
ts_parser = TypeScriptParser()
ts_entities = ts_parser.parse_project('./src/types')

# Merge entities (handle conflicts as needed)
all_entities = prisma_entities + ts_entities
print(f'Total entities: {len(all_entities)}')
"
```

## Step 4: Generate SpecQL Configuration

### Automatic Configuration Generation

```python
from src.core.universal_ast import UniversalEntity
from src.generators import SpecQLGenerator

# Assuming you have entities from parsing
def generate_specql_config(entities: list[UniversalEntity]) -> str:
    config_lines = ['# Auto-generated SpecQL configuration', '']

    for entity in entities:
        config_lines.append(f'entity {entity.name}:')
        config_lines.append(f'  schema: {entity.schema}')

        for field in entity.fields:
            required = 'required' if field.required else 'optional'
            config_lines.append(f'  {field.name}: {field.type.value} {required}')

        if entity.fields:
            config_lines.append('')

    return '\\n'.join(config_lines)

# Generate and save config
config = generate_specql_config(all_entities)
with open('specql_config.yaml', 'w') as f:
    f.write(config)
```

### Manual Configuration Review

After automatic generation, review and customize the configuration:

```yaml
# specql_config.yaml
entities:
  - name: User
    schema: public
    fields:
      - name: id
        type: integer
        required: true
        primary_key: true
      - name: email
        type: text
        required: true
        unique: true
      - name: name
        type: text
        required: false
      - name: profile
        type: reference
        required: false
        references: Profile

  - name: Post
    schema: public
    fields:
      - name: id
        type: integer
        required: true
        primary_key: true
      - name: title
        type: text
        required: true
      - name: content
        type: text
        required: false
      - name: authorId
        type: reference
        required: true
        references: User
```

## Step 5: Handle Complex Cases

### Type Mapping Reference

| TypeScript Type | Prisma Type | SpecQL Type | Notes |
|----------------|-------------|-------------|-------|
| `string` | `String` | `text` | Basic text type |
| `number` | `Int`/`Float` | `integer`/`rich` | Numbers map to integer, floats to rich |
| `boolean` | `Boolean` | `boolean` | Direct mapping |
| `Date` | `DateTime` | `datetime` | Date/time handling |
| `string[]` | `String[]` | `list` | Array types |
| `any` | `Json` | `rich` | Complex types |
| `T \| U` | N/A | `rich` | Union types |
| `T & U` | N/A | `rich` | Intersection types |

### Handling Relationships

```typescript
// TypeScript
interface Post {
  id: number;
  author: User;        // Direct reference
  authorId: number;    // Foreign key
}

// Prisma
model Post {
  id       Int  @id
  authorId Int
  author   User @relation(fields: [authorId], references: [id])
}
```

Both patterns are supported. The parsers will create REFERENCE type fields for relationships.

### Enum Handling

```typescript
enum Status {
  ACTIVE = 'active',
  INACTIVE = 'inactive'
}
```

Enums are parsed as entities with values stored in the description field. You can reference them in your SpecQL configuration.

## Step 6: Validation and Testing

### Validate Parsed Entities

```python
def validate_entities(entities):
    """Basic validation of parsed entities"""
    for entity in entities:
        assert entity.name, f"Entity missing name: {entity}"
        assert entity.fields, f"Entity {entity.name} has no fields"

        for field in entity.fields:
            assert field.name, f"Field missing name in {entity.name}"
            assert field.type, f"Field {field.name} missing type in {entity.name}"

    print("✓ All entities validated")

validate_entities(all_entities)
```

### Generate Test Data

```python
# Generate sample data for testing
from src.core.specql import SpecQL

specql = SpecQL.from_config('specql_config.yaml')

# Generate test fixtures
test_data = specql.generate_test_data()
print(f"Generated test data for {len(test_data)} entities")
```

## Step 7: Migration Best Practices

### Incremental Migration

1. **Start small**: Begin with 2-3 core entities
2. **Test thoroughly**: Validate each entity before moving to the next
3. **Gradual rollout**: Migrate entities in order of dependency

### Handling Inconsistencies

```python
def resolve_conflicts(ts_entities, prisma_entities):
    """Resolve conflicts between TypeScript and Prisma definitions"""
    conflicts = []

    ts_names = {e.name for e in ts_entities}
    prisma_names = {e.name for e in prisma_entities}

    # Find entities in both
    common = ts_names & prisma_names

    for name in common:
        ts_entity = next(e for e in ts_entities if e.name == name)
        prisma_entity = next(e for e in prisma_entities if e.name == name)

        # Compare field counts
        if len(ts_entity.fields) != len(prisma_entity.fields):
            conflicts.append(f"Field count mismatch for {name}")

    return conflicts
```

### Performance Optimization

- **Cache parsed results**: Store parsed entities to avoid re-parsing
- **Parallel processing**: Parse multiple files concurrently
- **Selective parsing**: Only parse files that have changed

## Troubleshooting

### Common Issues

1. **"File not found" errors**
   - Ensure correct file paths
   - Check file permissions

2. **Empty entity lists**
   - Verify file contains valid TypeScript/Prisma syntax
   - Check for syntax errors in source files

3. **Type mapping issues**
   - Review the type mapping table above
   - Custom types may need manual mapping

4. **Relationship resolution**
   - Ensure foreign key naming conventions are followed
   - Check that referenced entities exist

### Debug Commands

```bash
# Debug TypeScript parsing
python -c "
from src.parsers.typescript.typescript_parser import TypeScriptParser
parser = TypeScriptParser()
try:
    entities = parser.parse_file('debug.ts')
    print(f'Success: {len(entities)} entities')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
"

# Debug Prisma parsing
python -c "
from src.parsers.typescript.prisma_parser import PrismaParser
parser = PrismaParser()
try:
    entities = parser.parse_schema_file('schema.prisma')
    print(f'Success: {len(entities)} entities')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
"
```

## Next Steps

After successful migration:

1. **Generate database schema** from your SpecQL configuration
2. **Create API endpoints** using SpecQL generators
3. **Set up data validation** and business rules
4. **Implement authentication** and authorization
5. **Add monitoring** and logging

## Support

For issues or questions:

- Check the [SpecQL documentation](../README.md)
- Review parser source code in `src/parsers/typescript/`
- File issues on the [SpecQL GitHub repository](https://github.com/your-org/specql)

---

*This migration guide covers the core functionality available in SpecQL's TypeScript and Prisma parsers. Features may be extended in future versions.*