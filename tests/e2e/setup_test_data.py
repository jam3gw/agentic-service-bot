#!/usr/bin/env python3
"""
Script to set up test data in the database for API testing.

This script creates a test customer with devices in the database
to be used for end-to-end testing of the API endpoints.
"""

import os
import sys
import json
import boto3
import uuid
from datetime import datetime
from pathlib import Path

# DynamoDB configuration
REGION = "us-west-2"  # Same region as the API
CUSTOMERS_TABLE = "dev-customers"  # Corrected table name

def print_separator():
    """Print a separator line."""
    print("\n" + "="*80 + "\n")

def create_dynamodb_client():
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

def create_test_customer(dynamodb, customer_id="test-customer-e2e"):
    """
    Create a test customer in the DynamoDB table.
    
    Args:
        dynamodb: DynamoDB resource
        customer_id: ID for the test customer
        
    Returns:
        The created customer data if successful, None otherwise
    """
    try:
        table = dynamodb.Table(CUSTOMERS_TABLE)
        
        # Create a test customer with devices
        customer_data = {
            'id': customer_id,
            'name': 'E2E Test Customer',
            'email': 'test@example.com',
            'serviceLevel': 'premium',
            'createdAt': datetime.now().isoformat(),
            'devices': [
                {
                    'id': f"{customer_id}-device-1",
                    'name': 'Test Speaker',
                    'type': 'speaker',
                    'state': 'off',
                    'location': 'living_room',
                    'capabilities': ['power', 'volume']
                },
                {
                    'id': f"{customer_id}-device-2",
                    'name': 'Test Light',
                    'type': 'light',
                    'state': 'off',
                    'location': 'bedroom',
                    'capabilities': ['power', 'brightness']
                }
            ]
        }
        
        # Put the item in the table
        response = table.put_item(Item=customer_data)
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"✅ Created test customer: {customer_id}")
            return customer_data
        else:
            print(f"❌ Failed to create test customer: {response}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test customer: {str(e)}")
        return None

def main():
    """Run the test data setup process."""
    print("\n🔧 Setting up test data for API testing...\n")
    
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
        proceed = input("Do you want to proceed anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Setup aborted.")
            return 1
    
    # Create a test customer with a unique ID
    print_separator()
    print(f"Creating test customer in table: {CUSTOMERS_TABLE}")
    customer_id = f"test-customer-e2e-{uuid.uuid4().hex[:8]}"
    customer = create_test_customer(dynamodb, customer_id)
    
    if not customer:
        print("Failed to set up test data.")
        return 1
    
    print_separator()
    print("Test Data Setup Complete:")
    
    print(f"\nCustomer ID: {customer['id']}")
    print(f"Customer Name: {customer['name']}")
    print(f"Service Level: {customer['serviceLevel']}")
    
    print("\nDevices:")
    for device in customer['devices']:
        print(f"  - {device['id']}: {device['name']} ({device['type']})")
    
    print_separator()
    print("Test Configuration:")
    print(f"TEST_CUSTOMER_ID = \"{customer['id']}\"")
    print(f"TEST_DEVICE_ID = \"{customer['devices'][0]['id']}\"")
    
    print_separator()
    print("Update your test_api_endpoints.py file with these values.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 