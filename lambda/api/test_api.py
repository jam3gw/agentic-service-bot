"""
Test file for the API Lambda function.

This module contains tests for the API Lambda function that handles
device and capability endpoints.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the Lambda handler
from index import handler

class TestApiLambda(unittest.TestCase):
    """Test cases for the API Lambda function."""

    @patch('index.handle_get_devices')
    def test_get_devices_endpoint(self, mock_handle_get_devices):
        """Test the GET /api/customers/{customerId}/devices endpoint."""
        # Setup mock
        mock_handle_get_devices.return_value = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'devices': []})
        }

        # Create test event
        event = {
            'httpMethod': 'GET',
            'path': '/api/customers/cust_123/devices',
            'pathParameters': {'customerId': 'cust_123'}
        }

        # Call the handler
        response = handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        mock_handle_get_devices.assert_called_once_with('cust_123', {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type,Authorization', 'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PATCH,DELETE', 'Access-Control-Allow-Credentials': 'true'})

    @patch('index.handle_update_device')
    def test_update_device_endpoint(self, mock_handle_update_device):
        """Test the PATCH /api/customers/{customerId}/devices/{deviceId} endpoint."""
        # Setup mock
        mock_handle_update_device.return_value = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'device': {}})
        }

        # Create test event
        event = {
            'httpMethod': 'PATCH',
            'path': '/api/customers/cust_123/devices/dev_456',
            'pathParameters': {'customerId': 'cust_123', 'deviceId': 'dev_456'},
            'body': json.dumps({'state': 'on'})
        }

        # Call the handler
        response = handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        mock_handle_update_device.assert_called_once_with('cust_123', 'dev_456', {'state': 'on'}, {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type,Authorization', 'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PATCH,DELETE', 'Access-Control-Allow-Credentials': 'true'})

    @patch('index.handle_get_capabilities')
    def test_get_capabilities_endpoint(self, mock_handle_get_capabilities):
        """Test the GET /api/capabilities endpoint."""
        # Setup mock
        mock_handle_get_capabilities.return_value = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'capabilities': []})
        }

        # Create test event
        event = {
            'httpMethod': 'GET',
            'path': '/api/capabilities',
            'pathParameters': {}
        }

        # Call the handler
        response = handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        mock_handle_get_capabilities.assert_called_once_with({'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type,Authorization', 'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PATCH,DELETE', 'Access-Control-Allow-Credentials': 'true'})

    def test_not_found_endpoint(self):
        """Test handling of non-existent endpoints."""
        # Create test event for non-existent endpoint
        event = {
            'httpMethod': 'GET',
            'path': '/api/nonexistent',
            'pathParameters': {}
        }

        # Call the handler
        response = handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        self.assertIn('error', json.loads(response['body']))

    def test_options_request(self):
        """Test handling of OPTIONS requests (CORS preflight)."""
        # Create test event for OPTIONS request
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/api/customers/cust_123/devices',
            'pathParameters': {'customerId': 'cust_123'}
        }

        # Call the handler
        response = handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], '')
        self.assertIn('Access-Control-Allow-Origin', response['headers'])
        self.assertIn('Access-Control-Allow-Methods', response['headers'])

if __name__ == '__main__':
    unittest.main() 