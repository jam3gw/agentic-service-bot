#!/usr/bin/env python3
"""
Script to run the API endpoint tests and provide a summary of the results.

This script runs the tests in the individual API test files and provides a detailed
report of which endpoints are working correctly and which are failing.
"""

import os
import sys
import unittest
import json
import uuid
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import boto3 for DynamoDB access
import boto3

# Import the capabilities API tests
from tests.e2e.test_capabilities_api import (
    test_get_capabilities
)

# Import the devices API tests
from tests.e2e.test_devices_api import (
    test_get_devices,
    test_get_devices_invalid_customer,
    test_update_device,
    test_update_device_invalid_customer,
    test_update_device_invalid_device
)

# Import the chat API tests
from tests.e2e.test_chat_api import (
    test_chat_history,
    test_chat_history_invalid_customer,
    test_send_message,
    test_send_message_invalid_customer,
    test_send_message_missing_parameters
)

# Import the customer API tests
from tests.e2e.test_customer_api import (
    test_get_customers,
    test_get_customer,
    test_get_customer_invalid_id
)

# Import the chat action tests
from tests.e2e.test_chat_actions import (
    test_device_status_action,
    test_device_power_action,
    test_volume_control_action,
    test_song_changes_action,
    test_service_level_permissions,
    test_basic_service_level_device_power,
    test_basic_user_device_flow
)

# Import test data setup functions from conftest.py
from tests.e2e.conftest import (
    create_dynamodb_client,
    create_test_customer,
    delete_test_customer
)

def setup_test_data():
    """Set up test data for the tests and return it."""
    # Generate a unique customer ID for this test run
    customer_id = f"test-customer-e2e-{uuid.uuid4().hex[:8]}"
    
    # Create DynamoDB client
    dynamodb = create_dynamodb_client()
    if not dynamodb:
        raise Exception("Failed to create DynamoDB client")
    
    # Create test customer
    customer_data = create_test_customer(dynamodb, customer_id)
    if not customer_data:
        raise Exception("Failed to create test customer")
    
    # Extract device ID (since we now only have one device per customer)
    device_id = customer_data['device']['id'] if 'device' in customer_data else None
    
    # Create test data dictionary
    test_data = {
        'customer_id': customer_id,
        'device_id': device_id,
        'dynamodb': dynamodb  # Store the dynamodb client for cleanup
    }
    
    print(f"\nTest data created:")
    print(f"  Customer ID: {customer_id}")
    print(f"  Device ID: {device_id}")
    
    return test_data

def cleanup_test_data(test_data):
    """Clean up test data after tests are complete."""
    print("\nCleaning up test data...")
    delete_result = delete_test_customer(test_data['dynamodb'], test_data['customer_id'])
    if not delete_result:
        print(f"⚠️ Warning: Failed to delete test customer {test_data['customer_id']}")

def run_test(test_func, name, test_data=None):
    """Run a test function and return the result."""
    print(f"\n{'='*80}\nRunning test: {name}\n{'='*80}")
    try:
        # Check if the function expects test_data
        import inspect
        sig = inspect.signature(test_func)
        
        if 'test_data' in sig.parameters:
            if test_data is None:
                raise Exception("Test requires test_data but none was provided")
            test_func(test_data)
        else:
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
    
    # Set up test data
    try:
        test_data = setup_test_data()
    except Exception as e:
        print(f"❌ Failed to set up test data: {str(e)}")
        return 1
    
    try:
        # Define the tests to run
        tests = [
            # Chat API tests
            (test_chat_history, "GET /chat/history/{customerId}"),
            (test_chat_history_invalid_customer, "GET /chat/history/invalid-customer-id"),
            (test_send_message, "POST /chat"),
            (test_send_message_invalid_customer, "POST /chat with invalid customer ID"),
            (test_send_message_missing_parameters, "POST /chat with missing parameters"),
            
            # Chat Action tests
            (test_device_status_action, "Chat API - Device Status Action"),
            (test_device_power_action, "Chat API - Device Power Action"),
            (test_volume_control_action, "Chat API - Volume Control Action"),
            (test_song_changes_action, "Chat API - Song Changes Action"),
            (test_service_level_permissions, "Chat API - Service Level Permissions"),
            (test_basic_service_level_device_power, "Chat API - Basic Service Level Device Power"),
            (test_basic_user_device_flow, "Chat API - Basic User Device Flow"),
            
            # Devices API tests
            (test_get_devices, "GET /customers/{customerId}/devices"),
            (test_get_devices_invalid_customer, "GET /customers/invalid-customer-id/devices"),
            (test_update_device, "PATCH /customers/{customerId}/devices/{deviceId}"),
            (test_update_device_invalid_customer, "PATCH /customers/invalid-customer-id/devices/{deviceId}"),
            (test_update_device_invalid_device, "PATCH /customers/{customerId}/devices/invalid-device-id"),
            
            # Customer API tests
            (test_get_customers, "GET /customers"),
            (test_get_customer, "GET /customers/{customerId}"),
            (test_get_customer_invalid_id, "GET /customers/invalid-customer-id"),
            
            # Capabilities API tests
            (test_get_capabilities, "GET /capabilities")
        ]
        
        # Run the tests
        results = {}
        for test_func, name in tests:
            results[name] = run_test(test_func, name, test_data)
        
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
    
    finally:
        # Clean up test data
        cleanup_test_data(test_data)

if __name__ == "__main__":
    sys.exit(main()) 