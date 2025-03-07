"""
Anthropic service for the Agentic Service Bot.

This module provides functions for interacting with Anthropic's Claude API
to generate responses to user requests.
"""

# Standard library imports
import os
import logging
import sys
import json
import re
from typing import Dict, Any, Optional, List, Union

# Third-party imports
import anthropic

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define empty dictionaries for response examples
ALLOWED_ACTION_EXAMPLES = {}
DISALLOWED_ACTION_EXAMPLES = {}
UPGRADE_INFORMATION_EXAMPLES = {}

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
    if os.environ.get('ANTHROPIC_API_KEY'):
        anthropic_client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY')
        )
    else:
        anthropic_client = None
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-opus-20240229')
except ImportError:
    logger.warning("anthropic package not installed. Using mock responses.")
    anthropic_client = None
    ANTHROPIC_MODEL = 'claude-3-opus-20240229'

def analyze_request(user_input: str) -> Dict[str, Any]:
    """
    Use Claude to analyze a user request and determine which action(s) it maps to.
    
    Args:
        user_input: The user's request text
        
    Returns:
        A dictionary containing the analysis results, including:
        - request_type: The primary action the request maps to, or None
        - required_actions: List of all actions required to fulfill the request
        - context: Additional context extracted from the request
        - ambiguous: Boolean indicating if the request could map to multiple actions
        - out_of_scope: Boolean indicating if the request doesn't map to any actions
    """
    system_prompt = """You are an AI assistant analyzing user requests for a smart home device system.
    
AVAILABLE ACTIONS:
- device_status: Check if devices are online/offline and view basic status info
- device_power: Turn devices on/off
- volume_control: Adjust device volume up/down
- song_changes: Change songs (next, previous, or random)

YOUR TASK:
Analyze the user's request and determine which action(s) it maps to. If it maps to multiple actions, list them in order of execution. If it doesn't map to any action, indicate that it's out of scope.

RESPONSE FORMAT:
Respond with a JSON object containing:
- primary_action: The main action the request maps to, or null if none
- all_actions: Array of all actions required to fulfill the request, in order of execution
- context: Object containing relevant details extracted from the request (e.g., power_state, volume_direction)
- ambiguous: Boolean indicating if the request could map to multiple actions and needs clarification
- out_of_scope: Boolean indicating if the request doesn't map to any available actions

EXAMPLES:
User: "Turn on my speaker"
{
  "primary_action": "device_power",
  "all_actions": ["device_power"],
  "context": {"power_state": "on"},
  "ambiguous": false,
  "out_of_scope": false
}

User: "Turn up the volume and play the next song"
{
  "primary_action": "volume_control",
  "all_actions": ["volume_control", "song_changes"],
  "context": {"volume_direction": "up", "song_action": "next"},
  "ambiguous": false,
  "out_of_scope": false
}

User: "What's the weather like today?"
{
  "primary_action": null,
  "all_actions": [],
  "context": {},
  "ambiguous": false,
  "out_of_scope": true
}
"""
    
    # If Anthropic client is not available, return a mock response
    if not anthropic_client:
        logger.info("Using mock response for local development")
        return {
            "request_type": "device_status" if "status" in user_input.lower() else "device_power",
            "required_actions": ["device_status"] if "status" in user_input.lower() else ["device_power"],
            "context": {},
            "ambiguous": False,
            "out_of_scope": False
        }
    
    try:
        message = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_input}
            ],
            max_tokens=500,
            temperature=0.0  # Use 0 temperature for consistent, deterministic responses
        )
        
        # Parse the JSON response
        response_text = message.content[0].text
        
        # Extract JSON from the response (in case Claude adds any explanatory text)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            analysis = json.loads(json_str)
        else:
            # Fallback if no JSON is found
            analysis = {
                "primary_action": None,
                "all_actions": [],
                "context": {},
                "ambiguous": False,
                "out_of_scope": True
            }
        
        # Convert to our existing format for compatibility
        result = {
            "request_type": analysis.get("primary_action"),
            "required_actions": analysis.get("all_actions", []),
            "context": analysis.get("context", {}),
            "ambiguous": analysis.get("ambiguous", False),
            "out_of_scope": analysis.get("out_of_scope", False)
        }
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing request with Claude: {e}")
        # Fallback to a safe default
        return {
            "request_type": None,
            "required_actions": [],
            "context": {},
            "ambiguous": False,
            "out_of_scope": True
        }

def generate_response(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a response using Anthropic's Claude API.
    
    Args:
        prompt: The user's request text
        context: Additional context for the request (customer, devices, permissions, etc.)
        
    Returns:
        The generated response text
    """
    system_prompt = build_system_prompt(context or {})
    
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

def build_system_prompt(context: Dict[str, Any]) -> str:
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
1. Always respect service level permissions and NEVER suggest actions that are not permitted for the customer's service level.
2. For ALLOWED actions that have been executed, be confident and direct - DO NOT apologize or express uncertainty. Respond based on the action that was actually executed by the system.
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

RESPONSE GUIDELINES:
- If an action was successfully executed (indicated in the context), respond by confirming what was done (e.g., "I've turned on your living room speaker" or "I've increased the volume to 60%").
- If an action was attempted but failed, explain why it failed and what the user can do instead.
- If a user asks about device status, respond with the current status information provided in the context.
- NEVER provide manual instructions for how to physically operate devices - the system handles all actions automatically.
"""
    
    # Add customer info if available
    if "customer" in context:
        customer = context["customer"]
        system_prompt += f"\nCUSTOMER INFORMATION:\nName: {customer.name}\nService Level: {customer.service_level.capitalize()}\n"
    
    # Add device info if available - always include the section header even if no devices
    system_prompt += "\nDEVICE INFORMATION:\n"
    if "customer" in context and hasattr(context["customer"], "device") and context["customer"].device:
        device = context["customer"].device
        location = device.get('location', '').replace('_', ' ')
        device_info = f"- {device.get('type', 'unknown')} in the {location}"
        
        # Add volume information if available
        if 'volume' in device:
            device_info += f" (volume: {device['volume']}%)"
            
        system_prompt += f"{device_info}\n"
    else:
        system_prompt += "No device currently registered.\n"
    
    # Add service level permissions with clear explanations
    if "permissions" in context and "allowed_actions" in context["permissions"]:
        allowed_actions = context["permissions"]["allowed_actions"]
        system_prompt += "\nALLOWED ACTIONS WITH CURRENT SERVICE LEVEL:\n"
        
        # Map action names to user-friendly descriptions
        # Updated to match exactly with the service level permissions
        action_descriptions = {
            "device_status": "Check if devices are online/offline and view basic status info",
            "device_power": "Turn devices on/off",
            "volume_control": "Adjust device volume up/down", 
            "song_changes": "Change songs (next, previous, or random)"
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
                    system_prompt += "Premium tier adds: volume control\n"
                if "enterprise" in upgrade_options:
                    system_prompt += "Enterprise tier adds: song changes\n"
    
    # Add information about executed actions
    if "action_executed" in context and context["action_executed"]:
        system_prompt += "\nACTION EXECUTION INFORMATION:\n"
        
        if "device_info" in context:
            device_info = context["device_info"]
            power_state = device_info.get("power", "unknown")
            volume = device_info.get("volume", 50)
            location = device_info.get("location", "unknown")
            
            system_prompt += f"- SYSTEM ACTION: Retrieved device status for {location} speaker\n"
            system_prompt += f"- Current power state: {power_state}\n"
            system_prompt += f"- Current volume: {volume}%\n"
            system_prompt += f"- Respond with this current status information\n"
        
        elif "device_state" in context:
            device_state = context["device_state"]
            device = context.get("device", {})
            device_type = device.get("type", "device")
            location = device.get("location", "").replace("_", " ")
            
            system_prompt += f"- SYSTEM ACTION: Changed power state of {device_type} in {location} to {device_state}\n"
            system_prompt += f"- The device is now {device_state}\n"
            system_prompt += f"- Confirm this action was completed in your response\n"
        
        elif "volume_change" in context:
            volume_info = context["volume_change"]
            previous_volume = volume_info.get("previous", 0)
            new_volume = volume_info.get("new", 0)
            device = context.get("device", {})
            device_type = device.get("type", "device")
            location = device.get("location", "").replace("_", " ")
            
            system_prompt += f"- SYSTEM ACTION: Changed volume of {device_type} in {location} from {previous_volume}% to {new_volume}%\n"
            system_prompt += f"- The volume is now set to {new_volume}%\n"
            system_prompt += f"- Confirm this action was completed in your response\n"
        
        elif "song_change" in context:
            song_info = context["song_change"]
            action = song_info.get("action", "changed")
            device = context.get("device", {})
            device_type = device.get("type", "device")
            location = device.get("location", "").replace("_", " ")
            
            system_prompt += f"- SYSTEM ACTION: {action.capitalize()} song on {device_type} in {location}\n"
            system_prompt += f"- The song has been {action}ed\n"
            system_prompt += f"- Confirm this action was completed in your response\n"
        
        # Add more action execution information for other action types
    
    # If there was an error executing the action
    elif "error" in context:
        system_prompt += f"\nACTION EXECUTION ERROR:\n"
        system_prompt += f"- ERROR: {context['error']}\n"
        
        # Add information about the attempted action
        if "request_type" in context:
            request_type = context["request_type"]
            system_prompt += f"- ATTEMPTED ACTION: {request_type.replace('_', ' ')}\n"
            
            # Add service level information if available
            if "customer" in context and hasattr(context["customer"], "service_level"):
                service_level = context["customer"].service_level
                system_prompt += f"- Customer's current service level: {service_level}\n"
                
                # Add upgrade information if available
                if "permissions" in context and "upgrade_options" in context["permissions"]:
                    upgrade_options = context["permissions"]["upgrade_options"]
                    if upgrade_options:
                        next_tier = upgrade_options[0]
                        system_prompt += f"- Next available tier: {next_tier}\n"
        
        system_prompt += "- Explain the error clearly and suggest what the user can do instead\n"
        system_prompt += "- If the error is due to service level restrictions, mention the tier that would allow this action\n"
    
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