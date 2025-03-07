#!/usr/bin/env python3
"""
Script to verify DynamoDB data structure after migration.
This script reads and displays records from both customers and service levels tables.
"""

import boto3
import json
from decimal import Decimal
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DynamoDB configuration
REGION = "us-west-2"
CUSTOMERS_TABLE = "dev-customers"
SERVICE_LEVELS_TABLE = "dev-service-levels"

class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types in JSON encoding."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

def print_json(data: Dict[str, Any]) -> None:
    """Print dictionary as formatted JSON."""
    print(json.dumps(data, indent=2, cls=DecimalEncoder))

def verify_customers_table():
    """Verify the structure of records in the customers table."""
    logger.info("\nVerifying Customers Table:")
    print("-" * 50)
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(CUSTOMERS_TABLE)
    
    try:
        response = table.scan()
        items = response.get('Items', [])
        
        for item in items:
            logger.info(f"\nCustomer ID: {item.get('id')}")
            print_json(item)
            
            # Specifically check for level field
            if 'level' in item:
                logger.info(f"✓ Has 'level' field: {item['level']}")
            else:
                logger.error("✗ Missing 'level' field!")
                
            if 'serviceLevel' in item:
                logger.error("✗ Still has old 'serviceLevel' field!")
                
    except Exception as e:
        logger.error(f"Error reading customers table: {str(e)}")

def verify_service_levels_table():
    """Verify the structure of records in the service levels table."""
    logger.info("\nVerifying Service Levels Table:")
    print("-" * 50)
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(SERVICE_LEVELS_TABLE)
    
    try:
        response = table.scan()
        items = response.get('Items', [])
        
        for item in items:
            logger.info(f"\nService Level ID: {item.get('id')}")
            print_json(item)
            
            # Specifically check for level field
            if 'level' in item:
                logger.info(f"✓ Has 'level' field: {item['level']}")
            else:
                logger.error("✗ Missing 'level' field!")
                
            if 'serviceLevel' in item:
                logger.error("✗ Still has old 'serviceLevel' field!")
                
    except Exception as e:
        logger.error(f"Error reading service levels table: {str(e)}")

def main():
    """Run the verification process."""
    logger.info("Starting DynamoDB data verification...")
    
    try:
        verify_customers_table()
        verify_service_levels_table()
        
        logger.info("\nVerification completed!")
        return 0
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 