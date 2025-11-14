# Fields Guide

**Define your data structure** - Complete field type reference for SpecQL entities

Fields define the data structure of your entities. SpecQL supports a comprehensive set of field types for different data requirements.

## 🎯 Field Definition

Fields are defined in the `fields` section of your entity:

```yaml
entity: Contact
schema: crm

fields:
  email: text                    # Simple type
  status: enum(lead, qualified)  # Enum with values
  company: ref(Company)          # Reference to another entity
  metadata: jsonb               # Complex type
```

## 📋 Basic Types

### Text and Strings
```yaml
fields:
  name: text           # VARCHAR, unlimited length
  email: text          # Standard text field
  description: text    # Long text content
  code: text           # Short codes or identifiers
```

**Generated SQL**: `TEXT`

### Numbers
```yaml
fields:
  age: integer         # INTEGER (-2^31 to 2^31-1)
  count: integer       # Whole numbers
  year: integer        # Year values
  quantity: integer    # Quantities
```

**Generated SQL**: `INTEGER`

```yaml
fields:
  price: decimal       # DECIMAL for money (avoid for calculations)
  weight: decimal      # Precise decimal values
  percentage: decimal  # Percentage values
```

**Generated SQL**: `DECIMAL`

### Boolean
```yaml
fields:
  active: boolean      # TRUE/FALSE values
  enabled: boolean     # Feature flags
  verified: boolean    # Verification status
```

**Generated SQL**: `BOOLEAN`

### Dates and Times
```yaml
fields:
  birthday: date       # Date only (YYYY-MM-DD)
  created: timestamp   # Full timestamp with timezone
  start_time: time     # Time only (HH:MM:SS)
```

**Generated SQL**:
- `date`: `DATE`
- `timestamp`: `TIMESTAMPTZ` (with timezone)
- `time`: `TIME`

### Identifiers
```yaml
fields:
  user_id: uuid        # Universally unique identifier
  external_id: uuid    # External system references
```

**Generated SQL**: `UUID`

### JSON Data
```yaml
fields:
  settings: jsonb      # JSON data with indexing
  metadata: jsonb      # Flexible key-value data
  preferences: jsonb   # User preferences
```

**Generated SQL**: `JSONB`

## 🔧 Scalar Rich Types

SpecQL provides specialized types for common business needs:

### Contact Information
```yaml
fields:
  email: email         # Email validation
  website: url         # URL validation
  phone: phone         # Phone number format
```

**Validation**: Automatic format checking
**Storage**: TEXT with constraints

### Financial
```yaml
fields:
  amount: money        # Currency amount with precision
  discount: percentage # Percentage (0-100)
```

**Money**: Stores amount and currency
**Percentage**: Validates 0-100 range

### Physical Measurements
```yaml
fields:
  size: dimensions     # Width × Height × Depth
  weight: weight       # Weight with units
  capacity: volume     # Volume with units
```

**Dimensions**: JSONB with width, height, depth
**Weight/Volume**: JSONB with value and unit

## 🏗️ Composite Types

### Address
```yaml
fields:
  address: address     # Complete address structure
```

**Structure**:
```json
{
  "street": "123 Main St",
  "city": "Anytown",
  "state": "CA",
  "zip": "12345",
  "country": "USA"
}
```

### Contact Info
```yaml
fields:
  contact: contact_info # Multiple contact methods
```

**Structure**:
```json
{
  "email": "user@example.com",
  "phone": "+1-555-0123",
  "fax": "+1-555-0124",
  "mobile": "+1-555-0125"
}
```

### Geographic
```yaml
fields:
  location: geo_location # Latitude/longitude/altitude
```

**Structure**:
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "altitude": 100.5
}
```

### Money with Currency
```yaml
fields:
  price: money_amount  # Amount + currency
```

**Structure**:
```json
{
  "amount": 99.99,
  "currency": "USD"
}
```

## 🔗 Reference Types

### Entity References
```yaml
fields:
  company: ref(Company)     # Reference to Company entity
  manager: ref(User)        # Reference to User entity
  category: ref(Category)   # Reference to Category entity
```

**Generated SQL**:
```sql
fk_company INTEGER REFERENCES crm.tb_company(pk_company)
```

**Benefits**:
- Automatic foreign key constraints
- Type-safe JOINs in queries
- Cascade options available

## 📊 List Types

### Arrays
```yaml
fields:
  tags: text[]              # Array of text values
  categories: text[]        # Multiple categories
  skills: text[]           # Multiple skills
```

**Generated SQL**: `TEXT[]`

### Reference Lists
```yaml
fields:
  projects: ref(Project)[]  # Multiple project references
```

**Implementation**: Junction table created automatically

## 🎯 Enum Types

### Simple Enums
```yaml
fields:
  status: enum(lead, qualified, customer)
  priority: enum(low, medium, high)
  type: enum(internal, external)
```

**Generated SQL**:
```sql
status TEXT CHECK (status IN ('lead', 'qualified', 'customer'))
```

### Best Practices
- Use lowercase enum values
- Keep enums small (≤10 values)
- Consider separate reference tables for large sets

## 🔍 Field Options

### Constraints
```yaml
fields:
  email: text
    unique: true           # UNIQUE constraint
    nullable: false        # NOT NULL constraint
    default: ""           # Default value
```

### Indexing
```yaml
fields:
  status: enum(active, inactive)
    index: true           # Create index
  email: text
    index: unique        # Unique index
```

### Validation
```yaml
fields:
  age: integer
    min: 0               # Minimum value
    max: 150             # Maximum value
  email: text
    pattern: "^[^@]+@[^@]+\\.[^@]+$"
```

## 🏗️ Advanced Field Patterns

### Identifiers
```yaml
fields:
  # Automatic identifier generation
  identifier: text
    generated: pattern   # Uses identifier patterns
    pattern: "CONT-{YYYY}-{NNN}"
```

### Computed Fields
```yaml
fields:
  # Virtual fields computed from other fields
  full_name: text
    computed: "first_name || ' ' || last_name"
```

### Conditional Fields
```yaml
fields:
  # Fields that appear based on other field values
  spouse_name: text
    conditional: "marital_status = 'married'"
```

## 📈 Field Evolution

Fields can be added safely to existing entities:

```yaml
entity: Contact
schema: crm

fields:
  # Original fields
  email: text
  first_name: text

  # Added later (safe)
  last_name: text
  phone: text
  status: enum(lead, qualified, customer)
```

**Migration Safety**: New fields are added as nullable by default.

## 🎯 Best Practices

### Type Selection
- Use specific types over generic ones
- Prefer `text` over `varchar(n)` for flexibility
- Use `decimal` only when precision matters
- Consider `jsonb` for flexible schemas

### Naming Conventions
- Use snake_case for field names
- Be descriptive but concise
- Use consistent prefixes for related fields
- Avoid reserved SQL keywords

### Validation Strategy
- Validate at the field level when possible
- Use action-level validation for business rules
- Provide clear error messages
- Consider user experience impact

### Performance Considerations
- Index frequently queried fields
- Consider field size for large datasets
- Use appropriate types for sorting/filtering
- Plan for future growth

## 🔍 Common Field Patterns

### User Management
```yaml
fields:
  username: text
    unique: true
  email: email
  password_hash: text
  role: enum(admin, user, guest)
  active: boolean
    default: true
```

### E-commerce
```yaml
fields:
  sku: text
    unique: true
  name: text
  price: money_amount
  inventory: integer
    min: 0
  category: ref(Category)
```

### Content Management
```yaml
fields:
  title: text
  slug: text
    unique: true
  content: text
  published: boolean
    default: false
  published_at: timestamp
```

## 🚀 Next Steps

- **[Relationships Guide](relationships.md)** - Connect entities with references
- **[Actions Guide](../actions/overview.md)** - Add business logic
- **[Validation Guide](../actions/validation.md)** - Field and business validation
- **[YAML Reference](../../03_reference/yaml/field_types.md)** - Complete type reference

## 📚 Related Topics

- **[Rich Types Guide](rich_types.md)** - Advanced type usage
- **[Constraints Guide](constraints.md)** - Database constraints
- **[Trinity Pattern Guide](trinity_pattern.md)** - Data access patterns