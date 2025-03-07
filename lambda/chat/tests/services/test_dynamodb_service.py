import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from datetime import datetime

# Add the parent directory to sys.path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from services.dynamodb_service import update_device_state
from models.customer import Customer

class TestDynamoDBService(unittest.TestCase):
    """Tests for the DynamoDB service functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a patcher for the customers_table
        self.customers_table_patcher = patch('services.dynamodb_service.customers_table')
        self.mock_customers_table = self.customers_table_patcher.start()
        
    def tearDown(self):
        """Clean up after tests."""
        self.customers_table_patcher.stop()
    
    def test_update_device_state_success(self):
        """Test updating a device state successfully."""
        # Mock data
        customer_id = "test-customer"
        device_id = "test-customer-device-1"
        state_updates = {"state": "on"}
        
        # Mock the get_item response
        mock_get_response = {
            'Item': {
                'id': customer_id,
                'name': 'Test Customer',
                'service_level': 'basic',
                'device': {
                    'id': device_id,
                    'type': 'speaker',
                    'state': 'off',
                    'location': 'living_room'
                }
            }
        }
        self.mock_customers_table.get_item.return_value = mock_get_response
        
        # Mock the update_item response
        mock_update_response = {
            'ResponseMetadata': {'HTTPStatusCode': 200},
            'Attributes': {
                'device': {
                    'id': device_id,
                    'type': 'speaker',
                    'state': 'on',
                    'location': 'living_room'
                }
            }
        }
        self.mock_customers_table.update_item.return_value = mock_update_response
        
        # Call the function
        result = update_device_state(customer_id, device_id, state_updates)
        
        # Assertions
        self.assertTrue(result)
        self.mock_customers_table.get_item.assert_called_once_with(Key={'id': customer_id})
        
        # Verify the update_item call
        self.mock_customers_table.update_item.assert_called_once()
        call_args = self.mock_customers_table.update_item.call_args[1]
        self.assertEqual(call_args['Key'], {'id': customer_id})
        self.assertTrue('device.state = :val_state' in call_args['UpdateExpression'])
        self.assertEqual(call_args['ExpressionAttributeValues'][':val_state'], 'on')
    
    def test_update_device_state_customer_not_found(self):
        """Test updating a device state when the customer is not found."""
        # Mock data
        customer_id = "nonexistent-customer"
        device_id = "nonexistent-customer-device-1"
        state_updates = {"state": "on"}
        
        # Mock the get_item response for a nonexistent customer
        self.mock_customers_table.get_item.return_value = {}
        
        # Call the function
        result = update_device_state(customer_id, device_id, state_updates)
        
        # Assertions
        self.assertFalse(result)
        self.mock_customers_table.get_item.assert_called_once_with(Key={'id': customer_id})
        self.mock_customers_table.update_item.assert_not_called()
    
    def test_update_device_state_device_id_mismatch(self):
        """Test updating a device state when the device ID doesn't match."""
        # Mock data
        customer_id = "test-customer"
        device_id = "test-customer-device-1"
        wrong_device_id = "test-customer-device-2"
        state_updates = {"state": "on"}
        
        # Mock the get_item response
        mock_get_response = {
            'Item': {
                'id': customer_id,
                'name': 'Test Customer',
                'service_level': 'basic',
                'device': {
                    'id': wrong_device_id,
                    'type': 'speaker',
                    'state': 'off',
                    'location': 'living_room'
                }
            }
        }
        self.mock_customers_table.get_item.return_value = mock_get_response
        
        # Call the function
        result = update_device_state(customer_id, device_id, state_updates)
        
        # Assertions
        self.assertFalse(result)
        self.mock_customers_table.get_item.assert_called_once_with(Key={'id': customer_id})
        self.mock_customers_table.update_item.assert_not_called()
    
    def test_update_device_state_multiple_attributes(self):
        """Test updating multiple device attributes at once."""
        # Mock data
        customer_id = "test-customer"
        device_id = "test-customer-device-1"
        state_updates = {
            "state": "on",
            "volume": 75
        }
        
        # Mock the get_item response
        mock_get_response = {
            'Item': {
                'id': customer_id,
                'name': 'Test Customer',
                'service_level': 'basic',
                'device': {
                    'id': device_id,
                    'type': 'speaker',
                    'state': 'off',
                    'volume': 50,
                    'location': 'living_room'
                }
            }
        }
        self.mock_customers_table.get_item.return_value = mock_get_response
        
        # Mock the update_item response
        mock_update_response = {
            'ResponseMetadata': {'HTTPStatusCode': 200},
            'Attributes': {
                'device': {
                    'id': device_id,
                    'type': 'speaker',
                    'state': 'on',
                    'volume': 75,
                    'location': 'living_room'
                }
            }
        }
        self.mock_customers_table.update_item.return_value = mock_update_response
        
        # Call the function
        result = update_device_state(customer_id, device_id, state_updates)
        
        # Assertions
        self.assertTrue(result)
        self.mock_customers_table.get_item.assert_called_once_with(Key={'id': customer_id})
        
        # Verify the update_item call
        self.mock_customers_table.update_item.assert_called_once()
        call_args = self.mock_customers_table.update_item.call_args[1]
        self.assertEqual(call_args['Key'], {'id': customer_id})
        self.assertTrue('device.state = :val_state' in call_args['UpdateExpression'])
        self.assertTrue('device.volume = :val_volume' in call_args['UpdateExpression'])
        self.assertEqual(call_args['ExpressionAttributeValues'][':val_state'], 'on')
        self.assertEqual(call_args['ExpressionAttributeValues'][':val_volume'], 75)

if __name__ == '__main__':
    unittest.main() 