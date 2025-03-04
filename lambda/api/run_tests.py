#!/usr/bin/env python3
"""
Script to run all tests for the API Lambda function.

This script discovers and runs all tests in the API Lambda package.
"""

import unittest
import os
import sys

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Set up environment variables for testing
def setup_test_environment():
    """Set up environment variables needed for tests."""
    os.environ['CUSTOMERS_TABLE'] = 'test-customers'
    os.environ['SERVICE_LEVELS_TABLE'] = 'test-service-levels'
    print("Test environment set up with mock DynamoDB tables")

if __name__ == '__main__':
    # Set up the test environment
    setup_test_environment()
    
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir=current_dir, pattern='test_*.py')
    
    # Run the tests
    print(f"Running tests from {current_dir}")
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful()) 