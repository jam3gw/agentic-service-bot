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
    Get a specific customer from DynamoDB.
    
    Args:
        customer_id: The ID of the customer to retrieve
        
    Returns:
        Customer dictionary, or None if not found or error
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

def update_device_state(customer_id: str, device_id: str, new_power: str) -> Optional[Dict[str, Any]]:
    """
    Update the power of a device for a customer.
    
    Args:
        customer_id: The ID of the customer
        device_id: The ID of the device to update
        new_power: The new power state to set for the device
        
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
        
        # Update the device power
        device['power'] = new_power
        device['lastUpdated'] = datetime.now().isoformat()
        
        # Update the customer record in DynamoDB
        table = dynamodb.Table(CUSTOMERS_TABLE)
        table.update_item(
            Key={'id': customer_id},
            UpdateExpression='SET device = :device',
            ExpressionAttributeValues={':device': device}
        )
        
        logger.info(f"Updated device {device_id} power to {new_power}")
        return device
        
    except Exception as e:
        logger.error(f"Error updating device power: {str(e)}")
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