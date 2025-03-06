#!/usr/bin/env python3
"""
Script to clean up test data from the database after API testing.

This script removes test customers and their associated data
from the database to keep it clean after running tests.
"""

import os
import sys
import boto3
import argparse
from pathlib import Path

# DynamoDB configuration
REGION = "us-west-2"  # Same region as the API
CUSTOMERS_TABLE = "dev-customers"  # Table name
MESSAGES_TABLE = "dev-messages"  # Messages table name

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

def delete_customer_messages(dynamodb, customer_id):
    """
    Delete all messages for a test customer from the messages table.
    
    Args:
        dynamodb: DynamoDB resource
        customer_id: ID of the test customer
        
    Returns:
        Number of messages deleted
    """
    try:
        table = dynamodb.Table(MESSAGES_TABLE)
        
        # Query for messages with the customer ID
        response = table.scan(
            FilterExpression="customerId = :customerId",
            ExpressionAttributeValues={
                ":customerId": customer_id
            }
        )
        
        items = response.get('Items', [])
        deleted_count = 0
        
        # Delete each message
        for item in items:
            if 'id' in item:
                table.delete_item(Key={'id': item['id']})
                deleted_count += 1
        
        print(f"✅ Deleted {deleted_count} messages for customer: {customer_id}")
        return deleted_count
            
    except Exception as e:
        print(f"❌ Error deleting customer messages: {str(e)}")
        return 0

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Clean up test data from the database")
    
    parser.add_argument("--customer-id", required=True,
                        help="ID of the test customer to delete")
    
    parser.add_argument("--delete-messages", action="store_true",
                        help="Also delete messages for the customer")
    
    parser.add_argument("--force", action="store_true",
                        help="Skip confirmation prompt")
    
    return parser.parse_args()

def main():
    """Run the test data cleanup process."""
    args = parse_args()
    
    print("\n🧹 Cleaning up test data from the database...\n")
    
    # Create DynamoDB client
    dynamodb = create_dynamodb_client()
    if not dynamodb:
        print("Cannot proceed with cleanup due to DynamoDB client issues.")
        return 1
    
    # List available tables
    print_separator()
    print("Checking available DynamoDB tables:")
    tables = list_dynamodb_tables()
    
    if CUSTOMERS_TABLE not in tables:
        print(f"⚠️ Warning: The table '{CUSTOMERS_TABLE}' was not found in the list of available tables.")
        proceed = input("Do you want to proceed anyway? (y/n): ") if not args.force else 'y'
        if proceed.lower() != 'y':
            print("Cleanup aborted.")
            return 1
    
    if args.delete_messages and MESSAGES_TABLE not in tables:
        print(f"⚠️ Warning: The table '{MESSAGES_TABLE}' was not found in the list of available tables.")
        proceed = input("Do you want to proceed anyway? (y/n): ") if not args.force else 'y'
        if proceed.lower() != 'y':
            print("Cleanup aborted.")
            return 1
    
    # Confirm deletion
    if not args.force:
        print_separator()
        print(f"You are about to delete test customer: {args.customer_id}")
        if args.delete_messages:
            print(f"And all messages for this customer.")
        
        confirm = input("Are you sure you want to proceed? (y/n): ")
        if confirm.lower() != 'y':
            print("Cleanup aborted.")
            return 1
    
    # Delete messages if requested
    if args.delete_messages:
        print_separator()
        print(f"Deleting messages for customer: {args.customer_id}")
        delete_customer_messages(dynamodb, args.customer_id)
    
    # Delete the test customer
    print_separator()
    print(f"Deleting test customer: {args.customer_id}")
    success = delete_test_customer(dynamodb, args.customer_id)
    
    print_separator()
    if success:
        print("Test data cleanup completed successfully.")
    else:
        print("Test data cleanup completed with errors.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 