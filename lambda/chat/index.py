import json
import os
import boto3
import logging
import time
import anthropic
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import threading

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE'))
customers_table = dynamodb.Table(os.environ.get('CUSTOMERS_TABLE'))
service_levels_table = dynamodb.Table(os.environ.get('SERVICE_LEVELS_TABLE'))
connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE'))

# Initialize API Gateway Management API client
# This will be initialized in the handler with the correct endpoint

# CORS headers (still needed for REST API fallback)
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',  # Allow all origins
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Requested-With',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(
    api_key=os.environ.get('ANTHROPIC_API_KEY')
)
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-opus-20240229')

# TTL for connections (24 hours in seconds)
CONNECTION_TTL = 24 * 60 * 60

# Maximum time to wait for a response (in seconds)
MAX_RESPONSE_TIME = 25  # Lambda timeout is 30s by default

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

def save_connection(connection_id: str, customer_id: str) -> None:
    """
    Save a WebSocket connection ID with a customer ID
    
    Args:
        connection_id: The WebSocket connection ID
        customer_id: The customer ID
    """
    logger.info(f"Saving connection {connection_id} for customer {customer_id}")
    
    # Calculate TTL
    ttl = int(time.time()) + CONNECTION_TTL
    
    try:
        # Save the connection in DynamoDB
        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'customerId': customer_id,
                'ttl': ttl,
                'timestamp': int(time.time())
            }
        )
        logger.info(f"Successfully saved connection {connection_id} for customer {customer_id}")
        
        # Verify the connection was saved by retrieving it
        try:
            response = connections_table.get_item(
                Key={
                    'connectionId': connection_id
                }
            )
            item = response.get('Item')
            if item:
                logger.info(f"Verified connection saved: {json.dumps(item)}")
            else:
                logger.warning(f"Connection verification failed: Item not found for connection {connection_id}")
        except Exception as verify_error:
            logger.error(f"Error verifying connection: {str(verify_error)}")
            
    except Exception as e:
        logger.error(f"Error saving connection: {str(e)}")
        raise

def get_customer_id_for_connection(connection_id: str) -> Optional[str]:
    """
    Get the customer ID associated with a connection ID
    
    Args:
        connection_id: The WebSocket connection ID
        
    Returns:
        The customer ID or None if not found
    """
    try:
        logger.info(f"Getting customer ID for connection {connection_id}")
        response = connections_table.get_item(
            Key={
                'connectionId': connection_id
            }
        )
        item = response.get('Item')
        if item:
            customer_id = item.get('customerId')
            logger.info(f"Found customer ID {customer_id} for connection {connection_id}")
            return customer_id
        logger.warning(f"No customer ID found for connection {connection_id}")
        return None
    except Exception as e:
        logger.error(f"Error getting customer ID for connection {connection_id}: {str(e)}")
        return None

def send_message(connection_id: str, message: str, endpoint_url: str) -> bool:
    """
    Send a message to a WebSocket client
    
    Args:
        connection_id: The WebSocket connection ID
        message: The message to send
        endpoint_url: The API Gateway Management API endpoint URL
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Sending message to connection {connection_id}")
        apigw_management_api = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
        
        # Ensure message is sent as a JSON object
        if isinstance(message, str):
            payload = json.dumps({'message': message})
        else:
            payload = json.dumps(message)
            
        apigw_management_api.post_to_connection(
            ConnectionId=connection_id,
            Data=payload.encode('utf-8')
        )
        logger.info(f"Message sent successfully to connection {connection_id}")
        return True
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error sending message to connection {connection_id}: {error_message}")
        
        # If the connection is gone, remove it from the database
        if "GoneException" in error_message:
            logger.info(f"Connection {connection_id} is gone, removing from database")
            try:
                connections_table.delete_item(
                    Key={
                        'connectionId': connection_id
                    }
                )
                logger.info(f"Successfully removed connection {connection_id} from database")
            except Exception as delete_error:
                logger.error(f"Error removing connection {connection_id} from database: {str(delete_error)}")
        
        return False

def handle_connect(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket connect event
    
    Args:
        event: The WebSocket event
        context: The Lambda context
        
    Returns:
        API Gateway response
    """
    connection_id = event['requestContext']['connectionId']
    logger.info(f"Connect event received for connection ID: {connection_id}")
    logger.info(f"Full connect event: {json.dumps(event)}")
    
    # Extract customer ID from query string parameters
    query_string_parameters = event.get('queryStringParameters', {}) or {}
    customer_id = query_string_parameters.get('customerId')
    logger.info(f"Query string parameters: {json.dumps(query_string_parameters)}")
    logger.info(f"Extracted customer ID from query: {customer_id}")
    
    # If no customer ID in query parameters, check for multiValueQueryStringParameters
    if not customer_id and 'multiValueQueryStringParameters' in event:
        multi_params = event.get('multiValueQueryStringParameters', {}) or {}
        customer_id_list = multi_params.get('customerId', [])
        if customer_id_list:
            customer_id = customer_id_list[0]
            logger.info(f"Extracted customer ID from multi-value query: {customer_id}")
    
    if not customer_id:
        logger.error("Missing customerId in connect request")
        return {'statusCode': 200, 'body': json.dumps({"status": "connected", "warning": "Missing customerId"})}
    
    # Save the connection
    try:
        save_connection(connection_id, customer_id)
        logger.info(f"Saved connection {connection_id} with customer ID {customer_id}")
    except Exception as e:
        logger.error(f"Error saving connection: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({"error": f"Error saving connection: {str(e)}"})}
    
    # Send a welcome message
    try:
        endpoint_url = f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
        welcome_message = {"type": "welcome", "message": f"Welcome! You are connected with customer ID: {customer_id}"}
        send_message(connection_id, welcome_message, endpoint_url)
        logger.info(f"Welcome message sent to connection {connection_id}")
    except Exception as e:
        logger.error(f"Error sending welcome message: {str(e)}")
    
    return {'statusCode': 200, 'body': json.dumps({"status": "connected", "customerId": customer_id})}

def handle_message(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket message event
    
    Args:
        event: The WebSocket event
        context: The Lambda context
        
    Returns:
        API Gateway response
    """
    connection_id = event['requestContext']['connectionId']
    logger.info(f"Message event received for connection ID: {connection_id}")
    
    # Create endpoint URL for sending messages
    endpoint_url = f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
    
    # Parse the message body first
    try:
        body = json.loads(event.get('body', '{}'))
        message = body.get('message')
        body_customer_id = body.get('customerId')
        
        logger.info(f"Parsed message body: {json.dumps(body)}")
        logger.info(f"Message content: {message}")
        logger.info(f"Customer ID from message body: {body_customer_id}")
        
        if not message:
            logger.error("Missing message in request")
            send_message(connection_id, {"error": "Missing message"}, endpoint_url)
            return {'statusCode': 400, 'body': json.dumps({"error": "Missing message"})}
    except Exception as e:
        logger.error(f"Error parsing message body: {str(e)}")
        send_message(connection_id, {"error": f"Invalid message format: {str(e)}"}, endpoint_url)
        return {'statusCode': 400, 'body': json.dumps({"error": f"Invalid message format: {str(e)}"})}
    
    # Get the customer ID for this connection
    customer_id = get_customer_id_for_connection(connection_id)
    logger.info(f"Retrieved customer ID for connection {connection_id}: {customer_id}")
    
    # If no customer ID found in connection table, use the one from the message body
    if not customer_id and body_customer_id:
        logger.info(f"Using customer ID from message body: {body_customer_id}")
        customer_id = body_customer_id
        
        # Save the connection with this customer ID for future messages
        try:
            save_connection(connection_id, customer_id)
            logger.info(f"Saved connection {connection_id} with customer ID {customer_id}")
        except Exception as e:
            logger.error(f"Error saving connection: {str(e)}")
    
    # If still no customer ID, return an error
    if not customer_id:
        logger.error("No customer ID found in connection or message")
        send_message(connection_id, {"error": "Missing customerId"}, endpoint_url)
        return {'statusCode': 400, 'body': json.dumps({"error": "Missing customerId"})}
    
    # Process the request
    try:
        # Send an acknowledgment
        ack_sent = send_message(connection_id, {"status": "processing", "message": "Processing your request..."}, endpoint_url)
        if not ack_sent:
            logger.warning(f"Failed to send acknowledgment to connection {connection_id}")
        
        # Process the request
        response_text = process_request(customer_id, message)
        logger.info(f"Generated response: {response_text}")
        
        # Send the response
        response_sent = send_message(connection_id, {"message": response_text}, endpoint_url)
        if not response_sent:
            logger.warning(f"Failed to send response to connection {connection_id}")
        
        return {'statusCode': 200, 'body': json.dumps({"status": "Message processed"})}
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error(f"Event: {json.dumps(event)}")
        send_message(connection_id, {"error": f"Error processing message: {str(e)}"}, endpoint_url)
        return {'statusCode': 500, 'body': json.dumps({"error": f"Error processing message: {str(e)}"})}

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for WebSocket and HTTP events
    
    Args:
        event: The event data
        context: The Lambda context
        
    Returns:
        API Gateway response
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Check if this is a WebSocket event
    if 'requestContext' in event and 'connectionId' in event['requestContext']:
        route_key = event['requestContext'].get('routeKey')
        
        if route_key == '$connect':
            return handle_connect(event, context)
        elif route_key == '$disconnect':
            # Simple disconnect handler
            connection_id = event['requestContext']['connectionId']
            logger.info(f"Disconnect event received for connection ID: {connection_id}")
            return {'statusCode': 200, 'body': 'Disconnected'}
        elif route_key == 'message':
            return handle_message(event, context)
        else:
            # Default route
            return handle_message(event, context)
    
    # If not a WebSocket event, handle as HTTP request (for backward compatibility)
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