#!/usr/bin/env python3
"""
Script to update API Gateway WebSocket settings.

This script updates the idle timeout for WebSocket connections in API Gateway
to prevent connections from becoming invalid too quickly.
"""

import argparse
import boto3
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_websocket_idle_timeout(api_id, stage_name, timeout_in_seconds):
    """
    Update the idle timeout for WebSocket connections in API Gateway.
    
    Args:
        api_id: The API Gateway API ID
        stage_name: The stage name (e.g., 'dev', 'prod')
        timeout_in_seconds: The idle timeout in seconds (10-3600)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate timeout value
        if timeout_in_seconds < 10 or timeout_in_seconds > 3600:
            logger.error("Idle timeout must be between 10 and 3600 seconds")
            return False
            
        # Initialize API Gateway client
        client = boto3.client('apigatewayv2')
        
        # Update the stage settings
        response = client.update_stage(
            ApiId=api_id,
            StageName=stage_name,
            DefaultRouteSettings={
                'DataTraceEnabled': True,
                'DetailedMetricsEnabled': True,
                'ThrottlingBurstLimit': 100,
                'ThrottlingRateLimit': 50
            },
            RouteSettings={
                '$connect': {
                    'DataTraceEnabled': True,
                    'DetailedMetricsEnabled': True,
                    'ThrottlingBurstLimit': 100,
                    'ThrottlingRateLimit': 50
                },
                '$disconnect': {
                    'DataTraceEnabled': True,
                    'DetailedMetricsEnabled': True,
                    'ThrottlingBurstLimit': 100,
                    'ThrottlingRateLimit': 50
                },
                'message': {
                    'DataTraceEnabled': True,
                    'DetailedMetricsEnabled': True,
                    'ThrottlingBurstLimit': 100,
                    'ThrottlingRateLimit': 50
                }
            },
            StageVariables={
                'lambdaAlias': stage_name
            },
            WebSocketIdleTimeoutInSeconds=timeout_in_seconds
        )
        
        logger.info(f"Successfully updated WebSocket idle timeout to {timeout_in_seconds} seconds")
        logger.info(f"API Gateway response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating WebSocket idle timeout: {str(e)}")
        return False

def main():
    """Main function to parse arguments and update API Gateway settings."""
    parser = argparse.ArgumentParser(description='Update API Gateway WebSocket settings')
    parser.add_argument('--api-id', required=True, help='API Gateway API ID')
    parser.add_argument('--stage-name', required=True, help='Stage name (e.g., dev, prod)')
    parser.add_argument('--timeout', type=int, default=600, help='Idle timeout in seconds (10-3600, default: 600)')
    
    args = parser.parse_args()
    
    logger.info(f"Updating WebSocket idle timeout for API {args.api_id} stage {args.stage_name} to {args.timeout} seconds")
    
    success = update_websocket_idle_timeout(args.api_id, args.stage_name, args.timeout)
    
    if success:
        logger.info("WebSocket idle timeout updated successfully")
        sys.exit(0)
    else:
        logger.error("Failed to update WebSocket idle timeout")
        sys.exit(1)

if __name__ == "__main__":
    main() 