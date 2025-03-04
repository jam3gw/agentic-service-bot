"""
Request processor for the Agentic Service Bot.

This module provides functions for processing user requests, analyzing them,
and generating appropriate responses.
"""

import time
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import DynamoDB table for storing messages
import boto3

# Local imports using absolute imports
from models.customer import Customer
from analyzers.request_analyzer import RequestAnalyzer
from services.dynamodb_service import get_customer, get_service_level_permissions, store_message
from services.anthropic_service import generate_response

# Configure logging
logger = logging.getLogger()

# Initialize DynamoDB resources
dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE'))

def is_action_allowed(customer: Customer, action: str) -> bool:
    """
    Check if an action is allowed for a customer's service level.
    
    Args:
        customer: The customer to check permissions for
        action: The action to check
        
    Returns:
        True if the action is allowed, False otherwise
    """
    permissions = get_service_level_permissions(customer.service_level)
    return action in permissions.get("allowed_actions", [])

def process_request(customer_id: str, user_input: str) -> str:
    """
    Process a user request and generate a response.
    
    Args:
        customer_id: The ID of the customer making the request
        user_input: The text of the user's request
        
    Returns:
        The generated response text
    """
    # Get customer data
    customer = get_customer(customer_id)
    if not customer:
        return "Error: Customer not found."
    
    # Identify request type
    request_type = RequestAnalyzer.identify_request_type(user_input)
    if not request_type:
        # If request type can't be determined, just have the LLM respond generically
        return generate_response(user_input, {"customer": customer})
    
    # Determine required actions for this request
    required_actions = RequestAnalyzer.get_required_actions(request_type)
    
    # Check if all required actions are allowed for this customer's service level
    all_actions_allowed = all(
        is_action_allowed(customer, action)
        for action in required_actions
    )
    
    # Extract source and destination locations if this is a relocation request
    source_location, destination_location = None, None
    if request_type == "device_relocation":
        source_location, destination_location = RequestAnalyzer.extract_locations(user_input)
    
    # Extract device groups for multi-room audio requests
    device_groups = None
    if request_type == "multi_room_setup":
        device_groups = RequestAnalyzer.extract_device_groups(user_input)
    
    # Extract routine details for custom action requests
    routine_details = None
    if request_type == "custom_routine":
        routine_details = RequestAnalyzer.extract_routine_details(user_input)
    
    # Build context for the LLM
    context = {
        "customer": customer,
        "devices": customer.devices,
        "permissions": get_service_level_permissions(customer.service_level),
        "action_allowed": all_actions_allowed,
        "request_type": request_type
    }
    
    # For relocation requests, add additional context
    if request_type == "device_relocation" and destination_location:
        context["destination"] = destination_location
        
        # Add specific explanation for relocation requests
        if all_actions_allowed:
            prompt = (
                f"Move device to {destination_location.replace('_', ' ')}. "
                f"This is allowed with {customer.service_level} service level."
            )
        else:
            prompt = (
                f"Customer wants to move device to {destination_location.replace('_', ' ')}. "
                f"Not allowed with {customer.service_level} service level. "
                f"Suggest upgrade options."
            )
    # For multi-room audio requests, add additional context
    elif request_type == "multi_room_setup" and device_groups:
        context["device_groups"] = device_groups
        
        if all_actions_allowed:
            if "all" in device_groups:
                prompt = (
                    f"Set up multi-room audio across all devices. "
                    f"Allowed with {customer.service_level} service level."
                )
            else:
                group_str = ", ".join([loc.replace("_", " ") for loc in device_groups])
                prompt = (
                    f"Set up multi-room audio in {group_str}. "
                    f"Allowed with {customer.service_level} service level."
                )
        else:
            prompt = (
                f"Multi-room audio setup requested. "
                f"Not allowed with {customer.service_level} service level. "
                f"Suggest upgrade options."
            )
    # For custom action requests, add additional context
    elif request_type == "custom_routine" and routine_details:
        context["routine"] = routine_details
        
        if all_actions_allowed:
            routine_name = routine_details["name"] or "the new routine"
            prompt = (
                f"Create custom routine '{routine_name}'. "
                f"Allowed with {customer.service_level} service level."
            )
        else:
            prompt = (
                f"Custom routine creation requested. "
                f"Not allowed with {customer.service_level} service level. "
                f"Suggest upgrade options."
            )
    else:
        # Generic prompt for other request types
        prompt = user_input
    
    # Generate and return the response
    response = generate_response(prompt, context)
    
    # Store the interaction in conversation history
    # FIX: Generate a unique conversation ID for each message to ensure they're stored separately
    # The previous implementation used the same conversation ID for both user and bot messages
    # which could cause race conditions in high-volume scenarios
    timestamp_ms = int(time.time() * 1000)
    user_conversation_id = f"conv_{customer_id}_user_{timestamp_ms}"
    bot_conversation_id = f"conv_{customer_id}_bot_{timestamp_ms}"
    
    try:
        # Store user message
        logger.info(f"Storing user message in DynamoDB for customer {customer_id}")
        user_stored = store_message(
            conversation_id=user_conversation_id,
            customer_id=customer_id,
            message=user_input,
            sender='user',
            request_type=request_type,
            actions_allowed=all_actions_allowed
        )
        if not user_stored:
            logger.error("Failed to store user message in DynamoDB")
        
        # Store bot response
        logger.info(f"Storing bot message in DynamoDB for customer {customer_id}")
        bot_stored = store_message(
            conversation_id=bot_conversation_id,
            customer_id=customer_id,
            message=response,
            sender='bot',
            request_type=request_type,
            actions_allowed=all_actions_allowed
        )
        if not bot_stored:
            logger.error("Failed to store bot message in DynamoDB")
    except Exception as e:
        logger.error(f"Error storing messages in DynamoDB: {str(e)}")
        # Continue even if message storage fails - don't impact user experience
    
    return response 