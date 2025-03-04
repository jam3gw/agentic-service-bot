import unittest
import sys
import os
import importlib.util
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the lambda module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the lambda module
lambda_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../lambda/chat/index.py'))
spec = importlib.util.spec_from_file_location("lambda_chat", lambda_path)
lambda_chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lambda_chat)

class TestProcessRequest(unittest.TestCase):
    """Integration tests for the process_request function"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock DynamoDB tables
        self.mock_messages_table = MagicMock()
        self.mock_customers_table = MagicMock()
        self.mock_service_levels_table = MagicMock()
        
        # Set up mock customer data
        self.customer_data = {
            'id': 'cust_001',
            'name': 'Jane Smith',
            'service_level': 'basic',
            'devices': [
                {
                    'id': 'dev_001',
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                }
            ]
        }
        
        # Set up mock service level data
        self.service_level_data = {
            'level': 'basic',
            'allowed_actions': [
                'status_check',
                'volume_control',
                'device_info'
            ],
            'max_devices': 1,
            'support_priority': 'standard'
        }
        
        # Configure mock responses
        self.mock_customers_table.get_item.return_value = {'Item': self.customer_data}
        self.mock_service_levels_table.get_item.return_value = {'Item': self.service_level_data}

    @patch('anthropic.Anthropic')
    def test_process_request_allowed_action(self, mock_anthropic):
        """Test processing a request for an allowed action"""
        # Set up mock Anthropic client
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Configure mock response from Anthropic
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Here's the information about your smart speaker.")]
        mock_anthropic_instance.messages.create.return_value = mock_message
        
        # Patch the DynamoDB tables
        with patch.object(lambda_chat, 'messages_table', self.mock_messages_table):
            with patch.object(lambda_chat, 'customers_table', self.mock_customers_table):
                with patch.object(lambda_chat, 'service_levels_table', self.mock_service_levels_table):
                    # Process a request for device info (allowed for basic tier)
                    response = lambda_chat.process_request(
                        'cust_001',
                        'What are the specs of my smart speaker?'
                    )
                    
                    # Verify the response
                    self.assertIn("Here's the information", response)
                    
                    # Verify that the customer data was retrieved
                    self.mock_customers_table.get_item.assert_called_once_with(
                        Key={'id': 'cust_001'}
                    )
                    
                    # Verify that the service level data was retrieved
                    self.mock_service_levels_table.get_item.assert_called_once_with(
                        Key={'level': 'basic'}
                    )
                    
                    # Verify that the messages were stored in DynamoDB
                    self.assertEqual(self.mock_messages_table.put_item.call_count, 2)

    @patch('anthropic.Anthropic')
    def test_process_request_disallowed_action(self, mock_anthropic):
        """Test processing a request for a disallowed action"""
        # Set up mock Anthropic client
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Configure mock response from Anthropic
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="I'm sorry, but your service level doesn't allow device relocation.")]
        mock_anthropic_instance.messages.create.return_value = mock_message
        
        # Patch the DynamoDB tables
        with patch.object(lambda_chat, 'messages_table', self.mock_messages_table):
            with patch.object(lambda_chat, 'customers_table', self.mock_customers_table):
                with patch.object(lambda_chat, 'service_levels_table', self.mock_service_levels_table):
                    # Process a request for device relocation (not allowed for basic tier)
                    response = lambda_chat.process_request(
                        'cust_001',
                        'Move my speaker to the bedroom'
                    )
                    
                    # Verify the response
                    self.assertIn("I'm sorry", response)
                    
                    # Verify that the customer data was retrieved
                    self.mock_customers_table.get_item.assert_called_once_with(
                        Key={'id': 'cust_001'}
                    )
                    
                    # Verify that the service level data was retrieved
                    self.mock_service_levels_table.get_item.assert_called_once_with(
                        Key={'level': 'basic'}
                    )
                    
                    # Verify that the messages were stored in DynamoDB
                    self.assertEqual(self.mock_messages_table.put_item.call_count, 2)

if __name__ == '__main__':
    unittest.main() 