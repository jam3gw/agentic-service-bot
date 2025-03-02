import json
import os
import boto3
import random
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('MESSAGES_TABLE'))

# Sample responses for demonstration
SAMPLE_RESPONSES = [
    "Hello! How can I help you today?",
    "That's interesting! Tell me more.",
    "I understand. Let me think about that.",
    "Thank you for sharing that information.",
    "Is there anything else you'd like to discuss?",
]

def get_random_response() -> str:
    """Get a random response from the sample responses."""
    return random.choice(SAMPLE_RESPONSES)

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
    
    try:
        # Parse the request body
        body = json.loads(event.get('body', '{}'))
        message = body.get('message')
        customer_id = body.get('customerId')
        
        if not message or not customer_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        # Generate a conversation ID if not provided
        conversation_id = body.get('conversationId') or f"conv_{customer_id}_{int(time.time() * 1000)}"
        
        # Store the user message
        timestamp = datetime.utcnow().isoformat()
        user_message_item = {
            'conversationId': conversation_id,
            'timestamp': timestamp,
            'userId': customer_id,
            'message': message,
            'sender': 'user',
        }
        
        table.put_item(Item=user_message_item)
        
        # Simulate processing time for a more complex interaction
        # This could be where you'd call an external AI service
        time.sleep(1)  # Simulating processing time
        
        # Generate a bot response
        bot_response = get_random_response()
        
        # Store the bot response
        bot_timestamp = datetime.utcnow().isoformat()
        bot_message_item = {
            'conversationId': conversation_id,
            'timestamp': bot_timestamp,
            'userId': customer_id,
            'message': bot_response,
            'sender': 'bot',
        }
        
        table.put_item(Item=bot_message_item)
        
        # Return the response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'message': bot_response,
                'conversationId': conversation_id,
            })
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': 'Internal server error'})
        } 