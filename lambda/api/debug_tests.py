#!/usr/bin/env python3
"""
Debug script to identify test failures.

This script runs tests individually to identify specific failures.
"""

import unittest
import os
import sys
import traceback

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Set up environment variables for testing
def setup_test_environment():
    """Set up environment variables needed for tests."""
    os.environ['CUSTOMERS_TABLE'] = 'test-customers'
    os.environ['SERVICE_LEVELS_TABLE'] = 'test-service-levels'
    print("Test environment set up with mock DynamoDB tables")

def run_test_class(test_class):
    """Run a specific test class and report results."""
    print(f"\n{'='*80}\nRunning tests for: {test_class.__name__}\n{'='*80}")
    
    # Get all test methods in the class
    test_methods = [m for m in dir(test_class) if m.startswith('test_')]
    
    success_count = 0
    failure_count = 0
    
    for method_name in test_methods:
        print(f"\n{'-'*40}\nRunning: {method_name}\n{'-'*40}")
        
        # Create a test suite with just this test method
        suite = unittest.TestSuite()
        suite.addTest(test_class(method_name))
        
        # Run the test
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        
        if result.wasSuccessful():
            success_count += 1
            print(f"✅ {method_name} PASSED")
        else:
            failure_count += 1
            print(f"❌ {method_name} FAILED")
            
    print(f"\nResults for {test_class.__name__}: {success_count} passed, {failure_count} failed")
    return success_count, failure_count

if __name__ == '__main__':
    # Set up the test environment
    setup_test_environment()
    
    # Import test classes
    from services.test_dynamodb_service import TestDynamoDBService
    from handlers.test_device_handler import TestDeviceHandler
    from handlers.test_capability_handler import TestCapabilityHandler
    from test_api import TestApiLambda
    
    # Track overall results
    total_success = 0
    total_failure = 0
    
    # Run each test class separately
    test_classes = [
        TestDynamoDBService,
        TestDeviceHandler,
        TestCapabilityHandler,
        TestApiLambda
    ]
    
    for test_class in test_classes:
        success, failure = run_test_class(test_class)
        total_success += success
        total_failure += failure
    
    # Print overall summary
    print(f"\n{'='*80}")
    print(f"OVERALL RESULTS: {total_success} passed, {total_failure} failed")
    print(f"{'='*80}")
    
    # Exit with non-zero code if tests failed
    sys.exit(1 if total_failure > 0 else 0) 