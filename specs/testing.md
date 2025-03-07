# Testing

## Overview

The Agentic Service Bot implements a comprehensive testing strategy to ensure reliability, functionality, and performance. This document outlines the testing approach, methodologies, and tools used across the project, with a particular focus on end-to-end testing in the AWS development environment.

## Testing Levels

### Unit Testing

**Purpose**: Test individual components in isolation.

**Tools**:
- Python: pytest
- TypeScript/JavaScript: Jest

**Coverage Targets**:
- Backend: 80% code coverage
- Frontend: 70% code coverage

**Key Areas**:
- Lambda function logic
- Request analysis algorithms
- Permission checking
- React component rendering
- WebSocket connection handling

### Integration Testing

**Purpose**: Test interactions between components.

**Tools**:
- Python: pytest with moto for AWS service mocking
- TypeScript/JavaScript: Jest with mock service workers

**Key Areas**:
- DynamoDB interactions
- WebSocket message handling
- Claude API integration
- Frontend-backend communication

### End-to-End Testing

**Purpose**: Test the complete application flow in a real AWS environment.

**Tools**:
- AWS SDK for direct service interaction
- Cypress for frontend testing
- Postman/Newman for API testing
- Custom Python test framework for orchestration

**Key Areas**:
- Complete user journeys across service tiers
- WebSocket connection and messaging
- Error handling and recovery
- Cross-browser compatibility
- Real AWS service interactions
- Claude API integration with real credentials

## Testing Environments

### Local Development

- Local DynamoDB instance
- Mocked AWS services
- Mocked Claude API
- WebSocket server running locally

### Development Environment

The development environment serves as our primary testing environment:

- Deployed using the existing AWS CDK infrastructure in the dev account
- Uses the `AgenticServiceBotDevApi` and `AgenticServiceBotDevFrontend` stacks
- Pre-loaded with test data in DynamoDB tables
- Isolated from production
- Real Claude API integration with test API keys
- Automated test suite execution
- Monitoring and logging enabled

**Key Components**:
- API Gateway with WebSocket support
- Lambda functions for request processing
- DynamoDB tables for data storage
- CloudWatch for logging and monitoring
- IAM roles and policies for secure access
- S3 buckets for frontend hosting

### Production-Like Staging

- Mirror of production environment
- Full-scale infrastructure
- Realistic data volumes
- Pre-production validation

## End-to-End Testing in AWS Development Environment

### Leveraging Existing Infrastructure

Our end-to-end tests utilize the existing development environment infrastructure deployed via CDK. The development environment includes:

- WebSocket API Gateway
- Lambda functions
- DynamoDB tables (customers, service levels, messages, connections)
- IAM roles and permissions
- CloudWatch logging

This approach eliminates the need for a separate test environment, reducing infrastructure costs and maintenance overhead.

### Test Data Setup

```python
# Example script for populating test data in the dev environment
import boto3
import json
import uuid
from datetime import datetime

def populate_test_data():
    """Populate DynamoDB tables with test data for end-to-end testing."""
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    
    # Get table references
    customers_table = dynamodb.Table('dev-customers')
    service_levels_table = dynamodb.Table('dev-service-levels')
    
    # Clear existing data
    clear_table(customers_table)
    clear_table(service_levels_table)
    
    # Add service levels
    service_levels = [
        {
            'level': 'basic',
            'allowed_actions': [
                'status_check',
                'volume_control',
                'device_info'
            ],
            'max_devices': 1,
            'support_priority': 'standard'
        },
        {
            'level': 'premium',
            'allowed_actions': [
                'status_check',
                'volume_control',
                'device_info',
                'device_relocation',
                'music_services'
            ],
            'max_devices': 1,
            'support_priority': 'high'
        },
        {
            'level': 'enterprise',
            'allowed_actions': [
                'status_check',
                'volume_control',
                'device_info',
                'device_relocation',
                'music_services',
                'multi_room_audio',
                'custom_actions'
            ],
            'max_devices': 1,
            'support_priority': 'dedicated'
        }
    ]
    
    for level in service_levels:
        service_levels_table.put_item(Item=level)
        print(f"Added service level: {level['level']}")
    
    # Add test customers
    customers = [
        {
            'id': 'cust_basic_001',
            'name': 'Jane Smith',
            'service_level': 'basic',
            'devices': [
                {
                    'id': 'dev_001',
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                }
            ]
        },
        {
            'id': 'cust_premium_001',
            'name': 'John Doe',
            'service_level': 'premium',
            'devices': [
                {
                    'id': 'dev_002',
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                },
                {
                    'id': 'dev_003',
                    'type': 'SmartDisplay',
                    'location': 'kitchen'
                }
            ]
        },
        {
            'id': 'cust_enterprise_001',
            'name': 'Alice Johnson',
            'service_level': 'enterprise',
            'devices': [
                {
                    'id': 'dev_004',
                    'type': 'SmartSpeaker',
                    'location': 'office'
                },
                {
                    'id': 'dev_005',
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                },
                {
                    'id': 'dev_006',
                    'type': 'SmartSpeaker',
                    'location': 'bedroom'
                },
                {
                    'id': 'dev_007',
                    'type': 'SmartDisplay',
                    'location': 'kitchen'
                }
            ]
        }
    ]
    
    for customer in customers:
        customers_table.put_item(Item=customer)
        print(f"Added customer: {customer['name']} ({customer['service_level']})")

def clear_table(table):
    """Clear all items from a DynamoDB table."""
    # Get the table's key schema
    key_names = [key['AttributeName'] for key in table.key_schema]
    
    # Scan the table
    scan = table.scan()
    with table.batch_writer() as batch:
        for item in scan['Items']:
            key = {key_name: item[key_name] for key_name in key_names}
            batch.delete_item(Key=key)
    
    print(f"Cleared table: {table.name}")

if __name__ == '__main__':
    populate_test_data()
```

### End-to-End Test Suite

```python
# Example end-to-end test suite for AWS development environment
import unittest
import boto3
import json
import websocket
import threading
import time
import uuid
from datetime import datetime

class AgenticServiceBotE2ETest(unittest.TestCase):
    """End-to-end tests for the Agentic Service Bot in AWS development environment."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        # Get WebSocket URL from CloudFormation outputs
        cloudformation = boto3.client('cloudformation')
        stack_outputs = cloudformation.describe_stacks(StackName='AgenticServiceBotDevApi')['Stacks'][0]['Outputs']
        cls.websocket_url = next(output['OutputValue'] for output in stack_outputs if output['OutputKey'] == 'WebSocketURL')
        
        # Initialize DynamoDB client
        cls.dynamodb = boto3.resource('dynamodb')
        cls.customers_table = cls.dynamodb.Table('dev-customers')
        cls.messages_table = cls.dynamodb.Table('dev-messages')
        
        # Test data
        cls.basic_customer_id = 'cust_basic_001'
        cls.premium_customer_id = 'cust_premium_001'
        cls.enterprise_customer_id = 'cust_enterprise_001'
        
        # WebSocket connection and message handling
        cls.received_messages = []
        cls.ws = None
    
    def setUp(self):
        """Set up test fixtures before each test."""
        # Clear received messages
        self.__class__.received_messages = []
        
        # Connect to WebSocket
        self.connect_websocket()
    
    def tearDown(self):
        """Tear down test fixtures after each test."""
        # Close WebSocket connection
        if self.__class__.ws and self.__class__.ws.connected:
            self.__class__.ws.close()
    
    def connect_websocket(self):
        """Connect to the WebSocket API."""
        # Define WebSocket callbacks
        def on_message(ws, message):
            self.__class__.received_messages.append(json.loads(message))
            print(f"Received message: {message}")
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket closed: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            print("WebSocket connection established")
        
        # Create WebSocket connection
        self.__class__.ws = websocket.WebSocketApp(
            self.__class__.websocket_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Start WebSocket connection in a separate thread
        wst = threading.Thread(target=self.__class__.ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Wait for connection to establish
        time.sleep(2)
    
    def send_message(self, customer_id, message_text):
        """Send a message through the WebSocket connection."""
        message = {
            'action': 'message',
            'customerId': customer_id,
            'message': message_text
        }
        self.__class__.ws.send(json.dumps(message))
        
        # Wait for response
        time.sleep(5)
    
    def test_basic_customer_allowed_action(self):
        """Test a basic customer requesting an allowed action."""
        # Send a message for a basic customer requesting device info (allowed)
        self.send_message(self.basic_customer_id, "What are the specs of my smart speaker?")
        
        # Verify response
        self.assertTrue(len(self.__class__.received_messages) > 0)
        last_message = self.__class__.received_messages[-1]
        self.assertIn('message', last_message)
        self.assertNotIn("I'm sorry", last_message['message'])
        self.assertNotIn("service level doesn't allow", last_message['message'])
    
    def test_basic_customer_disallowed_action(self):
        """Test a basic customer requesting a disallowed action."""
        # Send a message for a basic customer requesting device relocation (not allowed)
        self.send_message(self.basic_customer_id, "Move my speaker to the bedroom")
        
        # Verify response
        self.assertTrue(len(self.__class__.received_messages) > 0)
        last_message = self.__class__.received_messages[-1]
        self.assertIn('message', last_message)
        self.assertIn("I'm sorry", last_message['message'])
        self.assertIn("service level doesn't allow", last_message['message'])
    
    def test_premium_customer_allowed_action(self):
        """Test a premium customer requesting an allowed action."""
        # Send a message for a premium customer requesting device relocation (allowed)
        self.send_message(self.premium_customer_id, "Move my speaker to the bedroom")
        
        # Verify response
        self.assertTrue(len(self.__class__.received_messages) > 0)
        last_message = self.__class__.received_messages[-1]
        self.assertIn('message', last_message)
        self.assertNotIn("I'm sorry", last_message['message'])
        self.assertNotIn("service level doesn't allow", last_message['message'])
    
    def test_premium_customer_disallowed_action(self):
        """Test a premium customer requesting a disallowed action."""
        # Send a message for a premium customer requesting multi-room audio (not allowed)
        self.send_message(self.premium_customer_id, "Play the same music on all my speakers")
        
        # Verify response
        self.assertTrue(len(self.__class__.received_messages) > 0)
        last_message = self.__class__.received_messages[-1]
        self.assertIn('message', last_message)
        self.assertIn("I'm sorry", last_message['message'])
        self.assertIn("service level doesn't allow", last_message['message'])
    
    def test_enterprise_customer_all_actions(self):
        """Test an enterprise customer requesting various actions."""
        # Test device info (allowed)
        self.send_message(self.enterprise_customer_id, "What are the specs of my smart speaker?")
        self.assertTrue(len(self.__class__.received_messages) > 0)
        last_message = self.__class__.received_messages[-1]
        self.assertNotIn("I'm sorry", last_message['message'])
        
        # Test device relocation (allowed)
        self.send_message(self.enterprise_customer_id, "Move my speaker to the dining room")
        self.assertTrue(len(self.__class__.received_messages) > 0)
        last_message = self.__class__.received_messages[-1]
        self.assertNotIn("I'm sorry", last_message['message'])
        
        # Test multi-room audio (allowed)
        self.send_message(self.enterprise_customer_id, "Play the same music on all my speakers")
        self.assertTrue(len(self.__class__.received_messages) > 0)
        last_message = self.__class__.received_messages[-1]
        self.assertNotIn("I'm sorry", last_message['message'])
        
        # Test custom routine (allowed)
        self.send_message(self.enterprise_customer_id, "Create a routine to turn on my living room speaker at 7am")
        self.assertTrue(len(self.__class__.received_messages) > 0)
        last_message = self.__class__.received_messages[-1]
        self.assertNotIn("I'm sorry", last_message['message'])
    
    def test_conversation_history(self):
        """Test that conversation history is properly stored in DynamoDB."""
        # Generate a unique customer ID for this test
        test_customer_id = f"test_customer_{uuid.uuid4().hex[:8]}"
        
        # Add test customer to DynamoDB
        self.customers_table.put_item(Item={
            'id': test_customer_id,
            'name': 'Test Customer',
            'service_level': 'basic',
            'devices': [
                {
                    'id': f"dev_{uuid.uuid4().hex[:8]}",
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                }
            ]
        })
        
        # Send a series of messages
        messages = [
            "Hello, I need help with my smart speaker",
            "What's the volume level?",
            "Can you increase the volume?"
        ]
        
        for message in messages:
            self.send_message(test_customer_id, message)
            time.sleep(2)  # Wait for processing
        
        # Query DynamoDB for conversation history
        response = self.messages_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('userId').eq(test_customer_id)
        )
        
        # Verify that all messages are stored
        stored_messages = [item for item in response['Items'] if item['sender'] == 'user']
        self.assertEqual(len(stored_messages), len(messages))
        
        # Verify message content
        stored_message_texts = [item['message'] for item in stored_messages]
        for message in messages:
            self.assertIn(message, stored_message_texts)

if __name__ == '__main__':
    unittest.main()
```

## Test Automation

### Continuous Integration

- Tests run automatically on every pull request
- All tests must pass before merging
- Code coverage reports generated and tracked
- Test results published to dashboard

### GitHub Actions Workflow for E2E Testing

```yaml
# GitHub Actions workflow for running end-to-end tests against the dev environment
name: End-to-End Tests

on:
  push:
    branches: [ develop, main ]
  pull_request:
    branches: [ develop, main ]
  workflow_dispatch:

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install boto3 websocket-client pytest pytest-html
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      
      - name: Prepare test data
        run: |
          python tests/e2e/prepare_test_data.py
      
      - name: Run end-to-end tests
        run: |
          pytest tests/e2e/test_e2e.py -v --html=e2e-test-report.html
      
      - name: Upload test report
        uses: actions/upload-artifact@v2
        with:
          name: e2e-test-report
          path: e2e-test-report.html
```

## Business Value of End-to-End Testing

End-to-end testing in the AWS development environment provides critical business value by:

1. **Validating Real-World Behavior**: Tests the application as customers will experience it
2. **Ensuring Service Level Enforcement**: Verifies that service tier permissions are correctly enforced
3. **Detecting Integration Issues**: Identifies problems that only appear when all components work together
4. **Validating AWS Infrastructure**: Ensures the CDK deployment creates a working environment
5. **Reducing Production Incidents**: Catches issues before they reach customers
6. **Supporting Continuous Deployment**: Provides confidence for frequent releases
7. **Documenting Expected Behavior**: Serves as executable documentation of system capabilities

## Test Reporting and Monitoring

- Test results stored in CloudWatch Logs
- Custom CloudWatch Dashboard for test metrics
- Automated Slack notifications for test failures
- Weekly test coverage and success rate reports
- Integration with AWS X-Ray for performance analysis

## WebSocket Connection Testing

WebSocket connections are a critical part of the chat functionality in the Agentic Service Bot. The following tests should be implemented to ensure proper functionality:

### Unit Tests

1. **Request Analyzer Tests**
   - Test that the request analyzer correctly identifies different types of requests
   - Test that the request analyzer extracts the correct information from requests
   - Test that the request analyzer returns the correct required actions for each request type
   - Ensure device control requests are properly identified with various phrasings

2. **Service Level Permission Tests**
   - Test that service level permissions are correctly enforced for different request types
   - Test that basic tier customers can perform allowed actions (status check, volume control, device info, device control)
   - Test that basic tier customers cannot perform restricted actions (device relocation, music services, multi-room audio, custom actions)
   - Test similar permission checks for premium and enterprise tiers

3. **WebSocket Handler Tests**
   - Test that the WebSocket handler correctly processes messages
   - Test that the WebSocket handler correctly enforces service level permissions
   - Test that the WebSocket handler correctly generates responses based on service level permissions
   - Test connection establishment and disconnection handling

### Integration Tests

1. **End-to-End Flow Tests**
   - Test the complete flow from connection to message processing to response
   - Test with different customer service levels to ensure permissions are correctly enforced
   - Test with different request types to ensure proper handling
   - Test error scenarios and edge cases

2. **Service Level Enforcement Tests**
   - Test that a basic tier customer can control devices
   - Test that a basic tier customer cannot relocate devices
   - Test that a premium tier customer can control and relocate devices
   - Test that a premium tier customer cannot set up multi-room audio
   - Test that an enterprise tier customer can perform all actions

### Test Scenarios

| Test Case | Service Level | Request | Expected Result |
|-----------|---------------|---------|-----------------|
| Device Control - Basic | Basic | "Turn off my living room light" | Success - Action allowed |
| Device Relocation - Basic | Basic | "Move my speaker to the kitchen" | Failure - Action not allowed |
| Device Control - Premium | Premium | "Turn on the kitchen lights" | Success - Action allowed |
| Device Relocation - Premium | Premium | "Move my display to the bedroom" | Success - Action allowed |
| Multi-Room Audio - Premium | Premium | "Play music in all rooms" | Failure - Action not allowed |
| Device Control - Enterprise | Enterprise | "Turn off all lights" | Success - Action allowed |
| Multi-Room Audio - Enterprise | Enterprise | "Sync music across all speakers" | Success - Action allowed |

These tests ensure that the chat service correctly enforces service level permissions and provides appropriate responses to users based on their service level.

## Conclusion

End-to-end testing in the AWS development environment is a critical part of our testing strategy. By testing the complete system with real AWS services, we can ensure that the Agentic Service Bot functions correctly and provides value to customers across all service tiers. 