# Rust ORM Support

SpecQL reverse engineering supports both Diesel and SeaORM for Rust database operations.

## Supported ORMs

### 1. Diesel ORM
**Detection Pattern**: `diesel::table!` macros and `Queryable` derives
**Features**:
- Table macro parsing (`table! { ... }`)
- Derive macro detection (`#[derive(Queryable)]`, `#[derive(Insertable)]`)
- Association detection (`#[belongs_to(...)]`)
- Schema inference from table macros

**Example**:
```rust
table! {
    contacts (id) {
        id -> Integer,
        email -> Varchar,
        created_at -> Timestamp,
    }
}

#[derive(Queryable, Identifiable)]
#[belongs_to(User)]
pub struct Contact {
    pub id: i32,
    pub email: String,
    pub user_id: i32,
    pub created_at: NaiveDateTime,
}
```

### 2. SeaORM
**Detection Pattern**: `DeriveEntityModel` and SeaORM imports
**Features**:
- Entity model detection (`#[derive(DeriveEntityModel)]`)
- Field attribute parsing (`#[sea_orm(primary_key)]`, `#[sea_orm(unique)]`)
- Relation detection (`#[sea_orm(has_many = "...")]`)
- CRUD operation detection (find, insert, update, delete)

**Example**:
```rust
#[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
#[sea_orm(table_name = "contacts")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,

    #[sea_orm(unique)]
    pub email: String,

    pub created_at: DateTime,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {
    #[sea_orm(has_many = "super::companies::Entity")]
    Companies,
}
```

## ORM Detection

The parser automatically detects which ORM is being used:

- **Diesel**: `use diesel::` or `diesel::table!` macros
- **SeaORM**: `use sea_orm::` or `DeriveEntityModel` derives
- **Both**: Code using both ORMs is supported
- **Unknown**: Falls back to trying both parsers

## Entity Conversion

Both ORMs are converted to SpecQL entities:

```yaml
# From Diesel table! macro
entity: Contact
schema: public
table: contacts
fields:
  id: integer
  email: text
  user_id: integer

# From SeaORM DeriveEntityModel
entity: Contact
schema: crm
table: contacts
fields:
  id: integer
  email: text
  created_at: timestamp
```

## Type Mapping

### Diesel Types → SpecQL Types
- `Integer` → `integer`
- `BigInt` → `bigint`
- `Text`/`Varchar` → `text`
- `Bool` → `boolean`
- `Timestamp` → `timestamp`
- `Nullable<T>` → nullable field

### SeaORM Types → SpecQL Types
- `i32` → `integer`
- `i64` → `bigint`
- `String` → `text`
- `bool` → `boolean`
- `DateTime` → `timestamp`
- `Option<T>` → nullable field

## Migration Guide

### Diesel to SeaORM
```rust
// Diesel
table! {
    contacts (id) {
        id -> Integer,
        email -> Varchar,
    }
}

#[derive(Queryable)]
pub struct Contact {
    pub id: i32,
    pub email: String,
}

// SeaORM Equivalent
#[derive(DeriveEntityModel)]
#[sea_orm(table_name = "contacts")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub email: String,
}
```

### SeaORM to Diesel
```rust
// SeaORM
#[derive(DeriveEntityModel)]
#[sea_orm(table_name = "contacts")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub email: String,
}

// Diesel Equivalent
table! {
    contacts (id) {
        id -> Integer,
        email -> Text,
    }
}

#[derive(Queryable)]
pub struct Contact {
    pub id: i32,
    pub email: String,
}
```

## Testing

Run ORM tests with:
```bash
# SeaORM parser tests
uv run pytest tests/unit/reverse_engineering/test_seaorm_parser.py -v

# Integration tests
uv run pytest tests/integration/reverse_engineering/test_seaorm_integration.py -v
```

## Limitations

- Complex query expressions may not be fully parsed
- Custom derive macros beyond the standard ORM derives are not analyzed
- Runtime query building is not supported (only static schema definitions)
- Migration files are not parsed (only entity/model definitions)