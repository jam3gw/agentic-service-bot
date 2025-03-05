"""
Lambda function for handling chat interactions in the Agentic Service Bot.

This module serves as the entry point for the AWS Lambda function that handles
WebSocket and HTTP requests for the chat service.

Environment Variables:
    MESSAGES_TABLE: DynamoDB table for storing message history
    CUSTOMERS_TABLE: DynamoDB table for storing customer data
    SERVICE_LEVELS_TABLE: DynamoDB table for storing service level permissions
    CONNECTIONS_TABLE: DynamoDB table for storing WebSocket connections
    ANTHROPIC_API_KEY: API key for Anthropic's Claude API
    ANTHROPIC_MODEL: Model to use for Anthropic's Claude API
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
from handlers.websocket_handler import (
    handle_connect,
    handle_message,
    CORS_HEADERS
)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for WebSocket and HTTP events.
    
    Args:
        event: The event data
        context: The Lambda context
        
    Returns:
        API Gateway response
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Check if this is a WebSocket event
    if 'requestContext' in event and 'connectionId' in event['requestContext']:
        route_key = event['requestContext'].get('routeKey')
        
        if route_key == '$connect':
            return handle_connect(event, context)
        elif route_key == '$disconnect':
            # Simple disconnect handler
            connection_id = event['requestContext']['connectionId']
            logger.info(f"Disconnect event received for connection ID: {connection_id}")
            # Mark the connection as disconnected instead of removing it
            from services.dynamodb_service import update_connection_status
            update_connection_status(connection_id, "disconnected")
            return {'statusCode': 200, 'body': 'Disconnected'}
        elif route_key == 'message':
            return handle_message(event, context)
        else:
            # Default route
            return handle_message(event, context)
    
    # If not a WebSocket event, handle as HTTP request (for backward compatibility)
    # Handle OPTIONS request (CORS preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    try:
        # Parse the request body
        body = json.loads(event.get('body', '{}'))
        message = body.get('message')
        customer_id = body.get('customerId')
        
        if not message or not customer_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        # Process the request
        from services.request_processor import process_request
        response = process_request(customer_id=customer_id, user_input=message)
        response_text = response.get("message", "No response generated")
        
        # Return the response
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'message': response_text,
                'customerId': customer_id,
            })
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        } 