"""
Shared utility functions for the Agentic Service Bot Lambda functions.

This module provides utility functions used across multiple Lambda functions.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Union

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def convert_decimal_to_float(obj: Any) -> Any:
    """
    Recursively convert Decimal objects to floats in a data structure.
    
    Args:
        obj: The object to convert
        
    Returns:
        The object with all Decimal values converted to floats
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj

def convert_float_to_decimal(obj: Any) -> Any:
    """
    Recursively convert float objects to Decimal in a data structure for DynamoDB operations.
    
    Args:
        obj: The object to convert
        
    Returns:
        The object with all float values converted to Decimal objects
    """
    if isinstance(obj, float):
        return Decimal(str(obj))  # Convert via string to preserve precision
    elif isinstance(obj, dict):
        return {k: convert_float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_float_to_decimal(item) for item in obj]
    return obj 