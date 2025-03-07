"""
Customer model for the Agentic Service Bot.

This module defines the Customer class which represents a customer in the system
with their associated data and device.
"""

# Standard library imports
from typing import Dict, Any, Optional

class Customer:
    """
    Represents a customer in the system with their associated data and device.
    
    Attributes:
        id: Unique identifier for the customer
        name: Full name of the customer
        service_level: Service tier level (basic, premium, enterprise)
        device: The customer's smart device
    """
    
    # Class-level attribute declarations to satisfy hasattr checks
    id: str = ""
    name: str = ""
    service_level: str = ""
    device: Dict[str, Any] = {}
    
    def __init__(self, customer_id: str, name: str, service_level: str, device: Dict[str, Any]):
        """
        Initialize a Customer instance.
        
        Args:
            customer_id: Unique identifier for the customer
            name: Full name of the customer
            service_level: Service tier level (basic, premium, enterprise)
            device: The customer's smart device
        """
        self.id = customer_id
        self.name = name
        self.service_level = service_level
        self.device = device
    
    def __str__(self) -> str:
        """Return a string representation of the Customer."""
        return f"Customer(id={self.id}, name={self.name}, service_level={self.service_level})"

    def get_device(self) -> Dict[str, Any]:
        """
        Get the customer's device.
        
        Returns:
            The device dictionary
        """
        return self.device

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Customer instance to a dictionary.
        
        Returns:
            Dictionary representation of the Customer
        """
        return {
            'id': self.id,
            'name': self.name,
            'service_level': self.service_level,
            'device': self.device
        } 