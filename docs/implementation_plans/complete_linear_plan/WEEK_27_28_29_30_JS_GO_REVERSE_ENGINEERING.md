# Weeks 27-30: JavaScript/TypeScript & Go Reverse Engineering

**Date**: 2025-11-13
**Duration**: 20 days (4 weeks)
**Status**: 🔴 Planning

---

## Week 27-28: JavaScript/TypeScript Reverse Engineering

**Objective**: Reverse engineer TypeScript/Prisma/TypeORM applications to SpecQL

### Languages & ORMs Supported
- **TypeScript/JavaScript**
- **Prisma** schema → SpecQL
- **TypeORM** decorators → SpecQL  
- **Sequelize** models → SpecQL
- **Mongoose** (MongoDB) → SpecQL patterns

### Week 27: Core Parser & Prisma

**Day 1**: TypeScript AST Parser
```typescript
// Input: Prisma schema
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String
  posts     Post[]
  profile   Profile?
  createdAt DateTime @default(now())
}

model Post {
  id        Int     @id @default(autoincrement())
  title     String
  content   String?
  published Boolean @default(false)
  author    User    @relation(fields: [authorId], references: [id])
  authorId  Int
}
```

**Output: SpecQL YAML**
```yaml
entities:
  - entity: User
    fields:
      email: text! {unique: true}
      name: text!
      created_at: timestamp

  - entity: Post
    fields:
      title: text!
      content: text
      published: boolean
      author: ref(User)!
```

**Implementation**:
- Parser: `src/reverse_engineering/typescript/prisma_parser.py`
- Uses `@prisma/internals` or regex parsing
- Detects models, fields, relationships
- Maps Prisma types to SpecQL types

**Day 2**: TypeORM Decorator Detection
```typescript
// Input: TypeORM entity
@Entity('users')
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @Column()
  name: string;

  @ManyToOne(() => Organization)
  organization: Organization;

  @OneToMany(() => Post, post => post.author)
  posts: Post[];

  @CreateDateColumn()
  createdAt: Date;
}
```

**Converter**: `src/reverse_engineering/typescript/typeorm_converter.py`
- Parse TypeScript AST (using ts-morph or babel)
- Detect decorators (@Entity, @Column, @ManyToOne, etc.)
- Map to SpecQL entities

**Day 3**: Sequelize Models
```javascript
// Input: Sequelize model
const User = sequelize.define('User', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  email: {
    type: DataTypes.STRING,
    unique: true,
    allowNull: false
  },
  name: {
    type: DataTypes.STRING,
    allowNull: false
  }
});

User.belongsTo(Organization);
User.hasMany(Post);
```

**Converter**: `src/reverse_engineering/typescript/sequelize_converter.py`

**Day 4-5**: GraphQL Schema Integration
- Detect GraphQL type definitions
- Map GraphQL types to SpecQL entities
- Extract resolvers → SpecQL actions

### Week 28: Advanced Patterns

**Day 1-2**: Express/Fastify Route Handlers
```typescript
// Express routes → SpecQL actions
app.post('/users', async (req, res) => {
  const user = await prisma.user.create({
    data: req.body
  });
  res.json(user);
});

// Converts to:
# SpecQL action
- name: create_user
  steps:
    - insert: User
```

**Day 3-4**: Next.js/tRPC Patterns
- API routes → actions
- Server actions → mutations
- tRPC procedures → typed actions

**Day 5**: Testing & CLI
```bash
specql reverse typescript src/
specql reverse prisma prisma/schema.prisma
specql reverse typeorm src/entities/
```

---

## Week 29-30: Go Reverse Engineering

**Objective**: Reverse engineer Go/GORM/sqlx applications to SpecQL

### ORMs & Libraries Supported
- **GORM** - Most popular Go ORM
- **sqlx** - SQL extensions
- **sqlc** - Generate type-safe Go from SQL
- **ent** - Entity framework by Facebook

### Week 29: Core Parser & GORM

**Day 1**: Go AST Parser
```go
// Input: GORM model
type User struct {
    gorm.Model
    Email        string `gorm:"uniqueIndex;not null"`
    Name         string `gorm:"not null"`
    OrganizationID uint
    Organization Organization `gorm:"foreignKey:OrganizationID"`
    Posts        []Post       `gorm:"foreignKey:AuthorID"`
    Role         string       `gorm:"type:varchar(50);not null"`
}
```

**Output**: SpecQL entity
```yaml
entity: User
fields:
  email: text! {unique: true}
  name: text!
  organization: ref(Organization)
  role: text!
```

**Implementation**:
- Parser: `src/reverse_engineering/go/go_parser.py`
- Uses Go AST parsing (via subprocess calling `go/ast`)
- Detects struct tags (gorm, json, db)
- Maps Go types to SpecQL types

**Day 2**: GORM Struct Tag Parsing
```go
// Supported tags:
`gorm:"primaryKey"`
`gorm:"uniqueIndex"`
`gorm:"not null"`
`gorm:"foreignKey:OrgID"`
`gorm:"many2many:user_roles"`
`gorm:"type:text"`
`gorm:"default:true"`
```

**Converter**: `src/reverse_engineering/go/gorm_converter.py`

**Day 3**: sqlx Query Detection
```go
// Input: sqlx queries
type User struct {
    ID    int64  `db:"id"`
    Email string `db:"email"`
    Name  string `db:"name"`
}

// Query detection
users := []User{}
db.Select(&users, "SELECT * FROM users WHERE organization_id = $1", orgID)
```

**Pattern Detector**: `src/reverse_engineering/go/sqlx_detector.py`

**Day 4-5**: sqlc Integration
```sql
-- Input: sqlc queries (queries.sql)
-- name: GetUser :one
SELECT * FROM users WHERE id = $1 LIMIT 1;

-- name: ListUsers :many
SELECT * FROM users WHERE organization_id = $1;

-- name: CreateUser :one
INSERT INTO users (email, name, organization_id)
VALUES ($1, $2, $3)
RETURNING *;
```

**Converter**: Parse sqlc YAML config + queries → SpecQL

### Week 30: Advanced Patterns

**Day 1-2**: Gin/Echo/Fiber Handlers
```go
// Gin handlers → SpecQL actions
func CreateUser(c *gin.Context) {
    var user User
    c.BindJSON(&user)
    db.Create(&user)
    c.JSON(200, user)
}

// Converts to SpecQL action
```

**Day 3**: gRPC Service Detection
```protobuf
// Input: Protocol Buffer definitions
service UserService {
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc GetUser(GetUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
}
```

**Converter**: protobuf → SpecQL actions

**Day 4**: Complete Project Analyzer
```bash
# Scan Go project
specql reverse go .
specql reverse gorm models/
specql reverse sqlc sqlc.yaml
```

**Day 5**: Testing & Polish
- Integration tests
- Documentation
- Example projects

---

## Type Mapping Tables

### TypeScript/Prisma → SpecQL
| Prisma Type | SpecQL Type |
|-------------|-------------|
| String      | text        |
| Int         | integer     |
| BigInt      | integer     |
| Float       | decimal     |
| Boolean     | boolean     |
| DateTime    | timestamp   |
| Json        | json        |
| Bytes       | bytea       |

### Go/GORM → SpecQL
| Go Type       | SpecQL Type |
|---------------|-------------|
| string        | text        |
| int, int64    | integer     |
| float64       | decimal     |
| bool          | boolean     |
| time.Time     | timestamp   |
| sql.NullString| text        |
| []byte        | bytea       |
| interface{}   | json        |

---

## Success Metrics

### JavaScript/TypeScript
- [ ] Parse 95%+ Prisma schemas
- [ ] TypeORM decorator detection 90%+
- [ ] Sequelize model conversion accurate
- [ ] GraphQL schema mapping correct
- [ ] Express/Next.js route conversion working

### Go
- [ ] Parse 95%+ GORM models
- [ ] Struct tag detection accurate
- [ ] sqlx query patterns recognized
- [ ] sqlc integration working
- [ ] Gin/Echo handler conversion correct

---

## CLI Commands

```bash
# JavaScript/TypeScript
specql reverse typescript src/
specql reverse prisma prisma/schema.prisma
specql reverse typeorm src/entities/
specql reverse sequelize src/models/
specql reverse graphql schema.graphql

# Go
specql reverse go .
specql reverse gorm models/
specql reverse sqlx .
specql reverse sqlc sqlc.yaml

# With output
specql reverse typescript src/ --output project.specql.yaml
specql reverse go . --output project.specql.yaml
```

---

**Status**: 🔴 Ready to Execute
**Expected Output**: Complete JS/TS and Go reverse engineering capabilities
