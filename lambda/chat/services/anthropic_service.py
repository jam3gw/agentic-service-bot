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
import time
from typing import Dict, Any, Optional, List, Union, cast

# Third-party imports
import anthropic
from anthropic import Anthropic

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import custom metrics utility
from utils.metrics import metrics_client

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
    Use Claude to analyze a user request in two stages:
    1. Identify the high-level request type
    2. Extract detailed context based on the identified type
    
    Args:
        user_input: The user's request text
        
    Returns:
        A dictionary containing the analysis results, including:
        - primary_action: The primary action the request maps to, or None
        - all_actions: List of all actions required to fulfill the request
        - context: Additional context extracted from the request
        - ambiguous: Boolean indicating if the request could map to multiple actions
        - out_of_scope: Boolean indicating if the request doesn't map to any actions
    """
    logger.info("=" * 80)
    logger.info(f"Starting request analysis for input: {user_input}")
    
    # Stage 1: Identify request type
    stage1_prompt = """You are an AI assistant analyzing user requests for a smart home device system.
    
AVAILABLE ACTIONS:
- device_status: Check if devices are online/offline and view basic status info
- device_power: Turn devices on/off
- volume_control: Adjust device volume up/down
- song_changes: Change songs (next, previous, or specific song)

YOUR TASK:
Analyze the user's request and determine which action(s) it maps to. Focus ONLY on identifying the correct action type.
If it maps to multiple actions, list them in order of execution.
If it doesn't map to any action, indicate that it's out of scope.

AMBIGUITY GUIDELINES:
1. A request is ambiguous ONLY if:
   - It explicitly mentions multiple distinct actions (e.g., "turn up volume and play next song")
   - The intent is genuinely unclear between multiple possible actions
2. A request is NOT ambiguous if:
   - It uses different words/phrases for the same action (e.g., "skip this song" = "play next song")
   - It provides additional context that doesn't change the action (e.g., "I don't like this song" = "play next song")
   - It uses informal or colloquial language that maps to a clear action

RESPONSE FORMAT:
You must respond with a valid JSON object containing:
{
  "primary_action": "string or null",
  "all_actions": ["array of strings"],
  "ambiguous": "boolean",
  "out_of_scope": "boolean"
}

EXAMPLES:
User: "Turn on my speaker"
{
  "primary_action": "device_power",
  "all_actions": ["device_power"],
  "ambiguous": false,
  "out_of_scope": false
}

User: "Turn up the volume and play next song"
{
  "primary_action": "volume_control",
  "all_actions": ["volume_control", "song_changes"],
  "ambiguous": true,
  "out_of_scope": false
}

User: "Set the volume to 80%"
{
  "primary_action": "volume_control",
  "all_actions": ["volume_control"],
  "ambiguous": false,
  "out_of_scope": false
}

User: "I don't like this song"
{
  "primary_action": "song_changes",
  "all_actions": ["song_changes"],
  "ambiguous": false,
  "out_of_scope": false
}

User: "What's the weather like today?"
{
  "primary_action": null,
  "all_actions": [],
  "ambiguous": false,
  "out_of_scope": true
}

User: "Play Let's Get It Started"
{
  "primary_action": "song_changes",
  "all_actions": ["song_changes"],
  "ambiguous": false,
  "out_of_scope": false
}

User: "Play the next song"
{
  "primary_action": "song_changes",
  "all_actions": ["song_changes"],
  "ambiguous": false,
  "out_of_scope": false
}

User: "Play next"
{
  "primary_action": "song_changes",
  "all_actions": ["song_changes"],
  "ambiguous": false,
  "out_of_scope": false
}

IMPORTANT: Your response must be a valid JSON object. Do not include any explanatory text."""

    # If Anthropic client is not available, return a mock response
    if not anthropic_client:
        logger.info("Using mock response for local development")
        return _generate_mock_response(user_input)

    try:
        # Stage 1: Get high-level request type
        logger.info("Stage 1: Identifying request type...")
        
        # Track API call latency and token usage
        start_time = time.time()
        stage1_message = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            system=stage1_prompt,
            messages=[{"role": "user", "content": user_input}],
            max_tokens=300,
            temperature=0.0
        )
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Calculate token usage (input + output)
        input_tokens = stage1_message.usage.input_tokens if hasattr(stage1_message, 'usage') else 0
        output_tokens = stage1_message.usage.output_tokens if hasattr(stage1_message, 'usage') else 0
        total_tokens = input_tokens + output_tokens
        
        # Emit metrics
        metrics_client.track_anthropic_api_call(
            api_name="messages.create.stage1",
            duration_ms=duration_ms,
            tokens=total_tokens,
            success=True
        )
        
        stage1_result = _parse_json_response(stage1_message.content[0].text if stage1_message.content else "")
        logger.info(f"Stage 1 result: {json.dumps(stage1_result, indent=2)}")
        
        # If no valid action identified, return early
        if not stage1_result.get("primary_action"):
            return {
                "primary_action": None,
                "all_actions": [],
                "context": {},
                "ambiguous": stage1_result.get("ambiguous", False),
                "out_of_scope": stage1_result.get("out_of_scope", True)
            }
        
        # Stage 2: Extract detailed context based on identified action type
        primary_action = stage1_result["primary_action"]
        stage2_prompt = _build_context_extraction_prompt(primary_action)
        
        logger.info("Stage 2: Extracting detailed context...")
        
        # Track API call latency and token usage for stage 2
        start_time = time.time()
        stage2_message = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            system=stage2_prompt,
            messages=[{"role": "user", "content": user_input}],
            max_tokens=300,
            temperature=0.0
        )
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Calculate token usage (input + output)
        input_tokens = stage2_message.usage.input_tokens if hasattr(stage2_message, 'usage') else 0
        output_tokens = stage2_message.usage.output_tokens if hasattr(stage2_message, 'usage') else 0
        total_tokens = input_tokens + output_tokens
        
        # Emit metrics
        metrics_client.track_anthropic_api_call(
            api_name="messages.create.stage2",
            duration_ms=duration_ms,
            tokens=total_tokens,
            success=True
        )
        
        stage2_result = _parse_json_response(stage2_message.content[0].text if stage2_message.content else "")
        logger.info(f"Stage 2 result: {json.dumps(stage2_result, indent=2)}")
        
        # Combine results
        final_result = {
            "primary_action": stage1_result["primary_action"],
            "all_actions": stage1_result["all_actions"],
            "context": stage2_result.get("context", {}),
            "ambiguous": stage1_result["ambiguous"],
            "out_of_scope": stage1_result["out_of_scope"]
        }
        
        return final_result
        
    except Exception as e:
        logger.error(f"Error analyzing request: {str(e)}", exc_info=True)
        return {
            "primary_action": None,
            "all_actions": [],
            "context": {},
            "ambiguous": False,
            "out_of_scope": True
        }

def _build_context_extraction_prompt(action_type: str) -> str:
    """
    Build a prompt for extracting detailed context based on the action type.
    
    Args:
        action_type: The type of action identified in stage 1
        
    Returns:
        A prompt string for context extraction
    """
    if action_type == "volume_control":
        return """You are an AI assistant analyzing volume control requests.

YOUR TASK:
Extract specific details about how the volume should be changed.

RESPONSE FORMAT:
You must respond with a valid JSON object containing:
{
  "context": {
    "volume_change": {
      "direction": "up/down/set",
      "amount": number (1-100)
    }
  }
}

EXAMPLES:
User: "Turn up the volume"
{
  "context": {
    "volume_change": {
      "direction": "up",
      "amount": 10
    }
  }
}

User: "Set volume to 75%"
{
  "context": {
    "volume_change": {
      "direction": "set",
      "amount": 75
    }
  }
}

IMPORTANT: Your response must be a valid JSON object. Do not include any explanatory text."""
    
    elif action_type == "song_changes":
        return """You are an AI assistant analyzing song change requests.

YOUR TASK:
Extract specific details about how the song should be changed.

RESPONSE FORMAT:
You must respond with a valid JSON object containing:
{
  "context": {
    "song_action": "next/previous/specific",
    "requested_song": "song name" (only for specific songs)
  }
}

EXAMPLES:
User: "Play next song"
{
  "context": {
    "song_action": "next"
  }
}

User: "Go back to the previous song"
{
  "context": {
    "song_action": "previous"
  }
}

User: "Play Bohemian Rhapsody"
{
  "context": {
    "song_action": "specific",
    "requested_song": "Bohemian Rhapsody"
  }
}

User: "I don't like this song"
{
  "context": {
    "song_action": "next"
  }
}

IMPORTANT: Your response must be a valid JSON object. Do not include any explanatory text."""
    
    elif action_type == "device_power":
        return """You are an AI assistant analyzing device power requests.

YOUR TASK:
Extract specific details about how the device power should be changed.

RESPONSE FORMAT:
You must respond with a valid JSON object containing:
{
  "context": {
    "power_state": "on/off"
  }
}

EXAMPLES:
User: "Turn on my speaker"
{
  "context": {
    "power_state": "on"
  }
}

User: "Power off the device"
{
  "context": {
    "power_state": "off"
  }
}

IMPORTANT: Your response must be a valid JSON object. Do not include any explanatory text."""
    
    elif action_type == "device_status":
        return """You are an AI assistant analyzing device status requests.

YOUR TASK:
Extract specific details about what status information is being requested.

RESPONSE FORMAT:
You must respond with a valid JSON object containing:
{
  "context": {
    "query_type": "all/power/volume/song"
  }
}

EXAMPLES:
User: "What's the status of my speaker?"
{
  "context": {
    "query_type": "all"
  }
}

User: "Is my device on?"
{
  "context": {
    "query_type": "power"
  }
}

IMPORTANT: Your response must be a valid JSON object. Do not include any explanatory text."""
    
    else:
        return """You are an AI assistant analyzing user requests.

YOUR TASK:
Extract any relevant context from the request.

RESPONSE FORMAT:
You must respond with a valid JSON object containing:
{
  "context": {}
}

IMPORTANT: Your response must be a valid JSON object. Do not include any explanatory text."""

def _parse_json_response(response_text: str) -> Dict[str, Any]:
    """Parse JSON from Anthropic's response, handling various edge cases."""
    try:
        # First try to parse the entire response as JSON
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to extract the JSON object from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # Clean up any potential Unicode escapes
            json_str = json_str.encode('utf-8').decode('unicode_escape')
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse extracted JSON: {e}")
                logger.error(f"Extracted JSON string: {json_str}")
        else:
            logger.error("No JSON object found in response")
        
        # Return default structure if parsing fails
        return {
            "primary_action": None,
            "all_actions": [],
            "context": {},
            "ambiguous": False,
            "out_of_scope": True
        }

def _generate_mock_response(user_input: str) -> Dict[str, Any]:
    """Generate a mock response for local development."""
    text_lower = user_input.lower()
    
    if "status" in text_lower:
        return {
            "primary_action": "device_status",
            "all_actions": ["device_status"],
            "context": {"query_type": "all"},
            "ambiguous": False,
            "out_of_scope": False
        }
    
    return {
        "primary_action": None,
        "all_actions": [],
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
    logger.info("=" * 80)
    logger.info(f"Generating response for prompt: {prompt}")
    
    # Convert Customer object to dict before JSON serialization
    if context and "customer" in context and hasattr(context["customer"], "to_dict"):
        context = context.copy()  # Create a copy to avoid modifying the original
        context["customer"] = context["customer"].to_dict()
    
    # Add service level permissions to context
    if context and "customer" in context:
        service_level = context["customer"].get("service_level", "basic").lower()
        from .dynamodb_service import get_service_level_permissions
        permissions = get_service_level_permissions(service_level)
        context["permissions"] = permissions
        
        # Add action execution information based on permissions and device state
        if "request" in context:
            primary_action = context["request"].get("primary_action")
            if primary_action:
                allowed = primary_action in permissions.get("allowed_actions", [])
                
                # Check device state for actions that require the device to be on
                device_power = context["customer"].get("device", {}).get("power", "").lower()
                requires_power = primary_action in ["song_changes", "volume_control"]
                
                if allowed and requires_power and device_power != "on":
                    context["action_execution"] = {
                        "success": False,
                        "details": "Device is currently powered off. Please turn on your device first."
                    }
                else:
                    context["action_execution"] = {
                        "success": allowed,
                        "details": f"Action {primary_action} is {'allowed' if allowed else 'not allowed'} for service level {service_level}"
                    }
    
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
        
        # Track API call latency and token usage
        start_time = time.time()
        message = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,  # Reduced from 500
            temperature=0.5
        )
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Calculate token usage (input + output)
        input_tokens = message.usage.input_tokens if hasattr(message, 'usage') else 0
        output_tokens = message.usage.output_tokens if hasattr(message, 'usage') else 0
        total_tokens = input_tokens + output_tokens
        
        # Emit metrics
        metrics_client.track_anthropic_api_call(
            api_name="messages.create.response",
            duration_ms=duration_ms,
            tokens=total_tokens,
            success=True
        )
        
        response = str(message.content[0])
        logger.info("Received response from Anthropic API:")
        logger.info("-" * 40)
        logger.info(response)
        logger.info("-" * 40)
        
        return response
    except Exception as e:
        logger.error(f"Error generating response with Claude: {str(e)}", exc_info=True)
        
        # Track failed API call
        metrics_client.track_anthropic_api_call(
            api_name="messages.create.response",
            duration_ms=0,
            tokens=0,
            success=False
        )
        
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
            prompt += f"\nDEVICE INFORMATION:\n- {device_type}\n"
    
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