# pytest Tests - Python Integration Testing

pytest is SpecQL's Python integration testing framework. Test your SpecQL-generated functions from application code, validate API responses, and ensure end-to-end functionality with the full power of Python testing.

## 🎯 What You'll Learn

- pytest testing fundamentals with SpecQL
- Generate and run Python integration tests
- Test application-level functionality
- API testing and data validation
- CI/CD integration with pytest

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- [Entity with patterns created](../getting-started/first-entity.md)
- Python 3.8+ with pytest
- Basic Python knowledge

## 💡 pytest Fundamentals

### What is pytest?

**pytest** is a mature, feature-rich testing framework for Python that provides:
- ✅ **Simple test writing** - Write tests as functions
- ✅ **Powerful assertions** - Rich assertion introspection
- ✅ **Fixtures** - Reusable test setup/teardown
- ✅ **Plugins** - Extensive ecosystem
- ✅ **Parallel execution** - Speed up test suites
- ✅ **CI/CD integration** - Works with all CI systems

### Why pytest for SpecQL?

| Feature | pytest | pgTAP | Manual Tests |
|---------|--------|--------------|
| **Language** | 🐍 Python | 🐘 SQL | Any |
| **Scope** | Application | Database | Custom |
| **Setup** | 🛠️ Python deps | ✅ None | Custom |
| **Assertions** | Rich Python | SQL TAP | Basic |
| **Fixtures** | ✅ Advanced | ⚠️ Limited | Custom |
| **Parallel** | ✅ Native | ⚠️ Limited | Custom |

## 🚀 Step 1: Install pytest

### Basic Installation

```bash
# Install pytest and database connector
pip install pytest psycopg2-binary

# Verify installation
pytest --version
```

### Recommended Plugins

```bash
# Install useful pytest plugins
pip install \
    pytest-cov        # Coverage reporting
    pytest-xdist      # Parallel execution
    pytest-html       # HTML reports
    pytest-mock       # Mocking support
    pytest-asyncio    # Async testing
    pytest-django     # Django integration
    pytest-flask      # Flask integration
```

### Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --cov=src
    --cov-report=html
    --cov-report=term-missing
```

## 🧪 Step 2: Generate pytest Tests

### Create Test Entity

```yaml
# entities/product.yaml
name: product
fields:
  id: uuid
  name: string
  price: decimal
  category_id: uuid
  inventory_count: integer
  status: string

patterns:
  - name: state_machine
    description: "Product lifecycle"
    initial_state: draft
    states: [draft, active, discontinued]
    transitions:
      - from: draft
        to: active
        trigger: publish
        guard: "name IS NOT NULL AND price > 0"
      - from: active
        to: discontinued
        trigger: discontinue

  - name: validation
    description: "Product data rules"
    rules:
      - name: positive_price
        field: price
        rule: "price > 0"
        message: "Price must be positive"
      - name: valid_inventory
        field: inventory_count
        rule: "inventory_count >= 0"
        message: "Inventory cannot be negative"
```

### Generate Tests

```bash
# Generate pytest tests
specql generate tests --type pytest entities/product.yaml

# Check generated files
ls -la tests/pytest/
# test_product_state_machine.py
# test_product_validation.py
```

### Generated Test Structure

```python
# tests/pytest/test_product_state_machine.py
import pytest
import psycopg2
from specql.testing.fixtures import database_connection

class TestProductStateMachine:
    @pytest.fixture
    def db_conn(self, database_connection):
        return database_connection

    @pytest.fixture
    def test_product(self, db_conn):
        """Create test product and return ID"""
        with db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO product (name, price, status)
                VALUES (%s, %s, %s)
                RETURNING id
            """, ('Test Product', 29.99, 'draft'))
            product_id = cursor.fetchone()[0]
            db_conn.commit()
            yield product_id

            # Cleanup
            cursor.execute("DELETE FROM product WHERE id = %s", (product_id,))
            db_conn.commit()

    def test_initial_state_is_draft(self, db_conn, test_product):
        """Test product starts in draft state"""
        with db_conn.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM product WHERE id = %s",
                (test_product,)
            )
            status = cursor.fetchone()[0]
            assert status == 'draft'

    def test_successful_publish_transition(self, db_conn, test_product):
        """Test successful product publish"""
        with db_conn.cursor() as cursor:
            cursor.execute(
                "SELECT product_publish(%s)",
                (test_product,)
            )
            result = cursor.fetchone()[0]
            assert result is not None

            # Verify state change
            cursor.execute(
                "SELECT status FROM product WHERE id = %s",
                (test_product,)
            )
            status = cursor.fetchone()[0]
            assert status == 'active'

    def test_publish_fails_without_price(self, db_conn):
        """Test publish fails for product without price"""
        with db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO product (name, price, status)
                VALUES (%s, %s, %s)
                RETURNING id
            """, ('No Price Product', None, 'draft'))
            product_id = cursor.fetchone()[0]
            db_conn.commit()

            try:
                cursor.execute(
                    "SELECT product_publish(%s)",
                    (product_id,)
                )
                result = cursor.fetchone()[0]
                assert result is None  # Should fail due to guard
            finally:
                cursor.execute("DELETE FROM product WHERE id = %s", (product_id,))
                db_conn.commit()

    def test_discontinue_transition(self, db_conn, test_product):
        """Test product discontinuation"""
        with db_conn.cursor() as cursor:
            # First publish the product
            cursor.execute("SELECT product_publish(%s)", (test_product,))

            # Then discontinue it
            cursor.execute(
                "SELECT product_discontinue(%s)",
                (test_product,)
            )
            result = cursor.fetchone()[0]
            assert result is not None

            # Verify final state
            cursor.execute(
                "SELECT status FROM product WHERE id = %s",
                (test_product,)
            )
            status = cursor.fetchone()[0]
            assert status == 'discontinued'
```

## 🏃 Step 3: Run pytest Tests

### Basic Test Execution

```bash
# Run all pytest tests for entity
specql test run --type pytest entities/product.yaml

# Expected output:
# tests/pytest/test_product_state_machine.py::TestProductStateMachine::test_initial_state_is_draft
# PASSED
# tests/pytest/test_product_state_machine.py::TestProductStateMachine::test_successful_publish_transition
# PASSED
# tests/pytest/test_product_state_machine.py::TestProductStateMachine::test_publish_fails_without_price
# PASSED
# tests/pytest/test_product_state_machine.py::TestProductStateMachine::test_discontinue_transition
# PASSED
```

### Advanced pytest Options

```bash
# Run with coverage
specql test run --type pytest entities/product.yaml --cov --cov-report html

# Run in parallel
specql test run --type pytest entities/product.yaml --parallel 4

# Generate HTML report
specql test run --type pytest entities/product.yaml --html-report results.html

# Run specific test class
specql test run --type pytest entities/product.yaml --filter "TestProductStateMachine"

# Run specific test method
specql test run --type pytest entities/product.yaml --filter "test_successful_publish"

# Verbose output
specql test run --type pytest entities/product.yaml --verbose
```

### Manual pytest Execution

```bash
# Run tests directly with pytest
pytest tests/pytest/test_product_state_machine.py -v

# Run with coverage
pytest tests/pytest/ --cov=src --cov-report=html

# Run in parallel
pytest tests/pytest/ -n 4

# Generate HTML report
pytest tests/pytest/ --html=report.html
```

## 🔧 Step 4: Test Fixtures and Setup

### Database Connection Fixture

```python
# tests/conftest.py
import pytest
import psycopg2
import os

@pytest.fixture(scope="session")
def database_connection():
    """Provide database connection for tests"""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # Use transactions

    yield conn

    conn.close()

@pytest.fixture
def db_cursor(database_connection):
    """Provide database cursor with automatic rollback"""
    cursor = database_connection.cursor()

    yield cursor

    database_connection.rollback()  # Rollback after each test
```

### Test Data Factories

```python
# tests/fixtures/product_factory.py
import uuid

def create_test_product(db_cursor, **overrides):
    """Factory for creating test products"""
    defaults = {
        'id': str(uuid.uuid4()),
        'name': 'Test Product',
        'price': 29.99,
        'status': 'draft',
        'inventory_count': 100
    }
    data = {**defaults, **overrides}

    db_cursor.execute("""
        INSERT INTO product (id, name, price, status, inventory_count)
        VALUES (%s, %s, %s, %s, %s)
    """, (data['id'], data['name'], data['price'],
          data['status'], data['inventory_count']))

    return data['id']

def create_test_category(db_cursor, **overrides):
    """Factory for creating test categories"""
    defaults = {
        'id': str(uuid.uuid4()),
        'name': 'Test Category',
        'description': 'Test category description'
    }
    data = {**defaults, **overrides}

    db_cursor.execute("""
        INSERT INTO category (id, name, description)
        VALUES (%s, %s, %s)
    """, (data['id'], data['name'], data['description']))

    return data['id']
```

### Using Factories in Tests

```python
# tests/pytest/test_product_api.py
import pytest
from fixtures.product_factory import create_test_product, create_test_category

class TestProductAPI:
    def test_create_product_api(self, db_cursor, client):
        """Test product creation via API"""
        category_id = create_test_category(db_cursor)

        product_data = {
            'name': 'New Product',
            'price': 49.99,
            'category_id': category_id
        }

        # Assuming you have a test client
        response = client.post('/api/products', json=product_data)
        assert response.status_code == 201

        # Verify in database
        db_cursor.execute(
            "SELECT name, price FROM product WHERE id = %s",
            (response.json()['id'],)
        )
        name, price = db_cursor.fetchone()
        assert name == 'New Product'
        assert price == 49.99

    def test_product_state_machine_via_api(self, db_cursor, client):
        """Test state machine transitions via API"""
        product_id = create_test_product(db_cursor, status='draft')

        # Publish via API
        response = client.post(f'/api/products/{product_id}/publish')
        assert response.status_code == 200

        # Verify state change in database
        db_cursor.execute(
            "SELECT status FROM product WHERE id = %s",
            (product_id,)
        )
        status = db_cursor.fetchone()[0]
        assert status == 'active'
```

## 📊 Step 5: API Testing

### REST API Testing

```python
# tests/pytest/test_product_api.py
import pytest
import requests

class TestProductAPI:
    def test_get_product(self, api_client, test_product):
        """Test retrieving a product via API"""
        response = api_client.get(f'/api/products/{test_product}')

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == test_product
        assert data['status'] == 'draft'

    def test_create_product_validation(self, api_client):
        """Test product creation with validation"""
        # Test missing required field
        response = api_client.post('/api/products', json={
            'price': 29.99
            # Missing 'name'
        })

        assert response.status_code == 400
        assert 'name' in response.json()['errors']

    def test_product_state_transition_api(self, api_client, test_product):
        """Test state machine via REST API"""
        # Publish product
        response = api_client.post(f'/api/products/{test_product}/publish')
        assert response.status_code == 200

        # Verify state change
        response = api_client.get(f'/api/products/{test_product}')
        assert response.status_code == 200
        assert response.json()['status'] == 'active'

    def test_bulk_product_operations(self, api_client, db_cursor):
        """Test bulk operations via API"""
        # Create multiple products
        product_ids = []
        for i in range(5):
            product_ids.append(create_test_product(db_cursor, name=f'Product {i}'))

        # Bulk update via API
        response = api_client.post('/api/products/bulk-update', json={
            'product_ids': product_ids,
            'updates': {'status': 'active'}
        })

        assert response.status_code == 200
        assert response.json()['updated_count'] == 5

        # Verify all products updated
        db_cursor.execute("""
            SELECT count(*) FROM product
            WHERE id = ANY(%s) AND status = 'active'
        """, (product_ids,))
        active_count = db_cursor.fetchone()[0]
        assert active_count == 5
```

### GraphQL API Testing

```python
# tests/pytest/test_product_graphql.py
import pytest

class TestProductGraphQL:
    def test_product_query(self, graphql_client, test_product):
        """Test GraphQL product query"""
        query = """
        query GetProduct($id: ID!) {
            product(id: $id) {
                id
                name
                price
                status
            }
        }
        """

        response = graphql_client.execute(query, variables={'id': test_product})

        assert response.status_code == 200
        data = response.json()['data']['product']
        assert data['id'] == test_product
        assert data['status'] == 'draft'

    def test_product_mutation(self, graphql_client, test_product):
        """Test GraphQL product mutation"""
        mutation = """
        mutation PublishProduct($id: ID!) {
            publishProduct(id: $id) {
                id
                status
                publishedAt
            }
        }
        """

        response = graphql_client.execute(mutation, variables={'id': test_product})

        assert response.status_code == 200
        data = response.json()['data']['publishProduct']
        assert data['status'] == 'active'
        assert data['publishedAt'] is not None
```

## 🔍 Step 6: Integration Testing

### End-to-End Workflows

```python
# tests/pytest/test_ecommerce_workflow.py
import pytest
from fixtures.user_factory import create_test_user
from fixtures.product_factory import create_test_product, create_test_category
from fixtures.order_factory import create_test_order

class TestEcommerceWorkflow:
    def test_complete_purchase_flow(self, db_cursor, api_client):
        """Test complete purchase workflow"""
        # Setup test data
        user_id = create_test_user(db_cursor)
        category_id = create_test_category(db_cursor)
        product_id = create_test_product(db_cursor, category_id=category_id)

        # Step 1: Add to cart
        cart_response = api_client.post('/api/cart/add', json={
            'user_id': user_id,
            'product_id': product_id,
            'quantity': 2
        })
        assert cart_response.status_code == 200
        cart_id = cart_response.json()['cart_id']

        # Step 2: Checkout
        checkout_response = api_client.post('/api/checkout', json={
            'cart_id': cart_id,
            'shipping_address': '123 Main St'
        })
        assert checkout_response.status_code == 200
        order_id = checkout_response.json()['order_id']

        # Step 3: Verify order created
        db_cursor.execute("""
            SELECT status, total_amount FROM order WHERE id = %s
        """, (order_id,))
        status, total = db_cursor.fetchone()
        assert status == 'pending'
        assert total == 59.98  # 2 * 29.99

        # Step 4: Process payment
        payment_response = api_client.post('/api/payments', json={
            'order_id': order_id,
            'amount': 59.98,
            'payment_method': 'credit_card'
        })
        assert payment_response.status_code == 200

        # Step 5: Confirm order (should trigger state machine)
        confirm_response = api_client.post(f'/api/orders/{order_id}/confirm')
        assert confirm_response.status_code == 200

        # Step 6: Verify final state
        db_cursor.execute("""
            SELECT status FROM order WHERE id = %s
        """, (order_id,))
        final_status = db_cursor.fetchone()[0]
        assert final_status == 'confirmed'

        # Step 7: Check inventory updated
        db_cursor.execute("""
            SELECT inventory_count FROM product WHERE id = %s
        """, (product_id,))
        inventory = db_cursor.fetchone()[0]
        assert inventory == 98  # 100 - 2
```

### Cross-Service Testing

```python
# tests/pytest/test_cross_service.py
import pytest
from unittest.mock import patch

class TestCrossServiceIntegration:
    def test_inventory_service_integration(self, db_cursor, test_product):
        """Test integration with inventory service"""
        with patch('services.inventory.InventoryService.check_stock') as mock_check:
            mock_check.return_value = True

            # Attempt to place order
            response = place_order_via_api({
                'product_id': test_product,
                'quantity': 5
            })

            assert response.status_code == 200
            mock_check.assert_called_once_with(test_product, 5)

    def test_payment_gateway_integration(self, db_cursor):
        """Test payment gateway integration"""
        with patch('services.payment.PaymentGateway.charge') as mock_charge:
            mock_charge.return_value = {'status': 'success', 'transaction_id': 'txn_123'}

            # Process payment
            result = process_payment_via_api({
                'amount': 100.00,
                'card_token': 'tok_456'
            })

            assert result['status'] == 'success'
            mock_charge.assert_called_once()

    def test_notification_service_integration(self, db_cursor, test_product):
        """Test notification service integration"""
        with patch('services.notification.NotificationService.send_email') as mock_send:
            mock_send.return_value = True

            # Publish product (should trigger notification)
            publish_product_via_api(test_product)

            # Verify notification sent
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert 'product_published' in call_args[0]  # Email template
```

## 📈 Step 7: Performance and Load Testing

### Performance Benchmarks

```python
# tests/pytest/test_performance.py
import pytest
import time
from fixtures.product_factory import create_test_product

class TestProductPerformance:
    def test_product_creation_performance(self, db_cursor, benchmark):
        """Benchmark product creation performance"""
        def create_products():
            for i in range(100):
                create_test_product(db_cursor, name=f'Product {i}')

        # Benchmark the operation
        result = benchmark(create_products)

        # Assert performance requirements
        assert result.stats.mean < 1.0  # Average < 1 second for 100 products

    def test_state_machine_transition_performance(self, db_cursor, benchmark):
        """Benchmark state machine transitions"""
        # Create test products
        product_ids = []
        for i in range(100):
            product_ids.append(create_test_product(db_cursor))

        def bulk_publish():
            db_cursor.executemany("""
                SELECT product_publish(%s)
            """, [(pid,) for pid in product_ids])

        result = benchmark(bulk_publish)
        assert result.stats.mean < 2.0  # < 2 seconds for 100 transitions

    def test_concurrent_access(self, db_cursor):
        """Test concurrent access to products"""
        import threading

        product_id = create_test_product(db_cursor)
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    # Simulate concurrent operations
                    db_cursor.execute("""
                        UPDATE product
                        SET inventory_count = inventory_count - 1
                        WHERE id = %s AND inventory_count > 0
                    """, (product_id,))
                    db_cursor.connection.commit()
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0

        # Verify final inventory
        db_cursor.execute("SELECT inventory_count FROM product WHERE id = %s", (product_id,))
        final_inventory = db_cursor.fetchone()[0]
        assert final_inventory == 50  # 100 - (5 workers * 10 operations)
```

### Load Testing

```python
# tests/pytest/test_load.py
import pytest
import asyncio
import aiohttp
from fixtures.product_factory import create_test_product

class TestProductLoad:
    @pytest.mark.asyncio
    async def test_api_load(self, api_client):
        """Test API under load"""
        async with aiohttp.ClientSession() as session:
            # Create test data
            product_ids = []
            for i in range(100):
                product_ids.append(create_test_product(db_cursor))

            # Test concurrent API calls
            tasks = []
            for product_id in product_ids[:50]:  # Test 50 concurrent requests
                tasks.append(session.get(f'{api_client.base_url}/api/products/{product_id}'))

            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            # Verify all requests succeeded
            assert all(r.status == 200 for r in responses)

            # Verify performance
            total_time = end_time - start_time
            avg_response_time = total_time / len(tasks)
            assert avg_response_time < 0.5  # < 500ms average
```

## 🔧 Step 8: Customize pytest Tests

### Test Configuration

```yaml
# In your entity YAML
name: product
# ... fields and patterns ...

test_config:
  pytest:
    # Test structure
    test_class_prefix: "Test"
    test_method_prefix: "test_"

    # Fixtures
    fixtures:
      - name: test_product
        factory: "fixtures.product_factory.create_test_product"
        cleanup: true

      - name: test_category
        factory: "fixtures.category_factory.create_test_category"

    # Test data
    test_data:
      - name: premium_product
        data:
          name: "Premium Product"
          price: 99.99
          category: "premium"

    # Performance requirements
    performance:
      max_execution_time: "30 seconds"
      max_memory_usage: "100 MB"

    # Coverage requirements
    coverage:
      minimum: 95
      exclude_patterns: ["test_*", "fixture_*"]
```

### Custom Test Templates

```python
# tests/pytest/test_product_custom.py
import pytest
from specql.testing.base import SpecQLTestCase

class TestProductCustom(SpecQLTestCase):
    """Custom tests for product entity"""

    def test_product_search_functionality(self, db_cursor, test_product):
        """Test product search functionality"""
        # This would test custom search functions
        # that might not be auto-generated

        # Insert test data
        db_cursor.execute("""
            UPDATE product
            SET name = 'Special Test Product',
                tags = ARRAY['electronics', 'gadgets']
            WHERE id = %s
        """, (test_product,))

        # Test search function (assuming it exists)
        db_cursor.execute("""
            SELECT * FROM search_products('electronics')
        """)
        results = db_cursor.fetchall()

        assert len(results) > 0
        assert any('Special Test Product' in str(row) for row in results)

    def test_product_recommendation_engine(self, db_cursor):
        """Test product recommendation logic"""
        # Create test products with categories
        electronics_category = create_test_category(db_cursor, name='Electronics')
        books_category = create_test_category(db_cursor, name='Books')

        product1 = create_test_product(db_cursor,
            name='iPhone', category_id=electronics_category)
        product2 = create_test_product(db_cursor,
            name='Python Book', category_id=books_category)

        # Test recommendation (assuming recommendation function exists)
        db_cursor.execute("""
            SELECT * FROM recommend_products(%s, 5)
        """, (electronics_category,))
        recommendations = db_cursor.fetchall()

        # Should recommend electronics products
        assert len(recommendations) > 0
        # Add more specific assertions based on your recommendation logic
```

## 🔄 Step 9: CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/pytest-tests.yml
name: pytest Tests

on: [push, pull_request]

jobs:
  test:
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
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          pip install specql pytest pytest-cov pytest-xdist psycopg2-binary

      - name: Generate Schema
        run: specql generate schema entities/*.yaml

      - name: Apply Schema
        run: |
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/00_foundation/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/10_tables/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/40_functions/*.sql

      - name: Generate pytest Tests
        run: specql generate tests --type pytest entities/*.yaml

      - name: Run pytest Tests
        run: specql test run --type pytest entities/*.yaml --cov --cov-report xml

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Parallel Testing

```yaml
# .github/workflows/parallel-tests.yml
name: Parallel pytest Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-group: [1, 2, 3, 4]

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: pip install specql pytest pytest-xdist psycopg2-binary

      # ... schema setup steps ...

      - name: Generate Tests
        run: specql generate tests --type pytest entities/*.yaml

      - name: Run Parallel Tests
        run: |
          # Split tests into groups
          pytest tests/pytest/ \
            --numprocesses 4 \
            --group ${{ matrix.test-group }} \
            --cov=src \
            --cov-report xml \
            --cov-report term-missing
```

## 🎯 Best Practices

### Test Design
- **Use descriptive test names** - Explain what each test validates
- **Keep tests focused** - Test one behavior per test method
- **Use fixtures effectively** - Share setup/teardown code
- **Test realistic scenarios** - Use production-like data

### Performance
- **Use parallel execution** - Speed up test suites with pytest-xdist
- **Mock external services** - Avoid slow network calls in tests
- **Use appropriate fixtures** - session > module > class > function scope
- **Profile slow tests** - Identify and optimize bottlenecks

### Maintenance
- **Regenerate tests regularly** - Keep in sync with schema changes
- **Review test failures** - Understand root causes, not just symptoms
- **Update test expectations** - When business logic changes intentionally
- **Document custom tests** - Explain non-obvious test logic

### Integration Testing
- **Test complete workflows** - End-to-end user journeys
- **Use realistic test data** - Match production data characteristics
- **Test error scenarios** - Invalid inputs, network failures, timeouts
- **Verify data consistency** - Check database state after operations

## 🆘 Troubleshooting

### "pytest command not found"
```bash
# Install pytest
pip install pytest

# Or use specql wrapper
specql test run --type pytest entities/user.yaml
```

### "Database connection failed"
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection manually
python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"

# Use test database
export DATABASE_URL="postgresql://localhost/specql_test"
```

### "Tests pass locally but fail in CI"
```bash
# Check environment differences
# - Python version
# - PostgreSQL version
# - Database collation
# - Timezone settings

# Use same versions in CI as local
```

### "Fixture errors"
```python
# Check fixture scope
@pytest.fixture(scope="function")  # Default - per test
@pytest.fixture(scope="class")     # Per test class
@pytest.fixture(scope="module")    # Per test module
@pytest.fixture(scope="session")   # Once per test session
```

### "Import errors"
```python
# Check Python path
import sys
sys.path.append('tests')

# Or use absolute imports
from tests.fixtures.user_factory import create_test_user
```

### "Coverage not working"
```bash
# Install coverage
pip install pytest-cov

# Run with coverage
pytest --cov=src --cov-report html

# Check coverage configuration
pytest --cov-config=.coveragerc
```

## 📊 Success Metrics

### Test Quality Metrics
- **Test execution time**: <5 minutes for full suite
- **Test coverage**: >95% of application code
- **Test count**: 10-20 tests per entity
- **Failure rate**: <1% in stable branches

### Performance Benchmarks
- **API response time**: <200ms average
- **Database queries**: <50ms average
- **Concurrent users**: Support 100+ simultaneous users
- **Memory usage**: <100MB per test process

### Reliability Goals
- **Zero flaky tests** - Tests should be deterministic
- **Fast feedback** - Results in <10 minutes
- **CI stability** - <2% false failures
- **Maintenance cost** - <5% of development time

## 🎉 Summary

pytest testing provides:
- ✅ **Python integration testing** - Test from application code
- ✅ **Rich assertions** - Detailed failure information
- ✅ **Flexible fixtures** - Reusable test setup
- ✅ **Parallel execution** - Fast test suites
- ✅ **CI/CD integration** - Comprehensive reporting

## 🚀 What's Next?

- **[Performance Tests](performance-tests.md)** - Benchmarking and optimization
- **[CI/CD Integration](ci-cd-integration.md)** - Automated testing pipelines
- **[Custom Test Patterns](../best-practices/testing.md)** - Advanced testing techniques
- **[API Testing](../best-practices/api-testing.md)** - REST and GraphQL testing

**Ready to test your complete application stack? Let's continue! 🚀**