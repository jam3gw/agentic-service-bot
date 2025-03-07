"""
Pytest configuration for end-to-end API tests.

This module provides fixtures for setting up and tearing down test data.
"""

import os
import sys
import boto3
import uuid
import pytest
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path so that imports work correctly
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# DynamoDB configuration
REGION = "us-west-2"  # Same region as the API
CUSTOMERS_TABLE = "dev-customers"  # Table name

def create_dynamodb_client():
    """Create a DynamoDB client."""
    try:
        return boto3.resource('dynamodb', region_name=REGION)
    except Exception as e:
        print(f"Error creating DynamoDB client: {str(e)}")
        return None

def create_test_customer(dynamodb, customer_id):
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
        
        # Create a test customer with a single device
        device_id = f"{customer_id}-device-1"
        customer_data = {
            'id': customer_id,
            'name': 'E2E Test Customer',
            'email': 'test@example.com',
            'level': 'premium',
            'createdAt': datetime.now().isoformat(),
            'device': {
                'id': device_id,
                'name': 'Test Speaker',
                'type': 'speaker',
                'power': 'off',
                'volume': 5,
                'current_song': 'Test Song 1',
                'playlist': ['Test Song 1', 'Test Song 2', 'Test Song 3', 'Test Song 4'],
                'location': 'living_room',
                'capabilities': ['power', 'volume', 'song_control']
            }
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

@pytest.fixture(scope="session")
def test_data():
    """
    Fixture to set up and tear down test data for API tests.
    
    This fixture creates a test customer with devices before running the tests,
    and cleans up the data after the tests are complete.
    
    Returns:
        A dictionary containing the test customer ID and device ID
    """
    # Generate a unique customer ID for this test run
    customer_id = f"test-customer-e2e-{uuid.uuid4().hex[:8]}"
    
    # Create DynamoDB client
    dynamodb = create_dynamodb_client()
    if not dynamodb:
        pytest.fail("Failed to create DynamoDB client")
    
    # Create test customer
    customer_data = create_test_customer(dynamodb, customer_id)
    if not customer_data:
        pytest.fail("Failed to create test customer")
    
    # Extract device ID (since we now only have one device per customer)
    device_id = customer_data['device']['id'] if customer_data['device'] else None
    
    # Create test data dictionary
    test_data = {
        'customer_id': customer_id,
        'device_id': device_id
    }
    
    print(f"\nTest data created:")
    print(f"  Customer ID: {customer_id}")
    print(f"  Device ID: {device_id}")
    
    # Yield the test data to the tests
    yield test_data
    
    # Clean up after tests are complete
    print("\nCleaning up test data...")
    delete_result = delete_test_customer(dynamodb, customer_id)
    if not delete_result:
        print(f"⚠️ Warning: Failed to delete test customer {customer_id}") 