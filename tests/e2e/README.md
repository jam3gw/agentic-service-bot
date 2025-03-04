# End-to-End Tests

This directory contains end-to-end (E2E) tests for the Agentic Service Bot project. E2E tests focus on testing complete user journeys in a real AWS environment.

## Test Files

- `test_e2e.py`: Tests for complete user journeys across different service tiers
- `prepare_test_data.py`: Script to populate test data in the development environment

## Running E2E Tests

To run all E2E tests:

```bash
python -m unittest discover -s tests/e2e
```

Or using pytest:

```bash
pytest tests/e2e/
```

To run a specific test method:

```bash
python -m unittest tests/e2e/test_e2e.py:AgenticServiceBotE2ETest.test_basic_customer_allowed_action
```

Or using pytest:

```bash
pytest tests/e2e/test_e2e.py::AgenticServiceBotE2ETest::test_basic_customer_allowed_action
```

## Prerequisites

E2E tests require:

1. AWS credentials with appropriate permissions
2. The AWS CDK stack deployed to the development environment
3. Test data populated in the DynamoDB tables

## Preparing Test Data

Before running the E2E tests, you need to populate the development environment with test data:

```bash
python tests/e2e/prepare_test_data.py
```

This script will:

1. Create service level definitions in the `dev-service-levels` table
2. Create test customers with different service levels in the `dev-customers` table
3. Set up test devices for each customer

## WebSocket Testing

The E2E tests include WebSocket connection testing. These tests:

1. Connect to the WebSocket API in the development environment
2. Send messages to the bot
3. Verify that responses are received
4. Check that service level permissions are enforced

The WebSocket connection is managed by the `connect_websocket` and `send_message` methods in the `AgenticServiceBotE2ETest` class.

## Test Timeouts

E2E tests involve real AWS services, which can sometimes be slow to respond, especially during Lambda cold starts. The tests include appropriate timeouts to handle these delays:

- Connection timeout: 10 seconds
- Initial response timeout: 10 seconds
- Maximum wait time for response: 60 seconds

If tests are timing out, you may need to increase these values in the test code.

## Writing E2E Tests

When writing E2E tests, follow these guidelines:

1. Test complete user journeys
2. Include setup and teardown to create and clean up test resources
3. Use descriptive test method names that explain what is being tested
4. Include docstrings explaining the purpose of the test
5. Use flexible assertions for text validation to handle variations in wording
6. Include proper error handling and logging

Example:

```python
def test_premium_customer_allowed_action(self):
    """Test a premium customer requesting an allowed action.
    
    This test verifies that customers with premium service level
    can perform actions that are allowed for their service level,
    such as device relocation.
    """
    # Send a message for a premium customer requesting device relocation (allowed)
    response = self.send_message(self.premium_customer_id, "Move my speaker to the bedroom")
    
    # Verify response
    self.assertIn('message', response, f"Response does not contain 'message' field: {response}")
    
    # Check for various ways the success might be expressed
    success_phrases = ["moved", "relocated", "now in", "placed in"]
    message_text = response['message'].lower()
    
    self.assertTrue(
        any(phrase in message_text for phrase in success_phrases),
        f"Response should indicate successful relocation, but got: {response['message']}"
    )
    
    # Verify that the response does not indicate the action was disallowed
    self.assertNotIn("not allowed", message_text)
    self.assertNotIn("don't have permission", message_text)
    self.assertNotIn("service level doesn't allow", message_text)
```

## Logging

The E2E tests include comprehensive logging to help diagnose issues. You can increase the log level for more detailed output:

```bash
export LOG_LEVEL=DEBUG
python -m unittest tests/e2e/test_e2e.py
```

## Cleanup

The E2E tests include cleanup code in the `tearDown` method to remove test data from the development environment. This helps prevent test data from accumulating over time. 