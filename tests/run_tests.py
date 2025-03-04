#!/usr/bin/env python3
"""
Test runner for the Agentic Service Bot project.
Discovers and runs all tests in the tests directory.
"""
import unittest
import sys
import os

def run_tests():
    """Discover and run all tests"""
    # Add the parent directory to the path so we can import the lambda module
    sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests()) 