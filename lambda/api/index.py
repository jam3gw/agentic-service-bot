"""
Lambda function for handling API requests in the Agentic Service Bot.

This module serves as the entry point for the AWS Lambda function that handles
HTTP requests for the API service, including device and capability endpoints.

Environment Variables:
    CUSTOMERS_TABLE: DynamoDB table for storing customer data
    SERVICE_LEVELS_TABLE: DynamoDB table for storing service level permissions
"""

import json
import logging
import sys
import os
from typing import Dict, Any, List, Union

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add the current directory to sys.path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import utility functions from local module
import utils

# Import handlers
from handlers.customer_handler import handle_get_customers, handle_get_customer
from handlers.device_handler import handle_get_devices, handle_update_device
from handlers.capability_handler import handle_get_capabilities

# CORS headers
def get_cors_headers(event=None):
    """
    Get CORS headers based on the request origin.
    
    Args:
        event: The Lambda event (optional)
        
    Returns:
        Dictionary of CORS headers
    """
    # Since we're not using credentials, we can use a wildcard
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PATCH,DELETE',
        'Access-Control-Allow-Credentials': 'false',
    }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for HTTP API events.
    
    Args:
        event: The event data
        context: The Lambda context
        
    Returns:
        API Gateway response
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get CORS headers based on the request origin
    cors_headers = get_cors_headers(event)
    
    # Handle OPTIONS request (CORS preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': ''
        }
    
    try:
        # Extract path and method
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        
        # Parse path parameters
        path_parameters = event.get('pathParameters', {}) or {}
        
        # Route to appropriate handler based on path and method
        if path == '/api/customers':
            if http_method == 'GET':
                return handle_get_customers(cors_headers)
        
        elif path.startswith('/api/customers/') and path.endswith('/devices'):
            if http_method == 'GET':
                customer_id = path_parameters.get('customerId')
                return handle_get_devices(customer_id, cors_headers)
        
        elif path.startswith('/api/customers/') and '/devices/' in path:
            if http_method == 'PATCH':
                customer_id = path_parameters.get('customerId')
                device_id = path_parameters.get('deviceId')
                # Parse request body
                body = json.loads(event.get('body', '{}'))
                return handle_update_device(customer_id, device_id, body, cors_headers)
        
        elif path.startswith('/api/customers/') and not '/devices/' in path and not path.endswith('/devices'):
            if http_method == 'GET':
                customer_id = path_parameters.get('customerId')
                return handle_get_customer(customer_id, cors_headers)
        
        elif path == '/api/capabilities':
            if http_method == 'GET':
                return handle_get_capabilities(cors_headers)
        
        # If no route matches
        return {
            'statusCode': 404,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Not found'})
        }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Internal server error'})
        } 