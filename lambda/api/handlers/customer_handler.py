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

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Third-party imports
import boto3

# Local application imports
from utils import convert_decimal_to_float, convert_float_to_decimal
from services.dynamodb_service import get_customers, get_customer, get_service_level

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
customers_table = dynamodb.Table(os.environ.get('CUSTOMERS_TABLE', 'agentic-service-bot-customers'))
service_levels_table = dynamodb.Table(os.environ.get('SERVICE_LEVELS_TABLE', 'agentic-service-bot-service-levels'))

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
        customers = get_customers()
        
        if customers is None:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': "Failed to retrieve customers due to a service error"
                })
            }
        
        # Get service level details for each customer
        for customer in customers:
            service_level = customer.get('serviceLevel', 'basic')
            try:
                # Get service level details
                service_level_response = service_levels_table.get_item(
                    Key={'level': service_level}
                )
                service_level_item = service_level_response.get('Item', {})
                
                # Add service level details to customer
                customer['level'] = service_level
                customer['levelDetails'] = service_level_item
            except Exception as e:
                logger.error(f"Error retrieving service level for customer {customer.get('id')}: {str(e)}")
                customer['level'] = service_level
        
        # Convert Decimal objects to floats before serialization
        customers = convert_decimal_to_float(customers)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'customers': customers
            })
        }
    except Exception as e:
        logger.error(f"Error retrieving customers: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': f"Failed to retrieve customers: {str(e)}"
            })
        }

def handle_get_customer(customer_id: str, cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET request to retrieve a specific customer.
    
    Args:
        customer_id: ID of the customer to retrieve
        cors_headers: CORS headers to include in the response
        
    Returns:
        API Gateway response with customer data
    """
    try:
        logger.info(f"Retrieving customer {customer_id}")
        
        # Get customer from DynamoDB using the service function
        customer = get_customer(customer_id)
        
        if not customer:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': f"Customer {customer_id} not found"
                })
            }
        
        # Get service level details
        service_level = customer.get('serviceLevel', 'basic')
        try:
            # Get service level details
            service_level_response = service_levels_table.get_item(
                Key={'level': service_level}
            )
            service_level_item = service_level_response.get('Item', {})
            
            # Add service level details to customer
            customer['level'] = service_level
            customer['levelDetails'] = service_level_item
        except Exception as e:
            logger.error(f"Error retrieving service level for customer {customer_id}: {str(e)}")
            customer['level'] = service_level
        
        # Convert Decimal objects to floats before serialization
        customer = convert_decimal_to_float(customer)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'customer': customer
            })
        }
    except Exception as e:
        logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': f"Failed to retrieve customer {customer_id}: {str(e)}"
            })
        } 