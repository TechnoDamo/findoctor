# FinDoctor Backend Testing System

## Overview

This document describes the comprehensive testing system for the FinDoctor backend API. The system includes:

1. **Enhanced test runner** with command-line flags for different endpoint groups
2. **Comprehensive auth tests** with database verification
3. **Makefile commands** for easy test execution
4. **Detailed logging** with different verbosity levels

## Test Architecture

### Test Files Structure

```
backend/tests/
├── conftest.py              # Test fixtures and configuration
├── test_auth.py             # Basic authentication tests
├── test_auth_comprehensive.py # Comprehensive auth tests with DB verification
├── test_accounts.py         # Accounts endpoint tests
└── (more test files as endpoints are added)
```

### Test Runner

The enhanced test runner (`test_runner.py`) provides:
- Colorized output for better readability
- Command-line flags for testing specific endpoint groups
- Different verbosity levels (quiet, normal, verbose, debug)
- Database verification for auth tests

## Makefile Test Commands

### Basic Test Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all tests with pytest (default) |
| `make test-auth` | Run authentication tests only |
| `make test-accounts` | Run accounts tests only |
| `make test-comprehensive` | Run comprehensive tests with database verification |
| `make test-all` | Run all tests including comprehensive ones |

### Advanced Test Commands

| Command | Description |
|---------|-------------|
| `make test-verbose` | Run tests with verbose output |
| `make test-debug` | Run tests with debug output (no capture) |
| `make test-coverage` | Run tests with coverage report |

### Test Runner Commands

You can also use the enhanced test runner directly:

```bash
# Run all tests
python test_runner.py --all

# Run specific test groups
python test_runner.py --auth --accounts

# Run with verbose output
python test_runner.py --all --verbose

# Run with debug output
python test_runner.py --all --debug

# Run specific groups by name
python test_runner.py --groups auth accounts

# Run quietly
python test_runner.py --all --quiet
```

## Comprehensive Auth Tests

The `test_auth_comprehensive.py` file provides thorough testing of authentication endpoints with database verification:

### Test Categories

1. **Registration Tests**
   - User registration with database verification
   - Password hashing verification (not stored in plain text)
   - Session creation verification
   - Duplicate email handling

2. **Login Tests**
   - Successful login with session creation
   - Failed login with wrong password
   - Non-existent user login
   - Session management verification

3. **Token Tests**
   - Token refresh with session invalidation
   - Invalid token handling
   - Token expiration verification

4. **Logout Tests**
   - Session deletion on logout
   - Token invalidation after logout

5. **Current User Tests**
   - User data retrieval
   - Sensitive field protection (password, hash)
   - Database-API data consistency

6. **Edge Case Tests**
   - Invalid email format
   - Weak password handling
   - Various error scenarios

### Database Verification

Each test verifies:
- API response correctness
- Database state changes
- Data integrity
- Security measures (password hashing, token hashing)

## Running Tests

### Prerequisites

1. **Database**: PostgreSQL must be running
2. **Dependencies**: All Python dependencies installed
3. **Environment**: Proper environment variables set

### Quick Start

```bash
# Start the database
make db-up

# Apply migrations
make migrate

# Run all tests
make test

# Run comprehensive auth tests
make test-comprehensive

# Run tests with coverage
make test-coverage
```

### Test Environment

The test environment uses:
- **Test database**: `findoctor_test` on port 5433
- **Isolation**: Database is cleaned between tests
- **Real PostgreSQL**: Tests run against actual PostgreSQL via Docker

## Test Fixtures

Available fixtures in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `db_connection` | Clean database connection for each test |
| `test_client` | HTTP client for API testing |
| `register_data` | Test data for user registration |
| `auth_headers` | Authorization headers for authenticated requests |

## Writing New Tests

### Basic Test Structure

```python
import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_example_endpoint(
    test_client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Test description."""
    resp = await test_client.get(
        "/api/v1/endpoint",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Add assertions
```

### Test with Database Verification

```python
import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

@pytest.mark.anyio
async def test_with_db_verification(
    test_client: AsyncClient,
    db_connection: AsyncConnection,
    auth_headers: dict,
) -> None:
    """Test with database verification."""
    # API call
    resp = await test_client.post("/api/v1/endpoint", headers=auth_headers)
    assert resp.status_code == 201
    
    # Database verification
    async with db_connection.cursor() as cur:
        await cur.execute("SELECT * FROM table WHERE condition")
        row = await cur.fetchone()
        assert row is not None
        # Add assertions
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Verification**: Always verify both API response and database state
3. **Cleanup**: Tests should clean up after themselves
4. **Descriptive**: Use descriptive test names and assertions
5. **Coverage**: Aim for high test coverage of business logic

## Troubleshooting

### Common Issues

1. **Database connection errors**: Ensure Docker is running and database is started
2. **Test failures**: Check test isolation and cleanup
3. **Import errors**: Verify dependencies are installed

### Debugging Tests

```bash
# Run tests with debug output
make test-debug

# Run specific test with more output
uv run pytest tests/test_auth.py::test_specific_function -vvv --capture=no

# Run tests with logging
uv run pytest tests/ -v --log-level=DEBUG
```

## Coverage Reports

Generate coverage reports:

```bash
# Generate HTML coverage report
make test-coverage

# View coverage in terminal
uv run pytest tests/ --cov=app --cov-report=term

# Generate XML report for CI
uv run pytest tests/ --cov=app --cov-report=xml
```

The coverage report will be available in `htmlcov/` directory.

## CI/CD Integration

The testing system is designed for easy CI/CD integration:

```yaml
# Example GitHub Actions workflow
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --dev
      - name: Start database
        run: make db-up
      - name: Run migrations
        run: make migrate
      - name: Run tests
        run: make test
      - name: Generate coverage
        run: make test-coverage
```

## Conclusion

The FinDoctor testing system provides comprehensive, reliable testing for all API endpoints. The system emphasizes:

- **Thoroughness**: Complete endpoint coverage with database verification
- **Flexibility**: Multiple ways to run tests based on needs
- **Reliability**: Isolated tests with proper cleanup
- **Security**: Verification of security measures (hashing, tokens)

For questions or issues, refer to the test output or check the specific test files for implementation details.