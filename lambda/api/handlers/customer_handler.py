"""
Customer handler for the Agentic Service Bot API.

This module provides functions for handling customer-related API requests.
"""

# Standard library imports
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional
from decimal import Decimal

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Third-party imports
import boto3

# Local application imports
import services.dynamodb_service as dynamodb_service
from utils import convert_decimal_to_float, convert_float_to_decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS headers for responses
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PATCH,DELETE,PUT',
    'Access-Control-Allow-Credentials': 'false',
}

# Initialize DynamoDB client
CUSTOMERS_TABLE = os.environ.get('CUSTOMERS_TABLE', 'agentic-service-bot-customers')
SERVICE_LEVELS_TABLE = os.environ.get('SERVICE_LEVELS_TABLE', 'agentic-service-bot-service-levels')

def handle_get_customers(cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET request to retrieve all customers.
    
    Args:
        cors_headers: CORS headers to include in the response
        
    Returns:
        API Gateway response with customer data
    """
    try:
        logger.info("Retrieving all customers")
        
        # Get customers using the service function
        customers = dynamodb_service.get_customers()
        
        if customers is None:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Failed to retrieve customers'})
            }
        
        # Add service level details to each customer
        for customer in customers:
            # Use level consistently instead of serviceLevel
            level = customer.get('level', 'basic')
            
            try:
                # Get service level details
                service_levels = dynamodb_service.get_service_levels()
                level_details = service_levels.get(level, {}) if service_levels else {}
                
                # Add level details to customer
                customer['levelDetails'] = {
                    'level': level_details.get('name', level.capitalize()),
                    'description': level_details.get('description', ''),
                    'price': level_details.get('price', 0),
                    'allowed_actions': level_details.get('allowed_actions', [])
                }
            except Exception as e:
                logger.error(f"Error getting level details: {str(e)}")
                customer['levelDetails'] = {
                    'level': level.capitalize(),
                    'description': '',
                    'price': 0,
                    'allowed_actions': []
                }
        
        # Convert Decimal objects to floats before serialization
        customers = convert_decimal_to_float(customers)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'customers': customers})
        }
        
    except Exception as e:
        logger.error(f"Error retrieving customers: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f"Error retrieving customers: {str(e)}"})
        }

def handle_get_customer(customer_id: str, cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET request to retrieve a specific customer.
    
    Args:
        customer_id: The ID of the customer to retrieve
        cors_headers: CORS headers to include in the response
        
    Returns:
        API Gateway response with customer data
    """
    if not customer_id:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Missing required parameter: customerId'})
        }
    
    try:
        logger.info(f"Retrieving customer {customer_id}")
        
        # Get customer from DynamoDB using the service function
        customer = dynamodb_service.get_customer(customer_id)
        
        if not customer:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': f"Customer not found: {customer_id}"})
            }
        
        # Use level consistently instead of serviceLevel
        level = customer.get('level', 'basic')
        
        try:
            # Get service level details
            service_levels = dynamodb_service.get_service_levels()
            level_details = service_levels.get(level, {}) if service_levels else {}
            
            # Add level details to customer
            customer['levelDetails'] = {
                'level': level_details.get('name', level.capitalize()),
                'description': level_details.get('description', ''),
                'price': level_details.get('price', 0),
                'allowed_actions': level_details.get('allowed_actions', [])
            }
        except Exception as e:
            logger.error(f"Error getting level details: {str(e)}")
            customer['levelDetails'] = {
                'level': level.capitalize(),
                'description': '',
                'price': 0,
                'allowed_actions': []
            }
        
        # Convert Decimal objects to floats before serialization
        customer = convert_decimal_to_float(customer)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'customer': customer})
        }
        
    except Exception as e:
        logger.error(f"Error retrieving customer: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f"Error retrieving customer: {str(e)}"})
        }