"""
Capability handler for the Agentic Service Bot API.

This module provides functions for handling capability-related API requests.
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

def handle_get_capabilities(cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET request to retrieve all capabilities.
    
    Args:
        cors_headers: CORS headers to include in the response
        
    Returns:
        API Gateway response with capability data
    """
    try:
        logger.info("Retrieving all capabilities")
        
        # Get service levels from DynamoDB
        service_levels = dynamodb_service.get_service_levels()
        
        if not service_levels:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Failed to retrieve service levels'})
            }
        
        # Transform service levels into capabilities
        capabilities = generate_capabilities(service_levels)
        
        # Convert Decimal objects to floats before serialization
        capabilities = convert_decimal_to_float(capabilities)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'capabilities': capabilities
            })
        }
    
    except Exception as e:
        logger.error(f"Error getting capabilities: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': f"Failed to retrieve capabilities: {str(e)}"
            })
        }

def generate_capabilities(service_levels: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate capabilities list from service levels.
    
    Args:
        service_levels: Dictionary of service levels
        
    Returns:
        List of capability objects
    """
    # Define all capabilities with their categories
    all_capabilities = [
        # Device Control capabilities
        {
            'id': 'cap_001',
            'name': 'Device Status Check',
            'description': 'Check the status of smart home devices',
            'category': 'device-control'
        },
        {
            'id': 'cap_006',
            'name': 'Device Power Control',
            'description': 'Turn devices on and off',
            'category': 'device-control'
        },
        {
            'id': 'cap_002',
            'name': 'Volume Control',
            'description': 'Adjust volume of audio devices',
            'category': 'device-control'
        },
        {
            'id': 'cap_003',
            'name': 'Song Changes',
            'description': 'Change songs and manage playlists',
            'category': 'device-control'
        },
    ]
    
    # Map capabilities to service levels
    capability_mapping = {
        # Basic level capabilities
        'basic': [
            'cap_001',  # Device Status Check
            'cap_006',  # Device Power Control
            'cap_501'   # Device Limit
        ],
        
        # Premium level capabilities (includes all basic)
        'premium': [
            'cap_001',  # Device Status Check
            'cap_006',  # Device Power Control
            'cap_002',  # Volume Control
            'cap_501'   # Device Limit
        ],
        
        # Enterprise level capabilities (includes basic and premium capabilities plus song changes)
        'enterprise': [
            'cap_001',  # Device Status Check
            'cap_006',  # Device Power Control
            'cap_002',  # Volume Control
            'cap_003',  # Song Changes
            'cap_501'   # Device Limit
        ]
    }
    
    # Enhance capabilities with service level availability
    enhanced_capabilities = []
    for capability in all_capabilities:
        capability_id = capability['id']
        enhanced_capability = {
            **capability,
            'tiers': {
                'basic': capability_id in capability_mapping.get('basic', []),
                'premium': capability_id in capability_mapping.get('premium', []),
                'enterprise': capability_id in capability_mapping.get('enterprise', [])
            }
        }
        enhanced_capabilities.append(enhanced_capability)
    
    return enhanced_capabilities 

def handle_get_capability(capability_id: str, cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET request to retrieve a specific capability.
    
    Args:
        capability_id: The ID of the capability to retrieve
        cors_headers: CORS headers to include in the response
        
    Returns:
        API Gateway response with capability data
    """
    try:
        logger.info(f"Retrieving capability: {capability_id}")
        
        # Get service levels from DynamoDB
        service_levels = dynamodb_service.get_service_levels()
        
        if not service_levels:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Failed to retrieve service levels'})
            }
        
        # Generate capabilities from service levels
        capabilities = generate_capabilities(service_levels)
        
        # Find the requested capability
        capability = next((c for c in capabilities if c.get('id') == capability_id), None)
        
        if not capability:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Capability not found: {capability_id}'})
            }
        
        # Return the capability
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(capability)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving capability: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f'Error retrieving capability: {str(e)}'})
        } 