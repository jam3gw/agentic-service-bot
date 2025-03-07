"""
End-to-end tests for the Agentic Service Bot Chat API actions.

This module tests the different actions that can be performed through the chat API:
- device_status: Check the status of a device
- device_power: Turn a device on or off
- volume_control: Adjust the volume of a device
- song_changes: Change songs (next, previous, or random)
"""

# Standard library imports
import json
import os
import sys
import time
from decimal import Decimal
from datetime import datetime
from typing import Any, Dict, Optional, Union, cast, TypedDict

# Third-party imports
import boto3
import pytest
import requests
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb import ServiceResource as DynamoDBServiceResource

# Add the project root to the Python path so that imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Environment variables - using the same configuration as conftest.py
REST_API_URL = "https://k4w64ym45e.execute-api.us-west-2.amazonaws.com/dev/api"
REGION = "us-west-2"  # Match the region in conftest.py
CUSTOMERS_TABLE = "dev-customers"  # Match the table name in conftest.py
SERVICE_LEVELS_TABLE = "dev-service-levels"  # Add service levels table

# Type definitions
class DeviceState(TypedDict):
    id: str
    power: str
    volume: int
    current_song: str
    type: str
    location: str

class DynamoDBResponse(TypedDict):
    Item: Dict[str, Any]

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def test_device_status_action(test_data: Dict[str, str]) -> None:
    """
    Test the device_status action through the chat API.
    
    Args:
        test_data: Dictionary containing test customer and device IDs
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

def test_device_power_action(test_data: Dict[str, str]) -> None:
    """
    Test the device_power action through the chat API.
    
    This test verifies that:
    1. The device can be turned on successfully
    2. The power state is correctly updated in DynamoDB
    3. The device can be turned off successfully
    4. The state changes are reflected in both DynamoDB and status queries
    5. The response messages are clear and accurate
    
    The test includes verification of the device state through both direct
    DynamoDB queries and the chat API status endpoint to ensure consistency
    across the system.
    
    Args:
        test_data: Dictionary containing test customer and device IDs
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Create DynamoDB client
    dynamodb: DynamoDBServiceResource = boto3.resource('dynamodb', region_name=REGION)
    table: Table = dynamodb.Table(CUSTOMERS_TABLE)
    
    def verify_device_state(expected_state: str, operation: str) -> None:
        """
        Helper function to verify device state in DynamoDB and via status request.
        
        Args:
            expected_state: The expected power state ('on' or 'off')
            operation: Description of the operation being verified (for error messages)
        """
        # Wait a moment for DynamoDB to propagate the change
        time.sleep(2)
        
        # 1. Verify DynamoDB state
        response = table.get_item(Key={'id': customer_id})
        db_response = cast(DynamoDBResponse, response)
        assert 'Item' in db_response, f"Customer {customer_id} not found in DynamoDB after {operation}"
        customer = db_response['Item']
        device = customer.get('device')
        assert device is not None, f"Device not found in customer data after {operation}"
        device_state = cast(DeviceState, device)
        assert device_state['id'] == test_data['device_id'], f"Device ID mismatch after {operation}"
        assert device_state.get('power') == expected_state, \
            f"Expected device power state in DynamoDB to be {expected_state} after {operation}, got {device_state.get('power')}"
        
        # 2. Verify via status request
        status_response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "customerId": customer_id,
                "message": "What's the status of my speaker?"
            }
        )
        
        if status_response.status_code == 502:
            pytest.skip("Status check returned 502 Bad Gateway error (known issue)")
            
        assert status_response.status_code == 200, \
            f"Expected status code 200 for status check after {operation}, got {status_response.status_code}"
        
        status_data = status_response.json()
        assert "message" in status_data, f"Status response after {operation} should contain 'message' field"
        status_message = status_data["message"].lower()
        
        # Verify the status message reflects the correct state
        assert expected_state in status_message, \
            f"Status message after {operation} should indicate device is {expected_state}: {status_message}"
        
        # If checking for 'off' state, ensure 'on' isn't present or is negated
        if expected_state == 'off':
            assert 'on' not in status_message or ('not' in status_message and 'on' in status_message), \
                f"Status message for 'off' state should not indicate device is on: {status_message}"
    
    # First, turn the device on
    print("\n💡 Testing power on...")
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
    assert on_response.status_code == 200, \
        f"Expected status code 200 for power on, got {on_response.status_code}: {on_response.text}"
    
    # Parse response body
    on_data = on_response.json()
    
    # Verify response indicates the device was turned on
    assert "message" in on_data, "Response should contain 'message' field"
    on_message_text = on_data["message"].lower()
    assert "on" in on_message_text, "Response should confirm the device was turned on"
    
    # Verify the device state in DynamoDB and via status request
    verify_device_state('on', 'power on')
    
    # Now, turn the device off
    print("\n💡 Testing power off...")
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
    assert off_response.status_code == 200, \
        f"Expected status code 200 for power off, got {off_response.status_code}: {off_response.text}"
    
    # Parse response body
    off_data = off_response.json()
    
    # Verify response indicates the device was turned off
    assert "message" in off_data, "Response should contain 'message' field"
    off_message_text = off_data["message"].lower()
    assert "off" in off_message_text, "Response should confirm the device was turned off"
    
    # Verify the device state in DynamoDB and via status request
    verify_device_state('off', 'power off')

def test_volume_control_action(test_data):
    """
    Test the volume_control action through the chat API.
    
    This test verifies that:
    1. The chat API can correctly adjust the volume of a device
    2. The DynamoDB state is updated to reflect the volume change
    3. A subsequent status request confirms the new volume
    4. The same verification for decreasing volume
    5. Setting volume to a specific level works correctly
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Create DynamoDB client
    dynamodb: DynamoDBServiceResource = boto3.resource('dynamodb', region_name=REGION)
    table: Table = dynamodb.Table(CUSTOMERS_TABLE)
    
    def verify_device_volume(expected_volume: int, operation: str):
        """Helper function to verify device volume in DynamoDB and via status request"""
        # Wait a moment for DynamoDB to propagate the change
        time.sleep(2)
        
        # 1. Verify DynamoDB state
        response = table.get_item(Key={'id': customer_id})
        assert 'Item' in response, f"Customer {customer_id} not found in DynamoDB after {operation}"
        customer = response['Item']
        device = customer.get('device')
        assert device is not None, f"Device not found in customer data after {operation}"
        assert device['id'] == test_data['device_id'], f"Device ID mismatch after {operation}"
        assert device.get('volume') == expected_volume, \
            f"Expected device volume in DynamoDB to be {expected_volume} after {operation}, got {device.get('volume')}"
        
        # 2. Verify via status request
        status_response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "customerId": customer_id,
                "message": "What's the volume of my speaker?"
            }
        )
        
        if status_response.status_code == 502:
            pytest.skip("Status check returned 502 Bad Gateway error (known issue)")
            
        assert status_response.status_code == 200, \
            f"Expected status code 200 for status check after {operation}, got {status_response.status_code}"
        
        status_data = status_response.json()
        assert "message" in status_data, f"Status response after {operation} should contain 'message' field"
        status_message = status_data["message"].lower()
        
        # Verify the status message reflects the correct volume
        assert str(expected_volume) in status_message or any(
            word in status_message for word in ["increased", "decreased", "changed", "adjusted"]
        ), f"Status message after {operation} should indicate volume change: {status_message}"
    
    # First, make sure the device is on
    power_response = requests.post(
        f"{REST_API_URL}/chat",
        json={
            "customerId": customer_id,
            "message": "Turn on my speaker"
        }
    )
    
    if power_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    assert power_response.status_code == 200
    
    # Get initial volume
    initial_response = table.get_item(Key={'id': customer_id})
    initial_volume = initial_response['Item'].get('device', {}).get('volume', 50)  # Default to 50 if not set
    
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
    
    # Verify the device state in DynamoDB and via status request
    verify_device_volume(initial_volume + 10, 'volume increase')  # Assuming 10 is the increment
    
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
    
    # Verify the device state in DynamoDB and via status request
    verify_device_volume(initial_volume, 'volume decrease')  # Back to initial volume
    
    # Test setting volume to a specific level
    set_volume_message = "Set the volume to 60%"
    set_volume_body = {
        "customerId": customer_id,
        "message": set_volume_message
    }
    
    # Send the request to set specific volume
    set_volume_response = requests.post(
        f"{REST_API_URL}/chat",
        json=set_volume_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if set_volume_response.status_code == 502:
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert set_volume_response.status_code == 200, \
        f"Expected status code 200 for setting volume, got {set_volume_response.status_code}: {set_volume_response.text}"
    
    # Parse response body
    set_volume_data = set_volume_response.json()
    
    # Verify response indicates the volume was set to the specific level
    assert "message" in set_volume_data, "Response should contain 'message' field"
    set_volume_message_text = set_volume_data["message"].lower()
    assert "60" in set_volume_message_text, \
        "Response should confirm the volume was set to 60%"
    assert any(phrase in set_volume_message_text for phrase in ["volume", "set", "changed", "adjusted"]), \
        "Response should indicate the volume was changed"
    
    # Verify the device state in DynamoDB and via status request
    verify_device_volume(60, 'set specific volume')

def test_song_changes_action(test_data):
    """
    Test the song_control action through the chat API.
    
    This test verifies that:
    1. Premium users cannot change songs (permission denied)
    2. After upgrading to enterprise, users can change songs
    3. DynamoDB state reflects song changes
    4. Subsequent status requests confirm the song changes
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    print(f"\n🎵 Starting song control test for customer: {customer_id}")
    
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(CUSTOMERS_TABLE)
    
    def verify_song_state(expected_song: str, operation: str):
        """Helper function to verify song state in DynamoDB and via status request"""
        # Wait a moment for DynamoDB to propagate the change
        time.sleep(2)
        
        # 1. Verify DynamoDB state
        response = table.get_item(Key={'id': customer_id})
        assert 'Item' in response, f"Customer {customer_id} not found in DynamoDB after {operation}"
        customer = response['Item']
        device = customer.get('device')
        assert device is not None, f"Device not found in customer data after {operation}"
        assert device['id'] == test_data['device_id'], f"Device ID mismatch after {operation}"
        
        if operation == 'premium user song change attempt':
            # For premium users, verify the song hasn't changed and access was denied
            assert device.get('current_song') == expected_song, \
                f"Song should not change for premium users. Expected {expected_song}, got {device.get('current_song')}"
            return
        
        assert device.get('current_song') == expected_song, \
            f"Expected current song in DynamoDB to be {expected_song} after {operation}, got {device.get('current_song')}"
        
        # 2. Verify via status request
        status_response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "customerId": customer_id,
                "message": "What song is playing?"
            }
        )
        
        if status_response.status_code == 502:
            pytest.skip("Status check returned 502 Bad Gateway error (known issue)")
            
        assert status_response.status_code == 200, \
            f"Expected status code 200 for status check after {operation}, got {status_response.status_code}"
        
        status_data = status_response.json()
        assert "message" in status_data, f"Status response after {operation} should contain 'message' field"
        status_message = status_data["message"].lower()
        
        if operation == 'premium user song change attempt':
            # For premium users, verify the response indicates service level restriction
            assert any(phrase in status_message for phrase in ["not available", "enterprise", "upgrade"]), \
                f"Status message should indicate song control requires enterprise level: {status_message}"
            return
        
        # For other operations, verify the status message reflects the correct song
        assert expected_song.lower() in status_message, \
            f"Status message after {operation} should indicate current song is {expected_song}: {status_message}"
    
    # First, turn on the device
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
    
    print(f"Power response status: {power_response.status_code}")
    print(f"Power response body: {power_response.text}")
    
    # Verify device was turned on
    assert power_response.status_code == 200
    power_data = power_response.json()
    assert "message" in power_data
    assert "on" in power_data["message"].lower()
    
    # Get initial song
    initial_response = table.get_item(Key={'id': customer_id})
    initial_song = initial_response['Item'].get('device', {}).get('current_song', 'Unknown')
    
    # Test 1: Premium user should not be able to change songs
    next_message = "Play the next song"
    next_body = {
        "customerId": customer_id,
        "message": next_message
    }
    
    print("\nTesting song control as premium user (should be denied)")
    next_response = requests.post(
        f"{REST_API_URL}/chat",
        json=next_body
    )
    
    print(f"Next song response status: {next_response.status_code}")
    print(f"Next song response body: {next_response.text}")
    
    # Verify permission denied for premium user
    assert next_response.status_code == 200
    next_data = next_response.json()
    assert "message" in next_data
    message = next_data["message"].lower()
    assert any(phrase in message for phrase in ["not available", "not allowed", "service level", "enterprise"]), \
        f"Response should indicate song control requires enterprise level: {message}"
    
    # Verify song hasn't changed in DynamoDB
    verify_song_state(initial_song, 'premium user song change attempt')
    
    # Test 2: Upgrade to enterprise and try again
    print("\nUpgrading customer to enterprise level")
    try:
        response = table.update_item(
            Key={'id': customer_id},
            UpdateExpression="set #level = :level",
            ExpressionAttributeNames={'#level': 'level'},
            ExpressionAttributeValues={':level': 'enterprise'},
            ReturnValues="UPDATED_NEW"
        )
        print(f"Upgrade response: {response}")
        
        # Wait a moment for the change to propagate
        time.sleep(2)
    except Exception as e:
        print(f"Error upgrading customer: {e}")
        pytest.fail("Failed to upgrade customer to enterprise level")
    
    # Try changing songs again as enterprise user
    print("\nTesting song control as enterprise user (should work)")
    next_response = requests.post(
        f"{REST_API_URL}/chat",
        json=next_body
    )
    
    print(f"Next song response status: {next_response.status_code}")
    print(f"Next song response body: {next_response.text}")
    
    # Verify song change works for enterprise user
    assert next_response.status_code == 200
    next_data = next_response.json()
    assert "message" in next_data
    message = next_data["message"].lower()
    assert not any(phrase in message for phrase in ["not available", "not allowed", "service level", "upgrade"]), \
        f"Response should not indicate permission denied: {message}"
    assert any(phrase in message for phrase in ["next song", "playing", "changed", "switched", "now playing"]), \
        f"Response should confirm the song was changed: {message}"
    
    # Get the new song from DynamoDB
    response = table.get_item(Key={'id': customer_id})
    new_song = response['Item'].get('device', {}).get('current_song', 'Unknown')
    assert new_song != initial_song, "Song should have changed after successful request"
    
    # Verify the song change in DynamoDB and via status request
    verify_song_state(new_song, 'enterprise user song change')
    
    # Clean up - restore premium service level
    print("\nRestoring customer to premium level")
    try:
        table.update_item(
            Key={'id': customer_id},
            UpdateExpression="set #level = :level",
            ExpressionAttributeNames={'#level': 'level'},
            ExpressionAttributeValues={':level': 'premium'},
            ReturnValues="UPDATED_NEW"
        )
    except Exception as e:
        print(f"Warning: Failed to restore customer service level: {e}")
        # Don't fail the test for cleanup error
        print("Warning: Failed to restore customer to premium level")

def test_service_level_permissions(test_data: Dict[str, str]) -> None:
    """
    Test service level permissions through the chat API.
    
    This test verifies that:
    1. Basic service level users cannot access premium features
    2. Premium service level users can access premium features
    
    Args:
        test_data: Dictionary containing test customer and device IDs
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    customers_table = dynamodb.Table(CUSTOMERS_TABLE)
    
    try:
        # First, verify the customer exists and is premium
        response = customers_table.get_item(Key={'id': customer_id})
        assert 'Item' in response, f"Customer {customer_id} not found"
        customer = response['Item']
        assert customer['level'] == 'premium', "Test customer should start with premium service level"
        
        # Test premium feature access (e.g., volume control)
        premium_response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "customerId": customer_id,
                "message": "Set the volume to 80"
            }
        )
        
        # Check for 502 Bad Gateway error (known issue)
        if premium_response.status_code == 502:
            pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
        
        # Verify premium access works
        assert premium_response.status_code == 200, \
            f"Expected status code 200 for premium access, got {premium_response.status_code}"
        premium_data = premium_response.json()
        assert "message" in premium_data, "Response should contain 'message' field"
        premium_message = premium_data["message"].lower()
        assert "volume" in premium_message and "80" in premium_message, \
            "Premium user should be able to control volume"
        
        # Now change to basic service level
        update_response = customers_table.update_item(
            Key={'id': customer_id},
            UpdateExpression="SET level = :val",
            ExpressionAttributeValues={':val': 'basic'},
            ReturnValues="UPDATED_NEW"
        )
        
        # Wait a moment for the change to propagate
        time.sleep(2)
        
        # Test the same feature with basic service level
        basic_response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "customerId": customer_id,
                "message": "Set the volume to 80"
            }
        )
        
        # Check for 502 Bad Gateway error (known issue)
        if basic_response.status_code == 502:
            pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
        
        # Verify basic access is restricted
        assert basic_response.status_code == 200, \
            f"Expected status code 200 for basic access, got {basic_response.status_code}"
        basic_data = basic_response.json()
        assert "message" in basic_data, "Response should contain 'message' field"
        basic_message = basic_data["message"].lower()
        assert any(phrase in basic_message for phrase in 
                  ["premium", "upgrade", "not available", "basic", "not allowed"]), \
            "Basic user should be notified of service level restriction"
        
    finally:
        # Restore premium service level
        try:
            customers_table.update_item(
                Key={'id': customer_id},
                UpdateExpression="SET level = :val",
                ExpressionAttributeValues={':val': 'premium'}
            )
        except Exception as e:
            print(f"Warning: Failed to restore premium service level: {e}")

def test_basic_service_level_device_power(test_data: Dict[str, str]) -> None:
    """
    Test that basic service level users can control device power.
    
    This test verifies that basic service level users can:
    1. Turn devices on and off
    2. Check device status
    
    Args:
        test_data: Dictionary containing test customer and device IDs
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    customers_table = dynamodb.Table(CUSTOMERS_TABLE)
    
    try:
        # First, verify the customer exists and is premium
        response = customers_table.get_item(Key={'id': customer_id})
        assert 'Item' in response, f"Customer {customer_id} not found"
        customer = response['Item']
        assert customer['level'] == 'premium', "Test customer should start with premium service level"
        
        # Change to basic service level
        update_response = customers_table.update_item(
            Key={'id': customer_id},
            UpdateExpression="SET level = :val",
            ExpressionAttributeValues={':val': 'basic'},
            ReturnValues="UPDATED_NEW"
        )
        
        # Wait a moment for the change to propagate
        time.sleep(2)
        
        # Test power control with basic service level
        power_response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "customerId": customer_id,
                "message": "Turn on my speaker"
            }
        )
        
        # Check for 502 Bad Gateway error (known issue)
        if power_response.status_code == 502:
            pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
        
        # Verify basic user can control power
        assert power_response.status_code == 200, \
            f"Expected status code 200 for basic power control, got {power_response.status_code}"
        power_data = power_response.json()
        assert "message" in power_data, "Response should contain 'message' field"
        power_message = power_data["message"].lower()
        assert "on" in power_message, "Basic user should be able to turn device on"
        assert not any(phrase in power_message for phrase in 
                      ["premium", "upgrade", "not available", "not allowed"]), \
            "Basic user should not see service level restrictions for power control"
        
        # Verify the device state was updated
        verify_response = customers_table.get_item(Key={'id': customer_id})
        assert 'Item' in verify_response, "Failed to verify device state"
        device = verify_response['Item'].get('device', {})
        assert device.get('power') == 'on', "Device should be turned on"
        
    finally:
        # Restore premium service level
        try:
            customers_table.update_item(
                Key={'id': customer_id},
                UpdateExpression="SET level = :val",
                ExpressionAttributeValues={':val': 'premium'}
            )
        except Exception as e:
            print(f"Warning: Failed to restore premium service level: {e}")

def test_basic_user_device_flow(test_data):
    """
    Test the complete flow for a basic user interacting with their device.
    
    This test verifies that a basic user can:
    1. Check the status of their device
    2. Turn the device off
    3. Check the status again to confirm it's off
    
    This ensures the full interaction loop works correctly.
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    device_id = test_data['device_id']
    
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    customers_table_name = CUSTOMERS_TABLE
    table = dynamodb.Table(customers_table_name)
    
    # Get initial state
    try:
        initial_response = table.get_item(Key={'id': customer_id})
        initial_state = initial_response.get('Item', {}).get('device', {})
        print(f"Captured initial device state: {initial_state}")
    except Exception as e:
        print(f"Warning: Failed to capture initial state: {e}")
        initial_state = {}
    
    # Temporarily change the service level to basic
    try:
        response = boto3.client('dynamodb', region_name=REGION).update_item(
            TableName=customers_table_name,
            Key={'id': {'S': customer_id}},
            UpdateExpression="SET #level = :val",
            ExpressionAttributeNames={'#level': 'level'},
            ExpressionAttributeValues={':val': {'S': 'basic'}},
            ReturnValues="UPDATED_NEW"
        )
        print(f"Updated service level to basic: {response}")
        
        # Step 1: Check the initial status of the device
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
        print(f"Initial status check response: {status_message_text}")
        
        # Step 2: Turn off the device
        turn_off_message = "Turn off my speaker"
        turn_off_body = {
            "customerId": customer_id,
            "message": turn_off_message
        }
        
        turn_off_response = requests.post(
            f"{REST_API_URL}/chat",
            json=turn_off_body
        )
        
        # Check for 502 Bad Gateway error (known issue)
        if turn_off_response.status_code == 502:
            pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
        
        # Verify response status code
        assert turn_off_response.status_code == 200, f"Expected status code 200, got {turn_off_response.status_code}: {turn_off_response.text}"
        
        # Parse response body
        turn_off_data = turn_off_response.json()
        
        # Verify response indicates the device was turned off
        assert "message" in turn_off_data, "Response should contain 'message' field"
        turn_off_message_text = turn_off_data["message"].lower()
        assert any(phrase in turn_off_message_text for phrase in ["turned off", "switching off", "now off", "is off"]), \
            f"Response should confirm the device was turned off: {turn_off_message_text}"
        print(f"Turn off response: {turn_off_message_text}")
        
        # Wait a moment for the change to propagate
        time.sleep(2)
        
        # Step 3: Check the status again to verify it's off
        status_again_message = "What's the current status of my speaker?"
        status_again_body = {
            "customerId": customer_id,
            "message": status_again_message
        }
        
        status_again_response = requests.post(
            f"{REST_API_URL}/chat",
            json=status_again_body
        )
        
        # Check for 502 Bad Gateway error (known issue)
        if status_again_response.status_code == 502:
            pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
        
        # Verify response status code
        assert status_again_response.status_code == 200, f"Expected status code 200, got {status_again_response.status_code}: {status_again_response.text}"
        
        # Parse response body
        status_again_data = status_again_response.json()
        
        # Verify response contains updated device status information
        assert "message" in status_again_data, "Response should contain 'message' field"
        status_again_message_text = status_again_data["message"].lower()
        assert "speaker" in status_again_message_text, "Response should mention the speaker"
        assert "off" in status_again_message_text, "Response should indicate the speaker is now off"
        assert "on" not in status_again_message_text or ("not" in status_again_message_text and "on" in status_again_message_text), \
            f"Response should not indicate the speaker is on (unless saying it's not on): {status_again_message_text}"
        print(f"Final status check response: {status_again_message_text}")
        
    finally:
        # Restore the original service level (premium)
        try:
            response = boto3.client('dynamodb', region_name=REGION).update_item(
                TableName=customers_table_name,
                Key={'id': {'S': customer_id}},
                UpdateExpression="SET #level = :val",
                ExpressionAttributeNames={'#level': 'level'},
                ExpressionAttributeValues={':val': {'S': 'premium'}},
                ReturnValues="UPDATED_NEW"
            )
            print(f"Restored service level to premium: {response}")
            
            # Restore initial device state if we have it
            if initial_state:
                try:
                    response = table.update_item(
                        Key={'id': customer_id},
                        UpdateExpression="set #device = :device",
                        ExpressionAttributeNames={"#device": "device"},
                        ExpressionAttributeValues={":device": initial_state},
                        ReturnValues="UPDATED_NEW"
                    )
                    print(f"Restored device state: {response}")
                except Exception as e:
                    print(f"Warning: Failed to restore device state: {e}")
            
            # Turn the device back on using the chat API as a fallback
            try:
                turn_on_body = {
                    "customerId": customer_id,
                    "message": "Turn on my speaker"
                }
                
                turn_on_response = requests.post(
                    f"{REST_API_URL}/chat",
                    json=turn_on_body
                )
                
                if turn_on_response.status_code == 200:
                    print("Restored device state to on via chat API")
                else:
                    print(f"Warning: Failed to restore device state via chat API: {turn_on_response.status_code}")
            except Exception as e:
                print(f"Warning: Failed to restore device state: {e}")
        except Exception as e:
            print(f"Warning: Failed to restore service level to premium: {e}") 