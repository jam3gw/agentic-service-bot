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

# Import response examples
try:
    from response_examples import (
        ALLOWED_ACTION_EXAMPLES,
        DISALLOWED_ACTION_EXAMPLES,
        UPGRADE_INFORMATION_EXAMPLES
    )
except ImportError:
    # Define empty dictionaries if import fails
    ALLOWED_ACTION_EXAMPLES = {}
    DISALLOWED_ACTION_EXAMPLES = {}
    UPGRADE_INFORMATION_EXAMPLES = {}

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
            max_tokens=500,
            temperature=0.5
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
    system_prompt = """You are an AI assistant for a smart home device company. Keep all responses brief and concise. 

IMPORTANT GUIDELINES FOR SERVICE LEVEL COMMUNICATION:
1. Always respect service level permissions and NEVER provide instructions for actions that are not permitted for the customer's service level.
2. For ALLOWED actions, be confident and direct - DO NOT apologize or express uncertainty. Provide clear, actionable instructions.
3. For DISALLOWED actions, clearly explain the limitation with the following structure:
   - Acknowledge the request
   - Clearly state this feature is not available with their current service level
   - Briefly mention the specific tier that offers this feature
   - Offer an alternative action they CAN perform with their current service level

COMMUNICATION STYLE:
- Be conversational but professional
- Use simple, clear language
- Focus on what the customer CAN do rather than dwelling on limitations
- When mentioning upgrades, be informative rather than sales-focused
"""
    
    # Add customer info if available
    if "customer" in context:
        customer = context["customer"]
        system_prompt += f"\nCUSTOMER INFORMATION:\nName: {customer.name}\nService Level: {customer.service_level.capitalize()}\n"
    
    # Add device info if available - always include the section header even if no devices
    system_prompt += "\nDEVICE INFORMATION:\n"
    if "customer" in context and hasattr(context["customer"], "devices") and context["customer"].devices:
        for device in context["customer"].devices:
            location = device['location'].replace('_', ' ')
            device_info = f"- {device['type']} in the {location}"
            
            # Add volume information if available
            if 'volume' in device:
                device_info += f" (volume: {device['volume']}%)"
                
            system_prompt += f"{device_info}\n"
    else:
        system_prompt += "No devices currently registered.\n"
    
    # Add service level permissions with clear explanations
    if "permissions" in context and "allowed_actions" in context["permissions"]:
        allowed_actions = context["permissions"]["allowed_actions"]
        system_prompt += "\nALLOWED ACTIONS WITH CURRENT SERVICE LEVEL:\n"
        
        # Map action names to user-friendly descriptions
        action_descriptions = {
            "status_check": "Check if devices are online, offline, or experiencing issues",
            "volume_control": "Adjust the volume of audio devices",
            "device_info": "Get information about devices",
            "device_relocation": "Move devices from one location to another",
            "lighting_control": "Control smart lights (on/off, brightness, color)",
            "music_services": "Play music on devices",
            "multi_room_audio": "Synchronize audio across multiple devices",
            "custom_actions": "Create and execute custom routines or automations",
            "temperature_control": "Control thermostats and temperature settings"
        }
        
        # Add each allowed action with its description
        for action in allowed_actions:
            description = action_descriptions.get(action, action.replace("_", " "))
            system_prompt += f"- {description}\n"
        
        # If context includes service level and upgrade options, add information about upgrade path
        if "customer" in context and "upgrade_options" in context["permissions"]:
            service_level = context["customer"].service_level
            upgrade_options = context["permissions"]["upgrade_options"]
            
            if upgrade_options:
                system_prompt += "\nUPGRADE INFORMATION:\n"
                if "premium" in upgrade_options:
                    system_prompt += "Premium tier adds: device relocation, lighting control, and music services\n"
                if "enterprise" in upgrade_options:
                    system_prompt += "Enterprise tier adds: multi-room audio, custom actions, and advanced temperature control\n"
    
    # Add information about executed actions
    if "action_executed" in context and context["action_executed"]:
        system_prompt += "\nACTION EXECUTION INFORMATION:\n"
        
        if "volume_change" in context:
            volume_info = context["volume_change"]
            device = volume_info["device"]
            device_type = device["type"]
            location = device["location"].replace("_", " ")
            previous_volume = volume_info["previous_volume"]
            new_volume = volume_info["new_volume"]
            
            system_prompt += f"- Volume change executed: {device_type} in {location} volume changed from {previous_volume}% to {new_volume}%\n"
            system_prompt += f"- Make sure to reference the new volume ({new_volume}%) in your response\n"
        
        elif "relocation" in context:
            relocation_info = context["relocation"]
            device = relocation_info["device"]
            device_type = device["type"]
            previous_location = relocation_info["previous_location"].replace("_", " ")
            new_location = relocation_info["new_location"].replace("_", " ")
            
            system_prompt += f"- Device relocation executed: {device_type} moved from {previous_location} to {new_location}\n"
            system_prompt += f"- Make sure to reference the new location ({new_location}) in your response\n"
        
        # Add more action execution information for other action types
    
    # If there was an error executing the action
    elif "error" in context:
        system_prompt += f"\nACTION EXECUTION ERROR:\n- {context['error']}\n"
        system_prompt += "- Acknowledge the error in your response and suggest troubleshooting steps\n"
    
    # Add specific instructions based on context
    if "action_allowed" in context:
        if context["action_allowed"]:
            system_prompt += "\nREQUEST IS PERMITTED. Respond helpfully with clear, actionable instructions. Be confident and direct.\n"
        else:
            system_prompt += "\nREQUEST IS NOT PERMITTED. Follow this structure in your response:\n1. Acknowledge their request\n2. Clearly explain this feature is not available with their current service level\n3. Briefly mention which tier offers this feature\n4. Suggest an alternative action they CAN perform\n"
    
    # Add examples of good responses based on request type and service level
    system_prompt += "\nEXAMPLES OF GOOD RESPONSES:\n"
    
    # Add examples for allowed actions
    if "request_type" in context and context.get("action_allowed", False):
        request_type = context["request_type"]
        system_prompt += "\nFor Allowed Actions:\n"
        
        if request_type in ALLOWED_ACTION_EXAMPLES:
            for i, example in enumerate(ALLOWED_ACTION_EXAMPLES[request_type]):
                if example:
                    system_prompt += f"\nExample {i+1}:\n{example}\n"
    
    # Add examples for disallowed actions
    if "request_type" in context and not context.get("action_allowed", True):
        request_type = context["request_type"]
        system_prompt += "\nFor Disallowed Actions:\n"
        
        if request_type in DISALLOWED_ACTION_EXAMPLES:
            for i, example in enumerate(DISALLOWED_ACTION_EXAMPLES[request_type]):
                if example:
                    system_prompt += f"\nExample {i+1}:\n{example}\n"
        
        # Add upgrade information examples
        if "customer" in context and "permissions" in context and "upgrade_options" in context["permissions"]:
            service_level = context["customer"].service_level
            upgrade_options = context["permissions"]["upgrade_options"]
            
            if upgrade_options and upgrade_options[0] in UPGRADE_INFORMATION_EXAMPLES:
                upgrade_tier = upgrade_options[0]
                system_prompt += "\nUpgrade Information Examples:\n"
                
                for i, example in enumerate(UPGRADE_INFORMATION_EXAMPLES[upgrade_tier]):
                    if example:
                        system_prompt += f"\nExample {i+1}:\n{example}\n"
    
    # Add multi-room audio context if available
    if "device_groups" in context and context.get("request_type") == "multi_room_audio":
        if "all" in context["device_groups"]:
            system_prompt += "\nCONTEXT: Customer is asking about multi-room audio setup for all devices.\n"
        else:
            group_str = ", ".join([loc.replace("_", " ") for loc in context["device_groups"]])
            system_prompt += f"\nCONTEXT: Customer is asking about multi-room audio setup for these locations: {group_str}.\n"
    
    # Add custom routine context if available
    if "routine" in context and context.get("request_type") == "custom_actions":
        routine = context["routine"]
        routine_name = routine.get("name", "unnamed")
        system_prompt += f"\nCONTEXT: Customer is asking about a custom routine named '{routine_name}'.\n"
        
        if "trigger" in routine and routine["trigger"] == "time" and "trigger_value" in routine:
            system_prompt += f"Trigger: {routine['trigger_value']}\n"
        
        if "actions" in routine and routine["actions"]:
            actions_str = ", ".join(routine["actions"])
            system_prompt += f"Actions: {actions_str}\n"
    
    return system_prompt 