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
            max_tokens=1000
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
        return "You are a helpful AI assistant for a smart home device company."
    
    # Start with base prompt
    system_prompt = "You are an AI assistant for a smart home device company. "
    
    # Add customer info if available
    if "customer" in context:
        customer = context["customer"]
        system_prompt += f"You are speaking with {customer.name}, who has a {customer.service_level} service level. "
    
    # Add device info if available
    if "devices" in context and context["devices"]:
        devices_desc = ", ".join([f"{d['type']} in the {d['location'].replace('_', ' ')}" for d in context["devices"]])
        system_prompt += f"They have the following devices: {devices_desc}. "
    
    # Add service level permissions
    if "permissions" in context:
        allowed = ", ".join(context["permissions"]["allowed_actions"])
        system_prompt += f"Their service level permits these actions: {allowed}. "
    
    # Add specific instructions based on context
    if "action_allowed" in context:
        if context["action_allowed"]:
            system_prompt += "The requested action IS permitted for this customer's service level. Respond helpfully and proceed with the request. "
        else:
            system_prompt += (
                "The requested action is NOT permitted for this customer's service level. "
                "Politely explain this limitation and offer to connect them with customer support to upgrade their service. "
                "Do not explain specific pricing or offer workarounds."
            )
    
    return system_prompt 