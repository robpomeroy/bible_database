# Test Suite Documentation

This document describes the test suite for the Bible Database Python client.

## Overview

The test suite consists of both unit tests and integration tests. The unit tests
mock the database connection to ensure they can run without an actual database,
while the integration tests require a real database connection.

## Test Structure

The tests are organized into the following classes:

1. `TestBibleDatabase` - Tests for the core functionality of the `BibleDatabase` class
2. `TestBibleDatabaseBookMethods` - Tests for book-related methods
3. `TestBibleDatabaseReferenceParser` - Tests for reference parsing
4. `TestBibleDatabaseVerses` - Tests for fetching verses
5. `TestBibleDatabaseIntegration` - Integration tests with a real database

## Running the Tests

To run all tests:
```bash
python run_tests.py
```

To run with verbose output:
```bash
python run_tests.py -v
```

To run specific tests (e.g., only book-related tests):
```bash
python run_tests.py -k "book"
```

To run only integration tests:
```bash
python run_tests.py -m integration
```

### Pytest Configuration

The test suite uses two configuration files for pytest:

1. **pytest.ini**: Registers custom markers, including the `integration` marker
2. **conftest.py**: Contains shared pytest configuration 

These files help pytest recognize our custom markers and prevent warnings when running tests.

To add new markers, update both files:
```python
# In conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "mymarker: description of the marker")

# In pytest.ini
[pytest]
markers =
    integration: marks tests that require a real database connection
    mymarker: description of the marker
```

## Integration Tests

Integration tests require a database connection. By default, they are skipped.
To run these tests:

1. Copy `.env.test.example` to `.env.test`
2. Configure the database connection in `.env.test`
3. Set `SKIP_DB_INTEGRATION_TESTS=false` in `.env.test`
4. Run tests with one of these commands:
   ```bash
   # All tests will automatically include integration tests when SKIP_DB_INTEGRATION_TESTS=false
   python run_tests.py
   
   # To run ONLY the integration tests
   python run_tests.py -m integration
   ```

The integration tests connect to the database using the settings in `.env.test`.
Make sure your database is running and accessible with the Bible database schema
already loaded.

## Test Coverage

The test suite covers the following aspects of the `BibleDatabase` class:

### Core Functionality
- Initialization
- Connection and disconnection
- Context manager support
- SQL debugging
- Log level setting

### Book Methods
- Getting book number from name
- Getting book name from number
- Error handling for invalid books

### Reference Parsing
- Standard book chapter:verse references
- Chapterless book references
- Verse ranges
- Chapter ranges
- Invalid reference handling

### Verse Retrieval
- Getting single verses
- Getting verse ranges
- Handling empty references
- Handling non-existent translations
- Handling no results

### Available Translations
- Getting all available translations
- Handling database errors

## Adding New Tests

When adding new tests:

1. Use the appropriate test class based on the functionality being tested
2. Follow the existing patterns for mocking database connections and cursors
3. For unit tests, ensure they don't depend on a database connection
4. For integration tests, use the `@pytest.mark.integration` decorator

## Mocking Strategy

The test suite uses the `unittest.mock` module to mock the database connection and cursor.
This allows testing database operations without an actual database connection.

The main fixtures are:

- `mock_connection` - Provides a mock connection and cursor
- `bible_db` - Provides a `BibleDatabase` instance with mocked connections

For integration tests, the `real_db` fixture provides a real database connection.
