"""
End-to-end tests for the Agentic Service Bot Chat API endpoints.

This module tests the chat API endpoints:
- GET /chat/history/{customerId}
- POST /chat
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


def test_chat_history(test_data):
    """
    Test the GET /chat/history/{customerId} endpoint.
    
    This test verifies that the endpoint returns the chat history for a customer
    with the correct structure.
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Make the API request
    response = requests.get(f"{REST_API_URL}/chat/history/{customer_id}")
    
    # Check for 502 Bad Gateway error (known issue)
    if response.status_code == 502:
        print("\n⚠️ WARNING: Received 502 Bad Gateway error from chat history endpoint.")
        print("This is a known issue with the current API deployment.")
        print("Please check the API logs for more information.")
        
        # Still fail the test, but with a more informative message
        assert False, "Chat history endpoint returned 502 Bad Gateway error (known issue)"
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify response structure
    assert "messages" in data, "Response should contain 'messages' field"
    assert isinstance(data["messages"], list), "'messages' should be a list"
    assert "customerId" in data, "Response should contain 'customerId' field"
    assert data["customerId"] == customer_id, f"customerId should be '{customer_id}'"
    
    # If there are messages, verify their structure
    if data["messages"]:
        message = data["messages"][0]
        assert "id" in message, "Message should have an 'id'"
        assert "text" in message, "Message should have 'text'"
        assert "sender" in message, "Message should have a 'sender'"
        assert "timestamp" in message, "Message should have a 'timestamp'"
        assert "conversationId" in message, "Message should have a 'conversationId'"


def test_chat_history_invalid_customer():
    """
    Test the GET /chat/history/{customerId} endpoint with an invalid customer ID.
    
    This test verifies that the endpoint returns a 404 error when
    an invalid customer ID is provided.
    """
    # Make the API request with an invalid customer ID
    response = requests.get(f"{REST_API_URL}/chat/history/invalid-customer-id")
    
    # Check for 502 Bad Gateway error (known issue)
    if response.status_code == 502:
        print("\n⚠️ WARNING: Received 502 Bad Gateway error from chat history endpoint.")
        print("This is a known issue with the current API deployment.")
        print("Please check the API logs for more information.")
        
        # Still fail the test, but with a more informative message
        assert False, "Chat history endpoint returned 502 Bad Gateway error (known issue)"
    
    # Verify response status code
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify error message
    assert "error" in data, "Response should contain 'error' key"
    assert "not found" in data["error"].lower(), "Error message should indicate customer not found"


def test_send_message(test_data):
    """
    Test the POST /chat endpoint.
    
    This test verifies that the endpoint processes a chat message
    and returns a response with the correct structure.
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Prepare request body
    message = "Hello, what can you do for me?"
    body = {
        "customerId": customer_id,
        "message": message
    }
    
    # Send the request
    response = requests.post(
        f"{REST_API_URL}/chat",
        json=body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if response.status_code == 502:
        print("\n⚠️ WARNING: Received 502 Bad Gateway error from chat endpoint.")
        print("This is a known issue with the current API deployment.")
        print("Please check the API logs for more information.")
        
        # Still fail the test, but with a more informative message
        assert False, "Chat endpoint returned 502 Bad Gateway error (known issue)"
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify response structure
    assert "message" in data, "Response should contain 'message' field"
    assert "id" in data, "Response should contain 'id' field"
    assert "timestamp" in data, "Response should contain 'timestamp' field"
    assert "customerId" in data, "Response should contain 'customerId' field"
    assert data["customerId"] == customer_id, f"customerId should be '{customer_id}'"


def test_send_message_invalid_customer():
    """
    Test the POST /chat endpoint with an invalid customer ID.
    
    This test verifies that the endpoint returns a 404 error when
    an invalid customer ID is provided.
    """
    # Prepare request body
    message = "Hello, what can you do for me?"
    body = {
        "customerId": "invalid-customer-id",
        "message": message
    }
    
    # Send the request
    response = requests.post(
        f"{REST_API_URL}/chat",
        json=body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if response.status_code == 502:
        print("\n⚠️ WARNING: Received 502 Bad Gateway error from chat endpoint.")
        print("This is a known issue with the current API deployment.")
        print("Please check the API logs for more information.")
        
        # Still fail the test, but with a more informative message
        assert False, "Chat endpoint returned 502 Bad Gateway error (known issue)"
    
    # Verify response status code
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify error message
    assert "error" in data, "Response should contain 'error' key"
    assert "not found" in data["error"].lower(), "Error message should indicate customer not found"


def test_send_message_missing_parameters():
    """
    Test the POST /chat endpoint with missing required parameters.
    
    This test verifies that the endpoint returns a 400 error when
    required parameters are missing.
    """
    # Prepare request body with missing customerId
    body = {
        "message": "Hello, what can you do for me?"
    }
    
    # Send the request
    response = requests.post(
        f"{REST_API_URL}/chat",
        json=body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if response.status_code == 502:
        print("\n⚠️ WARNING: Received 502 Bad Gateway error from chat endpoint.")
        print("This is a known issue with the current API deployment.")
        print("Please check the API logs for more information.")
        
        # Still fail the test, but with a more informative message
        assert False, "Chat endpoint returned 502 Bad Gateway error (known issue)"
    
    # Verify response status code
    assert response.status_code == 400, f"Expected status code 400, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify error message
    assert "error" in data, "Response should contain 'error' key"
    assert "message" in data["error"].lower(), "Error message should indicate missing message parameter" 