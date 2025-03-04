"""
Customer model for the Agentic Service Bot.

This module defines the Customer class which represents a customer in the system
with their associated data and devices.
"""

import os
import sys
from typing import Dict, Any, List, Optional

# Add the parent directory to sys.path to enable absolute imports if needed
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class Customer:
    """
    Represents a customer in the system with their associated data and devices.
    
    Attributes:
        id: Unique identifier for the customer
        name: Full name of the customer
        service_level: Service tier level (basic, premium, enterprise)
        devices: List of smart devices owned by the customer
    """
    
    def __init__(self, customer_id: str, name: str, service_level: str, devices: List[Dict[str, Any]]):
        """
        Initialize a Customer instance.
        
        Args:
            customer_id: Unique identifier for the customer
            name: Full name of the customer
            service_level: Service tier level (basic, premium, enterprise)
            devices: List of smart devices owned by the customer
        """
        self.id = customer_id
        self.name = name
        self.service_level = service_level
        self.devices = devices
    
    def __str__(self) -> str:
        """Return a string representation of the Customer."""
        return f"Customer(id={self.id}, name={self.name}, service_level={self.service_level})"

    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a device by its ID.
        
        Args:
            device_id: The ID of the device to find
            
        Returns:
            The device dictionary if found, None otherwise
        """
        for device in self.devices:
            if device["id"] == device_id:
                return device
        return None

    def get_device_by_location(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Get a device by its location.
        
        Args:
            location: The location of the device to find
            
        Returns:
            The device dictionary if found, None otherwise
        """
        for device in self.devices:
            if device["location"] == location:
                return device
        return None 