"""
Customer model for the Agentic Service Bot.

This module defines the Customer class which represents a customer in the system
with their associated data and device.
"""

import os
import sys
from typing import Dict, Any, Optional

# Add the parent directory to sys.path to enable absolute imports if needed
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

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
    id: str = None
    name: str = None
    service_level: str = None
    device: Dict[str, Any] = None
    
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