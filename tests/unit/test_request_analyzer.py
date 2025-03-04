import unittest
import sys
import os
import importlib.util

# Add the parent directory to the path so we can import the lambda module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the RequestAnalyzer class using a different approach
lambda_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../lambda/chat/index.py'))
spec = importlib.util.spec_from_file_location("lambda_chat", lambda_path)
lambda_chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lambda_chat)
RequestAnalyzer = lambda_chat.RequestAnalyzer

class TestRequestAnalyzer(unittest.TestCase):
    """Test cases for the RequestAnalyzer class"""

    def test_identify_request_type(self):
        """Test that request types are correctly identified from user text"""
        # Test device relocation
        self.assertEqual(
            RequestAnalyzer.identify_request_type("Can you move my speaker to the bedroom?"),
            "device_relocation"
        )
        
        # Test volume change
        self.assertEqual(
            RequestAnalyzer.identify_request_type("Turn up the volume on my speaker"),
            "volume_change"
        )
        
        # Test device status
        self.assertEqual(
            RequestAnalyzer.identify_request_type("Is my device working properly?"),
            "device_status"
        )
        
        # Test play music
        self.assertEqual(
            RequestAnalyzer.identify_request_type("Play some jazz music in the living room"),
            "play_music"
        )
        
        # Test device info
        self.assertEqual(
            RequestAnalyzer.identify_request_type("What are the specs of my smart speaker?"),
            "device_info"
        )
        
        # Test multi-room setup
        self.assertEqual(
            RequestAnalyzer.identify_request_type("Set up multi-room audio for all my devices"),
            "multi_room_setup"
        )
        
        # Test custom routine
        self.assertEqual(
            RequestAnalyzer.identify_request_type("Create a routine for when I wake up"),
            "custom_routine"
        )
        
        # Test unrecognized request
        self.assertIsNone(
            RequestAnalyzer.identify_request_type("Hello, how are you today?")
        )

    def test_extract_locations(self):
        """Test that source and destination locations are correctly extracted"""
        # Test from/to pattern
        source, destination = RequestAnalyzer.extract_locations(
            "Move my speaker from the living room to the bedroom"
        )
        self.assertEqual(source, "living_room")
        self.assertEqual(destination, "bedroom")
        
        # Test destination only
        source, destination = RequestAnalyzer.extract_locations(
            "Move my speaker to the kitchen"
        )
        self.assertIsNone(source)
        self.assertEqual(destination, "kitchen")
        
        # Test no locations
        source, destination = RequestAnalyzer.extract_locations(
            "How is the weather today?"
        )
        self.assertIsNone(source)
        self.assertIsNone(destination)

    def test_get_required_actions(self):
        """Test that required actions are correctly retrieved for request types"""
        # Test device relocation
        self.assertEqual(
            RequestAnalyzer.get_required_actions("device_relocation"),
            ["device_relocation"]
        )
        
        # Test volume change
        self.assertEqual(
            RequestAnalyzer.get_required_actions("volume_change"),
            ["volume_control"]
        )
        
        # Test unknown request type
        self.assertEqual(
            RequestAnalyzer.get_required_actions("unknown_type"),
            []
        )

if __name__ == '__main__':
    unittest.main() 