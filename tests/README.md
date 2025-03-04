# Agentic Service Bot Testing Guide

This directory contains tests for the Agentic Service Bot project, organized into different categories based on their scope and purpose.

## Test Structure

The tests are organized into the following directories:

- **Unit Tests** (`unit/`): Tests for individual components and functions in isolation
- **Integration Tests** (`integration/`): Tests for interactions between multiple components
- **End-to-End Tests** (`e2e/`): Tests for complete user journeys in a real AWS environment

## Prerequisites

Before running the tests, ensure you have the following:

1. Python 3.9 or higher installed
2. Required Python packages installed:
   ```
   pip install -r requirements-dev.txt
   ```
3. AWS credentials configured for the development environment (for integration and E2E tests)
4. The AWS CDK stack deployed to the development environment (for E2E tests)

## Running Tests

### Running All Tests

To run all tests, use the provided `run_tests.py` script:

```bash
python tests/run_tests.py
```

This will discover and run all tests in the `tests` directory.

### Running Specific Test Categories

#### Unit Tests

To run only the unit tests:

```bash
python -m unittest discover -s tests/unit
```

#### Integration Tests

To run only the integration tests:

```bash
python -m unittest discover -s tests/integration
```

#### End-to-End Tests

To run the end-to-end tests, you need to have the AWS CDK stack deployed to the development environment:

```bash
python -m unittest discover -s tests/e2e
```

Note: E2E tests require AWS credentials with appropriate permissions.

### Running Individual Test Files

To run a specific test file:

```bash
python -m unittest tests/path/to/test_file.py
```

### Running with pytest

You can also use pytest to run the tests with more detailed output:

```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run specific test file
pytest tests/path/to/test_file.py

# Run with verbose output
pytest -v tests/

# Run with coverage report
pytest --cov=lambda tests/
```

## Test Data Setup

For E2E tests, you may need to prepare test data in the development environment. Use the provided script:

```bash
python tests/e2e/prepare_test_data.py
```

This script will populate the DynamoDB tables in the development environment with test data required for the E2E tests.

## WebSocket Testing

The E2E tests include WebSocket connection testing. These tests connect to the WebSocket API in the development environment and verify that messages are correctly processed and responses are received.

To run only the WebSocket tests:

```bash
pytest tests/e2e/test_e2e.py::AgenticServiceBotE2ETest::test_basic_customer_allowed_action
```

## Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure your AWS credentials are correctly configured with the necessary permissions.

2. **WebSocket Connection Failures**: If WebSocket tests fail with connection errors, verify that the WebSocket API is deployed and accessible.

3. **DynamoDB Access**: Ensure your AWS credentials have access to the DynamoDB tables in the development environment.

4. **Timeouts**: E2E tests may time out if the Lambda functions are experiencing cold starts. Try running the tests again or increase the timeout values in the test code.

### Logs

For detailed logs during test execution, set the log level to DEBUG:

```bash
export LOG_LEVEL=DEBUG
python tests/run_tests.py
```

## Adding New Tests

When adding new tests, follow these guidelines:

1. Place tests in the appropriate directory based on their scope (unit, integration, or E2E).
2. Follow the naming convention: `test_*.py` for test files and `test_*` for test methods.
3. Include docstrings explaining the purpose of the test and the business value it provides.
4. Use flexible assertions for text validation to handle variations in wording.
5. Set appropriate timeouts for asynchronous operations.
6. Include proper cleanup in `tearDown` methods to avoid leaving test data in the development environment.

## CI/CD Integration

The tests are automatically run as part of the CI/CD pipeline. See the GitHub Actions workflow files in the `.github/workflows` directory for details. 