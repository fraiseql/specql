# SeaORM Support

SpecQL reverse engineering supports SeaORM alongside Diesel.

## Supported Features

### Entity Detection
- `DeriveEntityModel` structs
- Field attributes (primary_key, unique, indexed, nullable)
- Relations (has_one, has_many, belongs_to)

### Query Detection
- Find operations (find, find_by_id)
- Insert operations
- Update operations (update, update_many)
- Delete operations (delete_by_id, delete_many)

## Example

### SeaORM Input
```rust
#[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
#[sea_orm(table_name = "contacts")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub email: String,
}

pub async fn create_contact(db: &DatabaseConnection, email: String) -> Result<Model, DbErr> {
    Contact::insert(ActiveModel {
        email: Set(email),
        ..Default::default()
    })
    .exec_with_returning(db)
    .await
}
```

### SpecQL Output
```yaml
entity: Contact
schema: crm
fields:
  email: text
actions:
  - name: create_contact
    steps:
      - insert: Contact
```

## Migration Guide

### From Diesel to SeaORM
```rust
# Diesel
diesel::table! {
    contacts (id) {
        id -> Integer,
        email -> Varchar,
    }
}

# SeaORM Equivalent
#[derive(DeriveEntityModel)]
#[sea_orm(table_name = "contacts")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub email: String,
}
```