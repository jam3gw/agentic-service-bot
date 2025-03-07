"""
Unit tests for the request processor.

This module contains tests for the request processor functions, focusing on
service level permissions and action checking.
"""

import unittest
import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the module to test
from services.request_processor import is_action_allowed, process_request
from models.customer import Customer

class TestRequestProcessor(unittest.TestCase):
    """Tests for the request processor functions."""
    
    @patch('services.request_processor.get_service_level_permissions')
    def test_is_action_allowed_basic_actions(self, mock_get_permissions):
        """Test that basic actions are allowed for all service levels."""
        # Setup mock
        mock_get_permissions.return_value = {
            "allowed_actions": ["device_status", "device_power"],
            "max_devices": 1,
            "support_priority": "standard"
        }
        
        # Test basic actions for different service levels
        basic_actions = ["device_status", "device_power"]
        service_levels = ["basic", "premium", "enterprise"]
        
        for service_level in service_levels:
            for action in basic_actions:
                with self.subTest(service_level=service_level, action=action):
                    result = is_action_allowed(service_level, action)
                    self.assertTrue(result, f"Action {action} should be allowed for {service_level}")
    
    @patch('services.request_processor.get_service_level_permissions')
    def test_is_action_allowed_premium_actions(self, mock_get_permissions):
        """Test that premium actions are allowed only for premium and enterprise service levels."""
        # Setup mocks for different service levels
        def mock_get_permissions_side_effect(service_level):
            if service_level == "basic":
                return {
                    "allowed_actions": ["device_status", "device_power"],
                    "max_devices": 1,
                    "support_priority": "standard"
                }
            elif service_level == "premium":
                return {
                    "allowed_actions": ["device_status", "device_power", "volume_control"],
                    "max_devices": 1,
                    "support_priority": "priority"
                }
            elif service_level == "enterprise":
                return {
                    "allowed_actions": ["device_status", "device_power", "volume_control", "song_changes"],
                    "max_devices": 1,
                    "support_priority": "vip"
                }
            return {}
        
        mock_get_permissions.side_effect = mock_get_permissions_side_effect
        
        # Test volume_control action
        # Should be denied for basic
        self.assertFalse(is_action_allowed("basic", "volume_control"), 
                        "volume_control should not be allowed for basic")
        
        # Should be allowed for premium and enterprise
        self.assertTrue(is_action_allowed("premium", "volume_control"), 
                       "volume_control should be allowed for premium")
        self.assertTrue(is_action_allowed("enterprise", "volume_control"), 
                       "volume_control should be allowed for enterprise")
    
    @patch('services.request_processor.get_service_level_permissions')
    def test_is_action_allowed_enterprise_actions(self, mock_get_permissions):
        """Test that enterprise actions are allowed only for enterprise service level."""
        # Setup mocks for different service levels
        def mock_get_permissions_side_effect(service_level):
            if service_level == "basic":
                return {
                    "allowed_actions": ["device_status", "device_power"],
                    "max_devices": 1,
                    "support_priority": "standard"
                }
            elif service_level == "premium":
                return {
                    "allowed_actions": ["device_status", "device_power", "volume_control"],
                    "max_devices": 1,
                    "support_priority": "priority"
                }
            elif service_level == "enterprise":
                return {
                    "allowed_actions": ["device_status", "device_power", "volume_control", "song_changes"],
                    "max_devices": 1,
                    "support_priority": "vip"
                }
            return {}
        
        mock_get_permissions.side_effect = mock_get_permissions_side_effect
        
        # Test song_changes action
        # Should be denied for basic and premium
        self.assertFalse(is_action_allowed("basic", "song_changes"), 
                        "song_changes should not be allowed for basic")
        self.assertFalse(is_action_allowed("premium", "song_changes"), 
                        "song_changes should not be allowed for premium")
        
        # Should be allowed for enterprise
        self.assertTrue(is_action_allowed("enterprise", "song_changes"), 
                       "song_changes should be allowed for enterprise")
    
    @patch('services.request_processor.get_service_level_permissions')
    def test_is_action_allowed_with_customer_object(self, mock_get_permissions):
        """Test that is_action_allowed works with a Customer object."""
        # Setup mock
        mock_get_permissions.return_value = {
            "allowed_actions": ["device_status", "device_power", "volume_control"],
            "max_devices": 1,
            "support_priority": "priority"
        }
        
        # Create a customer object with correct parameters
        customer = Customer(
            customer_id="test-customer",
            name="Test Customer",
            service_level="premium",
            device={"id": "device-1", "type": "speaker", "state": "off"}
        )
        
        # Test with customer object
        self.assertTrue(is_action_allowed(customer, "device_status"), 
                       "device_status should be allowed for premium customer")
        self.assertTrue(is_action_allowed(customer, "device_power"), 
                       "device_power should be allowed for premium customer")
        self.assertTrue(is_action_allowed(customer, "volume_control"), 
                       "volume_control should be allowed for premium customer")
        self.assertFalse(is_action_allowed(customer, "song_changes"), 
                        "song_changes should not be allowed for premium customer")
    
    @patch('services.request_processor.get_customer')
    @patch('services.request_processor.get_service_level_permissions')
    @patch('services.request_processor.analyze_request')
    @patch('services.request_processor.store_message')
    def test_process_request_basic_service_level(self, mock_store_message, 
                                               mock_analyze, mock_get_permissions, mock_get_customer):
        """Test processing a request for a basic service level customer."""
        # Setup mocks
        mock_customer = MagicMock()
        mock_customer.id = "test-customer"
        mock_customer.service_level = "basic"
        mock_customer.get_device.return_value = {"id": "device-1", "type": "speaker", "state": "off"}
        mock_get_customer.return_value = mock_customer
        
        mock_get_permissions.return_value = {
            "allowed_actions": ["device_status", "device_power"],
            "max_devices": 1,
            "support_priority": "standard"
        }
        
        # Test volume control request (should be denied)
        mock_analyze.return_value = {
            "request_type": "volume_control",
            "required_actions": ["volume_control"],
            "context": {"volume_direction": "up"}
        }
        
        mock_store_message.return_value = {"id": "msg-123"}
        
        # Note: We're not mocking generate_response to test actual prompt analysis
        result = process_request("test-customer", {"message": "Turn up the volume"})
        
        # Verify the response indicates the action is not allowed
        self.assertIn("not available with your basic service level", result.get("message", "").lower())
        
        # Test device status request (should be allowed)
        mock_analyze.return_value = {
            "request_type": "device_status",
            "required_actions": ["device_status"],
            "context": {}
        }
        
        result = process_request("test-customer", {"message": "What's the status of my speaker?"})
        
        # Verify the response indicates the action is allowed
        self.assertNotIn("not available with your basic service level", result.get("message", "").lower())
    
    @patch('services.request_processor.get_customer')
    @patch('services.request_processor.get_service_level_permissions')
    @patch('services.request_processor.analyze_request')
    @patch('services.request_processor.store_message')
    def test_process_request_premium_service_level(self, mock_store_message, 
                                                mock_analyze, mock_get_permissions, mock_get_customer):
        """Test processing a request for a premium service level customer."""
        # Setup mocks
        mock_customer = MagicMock()
        mock_customer.id = "test-customer"
        mock_customer.service_level = "premium"
        mock_customer.get_device.return_value = {"id": "device-1", "type": "speaker", "state": "on"}
        mock_get_customer.return_value = mock_customer
        
        mock_get_permissions.return_value = {
            "allowed_actions": ["device_status", "device_power", "volume_control"],
            "max_devices": 1,
            "support_priority": "priority"
        }
        
        # Test volume control request (should be allowed)
        mock_analyze.return_value = {
            "request_type": "volume_control",
            "required_actions": ["volume_control"],
            "context": {"volume_direction": "up"}
        }
        
        mock_store_message.return_value = {"id": "msg-123"}
        
        # Note: We're not mocking generate_response to test actual prompt analysis
        result = process_request("test-customer", {"message": "Turn up the volume"})
        
        # Verify the response doesn't indicate the action is not allowed
        self.assertNotIn("not available with your premium service level", result.get("message", "").lower())
        
        # Test song changes request (should be denied)
        mock_analyze.return_value = {
            "request_type": "song_changes",
            "required_actions": ["song_changes"],
            "context": {"song_action": "next"}
        }
        
        result = process_request("test-customer", {"message": "Play the next song"})
        
        # Verify the response indicates the action is not allowed
        self.assertIn("not available with your premium service level", result.get("message", "").lower())

if __name__ == "__main__":
    unittest.main() 