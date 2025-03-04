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

class TestWebSocketHandlers(unittest.TestCase):
    """Integration tests for WebSocket handler functions"""

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

    @patch('lambda_chat.save_connection')
    def test_handle_connect(self, mock_save_connection):
        """Test handling a WebSocket connect event"""
        # Create a mock connect event
        connect_event = {
            'requestContext': {
                'connectionId': 'ABC123',
                'domainName': 'example.execute-api.us-east-1.amazonaws.com',
                'stage': 'dev'
            },
            'queryStringParameters': {
                'customerId': 'cust_001'
            }
        }
        
        # Patch the send_message function
        with patch.object(lambda_chat, 'send_message', return_value=True):
            # Handle the connect event
            response = lambda_chat.handle_connect(connect_event, None)
            
            # Verify the response
            self.assertEqual(response['statusCode'], 200)
            self.assertIn('connected', json.loads(response['body'])['status'])
            
            # Verify that the connection was saved
            mock_save_connection.assert_called_once_with('ABC123', 'cust_001')

    @patch('lambda_chat.get_customer_id_for_connection')
    @patch('lambda_chat.process_request')
    def test_handle_message(self, mock_process_request, mock_get_customer_id):
        """Test handling a WebSocket message event"""
        # Configure mocks
        mock_get_customer_id.return_value = 'cust_001'
        mock_process_request.return_value = "Here's the information about your smart speaker."
        
        # Create a mock message event
        message_event = {
            'requestContext': {
                'connectionId': 'ABC123',
                'domainName': 'example.execute-api.us-east-1.amazonaws.com',
                'stage': 'dev'
            },
            'body': json.dumps({
                'message': 'What are the specs of my smart speaker?',
                'customerId': 'cust_001'
            })
        }
        
        # Patch the send_message function
        with patch.object(lambda_chat, 'send_message', return_value=True):
            # Handle the message event
            response = lambda_chat.handle_message(message_event, None)
            
            # Verify the response
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body'])['status'], 'Message processed')
            
            # Verify that the customer ID was retrieved
            mock_get_customer_id.assert_called_once_with('ABC123')
            
            # Verify that the request was processed
            mock_process_request.assert_called_once_with(
                'cust_001',
                'What are the specs of my smart speaker?'
            )

    def test_handler_connect(self):
        """Test the main handler function with a connect event"""
        # Create a mock connect event
        connect_event = {
            'requestContext': {
                'connectionId': 'ABC123',
                'routeKey': '$connect',
                'domainName': 'example.execute-api.us-east-1.amazonaws.com',
                'stage': 'dev'
            },
            'queryStringParameters': {
                'customerId': 'cust_001'
            }
        }
        
        # Patch the handle_connect function
        with patch.object(lambda_chat, 'handle_connect', return_value={'statusCode': 200, 'body': 'Connected'}):
            # Handle the event
            response = lambda_chat.handler(connect_event, None)
            
            # Verify the response
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(response['body'], 'Connected')

    def test_handler_disconnect(self):
        """Test the main handler function with a disconnect event"""
        # Create a mock disconnect event
        disconnect_event = {
            'requestContext': {
                'connectionId': 'ABC123',
                'routeKey': '$disconnect',
                'domainName': 'example.execute-api.us-east-1.amazonaws.com',
                'stage': 'dev'
            }
        }
        
        # Handle the event
        response = lambda_chat.handler(disconnect_event, None)
        
        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], 'Disconnected')

    def test_handler_message(self):
        """Test the main handler function with a message event"""
        # Create a mock message event
        message_event = {
            'requestContext': {
                'connectionId': 'ABC123',
                'routeKey': 'message',
                'domainName': 'example.execute-api.us-east-1.amazonaws.com',
                'stage': 'dev'
            },
            'body': json.dumps({
                'message': 'What are the specs of my smart speaker?',
                'customerId': 'cust_001'
            })
        }
        
        # Patch the handle_message function
        with patch.object(lambda_chat, 'handle_message', return_value={'statusCode': 200, 'body': 'Message processed'}):
            # Handle the event
            response = lambda_chat.handler(message_event, None)
            
            # Verify the response
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(response['body'], 'Message processed')

if __name__ == '__main__':
    unittest.main() 