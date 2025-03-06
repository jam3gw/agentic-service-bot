#!/usr/bin/env python3
"""
Script to check what customers and devices exist in the database.

This script makes API requests to discover what data is available
for testing, helping us identify valid customer and device IDs.
"""

import os
import sys
import json
import requests
from pathlib import Path

# API URLs for testing
REST_API_URL = "https://dehqrpqs4i.execute-api.us-west-2.amazonaws.com/dev/api"

def print_separator():
    """Print a separator line."""
    print("\n" + "="*80 + "\n")

def check_api_health():
    """Check if the API is accessible."""
    print("Checking API health...")
    try:
        # Try to access a known endpoint
        response = requests.get(f"{REST_API_URL}/capabilities")
        if response.status_code == 200:
            print("✅ API is accessible")
            return True
        else:
            print(f"❌ API returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing API: {str(e)}")
        return False

def discover_customers():
    """
    Try to discover what customers exist in the database.
    
    Since we don't have a direct endpoint to list all customers,
    we'll try some common IDs and patterns.
    """
    print_separator()
    print("Attempting to discover customers...")
    
    # List of customer IDs to try
    customer_ids = [
        "test-customer",
        "test-customer-1",
        "test-customer-2",
        "customer-1",
        "customer1",
        "demo-customer",
        "demo",
        "admin",
        "user-1",
        "default-customer"
    ]
    
    found_customers = []
    
    for customer_id in customer_ids:
        print(f"Checking customer ID: {customer_id}")
        response = requests.get(f"{REST_API_URL}/customers/{customer_id}/devices")
        
        if response.status_code == 200:
            data = response.json()
            devices = data.get("devices", [])
            print(f"✅ Found customer: {customer_id} with {len(devices)} devices")
            found_customers.append({
                "id": customer_id,
                "devices": devices
            })
        else:
            print(f"❌ Customer not found: {customer_id}")
    
    return found_customers

def main():
    """Run the data discovery process."""
    print("\n🔍 Starting data discovery...\n")
    
    if not check_api_health():
        print("Cannot proceed with data discovery due to API issues.")
        return 1
    
    customers = discover_customers()
    
    print_separator()
    print("Discovery Results:")
    
    if not customers:
        print("No customers found. You may need to create test data.")
        return 1
    
    print(f"Found {len(customers)} customers:")
    
    for customer in customers:
        print(f"\nCustomer ID: {customer['id']}")
        
        if customer['devices']:
            print(f"Devices ({len(customer['devices'])}):")
            for device in customer['devices']:
                print(f"  - {device.get('id', 'Unknown ID')}: {device.get('name', 'Unnamed')} ({device.get('type', 'Unknown type')})")
        else:
            print("No devices found for this customer.")
    
    print_separator()
    print("Recommended Test Configuration:")
    
    if customers:
        recommended_customer = customers[0]
        print(f"TEST_CUSTOMER_ID = \"{recommended_customer['id']}\"")
        
        if recommended_customer['devices']:
            recommended_device = recommended_customer['devices'][0]
            print(f"TEST_DEVICE_ID = \"{recommended_device.get('id', '')}\"")
        else:
            print("No devices found for testing.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 