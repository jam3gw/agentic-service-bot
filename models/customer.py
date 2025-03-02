import json
import os
from typing import Dict, List, Optional

class Customer:
    def __init__(self, customer_id: str, name: str, service_level: str, devices: List[Dict]):
        self.id = customer_id
        self.name = name
        self.service_level = service_level
        self.devices = devices
    
    def __str__(self) -> str:
        return f"Customer(id={self.id}, name={self.name}, service_level={self.service_level})"

    def get_device_by_id(self, device_id: str) -> Optional[Dict]:
        """Get a device by its ID"""
        for device in self.devices:
            if device["id"] == device_id:
                return device
        return None

    def get_device_by_location(self, location: str) -> Optional[Dict]:
        """Get a device by its location"""
        for device in self.devices:
            if device["location"] == location:
                return device
        return None

class CustomerDB:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self._load_data()
    
    def _load_data(self):
        """Load customer data from JSON file"""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Customer data file not found at {self.data_path}")
        
        with open(self.data_path, 'r') as f:
            data = json.load(f)
        
        self.customers_data = data["customers"]
        self.service_levels = data["service_levels"]
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a customer by ID"""
        for cust_data in self.customers_data:
            if cust_data["id"] == customer_id:
                return Customer(
                    cust_data["id"],
                    cust_data["name"],
                    cust_data["service_level"],
                    cust_data["devices"]
                )
        return None
    
    def get_service_level_permissions(self, service_level: str) -> Dict:
        """Get the permissions for a given service level"""
        if service_level in self.service_levels:
            return self.service_levels[service_level]
        raise ValueError(f"Unknown service level: {service_level}")
    
    def is_action_allowed(self, customer: Customer, action: str) -> bool:
        """Check if a specific action is allowed for a customer's service level"""
        permissions = self.get_service_level_permissions(customer.service_level)
        return action in permissions["allowed_actions"]