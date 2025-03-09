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
                'name': device.get('type', ''),  # Just use the device type as name
                'power': device.get('power', 'off'),
                'capabilities': get_device_capabilities(device.get('type', '')),
                'lastUpdated': device.get('lastUpdated', '2023-03-01T14:30:45.123Z')
            }

            # Add volume and currentSong for audio devices
            if device.get('type') in ['audio', 'speaker']:
                enhanced_device['volume'] = device.get('volume', '0')
                enhanced_device['playlist'] = device.get('playlist', [
                    "Let's Get It Started - The Black Eyed Peas",
                    "Imagine - John Lennon",
                    "Don't Stop Believin' - Journey",
                    "Sweet Caroline - Neil Diamond",
                    "I Wanna Dance with Somebody - Whitney Houston",
                    "Walking on Sunshine - Katrina & The Waves",
                    "Happy - Pharrell Williams",
                    "Uptown Funk - Mark Ronson ft. Bruno Mars",
                    "Can't Stop the Feeling! - Justin Timberlake",
                    "Good Vibrations - The Beach Boys",
                    "Three Little Birds - Bob Marley & The Wailers"
                ])
                # Convert Decimal to int for list indexing
                current_song_index = int(device.get('currentSongIndex', 0))
                enhanced_device['currentSongIndex'] = current_song_index
                # Always determine current song from the index
                if enhanced_device.get('playlist'):
                    enhanced_device['currentSong'] = enhanced_device['playlist'][current_song_index]
                else:
                    enhanced_device['currentSong'] = 'No song playing'

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
        body: Request body containing the updates
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
    
    try:
        # Get current device state first
        customer = dynamodb_service.get_customer(customer_id)
        if not customer or 'device' not in customer:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': f"Device {device_id} not found for customer {customer_id}"
                })
            }
        
        device = customer['device']
        updates = {}
        
        # Handle basic updates
        if 'power' in body:
            updates['power'] = body['power']
        if 'volume' in body:
            updates['volume'] = body['volume']
            
        # Handle playlist operations
        if 'songAction' in body:
            current_playlist = device.get('playlist', [])
            # Convert Decimal to int for list indexing
            current_index = int(device.get('currentSongIndex', 0))
            
            if not current_playlist:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({
                        'error': 'No playlist available'
                    })
                }
            
            if body['songAction'] == 'next':
                # Move to next song, loop back to start if at end
                next_index = (current_index + 1) % len(current_playlist)
                updates['currentSongIndex'] = next_index
                updates['currentSong'] = current_playlist[next_index]
            elif body['songAction'] == 'previous':
                # Move to previous song, loop to end if at start
                prev_index = (current_index - 1) % len(current_playlist)
                updates['currentSongIndex'] = prev_index
                updates['currentSong'] = current_playlist[prev_index]
            elif body['songAction'] == 'specific' and 'songIndex' in body:
                # Change to specific song by index
                requested_index = int(body['songIndex'])  # Convert to int in case it's a string
                if 0 <= requested_index < len(current_playlist):
                    updates['currentSongIndex'] = requested_index
                    updates['currentSong'] = current_playlist[requested_index]
                else:
                    return {
                        'statusCode': 400,
                        'headers': cors_headers,
                        'body': json.dumps({
                            'error': f"Invalid song index: {requested_index}"
                        })
                    }
        
        if not updates:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'No valid updates provided'
                })
            }
        
        # Convert any float values to Decimal for DynamoDB
        updates = convert_float_to_decimal(updates)
        
        # Update device in DynamoDB
        updated_device = dynamodb_service.update_device_state(customer_id, device_id, updates)
        
        if not updated_device:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': f"Failed to update device {device_id}"
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