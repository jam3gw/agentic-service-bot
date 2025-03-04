#!/usr/bin/env python3
"""
Local test script for the Agentic Service Bot.

This script tests the local functionality of the bot without requiring
AWS resources or environment variables to be set.
"""

import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_imports():
    """Test that all imports work correctly."""
    logger.info("Testing imports...")
    
    try:
        # Test importing handlers
        from handlers.websocket_handler import handle_connect, handle_message, CORS_HEADERS
        logger.info("✅ Successfully imported from handlers.websocket_handler")
        
        # Test importing services
        from services.request_processor import process_request
        logger.info("✅ Successfully imported from services.request_processor")
        
        # Test importing models
        from models.customer import Customer
        logger.info("✅ Successfully imported from models.customer")
        
        # Test importing analyzers
        from analyzers.request_analyzer import RequestAnalyzer
        logger.info("✅ Successfully imported from analyzers.request_analyzer")
        
        # Test importing index
        import index
        logger.info("✅ Successfully imported index")
        
        logger.info("All imports successful! The modularization is working correctly.")
        return True
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        logger.error(f"Module path that failed: {e.__traceback__.tb_frame.f_globals['__name__']}")
        logger.error(f"Line number: {e.__traceback__.tb_lineno}")
        return False
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

def test_request_processing():
    """Test the request processing functionality."""
    logger.info("Testing request processing...")
    
    try:
        from services.request_processor import process_request
        
        # Create a mock customer ID and request
        customer_id = "test-customer-123"
        user_input = "Can you help me move my device to the living room?"
        
        # Process the request
        response = process_request(customer_id, user_input)
        
        logger.info(f"Response: {response}")
        logger.info("✅ Request processing test completed")
        return True
    except Exception as e:
        logger.error(f"Error in request processing test: {str(e)}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting local tests...")
    
    # Test imports
    if not test_imports():
        logger.error("Import tests failed. Exiting.")
        return False
    
    # Test request processing
    if not test_request_processing():
        logger.error("Request processing tests failed.")
        return False
    
    logger.info("✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 