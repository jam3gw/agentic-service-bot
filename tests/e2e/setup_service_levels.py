#!/usr/bin/env python3
"""
Script to set up service level data in the database for API testing.

This script creates the service level definitions in the database
to be used for end-to-end testing of the API endpoints.
"""

import os
import sys
import boto3
from pathlib import Path

# DynamoDB configuration
REGION = "us-west-2"  # Same region as the API
SERVICE_LEVELS_TABLE = "dev-service-levels"  # Table name

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

def create_service_level(dynamodb, level, allowed_actions, description):
    """
    Create a service level in the DynamoDB table.
    
    Args:
        dynamodb: DynamoDB resource
        level: Service level name (basic, premium, enterprise)
        allowed_actions: List of allowed actions for this service level
        description: Description of the service level
        
    Returns:
        The created service level data if successful, None otherwise
    """
    try:
        table = dynamodb.Table(SERVICE_LEVELS_TABLE)
        
        # Create service level data
        service_level_data = {
            'level': level,
            'allowed_actions': allowed_actions,
            'description': description
        }
        
        # Put the item in the table
        response = table.put_item(Item=service_level_data)
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"✅ Created service level: {level}")
            return service_level_data
        else:
            print(f"❌ Failed to create service level: {response}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating service level: {str(e)}")
        return None

def main():
    """Run the service level setup process."""
    print("\n🔧 Setting up service level data for API testing...\n")
    
    # Create DynamoDB client
    dynamodb = create_dynamodb_client()
    if not dynamodb:
        print("Cannot proceed with setup due to DynamoDB client issues.")
        return 1
    
    # List available tables
    print_separator()
    print("Checking available DynamoDB tables:")
    tables = list_dynamodb_tables()
    
    if SERVICE_LEVELS_TABLE not in tables:
        print(f"⚠️ Warning: The table '{SERVICE_LEVELS_TABLE}' was not found in the list of available tables.")
        proceed = input("Do you want to proceed anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Setup aborted.")
            return 1
    
    # Create service levels
    print_separator()
    print(f"Creating service levels in table: {SERVICE_LEVELS_TABLE}")
    
    # Basic service level
    basic_actions = ["device_status", "device_power"]
    basic = create_service_level(
        dynamodb, 
        "basic", 
        basic_actions,
        "Basic service level with limited device control capabilities"
    )
    
    # Premium service level
    premium_actions = ["device_status", "device_power", "volume_control"]
    premium = create_service_level(
        dynamodb, 
        "premium", 
        premium_actions,
        "Premium service level with advanced device control capabilities"
    )
    
    # Enterprise service level
    enterprise_actions = ["device_status", "device_power", "volume_control", "song_changes"]
    enterprise = create_service_level(
        dynamodb, 
        "enterprise", 
        enterprise_actions,
        "Enterprise service level with full device control capabilities"
    )
    
    if not basic or not premium or not enterprise:
        print("Failed to set up service level data.")
        return 1
    
    print_separator()
    print("Service Level Setup Complete:")
    
    print("\nBasic Service Level:")
    print(f"  Allowed Actions: {', '.join(basic_actions)}")
    
    print("\nPremium Service Level:")
    print(f"  Allowed Actions: {', '.join(premium_actions)}")
    
    print("\nEnterprise Service Level:")
    print(f"  Allowed Actions: {', '.join(enterprise_actions)}")
    
    print_separator()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 