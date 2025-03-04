"""
Capability handler for the Agentic Service Bot API.

This module provides handlers for capability-related API endpoints.
"""

import json
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import services
from services.dynamodb_service import get_service_levels

def handle_get_capabilities(cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET request for service capabilities.
    
    Args:
        cors_headers: CORS headers to include in the response
        
    Returns:
        API Gateway response with capabilities data
    """
    try:
        # Get service levels from DynamoDB
        service_levels = get_service_levels()
        
        if not service_levels:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Failed to retrieve service levels'})
            }
        
        # Transform service levels into capabilities
        capabilities = generate_capabilities(service_levels)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'capabilities': capabilities})
        }
    
    except Exception as e:
        logger.error(f"Error getting capabilities: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Failed to retrieve capabilities'})
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
            'id': 'cap_002',
            'name': 'Volume Control',
            'description': 'Adjust volume of audio devices',
            'category': 'device-control'
        },
        {
            'id': 'cap_003',
            'name': 'Light Control',
            'description': 'Turn lights on/off and adjust brightness',
            'category': 'device-control'
        },
        {
            'id': 'cap_004',
            'name': 'Temperature Control',
            'description': 'Adjust thermostat temperature',
            'category': 'device-control'
        },
        {
            'id': 'cap_005',
            'name': 'Multi-room Audio',
            'description': 'Play audio across multiple speakers',
            'category': 'device-control'
        },
        
        # Automation capabilities
        {
            'id': 'cap_101',
            'name': 'Basic Routines',
            'description': 'Create simple automation routines',
            'category': 'automation'
        },
        {
            'id': 'cap_102',
            'name': 'Advanced Routines',
            'description': 'Create complex automation routines with conditions',
            'category': 'automation'
        },
        {
            'id': 'cap_103',
            'name': 'Scheduled Actions',
            'description': 'Schedule device actions at specific times',
            'category': 'automation'
        },
        
        # Security capabilities
        {
            'id': 'cap_201',
            'name': 'Basic Security',
            'description': 'Basic security monitoring',
            'category': 'security'
        },
        {
            'id': 'cap_202',
            'name': 'Advanced Security',
            'description': 'Advanced security monitoring and alerts',
            'category': 'security'
        },
        {
            'id': 'cap_203',
            'name': 'Remote Lock Control',
            'description': 'Control smart locks remotely',
            'category': 'security'
        },
        
        # Integration capabilities
        {
            'id': 'cap_301',
            'name': 'Music Services',
            'description': 'Integration with music streaming services',
            'category': 'integration'
        },
        {
            'id': 'cap_302',
            'name': 'Weather Services',
            'description': 'Integration with weather services',
            'category': 'integration'
        },
        {
            'id': 'cap_303',
            'name': 'Third-party Integrations',
            'description': 'Integration with third-party smart home systems',
            'category': 'integration'
        },
        
        # Analytics capabilities
        {
            'id': 'cap_401',
            'name': 'Basic Usage Stats',
            'description': 'View basic device usage statistics',
            'category': 'analytics'
        },
        {
            'id': 'cap_402',
            'name': 'Advanced Analytics',
            'description': 'Detailed analytics and insights',
            'category': 'analytics'
        },
        {
            'id': 'cap_403',
            'name': 'Energy Monitoring',
            'description': 'Monitor energy usage of compatible devices',
            'category': 'analytics'
        }
    ]
    
    # Map capabilities to service levels
    capability_mapping = {
        # Basic level capabilities
        'basic': [
            'cap_001',  # Device Status Check
            'cap_002',  # Volume Control
            'cap_003',  # Light Control
            'cap_101',  # Basic Routines
            'cap_201',  # Basic Security
            'cap_301',  # Music Services
            'cap_401'   # Basic Usage Stats
        ],
        
        # Premium level capabilities (includes all basic)
        'premium': [
            'cap_001',  # Device Status Check
            'cap_002',  # Volume Control
            'cap_003',  # Light Control
            'cap_004',  # Temperature Control
            'cap_005',  # Multi-room Audio
            'cap_101',  # Basic Routines
            'cap_102',  # Advanced Routines
            'cap_201',  # Basic Security
            'cap_202',  # Advanced Security
            'cap_301',  # Music Services
            'cap_302',  # Weather Services
            'cap_401',  # Basic Usage Stats
            'cap_402'   # Advanced Analytics
        ],
        
        # Enterprise level capabilities (includes all)
        'enterprise': [
            'cap_001',  # Device Status Check
            'cap_002',  # Volume Control
            'cap_003',  # Light Control
            'cap_004',  # Temperature Control
            'cap_005',  # Multi-room Audio
            'cap_101',  # Basic Routines
            'cap_102',  # Advanced Routines
            'cap_103',  # Scheduled Actions
            'cap_201',  # Basic Security
            'cap_202',  # Advanced Security
            'cap_203',  # Remote Lock Control
            'cap_301',  # Music Services
            'cap_302',  # Weather Services
            'cap_303',  # Third-party Integrations
            'cap_401',  # Basic Usage Stats
            'cap_402',  # Advanced Analytics
            'cap_403'   # Energy Monitoring
        ]
    }
    
    # Enhance capabilities with service level availability
    enhanced_capabilities = []
    for capability in all_capabilities:
        capability_id = capability['id']
        enhanced_capability = {
            **capability,
            'basic': capability_id in capability_mapping.get('basic', []),
            'premium': capability_id in capability_mapping.get('premium', []),
            'enterprise': capability_id in capability_mapping.get('enterprise', [])
        }
        enhanced_capabilities.append(enhanced_capability)
    
    return enhanced_capabilities 