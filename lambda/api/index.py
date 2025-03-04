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
from typing import Dict, Any

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import handlers
from handlers.device_handler import handle_get_devices, handle_update_device
from handlers.capability_handler import handle_get_capabilities

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PATCH,DELETE',
    'Access-Control-Allow-Credentials': 'true'
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
        if path.startswith('/api/customers/') and path.endswith('/devices'):
            if http_method == 'GET':
                customer_id = path_parameters.get('customerId')
                return handle_get_devices(customer_id, CORS_HEADERS)
        
        elif path.startswith('/api/customers/') and '/devices/' in path:
            if http_method == 'PATCH':
                customer_id = path_parameters.get('customerId')
                device_id = path_parameters.get('deviceId')
                # Parse request body
                body = json.loads(event.get('body', '{}'))
                return handle_update_device(customer_id, device_id, body, CORS_HEADERS)
        
        elif path == '/api/capabilities':
            if http_method == 'GET':
                return handle_get_capabilities(CORS_HEADERS)
        
        # If no route matches
        return {
            'statusCode': 404,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Not found'})
        }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        } 