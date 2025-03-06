"""
Local test script for the chat Lambda function.

This script allows you to test the Lambda function locally without deploying to AWS.
It simulates an API Gateway event and passes it to the Lambda handler.
"""

import json
import os
import sys
from typing import Dict, Any

# Set environment variables for local testing
os.environ['CUSTOMERS_TABLE'] = 'agentic-service-bot-dev-customers'
os.environ['SERVICE_LEVELS_TABLE'] = 'agentic-service-bot-dev-service-levels'
os.environ['MESSAGES_TABLE'] = 'agentic-service-bot-dev-messages'
os.environ['CONNECTIONS_TABLE'] = 'agentic-service-bot-dev-connections'
os.environ['ANTHROPIC_API_KEY'] = 'your-api-key-here'  # Replace with your actual API key or use a mock
os.environ['ANTHROPIC_MODEL'] = 'claude-3-sonnet-20240229'
os.environ['ALLOWED_ORIGIN'] = '*'

# Add the current directory to sys.path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Temporarily modify the handlers to use absolute imports
import utils
import handlers.chat_handler

# Monkey patch the imports in chat_handler
handlers.chat_handler.convert_decimal_to_float = utils.convert_decimal_to_float
handlers.chat_handler.convert_float_to_decimal = utils.convert_float_to_decimal

# Now import the handler
from index import handler

def create_chat_event(customer_id: str, message: str) -> Dict[str, Any]:
    """
    Create a simulated API Gateway event for a chat message.
    
    Args:
        customer_id: The ID of the customer
        message: The chat message
        
    Returns:
        A simulated API Gateway event
    """
    return {
        'httpMethod': 'POST',
        'path': '/api/chat',
        'pathParameters': {},
        'queryStringParameters': {},
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'customerId': customer_id,
            'message': message
        })
    }

def create_history_event(customer_id: str) -> Dict[str, Any]:
    """
    Create a simulated API Gateway event for retrieving chat history.
    
    Args:
        customer_id: The ID of the customer
        
    Returns:
        A simulated API Gateway event
    """
    return {
        'httpMethod': 'GET',
        'path': '/api/chat/history',
        'pathParameters': {},
        'queryStringParameters': {
            'customerId': customer_id
        },
        'headers': {}
    }

def test_chat_message():
    """Test sending a chat message."""
    print("\n=== Testing Chat Message ===")
    
    # Create a test event
    event = create_chat_event('test-customer-id', 'Turn on my speaker')
    
    # Call the Lambda handler
    try:
        response = handler(event, {})
        print(f"Status Code: {response.get('statusCode')}")
        print(f"Headers: {json.dumps(response.get('headers'), indent=2)}")
        print(f"Body: {json.dumps(json.loads(response.get('body', '{}')), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_chat_history():
    """Test retrieving chat history."""
    print("\n=== Testing Chat History ===")
    
    # Create a test event
    event = create_history_event('test-customer-id')
    
    # Call the Lambda handler
    try:
        response = handler(event, {})
        print(f"Status Code: {response.get('statusCode')}")
        print(f"Headers: {json.dumps(response.get('headers'), indent=2)}")
        print(f"Body: {json.dumps(json.loads(response.get('body', '{}')), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'chat':
            test_chat_message()
        elif sys.argv[1] == 'history':
            test_chat_history()
        else:
            print(f"Unknown test: {sys.argv[1]}")
            print("Available tests: chat, history")
    else:
        # Run all tests
        test_chat_message()
        test_chat_history() 