"""
Anthropic service for the Agentic Service Bot.

This module provides functions for interacting with Anthropic's Claude API
to generate responses to user requests.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

# Add the parent directory to sys.path to enable absolute imports if needed
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Configure logging
logger = logging.getLogger()

# Set default environment variables for local development
def set_default_env_vars():
    """Set default environment variables for local development if they're not already set."""
    defaults = {
        'ANTHROPIC_MODEL': 'claude-3-opus-20240229',
    }
    
    for key, value in defaults.items():
        if not os.environ.get(key):
            logger.info(f"Setting default environment variable {key}={value}")
            os.environ[key] = value

# Set default environment variables
set_default_env_vars()

# Check if ANTHROPIC_API_KEY is set
if not os.environ.get('ANTHROPIC_API_KEY'):
    logger.warning("ANTHROPIC_API_KEY environment variable is not set. Using mock responses for local development.")

# Initialize Anthropic client if API key is available
try:
    import anthropic
    if os.environ.get('ANTHROPIC_API_KEY'):
        anthropic_client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY')
        )
    else:
        anthropic_client = None
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL')
except ImportError:
    logger.warning("anthropic package not installed. Using mock responses.")
    anthropic_client = None
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL')

def generate_response(prompt: str, context: Dict[str, Any] = None) -> str:
    """
    Generate a response using Anthropic's Claude API.
    
    Args:
        prompt: The user's request text
        context: Additional context for the request (customer, devices, permissions, etc.)
        
    Returns:
        The generated response text
    """
    system_prompt = build_system_prompt(context)
    
    # If Anthropic client is not available, return a mock response
    if not anthropic_client:
        logger.info("Using mock response for local development")
        return f"This is a mock response for local development. Your prompt was: '{prompt}'"
    
    try:
        message = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        return "I apologize, but I'm having trouble processing your request right now."

def build_system_prompt(context: Dict[str, Any] = None) -> str:
    """
    Build a system prompt based on context.
    
    Args:
        context: Additional context for the request (customer, devices, permissions, etc.)
        
    Returns:
        The system prompt for the Anthropic API
    """
    if not context:
        return "You are a helpful AI assistant for a smart home device company. Keep responses brief and to the point."
    
    # Start with base prompt
    system_prompt = "You are an AI assistant for a smart home device company. Keep all responses brief and concise. "
    
    # Add customer info if available
    if "customer" in context:
        customer = context["customer"]
        system_prompt += f"Customer: {customer.name}, {customer.service_level} service. "
    
    # Add device info if available
    if "devices" in context and context["devices"]:
        devices_desc = ", ".join([f"{d['type']} ({d['location'].replace('_', ' ')})" for d in context["devices"]])
        system_prompt += f"Devices: {devices_desc}. "
    
    # Add service level permissions
    if "permissions" in context:
        allowed = ", ".join(context["permissions"]["allowed_actions"])
        system_prompt += f"Allowed actions: {allowed}. "
    
    # Add specific instructions based on context
    if "action_allowed" in context:
        if context["action_allowed"]:
            system_prompt += "Request IS permitted. Respond helpfully and briefly. "
        else:
            system_prompt += "Request NOT permitted. Politely explain and suggest upgrade. "
    
    # Add multi-room audio context if available
    if "device_groups" in context and context["request_type"] == "multi_room_setup":
        if "all" in context["device_groups"]:
            system_prompt += "Setup: multi-room audio (all devices). "
        else:
            group_str = ", ".join([loc.replace("_", " ") for loc in context["device_groups"]])
            system_prompt += f"Setup: multi-room audio ({group_str}). "
    
    # Add custom routine context if available
    if "routine" in context and context["request_type"] == "custom_routine":
        routine = context["routine"]
        routine_name = routine["name"] or "unnamed"
        system_prompt += f"Routine: '{routine_name}'. "
        
        if routine["trigger"] and routine["trigger"] == "time" and routine["trigger_value"]:
            system_prompt += f"Trigger: {routine['trigger_value']}. "
        
        if routine["actions"]:
            actions_str = ", ".join(routine["actions"])
            system_prompt += f"Actions: {actions_str}. "
    
    return system_prompt 