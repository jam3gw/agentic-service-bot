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

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import utility functions from local module
from utils import convert_decimal_to_float, convert_float_to_decimal

# Import local modules
from services.dynamodb_service import (
    get_customer,
    get_service_level_permissions,
    save_message,
    get_conversation_messages
)
from services.anthropic_service import generate_response
from models.customer import Customer
from models.message import Message

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
    'Access-Control-Allow-Credentials': 'true',
}

def handle_chat_message(customer_id: str, message_text: str) -> Dict[str, Any]:
    """
    Handle a chat message from a customer.
    
    Args:
        customer_id: The ID of the customer sending the message
        message_text: The text of the message
        
    Returns:
        A dictionary containing the response message
    """
    logger.info(f"Processing chat message from customer {customer_id}: {message_text}")
    
    try:
        # Get customer data
        customer = get_customer(customer_id)
        if not customer:
            logger.error(f"Customer not found: {customer_id}")
            return {
                'error': f"Customer not found: {customer_id}"
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
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        return {
            'error': f"Error processing message: {str(e)}"
        }

def handle_chat_history(customer_id: str) -> Dict[str, Any]:
    """
    Get chat history for a customer.
    
    Args:
        customer_id: The ID of the customer
        
    Returns:
        A dictionary containing the chat history
    """
    logger.info(f"Getting chat history for customer {customer_id}")
    
    try:
        # Get customer data to verify customer exists
        customer = get_customer(customer_id)
        if not customer:
            logger.error(f"Customer not found: {customer_id}")
            return {
                'error': f"Customer not found: {customer_id}"
            }
        
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
            'messages': formatted_messages,
            'customerId': customer_id
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return {
            'error': f"Error getting chat history: {str(e)}"
        }

def get_messages_by_user_id(user_id: str) -> List[Message]:
    """
    Get all messages for a user from DynamoDB.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        A list of Message objects
    """
    # This is a placeholder - this function would need to be implemented
    # in dynamodb_service.py to query the GSI for userId
    from services.dynamodb_service import get_messages_by_user_id
    return get_messages_by_user_id(user_id) 