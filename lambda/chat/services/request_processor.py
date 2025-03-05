"""
Request processor for the Agentic Service Bot.

This module provides functions for processing user requests, analyzing them,
and generating appropriate responses based on service level permissions.

Service Levels:
- Basic: Can control device power (on/off)
- Premium: Basic + volume control
- Enterprise: Premium + light control
"""

import time
import os
import sys
import logging
import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from analyzers.request_analyzer_simplified import RequestAnalyzer
from services.dynamodb_service import (
    get_customer, 
    get_service_level_permissions, 
    update_device_state,
    store_message
)
from services.llm_service import generate_response
from models.customer import Customer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_action_allowed(service_level, action: str) -> bool:
    """
    Check if an action is allowed for a given service level.
    
    Args:
        service_level: The service level to check (can be a string or a Customer object)
        action: The action to check
        
    Returns:
        True if the action is allowed, False otherwise
    """
    # Extract service level string if a Customer object was passed
    if hasattr(service_level, 'service_level'):
        service_level = service_level.service_level
    
    # Handle None or empty service level
    if not service_level:
        return False
    
    # Get permissions from DynamoDB
    permissions = get_service_level_permissions(service_level.lower())
    
    # Get the allowed actions for the service level
    service_level_info = permissions.get("allowed_actions", [])
    
    return action in service_level_info

def process_request(request=None, **kwargs) -> Dict[str, Any]:
    """
    Process a user request and generate a response.
    
    Args:
        request: A dictionary containing the request details
            - customer_id: The ID of the customer
            - user_input: The text input from the user
            - connection_id: The WebSocket connection ID (optional)
        **kwargs: Alternative way to pass parameters directly:
            - customer_id: The ID of the customer
            - user_input: The text input from the user
            - connection_id: The WebSocket connection ID (optional)
            
    Returns:
        A dictionary containing the response details
    """
    # Handle both dictionary and keyword arguments
    if request is None:
        request = {}
    
    # Extract request details (prioritize kwargs over request dict)
    customer_id = kwargs.get("customer_id", request.get("customer_id"))
    user_input = kwargs.get("user_input", request.get("user_input", ""))
    connection_id = kwargs.get("connection_id", request.get("connection_id"))
    
    # Get customer data
    customer = get_customer(customer_id)
    if not customer:
        return {
            "success": False,
            "message": f"Customer with ID {customer_id} not found"
        }
    
    # Get service level permissions
    service_level = customer.service_level
    
    # Analyze the request to determine the type
    request_type = RequestAnalyzer.identify_request_type(user_input)
    
    # Build context for LLM
    context = {
        "customer": customer,
        "request_type": request_type,
        "service_level": service_level,
        "permissions": get_service_level_permissions(service_level),
        "devices": [customer.get_device()],
        "action_executed": False,
        "timestamp": datetime.now().isoformat()
    }
    
    # If a device is mentioned in the request, identify it
    device = customer.get_device()
    device_id = device.get("id")
    
    # Process based on request type
    if request_type == "device_power":
        if is_action_allowed(service_level, "device_control"):
            # Determine if turning on or off
            turn_on = any(keyword in user_input.lower() for keyword in ["on", "start", "activate"])
            turn_off = any(keyword in user_input.lower() for keyword in ["off", "stop", "deactivate"])
            
            new_state = "on" if turn_on else "off" if turn_off else None
            
            if new_state:
                # Update device state
                update_device_state(customer_id, device_id, {"power": new_state})
                context["action_executed"] = True
                context["device_state"] = new_state
        else:
            context["error"] = "This action requires a higher service level"
    
    elif request_type == "volume_control":
        if is_action_allowed(service_level, "volume_control"):
            # Determine volume change
            current_volume = device.get("volume", 50)
            
            # Check for volume up/down
            volume_up = any(keyword in user_input.lower() for keyword in ["up", "increase", "louder", "higher"])
            volume_down = any(keyword in user_input.lower() for keyword in ["down", "decrease", "lower", "quieter"])
            
            # Check for specific volume level
            volume_match = re.search(r"(?:set|change|make|to)\s+(?:the\s+)?volume\s+(?:to\s+)?(\d+)", user_input.lower())
            
            new_volume = current_volume
            if volume_up:
                new_volume = min(100, current_volume + 10)
            elif volume_down:
                new_volume = max(0, current_volume - 10)
            elif volume_match:
                requested_volume = int(volume_match.group(1))
                new_volume = max(0, min(100, requested_volume))
            
            if new_volume != current_volume:
                # Update device volume
                update_device_state(customer_id, device_id, {"volume": new_volume})
                context["action_executed"] = True
                context["volume_change"] = {
                    "previous": current_volume,
                    "new": new_volume
                }
        else:
            context["error"] = "Volume control requires Premium or Enterprise service level"
    
    elif request_type == "light_control":
        if is_action_allowed(service_level, "light_control"):
            # Determine light action
            turn_on = any(keyword in user_input.lower() for keyword in ["on", "brighten", "illuminate"])
            turn_off = any(keyword in user_input.lower() for keyword in ["off", "dim", "darken"])
            toggle = "toggle" in user_input.lower()
            
            current_state = device.get("light", "off")
            new_state = None
            
            if turn_on:
                new_state = "on"
            elif turn_off:
                new_state = "off"
            elif toggle:
                new_state = "off" if current_state == "on" else "on"
            
            if new_state and new_state != current_state:
                # Update device light state
                update_device_state(customer_id, device_id, {"light": new_state})
                context["action_executed"] = True
                context["light_state"] = new_state
        else:
            context["error"] = "Light control requires Enterprise service level"
    
    # Generate response using LLM
    response_text = generate_response(user_input, context)
    
    # Store the message
    message_data = {
        "customer_id": customer_id,
        "user_input": user_input,
        "response": response_text,
        "request_type": request_type,
        "timestamp": context["timestamp"],
        "connection_id": connection_id
    }
    
    # Generate a conversation ID (using connection_id as fallback)
    conversation_id = connection_id or f"conv-{customer_id}-{context['timestamp']}"
    
    # Store the user message and bot response
    store_message(
        conversation_id=conversation_id,
        customer_id=customer_id,
        message=user_input,
        sender="user",
        request_type=request_type
    )
    
    store_message(
        conversation_id=conversation_id,
        customer_id=customer_id,
        message=response_text,
        sender="bot",
        request_type=request_type,
        actions_allowed=context.get("action_executed", False)
    )
    
    return {
        "success": True,
        "message": response_text,
        "request_type": request_type,
        "action_executed": context.get("action_executed", False)
    }

def execute_action(action: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an action based on the request type and context.
    
    Args:
        action: The action to execute
        context: The context containing request details
        
    Returns:
        Updated context with action results
    """
    # This is a simplified version that only handles our three main actions
    customer = context.get("customer")
    service_level = customer.service_level if isinstance(customer, Customer) else customer.get("service_level")
    
    # Check if the action is allowed for the service level
    if not is_action_allowed(service_level, action):
        context["error"] = f"The {action} action is not allowed with your service level"
        return context
    
    # Get the device
    device = None
    if isinstance(customer, Customer):
        device = customer.get_device()
    else:
        devices = context.get("devices", [])
        if devices:
            device = devices[0]
    
    if not device:
        context["error"] = "No device found"
        return context
    
    device_id = device.get("id")
    customer_id = customer.id if isinstance(customer, Customer) else customer.get("customer_id")
    
    # Execute the appropriate action
    if action == "device_power":
        # Handle device power control
        power_state = context.get("power_state")
        if power_state:
            update_device_state(customer_id, device_id, {"power": power_state})
            context["action_executed"] = True
    
    elif action == "volume_control":
        # Handle volume control
        volume_change = context.get("volume_change")
        if volume_change:
            new_volume = volume_change.get("new")
            update_device_state(customer_id, device_id, {"volume": new_volume})
            context["action_executed"] = True
    
    elif action == "song_changes":
        # Handle song changes
        song_change = context.get("song_change")
        if song_change:
            new_song = song_change.get("new")
            update_device_state(customer_id, device_id, {"current_song": new_song})
            context["action_executed"] = True
    
    return context