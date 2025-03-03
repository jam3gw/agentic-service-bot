import json
import os
import boto3
import logging
import time
import anthropic
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE'))
customers_table = dynamodb.Table(os.environ.get('CUSTOMERS_TABLE'))
service_levels_table = dynamodb.Table(os.environ.get('SERVICE_LEVELS_TABLE'))

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', 'https://agentic-service-bot.dev.jake-moses.com'),
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Requested-With',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
    'Access-Control-Allow-Credentials': 'true'
}

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(
    api_key=os.environ.get('ANTHROPIC_API_KEY')
)
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-opus-20240229')

class Customer:
    def __init__(self, customer_id: str, name: str, service_level: str, devices: List[Dict]):
        self.id = customer_id
        self.name = name
        self.service_level = service_level
        self.devices = devices
    
    def __str__(self) -> str:
        return f"Customer(id={self.id}, name={self.name}, service_level={self.service_level})"

    def get_device_by_id(self, device_id: str) -> Optional[Dict]:
        """Get a device by its ID"""
        for device in self.devices:
            if device["id"] == device_id:
                return device
        return None

    def get_device_by_location(self, location: str) -> Optional[Dict]:
        """Get a device by its location"""
        for device in self.devices:
            if device["location"] == location:
                return device
        return None

class RequestAnalyzer:
    """Analyzes and categorizes user requests"""
    
    # Mapping of request types to required actions
    REQUEST_TYPES = {
        "device_relocation": ["device_relocation"],
        "volume_change": ["volume_control"],
        "device_status": ["status_check"],
        "play_music": ["music_services"],
        "device_info": ["device_info"],
        "multi_room_setup": ["multi_room_audio"],
        "custom_routine": ["custom_actions"]
    }
    
    # Keywords that help identify request types
    KEYWORDS = {
        "device_relocation": ["move", "relocate", "place", "put", "position", "bedroom", "kitchen", "office", "living room"],
        "volume_change": ["volume", "louder", "quieter", "turn up", "turn down", "mute"],
        "device_status": ["status", "working", "broken", "online", "offline", "connected"],
        "play_music": ["play", "music", "song", "artist", "album", "playlist"],
        "device_info": ["what is", "information", "details", "specs", "tell me about"],
        "multi_room_setup": ["multi-room", "whole home", "multiple devices", "sync", "all devices"],
        "custom_routine": ["routine", "automation", "automate", "sequence", "schedule", "when I"]
    }
    
    @classmethod
    def identify_request_type(cls, text: str) -> Optional[str]:
        """Identifies the type of request from user text"""
        text = text.lower()
        scores = {req_type: 0 for req_type in cls.REQUEST_TYPES}
        
        # Score each request type based on keyword matches
        for req_type, keywords in cls.KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    scores[req_type] += 1
        
        # Get the request type with the highest score, if any score > 0
        if max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    @classmethod
    def extract_locations(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract source and destination locations from text"""
        locations = ["living room", "bedroom", "kitchen", "office", "bathroom", "dining room", 
                    "conference room", "reception"]
        
        source = None
        destination = None
        
        # Look for "from X to Y" pattern
        text = text.lower()
        for loc in locations:
            if f"from {loc}" in text:
                source = loc.replace(" ", "_")
            if f"to {loc}" in text:
                destination = loc.replace(" ", "_")
        
        # If only destination found, look for simple placement
        if not destination:
            for loc in locations:
                if loc in text and not source:
                    destination = loc.replace(" ", "_")
                    break
        
        return source, destination
    
    @classmethod
    def get_required_actions(cls, request_type: str) -> List[str]:
        """Get the list of actions required for a request type"""
        if request_type in cls.REQUEST_TYPES:
            return cls.REQUEST_TYPES[request_type]
        return []

def get_customer(customer_id: str) -> Optional[Customer]:
    """Get customer data from DynamoDB"""
    try:
        response = customers_table.get_item(Key={'id': customer_id})
        if 'Item' in response:
            item = response['Item']
            return Customer(
                item['id'],
                item['name'],
                item['service_level'],
                item['devices']
            )
        return None
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        return None

def get_service_level_permissions(service_level: str) -> Dict:
    """Get service level permissions from DynamoDB"""
    try:
        response = service_levels_table.get_item(Key={'level': service_level})
        if 'Item' in response:
            return response['Item']
        raise ValueError(f"Unknown service level: {service_level}")
    except Exception as e:
        logger.error(f"Error getting service level: {str(e)}")
        return {"allowed_actions": []}

def is_action_allowed(customer: Customer, action: str) -> bool:
    """Check if an action is allowed for a customer's service level"""
    permissions = get_service_level_permissions(customer.service_level)
    return action in permissions.get("allowed_actions", [])

def generate_response(prompt: str, context: Dict[str, Any] = None) -> str:
    """Generate a response using Anthropic's Claude API"""
    system_prompt = build_system_prompt(context)
    
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
    """Build a system prompt based on context"""
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

def process_request(customer_id: str, user_input: str) -> str:
    """Process a user request and generate a response"""
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

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for chat messages.
    
    Args:
        event: The event data from API Gateway
        context: The Lambda context
        
    Returns:
        API Gateway response
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Handle OPTIONS request (CORS preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    try:
        # Parse the request body
        body = json.loads(event.get('body', '{}'))
        message = body.get('message')
        customer_id = body.get('customerId')
        
        if not message or not customer_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        # Process the request
        response_text = process_request(customer_id, message)
        
        # Return the response
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'message': response_text,
                'customerId': customer_id,
            })
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        } 