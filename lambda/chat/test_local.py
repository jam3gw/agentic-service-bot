#!/usr/bin/env python3
"""
Local test script for the Agentic Service Bot.

This script tests the local functionality of the bot without requiring
AWS resources or environment variables to be set. It focuses on testing
business-critical functionality rather than implementation details.
"""

import os
import sys
import json
import logging
import unittest
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

class TestLocalFunctionality(unittest.TestCase):
    """Test local functionality with a focus on business value."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set up mock data
        self.mock_customers = {
            'test-customer-123': {
                'id': 'test-customer-123',
                'name': 'Test User',
                'service_level': 'basic',
                'devices': [
                    {
                        'id': 'device-1',
                        'type': 'speaker',
                        'location': 'living_room',
                        'status': 'online'
                    }
                ]
            }
        }
        
        self.mock_service_levels = {
            'basic': {
                'level': 'basic',
                'allowed_actions': ['device_control', 'status_check', 'device_info']
            },
            'premium': {
                'level': 'premium',
                'allowed_actions': ['device_control', 'status_check', 'device_info', 'device_relocation', 'volume_control']
            }
        }
        
        # Set up patches
        self.patches = []
        
        # Patch DynamoDB resource and tables
        self.mock_dynamodb_resource = MagicMock()
        self.mock_customers_table = MagicMock()
        self.mock_service_levels_table = MagicMock()
        self.mock_messages_table = MagicMock()
        
        # Configure mock tables
        self.mock_customers_table.get_item.side_effect = self._mock_get_customer
        self.mock_service_levels_table.get_item.side_effect = self._mock_get_service_level
        self.mock_messages_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # Configure mock resource
        self.mock_dynamodb_resource.Table.side_effect = lambda name: {
            'agentic-service-bot-customers': self.mock_customers_table,
            'agentic-service-bot-service-levels': self.mock_service_levels_table,
            'agentic-service-bot-messages': self.mock_messages_table
        }.get(name, MagicMock())
        
        # Create patches
        boto3_patcher = patch('boto3.resource', return_value=self.mock_dynamodb_resource)
        self.patches.append(boto3_patcher)
        
        # Patch environment variables
        os.environ['CUSTOMERS_TABLE'] = 'agentic-service-bot-customers'
        os.environ['SERVICE_LEVELS_TABLE'] = 'agentic-service-bot-service-levels'
        os.environ['MESSAGES_TABLE'] = 'agentic-service-bot-messages'
        
        # Start all patches
        for patcher in self.patches:
            patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop all patches
        for patcher in self.patches:
            patcher.stop()
    
    def _mock_get_customer(self, **kwargs):
        """Mock get_item for customers table."""
        customer_id = kwargs.get('Key', {}).get('id')
        if customer_id in self.mock_customers:
            return {'Item': self.mock_customers[customer_id]}
        return {}
    
    def _mock_get_service_level(self, **kwargs):
        """Mock get_item for service levels table."""
        level = kwargs.get('Key', {}).get('level')
        if level in self.mock_service_levels:
            return {'Item': self.mock_service_levels[level]}
        return {}
    
    def test_imports(self):
        """Test that all imports work correctly."""
        logger.info("Testing imports...")
        
        try:
            # Test importing handlers
            from handlers.websocket_handler import handle_connect, handle_message
            logger.info("✅ Successfully imported from handlers.websocket_handler")
            
            # Test importing services
            from services.request_processor import process_request
            logger.info("✅ Successfully imported from services.request_processor")
            
            # Test importing models
            from models.customer import Customer
            logger.info("✅ Successfully imported from models.customer")
            
            # Test importing analyzers
            from analyzers.request_analyzer import RequestAnalyzer
            logger.info("✅ Successfully imported from analyzers.request_analyzer")
            
            # Test importing index
            import index
            logger.info("✅ Successfully imported index")
            
            logger.info("All imports successful! The modularization is working correctly.")
            self.assertTrue(True)
        except ImportError as e:
            logger.error(f"Import error: {str(e)}")
            logger.error(f"Module path that failed: {e.__traceback__.tb_frame.f_globals['__name__']}")
            logger.error(f"Line number: {e.__traceback__.tb_lineno}")
            self.fail(f"Import error: {str(e)}")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            self.fail(f"Error: {str(e)}")
    
    @patch('services.anthropic_service.generate_response')
    def test_request_processing_device_control(self, mock_generate_response):
        """
        Test the request processing functionality for device control.
        
        This test verifies that our system correctly identifies device control
        requests and processes them according to the customer's service level.
        """
        logger.info("Testing request processing for device control...")
        
        # Mock the response generation
        mock_generate_response.return_value = "I'll turn on your living room light."
        
        # Import the necessary modules
        from services.request_processor import process_request
        from analyzers.request_analyzer import RequestAnalyzer
        
        # Test request analyzer for device control requests
        test_requests = [
            "Can you turn off my living room light?",
            "I want to turn on the kitchen lights",
            "Please switch off the bedroom lamp",
            "I would like to turn off one of my lights"
        ]
        
        for request in test_requests:
            request_type = RequestAnalyzer.identify_request_type(request)
            self.assertEqual(request_type, "device_control", 
                            f"Failed to identify device control request: '{request}', got: {request_type}")
        
        # Process a device control request
        customer_id = "test-customer-123"
        user_input = "Can you turn on my living room speaker?"
        
        response = process_request(customer_id, user_input)
        
        # Verify the response
        self.assertIsNotNone(response)
        self.assertEqual(response, "I'll turn on your living room light.")
        
        # Verify that generate_response was called with the right context
        args, kwargs = mock_generate_response.call_args
        self.assertIn('context', kwargs)
        context = kwargs['context']
        
        # Verify the context contains the expected data
        self.assertEqual(context['customer'].id, customer_id)
        self.assertEqual(context['request_type'], 'device_control')
        self.assertTrue(context['action_allowed'])
        
        logger.info("✅ Device control request processing test completed")
    
    @patch('services.anthropic_service.generate_response')
    def test_request_processing_device_relocation(self, mock_generate_response):
        """
        Test the request processing functionality for device relocation.
        
        This test verifies that our system correctly identifies device relocation
        requests and processes them according to the customer's service level.
        """
        logger.info("Testing request processing for device relocation...")
        
        # Mock the response generation
        mock_generate_response.return_value = "I'm sorry, device relocation is not available with your basic service level. Would you like to upgrade to premium?"
        
        # Import the necessary modules
        from services.request_processor import process_request
        from analyzers.request_analyzer import RequestAnalyzer
        
        # Test request analyzer for device relocation requests
        test_requests = [
            "Can you move my speaker to the kitchen?",
            "I want to relocate my display to the bedroom",
            "Please move the living room speaker to the office",
            "I would like to put my hub in the dining room"
        ]
        
        for request in test_requests:
            request_type = RequestAnalyzer.identify_request_type(request)
            self.assertEqual(request_type, "device_relocation", 
                            f"Failed to identify device relocation request: '{request}', got: {request_type}")
        
        # Process a device relocation request for a basic customer
        customer_id = "test-customer-123"
        user_input = "Can you move my speaker to the kitchen?"
        
        response = process_request(customer_id, user_input)
        
        # Verify the response
        self.assertIsNotNone(response)
        self.assertEqual(response, "I'm sorry, device relocation is not available with your basic service level. Would you like to upgrade to premium?")
        
        # Verify that generate_response was called with the right context
        args, kwargs = mock_generate_response.call_args
        self.assertIn('context', kwargs)
        context = kwargs['context']
        
        # Verify the context contains the expected data
        self.assertEqual(context['customer'].id, customer_id)
        self.assertEqual(context['request_type'], 'device_relocation')
        self.assertFalse(context['action_allowed'])
        
        logger.info("✅ Device relocation request processing test completed")
    
    def test_service_level_permissions(self):
        """
        Test service level permissions.
        
        This test verifies that our permission system correctly enforces
        service level restrictions, which is critical for our tiered pricing model.
        """
        logger.info("Testing service level permissions...")
        
        # Import the necessary modules
        from services.request_processor import is_action_allowed
        from models.customer import Customer
        
        # Create test customers
        basic_customer = Customer(
            'basic-customer',
            'Basic User',
            'basic',
            [{'id': 'device-1', 'type': 'speaker', 'location': 'living_room'}]
        )
        
        premium_customer = Customer(
            'premium-customer',
            'Premium User',
            'premium',
            [{'id': 'device-2', 'type': 'speaker', 'location': 'living_room'}]
        )
        
        # Test basic customer permissions
        self.assertTrue(is_action_allowed(basic_customer, 'device_control'))
        self.assertTrue(is_action_allowed(basic_customer, 'status_check'))
        self.assertTrue(is_action_allowed(basic_customer, 'device_info'))
        self.assertFalse(is_action_allowed(basic_customer, 'device_relocation'))
        self.assertFalse(is_action_allowed(basic_customer, 'volume_control'))
        
        # Test premium customer permissions
        self.assertTrue(is_action_allowed(premium_customer, 'device_control'))
        self.assertTrue(is_action_allowed(premium_customer, 'status_check'))
        self.assertTrue(is_action_allowed(premium_customer, 'device_info'))
        self.assertTrue(is_action_allowed(premium_customer, 'device_relocation'))
        self.assertTrue(is_action_allowed(premium_customer, 'volume_control'))
        
        logger.info("✅ Service level permissions test completed")

def main():
    """Run all tests."""
    logger.info("Starting local tests...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    logger.info("Local tests completed.")

if __name__ == "__main__":
    main() 