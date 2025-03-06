"""
Local test script for the API Lambda function.

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
os.environ['ALLOWED_ORIGIN'] = '*'

# Add the current directory to sys.path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Temporarily modify the handlers to use absolute imports
import utils
import handlers.customer_handler
import handlers.device_handler
import handlers.capability_handler

# Monkey patch the imports in handlers
handlers.customer_handler.convert_decimal_to_float = utils.convert_decimal_to_float
handlers.customer_handler.convert_float_to_decimal = utils.convert_float_to_decimal
handlers.device_handler.convert_decimal_to_float = utils.convert_decimal_to_float
handlers.device_handler.convert_float_to_decimal = utils.convert_float_to_decimal
handlers.capability_handler.convert_decimal_to_float = utils.convert_decimal_to_float
handlers.capability_handler.convert_float_to_decimal = utils.convert_float_to_decimal

# Now import the handler
from index import handler

def create_get_customers_event() -> Dict[str, Any]:
    """
    Create a simulated API Gateway event for getting all customers.
    
    Returns:
        A simulated API Gateway event
    """
    return {
        'httpMethod': 'GET',
        'path': '/api/customers',
        'pathParameters': {},
        'queryStringParameters': {},
        'headers': {}
    }

def create_get_customer_event(customer_id: str) -> Dict[str, Any]:
    """
    Create a simulated API Gateway event for getting a specific customer.
    
    Args:
        customer_id: The ID of the customer
        
    Returns:
        A simulated API Gateway event
    """
    return {
        'httpMethod': 'GET',
        'path': f'/api/customers/{customer_id}',
        'pathParameters': {
            'customerId': customer_id
        },
        'queryStringParameters': {},
        'headers': {}
    }

def create_get_devices_event(customer_id: str) -> Dict[str, Any]:
    """
    Create a simulated API Gateway event for getting a customer's devices.
    
    Args:
        customer_id: The ID of the customer
        
    Returns:
        A simulated API Gateway event
    """
    return {
        'httpMethod': 'GET',
        'path': f'/api/customers/{customer_id}/devices',
        'pathParameters': {
            'customerId': customer_id
        },
        'queryStringParameters': {},
        'headers': {}
    }

def create_update_device_event(customer_id: str, device_id: str, new_state: str) -> Dict[str, Any]:
    """
    Create a simulated API Gateway event for updating a device state.
    
    Args:
        customer_id: The ID of the customer
        device_id: The ID of the device
        new_state: The new state for the device
        
    Returns:
        A simulated API Gateway event
    """
    return {
        'httpMethod': 'PATCH',
        'path': f'/api/customers/{customer_id}/devices/{device_id}',
        'pathParameters': {
            'customerId': customer_id,
            'deviceId': device_id
        },
        'queryStringParameters': {},
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'state': new_state
        })
    }

def create_get_capabilities_event() -> Dict[str, Any]:
    """
    Create a simulated API Gateway event for getting capabilities.
    
    Returns:
        A simulated API Gateway event
    """
    return {
        'httpMethod': 'GET',
        'path': '/api/capabilities',
        'pathParameters': {},
        'queryStringParameters': {},
        'headers': {}
    }

def test_get_customers():
    """Test getting all customers."""
    print("\n=== Testing Get Customers ===")
    
    # Create a test event
    event = create_get_customers_event()
    
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

def test_get_customer():
    """Test getting a specific customer."""
    print("\n=== Testing Get Customer ===")
    
    # Create a test event
    event = create_get_customer_event('test-customer-id')
    
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

def test_get_devices():
    """Test getting a customer's devices."""
    print("\n=== Testing Get Devices ===")
    
    # Create a test event
    event = create_get_devices_event('test-customer-id')
    
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

def test_update_device():
    """Test updating a device state."""
    print("\n=== Testing Update Device ===")
    
    # Create a test event
    event = create_update_device_event('test-customer-id', 'test-device-id', 'on')
    
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

def test_get_capabilities():
    """Test getting capabilities."""
    print("\n=== Testing Get Capabilities ===")
    
    # Create a test event
    event = create_get_capabilities_event()
    
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
        if sys.argv[1] == 'customers':
            test_get_customers()
        elif sys.argv[1] == 'customer':
            test_get_customer()
        elif sys.argv[1] == 'devices':
            test_get_devices()
        elif sys.argv[1] == 'update-device':
            test_update_device()
        elif sys.argv[1] == 'capabilities':
            test_get_capabilities()
        else:
            print(f"Unknown test: {sys.argv[1]}")
            print("Available tests: customers, customer, devices, update-device, capabilities")
    else:
        # Run all tests
        test_get_customers()
        test_get_customer()
        test_get_devices()
        test_update_device()
        test_get_capabilities() 