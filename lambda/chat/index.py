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
    # Log the event for debugging
    logger.info(f"Event received: {json.dumps(event)}")
    
    try:
        # Handle HTTP events
        if event.get('httpMethod') == 'OPTIONS':
            # Handle CORS preflight request
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': ''
            }
        
        # Handle chat message POST request
        if event.get('httpMethod') == 'POST' and event.get('path', '').endswith('/chat'):
            try:
                # Parse request body
                body = json.loads(event.get('body', '{}'))
                
                # Handle regular chat message
                customer_id = body.get('customerId')
                message = body.get('message')
                
                if not customer_id or not message:
                    logger.error("Missing required parameters: customerId and message are required")
                    return {
                        'statusCode': 400,
                        'headers': CORS_HEADERS,
                        'body': json.dumps({
                            'error': 'Missing required parameters: customerId and message are required'
                        })
                    }
                
                # Process the chat message
                response = handle_chat_message(customer_id, message)
                
                # Check if the response contains an error about customer not found
                if 'error' in response and 'Customer not found' in response['error']:
                    return {
                        'statusCode': 404,
                        'body': json.dumps(response)
                    }
                
                # Convert Decimal objects to floats before serialization
                response = utils.convert_decimal_to_float(response)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(response)
                }
            except Exception as e:
                logger.error(f"Error handling chat message: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': f"Internal server error: {str(e)}"
                    })
                }
        
        # Handle chat history GET request
        if event.get('httpMethod') == 'GET' and '/chat/history/' in event.get('path', ''):
            try:
                # Extract customer ID from path
                path_parts = event.get('path', '').split('/')
                customer_id = path_parts[-1]  # Last part of the path should be the customer ID
                
                if not customer_id:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({
                            'error': 'Missing required parameter: customerId'
                        })
                    }
                
                # Get chat history
                history = handle_chat_history(customer_id)
                
                # Check if the response contains an error about customer not found
                if 'error' in history and 'Customer not found' in history['error']:
                    return {
                        'statusCode': 404,
                        'body': json.dumps(history)
                    }
                
                # Convert Decimal objects to floats before serialization
                history = utils.convert_decimal_to_float(history)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(history)
                }
            except Exception as e:
                logger.error(f"Error handling chat history: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': f"Internal server error: {str(e)}"
                    })
                }
        
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
