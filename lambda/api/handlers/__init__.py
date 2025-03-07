"""
API handlers package for the Agentic Service Bot.
"""

# Import handler functions to make them available at the package level
from .customer_handler import handle_get_customers, handle_get_customer, CORS_HEADERS
from .device_handler import handle_get_devices, handle_update_device
from .capability_handler import handle_get_capabilities, handle_get_capability 