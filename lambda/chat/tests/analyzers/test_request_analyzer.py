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
    
    def test_identify_device_status_request(self):
        """Test identifying device status requests."""
        test_cases = [
            "What's the status of my speaker?",
            "Is my speaker on?",
            "Check if my device is working",
            "What's the state of my speaker?",
            "Is my speaker turned on or off?"
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                request_type = RequestAnalyzer.identify_request_type(text)
                self.assertEqual(request_type, "device_status", f"Failed to identify device status request: {text}")
    
    def test_identify_device_power_request(self):
        """Test identifying device power requests."""
        test_cases = [
            "Turn on my speaker",
            "Turn off my device",
            "Switch on the speaker",
            "Power off my speaker",
            "Enable my device",
            "Disable the speaker"
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                request_type = RequestAnalyzer.identify_request_type(text)
                self.assertEqual(request_type, "device_power", f"Failed to identify device power request: {text}")
    
    def test_identify_volume_control_request(self):
        """Test identifying volume control requests."""
        test_cases = [
            "Turn up the volume",
            "Make it louder",
            "Decrease the volume",
            "Make it quieter",
            "Set the volume to 50 percent",
            "Adjust the volume"
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                request_type = RequestAnalyzer.identify_request_type(text)
                self.assertEqual(request_type, "volume_control", f"Failed to identify volume control request: {text}")
    
    def test_identify_song_changes_request(self):
        """Test identifying song change requests."""
        test_cases = [
            "Play the next song",
            "Skip this track",
            "Go to the previous song",
            "Change the song",
            "Play something else",
            "Switch to another track"
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                request_type = RequestAnalyzer.identify_request_type(text)
                self.assertEqual(request_type, "song_changes", f"Failed to identify song changes request: {text}")
    
    def test_get_required_actions(self):
        """Test getting required actions for request types."""
        test_cases = [
            ("device_status", ["device_status"]),
            ("device_power", ["device_power"]),
            ("volume_control", ["volume_control"]),
            ("song_changes", ["song_changes"]),
            ("unknown_type", [])
        ]
        
        for request_type, expected_actions in test_cases:
            with self.subTest(request_type=request_type):
                actions = RequestAnalyzer.get_required_actions(request_type)
                self.assertEqual(actions, expected_actions, f"Incorrect actions for request type: {request_type}")
    
    def test_analyze_device_power_request(self):
        """Test analyzing a device power request."""
        # Test turning on
        result = RequestAnalyzer.analyze("Turn on my speaker")
        self.assertEqual(result["request_type"], "device_power")
        self.assertEqual(result["required_actions"], ["device_power"])
        self.assertEqual(result["context"]["power_state"], "on")
        
        # Test turning off
        result = RequestAnalyzer.analyze("Turn off my speaker")
        self.assertEqual(result["request_type"], "device_power")
        self.assertEqual(result["required_actions"], ["device_power"])
        self.assertEqual(result["context"]["power_state"], "off")
    
    def test_analyze_volume_control_request(self):
        """Test analyzing a volume control request."""
        # Test increasing volume
        result = RequestAnalyzer.analyze("Turn up the volume")
        self.assertEqual(result["request_type"], "volume_control")
        self.assertEqual(result["required_actions"], ["volume_control"])
        self.assertEqual(result["context"]["volume_direction"], "up")
        
        # Test decreasing volume
        result = RequestAnalyzer.analyze("Turn down the volume")
        self.assertEqual(result["request_type"], "volume_control")
        self.assertEqual(result["required_actions"], ["volume_control"])
        self.assertEqual(result["context"]["volume_direction"], "down")
        
        # Test setting specific volume
        result = RequestAnalyzer.analyze("Set the volume to 50 percent")
        self.assertEqual(result["request_type"], "volume_control")
        self.assertEqual(result["required_actions"], ["volume_control"])
        self.assertEqual(result["context"].get("volume_level"), 50)
    
    def test_analyze_song_changes_request(self):
        """Test analyzing a song changes request."""
        # Test next song
        result = RequestAnalyzer.analyze("Play the next song")
        self.assertEqual(result["request_type"], "song_changes")
        self.assertEqual(result["required_actions"], ["song_changes"])
        self.assertEqual(result["context"]["song_action"], "next")
        
        # Test previous song
        result = RequestAnalyzer.analyze("Play the previous song")
        self.assertEqual(result["request_type"], "song_changes")
        self.assertEqual(result["required_actions"], ["song_changes"])
        self.assertEqual(result["context"]["song_action"], "previous")
    
    def test_analyze_unknown_request(self):
        """Test analyzing an unknown request."""
        result = RequestAnalyzer.analyze("What's the weather like today?")
        self.assertIsNone(result["request_type"])
        self.assertEqual(result["required_actions"], [])
        self.assertEqual(result["context"], {})

if __name__ == "__main__":
    unittest.main() 