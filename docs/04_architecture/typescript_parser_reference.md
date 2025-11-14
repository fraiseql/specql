# TypeScript Parser Reference

## Overview

The TypeScript parser provides comprehensive reverse engineering capabilities for TypeScript projects, extracting entity definitions from interface and type definitions. This document details supported features, limitations, and usage patterns.

## Supported Features

### Core Language Constructs

#### Interfaces
```typescript
interface User {
  id: number;
  email: string;
  name?: string;           // Optional fields
  profile?: UserProfile;   // Reference types
  posts: Post[];          // Array types
  metadata: any;          // Complex types
  createdAt: Date;        // Built-in types
}
```
- ✅ Basic interface parsing
- ✅ Optional fields (`field?: Type`)
- ✅ Interface inheritance (`extends BaseInterface`)
- ✅ Nested object types
- ✅ Complex type expressions

#### Type Aliases
```typescript
type UserId = number;

type UserProfile = {
  bio?: string;
  avatarUrl?: string;
};

type ApiResponse<T> = {
  success: boolean;
  data?: T;
  error?: string;
};
```
- ✅ Object type aliases
- ✅ Generic type parameters (basic support)
- ✅ Simple type aliases (mapped to rich types)

#### Enums
```typescript
enum Status {
  ACTIVE,
  INACTIVE,
  PENDING = 'pending',
  APPROVED = 1
}
```
- ✅ String enums
- ✅ Numeric enums
- ✅ Mixed enums
- ✅ Auto-assigned values

### Type System Support

#### Primitive Types
| TypeScript Type | SpecQL Mapping | Notes |
|----------------|----------------|-------|
| `string` | `text` | Basic string type |
| `number` | `integer` | All numbers map to integer |
| `boolean` | `boolean` | Direct boolean mapping |
| `Date` | `datetime` | Date objects |
| `any` | `rich` | Generic complex type |
| `unknown` | `rich` | Unknown types |
| `null` | `rich` | Null type |
| `undefined` | `rich` | Undefined type |

#### Complex Types
```typescript
interface ComplexEntity {
  // Union types
  status: 'active' | 'inactive' | 'pending';

  // Intersection types
  data: BaseData & ExtendedData;

  // Generic types
  items: Array<string>;
  mapping: Record<string, number>;

  // Function types (ignored)
  callback: (data: any) => void;

  // Literal types
  theme: 'light' | 'dark';
}
```

##### Union Types
- ✅ Basic union parsing (first type used)
- ✅ String literal unions → `rich`
- ✅ Complex unions → `rich`

##### Intersection Types
- ✅ Intersection parsing (`T & U` → `rich`)
- ✅ Complex intersections → `rich`

##### Array Types
- ✅ `Type[]` syntax → `list`
- ✅ `Array<Type>` syntax → `list`
- ✅ Nested arrays supported

##### Generic Types
- ✅ Basic generic parsing
- ✅ Generic constraints (limited)
- ✅ Complex generics → `rich`

### Advanced Patterns

#### Interface Inheritance
```typescript
interface BaseEntity {
  id: number;
  createdAt: Date;
  updatedAt: Date;
}

interface User extends BaseEntity {
  email: string;
  name: string;
}

interface Admin extends User {
  permissions: string[];
}
```
- ✅ Single inheritance
- ✅ Multiple inheritance (limited)
- ✅ Deep inheritance chains

#### Method Filtering
```typescript
interface Service {
  id: number;
  name: string;

  // Methods are automatically ignored
  getData(): Promise<any>;
  processData(data: any): void;
  validate(): boolean;
}
```
- ✅ Automatic method detection and filtering
- ✅ Function type fields ignored
- ✅ Constructor functions ignored

#### Comment Handling
```typescript
interface Documented {
  // This field is important
  id: number;

  /* Multi-line
     comment */
  name: string;

  // @deprecated - This field will be removed
  legacyField?: string;
}
```
- ✅ Single-line comments ignored
- ✅ Multi-line comments ignored
- ✅ JSDoc comments ignored

## Limitations and Known Issues

### Parser Limitations

#### Regex-Based Parsing
- **No full TypeScript AST parsing** - Uses regex patterns for performance
- **Limited error recovery** - Malformed syntax may cause parsing failures
- **No semantic analysis** - Cannot resolve type aliases or imports

#### Type System Gaps
```typescript
// Limited support for advanced types
type DeepPartial<T> = {
  [P in keyof T]?: DeepPartial<T[P]>;
};

interface Advanced {
  // These may not parse correctly
  recursive: Advanced;
  conditional: T extends string ? string : number;
  template: `user_${string}`;
}
```

#### Import/Export Handling
```typescript
// Not currently supported
import { User } from './types';
export interface Post extends User { ... }

// Parser cannot resolve imported types
```

#### Advanced TypeScript Features
- ❌ **Decorators**: `@Component`, `@Injectable`, etc.
- ❌ **Namespaces**: `namespace MyNamespace { ... }`
- ❌ **Modules**: `module MyModule { ... }`
- ❌ **Conditional types**: `T extends U ? X : Y`
- ❌ **Template literal types**: `` `user_${string}` ``
- ❌ **Mapped types**: `{ [K in keyof T]: ... }`
- ❌ **Utility types**: `Partial<T>`, `Required<T>`, etc.
- ❌ **Type assertions**: `value as Type`
- ❌ **Non-null assertions**: `value!`

### Performance Considerations

#### File Size Limits
- Large files (>10MB) may impact parsing performance
- Consider splitting large interface files

#### Complex Type Expressions
```typescript
// This may impact performance
interface Complex {
  data: Record<string, {
    items: Array<{
      nested: {
        value: string | number | boolean
      }[]
    }>
  }>;
}
```

#### Memory Usage
- Parser loads entire files into memory
- Large projects may require significant RAM

## Usage Patterns

### Recommended Project Structure

```
src/
  types/
    entities/           # Core business entities
      user.ts
      post.ts
      comment.ts
    enums/             # Enum definitions
      status.ts
      role.ts
    api/               # API-related types
      requests.ts
      responses.ts
  components/          # React components (ignored)
  services/           # Service classes (ignored)
```

### Best Practices

#### Interface Design
```typescript
// ✅ Recommended patterns
interface User {
  id: number;              // Required ID field
  email: string;           // Required unique field
  name?: string;           // Optional field
  profile?: UserProfile;   // Reference to other entity
  posts: Post[];          // Array relationship
  createdAt: Date;        // Date/time field
  metadata?: any;         // Complex data
}

// ❌ Avoid these patterns
interface BadExample {
  // Methods (will be ignored)
  getFullName(): string;

  // Complex computed types
  displayName: this['firstName'] & this['lastName'];

  // Advanced TypeScript features
  settings: Partial<UserSettings>;
}
```

#### Naming Conventions
- Use PascalCase for interface names
- Use camelCase for field names
- Use `Id` suffix for foreign key fields
- Use plural names for array fields

#### Type Organization
```typescript
// Group related interfaces together
interface User { ... }
interface UserProfile { ... }
interface UserSettings { ... }

// Use clear inheritance
interface BaseEntity {
  id: number;
  createdAt: Date;
}

interface Post extends BaseEntity {
  title: string;
  content?: string;
}
```

### Integration with Prisma

#### TypeScript + Prisma Workflow
```typescript
// 1. Define Prisma schema
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  posts     Post[]
  profile   Profile?
}

// 2. Generate TypeScript types (optional)
interface User {
  id: number;
  email: string;
  name?: string;
  posts: Post[];
  profile?: Profile;
}

// 3. Use SpecQL parser on both
from src.parsers.typescript import TypeScriptParser, PrismaParser

ts_parser = TypeScriptParser()
prisma_parser = PrismaParser()

ts_entities = ts_parser.parse_file('types.ts')
prisma_entities = prisma_parser.parse_schema_file('schema.prisma')
```

## Error Handling

### Common Error Scenarios

#### Malformed Interfaces
```typescript
// This will cause parsing errors
interface Bad {
  id: number
  name: string  // Missing semicolon
  email: string;
}  // Missing closing brace
```

#### Complex Type Expressions
```typescript
// May not parse correctly
interface Complex {
  data: Record<string, any> & { extra: string };
  callback: (data: T) => Promise<T>;
}
```

### Debugging Tips

#### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

parser = TypeScriptParser()
entities = parser.parse_file('types.ts')  # Detailed logs
```

#### Validate Input Files
```bash
# Check TypeScript syntax
npx tsc --noEmit types.ts

# Use TypeScript compiler for validation
npx tsc --strict types.ts
```

#### Test Parsing Incrementally
```python
# Parse one interface at a time
parser = TypeScriptParser()

# Test with minimal interface
test_code = """
interface Test {
  id: number;
  name: string;
}
"""

entities = parser.parse_content(test_code)
print(f"Parsed: {entities}")
```

## Future Enhancements

### Planned Features
- **Full TypeScript AST parsing** - Replace regex with proper AST
- **Import resolution** - Handle imported types
- **Advanced type inference** - Better type mapping
- **Decorator support** - Parse TypeScript decorators
- **Utility type expansion** - Handle `Partial<T>`, `Required<T>`, etc.

### Performance Improvements
- **Streaming parsing** - Handle large files without full memory load
- **Parallel processing** - Parse multiple files concurrently
- **Incremental parsing** - Only re-parse changed files

### Extended Language Support
- **TypeScript 4.0+ features** - Template literal types, variadic tuples
- **JSX support** - Parse TSX files
- **Declaration files** - Parse `.d.ts` files

## API Reference

### TypeScriptParser Class

#### Constructor
```python
parser = TypeScriptParser()
```

#### Methods
```python
# Parse single file
entities = parser.parse_file(file_path: str) -> List[UniversalEntity]

# Parse content string
entities = parser.parse_content(content: str, source_file: str = "unknown") -> List[UniversalEntity]

# Parse project directory
entities = parser.parse_project(project_dir: str) -> List[UniversalEntity]
```

#### Type Mappings
```python
parser.type_mapping = {
    "string": FieldType.TEXT,
    "number": FieldType.INTEGER,
    "boolean": FieldType.BOOLEAN,
    "Date": FieldType.DATETIME,
    # ... custom mappings
}
```

## Troubleshooting

### Parser Fails Silently
- Check file encoding (must be UTF-8)
- Verify file permissions
- Ensure file is not empty

### Incorrect Type Mappings
- Review `type_mapping` dictionary
- Check for custom type definitions
- Verify TypeScript syntax

### Missing Entities
- Ensure interfaces have fields
- Check for syntax errors
- Verify file extensions (.ts, .tsx)

### Performance Issues
- Split large files
- Use `parse_project()` for batch processing
- Consider caching parsed results

---

*This reference covers the current implementation of the TypeScript parser. Features and limitations may change in future versions.*