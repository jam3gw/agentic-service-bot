"""
DynamoDB service for the Agentic Service Bot API.

This module provides functions for interacting with DynamoDB tables
to store and retrieve customer data, service levels, messages, and connections.
"""

# Standard library imports
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

# Third-party imports
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Get table names from environment variables
CUSTOMERS_TABLE = os.environ.get('CUSTOMERS_TABLE', '')
SERVICE_LEVELS_TABLE = os.environ.get('SERVICE_LEVELS_TABLE', '')

# Device fields that can be updated
DEVICE_FIELDS = {
    'power': str,
    'volume': int,
    'currentSong': str,
    'playlist': list,
    'currentSongIndex': int  # Add this to track the current position in playlist
}

def get_customers() -> Optional[List[Dict[str, Any]]]:
    """
    Get all customers from DynamoDB.
    
    Returns:
        List of customer dictionaries, or None if error
    """
    if not CUSTOMERS_TABLE:
        logger.error("CUSTOMERS_TABLE environment variable not set")
        return None
    
    try:
        table = dynamodb.Table(CUSTOMERS_TABLE)
        response = table.scan()
        
        if 'Items' not in response:
            logger.warning("No customers found")
            return []
        
        return response['Items']
        
    except Exception as e:
        logger.error(f"Error getting customers: {str(e)}")
        return None

def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
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

def update_device_state(customer_id: str, device_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update the state of a device for a customer.
    
    Args:
        customer_id: The ID of the customer
        device_id: The ID of the device to update
        updates: Dictionary of fields to update and their new values
        
    Returns:
        Updated device data as a dictionary, or None if not found
    """
    if not CUSTOMERS_TABLE:
        logger.error("CUSTOMERS_TABLE environment variable not set")
        return None
    
    try:
        # Get the customer first
        customer = get_customer(customer_id)
        
        if not customer:
            logger.warning(f"Customer not found: {customer_id}")
            return None
        
        # Get the device
        device = customer.get('device', {})
        
        if not device:
            logger.warning(f"No device found for customer: {customer_id}")
            return None
            
        # Verify it's the correct device
        if device.get('id') != device_id:
            logger.warning(f"Device ID mismatch: expected {device_id}, found {device.get('id')}")
            return None
        
        # Validate updates
        update_expressions = []
        expression_values = {}
        expression_names = {}
        
        for field, value in updates.items():
            if field not in DEVICE_FIELDS:
                logger.warning(f"Invalid field: {field}")
                continue
                
            # Validate field type
            try:
                value = DEVICE_FIELDS[field](value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value for field {field}: {value}")
                continue
            
            # Add to update expression
            update_expressions.append(f"device.#attr_{field} = :val_{field}")
            expression_values[f":val_{field}"] = value
            expression_names[f"#attr_{field}"] = field
        
        if not update_expressions:
            logger.warning("No valid updates provided")
            return None
        
        # Update the device state
        table = dynamodb.Table(CUSTOMERS_TABLE)
        response = table.update_item(
            Key={'id': customer_id},
            UpdateExpression=f"SET {', '.join(update_expressions)}",
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
            ReturnValues='ALL_NEW'
        )
        
        if 'Attributes' not in response:
            logger.warning("Update successful but no attributes returned")
            return None
            
        return response['Attributes'].get('device')
        
    except ClientError as e:
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
            return {}
        
        # Convert list of items to dictionary keyed by level
        service_levels = {}
        for item in response['Items']:
            level = item.get('level')
            if level:
                service_levels[level] = item
        
        return service_levels
        
    except Exception as e:
        logger.error(f"Error getting service levels: {str(e)}")
        return None

# Alias for backward compatibility
get_service_level = get_service_levels 