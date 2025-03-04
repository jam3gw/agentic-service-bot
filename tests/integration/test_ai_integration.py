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

class TestAIIntegration(unittest.TestCase):
    """Integration tests for AI integration"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock customer
        self.customer = lambda_chat.Customer(
            'cust_001',
            'Jane Smith',
            'basic',
            [
                {
                    'id': 'dev_001',
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                }
            ]
        )
        
        # Set up mock permissions
        self.permissions = {
            'allowed_actions': [
                'status_check',
                'volume_control',
                'device_info'
            ],
            'max_devices': 1,
            'support_priority': 'standard'
        }

    @patch('anthropic.Anthropic')
    def test_generate_response(self, mock_anthropic):
        """Test generating a response using the Anthropic API"""
        # Set up mock Anthropic client
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Configure mock response from Anthropic
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Here's the information about your smart speaker.")]
        mock_anthropic_instance.messages.create.return_value = mock_message
        
        # Generate a response
        response = lambda_chat.generate_response(
            "What are the specs of my smart speaker?",
            {
                "customer": self.customer,
                "devices": self.customer.devices,
                "permissions": self.permissions,
                "action_allowed": True,
                "request_type": "device_info"
            }
        )
        
        # Verify the response
        self.assertEqual(response, "Here's the information about your smart speaker.")
        
        # Verify that the Anthropic API was called with the correct parameters
        mock_anthropic_instance.messages.create.assert_called_once()
        call_args = mock_anthropic_instance.messages.create.call_args[1]
        self.assertEqual(call_args['model'], lambda_chat.ANTHROPIC_MODEL)
        self.assertIn("You are an AI assistant for a smart home device company", call_args['system'])
        self.assertIn("Jane Smith", call_args['system'])
        self.assertIn("basic service level", call_args['system'])
        self.assertIn("SmartSpeaker in the living room", call_args['system'])
        self.assertEqual(call_args['messages'][0]['role'], 'user')
        self.assertEqual(call_args['messages'][0]['content'], "What are the specs of my smart speaker?")

    def test_build_system_prompt(self):
        """Test building a system prompt based on context"""
        # Build a system prompt with full context
        system_prompt = lambda_chat.build_system_prompt({
            "customer": self.customer,
            "devices": self.customer.devices,
            "permissions": self.permissions,
            "action_allowed": True,
            "request_type": "device_info"
        })
        
        # Verify the system prompt
        self.assertIn("You are an AI assistant for a smart home device company", system_prompt)
        self.assertIn("Jane Smith", system_prompt)
        self.assertIn("basic service level", system_prompt)
        self.assertIn("SmartSpeaker in the living room", system_prompt)
        self.assertIn("status_check", system_prompt)
        self.assertIn("volume_control", system_prompt)
        self.assertIn("device_info", system_prompt)
        self.assertIn("IS permitted", system_prompt)
        
        # Build a system prompt with action not allowed
        system_prompt = lambda_chat.build_system_prompt({
            "customer": self.customer,
            "devices": self.customer.devices,
            "permissions": self.permissions,
            "action_allowed": False,
            "request_type": "device_relocation"
        })
        
        # Verify the system prompt
        self.assertIn("NOT permitted", system_prompt)
        self.assertIn("Politely explain this limitation", system_prompt)
        
        # Build a system prompt with minimal context
        system_prompt = lambda_chat.build_system_prompt({
            "customer": self.customer
        })
        
        # Verify the system prompt
        self.assertIn("You are an AI assistant for a smart home device company", system_prompt)
        self.assertIn("Jane Smith", system_prompt)
        self.assertIn("basic service level", system_prompt)
        self.assertNotIn("SmartSpeaker", system_prompt)
        self.assertNotIn("permitted", system_prompt)
        
        # Build a system prompt with no context
        system_prompt = lambda_chat.build_system_prompt()
        
        # Verify the system prompt
        self.assertEqual(system_prompt, "You are a helpful AI assistant for a smart home device company.")

    @patch('anthropic.Anthropic')
    def test_generate_response_error_handling(self, mock_anthropic):
        """Test error handling when generating a response"""
        # Set up mock Anthropic client
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Configure mock to raise an exception
        mock_anthropic_instance.messages.create.side_effect = Exception("API error")
        
        # Generate a response
        response = lambda_chat.generate_response(
            "What are the specs of my smart speaker?",
            {
                "customer": self.customer,
                "devices": self.customer.devices,
                "permissions": self.permissions,
                "action_allowed": True,
                "request_type": "device_info"
            }
        )
        
        # Verify the response
        self.assertIn("I apologize", response)
        self.assertIn("trouble processing", response)

if __name__ == '__main__':
    unittest.main() 