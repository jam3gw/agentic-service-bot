"""
Chat handler for the Agentic Service Bot.

This module provides functions for handling chat messages via REST API.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from decimal import Decimal

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import local modules
from services.dynamodb_service import (
    get_customer,
    get_service_level_permissions,
    save_message,
    get_conversation_messages,
    get_messages_by_user_id
)
from services.anthropic_service import generate_response
from models.customer import Customer
from models.message import Message

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

def handle_chat_message(customer_id: str, message_text: str, event=None) -> Dict[str, Any]:
    """
    Handle a chat message from a customer.
    
    Args:
        customer_id: The ID of the customer sending the message
        message_text: The text of the message
        event: The Lambda event (optional, for CORS headers)
        
    Returns:
        API Gateway response
    """
    # Get CORS headers based on the request origin
    cors_headers = get_cors_headers(event)
    
    logger.info(f"Processing chat message from customer {customer_id}: {message_text}")
    
    try:
        # Validate message text - prevent empty messages
        if not message_text or not message_text.strip():
            logger.warning(f"Empty message received from customer {customer_id}")
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': "Empty messages are not allowed"
                })
            }
        
        # Get customer data
        customer = get_customer(customer_id)
        if not customer:
            logger.error(f"Customer not found: {customer_id}")
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': f"Customer not found: {customer_id}"})
            }
        
        # Get service level permissions
        service_level = customer.service_level
        permissions = get_service_level_permissions(service_level)
        
        # Generate a conversation ID if not provided
        # In a real app, this would be passed in from the client
        conversation_id = str(uuid.uuid4())
        
        # Create user message
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=customer_id,
            text=message_text,
            sender="user",
            timestamp=datetime.now().isoformat()
        )
        
        # Save user message to DynamoDB
        save_message(user_message)
        
        # Generate response using Anthropic Claude
        response_text = generate_response(
            prompt=message_text,
            context={
                "customer": customer,
                "permissions": permissions
            }
        )
        
        # Create bot message
        bot_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=customer_id,
            text=response_text,
            sender="bot",
            timestamp=datetime.now().isoformat()
        )
        
        # Save bot message to DynamoDB
        save_message(bot_message)
        
        # Prepare response
        response = {
            'message': response_text,
            'timestamp': bot_message.timestamp,
            'messageId': bot_message.id,
            'id': bot_message.id,
            'conversationId': conversation_id,
            'customerId': customer_id
        }
        
        # Convert any Decimal objects to floats for JSON serialization
        response = convert_decimal_to_float(response)
        
        # Return response
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(response)
        }
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
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
    
    logger.info(f"Getting chat history for customer {customer_id}" + 
                (f" and conversation {conversation_id}" if conversation_id else ""))
    
    try:
        # Get customer data to verify customer exists
        customer = get_customer(customer_id)
        if not customer:
            logger.error(f"Customer not found: {customer_id}")
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': f"Customer not found: {customer_id}"})
            }
        
        # Get messages based on whether a conversation_id was provided
        if conversation_id:
            # Get messages for the specific conversation
            message_items = get_conversation_messages(conversation_id)
            
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
        else:
            # Get all messages for this customer
            messages = get_messages_by_user_id(customer_id)
        
        # Format messages for the response
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
        
        # Return response
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
        logger.error(f"Error getting chat history: {str(e)}")
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