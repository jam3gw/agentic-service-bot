#!/usr/bin/env python
"""
Test runner for the chat Lambda function.

This script runs all the tests for the chat Lambda function.
"""

import unittest
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set environment variables for testing
os.environ['CUSTOMERS_TABLE'] = 'dev-customers'
os.environ['SERVICE_LEVELS_TABLE'] = 'dev-service-levels'
os.environ['MESSAGES_TABLE'] = 'dev-messages'
os.environ['CONNECTIONS_TABLE'] = 'dev-connections'
os.environ['ANTHROPIC_API_KEY'] = 'dummy-key-for-testing'  # Will be ignored as we're not actually calling Anthropic
os.environ['ANTHROPIC_MODEL'] = 'claude-3-sonnet-20240229'
os.environ['ALLOWED_ORIGIN'] = '*'

def run_tests():
    """Run all tests."""
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir=current_dir, pattern='test_*.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return exit code based on test result
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run tests for the chat Lambda function.')
    parser.add_argument('--pattern', type=str, default='test_*.py',
                        help='Pattern to match test files (default: test_*.py)')
    parser.add_argument('--start-dir', type=str, default=None,
                        help='Directory to start discovery (default: current directory)')
    args = parser.parse_args()
    
    # Set pattern and start directory
    pattern = args.pattern
    start_dir = args.start_dir or current_dir
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir=start_dir, pattern=pattern)
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1) 