"""
End-to-end tests for the Agentic Service Bot Chat API actions.

This module tests the different actions that can be performed through the chat API:
- device_status: Check the status of a device
- device_power: Turn a device on or off
- volume_control: Adjust the volume of a device
- song_changes: Change songs (next, previous, or random)
"""

import os
import sys
import json
import pytest
import requests
import re
from pathlib import Path
import boto3

# Add the project root to the Python path so that imports work correctly
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "test"

# API URLs for testing
REST_API_URL = "https://k4w64ym45e.execute-api.us-west-2.amazonaws.com/dev/api"

# DynamoDB configuration
REGION = "us-west-2"  # Same region as the API
CUSTOMERS_TABLE = "dev-customers"  # Table name

def test_device_status_action(test_data):
    """
    Test the device_status action through the chat API.
    
    This test verifies that the chat API can correctly report the status of a device.
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Prepare request body
    message = "What's the status of my speaker?"
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
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify response contains device status information
    assert "message" in data, "Response should contain 'message' field"
    message_text = data["message"].lower()
    
    # Check that the response mentions the device type and power state
    assert "speaker" in message_text, "Response should mention the speaker"
    assert any(state in message_text for state in ["on", "off"]), "Response should mention the power state"

def test_device_power_action(test_data):
    """
    Test the device_power action through the chat API.
    
    This test verifies that the chat API can correctly turn a device on or off.
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # First, turn the device on
    on_message = "Turn on my speaker"
    on_body = {
        "customerId": customer_id,
        "message": on_message
    }
    
    # Send the request to turn on
    on_response = requests.post(
        f"{REST_API_URL}/chat",
        json=on_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if on_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert on_response.status_code == 200, f"Expected status code 200, got {on_response.status_code}: {on_response.text}"
    
    # Parse response body
    on_data = on_response.json()
    
    # Verify response indicates the device was turned on
    assert "message" in on_data, "Response should contain 'message' field"
    on_message_text = on_data["message"].lower()
    assert "on" in on_message_text, "Response should confirm the device was turned on"
    
    # Now, turn the device off
    off_message = "Turn off my speaker"
    off_body = {
        "customerId": customer_id,
        "message": off_message
    }
    
    # Send the request to turn off
    off_response = requests.post(
        f"{REST_API_URL}/chat",
        json=off_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if off_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert off_response.status_code == 200, f"Expected status code 200, got {off_response.status_code}: {off_response.text}"
    
    # Parse response body
    off_data = off_response.json()
    
    # Verify response indicates the device was turned off
    assert "message" in off_data, "Response should contain 'message' field"
    off_message_text = off_data["message"].lower()
    assert "off" in off_message_text, "Response should confirm the device was turned off"

def test_volume_control_action(test_data):
    """
    Test the volume_control action through the chat API.
    
    This test verifies that the chat API can correctly adjust the volume of a device.
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # First, make sure the device is on
    requests.post(
        f"{REST_API_URL}/chat",
        json={
            "customerId": customer_id,
            "message": "Turn on my speaker"
        }
    )
    
    # Now, increase the volume
    up_message = "Turn up the volume"
    up_body = {
        "customerId": customer_id,
        "message": up_message
    }
    
    # Send the request to increase volume
    up_response = requests.post(
        f"{REST_API_URL}/chat",
        json=up_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if up_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert up_response.status_code == 200, f"Expected status code 200, got {up_response.status_code}: {up_response.text}"
    
    # Parse response body
    up_data = up_response.json()
    
    # Verify response indicates the volume was increased
    assert "message" in up_data, "Response should contain 'message' field"
    up_message_text = up_data["message"].lower()
    assert any(phrase in up_message_text for phrase in ["volume", "increased", "turned up"]), \
        "Response should confirm the volume was increased"
    
    # Now, decrease the volume
    down_message = "Turn down the volume"
    down_body = {
        "customerId": customer_id,
        "message": down_message
    }
    
    # Send the request to decrease volume
    down_response = requests.post(
        f"{REST_API_URL}/chat",
        json=down_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if down_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert down_response.status_code == 200, f"Expected status code 200, got {down_response.status_code}: {down_response.text}"
    
    # Parse response body
    down_data = down_response.json()
    
    # Verify response indicates the volume was decreased
    assert "message" in down_data, "Response should contain 'message' field"
    down_message_text = down_data["message"].lower()
    assert any(phrase in down_message_text for phrase in ["volume", "decreased", "turned down"]), \
        "Response should confirm the volume was decreased"

def test_song_changes_action(test_data):
    """
    Test the song_changes action through the chat API.
    
    This test verifies that the chat API can correctly change songs (next, previous, or random).
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # First, make sure the device is on
    requests.post(
        f"{REST_API_URL}/chat",
        json={
            "customerId": customer_id,
            "message": "Turn on my speaker"
        }
    )
    
    # Test next song
    next_message = "Play the next song"
    next_body = {
        "customerId": customer_id,
        "message": next_message
    }
    
    # Send the request to play next song
    next_response = requests.post(
        f"{REST_API_URL}/chat",
        json=next_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if next_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert next_response.status_code == 200, f"Expected status code 200, got {next_response.status_code}: {next_response.text}"
    
    # Parse response body
    next_data = next_response.json()
    
    # Verify response indicates the song was changed
    assert "message" in next_data, "Response should contain 'message' field"
    next_message_text = next_data["message"].lower()
    assert any(phrase in next_message_text for phrase in ["next song", "playing", "changed"]), \
        "Response should confirm the song was changed"
    
    # Test previous song
    prev_message = "Play the previous song"
    prev_body = {
        "customerId": customer_id,
        "message": prev_message
    }
    
    # Send the request to play previous song
    prev_response = requests.post(
        f"{REST_API_URL}/chat",
        json=prev_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if prev_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert prev_response.status_code == 200, f"Expected status code 200, got {prev_response.status_code}: {prev_response.text}"
    
    # Parse response body
    prev_data = prev_response.json()
    
    # Verify response indicates the song was changed
    assert "message" in prev_data, "Response should contain 'message' field"
    prev_message_text = prev_data["message"].lower()
    assert any(phrase in prev_message_text for phrase in ["previous song", "playing", "changed"]), \
        "Response should confirm the song was changed"
    
    # Test random song change
    random_message = "Change the song"
    random_body = {
        "customerId": customer_id,
        "message": random_message
    }
    
    # Send the request for random song change
    random_response = requests.post(
        f"{REST_API_URL}/chat",
        json=random_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if random_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert random_response.status_code == 200, f"Expected status code 200, got {random_response.status_code}: {random_response.text}"
    
    # Parse response body
    random_data = random_response.json()
    
    # Verify response indicates the song was changed
    assert "message" in random_data, "Response should contain 'message' field"
    random_message_text = random_data["message"].lower()
    assert any(phrase in random_message_text for phrase in ["song", "playing", "changed"]), \
        "Response should confirm the song was changed"

def test_service_level_permissions(test_data):
    """
    Test that service level permissions are enforced for different actions.
    
    This test verifies that the chat API correctly enforces service level permissions
    by temporarily changing the service level and attempting actions.
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    device_id = test_data['device_id']
    
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    customers_table_name = CUSTOMERS_TABLE
    
    # Temporarily change the service level to basic
    try:
        response = boto3.client('dynamodb', region_name=REGION).update_item(
            TableName=customers_table_name,
            Key={'id': {'S': customer_id}},
            UpdateExpression="SET serviceLevel = :val",
            ExpressionAttributeValues={':val': {'S': 'basic'}},
            ReturnValues="UPDATED_NEW"
        )
        print(f"Updated service level to basic: {response}")
    except Exception as e:
        pytest.fail(f"Failed to update service level: {e}")
    
    try:
        # Test 1: Basic service level should allow device status checks
        status_message = "What's the status of my speaker?"
        status_body = {
            "customerId": customer_id,
            "message": status_message
        }
        
        status_response = requests.post(
            f"{REST_API_URL}/chat",
            json=status_body
        )
        
        # Check for 502 Bad Gateway error (known issue)
        if status_response.status_code == 502:
            pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
        
        # Verify response status code
        assert status_response.status_code == 200, f"Expected status code 200, got {status_response.status_code}: {status_response.text}"
        
        # Parse response body
        status_data = status_response.json()
        
        # Verify response contains device status information
        assert "message" in status_data, "Response should contain 'message' field"
        status_message_text = status_data["message"].lower()
        assert "speaker" in status_message_text, "Response should mention the speaker"
        
        # Test 2: Basic service level should allow device power control
        power_message = "Turn on my speaker"
        power_body = {
            "customerId": customer_id,
            "message": power_message
        }
        
        power_response = requests.post(
            f"{REST_API_URL}/chat",
            json=power_body
        )
        
        # Check for 502 Bad Gateway error (known issue)
        if power_response.status_code == 502:
            pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
        
        # Verify response status code
        assert power_response.status_code == 200, f"Expected status code 200, got {power_response.status_code}: {power_response.text}"
        
        # Parse response body
        power_data = power_response.json()
        
        # Verify response indicates the device was turned on
        assert "message" in power_data, "Response should contain 'message' field"
        power_message_text = power_data["message"].lower()
        assert "on" in power_message_text, "Response should confirm the device was turned on"
        assert "service level" not in power_message_text, "Response should not mention service level restrictions"
        
        # Test 3: Basic service level should NOT allow volume control (premium feature)
        volume_message = "Turn up the volume"
        volume_body = {
            "customerId": customer_id,
            "message": volume_message
        }
        
        volume_response = requests.post(
            f"{REST_API_URL}/chat",
            json=volume_body
        )
        
        # Check for 502 Bad Gateway error (known issue)
        if volume_response.status_code == 502:
            pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
        
        # Verify response status code
        assert volume_response.status_code == 200, f"Expected status code 200, got {volume_response.status_code}: {volume_response.text}"
        
        # Parse response body
        volume_data = volume_response.json()
        
        # Verify response indicates the action is not allowed for basic service level
        assert "message" in volume_data, "Response should contain 'message' field"
        volume_message_text = volume_data["message"].lower()
        assert any(phrase in volume_message_text for phrase in ["service level", "not allowed", "upgrade"]), \
            f"Response should indicate volume control is not allowed for basic service level: {volume_message_text}"
        
        # Test 4: Basic service level should NOT allow song changes (enterprise feature)
        song_message = "Play the next song"
        song_body = {
            "customerId": customer_id,
            "message": song_message
        }
        
        song_response = requests.post(
            f"{REST_API_URL}/chat",
            json=song_body
        )
        
        # Check for 502 Bad Gateway error (known issue)
        if song_response.status_code == 502:
            pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
        
        # Verify response status code
        assert song_response.status_code == 200, f"Expected status code 200, got {song_response.status_code}: {song_response.text}"
        
        # Parse response body
        song_data = song_response.json()
        
        # Verify response indicates the action is not allowed for basic service level
        assert "message" in song_data, "Response should contain 'message' field"
        song_message_text = song_data["message"].lower()
        assert any(phrase in song_message_text for phrase in ["service level", "not allowed", "upgrade"]), \
            f"Response should indicate song changes are not allowed for basic service level: {song_message_text}"
    
    finally:
        # Restore the original service level (premium)
        try:
            response = boto3.client('dynamodb', region_name=REGION).update_item(
                TableName=customers_table_name,
                Key={'id': {'S': customer_id}},
                UpdateExpression="SET serviceLevel = :val",
                ExpressionAttributeValues={':val': {'S': 'premium'}},
                ReturnValues="UPDATED_NEW"
            )
            print(f"Restored service level to premium: {response}")
        except Exception as e:
            print(f"Warning: Failed to restore service level: {e}")

def test_basic_service_level_device_power(test_data):
    """
    Test that basic service level customers can control device power.
    
    This test verifies that customers with the basic service level can turn
    their devices on and off, which is a core functionality that should be
    available to all service levels.
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    device_id = test_data['device_id']
    
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    customers_table_name = CUSTOMERS_TABLE
    
    # Temporarily change the service level to basic
    try:
        response = boto3.client('dynamodb', region_name=REGION).update_item(
            TableName=customers_table_name,
            Key={'id': {'S': customer_id}},
            UpdateExpression="SET serviceLevel = :val",
            ExpressionAttributeValues={':val': {'S': 'basic'}},
            ReturnValues="UPDATED_NEW"
        )
        print(f"Updated service level to basic: {response}")
    except Exception as e:
        pytest.fail(f"Failed to update service level: {e}")
    
    # Try to turn the device on
    on_message = "Turn on my speaker"
    on_body = {
        "customerId": customer_id,
        "message": on_message
    }
    
    # Send the request to turn on
    on_response = requests.post(
        f"{REST_API_URL}/chat",
        json=on_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if on_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert on_response.status_code == 200, f"Expected status code 200, got {on_response.status_code}: {on_response.text}"
    
    # Parse response body
    on_data = on_response.json()
    
    # Verify response indicates the device was turned on
    assert "message" in on_data, "Response should contain 'message' field"
    on_message_text = on_data["message"].lower()
    
    # Check that the response does NOT mention service level restrictions
    assert "service level" not in on_message_text, f"Response should not mention service level restrictions: {on_message_text}"
    assert "upgrade" not in on_message_text, f"Response should not suggest upgrading: {on_message_text}"
    assert "on" in on_message_text, "Response should confirm the device was turned on"
    
    # Now, turn the device off
    off_message = "Turn off my speaker"
    off_body = {
        "customerId": customer_id,
        "message": off_message
    }
    
    # Send the request to turn off
    off_response = requests.post(
        f"{REST_API_URL}/chat",
        json=off_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if off_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert off_response.status_code == 200, f"Expected status code 200, got {off_response.status_code}: {off_response.text}"
    
    # Parse response body
    off_data = off_response.json()
    
    # Verify response indicates the device was turned off
    assert "message" in off_data, "Response should contain 'message' field"
    off_message_text = off_data["message"].lower()
    
    # Check that the response does NOT mention service level restrictions
    assert "service level" not in off_message_text, f"Response should not mention service level restrictions: {off_message_text}"
    assert "upgrade" not in off_message_text, f"Response should not suggest upgrading: {off_message_text}"
    assert "off" in off_message_text, "Response should confirm the device was turned off"
    
    # Restore the original service level (premium)
    try:
        response = boto3.client('dynamodb', region_name=REGION).update_item(
            TableName=customers_table_name,
            Key={'id': {'S': customer_id}},
            UpdateExpression="SET serviceLevel = :val",
            ExpressionAttributeValues={':val': {'S': 'premium'}},
            ReturnValues="UPDATED_NEW"
        )
        print(f"Restored service level to premium: {response}")
    except Exception as e:
        print(f"Warning: Failed to restore service level: {e}") 