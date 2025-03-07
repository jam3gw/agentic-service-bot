#!/usr/bin/env python3
"""
Script to migrate existing DynamoDB data to use standardized field names.
This script updates any records that use 'serviceLevel' to use 'level' instead.
"""

import boto3
import logging
from typing import Dict, Any, List, Optional
from boto3.resources.base import ServiceResource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DynamoDB configuration
REGION = "us-west-2"
CUSTOMERS_TABLE = "dev-customers"
SERVICE_LEVELS_TABLE = "dev-service-levels"

def create_dynamodb_client() -> Optional[ServiceResource]:
    """Create a DynamoDB client."""
    try:
        return boto3.resource('dynamodb', region_name=REGION)
    except Exception as e:
        logger.error(f"Error creating DynamoDB client: {str(e)}")
        return None

def migrate_customers_table(dynamodb: ServiceResource) -> None:
    """
    Migrate customer records to use 'level' instead of 'serviceLevel'.
    
    Args:
        dynamodb: DynamoDB resource
    """
    table = dynamodb.Table(CUSTOMERS_TABLE)
    
    try:
        # Scan for all customers
        response = table.scan()
        items = response.get('Items', [])
        
        # Process each customer
        for item in items:
            customer_id = item.get('id')
            if not customer_id:
                continue
                
            # Check if the record needs migration
            if 'serviceLevel' in item and 'level' not in item:
                logger.info(f"Migrating customer {customer_id}")
                
                # Create update expression
                update_expr = "SET #level = :level_value REMOVE serviceLevel"
                expr_attr_names = {
                    "#level": "level"
                }
                expr_attr_values = {
                    ":level_value": item['serviceLevel']
                }
                
                # Update the record
                table.update_item(
                    Key={'id': customer_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeNames=expr_attr_names,
                    ExpressionAttributeValues=expr_attr_values
                )
                
                logger.info(f"Successfully migrated customer {customer_id}")
            else:
                logger.debug(f"Customer {customer_id} already uses 'level' field")
                
    except Exception as e:
        logger.error(f"Error migrating customers table: {str(e)}")

def migrate_service_levels_table(dynamodb: ServiceResource) -> None:
    """
    Migrate service level records to use 'level' instead of 'serviceLevel'.
    
    Args:
        dynamodb: DynamoDB resource
    """
    table = dynamodb.Table(SERVICE_LEVELS_TABLE)
    
    try:
        # Scan for all service levels
        response = table.scan()
        items = response.get('Items', [])
        
        # Process each service level
        for item in items:
            level_id = item.get('id')
            if not level_id:
                continue
                
            # Check if the record needs migration
            if 'serviceLevel' in item and 'level' not in item:
                logger.info(f"Migrating service level {level_id}")
                
                # Create update expression
                update_expr = "SET #level = :level_value REMOVE serviceLevel"
                expr_attr_names = {
                    "#level": "level"
                }
                expr_attr_values = {
                    ":level_value": item['serviceLevel']
                }
                
                # Update the record
                table.update_item(
                    Key={'id': level_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeNames=expr_attr_names,
                    ExpressionAttributeValues=expr_attr_values
                )
                
                logger.info(f"Successfully migrated service level {level_id}")
            else:
                logger.debug(f"Service level {level_id} already uses 'level' field")
                
    except Exception as e:
        logger.error(f"Error migrating service levels table: {str(e)}")

def main():
    """Run the migration process."""
    logger.info("Starting DynamoDB data migration...")
    
    # Create DynamoDB client
    dynamodb = create_dynamodb_client()
    if not dynamodb:
        logger.error("Cannot proceed with migration due to DynamoDB client issues.")
        return 1
    
    try:
        # Migrate customers table
        logger.info("Migrating customers table...")
        migrate_customers_table(dynamodb)
        
        # Migrate service levels table
        logger.info("Migrating service levels table...")
        migrate_service_levels_table(dynamodb)
        
        logger.info("Migration completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 