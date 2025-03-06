"""
End-to-end tests for the Agentic Service Bot Devices API endpoints.

This module tests the devices API endpoints:
- GET /customers/{customerId}/devices
- PATCH /customers/{customerId}/devices/{deviceId}
"""

import os
import sys
import json
import pytest
import requests
from pathlib import Path

# Add the project root to the Python path so that imports work correctly
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "test"

# API URLs for testing
REST_API_URL = "https://k4w64ym45e.execute-api.us-west-2.amazonaws.com/dev/api"

# Test data - these are now used as fallbacks if the fixture isn't available
TEST_CUSTOMER_ID = "test-customer-e2e-d1a936e3"
TEST_DEVICE_ID = "test-customer-e2e-d1a936e3-device-1"

def test_get_devices(test_data):
    """Test the GET /customers/{customerId}/devices endpoint."""
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Make the API request
    response = requests.get(
        f"{REST_API_URL}/customers/{customer_id}/devices"
    )
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    response_body = response.json()
    
    # Verify response structure
    assert "devices" in response_body, "Response is missing devices array"
    devices = response_body["devices"]
    assert isinstance(devices, list), f"Expected devices to be a list, got {type(devices)}"
    
    # If there are devices, verify their structure
    if devices:
        device = devices[0]
        assert "id" in device, "Device is missing id"
        assert "name" in device, "Device is missing name"
        assert "type" in device, "Device is missing type"
        assert "state" in device, "Device is missing state"

def test_get_devices_invalid_customer():
    """Test the GET /customers/{customerId}/devices endpoint with an invalid customer ID."""
    # Make the API request
    response = requests.get(
        f"{REST_API_URL}/customers/invalid-customer-id/devices"
    )
    
    # Verify response status code
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}: {response.text}"

def test_update_device(test_data):
    """Test the PATCH /customers/{customerId}/devices/{deviceId} endpoint."""
    # Get customer and device IDs from test data fixture
    customer_id = test_data['customer_id']
    device_id = test_data['device_id']  # Use the single device
    
    # Prepare request body
    request_body = {
        "state": "on"
    }
    
    # Make the API request
    response = requests.patch(
        f"{REST_API_URL}/customers/{customer_id}/devices/{device_id}",
        json=request_body
    )
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    response_body = response.json()
    
    # Verify response structure
    assert "device" in response_body, "Response is missing device object"
    device = response_body["device"]
    assert "id" in device, "Device is missing id"
    assert "name" in device, "Device is missing name"
    assert "type" in device, "Device is missing type"
    assert "state" in device, "Device is missing state"
    
    # Verify the device status was updated
    assert device["state"] == "on", f"Expected device state to be 'on', got {device.get('state')}"
    
    # Get the device list to verify the update
    get_response = requests.get(
        f"{REST_API_URL}/customers/{customer_id}/devices"
    )
    get_response_body = get_response.json()
    
    # Find the updated device in the list
    updated_device = next(
        (d for d in get_response_body["devices"] if d["id"] == device_id),
        None
    )
    
    # Verify the device was found and has the updated status
    assert updated_device is not None, f"Device {device_id} not found in device list"
    assert updated_device["state"] == "on", f"Expected device state to be 'on', got {updated_device.get('state')}"

def test_update_device_invalid_customer(test_data):
    """Test the PATCH /customers/{customerId}/devices/{deviceId} endpoint with an invalid customer ID."""
    # Get device ID from test data fixture
    device_id = test_data['device_id']  # Use the single device
    
    # Prepare request body
    request_body = {
        "state": "on"
    }
    
    # Make the API request
    response = requests.patch(
        f"{REST_API_URL}/customers/invalid-customer-id/devices/{device_id}",
        json=request_body
    )
    
    # Verify response status code
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}: {response.text}"

def test_update_device_invalid_device(test_data):
    """Test the PATCH /customers/{customerId}/devices/{deviceId} endpoint with an invalid device ID."""
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Prepare request body
    request_body = {
        'state': 'on'
    }
    
    # Make the API request
    response = requests.patch(
        f"{REST_API_URL}/customers/{customer_id}/devices/invalid-device-id",
        json=request_body
    )
    
    # Verify response status code
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}: {response.text}"