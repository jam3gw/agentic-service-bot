"""
WebSocket handler for the Agentic Service Bot.

This module provides functions for handling WebSocket connections, messages,
and disconnections.
"""

import json
import logging
import boto3
import time
import os
import sys
from typing import Dict, Any, Optional

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Use absolute imports instead of relative imports
from services.dynamodb_service import (
    save_connection, 
    get_customer_id_for_connection,
    delete_connection,
    update_connection_status,
    store_message,
    get_customer
)
from services.request_processor import process_request

# Configure logging
logger = logging.getLogger()

# CORS headers (still needed for REST API fallback)
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',  # Allow all origins
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Requested-With',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}

def send_message(connection_id: str, message: str, endpoint_url: str, max_retries: int = 3) -> bool:
    """
    Send a message to a WebSocket client.
    
    Args:
        connection_id: The WebSocket connection ID
        message: The message to send
        endpoint_url: The API Gateway Management API endpoint URL
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if successful, False otherwise
    """
    retries = 0
    last_error = None
    
    while retries <= max_retries:
        try:
            logger.info(f"Sending message to connection {connection_id} (attempt {retries + 1}/{max_retries + 1})")
            apigw_management_api = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
            
            # Ensure message is sent as a JSON object
            if isinstance(message, str):
                payload = json.dumps({'message': message})
                logger.info(f"RESPONSE PAYLOAD (string): {payload}")
            else:
                payload = json.dumps(message)
                logger.info(f"RESPONSE PAYLOAD (object): {payload}")
            
            # Check if connection is valid before sending
            try:
                apigw_management_api.get_connection(ConnectionId=connection_id)
                logger.info(f"Connection {connection_id} is valid, proceeding with message send")
            except Exception as conn_err:
                logger.error(f"Connection {connection_id} is invalid: {str(conn_err)}")
                if "GoneException" in str(conn_err):
                    update_connection_status(connection_id, "disconnected")
                return False
                
            apigw_management_api.post_to_connection(
                ConnectionId=connection_id,
                Data=payload.encode('utf-8')
            )
            logger.info(f"Message sent successfully to connection {connection_id}")
            return True
        except Exception as e:
            last_error = str(e)
            error_type = type(e).__name__
            logger.warning(f"Error sending message to connection {connection_id} (attempt {retries + 1}): {error_type}: {last_error}")
            
            # If the connection is gone, mark it as disconnected instead of removing it
            if "GoneException" in last_error:
                logger.info(f"Connection {connection_id} is gone, marking as disconnected instead of removing")
                update_connection_status(connection_id, "disconnected")
                return False
            
            # For other errors, retry if we haven't exceeded max_retries
            retries += 1
            if retries <= max_retries:
                logger.info(f"Retrying in 0.5 seconds... ({retries}/{max_retries})")
                time.sleep(0.5)  # Wait before retrying
            else:
                logger.error(f"Failed to send message after {max_retries + 1} attempts: {last_error}")
                return False
    
    return False

def handle_connect(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket connect event.
    
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
    Handle WebSocket message event.
    
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
    
    # If customer ID is provided in the message body, use it instead
    if body_customer_id:
        if customer_id and customer_id != body_customer_id:
            logger.info(f"Overriding connection customer ID {customer_id} with message body customer ID {body_customer_id}")
        else:
            logger.info(f"Using customer ID from message body: {body_customer_id}")
        customer_id = body_customer_id
        
        # Save the connection with this customer ID for future messages
        try:
            save_connection(connection_id, customer_id)
            logger.info(f"Saved connection {connection_id} with customer ID {customer_id}")
        except Exception as e:
            logger.error(f"Error saving connection: {str(e)}")
    # If no customer ID found in connection table or message body, return an error
    elif not customer_id:
        logger.error("No customer ID found in connection or message")
        send_message(connection_id, {"error": "Missing customerId"}, endpoint_url)
        return {'statusCode': 400, 'body': json.dumps({"error": "Missing customerId"})}
    
    # Store the user message in DynamoDB before processing
    try:
        timestamp_ms = int(time.time() * 1000)
        user_conversation_id = f"conv_{customer_id}_user_{timestamp_ms}"
        
        logger.info(f"Storing user message in DynamoDB for customer {customer_id} from WebSocket handler")
        user_stored = store_message(
            conversation_id=user_conversation_id,
            customer_id=customer_id,
            message=message,
            sender='user'
        )
        if not user_stored:
            logger.error("Failed to store user message in DynamoDB from WebSocket handler")
    except Exception as e:
        logger.error(f"Error storing user message from WebSocket handler: {str(e)}")
        # Continue processing even if storage fails
    
    # Process the request
    try:
        # Send an acknowledgment
        logger.info(f"Sending acknowledgment to connection {connection_id}")
        ack_sent = send_message(connection_id, {"status": "processing", "message": "Processing your request..."}, endpoint_url)
        if not ack_sent:
            logger.warning(f"Failed to send acknowledgment to connection {connection_id}")
            # Check if connection is still valid
            try:
                apigw_management_api = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
                apigw_management_api.get_connection(ConnectionId=connection_id)
                logger.info(f"Connection {connection_id} is still valid despite acknowledgment failure")
            except Exception as conn_err:
                logger.error(f"Connection {connection_id} appears to be invalid: {str(conn_err)}")
                return {'statusCode': 500, 'body': json.dumps({"error": "Connection lost before processing completed"})}
        
        # Process the request
        logger.info(f"Processing request for customer {customer_id} (service level: {get_customer(customer_id).service_level}): '{message}'")
        start_time = time.time()
        response = process_request(customer_id=customer_id, user_input=message)
        response_text = response.get("message", "No response generated")
        processing_time = time.time() - start_time
        logger.info(f"Generated response in {processing_time:.2f} seconds: {response_text}")
        
        # Verify connection is still valid before sending response
        try:
            apigw_management_api = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
            apigw_management_api.get_connection(ConnectionId=connection_id)
            logger.info(f"Connection {connection_id} is still valid before sending response")
        except Exception as conn_err:
            logger.error(f"Connection {connection_id} is no longer valid before sending response: {str(conn_err)}")
            return {'statusCode': 500, 'body': json.dumps({"error": "Connection lost before response could be sent"})}
        
        # Send the response
        logger.info(f"Sending response to connection {connection_id}")
        response_payload = {"message": response_text}
        response_sent = send_message(connection_id, response_payload, endpoint_url)
        if not response_sent:
            logger.warning(f"Failed to send response to connection {connection_id}")
        else:
            logger.info(f"Successfully sent response to connection {connection_id}")
        
        return {'statusCode': 200, 'body': json.dumps({"status": "Message processed"})}
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error(f"Event: {json.dumps(event)}")
        send_message(connection_id, {"error": f"Error processing message: {str(e)}"}, endpoint_url)
        return {'statusCode': 500, 'body': json.dumps({"error": f"Error processing message: {str(e)}"})}

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for WebSocket and HTTP events.
    
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
            # Mark the connection as disconnected instead of removing it
            update_connection_status(connection_id, "disconnected")
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