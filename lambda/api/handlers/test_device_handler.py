"""
Test file for the device handler.

This module contains tests for the device handler functions.
"""

import json
import unittest
from unittest.mock import patch, MagicMock

from handlers.device_handler import handle_get_devices, handle_update_device, get_device_capabilities

class TestDeviceHandler(unittest.TestCase):
    """Test cases for the device handler functions."""

    @patch('handlers.device_handler.get_customer_by_id')
    def test_handle_get_devices_success(self, mock_get_customer):
        """Test successful retrieval of devices."""
        # Setup mock
        mock_get_customer.return_value = {
            'id': 'cust_123',
            'name': 'Test Customer',
            'service_level': 'premium',
            'devices': [
                {
                    'id': 'dev_001',
                    'type': 'SmartSpeaker',
                    'location': 'living_room',
                    'state': 'on'
                }
            ]
        }

        # Call the function
        response = handle_get_devices('cust_123', {'Content-Type': 'application/json'})

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('devices', body)
        self.assertEqual(len(body['devices']), 1)
        
        device = body['devices'][0]
        self.assertEqual(device['id'], 'dev_001')
        self.assertEqual(device['type'], 'SmartSpeaker')
        self.assertEqual(device['name'], 'Living Room SmartSpeaker')
        self.assertEqual(device['location'], 'Living Room')
        self.assertEqual(device['state'], 'on')
        self.assertIn('capabilities', device)
        self.assertIn('lastUpdated', device)

    @patch('handlers.device_handler.get_customer_by_id')
    def test_handle_get_devices_customer_not_found(self, mock_get_customer):
        """Test handling of non-existent customer."""
        # Setup mock
        mock_get_customer.return_value = None

        # Call the function
        response = handle_get_devices('cust_123', {'Content-Type': 'application/json'})

        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Customer not found')

    def test_handle_get_devices_missing_customer_id(self):
        """Test handling of missing customer ID."""
        # Call the function with empty customer ID
        response = handle_get_devices('', {'Content-Type': 'application/json'})

        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Missing customer ID')

    @patch('handlers.device_handler.update_device_state')
    def test_handle_update_device_success(self, mock_update_device):
        """Test successful update of device state."""
        # Setup mock
        mock_update_device.return_value = {
            'id': 'dev_001',
            'type': 'SmartSpeaker',
            'location': 'living_room',
            'state': 'off'
        }

        # Call the function
        response = handle_update_device('cust_123', 'dev_001', {'state': 'off'}, {'Content-Type': 'application/json'})

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('device', body)
        
        device = body['device']
        self.assertEqual(device['id'], 'dev_001')
        self.assertEqual(device['type'], 'SmartSpeaker')
        self.assertEqual(device['name'], 'Living Room SmartSpeaker')
        self.assertEqual(device['location'], 'Living Room')
        self.assertEqual(device['state'], 'off')
        self.assertIn('capabilities', device)
        self.assertIn('lastUpdated', device)

    @patch('handlers.device_handler.update_device_state')
    def test_handle_update_device_not_found(self, mock_update_device):
        """Test handling of non-existent device."""
        # Setup mock
        mock_update_device.return_value = None

        # Call the function
        response = handle_update_device('cust_123', 'dev_001', {'state': 'off'}, {'Content-Type': 'application/json'})

        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Device not found')

    def test_handle_update_device_missing_state(self):
        """Test handling of missing state in request body."""
        # Call the function with empty state
        response = handle_update_device('cust_123', 'dev_001', {}, {'Content-Type': 'application/json'})

        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Missing state in request body')

    def test_get_device_capabilities(self):
        """Test retrieval of device capabilities."""
        # Test for SmartSpeaker
        capabilities = get_device_capabilities('SmartSpeaker')
        self.assertIn('volume_control', capabilities)
        self.assertIn('music_playback', capabilities)
        self.assertIn('voice_control', capabilities)
        
        # Test for SmartLight
        capabilities = get_device_capabilities('SmartLight')
        self.assertIn('brightness_control', capabilities)
        self.assertIn('color_control', capabilities)
        self.assertIn('on_off', capabilities)
        
        # Test for unknown device type
        capabilities = get_device_capabilities('UnknownDevice')
        self.assertEqual(capabilities, [])

if __name__ == '__main__':
    unittest.main() 