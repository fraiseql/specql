# User Authentication System Example

**What You'll Build**: A complete user authentication system with registration, login, email verification, and permissions.

**Time**: 25 minutes
**Complexity**: Intermediate

## System Overview

Our authentication system will have:
- **Users**: Registered users with profiles
- **Roles**: User roles (admin, user, moderator)
- **Permissions**: Specific permissions for actions
- **Email Verification**: Email confirmation for new accounts
- **Password Reset**: Secure password recovery
- **Sessions**: User login sessions

## Architecture

```
User (1) ──< (N) UserRole >── (N) Role
   │                           │
   │                           │
   └──< (N) Session            └──< (N) RolePermission >── (N) Permission
   │
   └──< (1) EmailVerification
   │
   └──< (1) PasswordReset
```

## Step 1: Create User Entity

Create `entities/auth/user.yaml`:

```yaml
entity: User
schema: auth
description: A registered user account

fields:
  # Identity
  username: text
  email: email
  password_hash: text

  # Profile
  display_name: text
  first_name: text
  last_name: text

  # Status
  status: enum(active, inactive, suspended, pending_verification)
  email_verified: boolean

  # Security
  failed_login_attempts: integer
  locked_until: timestamp
  last_login_at: timestamp

indexes:
  - fields: [username]
    unique: true
  - fields: [email]
    unique: true
  - fields: [status]

actions:
  - name: verify_email
    description: Mark user email as verified
    requires: system
    steps:
      - update: User SET email_verified = true, status = 'active'
      - delete: EmailVerification WHERE user_id = id
      - log: "Email verified for user"

  - name: suspend_user
    description: Suspend a user account
    requires: caller.can_suspend_users
    steps:
      - validate: status IN ('active', 'inactive')
        error: "user_already_suspended"
      - update: User SET status = 'suspended'
      - log: "User suspended"

  - name: record_login_attempt
    description: Record a login attempt (success or failure)
    requires: system
    steps:
      - update: User SET
          failed_login_attempts = CASE WHEN ? THEN 0 ELSE failed_login_attempts + 1 END,
          last_login_at = CASE WHEN ? THEN NOW() ELSE last_login_at END,
          locked_until = CASE WHEN failed_login_attempts >= 5 THEN NOW() + INTERVAL '30 minutes' ELSE locked_until END
      - log: "Login attempt recorded"

  - name: unlock_account
    description: Unlock a locked user account
    requires: caller.can_unlock_accounts
    steps:
      - update: User SET failed_login_attempts = 0, locked_until = NULL
      - log: "Account unlocked"
```

## Step 2: Create Role Entity

Create `entities/auth/role.yaml`:

```yaml
entity: Role
schema: auth
description: A user role with associated permissions

fields:
  # Identity
  name: text
  description: text

  # Status
  status: enum(active, inactive)

indexes:
  - fields: [name]
    unique: true
```

## Step 3: Create Permission Entity

Create `entities/auth/permission.yaml`:

```yaml
entity: Permission
schema: auth
description: A specific permission for actions

fields:
  # Identity
  name: text
  description: text
  resource: text  # e.g., 'users', 'posts', 'comments'
  action: text    # e.g., 'create', 'read', 'update', 'delete'

indexes:
  - fields: [name]
    unique: true
  - fields: [resource, action]
```

## Step 4: Create UserRole Entity

Create `entities/auth/user_role.yaml`:

```yaml
entity: UserRole
schema: auth
description: Many-to-many relationship between users and roles

fields:
  # Relationships
  user: ref(User)
  role: ref(Role)

  # Metadata
  assigned_at: timestamp
  assigned_by: text

indexes:
  - fields: [user_id, role_id]
    unique: true
  - fields: [role_id]
```

## Step 5: Create RolePermission Entity

Create `entities/auth/role_permission.yaml`:

```yaml
entity: RolePermission
schema: auth
description: Many-to-many relationship between roles and permissions

fields:
  # Relationships
  role: ref(Role)
  permission: ref(Permission)

indexes:
  - fields: [role_id, permission_id]
    unique: true
  - fields: [permission_id]
```

## Step 6: Create EmailVerification Entity

Create `entities/auth/email_verification.yaml`:

```yaml
entity: EmailVerification
schema: auth
description: Email verification tokens for new accounts

fields:
  # Relationships
  user: ref(User)

  # Token
  token: text
  expires_at: timestamp

  # Status
  used: boolean

indexes:
  - fields: [token]
    unique: true
  - fields: [user_id]
  - fields: [expires_at]
```

## Step 7: Create PasswordReset Entity

Create `entities/auth/password_reset.yaml`:

```yaml
entity: PasswordReset
schema: auth
description: Password reset tokens for account recovery

fields:
  # Relationships
  user: ref(User)

  # Token
  token: text
  expires_at: timestamp

  # Status
  used: boolean

indexes:
  - fields: [token]
    unique: true
  - fields: [user_id]
  - fields: [expires_at]
```

## Step 8: Create Session Entity

Create `entities/auth/session.yaml`:

```yaml
entity: Session
schema: auth
description: User login sessions

fields:
  # Relationships
  user: ref(User)

  # Session
  session_token: text
  ip_address: text
  user_agent: text

  # Validity
  expires_at: timestamp
  revoked: boolean

indexes:
  - fields: [session_token]
    unique: true
  - fields: [user_id]
  - fields: [expires_at]
```

## Step 9: Generate the Complete System

```bash
# Create output directory
mkdir -p output/auth

# Generate all entities
specql generate entities/auth/*.yaml --output output/auth

# You should see generation for all 8 entities
```

## Step 10: Inspect Generated Code

### PostgreSQL Schema
```bash
# Check the generated tables
cat output/auth/postgresql/auth/01_tables.sql

# You'll see:
# - auth.tb_user (users)
# - auth.tb_role (roles)
# - auth.tb_permission (permissions)
# - auth.tb_user_role (user-role relationships)
# - auth.tb_role_permission (role-permission relationships)
# - auth.tb_email_verification (email verification tokens)
# - auth.tb_password_reset (password reset tokens)
# - auth.tb_session (user sessions)
# - Foreign key relationships and indexes
```

### Business Logic Functions
```bash
# Check the generated functions
cat output/auth/postgresql/auth/02_functions.sql

# You'll see functions like:
# - auth.fn_user_verify_email()
# - auth.fn_user_suspend_user()
# - auth.fn_user_record_login_attempt()
```

### Java/Spring Boot
```bash
# Check Java entities
ls output/auth/java/com/example/auth/

# You'll see all 8 entity classes with repositories and services
```

## Step 11: Test the Authentication System

If you have PostgreSQL running:

```bash
# Create test database
createdb auth_test

# Apply schema
psql auth_test < output/auth/postgresql/auth/01_tables.sql
psql auth_test < output/auth/postgresql/auth/02_functions.sql

# Insert test data
psql auth_test << 'EOF'
-- Create permissions
INSERT INTO auth.tb_permission (name, description, resource, action)
VALUES ('can_create_users', 'Can create user accounts', 'users', 'create');

INSERT INTO auth.tb_permission (name, description, resource, action)
VALUES ('can_suspend_users', 'Can suspend user accounts', 'users', 'suspend');

-- Create roles
INSERT INTO auth.tb_role (name, description, status)
VALUES ('admin', 'Administrator with full access', 'active');

INSERT INTO auth.tb_role (name, description, status)
VALUES ('user', 'Regular user', 'active');

-- Assign permissions to admin role
INSERT INTO auth.tb_role_permission (role_id, permission_id)
SELECT r.pk_role, p.pk_permission
FROM auth.tb_role r, auth.tb_permission p
WHERE r.name = 'admin' AND p.name IN ('can_create_users', 'can_suspend_users');

-- Create a user
INSERT INTO auth.tb_user (username, email, password_hash, display_name, status, email_verified)
VALUES ('johndoe', 'john@example.com', '$2b$10$hashedpassword', 'John Doe', 'pending_verification', false);

-- Create email verification token
INSERT INTO auth.tb_email_verification (user_id, token, expires_at, used)
VALUES (1, 'abc123verificationtoken', NOW() + INTERVAL '24 hours', false);
EOF

# Query the data
psql auth_test -c "SELECT * FROM auth.tv_user;"
psql auth_test -c "SELECT * FROM auth.tv_role;"
psql auth_test -c "SELECT * FROM auth.tv_permission;"

# Test business logic
psql auth_test -c "SELECT auth.fn_user_verify_email(1);"
psql auth_test -c "SELECT auth.fn_user_suspend_user(1, 'admin@example.com');"
```

## Step 12: FraiseQL Integration

Add this to your FraiseQL configuration:

```yaml
# fraiseql-config.yaml
schemas:
  - name: auth
    entities:
      - entities/auth/user.yaml
      - entities/auth/role.yaml
      - entities/auth/permission.yaml
      - entities/auth/user_role.yaml
      - entities/auth/role_permission.yaml
      - entities/auth/email_verification.yaml
      - entities/auth/password_reset.yaml
      - entities/auth/session.yaml

# This gives you instant GraphQL API:
# - mutation { createUser(input: {username: "johndoe", email: "john@example.com"}) { id } }
# - mutation { verifyEmail(token: "abc123") { success } }
# - query { user(id: 1) { username roles { name permissions { name } } } }
```

## Common Authentication Patterns Used

### 1. Account States
- **Pending Verification** → **Active** → **Suspended/Inactive**
- Email verification required before account activation

### 2. Security Measures
- **Failed Login Tracking**: Lock accounts after multiple failures
- **Session Management**: Track user sessions with expiration
- **Token-based Verification**: Secure tokens for email verification and password reset

### 3. Role-Based Access Control (RBAC)
```yaml
# Users have roles, roles have permissions
User ──< UserRole >── Role ──< RolePermission >── Permission
```

### 4. Password Security
- Store hashed passwords (bcrypt/scrypt)
- Implement password strength requirements
- Secure password reset flow

### 5. Audit Logging
All security actions automatically logged with timestamps and user context.

## Full Source Code

All YAML files for this example:
- [View Source](../../examples/)  <!-- Auth entities would be in separate auth example -->
- [View on GitHub](https://github.com/fraiseql/specql/tree/main/examples)

## Next Steps

- Implement JWT token authentication
- Add OAuth integration (Google, GitHub)
- Create password policies and validation
- Add two-factor authentication (2FA)
- Implement account lockout policies
- Add login attempt rate limiting
- Create admin dashboard for user management
- Add audit logging and compliance features

This authentication system demonstrates how SpecQL enables rapid development of secure, production-ready user management systems with proper access control, security measures, and multi-language code generation.