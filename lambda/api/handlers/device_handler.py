"""
Device handler for the Agentic Service Bot API.

This module provides handlers for device-related API endpoints.
"""

import json
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import services
from services.dynamodb_service import get_customer_by_id, update_device_state

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
            'body': json.dumps({'error': 'Missing customer ID'})
        }
    
    try:
        # Get customer data from DynamoDB
        customer = get_customer_by_id(customer_id)
        
        if not customer:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Customer not found'})
            }
        
        # Transform devices to include additional fields
        devices = []
        for device in customer.get('devices', []):
            # Add default values for fields not in the original data model
            enhanced_device = {
                'id': device.get('id', ''),
                'type': device.get('type', ''),
                'name': f"{device.get('location', '').replace('_', ' ').title()} {device.get('type', '')}",
                'location': device.get('location', '').replace('_', ' ').title(),
                'state': device.get('state', 'off'),
                'capabilities': get_device_capabilities(device.get('type', '')),
                'lastUpdated': device.get('lastUpdated', '2023-03-01T14:30:45.123Z')
            }
            devices.append(enhanced_device)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'devices': devices})
        }
    
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Failed to retrieve devices'})
        }

def handle_update_device(customer_id: str, device_id: str, body: Dict[str, Any], cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle PATCH request to update device state.
    
    Args:
        customer_id: The ID of the customer
        device_id: The ID of the device to update
        body: Request body containing the new state
        cors_headers: CORS headers to include in the response
        
    Returns:
        API Gateway response with updated device data
    """
    if not customer_id or not device_id:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Missing customer ID or device ID'})
        }
    
    new_state = body.get('state')
    if not new_state:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Missing state in request body'})
        }
    
    try:
        # Update device state in DynamoDB
        updated_device = update_device_state(customer_id, device_id, new_state)
        
        if not updated_device:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Device not found'})
            }
        
        # Transform device to include additional fields
        enhanced_device = {
            'id': updated_device.get('id', ''),
            'type': updated_device.get('type', ''),
            'name': f"{updated_device.get('location', '').replace('_', ' ').title()} {updated_device.get('type', '')}",
            'location': updated_device.get('location', '').replace('_', ' ').title(),
            'state': updated_device.get('state', 'off'),
            'capabilities': get_device_capabilities(updated_device.get('type', '')),
            'lastUpdated': updated_device.get('lastUpdated', '2023-03-01T14:30:45.123Z')
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'device': enhanced_device})
        }
    
    except Exception as e:
        logger.error(f"Error updating device: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Failed to update device'})
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