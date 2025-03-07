"""
Unit tests for the request analyzer.

This module contains tests for the RequestAnalyzer class to ensure it correctly
identifies request types and extracts required actions.
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
from analyzers.request_analyzer_simplified import RequestAnalyzer

class TestRequestAnalyzer(unittest.TestCase):
    """Tests for the RequestAnalyzer class."""
    
    def setUp(self):
        """Set up test environment."""
        # Capture logging output for testing
        self.log_capture = []
        self.log_handler = logging.StreamHandler()
        self.log_handler.setLevel(logging.INFO)
        logger.addHandler(self.log_handler)
    
    def tearDown(self):
        """Clean up after tests."""
        logger.removeHandler(self.log_handler)
    
    def test_identify_device_status_request(self):
        """Test identifying device status requests."""
        test_cases = [
            # Standard cases
            "What's the status of my speaker?",
            "Is my speaker on?",
            "Check if my device is working",
            "What's the state of my speaker?",
            "Is my speaker turned on or off?",
            # Edge cases
            "STATUS",  # All caps
            "status",  # All lowercase
            "What is the current state",  # Partial match
            "How is my speaker doing?",  # Natural language
            "Can you check my speaker?"  # Indirect request
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                request_type = RequestAnalyzer.identify_request_type(text)
                self.assertEqual(request_type, "device_status", f"Failed to identify device status request: {text}")
    
    def test_identify_device_power_request(self):
        """Test identifying device power requests."""
        test_cases = [
            # Standard cases
            "Turn on my speaker",
            "Turn off my device",
            "Switch on the speaker",
            "Power off my speaker",
            "Enable my device",
            "Disable the speaker",
            # Edge cases
            "TURN ON",  # All caps
            "turn off",  # All lowercase
            "Can you turn it on?",  # Question form
            "I want the speaker turned on",  # Indirect request
            "Start the speaker",  # Alternative phrasing
            "Stop the device"  # Alternative phrasing
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                request_type = RequestAnalyzer.identify_request_type(text)
                self.assertEqual(request_type, "device_power", f"Failed to identify device power request: {text}")
    
    def test_identify_volume_control_request(self):
        """Test identifying volume control requests."""
        test_cases = [
            # Standard cases
            "Turn up the volume",
            "Make it louder",
            "Decrease the volume",
            "Make it quieter",
            "Set the volume to 50 percent",
            "Adjust the volume",
            # Edge cases
            "VOLUME UP",  # All caps
            "volume down",  # All lowercase
            "Can you make it a bit louder?",  # Natural language
            "I can barely hear it",  # Implicit volume request
            "Set volume 75",  # Different format
            "Change volume to maximum"  # Extreme value
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                request_type = RequestAnalyzer.identify_request_type(text)
                self.assertEqual(request_type, "volume_control", f"Failed to identify volume control request: {text}")
    
    def test_identify_song_changes_request(self):
        """Test identifying song change requests."""
        test_cases = [
            # Standard cases
            "Play the next song",
            "Skip this track",
            "Go to the previous song",
            "Change the song",
            "Play something else",
            "Switch to another track",
            # Edge cases
            "NEXT SONG",  # All caps
            "next track",  # All lowercase
            "Can you play another song?",  # Question form
            "I don't like this song",  # Implicit request
            "Skip",  # Single word
            "Forward"  # Alternative word
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                request_type = RequestAnalyzer.identify_request_type(text)
                self.assertEqual(request_type, "song_changes", f"Failed to identify song changes request: {text}")
    
    def test_request_type_priority(self):
        """Test that request types are correctly prioritized when multiple matches exist."""
        # Test cases with multiple potential matches
        test_cases = [
            ("Turn on the volume", "volume_control"),  # Volume should win over power
            ("Change the power and volume", "device_power"),  # Power should win
            ("Skip to the next song and turn up volume", "song_changes"),  # Song changes should win
            ("Set the volume and change the song", "volume_control")  # First match should win
        ]
        
        for text, expected_type in test_cases:
            with self.subTest(text=text):
                request_type = RequestAnalyzer.identify_request_type(text)
                self.assertEqual(request_type, expected_type, 
                               f"Incorrect priority for mixed request: {text}")
    
    def test_get_required_actions(self):
        """Test getting required actions for request types."""
        test_cases = [
            ("device_status", ["device_status"]),
            ("device_power", ["device_power"]),
            ("volume_control", ["volume_control"]),
            ("song_changes", ["song_changes"]),
            ("unknown_type", []),
            ("", []),  # Empty string
            (None, [])  # None value
        ]
        
        for request_type, expected_actions in test_cases:
            with self.subTest(request_type=request_type):
                actions = RequestAnalyzer.get_required_actions(request_type)
                self.assertEqual(actions, expected_actions, 
                               f"Incorrect actions for request type: {request_type}")
    
    def test_analyze_device_power_request(self):
        """Test analyzing a device power request."""
        test_cases = [
            # Test turning on
            ("Turn on my speaker", "on"),
            ("Enable the device", "on"),
            ("Start my speaker", "on"),
            ("Activate the device", "on"),
            # Test turning off
            ("Turn off my speaker", "off"),
            ("Disable the device", "off"),
            ("Stop my speaker", "off"),
            ("Deactivate the device", "off"),
            # Edge cases
            ("TURN ON THE SPEAKER", "on"),  # All caps
            ("turn off the device", "off"),  # All lowercase
            ("Please turn it on", "on"),  # Polite form
            ("Can you turn it off?", "off")  # Question form
        ]
        
        for text, expected_state in test_cases:
            with self.subTest(text=text):
                result = RequestAnalyzer.analyze(text)
                self.assertEqual(result["request_type"], "device_power")
                self.assertEqual(result["required_actions"], ["device_power"])
                self.assertEqual(result["context"]["power_state"], expected_state)
    
    def test_analyze_volume_control_request(self):
        """Test analyzing a volume control request."""
        test_cases = [
            # Test volume direction
            ("Turn up the volume", "up", None),
            ("Make it louder", "up", None),
            ("Increase volume", "up", None),
            ("Turn down the volume", "down", None),
            ("Make it quieter", "down", None),
            ("Decrease volume", "down", None),
            # Test specific volume levels
            ("Set the volume to 50 percent", "set", 50),
            ("Volume at 75", "set", 75),
            ("Change volume to 25%", "set", 25),
            # Edge cases
            ("VOLUME UP", "up", None),  # All caps
            ("volume down", "down", None),  # All lowercase
            ("Set volume to 0", "set", 0),  # Zero volume
            ("Set volume to 100", "set", 100),  # Max volume
            ("Volume to hundred percent", "set", 100)  # Text number
        ]
        
        for text, expected_direction, expected_level in test_cases:
            with self.subTest(text=text):
                result = RequestAnalyzer.analyze(text)
                self.assertEqual(result["request_type"], "volume_control")
                self.assertEqual(result["required_actions"], ["volume_control"])
                self.assertEqual(result["context"]["volume_direction"], expected_direction)
                if expected_level is not None:
                    self.assertEqual(result["context"].get("volume_level"), expected_level)
    
    def test_analyze_song_changes_request(self):
        """Test analyzing a song changes request."""
        test_cases = [
            # Test next song
            ("Play the next song", "next"),
            ("Skip this track", "next"),
            ("Next song please", "next"),
            ("Forward", "next"),
            # Test previous song
            ("Play the previous song", "previous"),
            ("Go back one song", "previous"),
            ("Previous track", "previous"),
            ("Backward", "previous"),
            # Edge cases
            ("NEXT SONG", "next"),  # All caps
            ("previous track", "previous"),  # All lowercase
            ("Skip this one", "next"),  # Implicit next
            ("Go back", "previous")  # Implicit previous
        ]
        
        for text, expected_action in test_cases:
            with self.subTest(text=text):
                result = RequestAnalyzer.analyze(text)
                self.assertEqual(result["request_type"], "song_changes")
                self.assertEqual(result["required_actions"], ["song_changes"])
                self.assertEqual(result["context"]["song_action"], expected_action)
    
    def test_analyze_unknown_request(self):
        """Test analyzing an unknown request."""
        test_cases = [
            "What's the weather like today?",
            "Tell me a joke",
            "What time is it?",
            "",  # Empty string
            "   ",  # Whitespace only
            None  # None value
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = RequestAnalyzer.analyze(text)
                self.assertIsNone(result["request_type"])
                self.assertEqual(result["required_actions"], [])
                self.assertEqual(result["context"], {})
    
    def test_logging(self):
        """Test that appropriate logging occurs during request analysis."""
        with self.assertLogs(level=logging.INFO) as log_context:
            # Test successful request analysis
            result = RequestAnalyzer.analyze("Turn up the volume")
            self.assertEqual(result["request_type"], "volume_control")
            
            # Test unknown request
            result = RequestAnalyzer.analyze("What's the weather like?")
            self.assertIsNone(result["request_type"])
            
            # Verify logs contain key information
            log_output = '\n'.join(log_context.output)
            self.assertIn("Analyzing request:", log_output)
            self.assertIn("volume_control", log_output)
            self.assertIn("up", log_output)

if __name__ == "__main__":
    unittest.main() 