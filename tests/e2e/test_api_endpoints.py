"""
End-to-end tests for the Agentic Service Bot API endpoints.

This module tests the actual API endpoints:
- GET /api/customers/{customerId}/devices
- PATCH /api/customers/{customerId}/devices/{deviceId}
- GET /api/capabilities
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
REST_API_URL = "https://dehqrpqs4i.execute-api.us-west-2.amazonaws.com/dev"
WEBSOCKET_URL = "wss://ig3bth930d.execute-api.us-west-2.amazonaws.com/dev"

# Test data - updated with actual values from the database
TEST_CUSTOMER_ID = "test-customer-e2e-2b24b921"
TEST_DEVICE_ID = "test-customer-e2e-2b24b921-device-1"


def test_get_devices():
    """
    Test the GET /api/customers/{customerId}/devices endpoint.
    
    This test verifies that the endpoint returns the customer's devices
    with the correct structure.
    """
    # Make the API request
    response = requests.get(f"{REST_API_URL}/api/customers/{TEST_CUSTOMER_ID}/devices")
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify response structure
    assert "devices" in data, "Response should contain 'devices' key"
    assert isinstance(data["devices"], list), "'devices' should be a list"
    
    # If there are devices, verify their structure
    if data["devices"]:
        device = data["devices"][0]
        assert "id" in device, "Device should have an 'id'"
        assert "name" in device, "Device should have a 'name'"
        assert "type" in device, "Device should have a 'type'"
        assert "state" in device, "Device should have a 'state'"
        assert "capabilities" in device, "Device should have 'capabilities'"


def test_get_devices_invalid_customer():
    """
    Test the GET /api/customers/{customerId}/devices endpoint with an invalid customer ID.
    
    This test verifies that the endpoint returns a 404 error when the customer doesn't exist.
    """
    # Make the API request with an invalid customer ID
    response = requests.get(f"{REST_API_URL}/api/customers/invalid-customer-id/devices")
    
    # Verify response status code
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify error message
    assert "error" in data, "Response should contain 'error' key"
    assert "not found" in data["error"].lower(), "Error message should indicate customer not found"


def test_update_device():
    """
    Test the PATCH /api/customers/{customerId}/devices/{deviceId} endpoint.
    
    This test verifies that the endpoint updates the device state correctly.
    """
    # Prepare request body
    new_state = "on"
    body = {"state": new_state}
    
    # Make the API request
    response = requests.patch(
        f"{REST_API_URL}/api/customers/{TEST_CUSTOMER_ID}/devices/{TEST_DEVICE_ID}",
        json=body
    )
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify response structure
    assert "device" in data, "Response should contain 'device' key"
    assert "id" in data["device"], "Device should have an 'id'"
    assert "state" in data["device"], "Device should have a 'state'"
    assert data["device"]["state"] == new_state, f"Device state should be '{new_state}'"
    
    # Verify the device state was actually updated by making a GET request
    get_response = requests.get(f"{REST_API_URL}/api/customers/{TEST_CUSTOMER_ID}/devices")
    get_data = get_response.json()
    
    # Find the updated device
    updated_device = next((d for d in get_data["devices"] if d["id"] == TEST_DEVICE_ID), None)
    assert updated_device is not None, f"Device {TEST_DEVICE_ID} not found in GET response"
    assert updated_device["state"] == new_state, f"Device state should be '{new_state}'"


def test_update_device_invalid_customer():
    """
    Test the PATCH endpoint with an invalid customer ID.
    
    This test verifies that the endpoint returns a 404 error when the customer doesn't exist.
    """
    # Prepare request body
    body = {"state": "on"}
    
    # Make the API request with an invalid customer ID
    response = requests.patch(
        f"{REST_API_URL}/api/customers/invalid-customer-id/devices/{TEST_DEVICE_ID}",
        json=body
    )
    
    # Verify response status code
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}: {response.text}"


def test_update_device_invalid_device():
    """
    Test the PATCH endpoint with an invalid device ID.
    
    This test verifies that the endpoint returns a 404 error when the device doesn't exist.
    """
    # Prepare request body
    body = {"state": "on"}
    
    # Make the API request with an invalid device ID
    response = requests.patch(
        f"{REST_API_URL}/api/customers/{TEST_CUSTOMER_ID}/devices/invalid-device-id",
        json=body
    )
    
    # Verify response status code
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}: {response.text}"


def test_get_capabilities():
    """
    Test the GET /api/capabilities endpoint.
    
    This test verifies that the endpoint returns the service capabilities
    with the correct structure.
    """
    # Make the API request
    response = requests.get(f"{REST_API_URL}/api/capabilities")
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify response structure
    assert "capabilities" in data, "Response should contain 'capabilities' key"
    assert isinstance(data["capabilities"], list), "'capabilities' should be a list"
    
    # If there are capabilities, verify their structure
    if data["capabilities"]:
        capability = data["capabilities"][0]
        assert "id" in capability, "Capability should have an 'id'"
        assert "name" in capability, "Capability should have a 'name'"
        assert "description" in capability, "Capability should have a 'description'"
        # The serviceLevels field might not be present in all capabilities
        # so we'll make this check conditional
        if "serviceLevels" in capability:
            assert isinstance(capability["serviceLevels"], list), "'serviceLevels' should be a list"


if __name__ == "__main__":
    # This allows running the tests directly with python tests/e2e/test_api_endpoints.py
    pytest.main(["-xvs", __file__]) 