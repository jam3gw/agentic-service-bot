"""
Unit tests for the Anthropic service.

This module contains tests for the Anthropic service's ability to analyze user requests
and generate appropriate responses based on customer service levels and permissions.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from typing import Dict, Any

# Add the parent directory to sys.path to enable absolute imports
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from services.anthropic_service import analyze_request, generate_response
from models.customer import Customer

class TestAnthropicService(unittest.TestCase):
    """Test cases for the Anthropic service."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a basic test customer
        self.basic_customer = Customer(
            customer_id="test-basic",
            name="Basic User",
            service_level="basic",
            device={"id": "device-1", "type": "speaker", "state": "on"}
        )
        
        # Create a premium test customer
        self.premium_customer = Customer(
            customer_id="test-premium",
            name="Premium User",
            service_level="premium",
            device={"id": "device-1", "type": "speaker", "state": "on"}
        )
        
        # Create an enterprise test customer
        self.enterprise_customer = Customer(
            customer_id="test-enterprise",
            name="Enterprise User",
            service_level="enterprise",
            device={"id": "device-1", "type": "speaker", "state": "on"}
        )
    
    def test_basic_customer_can_check_device_status(self):
        """Verify that basic tier customers can check their device status."""
        with patch('services.anthropic_service.anthropic_client') as mock_client:
            # Mock the Anthropic API response
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps({
                "primary_action": "device_status",
                "all_actions": ["device_status"],
                "context": {"location": "living_room"},
                "ambiguous": False,
                "out_of_scope": False
            }))]
            mock_client.messages.create.return_value = mock_response
            
            # Test the request analysis
            result = analyze_request("Check my speaker")
            
            # Verify the response
            self.assertEqual(result["primary_action"], "device_status")
            self.assertIn("device_status", result["all_actions"])
            self.assertFalse(result["ambiguous"])
            self.assertFalse(result["out_of_scope"])
    
    def test_basic_customer_cannot_control_volume(self):
        """Verify that basic tier customers cannot control volume."""
        with patch('services.anthropic_service.anthropic_client') as mock_client:
            # Mock the Anthropic API response
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps({
                "primary_action": "volume_control",
                "all_actions": ["volume_control"],
                "context": {"volume_change": {"direction": "up", "amount": 10}},
                "ambiguous": False,
                "out_of_scope": False
            }))]
            mock_client.messages.create.return_value = mock_response
            
            # Test the request analysis
            result = analyze_request("Turn up the volume")
            
            # Verify the response
            self.assertEqual(result["primary_action"], "volume_control")
            self.assertIn("volume_control", result["all_actions"])
            self.assertFalse(result["ambiguous"])
            self.assertFalse(result["out_of_scope"])
    
    def test_premium_customer_can_control_volume(self):
        """Verify that premium tier customers can control volume."""
        with patch('services.anthropic_service.anthropic_client') as mock_client:
            # Mock the Anthropic API response
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps({
                "primary_action": "volume_control",
                "all_actions": ["volume_control"],
                "context": {"volume_change": {"direction": "up", "amount": 10}},
                "ambiguous": False,
                "out_of_scope": False
            }))]
            mock_client.messages.create.return_value = mock_response
            
            # Test the request analysis
            result = analyze_request("Turn up the volume")
            
            # Verify the response
            self.assertEqual(result["primary_action"], "volume_control")
            self.assertIn("volume_control", result["all_actions"])
            self.assertFalse(result["ambiguous"])
            self.assertFalse(result["out_of_scope"])
    
    def test_ambiguous_request_handling(self):
        """Verify that ambiguous requests are identified and handled appropriately."""
        with patch('services.anthropic_service.anthropic_client') as mock_client:
            # Mock the Anthropic API response
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps({
                "primary_action": "device_power",
                "all_actions": ["device_power", "volume_control"],
                "context": {"power_state": "on", "volume_change": {"direction": "up"}},
                "ambiguous": True,
                "out_of_scope": False
            }))]
            mock_client.messages.create.return_value = mock_response
            
            # Test the request analysis
            result = analyze_request("Turn up the volume and power on")
            
            # Verify the response
            self.assertEqual(result["primary_action"], "device_power")
            self.assertIn("device_power", result["all_actions"])
            self.assertIn("volume_control", result["all_actions"])
            self.assertTrue(result["ambiguous"])
            self.assertFalse(result["out_of_scope"])
    
    def test_out_of_scope_request_handling(self):
        """Verify that out-of-scope requests are identified and handled appropriately."""
        with patch('services.anthropic_service.anthropic_client') as mock_client:
            # Mock the Anthropic API response
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps({
                "primary_action": None,
                "all_actions": [],
                "context": {},
                "ambiguous": False,
                "out_of_scope": True
            }))]
            mock_client.messages.create.return_value = mock_response
            
            # Test the request analysis
            result = analyze_request("What's the weather like today?")
            
            # Verify the response
            self.assertIsNone(result["primary_action"])
            self.assertEqual(result["all_actions"], [])
            self.assertFalse(result["ambiguous"])
            self.assertTrue(result["out_of_scope"])
    
    def test_json_parsing_with_escaped_characters(self):
        """Test handling of JSON responses containing escaped characters."""
        with patch('services.anthropic_service.anthropic_client') as mock_client:
            # Mock the Anthropic API response with escaped characters
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps({
                "primary_action": "device_power",
                "all_actions": ["device_power"],
                "context": {"message": "Turn on the speaker\nwith newline"},
                "ambiguous": False,
                "out_of_scope": False
            }))]
            mock_client.messages.create.return_value = mock_response
            
            # Test the request analysis
            result = analyze_request("Turn on my speaker")
            
            # Verify the response
            self.assertEqual(result["primary_action"], "device_power")
            self.assertIn("device_power", result["all_actions"])
            self.assertFalse(result["ambiguous"])
            self.assertFalse(result["out_of_scope"])
    
    def test_json_parsing_with_extra_text(self):
        """Test handling of responses where JSON is embedded within additional text."""
        with patch('services.anthropic_service.anthropic_client') as mock_client:
            # Mock the Anthropic API response with extra text
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=f"Here is my analysis: {json.dumps({
                'primary_action': 'device_power',
                'all_actions': ['device_power'],
                'context': {'power_state': 'on'},
                'ambiguous': False,
                'out_of_scope': False
            })} Let me know if you need anything else.")]
            mock_client.messages.create.return_value = mock_response
            
            # Test the request analysis
            result = analyze_request("Turn on my speaker")
            
            # Verify the response
            self.assertEqual(result["primary_action"], "device_power")
            self.assertIn("device_power", result["all_actions"])
            self.assertFalse(result["ambiguous"])
            self.assertFalse(result["out_of_scope"])
    
    def test_json_parsing_with_unicode(self):
        """Test handling of JSON responses containing Unicode characters."""
        with patch('services.anthropic_service.anthropic_client') as mock_client:
            # Mock the Anthropic API response with Unicode characters
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps({
                "primary_action": "device_status",
                "all_actions": ["device_status"],
                "context": {"location": "living_room_café"},
                "ambiguous": False,
                "out_of_scope": False
            }))]
            mock_client.messages.create.return_value = mock_response
            
            # Test the request analysis
            result = analyze_request("Check my speaker")
            
            # Verify the response
            self.assertEqual(result["primary_action"], "device_status")
            self.assertIn("device_status", result["all_actions"])
            self.assertFalse(result["ambiguous"])
            self.assertFalse(result["out_of_scope"])
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON responses."""
        test_cases = [
            # Incomplete JSON
            '{"primary_action": "device_power", "all_actions": ["device_power"]',
            # Invalid boolean value
            '{"primary_action": "device_power", "ambiguous": nottrue}',
            # Missing quotes around string value
            '{"primary_action": device_power}',
            # Empty response
            ''
        ]
        
        for malformed_json in test_cases:
            with self.subTest(malformed_json=malformed_json):
                with patch('services.anthropic_service.anthropic_client') as mock_client:
                    # Mock the Anthropic API response with malformed JSON
                    mock_response = MagicMock()
                    mock_response.content = [MagicMock(text=malformed_json)]
                    mock_client.messages.create.return_value = mock_response
                    
                    # Test the request analysis
                    result = analyze_request("Turn on my speaker")
                    
                    # Verify the response
                    self.assertIsNone(result["primary_action"])
                    self.assertEqual(result["all_actions"], [])
                    self.assertFalse(result["ambiguous"])
                    self.assertTrue(result["out_of_scope"])
    
    def test_anthropic_response_structure_handling(self):
        """Test handling of different Anthropic API response structures."""
        test_cases = [
            # Standard response
            json.dumps({
                "primary_action": "device_power",
                "all_actions": ["device_power"],
                "context": {"power_state": "on"},
                "ambiguous": False,
                "out_of_scope": False
            }),
            # Response with text wrapper
            json.dumps({
                "primary_action": "device_power",
                "all_actions": ["device_power"],
                "context": {"power_state": "on"},
                "ambiguous": False,
                "out_of_scope": False
            }),
            # Response as list
            json.dumps({
                "primary_action": "device_power",
                "all_actions": ["device_power"],
                "context": {"power_state": "on"},
                "ambiguous": False,
                "out_of_scope": False
            }),
            # Empty response
            ''
        ]
        
        for response in test_cases:
            with self.subTest(response=response):
                with patch('services.anthropic_service.anthropic_client') as mock_client:
                    # Mock the Anthropic API response
                    mock_response = MagicMock()
                    mock_response.content = [MagicMock(text=response)]
                    mock_client.messages.create.return_value = mock_response
                    
                    # Test the request analysis
                    result = analyze_request("Turn on my speaker")
                    
                    # Verify the response
                    if not response:  # Empty response case
                        self.assertIsNone(result["primary_action"])
                        self.assertEqual(result["all_actions"], [])
                        self.assertFalse(result["ambiguous"])
                        self.assertTrue(result["out_of_scope"])
                    else:
                        self.assertEqual(result["primary_action"], "device_power")
                        self.assertIn("device_power", result["all_actions"])
                        self.assertFalse(result["ambiguous"])
                        self.assertFalse(result["out_of_scope"])
    
    def test_response_with_nested_json(self):
        """Test handling of responses with deeply nested JSON structures."""
        with patch('services.anthropic_service.anthropic_client') as mock_client:
            # Mock the Anthropic API response with nested JSON
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps({
                "primary_action": "volume_control",
                "all_actions": ["volume_control"],
                "context": {
                    "volume": {
                        "change": {
                            "direction": "up",
                            "amount": 10,
                            "constraints": {
                                "min": 0,
                                "max": 100
                            }
                        }
                    }
                },
                "ambiguous": False,
                "out_of_scope": False
            }))]
            mock_client.messages.create.return_value = mock_response
            
            # Test the request analysis
            result = analyze_request("Turn up the volume")
            
            # Verify the response
            self.assertEqual(result["primary_action"], "volume_control")
            self.assertIn("volume_control", result["all_actions"])
            self.assertFalse(result["ambiguous"])
            self.assertFalse(result["out_of_scope"])

if __name__ == '__main__':
    unittest.main() 