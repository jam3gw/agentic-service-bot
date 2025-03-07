"""
Request processor for the Agentic Service Bot.

This module provides functions for processing user requests, analyzing them,
and generating appropriate responses based on service level permissions.

Service Levels:
- Basic: Can check device status and control device power (on/off)
- Premium: Basic + volume control
- Enterprise: Premium + song changes
"""

import time
import os
import sys
import logging
import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Remove sys.path modification
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use relative imports
from ..analyzers.request_analyzer_simplified import RequestAnalyzer
from .dynamodb_service import (
    get_customer, 
    get_service_level_permissions,
    store_message
)
from .anthropic_service import analyze_request
from ..models.customer import Customer

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
    
    logger.info(f"Checking if action '{action}' is allowed for service level '{service_level}'")
    
    # Handle None or empty service level
    if not service_level:
        logger.info(f"Service level is None or empty, action '{action}' is not allowed")
        return False
    
    # Basic actions that should be allowed for all service levels
    basic_actions = ["device_status", "device_power"]
    if action in basic_actions:
        logger.info(f"Action '{action}' is a basic action allowed for all service levels")
        return True
    
    # Get permissions from DynamoDB
    permissions = get_service_level_permissions(service_level.lower())
    logger.info(f"Retrieved permissions for service level '{service_level}': {permissions}")
    
    # Get the allowed actions for the service level
    allowed_actions = permissions.get("allowed_actions", [])
    logger.info(f"Allowed actions for service level '{service_level}': {allowed_actions}")
    
    # Now that we have consistent naming, we can directly check if the action is allowed
    is_allowed = action in allowed_actions
    logger.info(f"Action '{action}' is allowed for service level '{service_level}': {is_allowed}")
    return is_allowed

def process_request(customer_id: str, message_data: Dict[str, Any], connection_id: str = "") -> Dict[str, Any]:
    """
    Process a user request and generate a response.
    
    Args:
        customer_id: The customer ID
        message_data: The message data containing the user input and other metadata
        connection_id: Optional WebSocket connection ID
        
    Returns:
        Response data
    """
    logger.info(f"Processing request for customer {customer_id}")
    
    # Extract user input from message data
    if isinstance(message_data, dict):
        user_input = message_data.get('message', '')
        # Extract additional metadata if needed
        metadata = message_data.get('metadata', {})
    else:
        user_input = str(message_data)
        metadata = {}
    
    if not user_input:
        logger.warning(f"Empty user input for customer {customer_id}")
        return {
            "success": False,
            "message": "Please provide a message",
            "request_type": "unknown"
        }
    
    # Get customer information
    customer = get_customer(customer_id)
    if not customer:
        logger.error(f"Customer not found: {customer_id}")
        return {
            "success": False,
            "message": f"Customer with ID {customer_id} not found"
        }
    
    # Get service level permissions
    service_level = customer.service_level
    permissions = get_service_level_permissions(service_level)
    device = customer.get_device()
    
    # Step 1: Analyze the request to determine the type and parameters
    # Use the new analyze_request function from anthropic_service.py
    request_analysis = analyze_request(user_input)
    request_type = request_analysis.get("request_type")
    
    # Build initial context for action execution
    context = {
        "customer": customer,
        "request_type": request_type,
        "service_level": service_level,
        "permissions": permissions,
        "device": device,
        "action_executed": False,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata,
        "user_input": user_input
    }
    
    # Step 2: Prepare action parameters based on request type
    if request_type == "device_power":
        # Determine if turning on or off
        turn_on = any(keyword in user_input.lower() for keyword in ["on", "start", "activate"])
        turn_off = any(keyword in user_input.lower() for keyword in ["off", "stop", "deactivate"])
        
        new_state = "on" if turn_on else "off" if turn_off else None
        
        if new_state:
            context["power_state"] = new_state
        else:
            context["error"] = "Could not determine whether to turn the device on or off"
    
    elif request_type == "volume_control":
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
            context["volume_change"] = {
                "previous": current_volume,
                "new": new_volume
            }
        else:
            context["error"] = "Could not determine how to change the volume"
    
    elif request_type == "song_changes":
        # Determine song action
        next_song = any(keyword in user_input.lower() for keyword in ["next", "skip", "forward"])
        previous_song = any(keyword in user_input.lower() for keyword in ["previous", "back", "backward"])
        
        action = "next" if next_song else "previous" if previous_song else "change"
        context["song_action"] = action
    
    # Step 3: Execute the action if a request type was identified
    if request_type and not context.get("error"):
        # Get the required action for this request type
        required_action = request_analysis.get("required_actions", [])[0] if request_type else None
        
        if required_action:
            # Check if the action is allowed for the customer's service level
            if is_action_allowed(service_level, required_action):
                # Execute the action and update the context
                context = execute_action(required_action, device, context)
                context["action_allowed"] = True
            else:
                # Action is not allowed for this service level
                context["error"] = f"This action is not allowed with your current service level"
                context["action_allowed"] = False
    
    # Step 4: Generate response based on the updated context
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
    
    # Return success response
    return {
        "success": True,
        "message": response_text,
        "request_type": request_type,
        "action_executed": context.get("action_executed", False),
        "timestamp": context["timestamp"]
    }

def execute_action(action: str, device: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an action on a device.
    
    Args:
        action: The action to execute
        device: The device to execute the action on
        context: The context containing action parameters
        
    Returns:
        Updated context with action execution results
    """
    logger.info(f"Executing action: {action}")
    
    if action == "device_status":
        # Get device status
        context["device_info"] = {
            "power": device.get("state", "unknown"),
            "volume": device.get("volume", 50),
            "location": device.get("location", "unknown")
        }
        context["action_executed"] = True
        
    elif action == "device_power":
        # Change device power state
        new_state = context.get("power_state")
        if new_state:
            # Update device state in DynamoDB
            device_id = device.get("id")
            if device_id:
                success = update_device_state(device_id, {"state": new_state})
                if success:
                    context["device_state"] = new_state
                    context["action_executed"] = True
                else:
                    context["error"] = f"Failed to update device state to {new_state}"
            else:
                context["error"] = "Device ID not found"
        else:
            context["error"] = "No power state specified"
            
    elif action == "volume_control":
        # Change device volume
        volume_change = context.get("volume_change")
        if volume_change:
            new_volume = volume_change.get("new")
            device_id = device.get("id")
            if device_id:
                success = update_device_state(device_id, {"volume": new_volume})
                if success:
                    context["action_executed"] = True
                else:
                    context["error"] = f"Failed to update device volume to {new_volume}"
            else:
                context["error"] = "Device ID not found"
        else:
            context["error"] = "No volume change specified"
            
    elif action == "song_changes":
        # Change song
        song_action = context.get("song_action")
        if song_action:
            # In a real implementation, this would interact with a music service
            # For now, we'll just simulate a successful song change
            context["song_change"] = {
                "action": song_action,
                "previous": "Unknown Song",
                "new": "New Song"
            }
            context["action_executed"] = True
        else:
            context["error"] = "No song action specified"
    
    else:
        context["error"] = f"Unknown action: {action}"
    
    return context

def update_device_state(device_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update the state of a device.
    
    Args:
        device_id: The ID of the device to update
        updates: The updates to apply to the device
        
    Returns:
        True if the update was successful, False otherwise
    """
    logger.info(f"Updating device {device_id} with {updates}")
    try:
        # Get the customer ID from the device ID (assuming format: customer-id-device-number)
        customer_id = device_id.split('-')[0] if '-' in device_id else None
        if not customer_id:
            logger.error(f"Invalid device ID format: {device_id}")
            return False
            
        # Import and call the update_device_state function from dynamodb_service
        from .dynamodb_service import update_device_state as db_update_device_state
        db_update_device_state(customer_id, device_id, updates)
        return True
    except Exception as e:
        logger.error(f"Error updating device state: {e}")
        return False

def generate_response(user_input: str, context: Dict[str, Any]) -> str:
    """
    Generate a response using the LLM based on the user input and context.
    
    Args:
        user_input: The user input
        context: The context containing customer, device, and other information
        
    Returns:
        The generated response
    """
    logger.info("Generating response with LLM")
    
    # Import and call the generate_response function from anthropic_service
    # with the correct parameter names
    from .anthropic_service import generate_response as anthropic_generate_response
    return anthropic_generate_response(prompt=user_input, context=context)