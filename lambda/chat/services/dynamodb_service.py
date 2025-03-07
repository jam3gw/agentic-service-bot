"""
DynamoDB service for the Agentic Service Bot.

This module provides functions for interacting with DynamoDB tables
to store and retrieve customer data, service levels, messages, and connections.
"""

# Standard library imports
import os
import logging
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

# Third-party imports
import boto3
from boto3.dynamodb.conditions import Key

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Local application imports
from models.customer import Customer
from models.message import Message
from utils import convert_decimal_to_float, convert_float_to_decimal

# Set default environment variables for local development
def set_default_env_vars():
    """Set default environment variables for local development if they're not already set."""
    defaults = {
        'MESSAGES_TABLE': 'dev-messages',
        'CUSTOMERS_TABLE': 'dev-customers',
        'SERVICE_LEVELS_TABLE': 'dev-service-levels',
        'CONNECTIONS_TABLE': 'dev-connections',
    }
    
    for key, value in defaults.items():
        if not os.environ.get(key):
            logger.info(f"Setting default environment variable {key}={value}")
            os.environ[key] = value

# Set default environment variables
set_default_env_vars()

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE'))
customers_table = dynamodb.Table(os.environ.get('CUSTOMERS_TABLE'))
service_levels_table = dynamodb.Table(os.environ.get('SERVICE_LEVELS_TABLE'))
connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE'))

# TTL for connections (24 hours in seconds)
CONNECTION_TTL = 24 * 60 * 60

def get_customer(customer_id: str) -> Optional[Customer]:
    """
    Get customer data from DynamoDB.
    
    Args:
        customer_id: The ID of the customer to retrieve
        
    Returns:
        A Customer object if found, None otherwise
    """
    try:
        response = customers_table.get_item(Key={'id': customer_id})
        if 'Item' in response:
            item = response['Item']
            # Map serviceLevel (camelCase in DynamoDB) to service_level (snake_case in model)
            service_level = item.get('serviceLevel', 'basic')
            
            # Get the first device or an empty dict if no devices
            devices = item.get('devices', [])
            device = devices[0] if devices and len(devices) > 0 else {}
            
            logger.info(f"Retrieved customer: {item['id']}, service level: {service_level}, device: {device.get('id', 'none')}")
            
            return Customer(
                item['id'],
                item['name'],
                service_level,
                device
            )
        logger.warning(f"Customer not found: {customer_id}")
        return None
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        return None

def get_service_level_permissions(service_level: str) -> Dict[str, Any]:
    """
    Get service level permissions from DynamoDB.
    
    Args:
        service_level: The service level to retrieve permissions for
        
    Returns:
        A dictionary containing the service level permissions
    """
    logger.info(f"Getting permissions for service level: {service_level}")
    try:
        logger.info(f"Querying DynamoDB table: {service_levels_table.table_name}")
        response = service_levels_table.get_item(Key={'level': service_level})
        logger.info(f"DynamoDB response: {response}")
        
        if 'Item' in response:
            permissions = response['Item']
            logger.info(f"Retrieved permissions: {permissions}")
            return permissions
        
        logger.warning(f"Unknown service level: {service_level}")
        raise ValueError(f"Unknown service level: {service_level}")
    except Exception as e:
        logger.error(f"Error getting service level permissions: {str(e)}")
        logger.info("Returning empty allowed_actions list as fallback")
        return {"allowed_actions": []}

def get_conversation_messages(conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve messages for a specific conversation.
    
    Args:
        conversation_id: The ID of the conversation to retrieve messages for
        limit: Maximum number of messages to retrieve (default: 50)
        
    Returns:
        List of message objects, sorted by timestamp
    """
    try:
        response = messages_table.query(
            KeyConditionExpression="conversationId = :conversation_id",
            ExpressionAttributeValues={
                ":conversation_id": conversation_id
            },
            ScanIndexForward=False,  # Sort in descending order (newest first)
            Limit=limit
        )
        
        messages = response.get('Items', [])
        logger.info(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
        
        # Sort messages by timestamp (newest first)
        messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return messages
    except Exception as e:
        logger.error(f"Error retrieving messages for conversation {conversation_id}: {str(e)}")
        return []

def get_messages_by_user_id(user_id: str) -> List[Message]:
    """
    Get all messages for a user from DynamoDB using the UserIdIndex GSI.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        A list of Message objects
    """
    try:
        logger.info(f"Getting messages for user {user_id}")
        
        # Query the GSI for messages with this user_id
        response = messages_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='userId = :uid',
            ExpressionAttributeValues={
                ':uid': user_id
            },
            ScanIndexForward=True  # Sort in ascending order by timestamp
        )
        
        # Convert items to Message objects
        messages = []
        for item in response.get('Items', []):
            messages.append(Message(
                id=item.get('id'),
                conversation_id=item.get('conversationId'),
                user_id=item.get('userId'),
                text=item.get('text'),
                sender=item.get('sender'),
                timestamp=item.get('timestamp')
            ))
        
        logger.info(f"Found {len(messages)} messages for user {user_id}")
        return messages
        
    except Exception as e:
        logger.error(f"Error getting messages for user {user_id}: {str(e)}")
        return []

def store_message(conversation_id: str, customer_id: str, message: str, sender: str, 
                 request_type: Optional[str] = None, actions_allowed: Optional[bool] = None) -> bool:
    """
    Store a message in the messages table.
    
    Args:
        conversation_id: The ID of the conversation
        customer_id: The ID of the customer
        message: The message text
        sender: The sender of the message (customer or assistant)
        request_type: Optional type of request (e.g., device_control)
        actions_allowed: Optional flag indicating if actions are allowed
        
    Returns:
        True if successful, False otherwise
    """
    try:
        item = {
            'conversationId': conversation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'userId': customer_id,
            'message': message,
            'sender': sender
        }
        
        if request_type:
            item['request_type'] = request_type
            
        if actions_allowed is not None:
            item['actions_allowed'] = actions_allowed
        
        # Convert any float values to Decimal for DynamoDB
        item = convert_float_to_decimal(item)
            
        messages_table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error storing message: {str(e)}")
        return False

def update_device_state(customer_id: str, device_id: str, state_updates: Dict[str, Any]) -> bool:
    """
    Update the state of a device in DynamoDB.
    
    Args:
        customer_id: The ID of the customer who owns the device
        device_id: The ID of the device to update
        state_updates: Dictionary of state attributes to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert any float values to Decimal for DynamoDB
        state_updates = convert_float_to_decimal(state_updates)
        
        # Get the customer to find the device
        response = customers_table.get_item(Key={'id': customer_id})
        if 'Item' not in response:
            logger.error(f"Customer {customer_id} not found")
            return False
            
        customer_data = response['Item']
        devices = customer_data.get('devices', [])
        
        if not devices:
            logger.error(f"No devices found for customer {customer_id}")
            return False
            
        # Get the first device
        device = devices[0]
        
        # Verify it's the correct device
        if device.get('id') != device_id:
            logger.error(f"Device {device_id} does not match customer's device {device.get('id')}")
            return False
            
        # Update the device state
        for key, value in state_updates.items():
            device[key] = value
            
        # Save the updated customer data
        update_response = customers_table.update_item(
            Key={'id': customer_id},
            UpdateExpression='SET devices[0] = :device',
            ExpressionAttributeValues={':device': device},
            ReturnValues='UPDATED_NEW'
        )
        
        logger.info(f"Updated device {device_id} for customer {customer_id}: {state_updates}")
        logger.debug(f"Update response: {update_response}")
        
        return update_response['ResponseMetadata']['HTTPStatusCode'] == 200
    except Exception as e:
        logger.error(f"Error updating device state: {str(e)}")
        return False

def save_message(message: Message) -> bool:
    """
    Save a message to the messages table.
    
    Args:
        message: The Message object to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Saving message {message.id} to conversation {message.conversation_id}")
        
        # Convert Message object to dictionary for DynamoDB
        item = message.to_dict()
        
        # Save to DynamoDB
        messages_table.put_item(Item=item)
        
        logger.info(f"Successfully saved message {message.id}")
        return True
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        return False 