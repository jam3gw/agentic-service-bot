"""
Test file for the capability handler.

This module contains tests for the capability handler functions.
"""

import json
import unittest
from unittest.mock import patch, MagicMock

from handlers.capability_handler import handle_get_capabilities, generate_capabilities

class TestCapabilityHandler(unittest.TestCase):
    """Test cases for the capability handler functions."""

    @patch('handlers.capability_handler.get_service_levels')
    def test_handle_get_capabilities_success(self, mock_get_service_levels):
        """Test successful retrieval of capabilities."""
        # Setup mock
        mock_get_service_levels.return_value = {
            'basic': {
                'level': 'basic',
                'allowed_actions': ['status_check', 'volume_control'],
                'max_devices': 2,
                'support_priority': 'standard'
            },
            'premium': {
                'level': 'premium',
                'allowed_actions': ['status_check', 'volume_control', 'device_relocation', 'music_services'],
                'max_devices': 5,
                'support_priority': 'priority'
            },
            'enterprise': {
                'level': 'enterprise',
                'allowed_actions': ['status_check', 'volume_control', 'device_relocation', 'music_services', 'multi_room_audio', 'custom_routines'],
                'max_devices': 10,
                'support_priority': 'dedicated'
            }
        }

        # Call the function
        response = handle_get_capabilities({'Content-Type': 'application/json'})

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('capabilities', body)
        self.assertTrue(len(body['capabilities']) > 0)
        
        # Check structure of a capability
        capability = body['capabilities'][0]
        self.assertIn('id', capability)
        self.assertIn('name', capability)
        self.assertIn('description', capability)
        self.assertIn('category', capability)
        self.assertIn('basic', capability)
        self.assertIn('premium', capability)
        self.assertIn('enterprise', capability)

    @patch('handlers.capability_handler.get_service_levels')
    def test_handle_get_capabilities_service_levels_not_found(self, mock_get_service_levels):
        """Test handling of missing service levels."""
        # Setup mock
        mock_get_service_levels.return_value = None

        # Call the function
        response = handle_get_capabilities({'Content-Type': 'application/json'})

        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Failed to retrieve service levels')

    @patch('handlers.capability_handler.get_service_levels')
    def test_handle_get_capabilities_exception(self, mock_get_service_levels):
        """Test handling of exceptions."""
        # Setup mock to raise an exception
        mock_get_service_levels.side_effect = Exception("Test exception")

        # Call the function
        response = handle_get_capabilities({'Content-Type': 'application/json'})

        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Failed to retrieve capabilities')

    def test_generate_capabilities(self):
        """Test generation of capabilities from service levels."""
        # Create test service levels
        service_levels = {
            'basic': {
                'level': 'basic',
                'allowed_actions': ['status_check', 'volume_control'],
                'max_devices': 2,
                'support_priority': 'standard'
            },
            'premium': {
                'level': 'premium',
                'allowed_actions': ['status_check', 'volume_control', 'device_relocation', 'music_services'],
                'max_devices': 5,
                'support_priority': 'priority'
            },
            'enterprise': {
                'level': 'enterprise',
                'allowed_actions': ['status_check', 'volume_control', 'device_relocation', 'music_services', 'multi_room_audio', 'custom_routines'],
                'max_devices': 10,
                'support_priority': 'dedicated'
            }
        }

        # Call the function
        capabilities = generate_capabilities(service_levels)

        # Verify the result
        self.assertTrue(len(capabilities) > 0)
        
        # Check structure of capabilities
        for capability in capabilities:
            self.assertIn('id', capability)
            self.assertIn('name', capability)
            self.assertIn('description', capability)
            self.assertIn('category', capability)
            self.assertIn('basic', capability)
            self.assertIn('premium', capability)
            self.assertIn('enterprise', capability)
            
            # Verify that the boolean values make sense (enterprise should have all capabilities)
            if capability['enterprise']:
                # If available for enterprise, check if it's available for other levels
                pass
            if capability['premium']:
                # If available for premium, it might not be available for basic
                pass
            if capability['basic']:
                # If available for basic, it should be available for premium and enterprise
                self.assertTrue(capability['premium'])
                self.assertTrue(capability['enterprise'])

if __name__ == '__main__':
    unittest.main() 