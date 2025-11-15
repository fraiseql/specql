# Reverse Engineering Tutorial

**Import existing code into SpecQL** - Convert databases and code to YAML definitions

This tutorial covers importing existing PostgreSQL databases, Python models, and other code into SpecQL YAML format.

## 🎯 What You'll Learn

- Import PostgreSQL schemas to YAML
- Import Python dataclasses to YAML
- Validate and refine imported entities
- Migrate existing applications to SpecQL

## 📋 Prerequisites

- [ ] Existing database or code to import
- [ ] SpecQL installed
- [ ] Access to source systems

## 🗄️ Step 1: PostgreSQL Database Import

Import an existing PostgreSQL database:

```bash
# Connect to your existing database
specql reverse postgresql \
  --host localhost \
  --database myapp \
  --user myuser \
  --schema public \
  --output entities/reverse/

# Or using connection string
specql reverse postgresql "postgresql://user:pass@localhost/myapp" \
  --schema public \
  --output entities/reverse/
```

**What gets imported:**
- Table structures → Entity fields
- Foreign keys → Relationships
- Indexes → Index definitions
- Enums → Enum field types
- Check constraints → Validation rules

## 🐍 Step 2: Python Model Import

Import Python dataclasses or Pydantic models:

```python
# existing_models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"

@dataclass
class User:
    username: str
    email: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None

@dataclass
class Post:
    title: str
    content: str
    author_id: int
    published: bool = False
    tags: List[str] = None
```

```bash
# Import Python models
specql reverse python existing_models.py --output entities/reverse/
```

## 🔍 Step 3: Review Generated YAML

Examine and refine the imported entities:

```yaml
# entities/reverse/user.yaml (generated)
entity: User
schema: public
description: "Imported from PostgreSQL table tb_user"

fields:
  username: text
  email: text
  role: enum(user, admin)  # From enum type
  created_at: timestamp
  last_login: timestamp    # Nullable field

indexes:
  - fields: [email]
    unique: true
  - fields: [username]
    unique: true

# Add business logic
actions:
  - name: update_role
    requires: caller.is_admin
    steps:
      - validate: role IN ('user', 'admin')
      - update: User SET role = :new_role
```

## 🧪 Step 4: Test Imported Schema

Verify the imported entities work correctly:

```bash
# Generate from imported YAML
specql generate entities/reverse/user.yaml --output test_reverse

# Create test database
createdb reverse_test

# Apply generated schema
psql reverse_test < test_reverse/public/01_tables.sql

# Compare with original
pg_dump original_db --schema-only | diff - generated_schema.sql
```

## 🔄 Step 5: Migration Strategy

Plan your migration from existing system to SpecQL:

### Phase 1: Parallel Operation
- Keep existing system running
- Generate SpecQL schema in parallel
- Test data migration scripts

### Phase 2: Data Migration
```sql
-- Export from old system
pg_dump old_db > old_data.sql

-- Import to new SpecQL schema
psql new_db < old_data.sql

-- Transform data if needed
UPDATE new_tb_user SET role = 'user' WHERE role IS NULL;
```

### Phase 3: Application Migration
```python
# Old code
user = User.query.get(user_id)

# New SpecQL code
user_result = db.execute("SELECT * FROM app.fn_user_get(?)", user_id)
user = user_result.fetchone()
```

## 🎯 Step 6: Best Practices

### Data Integrity
- Always backup before migration
- Test migrations on copy of production data
- Validate data integrity after migration

### Incremental Migration
- Start with least critical entities
- Migrate one feature at a time
- Keep old and new systems in sync during transition

### Validation
```yaml
# Add validation to imported entities
actions:
  - name: validate_import
    steps:
      - validate: email MATCHES "^[^@]+@[^@]+\\.[^@]+$"
      - validate: created_at <= NOW()
      - validate: role IN ('user', 'admin', 'moderator')
```

## 🔄 Next Steps

- **[Migration Guide](../00_getting_started/MIGRATION_FROM_OTHER_TOOLS.md)** - Complete migration strategies
- **[CRM Example](../06_examples/CRM_SYSTEM_COMPLETE.md)** - Real migration case study

## 🆘 Common Issues

**Import fails with permissions?**
- Ensure database user has SELECT on system catalogs
- Grant SELECT on pg_class, pg_namespace, pg_attribute

**Relationships not detected?**
- Foreign keys must be properly defined
- Check constraint names follow conventions

**Data type mismatches?**
- Review generated YAML for correct field types
- Adjust as needed for your use case

---

**Success!** You can now import existing systems into SpecQL and modernize your data layer.