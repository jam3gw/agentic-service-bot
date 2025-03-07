"""
Unit tests for the Anthropic service.

This module contains tests for the Anthropic service functions, focusing on
request analysis and response generation.
"""

import unittest
import sys
import os
import logging
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the module to test
from services.anthropic_service import analyze_request, generate_response, build_system_prompt
from models.customer import Customer

class TestAnthropicService(unittest.TestCase):
    """Tests for the Anthropic service functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Check if ANTHROPIC_API_KEY is set
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            self.skipTest("ANTHROPIC_API_KEY environment variable is not set. Skipping tests that call the Anthropic API.")
    
    def test_analyze_request_device_status(self):
        """Test analyzing a device status request."""
        result = analyze_request("What's the status of my speaker?")
        
        self.assertEqual(result["request_type"], "device_status")
        self.assertIn("device_status", result["required_actions"])
        self.assertFalse(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
    
    def test_analyze_request_device_power(self):
        """Test analyzing a device power request."""
        result = analyze_request("Turn on my speaker")
        
        self.assertEqual(result["request_type"], "device_power")
        self.assertIn("device_power", result["required_actions"])
        self.assertFalse(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
        self.assertEqual(result["context"].get("power_state"), "on")
    
    def test_analyze_request_volume_control(self):
        """Test analyzing a volume control request."""
        result = analyze_request("Turn up the volume")
        
        self.assertEqual(result["request_type"], "volume_control")
        self.assertIn("volume_control", result["required_actions"])
        self.assertFalse(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
        self.assertEqual(result["context"].get("volume_direction"), "up")
    
    def test_analyze_request_song_changes(self):
        """Test analyzing a song changes request."""
        result = analyze_request("Play the next song")
        
        self.assertEqual(result["request_type"], "song_changes")
        self.assertIn("song_changes", result["required_actions"])
        self.assertFalse(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
        self.assertEqual(result["context"].get("song_action"), "next")
    
    def test_analyze_request_multiple_actions(self):
        """Test analyzing a request with multiple actions."""
        result = analyze_request("Turn up the volume and play the next song")
        
        self.assertIn(result["request_type"], ["volume_control", "song_changes"])
        self.assertIn("volume_control", result["required_actions"])
        self.assertIn("song_changes", result["required_actions"])
        self.assertFalse(result["out_of_scope"])
    
    def test_analyze_request_out_of_scope(self):
        """Test analyzing an out-of-scope request."""
        result = analyze_request("What's the weather like today?")
        
        self.assertIsNone(result["request_type"])
        self.assertEqual(len(result["required_actions"]), 0)
        self.assertTrue(result["out_of_scope"])
    
    def test_analyze_request_ambiguous(self):
        """Test analyzing an ambiguous request."""
        result = analyze_request("Change it")
        
        # This should be ambiguous because "change it" could refer to multiple actions
        self.assertTrue(result["ambiguous"])
    
    def test_generate_response_basic_prompt(self):
        """Test generating a response with a basic prompt."""
        response = generate_response("Hello, how are you?")
        
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
    
    def test_generate_response_with_context(self):
        """Test generating a response with context."""
        # Create a context with customer and device information
        device_data = {"id": "device-1", "type": "speaker", "state": "off"}
        context = {
            "customer": Customer(
                customer_id="test-customer",
                name="Test Customer",
                service_level="basic",
                device=device_data
            ),
            "permissions": {
                "allowed_actions": ["device_status", "device_power"],
                "max_devices": 1,
                "support_priority": "standard",
                "upgrade_options": ["premium", "enterprise"]
            },
            "request_type": "device_status",
            "action_allowed": True
        }
        
        response = generate_response("What's the status of my speaker?", context)
        
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
    
    def test_generate_response_disallowed_action(self):
        """Test generating a response for a disallowed action."""
        # Create a context with customer and device information
        device_data = {"id": "device-1", "type": "speaker", "state": "off"}
        context = {
            "customer": Customer(
                customer_id="test-customer",
                name="Test Customer",
                service_level="basic",
                device=device_data
            ),
            "permissions": {
                "allowed_actions": ["device_status", "device_power"],
                "max_devices": 1,
                "support_priority": "standard",
                "upgrade_options": ["premium", "enterprise"]
            },
            "request_type": "volume_control",
            "action_allowed": False
        }
        
        print("\n=== DEBUG: test_generate_response_disallowed_action ===")
        print(f"Context: {context}")
        
        response = generate_response("Turn up the volume", context)
        
        print(f"Response: {response}")
        
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        
        # Use a more flexible assertion that checks for service level restriction messaging
        response_lower = response.lower()
        service_level_phrases = [
            "not available with your basic service",
            "not available with your current basic service",
            "not available with basic service",
            "requires premium",
            "premium tier",
            "upgrade"
        ]
        
        print(f"Checking for phrases: {service_level_phrases}")
        print(f"Found phrases: {[phrase for phrase in service_level_phrases if phrase in response_lower]}")
        
        self.assertTrue(
            any(phrase in response_lower for phrase in service_level_phrases),
            f"Response should indicate service level restriction. Got: {response}"
        )
    
    def test_build_system_prompt_empty_context(self):
        """Test building a system prompt with an empty context."""
        system_prompt = build_system_prompt({})
        
        self.assertIsNotNone(system_prompt)
        self.assertIsInstance(system_prompt, str)
        self.assertGreater(len(system_prompt), 0)
    
    def test_build_system_prompt_with_customer(self):
        """Test building a system prompt with customer information."""
        device_data = {"id": "device-1", "type": "speaker", "state": "off"}
        context = {
            "customer": Customer(
                customer_id="test-customer",
                name="Test Customer",
                service_level="basic",
                device=device_data
            )
        }
        
        system_prompt = build_system_prompt(context)
        
        self.assertIsNotNone(system_prompt)
        self.assertIsInstance(system_prompt, str)
        self.assertGreater(len(system_prompt), 0)
        self.assertIn("Test Customer", system_prompt)
        self.assertIn("Basic", system_prompt)
    
    def test_build_system_prompt_with_permissions(self):
        """Test building a system prompt with permissions."""
        device_data = {"id": "device-1", "type": "speaker", "state": "off"}
        context = {
            "customer": Customer(
                customer_id="test-customer",
                name="Test Customer",
                service_level="basic",
                device=device_data
            ),
            "permissions": {
                "allowed_actions": ["device_status", "device_power"],
                "max_devices": 1,
                "support_priority": "standard",
                "upgrade_options": ["premium", "enterprise"]
            }
        }
        
        system_prompt = build_system_prompt(context)
        
        self.assertIsNotNone(system_prompt)
        self.assertIsInstance(system_prompt, str)
        self.assertGreater(len(system_prompt), 0)
        self.assertIn("ALLOWED ACTIONS", system_prompt)
        
        # Check for user-friendly descriptions instead of action names
        self.assertIn("Check if devices are online/offline", system_prompt)
        self.assertIn("Turn devices on/off", system_prompt)
        self.assertIn("Premium tier adds", system_prompt)
    
    def test_build_system_prompt_with_action_execution(self):
        """Test building a system prompt with action execution information."""
        device_data = {"id": "device-1", "type": "speaker", "state": "off"}
        context = {
            "customer": Customer(
                customer_id="test-customer",
                name="Test Customer",
                service_level="basic",
                device=device_data
            ),
            "permissions": {
                "allowed_actions": ["device_status", "device_power"],
                "max_devices": 1,
                "support_priority": "standard"
            },
            "action_executed": True,
            "device_state": "on",
            "device": {"id": "device-1", "type": "speaker", "location": "living_room"}
        }
        
        system_prompt = build_system_prompt(context)
        
        self.assertIsNotNone(system_prompt)
        self.assertIsInstance(system_prompt, str)
        self.assertGreater(len(system_prompt), 0)
        self.assertIn("ACTION EXECUTION INFORMATION", system_prompt)
        self.assertIn("Changed power state", system_prompt)
        self.assertIn("on", system_prompt)
    
    def test_build_system_prompt_with_error(self):
        """Test building a system prompt with an error."""
        device_data = {"id": "device-1", "type": "speaker", "state": "off"}
        context = {
            "customer": Customer(
                customer_id="test-customer",
                name="Test Customer",
                service_level="basic",
                device=device_data
            ),
            "permissions": {
                "allowed_actions": ["device_status", "device_power"],
                "max_devices": 1,
                "support_priority": "standard",
                "upgrade_options": ["premium", "enterprise"]
            },
            "request_type": "volume_control",
            "error": "This action is not allowed with your current service level"
        }
        
        system_prompt = build_system_prompt(context)
        
        self.assertIsNotNone(system_prompt)
        self.assertIsInstance(system_prompt, str)
        self.assertGreater(len(system_prompt), 0)
        self.assertIn("ACTION EXECUTION ERROR", system_prompt)
        self.assertIn("not allowed with your current service level", system_prompt)

if __name__ == "__main__":
    unittest.main() 