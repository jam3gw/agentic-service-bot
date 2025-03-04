# Integration Tests

This directory contains integration tests for the Agentic Service Bot project. Integration tests focus on testing interactions between multiple components.

## Test Files

- `test_process_request.py`: Tests for the request processing pipeline
- `test_ai_integration.py`: Tests for integration with AI services
- `test_websocket_handler.py`: Tests for the WebSocket handler
- `test_websocket_handlers.py`: Tests for multiple WebSocket handlers
- `test_websocket_connections.py`: Tests for WebSocket connection management

## Running Integration Tests

To run all integration tests:

```bash
python -m unittest discover -s tests/integration
```

Or using pytest:

```bash
pytest tests/integration/
```

To run a specific test file:

```bash
python -m unittest tests/integration/test_process_request.py
```

Or using pytest:

```bash
pytest tests/integration/test_process_request.py
```

## Prerequisites

Integration tests may require:

1. AWS credentials with appropriate permissions
2. Mocked AWS services (using moto)
3. Environment variables for configuration

## Writing Integration Tests

When writing integration tests, follow these guidelines:

1. Test interactions between multiple components
2. Use mocks for external services when appropriate
3. Include setup and teardown to create and clean up test resources
4. Use descriptive test method names that explain what is being tested
5. Include docstrings explaining the purpose of the test
6. Follow the Arrange-Act-Assert pattern

Example:

```python
@mock_dynamodb
def test_process_request_with_device_relocation(self):
    """Test processing a device relocation request.
    
    This test ensures the request processing pipeline correctly
    handles device relocation requests and updates the device
    location in DynamoDB.
    """
    # Arrange
    self.setup_dynamodb_tables()
    customer_id = "test_customer_id"
    self.create_test_customer(customer_id)
    request_text = "Move my smart speaker to the bedroom"
    
    # Act
    response = process_request(customer_id, request_text)
    
    # Assert
    self.assertIn("moved", response.lower())
    # Verify the device location was updated in DynamoDB
    customer = get_customer_by_id(customer_id)
    self.assertEqual(customer.devices[0]["location"], "bedroom")
```

## Mocking AWS Services

Many integration tests use the `moto` library to mock AWS services. This allows testing AWS interactions without actually making API calls to AWS.

Example:

```python
from moto import mock_dynamodb

@mock_dynamodb
def test_save_connection(self):
    # Create mock DynamoDB tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-connections',
        KeySchema=[{'AttributeName': 'connectionId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'connectionId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Test the function
    save_connection('conn-123', 'cust-456')
    
    # Verify the result
    response = table.get_item(Key={'connectionId': 'conn-123'})
    self.assertIn('Item', response)
    self.assertEqual(response['Item']['customerId'], 'cust-456')
``` 