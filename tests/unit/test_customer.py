import unittest
import sys
import os
import importlib.util

# Add the parent directory to the path so we can import the lambda module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the Customer class using a different approach
lambda_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../lambda/chat/index.py'))
spec = importlib.util.spec_from_file_location("lambda_chat", lambda_path)
lambda_chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lambda_chat)
Customer = lambda_chat.Customer

class TestCustomer(unittest.TestCase):
    """Test cases for the Customer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.customer = Customer(
            customer_id="cust_001",
            name="Jane Smith",
            service_level="basic",
            devices=[
                {
                    "id": "dev_001",
                    "type": "SmartSpeaker",
                    "location": "living_room"
                },
                {
                    "id": "dev_002",
                    "type": "SmartDisplay",
                    "location": "kitchen"
                }
            ]
        )

    def test_customer_initialization(self):
        """Test that a customer is initialized correctly"""
        self.assertEqual(self.customer.id, "cust_001")
        self.assertEqual(self.customer.name, "Jane Smith")
        self.assertEqual(self.customer.service_level, "basic")
        self.assertEqual(len(self.customer.devices), 2)

    def test_get_device_by_id(self):
        """Test that a device can be retrieved by ID"""
        # Test existing device
        device = self.customer.get_device_by_id("dev_001")
        self.assertIsNotNone(device)
        self.assertEqual(device["id"], "dev_001")
        self.assertEqual(device["type"], "SmartSpeaker")
        self.assertEqual(device["location"], "living_room")
        
        # Test non-existent device
        device = self.customer.get_device_by_id("dev_999")
        self.assertIsNone(device)

    def test_get_device_by_location(self):
        """Test that a device can be retrieved by location"""
        # Test existing location
        device = self.customer.get_device_by_location("kitchen")
        self.assertIsNotNone(device)
        self.assertEqual(device["id"], "dev_002")
        self.assertEqual(device["type"], "SmartDisplay")
        self.assertEqual(device["location"], "kitchen")
        
        # Test non-existent location
        device = self.customer.get_device_by_location("bedroom")
        self.assertIsNone(device)

    def test_string_representation(self):
        """Test the string representation of a customer"""
        self.assertEqual(
            str(self.customer),
            "Customer(id=cust_001, name=Jane Smith, service_level=basic)"
        )

if __name__ == '__main__':
    unittest.main() 