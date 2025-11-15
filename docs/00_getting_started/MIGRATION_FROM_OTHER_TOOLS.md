# Migrating to SpecQL from Other Tools

**Switching to SpecQL?** This guide helps you migrate from popular tools like Prisma, JPA, Diesel, and raw SQL.

Each section shows equivalent SpecQL patterns and migration strategies.

## Migration Overview

### Why Migrate to SpecQL?

- **Single source of truth**: One YAML file generates all your backend code
- **Multi-language support**: Generate PostgreSQL, Java, Rust, TypeScript from one definition
- **Built-in business logic**: Actions compile to database functions
- **Type safety**: Generated code is fully typed
- **No ORM lock-in**: Generate raw SQL or use with any framework

### Migration Process

1. **Analyze existing schema** - Extract entities, relationships, business logic
2. **Create SpecQL YAML** - Define entities using SpecQL syntax
3. **Migrate data** - Export/import data between systems
4. **Update application code** - Use generated code instead of ORM
5. **Test thoroughly** - Verify all functionality works

---

## From Prisma → SpecQL

**Prisma** uses `schema.prisma` files. SpecQL uses YAML with similar concepts but different syntax.

### Schema Comparison

**Prisma**:
```prisma
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int
  published Boolean  @default(false)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

**SpecQL equivalent**:
```yaml
# entities/user.yaml
entity: User
schema: public
description: Application user

fields:
  email: text
  name: text
  created_at: timestamp
  updated_at: timestamp

indexes:
  - fields: [email]
    unique: true

# entities/post.yaml
entity: Post
schema: public
description: Blog post

fields:
  title: text
  content: text
  author_id: integer
  published: boolean
  created_at: timestamp
  updated_at: timestamp

relationships:
  - name: author
    entity: User
    type: many-to-one
    local_field: author_id
    foreign_field: pk_user

actions:
  - name: publish
    description: Publish a draft post
    steps:
      - validate: published = false
        error: "post_already_published"
      - update: Post SET published = true
```

### Key Differences

| Prisma | SpecQL | Notes |
|--------|--------|-------|
| `@id @default(autoincrement())` | Auto-generated `pk_*` field | Trinity pattern |
| `@unique` | `unique: true` in indexes | Same concept |
| `@default(now())` | Auto-generated timestamps | `created_at`, `updated_at` |
| `@relation(...)` | `relationships` section | More explicit |
| N/A | `actions` | Business logic in database |
| `@@map("table_name")` | `entity: Name` (becomes `tb_name`) | Automatic naming |

### Migration Steps

1. **Extract Prisma schema**:
   ```bash
   # Get current schema
   npx prisma db pull
   cat prisma/schema.prisma
   ```

2. **Convert to SpecQL YAML**:
   ```bash
   # Manual conversion (or use migration script)
   # See examples above
   ```

3. **Generate SpecQL code**:
   ```bash
   specql generate entities/user.yaml entities/post.yaml --output generated/
   ```

4. **Migrate data** (if needed):
   ```sql
   -- Export from Prisma
   pg_dump mydb > prisma_backup.sql

   -- Import to SpecQL schema
   psql newdb < generated/postgresql/public/01_tables.sql
   psql newdb < prisma_backup.sql
   ```

### Code Changes

**Prisma Client**:
```typescript
// Before
const user = await prisma.user.findUnique({
  where: { email: 'user@example.com' },
  include: { posts: true }
});

// After (with generated Prisma client)
import { PrismaClient } from './generated/prisma';

const prisma = new PrismaClient();
const user = await prisma.user.findUnique({
  where: { id: user.id },  // Use UUID instead of email
  include: { posts: true }
});
```

---

## From JPA/Hibernate → SpecQL

**JPA** uses Java annotations. SpecQL generates JPA entities automatically.

### Entity Comparison

**JPA Entity**:
```java
@Entity
@Table(name = "tb_user", schema = "crm")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "pk_user")
    private Long pkUser;

    @Column(name = "id", unique = true)
    private UUID id = UUID.randomUUID();

    @Column(name = "email", nullable = false)
    private String email;

    @Column(name = "name")
    private String name;

    @Column(name = "created_at")
    private Instant createdAt;

    @Column(name = "updated_at")
    private Instant updatedAt;

    // Getters and setters...
}
```

**SpecQL definition**:
```yaml
entity: User
schema: crm
description: CRM user

fields:
  email: text
  name: text
  created_at: timestamp
  updated_at: timestamp

indexes:
  - fields: [email]
    unique: true
```

### Key Differences

| JPA | SpecQL | Notes |
|-----|--------|-------|
| `@Entity @Table` | `entity: Name` | Automatic table naming |
| `@Id @GeneratedValue` | Auto `pk_*` field | Trinity pattern |
| `@Column` | Field definitions | Simpler syntax |
| `@OneToMany @ManyToOne` | `relationships` | Explicit relationships |
| Repository interfaces | Generated repositories | Auto-generated |
| Custom queries | `actions` | Database functions |
| Hibernate-specific | Pure JPA | Framework agnostic |

### Migration Steps

1. **Analyze existing entities**:
   ```bash
   # Find all JPA entities
   find src -name "*.java" -exec grep -l "@Entity" {} \;
   ```

2. **Extract field definitions**:
   - Look at `@Column` annotations
   - Note relationships (`@OneToMany`, `@ManyToOne`)
   - Extract validation rules

3. **Create SpecQL YAML**:
   ```yaml
   # Convert JPA entity to SpecQL
   entity: User
   fields:
     email: text  # From @Column private String email
     name: text   # From @Column private String name
   ```

4. **Generate new JPA code**:
   ```bash
   specql generate entities/user.yaml --target java --output src/main/java
   ```

### Code Changes

**Repository Pattern**:
```java
// Before (custom repository)
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    @Query("SELECT u FROM User u WHERE u.createdAt > :date")
    List<User> findRecentUsers(@Param("date") Instant date);
}

// After (generated repository)
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    // Generated methods available
    Optional<User> findById(UUID id);  // Uses UUID instead of Long

    // Custom business logic via database functions
    @Query(nativeQuery = true, value = "SELECT * FROM crm.fn_user_find_recent(:date)")
    List<User> findRecentUsers(@Param("date") Instant date);
}
```

---

## From Diesel → SpecQL

**Diesel** uses Rust macros. SpecQL generates Diesel models automatically.

### Model Comparison

**Diesel Model**:
```rust
use diesel::prelude::*;

#[derive(Queryable, Identifiable)]
#[diesel(table_name = tb_user)]
pub struct User {
    pub pk_user: i32,
    pub id: Uuid,
    pub email: String,
    pub name: Option<String>,
    pub created_at: NaiveDateTime,
    pub updated_at: NaiveDateTime,
}

#[derive(Insertable)]
#[diesel(table_name = tb_user)]
pub struct NewUser<'a> {
    pub id: Uuid,
    pub email: &'a str,
    pub name: Option<&'a str>,
}
```

**SpecQL definition**:
```yaml
entity: User
schema: public
description: Application user

fields:
  email: text
  name: text
  created_at: timestamp
  updated_at: timestamp

indexes:
  - fields: [email]
    unique: true
```

### Key Differences

| Diesel | SpecQL | Notes |
|--------|--------|-------|
| `#[derive(Queryable)]` | Auto-generated structs | Same concept |
| `table_name` attribute | `entity: Name` | Automatic naming |
| Manual schema definitions | Generated migrations | Less boilerplate |
| Custom queries | `actions` | Database functions |
| Type aliases | Built-in types | Simpler type system |

### Migration Steps

1. **Extract Diesel schemas**:
   ```bash
   # Find schema definitions
   find src -name "*.rs" -exec grep -l "table!" {} \;
   ```

2. **Convert to SpecQL YAML**:
   ```yaml
   # From Diesel table! macro to SpecQL
   entity: User
   fields:
     email: text     # From email -> Text
     name: text      # From name -> Nullable<Text>
   ```

3. **Generate Rust code**:
   ```bash
   specql generate entities/user.yaml --target rust --output src/models/
   ```

### Code Changes

**Query DSL**:
```rust
// Before (Diesel)
use diesel::prelude::*;

let results = tb_user::table
    .filter(tb_user::email.eq("user@example.com"))
    .load::<User>(&conn)?;

// After (generated Diesel code)
use generated::schema::tb_user;

let results = tb_user::table
    .filter(tb_user::id.eq(user_id))  // Uses UUID
    .load::<User>(&conn)?;
```

---

## From Raw SQL → SpecQL

**Raw SQL** requires manual schema management. SpecQL generates and manages everything.

### Schema Comparison

**Raw SQL**:
```sql
-- Manual table creation
CREATE SCHEMA crm;

CREATE TABLE crm.tb_contact (
    pk_contact SERIAL PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid(),
    identifier TEXT,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Manual indexes
CREATE UNIQUE INDEX idx_contact_email ON crm.tb_contact(email);
CREATE INDEX idx_contact_name ON crm.tb_contact(first_name, last_name);

-- Manual functions
CREATE OR REPLACE FUNCTION crm.fn_contact_create(
    p_email TEXT,
    p_first_name TEXT DEFAULT NULL,
    p_last_name TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO crm.tb_contact (email, first_name, last_name)
    VALUES (p_email, p_first_name, p_last_name)
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;
```

**SpecQL equivalent**:
```yaml
entity: Contact
schema: crm
description: CRM contact

fields:
  email: text
  first_name: text
  last_name: text
  created_at: timestamp
  updated_at: timestamp

indexes:
  - fields: [email]
    unique: true
  - fields: [first_name, last_name]

actions:
  - name: create
    description: Create a new contact
    parameters:
      - name: email
        type: text
        required: true
      - name: first_name
        type: text
      - name: last_name
        type: text
    steps:
      - insert: Contact SET email = :email, first_name = :first_name, last_name = :last_name
      - return: id
```

### Key Differences

| Raw SQL | SpecQL | Notes |
|---------|--------|-------|
| Manual CREATE TABLE | `entity:` definition | Declarative |
| Manual CREATE INDEX | `indexes:` section | Automatic optimization |
| Manual functions | `actions:` section | Compiled to functions |
| Manual migrations | Generated SQL | Version controlled |
| Manual relationships | `relationships:` | Explicit and validated |

### Migration Steps

1. **Analyze existing schema**:
   ```sql
   -- Extract current schema
   pg_dump --schema-only mydb > schema.sql
   ```

2. **Identify entities and relationships**:
   ```sql
   -- List all tables
   SELECT schemaname, tablename
   FROM pg_tables
   WHERE schemaname NOT IN ('pg_catalog', 'information_schema');

   -- List relationships
   SELECT conname, conrelid::regclass, confrelid::regclass
   FROM pg_constraint
   WHERE contype = 'f';
   ```

3. **Create SpecQL definitions**:
   ```yaml
   # Convert SQL table to SpecQL entity
   entity: Contact
   fields:
     email: text      # From email TEXT NOT NULL
     first_name: text # From first_name TEXT
   ```

4. **Migrate data**:
   ```bash
   # Generate SpecQL schema
   specql generate entities/contact.yaml --output migration/

   # Create new database
   createdb newdb

   # Apply SpecQL schema
   psql newdb < migration/postgresql/crm/01_tables.sql

   # Migrate data
   pg_dump olddb | psql newdb
   ```

### Code Changes

**Database Operations**:
```javascript
// Before (raw SQL)
const result = await pool.query(`
    SELECT * FROM crm.tb_contact
    WHERE email = $1
`, [email]);

// After (generated functions)
const contactId = await crm.fn_contact_create({
    email: 'user@example.com',
    first_name: 'John',
    last_name: 'Doe'
});

const contact = await crm.fn_contact_get_by_id(contactId);
```

---

## Common Migration Patterns

### Data Type Mapping

| SQL/JPA/Diesel | SpecQL |
|----------------|--------|
| VARCHAR(n) | `text` |
| INTEGER | `integer` |
| DECIMAL(p,s) | `decimal` |
| BOOLEAN | `boolean` |
| TIMESTAMP | `timestamp` |
| DATE | `date` |
| UUID | `uuid` |
| JSON/JSONB | `json` |
| ENUM | `enum(value1, value2)` |

### Relationship Conversion

**Foreign Keys**:
```sql
-- Raw SQL
ALTER TABLE tb_post ADD CONSTRAINT fk_post_author
    FOREIGN KEY (author_id) REFERENCES tb_user(pk_user);
```

```yaml
# SpecQL
entity: Post
relationships:
  - name: author
    entity: User
    type: many-to-one
    local_field: author_id
    foreign_field: pk_user
```

### Business Logic Migration

**Custom Functions**:
```sql
-- Raw SQL function
CREATE FUNCTION update_user_status(user_id UUID, new_status TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE tb_user SET status = new_status, updated_at = NOW()
    WHERE id = user_id;
END;
$$ LANGUAGE plpgsql;
```

```yaml
# SpecQL action
entity: User
actions:
  - name: update_status
    parameters:
      - name: new_status
        type: text
        required: true
    steps:
      - update: User SET status = :new_status
```

---

## Migration Checklist

### Pre-Migration
- [ ] Backup existing database
- [ ] Document current API contracts
- [ ] Identify performance-critical queries
- [ ] List all business logic functions

### During Migration
- [ ] Create SpecQL YAML definitions
- [ ] Generate code for all target languages
- [ ] Test generated code compilation
- [ ] Migrate data to new schema
- [ ] Update application code

### Post-Migration
- [ ] Run full test suite
- [ ] Performance test critical paths
- [ ] Update documentation
- [ ] Train team on new patterns

---

## Getting Help

Need help migrating a specific case?

- **Prisma migration**: Check the Prisma section above
- **JPA migration**: See the JPA/Hibernate section
- **Diesel migration**: Review the Rust/Diesel section
- **Raw SQL**: See the Raw SQL section

For complex migrations or custom cases, open an issue on [GitHub](https://github.com/fraiseql/specql/issues) with:
- Your current schema/tool
- What you're trying to migrate
- Any specific challenges

---

**Ready to migrate?** Start with a small entity to test the process, then scale up!