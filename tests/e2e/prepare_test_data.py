#!/usr/bin/env python3
"""
Prepare test data for end-to-end testing in the AWS development environment.

This script populates the DynamoDB tables in the development environment with
test data for end-to-end testing, including service levels and test customers
across different tiers.
"""

import boto3
import json
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def populate_test_data():
    """Populate DynamoDB tables with test data for end-to-end testing."""
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        
        # Get table references
        customers_table = dynamodb.Table('dev-customers')
        service_levels_table = dynamodb.Table('dev-service-levels')
        
        logger.info("Connected to DynamoDB tables")
        
        # Clear existing test data (only remove test customers, not all customers)
        clear_test_customers(customers_table)
        
        # Service levels should already exist, but we'll ensure they're correct
        ensure_service_levels(service_levels_table)
        
        # Add test customers
        add_test_customers(customers_table)
        
        logger.info("Test data preparation completed successfully")
        
    except Exception as e:
        logger.error(f"Error preparing test data: {str(e)}")
        raise

def clear_test_customers(table):
    """Clear test customers from the customers table."""
    logger.info("Clearing test customers from customers table")
    
    # Scan for test customers (those with IDs starting with 'test_' or specific test IDs)
    test_customer_prefixes = ['test_', 'cust_basic_001', 'cust_premium_001', 'cust_enterprise_001']
    
    for prefix in test_customer_prefixes:
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('id').begins_with(prefix)
        )
        
        # Delete test customers
        with table.batch_writer() as batch:
            for item in response['Items']:
                logger.info(f"Deleting test customer: {item['id']}")
                batch.delete_item(Key={'id': item['id']})

def ensure_service_levels(table):
    """Ensure service levels are correctly defined in the service levels table."""
    logger.info("Ensuring service levels are correctly defined")
    
    # Define expected service levels
    service_levels = [
        {
            'level': 'basic',
            'allowed_actions': [
                'status_check',
                'volume_control',
                'device_info'
            ],
            'max_devices': 1,
            'support_priority': 'standard'
        },
        {
            'level': 'premium',
            'allowed_actions': [
                'status_check',
                'volume_control',
                'device_info',
                'device_relocation',
                'music_services'
            ],
            'max_devices': 3,
            'support_priority': 'high'
        },
        {
            'level': 'enterprise',
            'allowed_actions': [
                'status_check',
                'volume_control',
                'device_info',
                'device_relocation',
                'music_services',
                'multi_room_audio',
                'custom_actions'
            ],
            'max_devices': 10,
            'support_priority': 'dedicated'
        }
    ]
    
    # Update or create service levels
    for level in service_levels:
        try:
            # Check if level exists
            response = table.get_item(Key={'level': level['level']})
            
            if 'Item' in response:
                logger.info(f"Updating service level: {level['level']}")
                table.update_item(
                    Key={'level': level['level']},
                    UpdateExpression='SET allowed_actions = :a, max_devices = :m, support_priority = :s',
                    ExpressionAttributeValues={
                        ':a': level['allowed_actions'],
                        ':m': level['max_devices'],
                        ':s': level['support_priority']
                    }
                )
            else:
                logger.info(f"Creating service level: {level['level']}")
                table.put_item(Item=level)
        except Exception as e:
            logger.error(f"Error updating service level {level['level']}: {str(e)}")
            raise

def add_test_customers(table):
    """Add test customers to the customers table."""
    logger.info("Adding test customers")
    
    # Define test customers
    customers = [
        {
            'id': 'cust_basic_001',
            'name': 'Jane Smith',
            'service_level': 'basic',
            'devices': [
                {
                    'id': 'dev_001',
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                }
            ]
        },
        {
            'id': 'cust_premium_001',
            'name': 'John Doe',
            'service_level': 'premium',
            'devices': [
                {
                    'id': 'dev_002',
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                },
                {
                    'id': 'dev_003',
                    'type': 'SmartDisplay',
                    'location': 'kitchen'
                }
            ]
        },
        {
            'id': 'cust_enterprise_001',
            'name': 'Alice Johnson',
            'service_level': 'enterprise',
            'devices': [
                {
                    'id': 'dev_004',
                    'type': 'SmartSpeaker',
                    'location': 'office'
                },
                {
                    'id': 'dev_005',
                    'type': 'SmartSpeaker',
                    'location': 'living_room'
                },
                {
                    'id': 'dev_006',
                    'type': 'SmartSpeaker',
                    'location': 'bedroom'
                },
                {
                    'id': 'dev_007',
                    'type': 'SmartDisplay',
                    'location': 'kitchen'
                }
            ]
        }
    ]
    
    # Add customers
    for customer in customers:
        try:
            logger.info(f"Adding customer: {customer['name']} ({customer['service_level']})")
            table.put_item(Item=customer)
        except Exception as e:
            logger.error(f"Error adding customer {customer['id']}: {str(e)}")
            raise

if __name__ == '__main__':
    populate_test_data() 