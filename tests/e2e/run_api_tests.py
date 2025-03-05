#!/usr/bin/env python3
"""
Script to run the API endpoint tests and provide a summary of the results.

This script runs the tests in test_api_endpoints.py and provides a detailed
report of which endpoints are working correctly and which are failing.
"""

import os
import sys
import unittest
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the test module
from tests.e2e.test_api_endpoints import (
    test_get_devices,
    test_get_devices_invalid_customer,
    test_update_device,
    test_update_device_invalid_customer,
    test_update_device_invalid_device,
    test_get_capabilities
)

def run_test(test_func, name):
    """Run a test function and return the result."""
    print(f"\n{'='*80}\nRunning test: {name}\n{'='*80}")
    try:
        test_func()
        print(f"\n✅ PASS: {name}")
        return True
    except AssertionError as e:
        print(f"\n❌ FAIL: {name}")
        print(f"Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {name}")
        print(f"Exception: {type(e).__name__}: {str(e)}")
        return False

def main():
    """Run all API tests and provide a summary."""
    print("\n🔍 Starting API endpoint verification...\n")
    
    # Define the tests to run
    tests = [
        (test_get_devices, "GET /api/customers/{customerId}/devices"),
        (test_get_devices_invalid_customer, "GET /api/customers/invalid-customer-id/devices"),
        (test_update_device, "PATCH /api/customers/{customerId}/devices/{deviceId}"),
        (test_update_device_invalid_customer, "PATCH /api/customers/invalid-customer-id/devices/{deviceId}"),
        (test_update_device_invalid_device, "PATCH /api/customers/{customerId}/devices/invalid-device-id"),
        (test_get_capabilities, "GET /api/capabilities")
    ]
    
    # Run the tests
    results = {}
    for test_func, name in tests:
        results[name] = run_test(test_func, name)
    
    # Print summary
    print("\n\n📊 API Endpoint Verification Summary:")
    print("="*80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"\nTotal endpoints tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    print("\nDetailed Results:")
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    # Return exit code based on test results
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main()) 