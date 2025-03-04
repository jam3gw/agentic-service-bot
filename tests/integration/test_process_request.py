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

# Import Customer model and process_request function
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../lambda')))
from chat.models.customer import Customer
from chat.services.request_processor import process_request

class TestProcessRequest(unittest.TestCase):
    """Integration tests for the process_request function"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock DynamoDB tables
        self.mock_messages_table = MagicMock()
        self.mock_customers_table = MagicMock()
        self.mock_service_levels_table = MagicMock()
        
        # Set up mock customer data
        self.customer_data = {
            'id': 'cust_001',
            'name': 'Jane Smith',
            'service_level': 'basic',
            'devices': [
                {
                    'id': 'dev_001',
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                }
            ]
        }
        
        # Set up mock service level data
        self.service_level_data = {
            'level': 'basic',
            'allowed_actions': [
                'status_check',
                'volume_control',
                'device_info'
            ],
            'max_devices': 1,
            'support_priority': 'standard'
        }
        
        # Configure mock responses
        self.mock_customers_table.get_item.return_value = {'Item': self.customer_data}
        self.mock_service_levels_table.get_item.return_value = {'Item': self.service_level_data}
        
        # Create a Customer object from the mock data
        self.mock_customer = Customer(
            self.customer_data['id'],
            self.customer_data['name'],
            self.customer_data['service_level'],
            self.customer_data['devices']
        )

    def test_process_request_with_device_relocation(self):
        """Test processing a device relocation request."""
        # Mock customer data
        mock_customer = Customer(
            "cust_002",
            "John Doe",
            "premium",
            [
                {"id": "dev_002", "type": "SmartSpeaker", "location": "living_room"},
                {"id": "dev_003", "type": "SmartDisplay", "location": "kitchen"}
            ]
        )
        
        # Mock service level permissions
        mock_permissions = {
            "allowed_actions": [
                "status_check",
                "volume_control",
                "device_info",
                "device_relocation",
                "music_services"
            ],
            "max_devices": 5,
            "support_priority": "high"
        }
        
        # Mock the necessary functions
        with patch('chat.services.request_processor.get_customer', return_value=mock_customer), \
             patch('chat.services.request_processor.get_service_level_permissions', return_value=mock_permissions), \
             patch('chat.services.request_processor.generate_response', return_value="I'll move your speaker to the bedroom."), \
             patch('chat.services.request_processor.messages_table.put_item'):
            
            # Test with premium customer (allowed)
            response = process_request("cust_002", "Move my speaker to the bedroom")
            self.assertIn("I'll move your speaker", response)

    def test_process_request_with_multi_room_audio(self):
        """Test processing a multi-room audio request."""
        # Mock customer data
        mock_customer = Customer(
            "cust_003",
            "Alice Johnson",
            "enterprise",
            [
                {"id": "dev_004", "type": "SmartSpeaker", "location": "office"},
                {"id": "dev_005", "type": "SmartSpeaker", "location": "living_room"},
                {"id": "dev_006", "type": "SmartSpeaker", "location": "bedroom"}
            ]
        )
        
        # Mock service level permissions
        mock_permissions = {
            "allowed_actions": [
                "status_check",
                "volume_control",
                "device_info",
                "device_relocation",
                "music_services",
                "multi_room_audio",
                "custom_actions"
            ],
            "max_devices": 10,
            "support_priority": "dedicated"
        }
        
        # Mock the necessary functions
        with patch('chat.services.request_processor.get_customer', return_value=mock_customer), \
             patch('chat.services.request_processor.get_service_level_permissions', return_value=mock_permissions), \
             patch('chat.services.request_processor.generate_response', return_value="I'll set up multi-room audio for your speakers."), \
             patch('chat.services.request_processor.messages_table.put_item'):
            
            # Test with enterprise customer (allowed)
            response = process_request("cust_003", "Play the same music on all my speakers")
            self.assertIn("I'll set up multi-room audio", response)
            
            # Test with specific locations
            response = process_request("cust_003", "Sync audio between my living room and bedroom speakers")
            self.assertIn("I'll set up multi-room audio", response)

    def test_process_request_with_custom_routine(self):
        """Test processing a custom routine request."""
        # Mock customer data
        mock_customer = Customer(
            "cust_003",
            "Alice Johnson",
            "enterprise",
            [
                {"id": "dev_004", "type": "SmartSpeaker", "location": "office"},
                {"id": "dev_005", "type": "SmartSpeaker", "location": "living_room"},
                {"id": "dev_006", "type": "SmartSpeaker", "location": "bedroom"}
            ]
        )
        
        # Mock service level permissions
        mock_permissions = {
            "allowed_actions": [
                "status_check",
                "volume_control",
                "device_info",
                "device_relocation",
                "music_services",
                "multi_room_audio",
                "custom_actions"
            ],
            "max_devices": 10,
            "support_priority": "dedicated"
        }
        
        # Mock the necessary functions
        with patch('chat.services.request_processor.get_customer', return_value=mock_customer), \
             patch('chat.services.request_processor.get_service_level_permissions', return_value=mock_permissions), \
             patch('chat.services.request_processor.generate_response', return_value="I'll create that routine for you."), \
             patch('chat.services.request_processor.messages_table.put_item'):
            
            # Test with enterprise customer (allowed)
            response = process_request("cust_003", "Create a routine called Morning Music to play music at 7:00 am on my bedroom speaker")
            self.assertIn("I'll create that routine for you", response)
            
            # Test with event trigger
            response = process_request("cust_003", "Create a routine when I say goodnight to turn off all speakers")
            self.assertIn("I'll create that routine for you", response)

    def test_process_request_with_disallowed_multi_room_audio(self):
        """Test processing a multi-room audio request for a basic customer (not allowed)."""
        # Mock customer data
        mock_customer = Customer(
            "cust_001",
            "Jane Smith",
            "basic",
            [
                {"id": "dev_001", "type": "SmartSpeaker", "location": "living_room"}
            ]
        )
        
        # Mock service level permissions
        mock_permissions = {
            "allowed_actions": [
                "status_check",
                "volume_control",
                "device_info"
            ],
            "max_devices": 1,
            "support_priority": "standard"
        }
        
        # Mock the necessary functions
        with patch('chat.services.request_processor.get_customer', return_value=mock_customer), \
             patch('chat.services.request_processor.get_service_level_permissions', return_value=mock_permissions), \
             patch('chat.services.request_processor.generate_response', 
                   return_value="I'm sorry, but your basic service level doesn't allow multi-room audio. Please upgrade to premium or enterprise for this feature."), \
             patch('chat.services.request_processor.messages_table.put_item'):
            
            # Test with basic customer (not allowed)
            response = process_request("cust_001", "Play the same music on all my speakers")
            self.assertIn("I'm sorry", response)
            self.assertIn("doesn't allow multi-room audio", response)

    def test_process_request_with_disallowed_custom_routine(self):
        """Test processing a custom routine request for a premium customer (not allowed)."""
        # Mock customer data
        mock_customer = Customer(
            "cust_002",
            "John Doe",
            "premium",
            [
                {"id": "dev_002", "type": "SmartSpeaker", "location": "living_room"},
                {"id": "dev_003", "type": "SmartDisplay", "location": "kitchen"}
            ]
        )
        
        # Mock service level permissions
        mock_permissions = {
            "allowed_actions": [
                "status_check",
                "volume_control",
                "device_info",
                "device_relocation",
                "music_services",
                "multi_room_audio"
            ],
            "max_devices": 5,
            "support_priority": "high"
        }
        
        # Mock the necessary functions
        with patch('chat.services.request_processor.get_customer', return_value=mock_customer), \
             patch('chat.services.request_processor.get_service_level_permissions', return_value=mock_permissions), \
             patch('chat.services.request_processor.generate_response', 
                   return_value="I'm sorry, but your premium service level doesn't allow custom routines. Please upgrade to enterprise for this feature."), \
             patch('chat.services.request_processor.messages_table.put_item'):
            
            # Test with premium customer (not allowed)
            response = process_request("cust_002", "Create a routine called Morning Music to play music at 7:00 am")
            self.assertIn("I'm sorry", response)
            self.assertIn("doesn't allow custom routines", response)

if __name__ == '__main__':
    unittest.main() 