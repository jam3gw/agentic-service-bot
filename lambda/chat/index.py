"""
Lambda function for handling chat interactions in the Agentic Service Bot.

This module serves as the entry point for the AWS Lambda function that handles
HTTP requests for the chat service.

Environment Variables:
    MESSAGES_TABLE: DynamoDB table for storing message history
    CUSTOMERS_TABLE: DynamoDB table for storing customer data
    SERVICE_LEVELS_TABLE: DynamoDB table for storing service level permissions
    ANTHROPIC_API_KEY: API key for Anthropic's Claude API
    ANTHROPIC_MODEL: Model to use for Anthropic's Claude API
"""

import json
import logging
import sys
import os
import time
from typing import Dict, Any, List, Union
from decimal import Decimal

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
from handlers.chat_handler import (
    handle_chat_message,
    handle_chat_history,
    CORS_HEADERS
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
        if path.startswith('/api/chat/history/'):
            if http_method == 'GET':
                customer_id = path_parameters.get('customerId')
                if not customer_id:
                    return {
                        'statusCode': 400,
                        'headers': CORS_HEADERS,
                        'body': json.dumps({'error': 'Missing customerId parameter'})
                    }
                # Get conversationId from query parameters if available
                query_parameters = event.get('queryStringParameters', {}) or {}
                conversation_id = query_parameters.get('conversationId')
                return handle_chat_history(customer_id, event, conversation_id)
        
        elif path == '/api/chat':
            if http_method == 'POST':
                # Parse request body
                body = json.loads(event.get('body', '{}'))
                customer_id = body.get('customerId')
                message = body.get('message')
                conversation_id = body.get('conversationId')  # Extract conversationId if provided
                
                if not customer_id or not message:
                    return {
                        'statusCode': 400,
                        'headers': CORS_HEADERS,
                        'body': json.dumps({'error': 'Missing customerId or message'})
                    }
                
                return handle_chat_message(customer_id, message, event, conversation_id)
        
        # If no matching route, return 404
        return {
            'statusCode': 404,
            'body': json.dumps({
                'error': 'Not found'
            })
        }
    
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Internal server error: {str(e)}"
            })
        }
