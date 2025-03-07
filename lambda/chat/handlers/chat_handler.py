"""
Chat handler for the Agentic Service Bot.

This module provides functions for handling chat messages via REST API.
"""

# Standard library imports
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Local application imports
from models.customer import Customer
from models.message import Message
from services.anthropic_service import generate_response
from services.dynamodb_service import (
    get_conversation_messages,
    get_customer,
    get_messages_by_user_id,
    get_service_level_permissions,
    save_message
)
from services.request_processor import process_request

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Utility functions
def convert_decimal_to_float(obj: Any) -> Any:
    """
    Recursively convert Decimal objects to floats in a data structure.
    
    Args:
        obj: The object to convert
        
    Returns:
        The converted object
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj

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
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Credentials': 'false',
    }

# For backward compatibility
CORS_HEADERS = get_cors_headers()

def handle_chat_message(customer_id: str, message_text: str, event=None, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Handle a chat message from a customer.
    
    Args:
        customer_id: The ID of the customer sending the message
        message_text: The text of the message
        event: The Lambda event (optional, for CORS headers)
        conversation_id: The ID of the conversation (optional)
        
    Returns:
        API Gateway response
    """
    # Get CORS headers based on the request origin
    cors_headers = get_cors_headers(event)
    
    logger.info(f"[CHAT_HANDLER] Processing chat message from customer {customer_id}: {message_text}" +
                (f" in conversation {conversation_id}" if conversation_id else ""))
    logger.debug(f"[CHAT_HANDLER] Event: {event}")
    
    try:
        # Validate message text - prevent empty messages
        if not message_text or not message_text.strip():
            logger.warning(f"[CHAT_HANDLER] Empty message received from customer {customer_id}")
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': "Empty messages are not allowed"
                })
            }
        
        # Prepare message data for process_request
        message_data = {
            'message': message_text,
            'metadata': {
                'event': event,
                'conversation_id': conversation_id
            }
        }
        
        # Use process_request to handle the message
        logger.info(f"[CHAT_HANDLER] Delegating to process_request for customer {customer_id}")
        result = process_request(customer_id, message_data, connection_id=conversation_id or "")
        logger.info(f"[CHAT_HANDLER] Received result from process_request")
        
        # Check for errors in the result
        error_message = result.get('error')
        if error_message:
            logger.error(f"[CHAT_HANDLER] process_request returned error: {error_message}")
            
            # Check if the error is a customer not found error
            if isinstance(error_message, str) and "Customer" in error_message and "not found" in error_message:
                # Return 404 for customer not found
                return {
                    'statusCode': 404,
                    'headers': cors_headers,
                    'body': json.dumps({'error': error_message})
                }
            
            # Return 500 for other errors
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': error_message})
            }
        
        # Prepare response
        response = {
            'message': result.get('message', ''),
            'timestamp': result.get('timestamp', datetime.now().isoformat()),
            'messageId': str(uuid.uuid4()),  # Generate a new ID if not provided
            'id': str(uuid.uuid4()),  # Generate a new ID if not provided
            'conversationId': conversation_id or result.get('conversation_id', str(uuid.uuid4())),
            'customerId': customer_id,
            'request_type': result.get('request_type', 'unknown'),
            'action_executed': result.get('action_executed', False)
        }
        
        # Convert any Decimal objects to floats for JSON serialization
        response = convert_decimal_to_float(response)
        logger.debug(f"[CHAT_HANDLER] Prepared response: {response}")
        
        # Return response
        logger.info(f"[CHAT_HANDLER] Request processing completed for customer {customer_id}")
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(response)
        }
        
    except Exception as e:
        logger.error(f"[CHAT_HANDLER] Error processing chat message: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f"Error processing message: {str(e)}"})
        }

def handle_chat_history(customer_id: str, event=None, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get chat history for a customer.
    
    Args:
        customer_id: The ID of the customer
        event: The Lambda event (optional, for CORS headers)
        conversation_id: The ID of the conversation (optional)
        
    Returns:
        API Gateway response
    """
    # Get CORS headers based on the request origin
    cors_headers = get_cors_headers(event)
    
    logger.info(f"[CHAT_HISTORY] Getting chat history for customer {customer_id}" + 
                (f" and conversation {conversation_id}" if conversation_id else ""))
    logger.debug(f"[CHAT_HISTORY] Event: {event}")
    
    try:
        # Get customer data to verify customer exists
        logger.debug(f"[CHAT_HISTORY] Verifying customer exists: {customer_id}")
        customer = get_customer(customer_id)
        if not customer:
            logger.error(f"[CHAT_HISTORY] Customer not found: {customer_id}")
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': f"Customer not found: {customer_id}"})
            }
        
        logger.info(f"[CHAT_HISTORY] Customer verified: {customer_id}")
        
        # Get messages based on whether a conversation_id was provided
        if conversation_id:
            # Get messages for the specific conversation
            logger.info(f"[CHAT_HISTORY] Retrieving messages for conversation: {conversation_id}")
            message_items = get_conversation_messages(conversation_id)
            logger.info(f"[CHAT_HISTORY] Retrieved {len(message_items)} messages for conversation {conversation_id}")
            
            # Convert to Message objects
            messages = []
            for item in message_items:
                messages.append(Message(
                    id=item.get('id', ''),
                    conversation_id=item.get('conversationId', ''),
                    user_id=item.get('userId', ''),
                    text=item.get('text', ''),
                    sender=item.get('sender', ''),
                    timestamp=item.get('timestamp') or datetime.now().isoformat()
                ))
            logger.debug(f"[CHAT_HISTORY] Converted {len(messages)} message items to Message objects")
        else:
            # Get all messages for this customer
            logger.info(f"[CHAT_HISTORY] Retrieving all messages for customer: {customer_id}")
            messages = get_messages_by_user_id(customer_id)
            logger.info(f"[CHAT_HISTORY] Retrieved {len(messages)} messages for customer {customer_id}")
        
        # Format messages for the response
        logger.debug(f"[CHAT_HISTORY] Formatting {len(messages)} messages for response")
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg.id,
                'text': msg.text,
                'sender': msg.sender,
                'timestamp': msg.timestamp,
                'conversationId': msg.conversation_id
            })
        
        # Convert any Decimal objects to floats for JSON serialization
        formatted_messages = convert_decimal_to_float(formatted_messages)
        logger.debug(f"[CHAT_HISTORY] Converted Decimal objects to floats for {len(formatted_messages)} messages")
        
        # Return response
        logger.info(f"[CHAT_HISTORY] Returning {len(formatted_messages)} messages for customer {customer_id}")
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'messages': formatted_messages,
                'customerId': customer_id,
                'conversationId': conversation_id
            })
        }
        
    except Exception as e:
        logger.error(f"[CHAT_HISTORY] Error getting chat history: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f"Error getting chat history: {str(e)}"})
        }

def get_messages_by_user_id(user_id: str) -> List[Message]:
    """
    Get all messages for a user from DynamoDB.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        A list of Message objects
    """
    # Import the actual implementation from dynamodb_service
    from services.dynamodb_service import get_messages_by_user_id as db_get_messages_by_user_id
    return db_get_messages_by_user_id(user_id) 