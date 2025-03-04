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

class TestWebSocketHandler(unittest.TestCase):
    """Integration tests for the WebSocket handler functions"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock DynamoDB tables
        self.mock_connections_table = MagicMock()
        self.mock_customers_table = MagicMock()
        self.mock_service_levels_table = MagicMock()
        self.mock_messages_table = MagicMock()
        
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
        self.mock_connections_table.get_item.return_value = {'Item': {'customerId': 'cust_001'}}

    @patch('boto3.client')
    def test_handle_connect(self, mock_boto3_client):
        """Test handling a WebSocket connect event"""
        # Create a mock event
        event = {
            'requestContext': {
                'connectionId': 'connection-123',
                'domainName': 'example.com',
                'stage': 'dev'
            },
            'queryStringParameters': {
                'customerId': 'cust_001'
            }
        }
        
        # Patch the DynamoDB tables
        with patch.object(lambda_chat, 'connections_table', self.mock_connections_table):
            # Call the handler
            response = lambda_chat.handle_connect(event, {})
            
            # Verify the response
            self.assertEqual(response['statusCode'], 200)
            self.assertIn('connected', response['body'])
            
            # Verify that the connection was saved
            self.mock_connections_table.put_item.assert_called_once()
            
            # Verify that the connection ID and customer ID were saved
            call_args = self.mock_connections_table.put_item.call_args[1]['Item']
            self.assertEqual(call_args['connectionId'], 'connection-123')
            self.assertEqual(call_args['customerId'], 'cust_001')

    @patch('anthropic.Anthropic')
    @patch('boto3.client')
    def test_handle_message(self, mock_boto3_client, mock_anthropic):
        """Test handling a WebSocket message event"""
        # Set up mock Anthropic client
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Configure mock response from Anthropic
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Here's the information about your smart speaker.")]
        mock_anthropic_instance.messages.create.return_value = mock_message
        
        # Set up mock API Gateway Management API client
        mock_apigw_client = MagicMock()
        mock_boto3_client.return_value = mock_apigw_client
        
        # Create a mock event
        event = {
            'requestContext': {
                'connectionId': 'connection-123',
                'domainName': 'example.com',
                'stage': 'dev'
            },
            'body': json.dumps({
                'message': 'What are the specs of my smart speaker?',
                'customerId': 'cust_001'
            })
        }
        
        # Patch the DynamoDB tables
        with patch.object(lambda_chat, 'connections_table', self.mock_connections_table):
            with patch.object(lambda_chat, 'customers_table', self.mock_customers_table):
                with patch.object(lambda_chat, 'service_levels_table', self.mock_service_levels_table):
                    with patch.object(lambda_chat, 'messages_table', self.mock_messages_table):
                        # Call the handler
                        response = lambda_chat.handle_message(event, {})
                        
                        # Verify the response
                        self.assertEqual(response['statusCode'], 200)
                        self.assertIn('Message processed', response['body'])
                        
                        # Verify that the connection was checked
                        self.mock_connections_table.get_item.assert_called_once_with(
                            Key={'connectionId': 'connection-123'}
                        )
                        
                        # Verify that messages were sent to the client
                        self.assertEqual(mock_apigw_client.post_to_connection.call_count, 2)

if __name__ == '__main__':
    unittest.main() 