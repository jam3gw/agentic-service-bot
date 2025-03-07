#!/usr/bin/env python3
"""
Script to purge all data from DynamoDB tables.

This script will delete all items from the specified DynamoDB tables.
It includes safety checks and requires confirmation before proceeding.

CAUTION: This is a destructive operation that cannot be undone.
"""

import boto3
import sys
import time
from botocore.exceptions import ClientError

# Configuration
REGION = "us-west-2"  # Change to your region
# List of tables to purge - add or remove tables as needed
TABLES_TO_PURGE = [
    "dev-customers",
    "dev-messages",
    "dev-service-levels",
    "dev-connections"
]

def confirm_purge():
    """Ask for confirmation before proceeding with the purge."""
    print("\n" + "="*80)
    print("WARNING: You are about to delete ALL DATA from the following tables:")
    for table in TABLES_TO_PURGE:
        print(f"  - {table}")
    print("\nThis operation CANNOT be undone. All data will be permanently deleted.")
    print("="*80 + "\n")
    
    confirmation = input("Type 'DELETE ALL DATA' (in all caps) to confirm: ")
    return confirmation == "DELETE ALL DATA"

def count_items(table_name):
    """Count the number of items in a table."""
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(table_name)
    
    try:
        response = table.scan(Select='COUNT')
        return response.get('Count', 0)
    except ClientError as e:
        print(f"Error counting items in {table_name}: {e}")
        return 0

def purge_table(table_name):
    """Delete all items from a table."""
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(table_name)
    
    # Get the primary key name(s)
    try:
        table_description = dynamodb.meta.client.describe_table(TableName=table_name)
        key_schema = table_description['Table']['KeySchema']
        primary_key_names = [key['AttributeName'] for key in key_schema]
    except ClientError as e:
        print(f"Error getting key schema for {table_name}: {e}")
        return 0
    
    # Scan and delete items
    items_deleted = 0
    try:
        print(f"Scanning table {table_name}...")
        response = table.scan()
        items = response.get('Items', [])
        
        while True:
            for item in items:
                # Create a key dictionary for this item
                key = {k: item[k] for k in primary_key_names}
                
                try:
                    table.delete_item(Key=key)
                    items_deleted += 1
                    
                    # Print progress every 10 items
                    if items_deleted % 10 == 0:
                        print(f"Deleted {items_deleted} items from {table_name}...")
                        
                except ClientError as e:
                    print(f"Error deleting item {key} from {table_name}: {e}")
            
            # Check if there are more items to scan
            if 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items = response.get('Items', [])
            else:
                break
                
        print(f"Completed purging {table_name}. Deleted {items_deleted} items.")
        return items_deleted
        
    except ClientError as e:
        print(f"Error purging table {table_name}: {e}")
        return items_deleted

def main():
    """Main function to purge all tables."""
    # Check if tables exist
    try:
        dynamodb_client = boto3.client('dynamodb', region_name=REGION)
        existing_tables = dynamodb_client.list_tables()['TableNames']
        
        # Filter to only include tables that exist
        tables_to_purge = [table for table in TABLES_TO_PURGE if table in existing_tables]
        
        if not tables_to_purge:
            print("None of the specified tables exist in the DynamoDB. Nothing to purge.")
            return
            
        # Count items in each table
        print("Counting items in tables...")
        table_counts = {}
        for table in tables_to_purge:
            count = count_items(table)
            table_counts[table] = count
            print(f"  - {table}: {count} items")
            
        # Get confirmation
        if not confirm_purge():
            print("Purge cancelled.")
            return
            
        # Purge each table
        print("\nStarting purge operation...")
        start_time = time.time()
        
        results = {}
        for table in tables_to_purge:
            print(f"\nPurging table: {table}")
            items_deleted = purge_table(table)
            results[table] = items_deleted
            
        # Print summary
        elapsed_time = time.time() - start_time
        print("\n" + "="*50)
        print("PURGE OPERATION COMPLETE")
        print("="*50)
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        print("\nSummary:")
        
        total_deleted = 0
        for table, count in results.items():
            print(f"  - {table}: {count} items deleted (was {table_counts[table]})")
            total_deleted += count
            
        print(f"\nTotal items deleted: {total_deleted}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return

if __name__ == "__main__":
    main() 