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

class TestWebSocketConnections(unittest.TestCase):
    """Integration tests for WebSocket connection handling"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock DynamoDB tables
        self.mock_connections_table = MagicMock()
        
        # Set up mock connection data
        self.connection_data = {
            'connectionId': 'ABC123',
            'customerId': 'cust_001',
            'ttl': 1677765000,
            'timestamp': 1677678600
        }
        
        # Configure mock responses
        self.mock_connections_table.get_item.return_value = {'Item': self.connection_data}

    def test_save_connection(self):
        """Test saving a WebSocket connection"""
        # Patch the connections table
        with patch.object(lambda_chat, 'connections_table', self.mock_connections_table):
            # Save a connection
            lambda_chat.save_connection('ABC123', 'cust_001')
            
            # Verify that the connection was saved
            self.mock_connections_table.put_item.assert_called_once()
            
            # Verify that the connection was retrieved for verification
            self.mock_connections_table.get_item.assert_called_once_with(
                Key={'connectionId': 'ABC123'}
            )

    def test_get_customer_id_for_connection(self):
        """Test retrieving a customer ID for a connection"""
        # Patch the connections table
        with patch.object(lambda_chat, 'connections_table', self.mock_connections_table):
            # Get customer ID for a connection
            customer_id = lambda_chat.get_customer_id_for_connection('ABC123')
            
            # Verify the customer ID
            self.assertEqual(customer_id, 'cust_001')
            
            # Verify that the connection was retrieved
            self.mock_connections_table.get_item.assert_called_once_with(
                Key={'connectionId': 'ABC123'}
            )

    def test_get_customer_id_for_nonexistent_connection(self):
        """Test retrieving a customer ID for a nonexistent connection"""
        # Configure mock response for nonexistent connection
        self.mock_connections_table.get_item.return_value = {}
        
        # Patch the connections table
        with patch.object(lambda_chat, 'connections_table', self.mock_connections_table):
            # Get customer ID for a nonexistent connection
            customer_id = lambda_chat.get_customer_id_for_connection('XYZ789')
            
            # Verify that None was returned
            self.assertIsNone(customer_id)
            
            # Verify that the connection was retrieved
            self.mock_connections_table.get_item.assert_called_once_with(
                Key={'connectionId': 'XYZ789'}
            )

    @patch('boto3.client')
    def test_send_message(self, mock_boto3_client):
        """Test sending a message to a WebSocket client"""
        # Set up mock API Gateway Management API client
        mock_apigw_client = MagicMock()
        mock_boto3_client.return_value = mock_apigw_client
        
        # Patch the connections table
        with patch.object(lambda_chat, 'connections_table', self.mock_connections_table):
            # Send a message
            result = lambda_chat.send_message(
                'ABC123',
                'Hello, world!',
                'https://example.execute-api.us-east-1.amazonaws.com/dev'
            )
            
            # Verify the result
            self.assertTrue(result)
            
            # Verify that the API Gateway client was created
            mock_boto3_client.assert_called_once_with(
                'apigatewaymanagementapi',
                endpoint_url='https://example.execute-api.us-east-1.amazonaws.com/dev'
            )
            
            # Verify that the message was sent
            mock_apigw_client.post_to_connection.assert_called_once_with(
                ConnectionId='ABC123',
                Data=json.dumps({'message': 'Hello, world!'}).encode('utf-8')
            )

    @patch('boto3.client')
    def test_send_message_gone_exception(self, mock_boto3_client):
        """Test sending a message to a gone connection"""
        # Set up mock API Gateway Management API client
        mock_apigw_client = MagicMock()
        mock_boto3_client.return_value = mock_apigw_client
        
        # Configure mock to raise GoneException
        mock_apigw_client.post_to_connection.side_effect = Exception("GoneException")
        
        # Patch the connections table
        with patch.object(lambda_chat, 'connections_table', self.mock_connections_table):
            # Send a message to a gone connection
            result = lambda_chat.send_message(
                'ABC123',
                'Hello, world!',
                'https://example.execute-api.us-east-1.amazonaws.com/dev'
            )
            
            # Verify the result
            self.assertFalse(result)
            
            # Verify that the connection was deleted
            self.mock_connections_table.delete_item.assert_called_once_with(
                Key={'connectionId': 'ABC123'}
            )

if __name__ == '__main__':
    unittest.main() 