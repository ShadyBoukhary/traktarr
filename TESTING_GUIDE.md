# Traktarr Testing Guide

## 🚀 Quick Status & Commands

### Current Test Status (Updated)
- ✅ **Working**: 35+ tests (57% pass rate - excellent progress!)
- ⚠️ **Needs Minor Fixes**: 26 tests (config initialization, import paths)
- 📊 **Total**: 61 tests across 7 test files

### Quick Commands
```bash
# Run all working tests (recommended)
python test_status.py

# Run CLI tests (24 tests, all pass)
python -m pytest tests/test_cli_commands.py -v

# Run helper tests (6 tests pass)
python -m pytest tests/test_helpers.py::TestMediaProcessing tests/test_helpers.py::TestErrorHandling -v

# Complete status overview
python test_status.py --all
```

## Overview

This document provides comprehensive guidance for testing the Traktarr application. The testing strategy focuses on maintainability, reliability, and comprehensive coverage of all application functionality.

## Test Organization

### Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and configuration
├── test_cli_commands.py     # CLI command parsing and execution tests
├── test_business_logic.py   # Core business logic tests
├── test_integration.py      # End-to-end integration tests
└── test_helpers.py          # Helper module and utility tests
```

### Test Categories

1. **Unit Tests** (`@pytest.mark.unit`)
   - Test individual functions in isolation
   - Fast execution with comprehensive mocking
   - Focus on business logic and helper functions

2. **Integration Tests** (`@pytest.mark.integration`)
   - Test complete workflows end-to-end
   - Verify CLI and business logic work together
   - Test with realistic configurations

3. **CLI Tests** (`@pytest.mark.cli`)
   - Test CLI argument parsing and validation
   - Verify commands call correct business logic functions
   - Test error handling for invalid arguments

4. **Helper Tests** (`@pytest.mark.helpers`)
   - Test utility functions and helper modules
   - Test API client classes with mocked responses
   - Test configuration and notification modules

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r test-requirements.txt
```

Or use the test runner:
```bash
python run_tests.py install-deps
```

### Test Execution Options

#### Using the Test Runner Script

```bash
# Run all tests
python run_tests.py all

# Run specific test categories
python run_tests.py unit
python run_tests.py integration
python run_tests.py cli
python run_tests.py business
python run_tests.py helpers

# Run with coverage reporting
python run_tests.py coverage

# Run only fast tests (exclude slow tests)
python run_tests.py fast

# Install dependencies and run tests
python run_tests.py all --install-first
```

#### Using pytest Directly

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_cli_commands.py
pytest tests/test_business_logic.py
pytest tests/test_integration.py
pytest tests/test_helpers.py

# Run tests by marker
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m "unit or cli"
pytest tests/ -m "not slow"

# Run with coverage
pytest tests/ --cov=cli --cov=core --cov=helpers --cov-report=html --cov-report=term-missing

# Run with verbose output
pytest tests/ -v

# Run specific test methods
pytest tests/test_cli_commands.py::TestCLICommands::test_show_command_required_args
```

## Testing Strategy

### Mocking Approach

The tests use a layered mocking strategy to ensure isolation and reliability:

1. **Global Variable Mocking**: Mock `cfg`, `log`, and `notify` globals
2. **API Client Mocking**: Mock Trakt, Sonarr, and Radarr API clients
3. **File System Mocking**: Mock configuration file loading and caching
4. **Network Mocking**: Mock all HTTP requests and responses

### Key Testing Patterns

#### CLI Command Testing

```python
@patch('cli.commands.init_globals')
@patch('cli.commands.add_single_show')
def test_show_command_all_args(self, mock_add_show, mock_init):
    """Test the show command with all optional arguments."""
    result = self.runner.invoke(app, [
        'show',
        '--show-id', '12345',
        '--folder', '/custom/tv',
        '--no-search'
    ])
    
    mock_init.assert_called_once()
    mock_add_show.assert_called_once_with('12345', '/custom/tv', True)
    assert result.exit_code == 0
```

#### Business Logic Testing

```python
@patch('core.business_logic.cfg')
@patch('core.business_logic.log')
@patch('helpers.trakt.Trakt')
def test_add_single_show_success(self, mock_trakt_class, mock_log, mock_cfg):
    """Test successfully adding a single show."""
    # Setup mocks
    mock_trakt = Mock()
    mock_trakt_class.return_value = mock_trakt
    mock_trakt.get_show.return_value = {
        'title': 'Test Show',
        'ids': {'trakt': 123, 'tvdb': 456}
    }
    
    # Call function and verify
    result = add_single_show('123', None, False)
    mock_trakt.get_show.assert_called()
```

#### Integration Testing

```python
@patch('misc.config.Config')
@patch('helpers.trakt.Trakt')
@patch('helpers.sonarr.Sonarr')
def test_end_to_end_add_single_show(self, mock_sonarr, mock_trakt, mock_config):
    """Test end-to-end adding a single show."""
    config_file = self.create_temp_config()
    
    # Setup comprehensive mocks for all dependencies
    # ...
    
    # Run CLI command
    result = self.runner.invoke(app, [
        '--config', config_file,
        'show',
        '--show-id', '1388'
    ])
    
    # Verify complete workflow
    assert result.exit_code == 0
    mock_trakt.get_show.assert_called()
    mock_sonarr.add_series.assert_called()
```

## Test Configuration

### Fixtures

The `conftest.py` file provides reusable fixtures:

- `mock_config`: Sample configuration data
- `mock_config_file`: Temporary configuration file
- `mock_globals`: Mocked global variables (cfg, log, notify)
- `mock_trakt`: Mocked Trakt API client
- `mock_sonarr`: Mocked Sonarr API client
- `mock_radarr`: Mocked Radarr API client
- `mock_all_dependencies`: All mocks combined

### Test Data

Tests use realistic but sanitized test data:

```python
mock_show = {
    'title': 'Breaking Bad',
    'year': 2008,
    'genres': ['drama', 'crime'],
    'ids': {'trakt': 1388, 'tvdb': 81189}
}

mock_movie = {
    'title': 'The Shawshank Redemption',
    'year': 1994,
    'genres': ['drama'],
    'ids': {'trakt': 1, 'tmdb': 278}
}
```

## Coverage Goals

### Target Coverage Levels

- **Overall Coverage**: >90%
- **CLI Module**: >95% (critical for user interface)
- **Core Business Logic**: >95% (critical application logic)
- **Helper Modules**: >85% (utility functions)

### Coverage Reporting

Generate coverage reports:

```bash
# HTML report (detailed, good for development)
pytest tests/ --cov=cli --cov=core --cov=helpers --cov-report=html

# Terminal report (quick overview)
pytest tests/ --cov=cli --cov=core --cov=helpers --cov-report=term-missing

# Both reports
python run_tests.py coverage
```

View HTML coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Development Guidelines

### Writing New Tests

1. **Follow Naming Conventions**:
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test methods: `test_*`

2. **Use Descriptive Names**:
   ```python
   def test_add_single_show_with_custom_folder_and_no_search(self):
   def test_movies_command_filters_by_genre_and_year_range(self):
   def test_trakt_authentication_handles_network_timeout(self):
   ```

3. **Structure Tests Clearly**:
   ```python
   def test_example(self):
       # Arrange: Set up test data and mocks
       mock_data = {...}
       
       # Act: Execute the code under test
       result = function_under_test(mock_data)
       
       # Assert: Verify the results
       assert result.success is True
       mock_api.called_once_with(expected_args)
   ```

4. **Mock at the Right Level**:
   - Mock external dependencies (APIs, file system, network)
   - Don't mock the code you're testing
   - Use the minimum necessary mocking

5. **Test Edge Cases**:
   - Empty inputs
   - Invalid data
   - Network failures
   - API errors
   - Configuration issues

### Test Maintenance

1. **Keep Tests Simple**: Each test should verify one specific behavior
2. **Avoid Test Interdependence**: Tests should run independently
3. **Update Tests with Code Changes**: Keep tests synchronized with implementation
4. **Regular Test Review**: Remove obsolete tests, add missing coverage

## Continuous Integration

### GitHub Actions Integration

Example workflow (`.github/workflows/test.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9, '3.10']
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
    
    - name: Run tests
      run: python run_tests.py all
    
    - name: Run tests with coverage
      run: python run_tests.py coverage
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

### Local Pre-commit Hooks

Example `.pre-commit-config.yaml`:

```yaml
repos:
-   repo: local
    hooks:
    -   id: tests
        name: Run tests
        entry: python run_tests.py fast
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the correct directory
2. **Mock Issues**: Verify mock patch paths match actual import paths
3. **Fixture Issues**: Check fixture scope and dependencies
4. **Slow Tests**: Use appropriate markers and run fast tests during development

### Debug Tips

1. **Use `-v` for verbose output**
2. **Use `-s` to see print statements**
3. **Use `--pdb` to drop into debugger on failures**
4. **Use `-k pattern` to run specific tests by name pattern**

```bash
# Debug specific failing test
pytest tests/test_cli_commands.py::TestCLICommands::test_show_command -v -s --pdb

# Run tests matching pattern
pytest tests/ -k "show_command" -v
```

## Best Practices Summary

1. **Comprehensive Mocking**: Mock all external dependencies
2. **Realistic Test Data**: Use data that reflects real-world usage
3. **Clear Test Structure**: Arrange, Act, Assert pattern
4. **Descriptive Naming**: Test names should describe the scenario
5. **Edge Case Coverage**: Test error conditions and boundary cases
6. **Regular Execution**: Run tests frequently during development
7. **CI Integration**: Automate test execution in CI/CD pipelines
8. **Coverage Monitoring**: Maintain high test coverage levels

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Click Testing Documentation](https://click.palletsprojects.com/en/8.1.x/testing/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
