# Testing Guidelines

## Directory Structure

All tests for the agentic-service-bot project must be placed in this `tests` directory, following this simplified structure:

```
tests/
└── e2e/                  # End-to-end tests for complete workflows
    ├── test_api_endpoints.py    # Tests for REST API endpoints
    ├── test_websocket_chat.py   # Tests for WebSocket chat functionality
    └── README_WEBSOCKET.md      # Documentation for WebSocket tests
```

## Testing Rules

1. **All test files must be placed in the `tests` directory**
   - No test files should be created in the main application directories
   - This ensures consistent test discovery and organization

2. **Test file naming**
   - All test files must be named with the prefix `test_`
   - Example: `test_user_workflow.py`

3. **Test organization**
   - End-to-end tests go in the `e2e/` directory
   - Additional test categories can be added as the project evolves

4. **Testing approach**
   - Tests should use real dependencies whenever possible
   - End-to-end tests should never use mocks
   - Each test file should be self-contained and not rely on external fixtures

## Running Tests

To run all tests:
```bash
pytest tests/
```

To run end-to-end tests:
```bash
pytest tests/e2e/
```

To run a specific test file:
```bash
pytest tests/e2e/test_user_workflow.py
```

## WebSocket Testing

The project includes end-to-end tests for the WebSocket chat functionality. These tests verify:

1. **Connection Establishment**: Tests that WebSocket connections can be established with proper customer authentication.
2. **Message Exchange**: Tests sending messages and receiving responses through the WebSocket connection.
3. **Device Control**: Tests that device control commands sent via WebSocket properly update device states in DynamoDB.

### WebSocket Test Configuration

WebSocket tests require the following environment variables:

```bash
export WEBSOCKET_URL="wss://your-api-id.execute-api.us-east-1.amazonaws.com/test"
export AWS_REGION="us-east-1"
export CUSTOMERS_TABLE="test-customers"
```

For more details on WebSocket testing, see the [WebSocket Testing README](e2e/README_WEBSOCKET.md).

### Manual WebSocket Testing

For manual testing of the WebSocket functionality, use the provided Node.js script:

```bash
node infrastructure/test-websocket.js "wss://your-api-id.execute-api.us-east-1.amazonaws.com/test" "your-customer-id"
``` 