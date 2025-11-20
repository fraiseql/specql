# Testing Guide

> **Comprehensive testing for SpecQL projects—from units to E2E**

## Overview

SpecQL supports multiple testing levels:
- ✅ **Unit Tests** - Test individual actions and functions
- ✅ **Integration Tests** - Test database interactions
- ✅ **E2E Tests** - Test full stack (DB → GraphQL → Frontend)
- ✅ **Contract Tests** - Validate API contracts
- ✅ **Performance Tests** - Load testing and benchmarks

**Goal**: 80%+ code coverage, sub-100ms test suite

---

## Quick Start

### Install Test Dependencies

```bash
# Python (pytest for SpecQL itself)
pip install pytest pytest-cov pytest-postgresql

# Database testing
pip install testing.postgresql psycopg2-binary

# GraphQL testing
npm install --save-dev @testing-library/react vitest
```

---

### Your First Test

**File**: `tests/test_qualify_lead.py`

```python
import pytest
from psycopg2.extras import RealDictCursor

def test_qualify_lead_success(db_connection):
    """Test qualifying a lead successfully"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    # Setup: Create test contact with status='lead'
    cursor.execute("""
        INSERT INTO crm.tb_contact (email, first_name, last_name, fk_company, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, ('test@example.com', 'John', 'Doe', 1, 'lead'))
    contact_id = cursor.fetchone()['id']

    # Execute: Call qualify_lead action
    cursor.execute("""
        SELECT * FROM app.qualify_lead(%s)
    """, (contact_id,))
    result = cursor.fetchone()

    # Assert: Check success
    assert result['status'] == 'success'
    assert result['code'] == 'lead_qualified'
    assert result['data']['status'] == 'qualified'

def test_qualify_lead_validation_error(db_connection):
    """Test validation error when qualifying non-lead"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    # Setup: Create contact with status='customer' (not lead)
    cursor.execute("""
        INSERT INTO crm.tb_contact (email, first_name, last_name, fk_company, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, ('test@example.com', 'Jane', 'Doe', 1, 'customer'))
    contact_id = cursor.fetchone()['id']

    # Execute: Call qualify_lead (should fail)
    cursor.execute("""
        SELECT * FROM app.qualify_lead(%s)
    """, (contact_id,))
    result = cursor.fetchone()

    # Assert: Check error
    assert result['status'] == 'error'
    assert result['code'] == 'not_a_lead'
```

---

## Test Fixtures

### Database Fixture

**File**: `tests/conftest.py`

```python
import pytest
import testing.postgresql
import psycopg2

@pytest.fixture(scope='session')
def postgresql():
    """Start PostgreSQL server for tests"""
    with testing.postgresql.Postgresql() as pg:
        yield pg

@pytest.fixture(scope='function')
def db_connection(postgresql):
    """Create fresh database connection with schema"""
    conn = psycopg2.connect(**postgresql.dsn())
    cursor = conn.cursor()

    # Load generated schema
    with open('generated/schema/00_framework/app_schema.sql') as f:
        cursor.execute(f.read())

    with open('generated/schema/10_tables/contact.sql') as f:
        cursor.execute(f.read())

    with open('generated/functions/qualify_lead.sql') as f:
        cursor.execute(f.read())

    conn.commit()

    yield conn

    # Cleanup
    conn.rollback()
    conn.close()
```

---

### Seed Data Fixture

```python
@pytest.fixture
def seed_data(db_connection):
    """Create test data"""
    cursor = db_connection.cursor()

    # Create company
    cursor.execute("""
        INSERT INTO crm.tb_company (name, website)
        VALUES (%s, %s)
        RETURNING pk_company
    """, ('ACME Corp', 'https://acme.com'))
    company_pk = cursor.fetchone()[0]

    # Create contacts
    cursor.execute("""
        INSERT INTO crm.tb_contact (email, first_name, last_name, fk_company, status)
        VALUES
            ('lead1@example.com', 'John', 'Doe', %s, 'lead'),
            ('lead2@example.com', 'Jane', 'Smith', %s, 'lead'),
            ('customer@example.com', 'Bob', 'Johnson', %s, 'customer')
        RETURNING id
    """, (company_pk, company_pk, company_pk))

    db_connection.commit()

    return {
        'company_pk': company_pk,
        'lead_ids': [row[0] for row in cursor.fetchall()]
    }
```

---

## Unit Testing Actions

### Test Validation Steps

```python
def test_validate_step_success(db_connection, seed_data):
    """Test validation step passes when condition is true"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    lead_id = seed_data['lead_ids'][0]

    # Call action with valid data
    cursor.execute("SELECT * FROM app.qualify_lead(%s)", (lead_id,))
    result = cursor.fetchone()

    assert result['status'] == 'success'

def test_validate_step_failure(db_connection, seed_data):
    """Test validation step fails when condition is false"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    # Use customer ID (not a lead)
    customer_id = seed_data['lead_ids'][2]

    cursor.execute("SELECT * FROM app.qualify_lead(%s)", (customer_id,))
    result = cursor.fetchone()

    assert result['status'] == 'error'
    assert result['code'] == 'not_a_lead'
```

---

### Test Update Steps

```python
def test_update_step(db_connection, seed_data):
    """Test update step modifies database"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    lead_id = seed_data['lead_ids'][0]

    # Before: status is 'lead'
    cursor.execute("SELECT status FROM crm.tb_contact WHERE id = %s", (lead_id,))
    assert cursor.fetchone()['status'] == 'lead'

    # Execute action
    cursor.execute("SELECT * FROM app.qualify_lead(%s)", (lead_id,))

    # After: status is 'qualified'
    cursor.execute("SELECT status FROM crm.tb_contact WHERE id = %s", (lead_id,))
    assert cursor.fetchone()['status'] == 'qualified'
```

---

### Test Conditional Logic

```python
def test_if_then_else(db_connection):
    """Test conditional logic in actions"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    # Test high-value order (>= 10000)
    cursor.execute("""
        SELECT * FROM app.create_order(%s, %s)
    """, (customer_id, 15000))
    result = cursor.fetchone()

    # Should require approval
    cursor.execute("""
        SELECT requires_approval FROM sales.tb_order WHERE id = %s
    """, (result['data']['id'],))
    assert cursor.fetchone()['requires_approval'] == True

    # Test low-value order (< 10000)
    cursor.execute("""
        SELECT * FROM app.create_order(%s, %s)
    """, (customer_id, 5000))
    result = cursor.fetchone()

    # Should auto-approve
    cursor.execute("""
        SELECT requires_approval FROM sales.tb_order WHERE id = %s
    """, (result['data']['id'],))
    assert cursor.fetchone()['requires_approval'] == False
```

---

### Test Foreach Loops

```python
def test_foreach_step(db_connection, seed_data):
    """Test foreach loop processes all items"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    # Qualify all leads at once
    lead_ids = seed_data['lead_ids'][:2]  # First 2 are leads

    cursor.execute("""
        SELECT * FROM app.bulk_qualify_leads(%s)
    """, (lead_ids,))
    result = cursor.fetchone()

    assert result['status'] == 'success'

    # Verify all are qualified
    cursor.execute("""
        SELECT COUNT(*) FROM crm.tb_contact
        WHERE id = ANY(%s) AND status = 'qualified'
    """, (lead_ids,))
    assert cursor.fetchone()['count'] == 2
```

---

## Integration Testing

### Test Database Constraints

```python
def test_foreign_key_constraint(db_connection):
    """Test FK constraint prevents invalid references"""
    cursor = db_connection.cursor()

    # Try to insert contact with invalid company FK
    with pytest.raises(psycopg2.errors.ForeignKeyViolation):
        cursor.execute("""
            INSERT INTO crm.tb_contact (email, first_name, last_name, fk_company, status)
            VALUES (%s, %s, %s, %s, %s)
        """, ('test@example.com', 'John', 'Doe', 99999, 'lead'))

def test_email_validation(db_connection, seed_data):
    """Test email validation constraint"""
    cursor = db_connection.cursor()

    # Try to insert invalid email
    with pytest.raises(psycopg2.errors.CheckViolation):
        cursor.execute("""
            INSERT INTO crm.tb_contact (email, first_name, last_name, fk_company)
            VALUES (%s, %s, %s, %s)
        """, ('not-an-email', 'John', 'Doe', seed_data['company_pk']))

def test_enum_constraint(db_connection, seed_data):
    """Test enum constraint rejects invalid values"""
    cursor = db_connection.cursor()

    # Try to insert invalid status
    with pytest.raises(psycopg2.errors.CheckViolation):
        cursor.execute("""
            INSERT INTO crm.tb_contact (email, first_name, last_name, fk_company, status)
            VALUES (%s, %s, %s, %s, %s)
        """, ('test@example.com', 'John', 'Doe', seed_data['company_pk'], 'invalid_status'))
```

---

### Test Trinity Pattern Helpers

```python
def test_trinity_pk_helper(db_connection, seed_data):
    """Test entity_pk() helper converts UUID to INTEGER"""
    cursor = db_connection.cursor()

    lead_id = seed_data['lead_ids'][0]

    # Get pk using helper
    cursor.execute("SELECT crm.contact_pk(%s)", (lead_id,))
    pk = cursor.fetchone()[0]

    assert isinstance(pk, int)
    assert pk > 0

def test_trinity_id_helper(db_connection, seed_data):
    """Test entity_id() helper converts INTEGER to UUID"""
    cursor = db_connection.cursor()

    # Get first contact's pk
    cursor.execute("SELECT pk_contact FROM crm.tb_contact LIMIT 1")
    pk = cursor.fetchone()[0]

    # Convert to UUID
    cursor.execute("SELECT crm.contact_id(%s)", (pk,))
    uuid = cursor.fetchone()[0]

    assert isinstance(uuid, str)
    assert len(uuid) == 36  # UUID format
```

---

## GraphQL Testing

### Test Mutations

**File**: `tests/graphql/test_mutations.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { executeGraphQL } from './test-utils';

describe('qualifyLead mutation', () => {
  it('should qualify a lead successfully', async () => {
    const result = await executeGraphQL(`
      mutation QualifyLead($contactId: ID!) {
        qualifyLead(contactId: $contactId) {
          status
          code
          data {
            id
            status
          }
        }
      }
    `, {
      contactId: testLeadId
    });

    expect(result.data.qualifyLead.status).toBe('SUCCESS');
    expect(result.data.qualifyLead.data.status).toBe('qualified');
  });

  it('should return error for non-lead', async () => {
    const result = await executeGraphQL(`
      mutation QualifyLead($contactId: ID!) {
        qualifyLead(contactId: $contactId) {
          status
          code
          message
        }
      }
    `, {
      contactId: testCustomerId
    });

    expect(result.data.qualifyLead.status).toBe('ERROR');
    expect(result.data.qualifyLead.code).toBe('not_a_lead');
  });
});
```

---

### Test Impact Metadata

```typescript
it('should return correct impact metadata', async () => {
  const result = await executeGraphQL(`
    mutation QualifyLead($contactId: ID!) {
      qualifyLead(contactId: $contactId) {
        status
        _meta {
          impacts {
            entity
            operation
            ids
          }
        }
      }
    }
  `, {
    contactId: testLeadId
  });

  expect(result.data.qualifyLead._meta.impacts).toEqual([
    {
      entity: 'Contact',
      operation: 'UPDATE',
      ids: [testLeadId]
    }
  ]);
});
```

---

## Frontend Testing

### Test React Hooks

**File**: `tests/frontend/useQualifyLead.test.tsx`

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useQualifyLead } from '@/generated/hooks';
import { MockedProvider } from '@apollo/client/testing';

describe('useQualifyLead', () => {
  it('should qualify lead successfully', async () => {
    const mocks = [
      {
        request: {
          query: QUALIFY_LEAD_MUTATION,
          variables: { contactId: 'test-id' }
        },
        result: {
          data: {
            qualifyLead: {
              status: 'SUCCESS',
              code: 'lead_qualified',
              data: {
                id: 'test-id',
                status: 'qualified'
              }
            }
          }
        }
      }
    ];

    const { result } = renderHook(() => useQualifyLead(), {
      wrapper: ({ children }) => (
        <MockedProvider mocks={mocks}>
          {children}
        </MockedProvider>
      )
    });

    const [qualifyLead] = result.current;

    await act(async () => {
      await qualifyLead({ variables: { contactId: 'test-id' } });
    });

    await waitFor(() => {
      expect(result.current[1].data.qualifyLead.status).toBe('SUCCESS');
    });
  });
});
```

---

## Performance Testing

### Load Testing with k6

**File**: `tests/load/qualify_lead.js`

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 50 },    // Ramp up to 50 users
    { duration: '30s', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
  },
};

export default function () {
  const payload = JSON.stringify({
    query: `
      mutation QualifyLead($contactId: ID!) {
        qualifyLead(contactId: $contactId) {
          status
          code
        }
      }
    `,
    variables: {
      contactId: '550e8400-e29b-41d4-a716-446655440000'
    }
  });

  const res = http.post('http://localhost:5000/graphql', payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
```

**Run**:
```bash
k6 run tests/load/qualify_lead.js
```

---

### Database Benchmark

```python
import pytest
import time

def test_qualify_lead_performance(db_connection, seed_data):
    """Test qualify_lead completes in < 10ms"""
    cursor = db_connection.cursor()
    lead_id = seed_data['lead_ids'][0]

    # Warm up
    cursor.execute("SELECT * FROM app.qualify_lead(%s)", (lead_id,))

    # Measure
    iterations = 100
    start = time.time()

    for _ in range(iterations):
        cursor.execute("SELECT * FROM app.qualify_lead(%s)", (lead_id,))
        cursor.fetchone()

    end = time.time()
    avg_time_ms = ((end - start) / iterations) * 1000

    assert avg_time_ms < 10, f"Average time {avg_time_ms}ms exceeds 10ms threshold"
```

---

## Test Coverage

### Generate Coverage Report

```bash
# Python tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

**Target**: 80%+ coverage

---

### Coverage by Module

```bash
pytest --cov=src --cov-report=term-missing

# Output:
# Name                                Stmts   Miss  Cover   Missing
# ----------------------------------------------------------------
# src/core/specql_parser.py            234      12    95%   145-156
# src/generators/actions/...           567      45    92%   ...
# src/generators/schema/...            423      38    91%   ...
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/                       # Unit tests (fast, isolated)
│   ├── core/
│   │   └── test_specql_parser.py
│   ├── actions/
│   │   ├── test_validate_step.py
│   │   ├── test_update_step.py
│   │   └── test_if_step.py
│   └── schema/
│       ├── test_table_generator.py
│       └── test_trinity_helpers.py
│
├── integration/                # Integration tests (DB access)
│   ├── actions/
│   │   ├── test_qualify_lead.py
│   │   └── test_create_order.py
│   ├── schema/
│   │   └── test_constraints.py
│   └── graphql/
│       └── test_mutations.ts
│
├── e2e/                        # End-to-end tests (full stack)
│   ├── test_order_workflow.ts
│   └── test_crm_workflow.ts
│
├── load/                       # Performance tests
│   ├── qualify_lead.js
│   └── create_order.js
│
└── conftest.py                 # Shared fixtures
```

---

## CI/CD Integration

### GitHub Actions Workflow

**File**: `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest tests/unit --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4

      - name: Run integration tests
        run: pytest tests/integration
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
```

---

## Best Practices

### ✅ DO

**Write tests first (TDD)**:
```yaml
# 1. Write failing test
def test_qualify_lead():
    assert result['status'] == 'success'  # Fails

# 2. Implement action
actions:
  - name: qualify_lead
    steps: ...

# 3. Test passes
```

**Test edge cases**:
```python
def test_qualify_lead_null_id():
    """Test with NULL contact_id"""
    result = execute_action('qualify_lead', None)
    assert result['status'] == 'error'

def test_qualify_lead_nonexistent_id():
    """Test with non-existent contact_id"""
    result = execute_action('qualify_lead', '00000000-0000-0000-0000-000000000000')
    assert result['status'] == 'error'
```

**Use descriptive test names**:
```python
# Good
def test_qualify_lead_fails_when_contact_is_already_customer():
    ...

# Bad
def test_1():
    ...
```

---

### ❌ DON'T

**Don't test implementation details**:
```python
# Bad: Testing internal SQL structure
def test_qualify_lead_uses_correct_sql():
    assert 'UPDATE tb_contact SET status' in generated_sql

# Good: Test behavior
def test_qualify_lead_changes_status_to_qualified():
    result = execute_action('qualify_lead', lead_id)
    assert result['data']['status'] == 'qualified'
```

**Don't share state between tests**:
```python
# Bad
global_contact_id = None

def test_create_contact():
    global global_contact_id
    global_contact_id = ...

def test_qualify_lead():
    # Depends on test_create_contact running first!
    execute_action('qualify_lead', global_contact_id)

# Good: Use fixtures
def test_qualify_lead(contact_fixture):
    execute_action('qualify_lead', contact_fixture.id)
```

---

## Next Steps

### Learn More

- **[Performance Tuning](performance-tuning.md)** - Optimize slow tests
- **[Monitoring](monitoring.md)** - Production testing
- **[Deployment](deployment.md)** - Test environments

### Tools

- **pytest** - Python testing
- **Vitest** - TypeScript/React testing
- **k6** - Load testing
- **Codecov** - Coverage tracking

---

## Summary

You've learned:
- ✅ Unit, integration, and E2E testing
- ✅ Test fixtures and seed data
- ✅ GraphQL and frontend testing
- ✅ Performance and load testing
- ✅ Coverage reporting and CI/CD

**Key Takeaway**: Comprehensive testing ensures SpecQL-generated code works correctly in production.

**Next**: Secure your application with [Security Hardening](security-hardening.md) →

---

**Test early, test often—confidence comes from coverage.**
