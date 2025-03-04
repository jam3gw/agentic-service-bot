"""
Request processor for the Agentic Service Bot.

This module provides functions for processing user requests, analyzing them,
and generating appropriate responses.
"""

import time
import os
import sys
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
from services.dynamodb_service import get_customer, get_service_level_permissions
from services.anthropic_service import generate_response

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
                f"The customer wants to move their device to the {destination_location.replace('_', ' ')}. "
                f"They are allowed to do this with their {customer.service_level} service level. "
                f"Please confirm the relocation and provide any helpful information."
            )
        else:
            prompt = (
                f"The customer wants to move their device to the {destination_location.replace('_', ' ')}, "
                f"but their {customer.service_level} service level doesn't allow device relocation. "
                f"Politely explain this limitation and offer to connect them with customer support to upgrade."
            )
    else:
        # Generic prompt for other request types
        prompt = user_input
    
    # Generate and return the response
    response = generate_response(prompt, context)
    
    # Store the interaction in conversation history
    conversation_id = f"conv_{customer_id}_{int(time.time() * 1000)}"
    timestamp = datetime.utcnow().isoformat()
    
    # Store user message
    messages_table.put_item(Item={
        'conversationId': conversation_id,
        'timestamp': timestamp,
        'userId': customer_id,
        'message': user_input,
        'sender': 'user',
        'request_type': request_type,
        'actions_allowed': all_actions_allowed
    })
    
    # Store bot response
    messages_table.put_item(Item={
        'conversationId': conversation_id,
        'timestamp': datetime.utcnow().isoformat(),
        'userId': customer_id,
        'message': response,
        'sender': 'bot',
        'request_type': request_type,
        'actions_allowed': all_actions_allowed
    })
    
    return response 