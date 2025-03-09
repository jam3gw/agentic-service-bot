# Testing Guidelines

## Directory Structure

The test suite for the agentic-service-bot project follows this structure:

```
tests/
├── e2e/                    # End-to-end tests
│   ├── test_api.py        # API endpoint tests
│   ├── test_chat.py       # Chat functionality tests
│   └── test_devices.py    # Device control tests
├── run_api_tests.py       # Test runner script
└── README.md              # This documentation
```

## Test Categories

1. **API Tests** (`test_api.py`)
   - Endpoint availability
   - Response formats
   - Error handling
   - Rate limiting
   - Authentication

2. **Chat Tests** (`test_chat.py`)
   - Message sending/receiving
   - Conversation history
   - Service level restrictions
   - Error scenarios

3. **Device Tests** (`test_devices.py`)
   - Device status retrieval
   - Power control
   - Volume control (Premium+)
   - Music control (Enterprise)
   - Service level enforcement

## Test Data Setup

The project includes a test data generation script that creates customers with different service levels:

```bash
python seed_test_data.py
```

This creates:
- Basic level test customer
- Premium level test customer
- Enterprise level test customer

Each test customer includes:
- Unique customer ID
- Test device (speaker)
- Appropriate service level permissions
- Sample playlist (for audio devices)

## Running Tests

### Full Test Suite
```bash
python tests/run_api_tests.py
```

### Specific Test Categories
```bash
# Test API endpoints
python tests/run_api_tests.py --test=api

# Test chat functionality
python tests/run_api_tests.py --test=chat

# Test device control
python tests/run_api_tests.py --test=devices
```

### Test Options
```bash
# Run with verbose logging
python tests/run_api_tests.py --verbose

# Run tests for a specific customer
python tests/run_api_tests.py --customer=test-premium-123

# Run tests with custom timeout
python tests/run_api_tests.py --timeout=30
```

## Test Writing Guidelines

1. **Test Organization**
   - Place tests in appropriate category files
   - Use descriptive test names
   - Include docstrings explaining test purpose

2. **Test Independence**
   - Each test should be self-contained
   - Clean up any created resources
   - Don't rely on other test results

3. **Service Level Testing**
   - Test both allowed and denied actions
   - Verify proper error messages
   - Test service level boundaries

4. **Error Handling**
   - Test both success and error cases
   - Verify error response formats
   - Test rate limiting behavior

Example test structure:
```python
def test_premium_customer_volume_control():
    """Test that premium customers can control device volume."""
    # Arrange
    customer_id = "test-premium-123"
    
    # Act
    response = set_device_volume(customer_id, 50)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify
    device = get_device_status(customer_id)
    assert device["volume"] == 50
```

## Test Environment

Tests require these environment variables:
```bash
export AWS_REGION="us-west-2"
export CUSTOMERS_TABLE="dev-customers"
export SERVICE_LEVELS_TABLE="dev-service-levels"
```

## Debugging Tests

1. Enable verbose logging:
```bash
python tests/run_api_tests.py --verbose
```

2. Check test data:
```bash
python seed_test_data.py --verify
```

3. Use the debug endpoint:
```bash
curl http://localhost:3000/api/debug/customer/{customerId}
```

## Test Reports

Test results are saved to:
- `tests/reports/test_results.json`: Detailed test results
- `tests/reports/coverage.xml`: Coverage report
- `tests/reports/test_log.txt`: Test execution log

## Continuous Integration

Tests are automatically run on:
- Pull request creation
- Push to main branch
- Daily scheduled runs

The CI pipeline:
1. Sets up test environment
2. Generates test data
3. Runs all tests
4. Publishes test reports
5. Checks test coverage

## Known Issues

1. **Rate Limiting**: Tests may fail if run too frequently due to API rate limits
   - Solution: Use `--delay` option to add delay between tests

2. **Test Data Cleanup**: Sometimes test data isn't properly cleaned up
   - Solution: Run `seed_test_data.py --cleanup` before tests

3. **Concurrent Tests**: Some tests may fail when run concurrently
   - Solution: Use `--sequential` option to run tests sequentially 