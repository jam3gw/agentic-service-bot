"""
Unit tests for the Anthropic service.

This module contains tests for the Anthropic service's ability to analyze user requests
and generate appropriate responses based on customer service levels and permissions.
"""

import unittest
import json
import os
from typing import Dict, Any

# Add the parent directory to sys.path to enable absolute imports
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from services.anthropic_service import analyze_request, generate_response
from models.customer import Customer

class TestAnthropicService(unittest.TestCase):
    """Test cases for the Anthropic service."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        # Check if ANTHROPIC_API_KEY is set
        if not os.environ.get('ANTHROPIC_API_KEY'):
            raise unittest.SkipTest("ANTHROPIC_API_KEY not set. Skipping real API tests.")
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a basic test customer
        self.basic_customer = Customer(
            customer_id="test-basic",
            name="Basic User",
            service_level="basic",
            device={"id": "device-1", "type": "speaker", "power": "on"}
        )
        
        # Create a premium test customer
        self.premium_customer = Customer(
            customer_id="test-premium",
            name="Premium User",
            service_level="premium",
            device={"id": "device-1", "type": "speaker", "power": "on"}
        )
        
        # Create an enterprise test customer
        self.enterprise_customer = Customer(
            customer_id="test-enterprise",
            name="Enterprise User",
            service_level="enterprise",
            device={"id": "device-1", "type": "speaker", "power": "on"}
        )
    
    def _prepare_context(self, result: Dict[str, Any], customer: Customer) -> Dict[str, Any]:
        """Helper method to prepare context for generate_response."""
        return {
            "request": result,
            "customer": customer.to_dict() if hasattr(customer, "to_dict") else customer.__dict__
        }
    
    def test_basic_customer_can_check_device_status(self):
        """Verify that basic tier customers can check their device status."""
        # Test the request analysis with real API call
        result = analyze_request("Check my speaker")
        
        # Verify the response
        self.assertEqual(result["primary_action"], "device_status")
        self.assertIn("device_status", result["all_actions"])
        self.assertFalse(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
    
    def test_basic_customer_cannot_control_volume(self):
        """Verify that basic tier customers cannot control volume."""
        # Test the request analysis with real API call
        result = analyze_request("Turn up the volume")
        
        # Verify the response
        self.assertEqual(result["primary_action"], "volume_control")
        self.assertIn("volume_control", result["all_actions"])
        self.assertFalse(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
        
        # Test response generation for basic customer
        context = self._prepare_context(result, self.basic_customer)
        response = generate_response("Turn up the volume", context)
        self.assertIn("not available with your current service level", response.lower())
        self.assertIn("premium", response.lower())
        self.assertIn("you can check your device status", response.lower())
    
    def test_premium_customer_can_control_volume(self):
        """Verify that premium tier customers can control volume."""
        # Test the request analysis with real API call
        result = analyze_request("Turn up the volume")
        
        # Verify the response
        self.assertEqual(result["primary_action"], "volume_control")
        self.assertIn("volume_control", result["all_actions"])
        self.assertFalse(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
        
        # Test response generation for premium customer
        context = self._prepare_context(result, self.premium_customer)
        response = generate_response("Turn up the volume", context)
        self.assertNotIn("not available", response.lower())
        self.assertNotIn("upgrade", response.lower())
    
    def test_ambiguous_request_handling(self):
        """Verify that ambiguous requests are identified and handled appropriately."""
        # Test the request analysis with real API call
        result = analyze_request("Turn up the volume and power on")
        
        # Verify the response
        self.assertEqual(result["primary_action"], "device_power")
        self.assertIn("device_power", result["all_actions"])
        self.assertIn("volume_control", result["all_actions"])
        self.assertTrue(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
    
    def test_out_of_scope_request_handling(self):
        """Verify that out-of-scope requests are identified and handled appropriately."""
        # Test the request analysis with real API call
        result = analyze_request("What's the weather like today?")
        
        # Verify the response
        self.assertIsNone(result["primary_action"])
        self.assertEqual(result["all_actions"], [])
        self.assertFalse(result["ambiguous"])
        self.assertTrue(result["out_of_scope"])
    
    def test_basic_customer_cannot_change_songs(self):
        """Verify that basic tier customers cannot change songs."""
        # Test the request analysis with real API call
        result = analyze_request("Play next song")
        
        # Verify the response
        self.assertEqual(result["primary_action"], "song_changes")
        self.assertIn("song_changes", result["all_actions"])
        self.assertFalse(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
        
        # Test response generation for basic customer
        context = self._prepare_context(result, self.basic_customer)
        response = generate_response("Play next song", context)
        
        # Check for key phrases indicating service level restriction
        self.assertTrue(
            any(phrase in response.lower() for phrase in [
                "not available with your current service level",
                "does not allow changing songs",
                "basic service plan does not allow"
            ]),
            f"Response should indicate service level restriction, got: {response}"
        )
        self.assertIn("enterprise", response.lower())
        self.assertIn("you can check your device status", response.lower())
    
    def test_premium_customer_cannot_change_songs(self):
        """Verify that premium tier customers cannot change songs."""
        # Test the request analysis with real API call
        result = analyze_request("Skip to next song")
        
        # Verify the response
        self.assertEqual(result["primary_action"], "song_changes")
        self.assertIn("song_changes", result["all_actions"])
        self.assertFalse(result["ambiguous"])
        self.assertFalse(result["out_of_scope"])
        
        # Test response generation for premium customer
        context = self._prepare_context(result, self.premium_customer)
        response = generate_response("Skip to next song", context)
        self.assertIn("not available with your current service level", response.lower())
        self.assertIn("enterprise", response.lower())
        self.assertIn("you can control volume and check device status", response.lower())
    
    def test_enterprise_customer_can_change_songs(self):
        """Verify that enterprise tier customers can change songs."""
        test_cases = [
            ("Play next song", "next"),
            ("Skip this song", "next"),
            ("Play previous song", "previous"),
            ("Go back to the last song", "previous"),
            ("Play Test Song 1", "specific", "Test Song 1"),
            ("Switch to Test Song 2", "specific", "Test Song 2"),
            ("I don't like this song", "next"),
            ("Play something else", "next")
        ]
        
        for test_input, expected_action, *extra_args in test_cases:
            with self.subTest(test_input=test_input):
                # Test the request analysis with real API call
                result = analyze_request(test_input)
                
                # Verify the response
                self.assertEqual(result["primary_action"], "song_changes")
                self.assertIn("song_changes", result["all_actions"])
                self.assertFalse(result["ambiguous"])
                self.assertFalse(result["out_of_scope"])
                self.assertEqual(result["context"]["song_action"], expected_action)
                if expected_action == "specific" and extra_args:
                    self.assertEqual(result["context"]["requested_song"], extra_args[0])
                
                # Test response generation for enterprise customer
                context = self._prepare_context(result, self.enterprise_customer)
                response = generate_response(test_input, context)
                self.assertNotIn("not available", response.lower())
                self.assertNotIn("upgrade", response.lower())
                if expected_action == "specific" and extra_args:
                    self.assertIn(extra_args[0].lower(), response.lower())
    
    def test_song_changes_with_powered_off_device(self):
        """Verify that song changes are not allowed when device is powered off."""
        # Create an enterprise customer with a powered off device
        customer = Customer(
            customer_id="test-enterprise",
            name="Enterprise User",
            service_level="enterprise",
            device={"id": "device-1", "type": "speaker", "power": "off"}
        )
        
        # Test the request analysis with real API call
        result = analyze_request("Play next song")
        
        # Verify the response
        self.assertEqual(result["primary_action"], "song_changes")
        
        # Test response generation
        context = self._prepare_context(result, customer)
        response = generate_response("Play next song", context)
        self.assertIn("powered off", response.lower())
        self.assertTrue(any(phrase in response.lower() for phrase in ["turn on your device", "turn on your speaker"]),
                       f"Response should ask to turn on device/speaker, got: {response}")
    
    def test_song_changes_with_nonexistent_song(self):
        """Verify handling of requests for nonexistent songs."""
        # Test the request analysis with real API call
        result = analyze_request("Play NonexistentSong")
        
        # Verify the response
        self.assertEqual(result["primary_action"], "song_changes")
        self.assertEqual(result["context"]["song_action"], "specific")
        self.assertEqual(result["context"]["requested_song"], "NonexistentSong")
        
        # Test response generation
        context = self._prepare_context(result, self.enterprise_customer)
        response = generate_response("Play NonexistentSong", context)
        self.assertIn("could not find", response.lower())
        self.assertIn("nonexistentsong", response.lower())
        self.assertIn("please try another song", response.lower())
    
    def test_ambiguous_song_change_request(self):
        """Verify handling of ambiguous song change requests."""
        # Test the request analysis with real API call
        result = analyze_request("Turn it up and play the next song")
        
        # Verify the response
        self.assertEqual(result["primary_action"], "song_changes")
        self.assertIn("song_changes", result["all_actions"])
        self.assertIn("volume_control", result["all_actions"])
        self.assertTrue(result["ambiguous"])
        
        # Test response generation
        context = self._prepare_context(result, self.enterprise_customer)
        response = generate_response("Turn it up and play the next song", context)
        self.assertIn("multiple actions", response.lower())
        self.assertIn("one at a time", response.lower())

if __name__ == '__main__':
    unittest.main() 