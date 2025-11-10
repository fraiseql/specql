# Common Issues and Solutions

Frequently encountered problems in SpecQL development and their solutions, covering installation, configuration, entity definition, and runtime issues.

## Installation Issues

### Python Version Compatibility

**Problem:** SpecQL fails to install with "Python version not supported" error.

**Symptoms:**
```
ERROR: Package 'specql' requires a different Python version.
```

**Solutions:**

1. **Check Python version:**
   ```bash
   python --version
   # Should be Python 3.8 or higher
   ```

2. **Use compatible Python version:**
   ```bash
   # Using pyenv
   pyenv install 3.11.0
   pyenv local 3.11.0

   # Using conda
   conda create -n specql python=3.11
   conda activate specql
   ```

3. **Upgrade pip and setuptools:**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

### PostgreSQL Connection Issues

**Problem:** Cannot connect to PostgreSQL database during installation or testing.

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**

1. **Verify PostgreSQL is running:**
   ```bash
   # Check if PostgreSQL service is running
   sudo systemctl status postgresql

   # Or on macOS
   brew services list | grep postgresql
   ```

2. **Check connection parameters:**
   ```bash
   # Test connection with psql
   psql -h localhost -p 5432 -U your_user -d your_database

   # Or check with Python
   python -c "import psycopg2; psycopg2.connect('host=localhost port=5432 user=your_user dbname=your_database')"
   ```

3. **Verify pg_hba.conf settings:**
   ```bash
   # Check PostgreSQL authentication configuration
   sudo cat /etc/postgresql/13/main/pg_hba.conf | grep -E "(local|host)"
   ```

4. **Create database and user:**
   ```sql
   CREATE DATABASE specql_test;
   CREATE USER specql_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE specql_test TO specql_user;
   ```

### Dependency Conflicts

**Problem:** Installation fails due to dependency conflicts.

**Symptoms:**
```
ERROR: Cannot install specql because these package versions have conflicting dependencies.
```

**Solutions:**

1. **Use virtual environment:**
   ```bash
   # Create and activate virtual environment
   python -m venv specql_env
   source specql_env/bin/activate  # On Windows: specql_env\Scripts\activate

   # Install SpecQL
   pip install specql
   ```

2. **Install with compatible versions:**
   ```bash
   # Install specific versions to avoid conflicts
   pip install 'specql>=1.0.0' 'psycopg2-binary>=2.9.0' 'click>=8.0.0'
   ```

3. **Use pip-tools for dependency management:**
   ```bash
   pip install pip-tools
   pip-compile requirements.in
   pip-sync
   ```

## Configuration Issues

### Invalid YAML Syntax

**Problem:** Entity definition files fail to parse with YAML syntax errors.

**Symptoms:**
```
yaml.YAMLError: mapping values are not allowed here
```

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   # Use Python to validate YAML
   python -c "import yaml; yaml.safe_load(open('your_entity.yaml'))"

   # Or use online YAML validator
   ```

2. **Common YAML syntax errors:**
   ```yaml
   # ❌ Wrong: Missing space after colon
   entity:User

   # ✅ Correct: Space after colon
   entity: User

   # ❌ Wrong: Inconsistent indentation
   fields:
     name: text
       type: string  # Wrong indentation

   # ✅ Correct: Consistent indentation
   fields:
     name:
       type: text

   # ❌ Wrong: Unquoted strings with special characters
   description: User's full name

   # ✅ Correct: Quoted strings
   description: "User's full name"
   ```

3. **Use YAML linter:**
   ```bash
   pip install yamllint
   yamllint your_entity.yaml
   ```

### Database Connection Configuration

**Problem:** SpecQL cannot connect to the configured database.

**Symptoms:**
```
ConnectionError: Unable to connect to database
```

**Solutions:**

1. **Check configuration file:**
   ```yaml
   # specql.yaml
   database:
     host: localhost
     port: 5432
     name: your_database
     user: your_user
     password: your_password
     sslmode: require  # or 'disable' for local development
   ```

2. **Test connection:**
   ```bash
   # Test with SpecQL
   specql test connection

   # Or test manually
   psql "host=localhost port=5432 user=your_user dbname=your_database sslmode=require"
   ```

3. **Check environment variables:**
   ```bash
   # Set environment variables
   export SPECQL_DATABASE_HOST=localhost
   export SPECQL_DATABASE_PASSWORD=your_password
   ```

4. **Verify SSL configuration:**
   ```bash
   # For SSL connections
   specql generate cert  # Generate self-signed cert for development
   ```

## Entity Definition Issues

### Invalid Field Types

**Problem:** Entity validation fails with unknown field type errors.

**Symptoms:**
```
ValidationError: Unknown field type 'invalid_type'
```

**Solutions:**

1. **Check supported field types:**
   ```yaml
   # Supported types
   fields:
     text_field: text
     number_field: integer
     decimal_field: decimal(10,2)
     boolean_field: boolean
     date_field: timestamp
     uuid_field: uuid
     json_field: jsonb
     enum_field: enum[value1,value2,value3]
     ref_field: ref(OtherEntity)
   ```

2. **Fix common type mistakes:**
   ```yaml
   # ❌ Wrong
   age: int  # 'int' is not a valid type

   # ✅ Correct
   age: integer

   # ❌ Wrong
   price: float  # Use decimal for money

   # ✅ Correct
   price: decimal(10,2)

   # ❌ Wrong
   status: enum(active, inactive)  # Missing brackets

   # ✅ Correct
   status: enum[active, inactive]
   ```

### Constraint Violations

**Problem:** Entity creation fails due to invalid constraints.

**Symptoms:**
```
ConstraintError: Invalid constraint definition
```

**Solutions:**

1. **Validate constraint syntax:**
   ```yaml
   constraints:
     # ✅ Correct unique constraint
     - name: unique_email
       type: unique
       fields: [email]

     # ✅ Correct check constraint
     - name: positive_amount
       type: check
       condition: "amount > 0"

     # ✅ Correct foreign key
     - name: fk_user
       type: foreign_key
       fields: [user_id]
       references: "users(id)"
   ```

2. **Fix common constraint errors:**
   ```yaml
   # ❌ Wrong: Missing fields for unique constraint
   - name: unique_constraint
     type: unique

   # ✅ Correct
   - name: unique_constraint
     type: unique
     fields: [field1, field2]

   # ❌ Wrong: Invalid SQL syntax in condition
   - name: check_constraint
     type: check
     condition: "field > 0 AND"  # Incomplete condition

   # ✅ Correct
   - name: check_constraint
     type: check
     condition: "field > 0"
   ```

### Action Pattern Errors

**Problem:** Actions fail to generate due to invalid pattern configuration.

**Symptoms:**
```
PatternError: Invalid pattern configuration for 'crud/create'
```

**Solutions:**

1. **Validate pattern syntax:**
   ```yaml
   actions:
     - name: create_entity
       pattern: crud/create
       config:
         duplicate_check:
           fields: [unique_field]
           error_message: "Duplicate found"

     - name: update_entity
       pattern: crud/update
       config:
         partial_updates: true
   ```

2. **Check pattern-specific requirements:**
   ```yaml
   # State machine patterns require from_states and to_state
   - name: approve_entity
     pattern: state_machine/transition
     config:
       from_states: [pending, draft]
       to_state: approved

   # Validation patterns need validation rules
   - name: validate_entity
     pattern: validation/validation_chain
     config:
       validations:
         - name: required_field
           field: name
           condition: "input_data.name IS NOT NULL"
   ```

## Runtime Issues

### Database Migration Failures

**Problem:** Schema migrations fail during entity generation.

**Symptoms:**
```
MigrationError: Cannot alter table due to dependent objects
```

**Solutions:**

1. **Check for dependent objects:**
   ```sql
   -- Find dependent objects
   SELECT * FROM pg_depend
   WHERE refobjid = 'your_table'::regclass;

   -- Check for views, functions, or triggers
   SELECT * FROM information_schema.views WHERE table_name = 'your_table';
   ```

2. **Drop dependent objects before migration:**
   ```sql
   -- Drop views that depend on the table
   DROP VIEW IF EXISTS dependent_view;

   -- Drop functions
   DROP FUNCTION IF EXISTS dependent_function();
   ```

3. **Use safe migration strategies:**
   ```bash
   # Generate migration with safety checks
   specql generate migration --safe

   # Preview migration before applying
   specql generate migration --dry-run
   ```

### Permission Errors

**Problem:** Operations fail due to insufficient database permissions.

**Symptoms:**
```
PermissionError: permission denied for table your_table
```

**Solutions:**

1. **Grant necessary permissions:**
   ```sql
   -- Grant schema permissions
   GRANT USAGE ON SCHEMA your_schema TO specql_user;
   GRANT CREATE ON SCHEMA your_schema TO specql_user;

   -- Grant table permissions
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA your_schema TO specql_user;
   GRANT USAGE ON ALL SEQUENCES IN SCHEMA your_schema TO specql_user;

   -- Grant future permissions
   ALTER DEFAULT PRIVILEGES IN SCHEMA your_schema GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO specql_user;
   ```

2. **Check current permissions:**
   ```sql
   -- Check user permissions
   SELECT * FROM information_schema.role_table_grants
   WHERE grantee = 'specql_user';

   -- Check schema permissions
   SELECT * FROM information_schema.schemata
   WHERE schema_name = 'your_schema';
   ```

### Memory Issues

**Problem:** SpecQL processes fail with out of memory errors.

**Symptoms:**
```
MemoryError: Out of memory
```

**Solutions:**

1. **Increase memory limits:**
   ```bash
   # Set Python memory limit
   export PYTHONPATH=/path/to/specql
   python -c "import resource; resource.setrlimit(resource.RLIMIT_AS, (4*1024*1024*1024, -1))"

   # Or use memory profiling
   python -m memory_profiler your_script.py
   ```

2. **Process large entities in batches:**
   ```bash
   # Generate entities one at a time
   specql generate entity large_entity.yaml

   # Use streaming for large datasets
   specql generate test-data --stream --batch-size 1000
   ```

3. **Optimize PostgreSQL memory settings:**
   ```sql
   -- Increase work memory for complex queries
   SET work_mem = '256MB';

   -- Increase maintenance work memory for indexes
   SET maintenance_work_mem = '512MB';
   ```

## Testing Issues

### Test Database Setup

**Problem:** Tests fail because test database is not properly configured.

**Symptoms:**
```
DatabaseError: test database not found
```

**Solutions:**

1. **Configure test database:**
   ```yaml
   # specql.yaml
   test:
     database:
       host: localhost
       port: 5432
       name: specql_test
       user: test_user
       password: test_password
   ```

2. **Create test database:**
   ```sql
   CREATE DATABASE specql_test;
   CREATE USER test_user WITH PASSWORD 'test_password';
   GRANT ALL PRIVILEGES ON DATABASE specql_test TO test_user;
   ```

3. **Reset test database between runs:**
   ```bash
   # Clean test database
   specql test --reset-db

   # Or manually
   psql -d specql_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   ```

### Test Fixture Issues

**Problem:** Test fixtures fail to load or cause conflicts.

**Symptoms:**
```
FixtureError: Duplicate key value violates unique constraint
```

**Solutions:**

1. **Use unique fixture data:**
   ```yaml
   # Generate unique fixtures
   specql generate fixtures --unique

   # Or use UUIDs in fixtures
   fixtures:
     users:
       - id: "fixture-user-1"
         email: "fixture1@example.com"
   ```

2. **Clean fixtures between tests:**
   ```python
   @pytest.fixture(autouse=True)
   def clean_fixtures(test_db):
       # Clean up before each test
       test_db.execute("DELETE FROM test_fixtures")
   ```

## Performance Issues

### Slow Entity Generation

**Problem:** Entity generation takes too long for large schemas.

**Symptoms:**
```
Generation time exceeds 30 seconds for simple entities
```

**Solutions:**

1. **Optimize entity definitions:**
   ```yaml
   # Use indexes strategically
   fields:
     frequently_queried_field:
       type: text
       indexed: true

   # Avoid over-indexing
   indexes:
     - name: composite_index
       columns: [field1, field2]  # Only when needed
   ```

2. **Use parallel generation:**
   ```bash
   # Generate multiple entities in parallel
   specql generate entities/*.yaml --parallel 4
   ```

3. **Cache generated code:**
   ```bash
   # Use build cache
   specql generate --cache-dir .specql_cache
   ```

### Query Performance Problems

**Problem:** Generated queries are slow in production.

**Symptoms:**
```
Query execution time > 1 second
```

**Solutions:**

1. **Analyze query plans:**
   ```sql
   -- Explain query execution
   EXPLAIN ANALYZE SELECT * FROM your_table WHERE condition;

   -- Check for missing indexes
   SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
   ```

2. **Add performance indexes:**
   ```yaml
   indexes:
     - name: idx_performance
       columns: [frequently_filtered_field]
       type: btree

     - name: idx_composite
       columns: [field1, field2, created_at DESC]
   ```

3. **Optimize field types:**
   ```yaml
   # Use appropriate types for performance
   fields:
     id: uuid  # Fast for primary keys
     category: enum[cat1,cat2,cat3]  # Faster than text
     tags: jsonb  # Efficient for flexible data
   ```

## Getting Help

### Diagnostic Information

**Collect diagnostic information:**
```bash
# SpecQL version and environment
specql --version
python --version
psql --version

# System information
uname -a
df -h  # Disk space
free -h  # Memory

# Database information
psql -d your_database -c "SELECT version();"
psql -d your_database -c "SELECT * FROM pg_settings WHERE name LIKE '%memory%';"
```

### Log Analysis

**Check SpecQL logs:**
```bash
# Enable debug logging
export SPECQL_LOG_LEVEL=DEBUG
specql generate entity your_entity.yaml

# Check log files
tail -f ~/.specql/logs/specql.log
```

### Community Support

**When asking for help:**
1. Include SpecQL version: `specql --version`
2. Provide error messages and stack traces
3. Share relevant entity definitions (anonymized)
4. Include database schema information
5. Describe your environment (OS, Python version, PostgreSQL version)

---

**See Also:**
- [Pattern-Specific Errors](pattern-errors.md)
- [Test Generation Errors](test-generation-errors.md)
- [Debugging Guide](debugging.md)
- [Performance Best Practices](../best-practices/performance.md)