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
from typing import Dict, Any, Optional, List, Union, cast

# Third-party imports
import anthropic
from anthropic import Anthropic

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define empty dictionaries for response examples
ALLOWED_ACTION_EXAMPLES = {}
DISALLOWED_ACTION_EXAMPLES = {}
UPGRADE_INFORMATION_EXAMPLES = {}

# Set default environment variables for local development
def set_default_env_vars():
    """Set default environment variables for local development if they're not already set."""
    defaults = {
        'ANTHROPIC_MODEL': 'claude-3-haiku-20240307',
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
    from anthropic import Anthropic
    
    # Initialize Anthropic client
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_api_key:
        anthropic_client = Anthropic(api_key=anthropic_api_key)
    else:
        logger.warning("ANTHROPIC_API_KEY not set. Using mock responses.")
        anthropic_client = None
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
except ImportError:
    logger.warning("anthropic package not installed. Using mock responses.")
    anthropic_client = None
    ANTHROPIC_MODEL = 'claude-3-haiku-20240307'

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
    logger.info("=" * 80)
    logger.info(f"Starting request analysis for input: {user_input}")
    
    system_prompt = """You are an AI assistant analyzing user requests for a smart home device system.
    
AVAILABLE ACTIONS:
- device_status: Check if devices are online/offline and view basic status info
- device_power: Turn devices on/off
- volume_control: Adjust device volume up/down
- song_changes: Change songs (next, previous, or random)

YOUR TASK:
Analyze the user's request and determine which action(s) it maps to. If it maps to multiple actions, list them in order of execution. If it doesn't map to any action, indicate that it's out of scope.

RESPONSE FORMAT:
You must respond with a valid JSON object containing:
{
  "primary_action": "string or null",
  "all_actions": ["array of strings"],
  "context": {"object with details"},
  "ambiguous": "boolean",
  "out_of_scope": "boolean"
}

EXAMPLES:
User: "Turn on my speaker"
{
  "primary_action": "device_power",
  "all_actions": ["device_power"],
  "context": {"power_state": "on"},
  "ambiguous": false,
  "out_of_scope": false
}

User: "Next song"
{
  "primary_action": "song_changes",
  "all_actions": ["song_changes"],
  "context": {"song_action": "next"},
  "ambiguous": false,
  "out_of_scope": false
}

User: "Turn up the volume"
{
  "primary_action": "volume_control",
  "all_actions": ["volume_control"],
  "context": {
    "volume_change": {
      "direction": "up",
      "amount": 10
    }
  },
  "ambiguous": false,
  "out_of_scope": false
}

User: "Set the volume to 60%"
{
  "primary_action": "volume_control",
  "all_actions": ["volume_control"],
  "context": {
    "volume_change": {
      "new": 60
    }
  },
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

IMPORTANT: Your response must be a valid JSON object. Do not include any explanatory text before or after the JSON."""

    logger.info("System Prompt:")
    logger.info("-" * 40)
    logger.info(system_prompt)
    logger.info("-" * 40)
    
    # If Anthropic client is not available, return a mock response
    if not anthropic_client:
        logger.info("Using mock response for local development")
        
        # Check if this is a device status query
        if "status" in user_input.lower():
            mock_response = "Your speaker is currently on and the volume is set to 60%."
        else:
            mock_response = f"This is a mock response for local development. Your prompt was: '{user_input}'"
            
        logger.info(f"Mock Response: {mock_response}")
        return mock_response
    
    try:
        logger.info("Sending request to Anthropic API...")
        message = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_input}
            ],
            max_tokens=500,
            temperature=0.0  # Use 0 temperature for consistent, deterministic responses
        )
        
        logger.info("Received response from Anthropic API")
        # Log the response for debugging
        logger.info("Claude response:")
        logger.info(f"Response type: {type(message)}")
        logger.info(f"Content type: {type(message.content)}")
        
        # Get the text content from the first ContentBlock
        response_text = message.content[0].text if message.content else ""
        logger.info(f"Response text: {response_text}")
        
        # Extract the JSON object from the response
        try:
            # First try to parse the entire response as JSON
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract the JSON object from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                # Clean up any potential Unicode escapes
                json_str = json_str.encode('utf-8').decode('unicode_escape')
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse extracted JSON: {e}")
                    logger.error(f"Extracted JSON string: {json_str}")
                    result = {
                        "primary_action": None,
                        "all_actions": [],
                        "context": {},
                        "ambiguous": False,
                        "out_of_scope": True
                    }
            else:
                logger.error("No JSON object found in response")
                result = {
                    "primary_action": None,
                    "all_actions": [],
                    "context": {},
                    "ambiguous": False,
                    "out_of_scope": True
                }
        
        # Ensure consistent response structure
        if not isinstance(result, dict):
            result = {
                "primary_action": None,
                "all_actions": [],
                "context": {},
                "ambiguous": False,
                "out_of_scope": True
            }
        
        # Ensure all required fields are present
        required_fields = ["primary_action", "all_actions", "context", "ambiguous", "out_of_scope"]
        for field in required_fields:
            if field not in result:
                result[field] = None if field == "primary_action" else [] if field == "all_actions" else {} if field == "context" else False
        
        logger.info("Final Result:")
        logger.info("-" * 40)
        logger.info(json.dumps(result, indent=2))
        logger.info("-" * 40)
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing request with Claude: {str(e)}", exc_info=True)
        # Fallback to a safe default
        fallback = {
            "primary_action": None,
            "all_actions": [],
            "context": {},
            "ambiguous": False,
            "out_of_scope": True
        }
        logger.info(f"Returning fallback response: {json.dumps(fallback, indent=2)}")
        return fallback

def generate_response(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a response using Anthropic's Claude API.
    
    Args:
        prompt: The user's request text
        context: Additional context for the request (customer, devices, permissions, etc.)
        
    Returns:
        The generated response text
    """
    logger.info("=" * 80)
    logger.info(f"Generating response for prompt: {prompt}")
    
    # Convert Customer object to dict before JSON serialization
    if context and "customer" in context and hasattr(context["customer"], "to_dict"):
        context = context.copy()  # Create a copy to avoid modifying the original
        context["customer"] = context["customer"].to_dict()
    
    if context:
        logger.info(f"Context: {json.dumps(context, indent=2)}")
    
    system_prompt = build_system_prompt(context or {})
    logger.info("System Prompt:")
    logger.info("-" * 40)
    logger.info(system_prompt)
    logger.info("-" * 40)
    
    # If Anthropic client is not available, return a mock response
    if not anthropic_client:
        # Check if this is a device status query
        if "status" in prompt.lower():
            mock_response = "Your speaker is currently on and the volume is set to 60%."
        else:
            mock_response = f"This is a mock response for local development. Your prompt was: '{prompt}'"
        
        logger.info(f"Using mock response: {mock_response}")
        return mock_response
    
    try:
        logger.info("Sending request to Anthropic API...")
        # Use a lower max_tokens value to reduce costs
        message = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,  # Reduced from 500
            temperature=0.5
        )
        
        response = str(message.content[0])
        logger.info("Received response from Anthropic API:")
        logger.info("-" * 40)
        logger.info(response)
        logger.info("-" * 40)
        
        return response
    except Exception as e:
        logger.error(f"Error generating response with Claude: {str(e)}", exc_info=True)
        return f"I apologize, but I encountered an error processing your request. Please try again."

def build_system_prompt(context: Dict[str, Any]) -> str:
    """
    Build the system prompt for Claude based on the provided context.
    
    Args:
        context: Dictionary containing customer, device, and request information
        
    Returns:
        The system prompt string
    """
    # Start with base prompt
    prompt = """You are an AI assistant for a smart home device company. Keep all responses brief and concise. 

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

    # Add customer information if available
    if "customer" in context:
        customer = context["customer"]
        # Handle both dict and Customer object
        if isinstance(customer, dict):
            customer_name = customer.get("name", "")
            service_level = customer.get("service_level", "").title()
            device = customer.get("device", {})
        else:
            customer_name = customer.name
            service_level = customer.service_level.title()
            device = customer.device

        prompt += f"\nCUSTOMER INFORMATION:\nName: {customer_name}\nService Level: {service_level}\n"
        
        # Add device information
        if device:
            device_type = device.get("type", "device")
            device_location = device.get("location", "")
            prompt += f"\nDEVICE INFORMATION:\n- {device_type} in the {device_location}\n"
    
    # Add permissions if available
    if "permissions" in context:
        permissions = context["permissions"]
        allowed_actions = permissions.get("allowed_actions", [])
        
        prompt += "\nALLOWED ACTIONS WITH CURRENT SERVICE LEVEL:\n"
        
        # Map action names to user-friendly descriptions
        action_descriptions = {
            "device_status": "Check if devices are online/offline and view basic status info",
            "device_power": "Turn devices on/off",
            "volume_control": "Adjust device volume",
            "song_changes": "Control music playback (next/previous/pause/play)"
        }
        
        for action in allowed_actions:
            if action in action_descriptions:
                prompt += f"- {action_descriptions[action]}\n"
    
    # Add action execution information if available
    if "action_execution" in context:
        execution = context["action_execution"]
        prompt += "\nACTION EXECUTION INFORMATION:\n"
        if "success" in execution:
            prompt += f"Action {'succeeded' if execution['success'] else 'failed'}"
            if "details" in execution:
                prompt += f": {execution['details']}"
        prompt += "\n"
    
    return prompt