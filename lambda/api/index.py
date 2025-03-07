"""
Lambda function for handling API requests in the Agentic Service Bot.

This module serves as the entry point for the AWS Lambda function that handles
HTTP requests for the API service.

Environment Variables:
    CUSTOMERS_TABLE: DynamoDB table for storing customer data
    SERVICE_LEVELS_TABLE: DynamoDB table for storing service level permissions
"""

import json
import logging
import sys
import os
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add the current directory to sys.path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import handlers
from handlers.customer_handler import (
    handle_get_customers,
    handle_get_customer,
    CORS_HEADERS
)
from handlers.device_handler import (
    handle_get_devices,
    handle_update_device
)
from handlers.capability_handler import (
    handle_get_capabilities,
    handle_get_capability
)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler.
    
    Args:
        event: The event data
        context: The Lambda context
        
    Returns:
        API Gateway response
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Handle OPTIONS request (CORS preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    try:
        # Extract path and method
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        
        # Parse path parameters
        path_parameters = event.get('pathParameters', {}) or {}
        
        # Route to appropriate handler based on path and method
        if path.startswith('/api/customers'):
            if path.endswith('/devices'):
                # Handle customer devices
                customer_id = path_parameters.get('customerId', '')
                
                if http_method == 'GET':
                    return handle_get_devices(customer_id, CORS_HEADERS)
                elif http_method == 'PUT':
                    # Parse request body
                    body = json.loads(event.get('body', '{}'))
                    device_id = body.get('deviceId', '')
                    new_power = body.get('power', '')
                    
                    return handle_update_device(customer_id, device_id, new_power, CORS_HEADERS)
            
            elif '/customers/' in path and not path.endswith('/customers'):
                # Handle specific customer
                customer_id = path_parameters.get('customerId', '')
                
                if http_method == 'GET':
                    return handle_get_customer(customer_id, CORS_HEADERS)
            
            else:
                # Handle all customers
                if http_method == 'GET':
                    return handle_get_customers(CORS_HEADERS)
        
        elif path.startswith('/api/capabilities'):
            if '/capabilities/' in path and not path.endswith('/capabilities'):
                # Handle specific capability
                capability_id = path_parameters.get('capabilityId', '')
                
                if http_method == 'GET':
                    return handle_get_capability(capability_id, CORS_HEADERS)
            
            else:
                # Handle all capabilities
                if http_method == 'GET':
                    return handle_get_capabilities(CORS_HEADERS)
        
        # If no matching route, return 404
        return {
            'statusCode': 404,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': 'Not found'
            })
        }
    
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': f"Internal server error: {str(e)}"
            })
        } 