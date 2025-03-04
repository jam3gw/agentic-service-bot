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

    @patch('services.dynamodb_service.dynamodb.Table')
    def test_get_customer_by_id_success(self, mock_table_constructor):
        """Test successful retrieval of a customer by ID."""
        # Setup mock
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'test-customer-id',
                'name': 'Test Customer',
                'email': 'test@example.com',
                'service_level': 'premium',
                'devices': [
                    {
                        'id': 'device1',
                        'type': 'speaker',
                        'location': 'living room',
                        'state': {
                            'power': 'on',
                            'volume': 50
                        }
                    }
                ]
            },
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            }
        }
        mock_table_constructor.return_value = mock_table

        # Call the function
        result = get_customer_by_id('test-customer-id')

        # Verify the result
        self.assertIsNotNone(result, "Result should not be None")
        self.assertEqual(result['id'], 'test-customer-id', "Customer ID should match")
        self.assertEqual(result['name'], 'Test Customer', "Customer name should match")
        self.assertEqual(result['service_level'], 'premium', "Service level should match")
        self.assertEqual(len(result['devices']), 1, "Should have one device")
        self.assertEqual(result['devices'][0]['id'], 'device1', "Device ID should match")

        # Verify the mock was called correctly
        mock_table_constructor.assert_called_once_with('test-customers')
        mock_table.get_item.assert_called_once_with(Key={'id': 'test-customer-id'})

    @patch('services.dynamodb_service.dynamodb.Table')
    def test_get_customer_by_id_not_found(self, mock_table_constructor):
        """Test handling of a non-existent customer."""
        # Setup mock
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            }
            # No 'Item' in response
        }
        mock_table_constructor.return_value = mock_table

        # Call the function
        result = get_customer_by_id('non-existent-id')

        # Verify the result
        self.assertIsNone(result, "Result should be None for non-existent customer")

        # Verify the mock was called correctly
        mock_table_constructor.assert_called_once_with('test-customers')
        mock_table.get_item.assert_called_once_with(Key={'id': 'non-existent-id'})

    @patch('services.dynamodb_service.dynamodb.Table')
    def test_get_customer_by_id_exception(self, mock_table_constructor):
        """Test handling of exceptions during customer retrieval."""
        # Setup mock to raise an exception
        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("Test exception")
        mock_table_constructor.return_value = mock_table

        # Call the function
        result = get_customer_by_id('test-customer-id')

        # Verify the result
        self.assertIsNone(result, "Result should be None when an exception occurs")

        # Verify the mock was called correctly
        mock_table_constructor.assert_called_once_with('test-customers')
        mock_table.get_item.assert_called_once_with(Key={'id': 'test-customer-id'})

    @patch('services.dynamodb_service.get_customer_by_id')
    @patch('boto3.resource')
    def test_update_device_state_success(self, mock_boto3_resource, mock_get_customer):
        """Test successful update of device state."""
        # Setup mock for get_customer_by_id
        customer_data = {
            'id': 'test-customer-id',
            'name': 'Test Customer',
            'email': 'test@example.com',
            'service_level': 'premium',
            'devices': [
                {
                    'id': 'device1',
                    'type': 'speaker',
                    'location': 'living room',
                    'state': {
                        'power': 'on',
                        'volume': 50
                    }
                }
            ]
        }
        
        # Mock get_customer_by_id to return our test customer
        mock_get_customer.return_value = customer_data
        
        # Create a copy of the devices list that we can modify
        updated_devices = customer_data['devices'].copy()
        # Update the device state in our copy
        updated_devices[0]['state'] = {'power': 'off', 'volume': 50}
        updated_devices[0]['lastUpdated'] = datetime.now().isoformat()
        
        # Setup mock table with proper response for update_item
        mock_table = MagicMock()
        mock_table.update_item.return_value = {
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            }
        }
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Call the function with a patch to ensure the update_item doesn't fail
        with patch('services.dynamodb_service.dynamodb.Table') as mock_table_constructor:
            mock_table_constructor.return_value = mock_table
            result = update_device_state('test-customer-id', 'device1', {'power': 'off'})

        # Verify the result
        self.assertIsNotNone(result, "Result should not be None")
        self.assertEqual(result['id'], 'device1', "Device ID should match")
        self.assertEqual(result['state']['power'], 'off', "Power state should be updated")
        self.assertIn('lastUpdated', result, "Should include lastUpdated timestamp")

        # Verify the mocks were called correctly
        mock_get_customer.assert_called_once_with('test-customer-id')
        mock_table.update_item.assert_called_once()
        
        # Verify update_item was called with correct parameters
        args, kwargs = mock_table.update_item.call_args
        self.assertEqual(kwargs['Key'], {'id': 'test-customer-id'}, "Key should match customer ID")
        self.assertIn('UpdateExpression', kwargs, "Should include UpdateExpression")
        self.assertEqual(kwargs['UpdateExpression'], 'SET devices = :devices', "UpdateExpression should update devices")
        self.assertIn('ExpressionAttributeValues', kwargs, "Should include ExpressionAttributeValues")

    @patch('services.dynamodb_service.get_customer_by_id')
    def test_update_device_state_customer_not_found(self, mock_get_customer):
        """Test handling of a non-existent customer during device state update."""
        # Setup mock to return None for customer
        mock_get_customer.return_value = None

        # Call the function
        result = update_device_state('non-existent-id', 'device1', {'power': 'off'})

        # Verify the result
        self.assertIsNone(result, "Result should be None for non-existent customer")

        # Verify the mock was called correctly
        mock_get_customer.assert_called_once_with('non-existent-id')

    @patch('services.dynamodb_service.get_customer_by_id')
    def test_update_device_state_device_not_found(self, mock_get_customer):
        """Test handling of a non-existent device during device state update."""
        # Setup mock to return a customer without the requested device
        customer_data = {
            'id': 'test-customer-id',
            'name': 'Test Customer',
            'email': 'test@example.com',
            'service_level': 'premium',
            'devices': [
                {
                    'id': 'device1',
                    'type': 'speaker',
                    'location': 'living room',
                    'state': {
                        'power': 'on',
                        'volume': 50
                    }
                }
            ]
        }
        mock_get_customer.return_value = customer_data

        # Call the function
        result = update_device_state('test-customer-id', 'non-existent-device', {'power': 'off'})

        # Verify the result
        self.assertIsNone(result, "Result should be None for non-existent device")

        # Verify the mock was called correctly
        mock_get_customer.assert_called_once_with('test-customer-id')

    @patch('services.dynamodb_service.dynamodb.Table')
    def test_get_service_levels_success(self, mock_table_constructor):
        """Test successful retrieval of service levels."""
        # Setup mock with proper response structure for scan
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
            ],
            'Count': 2,
            'ScannedCount': 2,
            'ResponseMetadata': {
                'RequestId': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'HTTPStatusCode': 200,
                'HTTPHeaders': {
                    'content-type': 'application/x-amz-json-1.0',
                    'x-amz-crc32': '1234567890',
                    'x-amzn-requestid': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                    'content-length': '1234',
                    'date': 'Wed, 01 Jan 2023 12:00:00 GMT'
                },
                'RetryAttempts': 0
            }
        }
        mock_table_constructor.return_value = mock_table

        # Call the function
        result = get_service_levels()

        # Verify the result
        self.assertIsNotNone(result, "Result should not be None")
        self.assertEqual(len(result), 2, "Should have two service levels")
        self.assertIn('basic', result, "Should include basic service level")
        self.assertIn('premium', result, "Should include premium service level")
        self.assertEqual(result['basic']['max_devices'], 2, "Basic should allow 2 devices")
        self.assertEqual(result['premium']['max_devices'], 5, "Premium should allow 5 devices")

        # Verify the mock was called correctly
        mock_table_constructor.assert_called_once_with('test-service-levels')
        mock_table.scan.assert_called_once()

    @patch('services.dynamodb_service.dynamodb.Table')
    def test_get_service_levels_no_items(self, mock_table_constructor):
        """Test handling of no service levels found."""
        # Setup mock with proper response structure but no items
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [],  # Empty items list
            'Count': 0,
            'ScannedCount': 0,
            'ResponseMetadata': {
                'RequestId': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'HTTPStatusCode': 200,
                'HTTPHeaders': {
                    'content-type': 'application/x-amz-json-1.0',
                    'x-amz-crc32': '1234567890',
                    'x-amzn-requestid': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                    'content-length': '1234',
                    'date': 'Wed, 01 Jan 2023 12:00:00 GMT'
                },
                'RetryAttempts': 0
            }
        }
        mock_table_constructor.return_value = mock_table

        # Call the function
        result = get_service_levels()

        # Verify the result
        self.assertEqual(result, {}, "Result should be an empty dictionary when no service levels found")

        # Verify the mock was called correctly
        mock_table_constructor.assert_called_once_with('test-service-levels')
        mock_table.scan.assert_called_once()

    @patch('services.dynamodb_service.dynamodb.Table')
    def test_get_service_levels_exception(self, mock_table_constructor):
        """Test handling of exceptions during service level retrieval."""
        # Setup mock to raise an exception
        mock_table = MagicMock()
        mock_table.scan.side_effect = Exception("Test exception")
        mock_table_constructor.return_value = mock_table

        # Call the function
        result = get_service_levels()

        # Verify the result
        self.assertIsNone(result, "Result should be None when an exception occurs")

        # Verify the mock was called correctly
        mock_table_constructor.assert_called_once_with('test-service-levels')
        mock_table.scan.assert_called_once()

if __name__ == '__main__':
    unittest.main() 