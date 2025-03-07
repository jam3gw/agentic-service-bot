"""
Device handler for the Agentic Service Bot API.

This module provides functions for handling device-related API requests.
"""

# Standard library imports
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional
from decimal import Decimal

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Local application imports
import services.dynamodb_service as dynamodb_service
from utils import convert_decimal_to_float, convert_float_to_decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS headers for responses
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PATCH,DELETE,PUT',
    'Access-Control-Allow-Credentials': 'false',
}

def handle_get_devices(customer_id: str, cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET request for customer devices.
    
    Args:
        customer_id: The ID of the customer
        cors_headers: CORS headers to include in the response
        
    Returns:
        API Gateway response with devices data
    """
    if not customer_id:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Missing required parameter: customerId'
            })
        }
    
    try:
        logger.info(f"Retrieving devices for customer {customer_id}")
        
        # Get customer data from DynamoDB
        customer = dynamodb_service.get_customer(customer_id)
        
        if not customer:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': f"Customer {customer_id} not found"
                })
            }
        
        # Initialize devices array
        devices = []
        
        # Get the device
        device = customer.get('device', {})
        if device:
            # Add default values for fields not in the original data model
            enhanced_device = {
                'id': device.get('id', ''),
                'type': device.get('type', ''),
                'name': f"{device.get('location', '').replace('_', ' ').title()} {device.get('type', '')}",
                'location': device.get('location', '').replace('_', ' ').title(),
                'power': device.get('power', 'off'),
                'capabilities': get_device_capabilities(device.get('type', '')),
                'lastUpdated': device.get('lastUpdated', '2023-03-01T14:30:45.123Z')
            }
            devices.append(enhanced_device)
        
        # Convert Decimal objects to floats before serialization
        devices = convert_decimal_to_float(devices)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'devices': devices
            })
        }
    
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': f"Failed to retrieve devices for customer {customer_id}: {str(e)}"
            })
        }

def handle_update_device(customer_id: str, device_id: str, body: Dict[str, Any], cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle PATCH request to update device power.
    
    Args:
        customer_id: The ID of the customer
        device_id: The ID of the device to update
        body: Request body containing the new power
        cors_headers: CORS headers to include in the response
        
    Returns:
        API Gateway response with updated device data
    """
    if not customer_id or not device_id:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Missing required parameters: customerId and deviceId'
            })
        }
    
    new_power = body.get('power')
    if not new_power:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Missing required parameter: power'
            })
        }
    
    try:
        # Convert any float values to Decimal for DynamoDB
        new_power = convert_float_to_decimal(new_power)
        
        # Update device power in DynamoDB
        updated_device = dynamodb_service.update_device_state(customer_id, device_id, new_power)
        
        if not updated_device:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': f"Device {device_id} not found for customer {customer_id}"
                })
            }
        
        # Convert Decimal objects to floats before serialization
        updated_device = convert_decimal_to_float(updated_device)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'device': updated_device
            })
        }
    
    except Exception as e:
        logger.error(f"Error updating device: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': f"Failed to update device {device_id} for customer {customer_id}: {str(e)}"
            })
        }

def get_device_capabilities(device_type: str) -> List[str]:
    """
    Get capabilities for a device type.
    
    Args:
        device_type: The type of device
        
    Returns:
        List of capability strings
    """
    # Map device types to capabilities
    capability_map = {
        'SmartSpeaker': ['volume_control', 'music_playback', 'voice_control'],
        'SmartLight': ['brightness_control', 'color_control', 'on_off'],
        'SmartThermostat': ['temperature_control', 'schedule', 'energy_saving'],
        'SmartLock': ['lock_unlock', 'access_log', 'remote_access'],
        'SmartCamera': ['video_streaming', 'motion_detection', 'recording'],
        'SmartPlug': ['on_off', 'energy_monitoring', 'scheduling']
    }
    
    return capability_map.get(device_type, []) 