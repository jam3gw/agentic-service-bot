"""
DynamoDB service for the Agentic Service Bot API.

This module provides functions for interacting with DynamoDB tables.
"""

import os
import boto3
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Get table names from environment variables
CUSTOMERS_TABLE = os.environ.get('CUSTOMERS_TABLE', '')
SERVICE_LEVELS_TABLE = os.environ.get('SERVICE_LEVELS_TABLE', '')

def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a customer by ID from DynamoDB.
    
    Args:
        customer_id: The ID of the customer to retrieve
        
    Returns:
        Customer data as a dictionary, or None if not found
    """
    if not CUSTOMERS_TABLE:
        logger.error("CUSTOMERS_TABLE environment variable not set")
        return None
    
    try:
        table = dynamodb.Table(CUSTOMERS_TABLE)
        response = table.get_item(Key={'id': customer_id})
        
        if 'Item' not in response:
            logger.warning(f"Customer not found: {customer_id}")
            return None
        
        return response['Item']
    
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        return None

def update_device_state(customer_id: str, device_id: str, new_state: str) -> Optional[Dict[str, Any]]:
    """
    Update the state of a device for a customer.
    
    Args:
        customer_id: The ID of the customer
        device_id: The ID of the device to update
        new_state: The new state to set for the device
        
    Returns:
        Updated device data as a dictionary, or None if not found
    """
    if not CUSTOMERS_TABLE:
        logger.error("CUSTOMERS_TABLE environment variable not set")
        return None
    
    try:
        # Get the customer first
        customer = get_customer_by_id(customer_id)
        
        if not customer:
            logger.warning(f"Customer not found: {customer_id}")
            return None
        
        # Find the device in the customer's devices
        devices = customer.get('devices', [])
        device_index = None
        device = None
        
        for i, d in enumerate(devices):
            if d.get('id') == device_id:
                device_index = i
                device = d
                break
        
        if device_index is None:
            logger.warning(f"Device not found: {device_id}")
            return None
        
        # Update the device state
        device['state'] = new_state
        device['lastUpdated'] = datetime.now().isoformat()
        devices[device_index] = device
        
        # Update the customer record in DynamoDB
        table = dynamodb.Table(CUSTOMERS_TABLE)
        table.update_item(
            Key={'id': customer_id},
            UpdateExpression='SET devices = :devices',
            ExpressionAttributeValues={':devices': devices}
        )
        
        return device
    
    except Exception as e:
        logger.error(f"Error updating device state: {str(e)}")
        return None

def get_service_levels() -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Get all service levels from DynamoDB.
    
    Returns:
        Dictionary of service levels, or None if error
    """
    if not SERVICE_LEVELS_TABLE:
        logger.error("SERVICE_LEVELS_TABLE environment variable not set")
        return None
    
    try:
        table = dynamodb.Table(SERVICE_LEVELS_TABLE)
        response = table.scan()
        
        if 'Items' not in response:
            logger.warning("No service levels found")
            return None
        
        # Convert list of items to dictionary keyed by level
        service_levels = {}
        for item in response.get('Items', []):
            level = item.get('level')
            if level:
                service_levels[level] = item
        
        return service_levels
    
    except Exception as e:
        logger.error(f"Error getting service levels: {str(e)}")
        return None 