"""
Request processor for the Agentic Service Bot.

This module provides functions for processing user requests, analyzing them,
and generating appropriate responses based on service level permissions.

Service Levels:
- Basic: Can check device status and control device power (on/off)
- Premium: Basic + volume control
- Enterprise: Premium + song changes
"""

# Standard library imports
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local application imports
from .dynamodb_service import (
    get_customer, 
    get_service_level_permissions,
    store_message
)
from .anthropic_service import analyze_request

def is_action_allowed(service_level, action: str) -> bool:
    """
    Check if an action is allowed for a given service level.
    
    Args:
        service_level: The service level to check (can be a string or a Customer object)
        action: The action to check
        
    Returns:
        True if the action is allowed, False otherwise
    """
    logger.info(f"[ACTION_CHECK] Checking if action '{action}' is allowed for service level '{service_level}'")
    
    # Extract service level string if a Customer object was passed
    if hasattr(service_level, 'service_level'):
        original_service_level = service_level
        service_level = service_level.service_level
        logger.debug(f"[ACTION_CHECK] Extracted service level '{service_level}' from Customer object")
    
    # Handle None or empty service level
    if not service_level:
        logger.warning(f"[ACTION_CHECK] Service level is None or empty, action '{action}' is not allowed")
        return False
    
    # Basic actions that should be allowed for all service levels
    basic_actions = ["device_status", "device_power"]
    if action in basic_actions:
        logger.info(f"[ACTION_CHECK] Action '{action}' is a basic action allowed for all service levels")
        return True
    
    # Get permissions from DynamoDB
    logger.debug(f"[ACTION_CHECK] Retrieving permissions for service level '{service_level}'")
    permissions = get_service_level_permissions(service_level.lower())
    logger.info(f"[ACTION_CHECK] Retrieved permissions for service level '{service_level}': {permissions}")
    
    # Get the allowed actions for the service level
    allowed_actions = permissions.get("allowed_actions", [])
    logger.info(f"[ACTION_CHECK] Allowed actions for service level '{service_level}': {allowed_actions}")
    
    # Now that we have consistent naming, we can directly check if the action is allowed
    is_allowed = action in allowed_actions
    logger.info(f"[ACTION_CHECK] Action '{action}' is {'allowed' if is_allowed else 'NOT allowed'} for service level '{service_level}'")
    return is_allowed

def process_request(customer_id: str, message_data: Dict[str, Any], connection_id: str = "") -> Dict[str, Any]:
    """
    Process a user request and generate an appropriate response.
    
    Args:
        customer_id: The ID of the customer making the request
        message_data: Dictionary containing message data
        connection_id: Optional WebSocket connection ID
        
    Returns:
        Dictionary containing the response message and context
    """
    context = {
        "timestamp": datetime.utcnow().isoformat(),
        "action_executed": False
    }
    
    try:
        # Extract message from the request data
        user_input = message_data.get("message", "").strip()
        if not user_input:
            return {
                "error": "No message content provided",
                "action_executed": False,
                "timestamp": context["timestamp"]
            }
        
        # Get conversation ID from message data or generate a new one
        conversation_id = message_data.get("conversationId") or str(uuid.uuid4())
        context["conversation_id"] = conversation_id
        
        # Get customer data
        customer = get_customer(customer_id)
        if not customer:
            return {
                "error": "Customer not found in our system. Please verify your customer ID.",
                "action_executed": False,
                "timestamp": context["timestamp"],
                "conversation_id": conversation_id
            }
        
        # Get customer's service level
        service_level = customer.service_level
        logger.info(f"[REQUEST_PROCESS] Customer service level: {service_level}")
        
        # Get device data
        device = customer.get_device()
        if not device:
            error_msg = "No devices found for your account. Please register a device first."
            logger.warning(f"[REQUEST_PROCESS] {error_msg}")
            return {
                "message": error_msg,
                "action_executed": False,
                "error": error_msg,
                "timestamp": context["timestamp"]
            }
        
        # Get the analysis result from Anthropic
        analysis_result = analyze_request(user_input)
        logger.info(f"Analysis result: {json.dumps(analysis_result, indent=2)}")
        
        if not analysis_result:
            error_msg = "Could not determine what you'd like me to do. Please try rephrasing your request."
            logger.warning(f"[REQUEST_PROCESS] {error_msg}")
            return {
                "message": error_msg,
                "action_executed": False,
                "error": error_msg,
                "timestamp": context["timestamp"]
            }
        
        # Update context with analysis results and ensure customer_id is preserved
        context.update(analysis_result)
        # Also merge the nested context from analysis_result
        if "context" in analysis_result:
            context.update(analysis_result["context"])
        context["customer_id"] = customer_id
        
        # Extract request type and required actions
        request_type = analysis_result.get("primary_action")
        required_actions = analysis_result.get("all_actions", [])
        
        if not request_type:
            message = "I'm not sure what you'd like me to do. Could you please rephrase your request?"
            logger.warning(f"[REQUEST_PROCESS] No request type identified")
            return {
                "message": message,
                "action_executed": False,
                "timestamp": context["timestamp"]
            }
        
        if not required_actions:
            message = "No actions required for this request"
            logger.warning(f"[REQUEST_PROCESS] {message}")
            return {
                "message": message,
                "action_executed": False,
                "timestamp": context["timestamp"]
            }
        
        # Check if action is allowed for service level
        action = required_actions[0]
        if not is_action_allowed(service_level, action):
            # Generate appropriate upgrade suggestion message
            if service_level == "basic":
                if action == "volume_control":
                    message = "Volume control is not available with your basic service plan. Please upgrade to our premium tier to control your device's volume."
                elif action == "song_changes":
                    message = "Song control is not available with your basic service plan. Please upgrade to our enterprise tier to control music playback."
            elif service_level == "premium":
                if action == "song_changes":
                    message = "Song control is only available with our enterprise service plan. Please upgrade to access this feature."
            else:
                message = f"Action {action} is not allowed for your service level"
            
            logger.warning(f"[REQUEST_PROCESS] {message}")
            return {
                "message": message,
                "action_executed": False,
                "request_type": request_type,
                "timestamp": context["timestamp"]
            }
        
        # For device status requests, check if device is off
        if request_type == "device_status":
            device_type = device.get("type", "device").lower()
            location = device.get("location", "unknown").replace("_", " ")
            if device.get("power") == "off":
                message = f"Your {device_type} in the {location} is currently off"
                return {
                    "message": message,
                    "action_executed": True,
                    "device_info": device,
                    "timestamp": context["timestamp"]
                }
        
        # For power control requests, ensure power state is specified
        if request_type == "device_power":
            power_state = context.get("power_state")
            if not power_state:
                message = "I couldn't determine if you want to turn the device on or off. Please specify."
                return {
                    "message": message,
                    "action_executed": False,
                    "timestamp": context["timestamp"]
                }
        
        # Execute the action
        try:
            action_result = execute_action(action, device, context)
            if action_result.get("error"):
                return {
                    "message": action_result["error"],
                    "action_executed": False,
                    "timestamp": context["timestamp"]
                }
            
            context.update(action_result)
            context["action_executed"] = True
            logger.info(f"[REQUEST_PROCESS] Action executed successfully: {action_result}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[REQUEST_PROCESS] Error executing action: {error_msg}")
            return {
                "message": error_msg,
                "action_executed": False,
                "timestamp": context["timestamp"]
            }
        
        # Generate response message
        response_message = generate_response(user_input, context)
        
        # Store the message
        try:
            store_message(
                conversation_id=conversation_id,
                customer_id=customer_id,
                message=user_input,
                sender="user",
                request_type=request_type,
                actions_allowed=context.get("action_executed", False)
            )
            # Store the bot's response
            store_message(
                conversation_id=conversation_id,
                customer_id=customer_id,
                message=response_message,
                sender="bot",
                request_type=request_type,
                actions_allowed=context.get("action_executed", False)
            )
        except Exception as e:
            logger.error(f"[REQUEST_PROCESS] Error storing message: {str(e)}")
        
        # Return the response
        return {
            "message": response_message,
            "action_executed": context.get("action_executed", False),
            "timestamp": context.get("timestamp"),
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(f"[REQUEST_PROCESS] {error_msg}")
        return {
            "message": error_msg,
            "action_executed": False,
            "timestamp": context["timestamp"],
            "conversation_id": context.get("conversation_id", str(uuid.uuid4()))
        }

def execute_action(action: str, device: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the specified action on the device.
    
    Args:
        action: The action to execute (e.g., device_status, device_power, volume_control)
        device: Dictionary containing device information
        context: Dictionary containing request context and parameters
        
    Returns:
        Dictionary containing the action execution results
    """
    logger.info(f"[ACTION_EXEC] Executing action: {action}")
    
    # Ensure we have a customer ID
    customer_id = context.get("customer_id")
    if not customer_id:
        error_msg = "Customer ID not found in context"
        logger.error(f"[ACTION_EXEC] {error_msg}")
        return {"error": error_msg}
    
    # Get device ID
    device_id = device.get("id")
    if not device_id:
        error_msg = "Device ID not found"
        logger.error(f"[ACTION_EXEC] {error_msg}")
        return {"error": error_msg}
    
    if action == "device_status":
        # Get current device state
        device_info = {
            "power": device.get("power", "off"),
            "volume": device.get("volume", 50),
            "location": device.get("location", "unknown"),
            "current_song": device.get("current_song", "No song playing")
        }
        logger.info(f"[ACTION_EXEC] Retrieved device status: {device_info}")
        return {"device_info": device_info}
    
    elif action == "device_power":
        # Change device power state
        new_state = context.get("power_state")
        if not new_state:
            error_msg = "No power state specified"
            logger.warning(f"[ACTION_EXEC] {error_msg}")
            return {"error": error_msg}
        
        logger.info(f"[ACTION_EXEC] Updating device {device_id} power state to {new_state}")
        success = update_device_state(customer_id, device_id, {"power": new_state})
        
        if success:
            return {
                "action_executed": True,
                "power_state": new_state
            }
        else:
            error_msg = f"Failed to update device power state to {new_state}"
            logger.error(f"[ACTION_EXEC] {error_msg}")
            return {"error": error_msg}
    
    elif action == "volume_control":
        # Change device volume
        volume_change = context.get("volume_change")
        if not volume_change:
            error_msg = "No volume change specified"
            logger.warning(f"[ACTION_EXEC] {error_msg}")
            return {"error": error_msg}
        
        # Check if device is powered on
        if device.get("power") != "on":
            error_msg = "Cannot change volume when device is powered off"
            logger.warning(f"[ACTION_EXEC] {error_msg}")
            return {"error": error_msg}
        
        # Get current volume as previous volume
        previous_volume = device.get("volume", 50)  # Default to 50 if not set
        
        # Determine new volume based on direction and amount or specific level
        if "new" in volume_change:
            new_volume = volume_change["new"]
        else:
            # Use amount if specified, otherwise default to 10
            amount = volume_change.get("amount", 10)
            direction = volume_change.get("direction", "up")
            
            if direction == "up":
                new_volume = previous_volume + amount
            else:
                new_volume = previous_volume - amount
        
        # Ensure volume is within bounds
        new_volume = max(0, min(100, new_volume))
        logger.info(f"[ACTION_EXEC] Updating device {device_id} volume from {previous_volume} to {new_volume}")
        
        success = update_device_state(customer_id, device_id, {"volume": new_volume})
        if success:
            return {
                "action_executed": True,
                "volume_change": {
                    "previous": previous_volume,
                    "new": new_volume
                }
            }
        else:
            error_msg = f"Failed to update device volume to {new_volume}"
            logger.error(f"[ACTION_EXEC] {error_msg}")
            return {"error": error_msg}
    
    elif action == "song_changes":
        # Change song
        song_action = context.get("song_action")
        if not song_action:
            error_msg = "No song action specified"
            logger.warning(f"[ACTION_EXEC] {error_msg}")
            return {"error": error_msg}
        
        # Check if device is powered on
        if device.get("power") != "on":
            error_msg = "Cannot change songs when device is powered off"
            logger.warning(f"[ACTION_EXEC] {error_msg}")
            return {"error": error_msg}
        
        # Get current song and playlist
        current_song = device.get("current_song", "")
        playlist = device.get("playlist", [])
        
        if not playlist:
            error_msg = "No playlist available"
            logger.warning(f"[ACTION_EXEC] {error_msg}")
            return {"error": error_msg}
        
        # Determine the new song based on the action
        current_index = playlist.index(current_song) if current_song in playlist else -1
        if song_action == "next":
            new_index = (current_index + 1) % len(playlist)
        elif song_action == "previous":
            new_index = (current_index - 1) % len(playlist)
        else:
            new_index = 0
        
        new_song = playlist[new_index]
        logger.info(f"[ACTION_EXEC] Changing song from {current_song} to {new_song}")
        
        success = update_device_state(customer_id, device_id, {"current_song": new_song})
        if success:
            return {
                "action_executed": True,
                "song_changed": True,
                "new_song": new_song,
                "previous_song": current_song
            }
        else:
            error_msg = f"Failed to update current song to {new_song}"
            logger.error(f"[ACTION_EXEC] {error_msg}")
            return {"error": error_msg}
    
    else:
        error_msg = f"Unknown action: {action}"
        logger.error(f"[ACTION_EXEC] {error_msg}")
        return {"error": error_msg}

def update_device_state(customer_id: str, device_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update the state of a device.
    
    Args:
        customer_id: The ID of the customer who owns the device
        device_id: The ID of the device to update
        updates: The updates to apply to the device
        
    Returns:
        True if the update was successful, False otherwise
    """
    logger.info(f"[DEVICE_UPDATE] Updating device {device_id} with {updates}")
    try:
        if not customer_id:
            logger.error(f"[DEVICE_UPDATE] Missing customer ID for device: {device_id}")
            return False
        
        logger.debug(f"[DEVICE_UPDATE] Using customer ID: {customer_id} for device ID: {device_id}")
            
        # Import and call the update_device_state function from dynamodb_service
        from .dynamodb_service import update_device_state as db_update_device_state
        logger.debug(f"[DEVICE_UPDATE] Calling DynamoDB service to update device state")
        result = db_update_device_state(customer_id, device_id, updates)
        
        if result:
            logger.info(f"[DEVICE_UPDATE] Successfully updated device {device_id} with {updates}")
        else:
            logger.error(f"[DEVICE_UPDATE] Failed to update device {device_id} with {updates}")
        
        return result
    except Exception as e:
        logger.error(f"[DEVICE_UPDATE] Error updating device state: {str(e)}", exc_info=True)
        return False

def generate_response(user_input: str, context: Dict[str, Any]) -> str:
    """
    Generate a response message based on the user input and action context.
    
    Args:
        user_input: The original user input
        context: Dictionary containing request context and action results
        
    Returns:
        A formatted response message
    """
    logger.info(f"[RESPONSE_GEN] Generating response for user input: '{user_input}'")
    
    # Check for errors first
    if context.get("error"):
        return context["error"]
    
    # If no action was executed, return early
    if not context.get("action_executed", False):
        return "I couldn't process your request. Please try again."
    
    request_type = context.get("primary_action")
    if not request_type:
        return "I'm not sure what you'd like me to do. Could you please rephrase your request?"
    
    # Generate response based on request type
    if request_type == "device_status":
        device_info = context.get("device_info", {})
        power_state = device_info.get("power", "unknown")
        device_type = device_info.get("type", "device").lower()
        location = device_info.get("location", "unknown").replace("_", " ")
        volume = device_info.get("volume", 0)
        current_song = device_info.get("current_song", "No song playing")
        
        response = f"Your {device_type} in the {location} is currently {power_state}"
        if power_state == "on":
            response += f", volume is at {volume}%"
            if current_song and current_song != "No song playing":
                response += f", and {current_song} is playing"
        return response
    
    elif request_type == "device_power":
        power_state = context.get("power_state", "unknown")
        return f"I've turned your device {power_state}"
    
    elif request_type == "volume_control":
        volume_change = context.get("volume_change", {})
        new_volume = volume_change.get("new", 0)
        previous_volume = volume_change.get("previous", 0)
        
        if new_volume > previous_volume:
            return f"I've increased the volume to {new_volume}%"
        elif new_volume < previous_volume:
            return f"I've decreased the volume to {new_volume}%"
        else:
            return f"The volume is already at {new_volume}%"
    
    elif request_type == "song_changes":
        if context.get("song_changed"):
            new_song = context.get("new_song", "")
            previous_song = context.get("previous_song", "")
            
            if new_song:
                if previous_song:
                    return f"I've changed the song from {previous_song} to {new_song}"
                else:
                    return f"I've changed the song to {new_song}"
            else:
                return "I've changed to the next song in your playlist"
        else:
            return "I couldn't change the song. Please try again."
    
    # Default response
    return "I've processed your request successfully"