"""
DynamoDB service for the Agentic Service Bot.

This module provides functions for interacting with DynamoDB tables
to store and retrieve customer data, service levels, messages, and connections.
"""

import os
import sys
import logging
import time
from typing import Dict, Any, Optional, List
import boto3
from datetime import datetime

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import local modules using absolute imports
from models.customer import Customer

# Configure logging
logger = logging.getLogger()

# Set default environment variables for local development
def set_default_env_vars():
    """Set default environment variables for local development if they're not already set."""
    defaults = {
        'MESSAGES_TABLE': 'agentic-service-bot-messages',
        'CUSTOMERS_TABLE': 'agentic-service-bot-customers',
        'SERVICE_LEVELS_TABLE': 'agentic-service-bot-service-levels',
        'CONNECTIONS_TABLE': 'agentic-service-bot-connections',
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
            return Customer(
                item['id'],
                item['name'],
                item['service_level'],
                item['devices']
            )
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
    try:
        response = service_levels_table.get_item(Key={'level': service_level})
        if 'Item' in response:
            return response['Item']
        raise ValueError(f"Unknown service level: {service_level}")
    except Exception as e:
        logger.error(f"Error getting service level: {str(e)}")
        return {"allowed_actions": []}

def save_connection(connection_id: str, customer_id: str) -> bool:
    """
    Save a WebSocket connection to the connections table.
    
    Args:
        connection_id: The WebSocket connection ID
        customer_id: The customer ID associated with this connection
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Calculate TTL
        ttl = int(time.time()) + CONNECTION_TTL
        
        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'customerId': customer_id,
                'timestamp': datetime.utcnow().isoformat(),
                'ttl': ttl,
                'status': 'connected'  # Add initial status
            }
        )
        logger.info(f"Successfully saved connection {connection_id} for customer {customer_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving connection {connection_id}: {str(e)}")
        return False

def get_customer_id_for_connection(connection_id: str) -> Optional[str]:
    """
    Get the customer ID associated with a connection ID.
    
    Args:
        connection_id: The WebSocket connection ID
        
    Returns:
        The customer ID or None if not found
    """
    try:
        logger.info(f"Getting customer ID for connection {connection_id}")
        response = connections_table.get_item(
            Key={
                'connectionId': connection_id
            }
        )
        item = response.get('Item')
        if item:
            customer_id = item.get('customerId')
            logger.info(f"Found customer ID {customer_id} for connection {connection_id}")
            return customer_id
        logger.warning(f"No customer ID found for connection {connection_id}")
        return None
    except Exception as e:
        logger.error(f"Error getting customer ID for connection {connection_id}: {str(e)}")
        return None

def delete_connection(connection_id: str) -> bool:
    """
    Delete a connection from the connections table.
    
    Args:
        connection_id: The WebSocket connection ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        connections_table.delete_item(
            Key={
                'connectionId': connection_id
            }
        )
        logger.info(f"Successfully removed connection {connection_id} from database")
        return True
    except Exception as e:
        logger.error(f"Error removing connection {connection_id} from database: {str(e)}")
        return False

def update_connection_status(connection_id: str, status: str) -> bool:
    """
    Update the status of a connection in the connections table.
    
    Args:
        connection_id: The WebSocket connection ID to update
        status: The new status for the connection (e.g., 'disconnected')
        
    Returns:
        True if successful, False otherwise
    """
    try:
        connections_table.update_item(
            Key={
                'connectionId': connection_id
            },
            UpdateExpression="SET #status = :status, updatedAt = :timestamp",
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': status,
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Successfully updated connection {connection_id} status to '{status}'")
        return True
    except Exception as e:
        logger.error(f"Error updating connection {connection_id} status: {str(e)}")
        return False

def store_message(conversation_id: str, customer_id: str, message: str, 
                 sender: str, request_type: Optional[str] = None, 
                 actions_allowed: Optional[bool] = None) -> bool:
    """
    Store a message in the messages table.
    
    Args:
        conversation_id: The ID of the conversation
        customer_id: The ID of the customer
        message: The message content
        sender: The sender of the message ('user' or 'bot')
        request_type: The type of request (optional)
        actions_allowed: Whether the requested actions are allowed (optional)
        
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
            
        messages_table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error storing message: {str(e)}")
        return False 