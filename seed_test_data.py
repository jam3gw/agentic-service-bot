#!/usr/bin/env python3
"""
Script to seed test data in the DynamoDB tables for the Agentic Service Bot.

This script creates test customers with different service levels (basic, premium, enterprise)
and their associated devices to help with testing the UI and API.
"""

import json
import boto3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from boto3.resources.base import ServiceResource
import logging

# DynamoDB configuration
REGION = "us-west-2"
CUSTOMERS_TABLE = "dev-customers"
SERVICE_LEVELS_TABLE = "dev-service-levels"

logger = logging.getLogger(__name__)

def print_separator():
    """Print a separator line."""
    print("\n" + "="*80 + "\n")

def create_dynamodb_client() -> Optional[ServiceResource]:
    """Create a DynamoDB client."""
    try:
        return boto3.resource('dynamodb', region_name=REGION)
    except Exception as e:
        print(f"Error creating DynamoDB client: {str(e)}")
        return None

def list_dynamodb_tables():
    """List all DynamoDB tables in the account."""
    try:
        # Create a DynamoDB client
        dynamodb_client = boto3.client('dynamodb', region_name=REGION)
        
        # List tables
        response = dynamodb_client.list_tables()
        
        if 'TableNames' in response:
            print(f"Found {len(response['TableNames'])} DynamoDB tables:")
            for table_name in response['TableNames']:
                print(f"  - {table_name}")
            return response['TableNames']
        else:
            print("No tables found or unable to list tables.")
            return []
            
    except Exception as e:
        print(f"Error listing DynamoDB tables: {str(e)}")
        return []

def create_test_customer(dynamodb, customer_id: str, name: str, level: str, device_type: str = "speaker") -> Optional[Dict[str, Any]]:
    """
    Create a test customer in DynamoDB.
    
    Args:
        dynamodb: DynamoDB resource
        customer_id: Unique identifier for the customer
        name: Customer's name
        level: Service level (basic, premium, enterprise)
        device_type: Type of device to create for the customer
        
    Returns:
        The created customer record or None if there was an error
    """
    table = dynamodb.Table(CUSTOMERS_TABLE)  # type: ignore
    
    # Set capabilities based on service level
    capabilities = ["device_status", "device_power"]  # Basic level capabilities
    
    if level in ['premium', 'enterprise']:
        capabilities.append("volume_control")
        
    if level == 'enterprise':
        capabilities.append("song_changes")
    
    # Create device object with all necessary fields
    device = {
        'id': f"{customer_id}-device-1",
        'name': f"{name}'s {device_type.title()}",
        'type': device_type,
        'power': 'off',  # Initial state is off
        'status': 'online',  # Initial status is online
        'lastUpdated': datetime.now().isoformat()
    }
    
    # Add volume and playlist for all audio devices, but control is based on service level
    if device_type in ['speaker', 'audio']:
        device['volume'] = str(40)  # Set volume to 40%
        device['currentSong'] = "Let's Get It Started - The Black Eyed Peas"  # Set default song
        device['playlist'] = json.dumps([
            "Let's Get It Started - The Black Eyed Peas",
            "Imagine - John Lennon",
            "Don't Stop Believin' - Journey",
            "Sweet Caroline - Neil Diamond",
            "I Wanna Dance with Somebody - Whitney Houston",
            "Walking on Sunshine - Katrina & The Waves",
            "Happy - Pharrell Williams",
            "Uptown Funk - Mark Ronson ft. Bruno Mars",
            "Can't Stop the Feeling! - Justin Timberlake",
            "Good Vibrations - The Beach Boys",
            "Three Little Birds - Bob Marley & The Wailers"
        ])
        device['currentSongIndex'] = "0"  # Add current song index as string
    
    # Create customer record
    customer = {
        'id': customer_id,
        'name': name,
        'level': level,
        'email': f"{name.lower().replace(' ', '.')}@example.com",
        'createdAt': datetime.now().isoformat(),
        'device': device,
        'capabilities': capabilities
    }
    
    try:
        table.put_item(Item=customer)
        logger.info(f"Created test customer: {customer_id}")
        return customer
    except Exception as e:
        logger.error(f"Error creating test customer: {str(e)}")
        return None

def delete_test_customer(dynamodb, customer_id):
    """
    Delete a test customer from the DynamoDB table.
    
    Args:
        dynamodb: DynamoDB resource
        customer_id: ID of the test customer to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        table = dynamodb.Table(CUSTOMERS_TABLE)
        
        # Check if the customer exists
        response = table.get_item(Key={'id': customer_id})
        
        if 'Item' not in response:
            print(f"⚠️ Customer {customer_id} not found in the database.")
            return False
        
        # Delete the customer
        response = table.delete_item(Key={'id': customer_id})
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"✅ Deleted test customer: {customer_id}")
            return True
        else:
            print(f"❌ Failed to delete test customer: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting test customer: {str(e)}")
        return False

def create_test_service_levels(dynamodb) -> None:
    """Create test service levels in DynamoDB."""
    table = dynamodb.Table(SERVICE_LEVELS_TABLE)
    
    # Define service levels
    service_levels = {
        'basic': {
            'level': 'basic',
            'name': 'Basic',
            'description': 'Basic service level with device status and power control',
            'price': 0,
            'allowed_actions': ['device_status', 'device_power']
        },
        'premium': {
            'level': 'premium',
            'name': 'Premium',
            'description': 'Premium service level with volume control',
            'price': 9.99,
            'allowed_actions': ['device_status', 'device_power', 'volume_control']
        },
        'enterprise': {
            'level': 'enterprise',
            'name': 'Enterprise',
            'description': 'Enterprise service level with full device control',
            'price': 29.99,
            'allowed_actions': ['device_status', 'device_power', 'volume_control', 'song_changes']
        }
    }
    
    # Put each service level in the table
    for level_data in service_levels.values():
        table.put_item(Item=level_data)
        print(f"✅ Created service level: {level_data['name']}")

def create_test_data(dynamodb) -> None:
    """Create test data in DynamoDB."""
    # Create test customers with different service levels
    customers = [
        {
            'id': 'cust_basic_001',
            'name': 'Jake',
            'level': 'basic',
            'device_type': 'speaker'
        },
        {
            'id': 'cust_premium_001',
            'name': 'Mo',
            'level': 'premium',
            'device_type': 'speaker'
        },
        {
            'id': 'cust_enterprise_001',
            'name': 'Tom',
            'level': 'enterprise',
            'device_type': 'speaker'
        }
    ]
    
    for customer in customers:
        create_test_customer(
            dynamodb,
            customer['id'],
            customer['name'],
            customer['level'],
            customer['device_type']
        )

def main():
    """Run the test data setup process."""
    print("\n🔧 Setting up test data for the Agentic Service Bot...\n")
    
    # Create DynamoDB client
    dynamodb = create_dynamodb_client()
    if not dynamodb:
        print("Cannot proceed with setup due to DynamoDB client issues.")
        return 1
    
    # List available tables
    print_separator()
    print("Checking available DynamoDB tables:")
    tables = list_dynamodb_tables()
    
    if CUSTOMERS_TABLE not in tables:
        print(f"⚠️ Warning: The table '{CUSTOMERS_TABLE}' was not found in the list of available tables.")
        print("Proceeding anyway...")
    
    # Check for existing test customers
    print_separator()
    print("Checking for existing test customers...")
    
    # Check for existing test customers
    try:
        table = dynamodb.Table(CUSTOMERS_TABLE)
        response = table.scan(
            FilterExpression="begins_with(id, :prefix)",
            ExpressionAttributeValues={":prefix": "test-"}
        )
        
        existing_customers = response.get('Items', [])
        if existing_customers:
            print(f"Found {len(existing_customers)} existing test customers:")
            for customer in existing_customers:
                print(f"  - {customer.get('id')}: {customer.get('name')} ({customer.get('level')})")
            
            print("Skipping deletion of existing test customers.")
    except Exception as e:
        print(f"Error checking for existing test customers: {str(e)}")
    
    # Create test customers with different service levels
    print_separator()
    print(f"Creating test customers in table: {CUSTOMERS_TABLE}")
    
    # Basic service level customer
    basic_customer_id = f"test-basic-{uuid.uuid4().hex[:8]}"
    basic_customer = create_test_customer(
        dynamodb,
        basic_customer_id,
        "Jake",
        "basic",
        "speaker"
    )
    
    # Premium service level customer
    premium_customer_id = f"test-premium-{uuid.uuid4().hex[:8]}"
    premium_customer = create_test_customer(
        dynamodb,
        premium_customer_id,
        "Mo",
        "premium",
        "speaker"
    )
    
    # Enterprise service level customer
    enterprise_customer_id = f"test-enterprise-{uuid.uuid4().hex[:8]}"
    enterprise_customer = create_test_customer(
        dynamodb,
        enterprise_customer_id,
        "Sonja",
        "enterprise",
        "speaker"
    )
    
    if not basic_customer or not premium_customer or not enterprise_customer:
        print("Failed to set up all test customers.")
        return 1
    
    print_separator()
    print("Test Data Setup Complete:")
    
    print("\nBasic Customer:")
    print(f"  ID: {basic_customer_id}")
    print(f"  Name: {basic_customer['name']}")
    print(f"  Level: {basic_customer['level']}")
    print(f"  Device: {basic_customer['device']['id']}")
    
    print("\nPremium Customer:")
    print(f"  ID: {premium_customer_id}")
    print(f"  Name: {premium_customer['name']}")
    print(f"  Level: {premium_customer['level']}")
    print(f"  Device: {premium_customer['device']['id']}")
    
    print("\nEnterprise Customer:")
    print(f"  ID: {enterprise_customer_id}")
    print(f"  Name: {enterprise_customer['name']}")
    print(f"  Level: {enterprise_customer['level']}")
    print(f"  Device: {enterprise_customer['device']['id']}")
    
    print_separator()
    print("You can now use these test customers in the UI and API tests.")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 