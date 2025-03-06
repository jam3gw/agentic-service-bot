"""
End-to-end tests for the Agentic Service Bot Customer API endpoints.

This module tests the customer API endpoints:
- GET /customers
- GET /customers/{customerId}
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

# Remove hardcoded TEST_CUSTOMER_ID
# TEST_CUSTOMER_ID = "test-customer-e2e-2b24b921"


def test_get_customers():
    """
    Test the GET /customers endpoint.
    
    This test verifies that the endpoint returns all customers
    with the correct structure, including their service levels.
    """
    # Make the API request
    response = requests.get(f"{REST_API_URL}/customers")
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify response structure
    assert "customers" in data, "Response should contain 'customers' key"
    assert isinstance(data["customers"], list), "'customers' should be a list"
    
    # Verify at least one customer is returned
    assert len(data["customers"]) > 0, "At least one customer should be returned"
    
    # Verify customer structure
    customer = data["customers"][0]
    assert "id" in customer, "Customer should have 'id' field"
    assert "name" in customer, "Customer should have 'name' field"
    assert "level" in customer, "Customer should have 'level' field"
    
    # Verify service level details are included
    assert "levelDetails" in customer, "Customer should have 'levelDetails' field"
    assert isinstance(customer["levelDetails"], dict), "'levelDetails' should be an object"
    
    # Verify service level details structure
    level_details = customer["levelDetails"]
    assert "level" in level_details, "Service level details should have 'level' field"
    assert "allowed_actions" in level_details, "Service level details should have 'allowed_actions' field"


def test_get_customer(test_data):
    """
    Test the GET /customers/{customerId} endpoint.
    
    This test verifies that the endpoint returns a specific customer
    with the correct structure, including their service level.
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Make the API request
    response = requests.get(f"{REST_API_URL}/customers/{customer_id}")
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify response structure
    assert "customer" in data, "Response should contain 'customer' key"
    
    # Verify customer structure
    customer = data["customer"]
    assert "id" in customer, "Customer should have 'id' field"
    assert customer["id"] == customer_id, f"Customer ID should be {customer_id}"
    assert "name" in customer, "Customer should have 'name' field"
    assert "level" in customer, "Customer should have 'level' field"
    
    # Verify service level details are included
    assert "levelDetails" in customer, "Customer should have 'levelDetails' field"
    assert isinstance(customer["levelDetails"], dict), "'levelDetails' should be an object"
    
    # Verify service level details structure
    level_details = customer["levelDetails"]
    assert "level" in level_details, "Service level details should have 'level' field"
    assert "allowed_actions" in level_details, "Service level details should have 'allowed_actions' field"


def test_get_customer_invalid_id():
    """
    Test the GET /customers/{customerId} endpoint with an invalid customer ID.
    
    This test verifies that the endpoint returns a 404 error when
    an invalid customer ID is provided.
    """
    # Make the API request with an invalid customer ID
    response = requests.get(f"{REST_API_URL}/customers/invalid-customer-id")
    
    # Verify response status code
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify error message
    assert "error" in data, "Response should contain 'error' key"
    assert "not found" in data["error"].lower(), "Error message should indicate customer not found" 