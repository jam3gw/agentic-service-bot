"""
Test file for the DynamoDB service.

This module contains tests for the DynamoDB service functions.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import boto3
from datetime import datetime

from services.dynamodb_service import get_customer_by_id, update_device_state, get_service_levels

class TestDynamoDBService(unittest.TestCase):
    """Test cases for the DynamoDB service functions."""

    def setUp(self):
        """Set up test environment."""
        # Set environment variables for testing
        os.environ['CUSTOMERS_TABLE'] = 'test-customers'
        os.environ['SERVICE_LEVELS_TABLE'] = 'test-service-levels'

    def tearDown(self):
        """Clean up test environment."""
        # Remove environment variables
        if 'CUSTOMERS_TABLE' in os.environ:
            del os.environ['CUSTOMERS_TABLE']
        if 'SERVICE_LEVELS_TABLE' in os.environ:
            del os.environ['SERVICE_LEVELS_TABLE']

    @patch('boto3.resource')
    def test_get_customer_by_id_success(self, mock_boto3_resource):
        """Test successful retrieval of customer."""
        # Setup mock
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'cust_123',
                'name': 'Test Customer',
                'service_level': 'premium',
                'devices': [
                    {
                        'id': 'dev_001',
                        'type': 'SmartSpeaker',
                        'location': 'living_room'
                    }
                ]
            }
        }
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Call the function
        result = get_customer_by_id('cust_123')

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 'cust_123')
        self.assertEqual(result['name'], 'Test Customer')
        self.assertEqual(result['service_level'], 'premium')
        self.assertEqual(len(result['devices']), 1)
        self.assertEqual(result['devices'][0]['id'], 'dev_001')

        # Verify the mock was called correctly
        mock_boto3_resource.assert_called_once_with('dynamodb')
        mock_dynamodb.Table.assert_called_once_with('test-customers')
        mock_table.get_item.assert_called_once_with(Key={'id': 'cust_123'})

    @patch('boto3.resource')
    def test_get_customer_by_id_not_found(self, mock_boto3_resource):
        """Test handling of non-existent customer."""
        # Setup mock
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No Item in response
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Call the function
        result = get_customer_by_id('cust_123')

        # Verify the result
        self.assertIsNone(result)

    @patch('boto3.resource')
    def test_get_customer_by_id_exception(self, mock_boto3_resource):
        """Test handling of exceptions."""
        # Setup mock to raise an exception
        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("Test exception")
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Call the function
        result = get_customer_by_id('cust_123')

        # Verify the result
        self.assertIsNone(result)

    @patch('services.dynamodb_service.get_customer_by_id')
    @patch('boto3.resource')
    def test_update_device_state_success(self, mock_boto3_resource, mock_get_customer):
        """Test successful update of device state."""
        # Setup mocks
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
        
        mock_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Call the function
        result = update_device_state('cust_123', 'dev_001', 'off')

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 'dev_001')
        self.assertEqual(result['type'], 'SmartSpeaker')
        self.assertEqual(result['location'], 'living_room')
        self.assertEqual(result['state'], 'off')
        self.assertIn('lastUpdated', result)

        # Verify the mock was called correctly
        mock_get_customer.assert_called_once_with('cust_123')
        mock_boto3_resource.assert_called_once_with('dynamodb')
        mock_dynamodb.Table.assert_called_once_with('test-customers')
        mock_table.update_item.assert_called_once()

    @patch('services.dynamodb_service.get_customer_by_id')
    def test_update_device_state_customer_not_found(self, mock_get_customer):
        """Test handling of non-existent customer."""
        # Setup mock
        mock_get_customer.return_value = None

        # Call the function
        result = update_device_state('cust_123', 'dev_001', 'off')

        # Verify the result
        self.assertIsNone(result)

    @patch('services.dynamodb_service.get_customer_by_id')
    def test_update_device_state_device_not_found(self, mock_get_customer):
        """Test handling of non-existent device."""
        # Setup mock
        mock_get_customer.return_value = {
            'id': 'cust_123',
            'name': 'Test Customer',
            'service_level': 'premium',
            'devices': [
                {
                    'id': 'dev_002',  # Different device ID
                    'type': 'SmartSpeaker',
                    'location': 'living_room',
                    'state': 'on'
                }
            ]
        }

        # Call the function
        result = update_device_state('cust_123', 'dev_001', 'off')

        # Verify the result
        self.assertIsNone(result)

    @patch('boto3.resource')
    def test_get_service_levels_success(self, mock_boto3_resource):
        """Test successful retrieval of service levels."""
        # Setup mock
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'level': 'basic',
                    'allowed_actions': ['status_check', 'volume_control'],
                    'max_devices': 2,
                    'support_priority': 'standard'
                },
                {
                    'level': 'premium',
                    'allowed_actions': ['status_check', 'volume_control', 'device_relocation', 'music_services'],
                    'max_devices': 5,
                    'support_priority': 'priority'
                }
            ]
        }
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Call the function
        result = get_service_levels()

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertIn('basic', result)
        self.assertIn('premium', result)
        self.assertEqual(result['basic']['max_devices'], 2)
        self.assertEqual(result['premium']['max_devices'], 5)

        # Verify the mock was called correctly
        mock_boto3_resource.assert_called_once_with('dynamodb')
        mock_dynamodb.Table.assert_called_once_with('test-service-levels')
        mock_table.scan.assert_called_once()

    @patch('boto3.resource')
    def test_get_service_levels_no_items(self, mock_boto3_resource):
        """Test handling of no service levels found."""
        # Setup mock
        mock_table = MagicMock()
        mock_table.scan.return_value = {}  # No Items in response
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Call the function
        result = get_service_levels()

        # Verify the result
        self.assertIsNone(result)

    @patch('boto3.resource')
    def test_get_service_levels_exception(self, mock_boto3_resource):
        """Test handling of exceptions."""
        # Setup mock to raise an exception
        mock_table = MagicMock()
        mock_table.scan.side_effect = Exception("Test exception")
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Call the function
        result = get_service_levels()

        # Verify the result
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main() 