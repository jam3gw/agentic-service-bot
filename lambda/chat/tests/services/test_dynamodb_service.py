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
        # Create a mock table
        self.mock_table = MagicMock()
        
        # Patch the customers_table directly in the module
        self.table_patcher = patch('services.dynamodb_service.customers_table', self.mock_table)
        self.table_patcher.start()
        
    def tearDown(self):
        """Clean up after tests."""
        self.table_patcher.stop()
    
    def test_update_device_state_success(self):
        """Test updating a device state successfully."""
        # Set up mock response
        self.mock_table.get_item.return_value = {
            'Item': {
                'id': 'test-customer',
                'device': {
                    'id': 'test-device',
                    'type': 'speaker',
                    'location': 'living_room'
                }
            }
        }
        self.mock_table.update_item.return_value = {
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }
        
        # Test parameters
        customer_id = 'test-customer'
        device_id = 'test-device'
        state_updates = {"power": "on"}
        
        # Call the function
        result = update_device_state(customer_id, device_id, state_updates)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the get_item call
        self.mock_table.get_item.assert_called_once_with(Key={'id': customer_id})
        
        # Verify the update_item call
        self.mock_table.update_item.assert_called_once()
        call_args = self.mock_table.update_item.call_args[1]
        self.assertEqual(call_args['Key'], {'id': customer_id})
        self.assertIn('device.#attr_power = :val_power', call_args['UpdateExpression'])
    
    def test_update_device_state_customer_not_found(self):
        """Test updating a device state when the customer is not found."""
        # Set up mock response for customer not found
        self.mock_table.get_item.return_value = {}
        
        # Test parameters
        customer_id = 'test-customer'
        device_id = 'test-device'
        state_updates = {"power": "on"}
        
        # Call the function
        result = update_device_state(customer_id, device_id, state_updates)
        
        # Verify the result
        self.assertFalse(result)
        
        # Verify the get_item call
        self.mock_table.get_item.assert_called_once_with(Key={'id': customer_id})
        
        # Verify update_item was not called
        self.mock_table.update_item.assert_not_called()
    
    def test_update_device_state_device_id_mismatch(self):
        """Test updating a device state when the device ID doesn't match."""
        # Set up mock response with different device ID
        self.mock_table.get_item.return_value = {
            'Item': {
                'id': 'test-customer',
                'device': {
                    'id': 'different-device',
                    'type': 'speaker',
                    'location': 'living_room'
                }
            }
        }
        
        # Test parameters
        customer_id = 'test-customer'
        device_id = 'test-device'
        state_updates = {"power": "on"}
        
        # Call the function
        result = update_device_state(customer_id, device_id, state_updates)
        
        # Verify the result
        self.assertFalse(result)
        
        # Verify the get_item call
        self.mock_table.get_item.assert_called_once_with(Key={'id': customer_id})
        
        # Verify update_item was not called
        self.mock_table.update_item.assert_not_called()
    
    def test_update_device_state_multiple_attributes(self):
        """Test updating multiple device attributes."""
        # Set up mock response
        self.mock_table.get_item.return_value = {
            'Item': {
                'id': 'test-customer',
                'device': {
                    'id': 'test-device',
                    'type': 'speaker',
                    'location': 'living_room'
                }
            }
        }
        self.mock_table.update_item.return_value = {
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }
        
        # Test parameters
        customer_id = 'test-customer'
        device_id = 'test-device'
        state_updates = {
            "power": "on",
            "volume": 75
        }
        
        # Call the function
        result = update_device_state(customer_id, device_id, state_updates)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the get_item call
        self.mock_table.get_item.assert_called_once_with(Key={'id': customer_id})
        
        # Verify the update_item call
        self.mock_table.update_item.assert_called_once()
        call_args = self.mock_table.update_item.call_args[1]
        self.assertEqual(call_args['Key'], {'id': customer_id})
        self.assertIn('device.#attr_power = :val_power', call_args['UpdateExpression'])
        self.assertIn('device.#attr_volume = :val_volume', call_args['UpdateExpression'])

if __name__ == '__main__':
    unittest.main() 