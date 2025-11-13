# Weeks 31-38: Multi-Language Code Generation

**Date**: 2025-11-13
**Duration**: 40 days (8 weeks)
**Status**: 🔴 Planning
**Objective**: Generate idiomatic code in Java, Rust, JavaScript/TypeScript, and Go from SpecQL

---

## 🎯 Overview

**Universal Pattern**: SpecQL YAML → Language-Specific Code

```
SpecQL Universal Format (YAML)
         ↓
    [Generator]
         ↓
┌────────┬────────┬────────┬────────┐
│  Java  │  Rust  │  JS/TS │   Go   │
├────────┼────────┼────────┼────────┤
│ JPA    │ Diesel │ Prisma │  GORM  │
│ Spring │ SeaORM │TypeORM │  sqlc  │
│ Hibernate│     │Sequelize│  sqlx  │
└────────┴────────┴────────┴────────┘
```

---

## Week 31-32: Java Output Generation

**Objective**: Generate Spring Boot + JPA/Hibernate code from SpecQL

### Output Targets
1. **JPA Entities** with annotations
2. **Spring Data Repositories**
3. **REST Controllers** (Spring MVC)
4. **Service Layer** classes
5. **DTOs** and Mappers
6. **Configuration** files

### Week 31: Entity & Repository Generation

**Day 1**: JPA Entity Generator

**Input**: SpecQL YAML
```yaml
entity: User
fields:
  email: text! {unique: true}
  name: text!
  organization: ref(Organization)
  role: enum(admin, user, viewer)
  created_at: timestamp
```

**Output**: `User.java`
```java
package com.example.entity;

import javax.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 255)
    private String email;

    @Column(nullable = false)
    private String name;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "organization_id", nullable = false)
    private Organization organization;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private UserRole role;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    // ... rest of getters/setters
}
```

**Enum**: `UserRole.java`
```java
package com.example.entity;

public enum UserRole {
    ADMIN,
    USER,
    VIEWER
}
```

**Generator**: `src/generators/java/jpa_entity_generator.py`

```python
from jinja2 import Environment, FileSystemLoader
from src.core.specql_parser import Entity, Field

class JPAEntityGenerator:
    def generate(self, entity: Entity) -> str:
        """Generate JPA entity class"""
        template = self.env.get_template("java/entity.java.j2")
        return template.render(
            entity=entity,
            package="com.example.entity",
            fields=self._convert_fields(entity.fields)
        )
    
    def _convert_fields(self, fields):
        """Convert SpecQL fields to Java fields"""
        java_fields = []
        for field in fields:
            java_fields.append({
                'name': self._to_camel_case(field.name),
                'type': self._map_type(field.field_type),
                'column_name': field.name,
                'nullable': not field.required,
                'unique': field.unique if hasattr(field, 'unique') else False,
                'annotations': self._get_annotations(field)
            })
        return java_fields
```

**Day 2**: Spring Data Repository Generator

**Output**: `UserRepository.java`
```java
package com.example.repository;

import com.example.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    
    List<User> findByOrganizationId(Long organizationId);
    
    @Query("SELECT u FROM User u WHERE u.role = :role")
    List<User> findByRole(@Param("role") UserRole role);
    
    boolean existsByEmail(String email);
}
```

**Day 3**: REST Controller Generator

**Output**: `UserController.java`
```java
package com.example.controller;

import com.example.dto.UserDTO;
import com.example.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping
    public ResponseEntity<List<UserDTO>> listUsers() {
        return ResponseEntity.ok(userService.findAll());
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<UserDTO> getUser(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
    
    @PostMapping
    public ResponseEntity<UserDTO> createUser(@Valid @RequestBody UserDTO dto) {
        UserDTO created = userService.create(dto);
        return ResponseEntity.ok(created);
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<UserDTO> updateUser(
        @PathVariable Long id,
        @Valid @RequestBody UserDTO dto
    ) {
        return userService.update(id, dto)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        userService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

**Day 4-5**: Service Layer & DTOs
- Service classes with business logic
- DTO classes for API responses
- MapStruct mappers for entity ↔ DTO conversion

### Week 32: Advanced Features

**Day 1-2**: Action → Spring Service Methods
```yaml
# SpecQL action
- name: assign_task
  parameters:
    task_id: uuid
    user_id: uuid
  steps:
    - validate: task.status != 'completed'
    - update: Task SET assignee_id = :user_id
    - notify: user "You have been assigned task {task.title}"
```

**Output**: Service method
```java
@Service
public class TaskService {
    @Transactional
    public TaskDTO assignTask(UUID taskId, UUID userId) {
        Task task = taskRepository.findById(taskId)
            .orElseThrow(() -> new NotFoundException("Task not found"));
        
        if (task.getStatus() == TaskStatus.COMPLETED) {
            throw new ValidationException("Cannot assign completed task");
        }
        
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new NotFoundException("User not found"));
        
        task.setAssignee(user);
        task = taskRepository.save(task);
        
        notificationService.notify(user, 
            "You have been assigned task " + task.getTitle());
        
        return taskMapper.toDTO(task);
    }
}
```

**Day 3-4**: Configuration & Build Files
- `application.properties` / `application.yml`
- `pom.xml` (Maven) or `build.gradle` (Gradle)
- Dockerfile
- Database migration scripts (Flyway/Liquibase)

**Day 5**: Testing & Documentation
- Integration tests
- Example projects
- Documentation

---

## Week 33-34: Rust Output Generation

**Objective**: Generate Rust/Diesel/SeaORM code from SpecQL

### Output Targets
1. **Diesel schema** and models
2. **SeaORM entities**
3. **Actix-web/Axum** handlers
4. **Service layer** functions
5. **DTOs** and serialization

### Week 33: Schema & Model Generation

**Day 1**: Diesel Schema Generator

**Output**: `schema.rs`
```rust
// Generated by SpecQL
table! {
    users (id) {
        id -> Int8,
        email -> Varchar,
        name -> Varchar,
        organization_id -> Int8,
        role -> Varchar,
        created_at -> Timestamp,
    }
}

table! {
    organizations (id) {
        id -> Int8,
        name -> Varchar,
        created_at -> Timestamp,
    }
}

joinable!(users -> organizations (organization_id));
allow_tables_to_appear_in_same_query!(users, organizations);
```

**Model**: `models.rs`
```rust
use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use chrono::NaiveDateTime;

#[derive(Queryable, Identifiable, Serialize, Deserialize)]
#[table_name = "users"]
pub struct User {
    pub id: i64,
    pub email: String,
    pub name: String,
    pub organization_id: i64,
    pub role: String,
    pub created_at: NaiveDateTime,
}

#[derive(Insertable, AsChangeset, Deserialize)]
#[table_name = "users"]
pub struct NewUser {
    pub email: String,
    pub name: String,
    pub organization_id: i64,
    pub role: String,
}
```

**Day 2**: SeaORM Entity Generator

**Output**: `user.rs`
```rust
use sea_orm::entity::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, DeriveEntityModel, Serialize, Deserialize)]
#[sea_orm(table_name = "users")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i64,
    
    #[sea_orm(unique)]
    pub email: String,
    
    pub name: String,
    
    pub organization_id: i64,
    
    pub role: String,
    
    pub created_at: DateTimeUtc,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {
    #[sea_orm(
        belongs_to = "super::organization::Entity",
        from = "Column::OrganizationId",
        to = "super::organization::Column::Id"
    )]
    Organization,
}

impl ActiveModelBehavior for ActiveModel {}
```

**Day 3**: Actix-web Handler Generator

**Output**: `handlers/user.rs`
```rust
use actix_web::{web, HttpResponse, Result};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct CreateUserRequest {
    pub email: String,
    pub name: String,
    pub organization_id: i64,
}

#[derive(Serialize)]
pub struct UserResponse {
    pub id: i64,
    pub email: String,
    pub name: String,
    pub organization_id: i64,
    pub role: String,
}

pub async fn list_users(
    pool: web::Data<DbPool>,
) -> Result<HttpResponse> {
    let conn = pool.get().unwrap();
    
    let users = web::block(move || {
        users::table
            .load::<User>(&conn)
    })
    .await
    .unwrap();
    
    Ok(HttpResponse::Ok().json(users))
}

pub async fn create_user(
    pool: web::Data<DbPool>,
    form: web::Json<CreateUserRequest>,
) -> Result<HttpResponse> {
    let conn = pool.get().unwrap();
    
    let new_user = NewUser {
        email: form.email.clone(),
        name: form.name.clone(),
        organization_id: form.organization_id,
        role: "user".to_string(),
    };
    
    let user = web::block(move || {
        diesel::insert_into(users::table)
            .values(&new_user)
            .get_result::<User>(&conn)
    })
    .await
    .unwrap();
    
    Ok(HttpResponse::Created().json(user))
}
```

**Days 4-5**: Repository pattern, error handling, tests

### Week 34: Advanced Features & Polish
- Async Rust patterns
- Error handling with `Result<T, E>`
- Cargo.toml configuration
- Testing framework setup

---

## Week 35-36: JavaScript/TypeScript Output Generation

**Objective**: Generate TypeScript/Prisma/TypeORM code from SpecQL

### Output Targets
1. **Prisma schema**
2. **TypeORM entities**
3. **tRPC/Express routes**
4. **GraphQL resolvers**
5. **Zod schemas** for validation

### Week 35: Schema & Model Generation

**Day 1**: Prisma Schema Generator

**Output**: `schema.prisma`
```prisma
// Generated by SpecQL

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model User {
  id             Int          @id @default(autoincrement())
  email          String       @unique
  name           String
  organizationId Int          @map("organization_id")
  organization   Organization @relation(fields: [organizationId], references: [id])
  role           String
  createdAt      DateTime     @default(now()) @map("created_at")
  posts          Post[]

  @@map("users")
}

model Organization {
  id        Int      @id @default(autoincrement())
  name      String
  users     User[]
  createdAt DateTime @default(now()) @map("created_at")

  @@map("organizations")
}
```

**Day 2**: TypeORM Entity Generator

**Output**: `User.entity.ts`
```typescript
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  OneToMany,
  CreateDateColumn,
  JoinColumn,
} from 'typeorm';
import { Organization } from './Organization.entity';
import { Post } from './Post.entity';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true, nullable: false })
  email: string;

  @Column({ nullable: false })
  name: string;

  @ManyToOne(() => Organization, (org) => org.users)
  @JoinColumn({ name: 'organization_id' })
  organization: Organization;

  @Column({ type: 'varchar', length: 50, nullable: false })
  role: string;

  @OneToMany(() => Post, (post) => post.author)
  posts: Post[];

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;
}
```

**Day 3**: tRPC Router Generator

**Output**: `user.router.ts`
```typescript
import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '../trpc';
import { prisma } from '../lib/prisma';

export const userRouter = router({
  list: publicProcedure.query(async () => {
    return await prisma.user.findMany({
      include: {
        organization: true,
      },
    });
  }),

  get: publicProcedure
    .input(z.object({ id: z.number() }))
    .query(async ({ input }) => {
      return await prisma.user.findUnique({
        where: { id: input.id },
        include: { organization: true },
      });
    }),

  create: protectedProcedure
    .input(
      z.object({
        email: z.string().email(),
        name: z.string(),
        organizationId: z.number(),
        role: z.enum(['admin', 'user', 'viewer']),
      })
    )
    .mutation(async ({ input }) => {
      return await prisma.user.create({
        data: input,
      });
    }),

  update: protectedProcedure
    .input(
      z.object({
        id: z.number(),
        email: z.string().email().optional(),
        name: z.string().optional(),
      })
    )
    .mutation(async ({ input }) => {
      const { id, ...data } = input;
      return await prisma.user.update({
        where: { id },
        data,
      });
    }),

  delete: protectedProcedure
    .input(z.object({ id: z.number() }))
    .mutation(async ({ input }) => {
      return await prisma.user.delete({
        where: { id: input.id },
      });
    }),
});
```

**Days 4-5**: Express routes, GraphQL resolvers, Zod schemas

### Week 36: Advanced Features
- Next.js App Router integration
- Server Actions
- Authentication patterns
- Testing (Jest/Vitest)

---

## Week 37-38: Go Output Generation

**Objective**: Generate Go/GORM/sqlc code from SpecQL

### Output Targets
1. **GORM models**
2. **sqlc queries** and generated code
3. **Gin/Echo** handlers
4. **gRPC services**
5. **Repository pattern**

### Week 37: Model & Query Generation

**Day 1**: GORM Model Generator

**Output**: `user.go`
```go
package models

import (
    "time"
    "gorm.io/gorm"
)

type User struct {
    ID             uint           `gorm:"primaryKey" json:"id"`
    Email          string         `gorm:"uniqueIndex;not null;size:255" json:"email"`
    Name           string         `gorm:"not null" json:"name"`
    OrganizationID uint           `gorm:"not null" json:"organization_id"`
    Organization   Organization   `gorm:"foreignKey:OrganizationID" json:"organization,omitempty"`
    Role           string         `gorm:"type:varchar(50);not null" json:"role"`
    Posts          []Post         `gorm:"foreignKey:AuthorID" json:"posts,omitempty"`
    CreatedAt      time.Time      `json:"created_at"`
    UpdatedAt      time.Time      `json:"updated_at"`
    DeletedAt      gorm.DeletedAt `gorm:"index" json:"deleted_at,omitempty"`
}

func (User) TableName() string {
    return "users"
}
```

**Day 2**: sqlc Query Generator

**Output**: `queries/user.sql`
```sql
-- name: GetUser :one
SELECT * FROM users
WHERE id = $1 LIMIT 1;

-- name: ListUsers :many
SELECT * FROM users
WHERE deleted_at IS NULL
ORDER BY created_at DESC;

-- name: ListUsersByOrganization :many
SELECT * FROM users
WHERE organization_id = $1
AND deleted_at IS NULL;

-- name: CreateUser :one
INSERT INTO users (
    email, name, organization_id, role, created_at, updated_at
) VALUES (
    $1, $2, $3, $4, NOW(), NOW()
)
RETURNING *;

-- name: UpdateUser :one
UPDATE users
SET name = $2, email = $3, updated_at = NOW()
WHERE id = $1
RETURNING *;

-- name: DeleteUser :exec
UPDATE users
SET deleted_at = NOW()
WHERE id = $1;
```

**sqlc.yaml**:
```yaml
version: "2"
sql:
  - engine: "postgresql"
    queries: "queries"
    schema: "schema.sql"
    gen:
      go:
        package: "db"
        out: "db"
        emit_json_tags: true
        emit_interface: true
```

**Day 3**: Gin Handler Generator

**Output**: `handlers/user.go`
```go
package handlers

import (
    "net/http"
    "strconv"

    "github.com/gin-gonic/gin"
    "myapp/db"
    "myapp/models"
)

type UserHandler struct {
    queries *db.Queries
}

func NewUserHandler(queries *db.Queries) *UserHandler {
    return &UserHandler{queries: queries}
}

func (h *UserHandler) ListUsers(c *gin.Context) {
    users, err := h.queries.ListUsers(c.Request.Context())
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    c.JSON(http.StatusOK, users)
}

func (h *UserHandler) GetUser(c *gin.Context) {
    id, err := strconv.ParseInt(c.Param("id"), 10, 64)
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
        return
    }

    user, err := h.queries.GetUser(c.Request.Context(), id)
    if err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
        return
    }

    c.JSON(http.StatusOK, user)
}

type CreateUserRequest struct {
    Email          string `json:"email" binding:"required,email"`
    Name           string `json:"name" binding:"required"`
    OrganizationID int64  `json:"organization_id" binding:"required"`
    Role           string `json:"role" binding:"required"`
}

func (h *UserHandler) CreateUser(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    user, err := h.queries.CreateUser(c.Request.Context(), db.CreateUserParams{
        Email:          req.Email,
        Name:           req.Name,
        OrganizationID: req.OrganizationID,
        Role:           req.Role,
    })
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    c.JSON(http.StatusCreated, user)
}
```

**Days 4-5**: Repository pattern, service layer, middleware

### Week 38: Advanced Features
- gRPC service generation
- Wire dependency injection
- Testing (testify)
- Docker & deployment

---

## CLI Commands

```bash
# Java
specql generate java entities/*.yaml --output src/main/java/
specql generate spring entities/*.yaml --with-controllers --with-services

# Rust
specql generate rust entities/*.yaml --orm diesel --output src/
specql generate rust entities/*.yaml --orm seaorm --output src/

# TypeScript
specql generate typescript entities/*.yaml --orm prisma --output prisma/
specql generate typescript entities/*.yaml --orm typeorm --output src/entities/
specql generate typescript entities/*.yaml --with-trpc --output src/server/

# Go
specql generate go entities/*.yaml --orm gorm --output models/
specql generate go entities/*.yaml --with-sqlc --output db/
specql generate go entities/*.yaml --framework gin --output handlers/
```

---

## Success Metrics

- [ ] Generate compilable code for all 4 languages
- [ ] Idiomatic patterns for each ecosystem
- [ ] Full CRUD operations working
- [ ] Relationships handled correctly
- [ ] Generated code passes linters
- [ ] Integration tests pass
- [ ] Production-ready code quality

---

**Status**: 🔴 Ready to Execute
**Expected Output**: Complete multi-language code generation from SpecQL
