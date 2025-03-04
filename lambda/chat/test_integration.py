#!/usr/bin/env python3
"""
Integration test script for the Agentic Service Bot.

This script tests the actual business functionality of the bot by hitting real APIs
and verifying end-to-end flows that deliver value to users. These tests focus on
business-critical paths rather than implementation details.
"""

import os
import sys
import json
import logging
import requests
import unittest
import boto3
import websocket
import time
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import local modules
from models.customer import Customer

class IntegrationTest(unittest.TestCase):
    """
    Integration tests for the Agentic Service Bot.
    
    These tests verify actual business functionality by testing real APIs
    and end-to-end flows that deliver value to users.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used for all tests."""
        # Load configuration
        cls.config = cls._load_config()
        
        # Set up DynamoDB client for verification
        cls.dynamodb = boto3.resource('dynamodb')
        cls.customers_table = cls.dynamodb.Table(cls.config.get('CUSTOMERS_TABLE', 'agentic-service-bot-customers'))
        cls.service_levels_table = cls.dynamodb.Table(cls.config.get('SERVICE_LEVELS_TABLE', 'agentic-service-bot-service-levels'))
        cls.messages_table = cls.dynamodb.Table(cls.config.get('MESSAGES_TABLE', 'agentic-service-bot-messages'))
        
        # Set up API endpoints
        cls.api_base_url = cls.config.get('API_BASE_URL')
        cls.websocket_url = cls.config.get('WEBSOCKET_URL')
        
        # Ensure we have test customers in the database
        cls._ensure_test_customers()
        cls._ensure_service_levels()
    
    @classmethod
    def _load_config(cls) -> Dict[str, str]:
        """
        Load configuration from environment or config file.
        
        Returns:
            Dictionary with configuration values
        """
        config = {
            'API_BASE_URL': os.environ.get('API_BASE_URL', 'http://localhost:3000/api'),
            'WEBSOCKET_URL': os.environ.get('WEBSOCKET_URL', 'ws://localhost:3001'),
            'CUSTOMERS_TABLE': os.environ.get('CUSTOMERS_TABLE', 'agentic-service-bot-customers'),
            'SERVICE_LEVELS_TABLE': os.environ.get('SERVICE_LEVELS_TABLE', 'agentic-service-bot-service-levels'),
            'MESSAGES_TABLE': os.environ.get('MESSAGES_TABLE', 'agentic-service-bot-messages'),
        }
        
        # Try to load from config file if it exists
        config_file = os.path.join(current_dir, 'test_config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        return config
    
    @classmethod
    def _ensure_test_customers(cls):
        """Ensure test customers exist in the database."""
        # Basic customer
        basic_customer = {
            'id': 'test-basic-customer',
            'name': 'Test Basic User',
            'service_level': 'basic',
            'devices': [
                {
                    'id': 'device-basic-1',
                    'type': 'speaker',
                    'location': 'living_room',
                    'status': 'online'
                }
            ]
        }
        
        # Premium customer
        premium_customer = {
            'id': 'test-premium-customer',
            'name': 'Test Premium User',
            'service_level': 'premium',
            'devices': [
                {
                    'id': 'device-premium-1',
                    'type': 'speaker',
                    'location': 'living_room',
                    'status': 'online'
                },
                {
                    'id': 'device-premium-2',
                    'type': 'display',
                    'location': 'kitchen',
                    'status': 'online'
                }
            ]
        }
        
        # Enterprise customer
        enterprise_customer = {
            'id': 'test-enterprise-customer',
            'name': 'Test Enterprise User',
            'service_level': 'enterprise',
            'devices': [
                {
                    'id': 'device-enterprise-1',
                    'type': 'speaker',
                    'location': 'living_room',
                    'status': 'online'
                },
                {
                    'id': 'device-enterprise-2',
                    'type': 'display',
                    'location': 'kitchen',
                    'status': 'online'
                },
                {
                    'id': 'device-enterprise-3',
                    'type': 'hub',
                    'location': 'office',
                    'status': 'online'
                }
            ]
        }
        
        # Add customers to the database
        try:
            cls.customers_table.put_item(Item=basic_customer)
            cls.customers_table.put_item(Item=premium_customer)
            cls.customers_table.put_item(Item=enterprise_customer)
            logger.info("Test customers added to the database")
        except Exception as e:
            logger.error(f"Failed to add test customers: {e}")
    
    @classmethod
    def _ensure_service_levels(cls):
        """Ensure service levels exist in the database."""
        # Basic service level
        basic_level = {
            'level': 'basic',
            'allowed_actions': ['device_control', 'status_check', 'device_info']
        }
        
        # Premium service level
        premium_level = {
            'level': 'premium',
            'allowed_actions': ['device_control', 'status_check', 'device_info', 'device_relocation', 'volume_control']
        }
        
        # Enterprise service level
        enterprise_level = {
            'level': 'enterprise',
            'allowed_actions': ['device_control', 'status_check', 'device_info', 'device_relocation', 'volume_control', 'multi_room_audio', 'custom_actions']
        }
        
        # Add service levels to the database
        try:
            cls.service_levels_table.put_item(Item=basic_level)
            cls.service_levels_table.put_item(Item=premium_level)
            cls.service_levels_table.put_item(Item=enterprise_level)
            logger.info("Service levels added to the database")
        except Exception as e:
            logger.error(f"Failed to add service levels: {e}")
    
    def test_device_control_basic_customer(self):
        """
        Test device control for a basic customer.
        
        This test verifies that a basic customer can control their devices,
        which is a core business functionality that delivers immediate value.
        """
        # Send a request to control a device
        response = self._send_api_request(
            'test-basic-customer',
            'Turn on my living room speaker'
        )
        
        # Verify the response
        self.assertIsNotNone(response)
        self.assertIn('message', response)
        
        # The response should indicate success for this allowed action
        self.assertNotIn("not allowed with basic service level", response['message'].lower())
        self.assertNotIn("upgrade", response['message'].lower())
        
        # Verify that the interaction was logged in the messages table
        self._verify_message_logged('test-basic-customer', 'Turn on my living room speaker')
    
    def test_device_relocation_basic_customer(self):
        """
        Test device relocation for a basic customer.
        
        This test verifies that a basic customer cannot relocate devices,
        which is a premium feature. This tests our service tier boundaries,
        which are critical for our business model.
        """
        # Send a request to relocate a device
        response = self._send_api_request(
            'test-basic-customer',
            'Move my speaker to the kitchen'
        )
        
        # Verify the response
        self.assertIsNotNone(response)
        self.assertIn('message', response)
        
        # The response should indicate this action is not allowed and suggest an upgrade
        self.assertIn("not allowed with basic service level", response['message'].lower())
        self.assertIn("upgrade", response['message'].lower())
        
        # Verify that the interaction was logged in the messages table
        self._verify_message_logged('test-basic-customer', 'Move my speaker to the kitchen')
    
    def test_device_relocation_premium_customer(self):
        """
        Test device relocation for a premium customer.
        
        This test verifies that a premium customer can relocate devices,
        which is a key differentiator for the premium tier and delivers
        significant value to these customers.
        """
        # Send a request to relocate a device
        response = self._send_api_request(
            'test-premium-customer',
            'Move my speaker to the kitchen'
        )
        
        # Verify the response
        self.assertIsNotNone(response)
        self.assertIn('message', response)
        
        # The response should indicate success for this allowed action
        self.assertNotIn("not allowed with premium service level", response['message'].lower())
        self.assertNotIn("upgrade", response['message'].lower())
        
        # Verify that the interaction was logged in the messages table
        self._verify_message_logged('test-premium-customer', 'Move my speaker to the kitchen')
    
    def test_multi_room_setup_enterprise_customer(self):
        """
        Test multi-room audio setup for an enterprise customer.
        
        This test verifies that an enterprise customer can set up multi-room audio,
        which is a high-value enterprise feature that justifies the higher tier.
        """
        # Send a request to set up multi-room audio
        response = self._send_api_request(
            'test-enterprise-customer',
            'Set up multi-room audio in the living room and kitchen'
        )
        
        # Verify the response
        self.assertIsNotNone(response)
        self.assertIn('message', response)
        
        # The response should indicate success for this allowed action
        self.assertNotIn("not allowed with enterprise service level", response['message'].lower())
        self.assertNotIn("upgrade", response['message'].lower())
        
        # Verify that the interaction was logged in the messages table
        self._verify_message_logged(
            'test-enterprise-customer',
            'Set up multi-room audio in the living room and kitchen'
        )
    
    def test_websocket_connection_and_messaging(self):
        """
        Test WebSocket connection and messaging.
        
        This test verifies the real-time communication capability,
        which is critical for providing responsive customer service.
        """
        # Connect to the WebSocket
        ws = self._connect_websocket('test-premium-customer')
        self.assertIsNotNone(ws)
        
        try:
            # Send a message
            message = {
                'message': 'What devices do I have?',
                'customerId': 'test-premium-customer'
            }
            ws.send(json.dumps(message))
            
            # Wait for and verify the response
            response = self._receive_websocket_message(ws)
            self.assertIsNotNone(response)
            self.assertIn('message', response)
            
            # The response should mention the customer's devices
            self.assertIn("speaker", response['message'].lower())
            self.assertIn("display", response['message'].lower())
            
            # Verify that the interaction was logged in the messages table
            self._verify_message_logged('test-premium-customer', 'What devices do I have?')
        finally:
            # Close the connection
            ws.close()
    
    def _send_api_request(self, customer_id: str, message: str) -> Dict[str, Any]:
        """
        Send a request to the API.
        
        Args:
            customer_id: The customer ID
            message: The message to send
            
        Returns:
            The API response as a dictionary
        """
        url = f"{self.api_base_url}/chat"
        payload = {
            'customerId': customer_id,
            'message': message
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def _connect_websocket(self, customer_id: str) -> Optional[websocket.WebSocket]:
        """
        Connect to the WebSocket.
        
        Args:
            customer_id: The customer ID
            
        Returns:
            The WebSocket connection or None if connection failed
        """
        ws_url = f"{self.websocket_url}?customerId={customer_id}"
        
        try:
            ws = websocket.create_connection(ws_url)
            
            # Wait for welcome message
            welcome = json.loads(ws.recv())
            logger.info(f"Received welcome message: {welcome}")
            
            return ws
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return None
    
    def _receive_websocket_message(self, ws: websocket.WebSocket, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """
        Receive a message from the WebSocket.
        
        Args:
            ws: The WebSocket connection
            timeout: The timeout in seconds
            
        Returns:
            The received message as a dictionary or None if no message received
        """
        ws.settimeout(timeout)
        
        try:
            message = ws.recv()
            return json.loads(message)
        except Exception as e:
            logger.error(f"Failed to receive WebSocket message: {e}")
            return None
    
    def _verify_message_logged(self, customer_id: str, message_text: str) -> bool:
        """
        Verify that a message was logged in the messages table.
        
        Args:
            customer_id: The customer ID
            message_text: The message text
            
        Returns:
            True if the message was found, False otherwise
        """
        # Wait a moment for the message to be logged
        time.sleep(1)
        
        try:
            # Scan the messages table for the customer's messages
            response = self.messages_table.scan(
                FilterExpression='userId = :userId',
                ExpressionAttributeValues={':userId': customer_id}
            )
            
            # Check if the message is in the results
            for item in response.get('Items', []):
                if item.get('message') == message_text:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to verify message logging: {e}")
            return False

def main():
    """Run the integration tests."""
    logger.info("Starting integration tests...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    logger.info("Integration tests completed.")

if __name__ == "__main__":
    main() 