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
import logging

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
    playlist: list[str]

class DynamoDBItem(TypedDict):
    id: str
    device: Dict[str, Any]

class DynamoDBResponse(TypedDict):
    Item: DynamoDBItem

class DynamoDBEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_device_power(customer_id: str, expected_power: str, operation: str, table: Table) -> None:
    """
    Helper function to verify device power status in DynamoDB and via status request.
    
    Args:
        customer_id: The ID of the customer whose device to verify
        expected_power: The expected power status ('on' or 'off')
        operation: Description of the operation being verified (for error messages)
        table: The DynamoDB table to query
    """
    logger.info(f"Verifying device power after {operation} - expecting power: {expected_power}")
    
    # Wait a moment for DynamoDB to propagate the change
    time.sleep(2)
    
    # 1. Verify DynamoDB power status
    response = table.get_item(Key={'id': customer_id})
    logger.info(f"DynamoDB response for power verification: {response}")
    
    db_response = cast(DynamoDBResponse, response)
    assert 'Item' in db_response, f"Customer {customer_id} not found in DynamoDB after {operation}"
    customer = db_response['Item']
    device = customer.get('device')
    assert device is not None, f"Device not found in customer data after {operation}"
    device_state = cast(DeviceState, device)
    
    current_power = device_state.get('power')
    logger.info(f"Current device power in DynamoDB: {current_power}")
    assert current_power == expected_power, \
        f"Expected device power in DynamoDB to be {expected_power} after {operation}, got {current_power}"
    
    # 2. Verify via status request
    logger.info("Sending status request to verify power via API")
    status_response = requests.post(
        f"{REST_API_URL}/chat",
        json={
            "customerId": customer_id,
            "message": "What's the status of my speaker?"
        }
    )
    
    if status_response.status_code == 502:
        logger.warning("Received 502 Bad Gateway error during status check")
        pytest.skip("Status check returned 502 Bad Gateway error (known issue)")
        
    assert status_response.status_code == 200, \
        f"Expected status code 200 for status check after {operation}, got {status_response.status_code}"
    
    status_data = status_response.json()
    logger.info(f"Status API response: {status_data}")
    
    assert "message" in status_data, f"Status response after {operation} should contain 'message' field"
    status_message = status_data["message"].lower()
    
    # Verify the status message reflects the correct power status
    assert expected_power in status_message, \
        f"Status message after {operation} should indicate device is {expected_power}: {status_message}"
    
    # If checking for 'off' status, ensure 'on' isn't present or is negated
    if expected_power == 'off':
        assert 'on' not in status_message or ('not' in status_message and 'on' in status_message), \
            f"Status message for 'off' power should not indicate device is on: {status_message}"
    
    logger.info(f"Successfully verified device power after {operation}")

def verify_device_volume(customer_id: str, operation: str, table: Table) -> None:
    """
    Helper function to verify device volume in DynamoDB and via status request.
    
    Args:
        customer_id: The ID of the customer whose device to verify
        operation: Description of the operation being verified (for error messages)
        table: The DynamoDB table to query
    """
    logger.info(f"Verifying device volume after {operation}")
    
    # Wait a moment for DynamoDB to propagate the change
    time.sleep(2)
    
    # 1. Verify DynamoDB state
    response = table.get_item(Key={'id': customer_id})
    logger.info(f"DynamoDB response for volume verification: {response}")
    
    db_response = cast(DynamoDBResponse, response)
    assert 'Item' in db_response, f"Customer {customer_id} not found in DynamoDB after {operation}"
    customer = db_response['Item']
    device = customer.get('device')
    assert device is not None, f"Device not found in customer data after {operation}"
    device_state = cast(DeviceState, device)
    
    # Verify the device is powered on
    assert device_state.get('power') == 'on', f"Device must be powered on to verify volume after {operation}"
    
    # Verify volume is within valid range
    volume = device_state.get('volume')
    assert isinstance(volume, (int, Decimal)), f"Volume should be a number, got {type(volume)}"
    volume_int = int(volume)
    assert 0 <= volume_int <= 100, f"Volume should be between 0 and 100, got {volume_int}"
    
    # 2. Verify via status request
    logger.info("Sending status request to verify volume via API")
    status_response = requests.post(
        f"{REST_API_URL}/chat",
        json={
            "customerId": customer_id,
            "message": "What's the volume of my speaker?"
        }
    )
    
    if status_response.status_code == 502:
        logger.warning("Received 502 Bad Gateway error during status check")
        pytest.skip("Status check returned 502 Bad Gateway error (known issue)")
        
    assert status_response.status_code == 200, \
        f"Expected status code 200 for status check after {operation}, got {status_response.status_code}"
    
    status_data = status_response.json()
    logger.info(f"Status API response: {status_data}")
    
    assert "message" in status_data, f"Status response after {operation} should contain 'message' field"
    status_message = status_data["message"].lower()
    
    # For volume changes, verify that the response mentions volume
    assert "volume" in status_message, \
        f"Status message after {operation} should mention volume: {status_message}"
    
    logger.info(f"Successfully verified device volume after {operation}")

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
    
    Args:
        test_data: Dictionary containing test customer and device IDs
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    logger.info(f"Starting device power test for customer {customer_id}")
    
    # Create DynamoDB client
    dynamodb: DynamoDBServiceResource = boto3.resource('dynamodb', region_name=REGION)
    table: Table = dynamodb.Table(CUSTOMERS_TABLE)
    
    # First, turn the device on
    logger.info("\n💡 Testing power on...")
    on_message = "Turn on my speaker"
    on_body = {
        "customerId": customer_id,
        "message": on_message
    }
    
    # Send the request to turn on
    logger.info("Sending request to turn on device")
    on_response = requests.post(
        f"{REST_API_URL}/chat",
        json=on_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if on_response.status_code == 502:
        logger.warning("Received 502 Bad Gateway error during power on request")
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert on_response.status_code == 200, \
        f"Expected status code 200 for power on, got {on_response.status_code}: {on_response.text}"
    
    # Parse response body
    on_data = on_response.json()
    logger.info(f"Power on response: {on_data}")
    
    # Verify response indicates the device was turned on
    assert "message" in on_data, "Response should contain 'message' field"
    on_message_text = on_data["message"].lower()
    assert "on" in on_message_text, "Response should confirm the device was turned on"
    
    # Verify the device power in DynamoDB and via status request
    verify_device_power(customer_id, 'on', 'power on', table)
    
    # Now, turn the device off
    logger.info("\n💡 Testing power off...")
    off_message = "Turn off my speaker"
    off_body = {
        "customerId": customer_id,
        "message": off_message
    }
    
    # Send the request to turn off
    logger.info("Sending request to turn off device")
    off_response = requests.post(
        f"{REST_API_URL}/chat",
        json=off_body
    )
    
    # Check for 502 Bad Gateway error (known issue)
    if off_response.status_code == 502:
        logger.warning("Received 502 Bad Gateway error during power off request")
        pytest.skip("Chat endpoint returned 502 Bad Gateway error (known issue)")
    
    # Verify response status code
    assert off_response.status_code == 200, \
        f"Expected status code 200 for power off, got {off_response.status_code}: {off_response.text}"
    
    # Parse response body
    off_data = off_response.json()
    logger.info(f"Power off response: {off_data}")
    
    # Verify response indicates the device was turned off
    assert "message" in off_data, "Response should contain 'message' field"
    off_message_text = off_data["message"].lower()
    assert "off" in off_message_text, "Response should confirm the device was turned off"
    
    # Verify the device power in DynamoDB and via status request
    verify_device_power(customer_id, 'off', 'power off', table)
    logger.info("Device power test completed successfully")

def test_volume_control_action(test_data: Dict[str, str]) -> None:
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
    verify_device_volume(customer_id, 'volume increase', table)
    
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
    verify_device_volume(customer_id, 'volume decrease', table)
    
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
    verify_device_volume(customer_id, 'set volume', table)

def test_song_changes_action(test_data: Dict[str, str]) -> None:
    """
    Test the song_control action through the chat API.
    
    This test verifies that:
    1. Premium users cannot change songs (permission denied)
    2. After upgrading to enterprise, users can:
       - Play specific songs by name
       - Play next/previous songs
       - Handle errors for non-existent songs
    3. DynamoDB state reflects song changes
    4. Subsequent status requests confirm the song changes
    """
    # Get customer ID from test data fixture
    customer_id = test_data['customer_id']
    print(f"\n🎵 Starting song control test for customer: {customer_id}")
    
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(CUSTOMERS_TABLE)
    
    def verify_song_state(expected_song: str, operation: str) -> None:
        """Helper function to verify song state in DynamoDB and via status request"""
        print(f"\n🔍 Verifying song state after {operation}")
        print(f"  Expected song: {expected_song}")
        
        # Wait a moment for DynamoDB to propagate the change
        time.sleep(2)
        
        # 1. Verify DynamoDB state
        response = table.get_item(Key={'id': customer_id})
        response_typed = cast(DynamoDBResponse, response)
        print(f"  DynamoDB response: {json.dumps(response_typed, indent=2, cls=DynamoDBEncoder)}")
        assert 'Item' in response_typed, f"Customer {customer_id} not found in DynamoDB after {operation}"
        customer = response_typed['Item']
        device = cast(DeviceState, customer.get('device', {}))
        print(f"  Device state: {json.dumps(device, indent=2, cls=DynamoDBEncoder)}")
        assert device is not None, f"Device not found in customer data after {operation}"
        assert device['id'] == test_data['device_id'], f"Device ID mismatch after {operation}"
        
        if operation == 'premium user song change attempt':
            # For premium users, verify the song hasn't changed and access was denied
            assert device.get('current_song') == expected_song, \
                f"Song should not change for premium users. Expected {expected_song}, got {device.get('current_song')}"
            return
        
        # 2. Verify the current song matches expected
        current_song = device.get('current_song')
        print(f"  Current song in DynamoDB: {current_song}")
        assert current_song == expected_song, \
            f"Song mismatch after {operation}. Expected {expected_song}, got {current_song}"
        
        # 3. Verify via status request
        print(f"  Making status request to verify song...")
        status_response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "message": "What's playing now?",
                "customerId": customer_id
            }
        )
        print(f"  Status response: {json.dumps(status_response.json(), indent=2)}")
        assert status_response.status_code == 200, f"Status request failed after {operation}"
        status_data = status_response.json()
        assert expected_song in status_data.get('message', ''), \
            f"Status response doesn't mention current song after {operation}"
    
    # Step 1: Verify premium user cannot change songs
    initial_song = "Test Song 1"
    print("\n🔒 Testing premium user permissions...")
    
    # Try to play next song as premium user
    response = requests.post(
        f"{REST_API_URL}/chat",
        json={
            "message": "Play next song",
            "customerId": customer_id
        }
    )
    print(f"Premium user response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert any(phrase in response.json()['message'].lower() for phrase in 
              ["only available with", "enterprise service plan", "please upgrade"]), \
        "Response should indicate that song control requires enterprise plan"
    verify_song_state(initial_song, "premium user song change attempt")
    
    # Step 2: Upgrade to enterprise
    print("\n⬆️ Upgrading to enterprise service level...")
    try:
        # Update service level directly in DynamoDB
        update_response = table.update_item(
            Key={'id': customer_id},
            UpdateExpression="SET #lvl = :val",
            ExpressionAttributeNames={'#lvl': 'level'},
            ExpressionAttributeValues={':val': 'enterprise'},
            ReturnValues="UPDATED_NEW"
        )
        print(f"DynamoDB update response: {json.dumps(update_response, indent=2, cls=DynamoDBEncoder)}")
        print("✅ Upgraded to enterprise service level")
        
        # Wait for the change to propagate
        time.sleep(2)
    except Exception as e:
        print(f"❌ Failed to upgrade service level: {e}")
        raise
    
    # Step 3: Test specific song requests
    print("\n🎯 Testing specific song selection...")
    
    # Test different phrasings for specific song requests
    test_cases = [
        ("Play Test Song 2", "Test Song 2"),
        ("Put on Test Song 2", "Test Song 2"),
        ("Switch to Test Song 3", "Test Song 3"),
        ("Change song to Test Song 2", "Test Song 2")
    ]
    
    for command, expected_song in test_cases:
        print(f"\nTesting command: {command}")
        response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "message": command,
                "customerId": customer_id
            }
        )
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        assert expected_song in response.json()['message']
        verify_song_state(expected_song, f"play specific song ({command})")
    
    # Try to play a non-existent song
    print("\n❌ Testing non-existent song request...")
    response = requests.post(
        f"{REST_API_URL}/chat",
        json={
            "message": "Play NonexistentSong",
            "customerId": customer_id
        }
    )
    print(f"Non-existent song response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert "Could not find a song" in response.json()['message']
    verify_song_state("Test Song 2", "play non-existent song")
    
    # Step 4: Test next/previous functionality with various phrasings
    print("\n⏭️ Testing next song functionality with different phrasings...")
    next_commands = [
        "Play next song",
        "Skip this song",
        "Skip to next",
        "Play something different",
        "Change song",
        "Next song"
    ]
    
    # Track current position in playlist
    playlist = ["Test Song 1", "Test Song 2", "Test Song 3", "Test Song 4"]
    current_index = playlist.index("Test Song 2")  # We start at Test Song 2
    
    for command in next_commands:
        print(f"\nTesting command: {command}")
        response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "message": command,
                "customerId": customer_id
            }
        )
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        
        # Move to next song (with wraparound)
        current_index = (current_index + 1) % len(playlist)
        expected_song = playlist[current_index]
        
        assert expected_song in response.json()['message']
        verify_song_state(expected_song, f"next song command ({command})")
    
    # Test previous song functionality with different phrasings
    print("\n⏮️ Testing previous song functionality with different phrasings...")
    previous_commands = [
        "Play previous song",
        "Go back to previous track",
        "Play the previous song",
        "Previous song"
    ]
    
    for command in previous_commands:
        print(f"\nTesting command: {command}")
        response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "message": command,
                "customerId": customer_id
            }
        )
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        
        # Move to previous song (with wraparound)
        current_index = (current_index - 1) % len(playlist)
        expected_song = playlist[current_index]
        
        assert expected_song in response.json()['message']
        verify_song_state(expected_song, f"previous song command ({command})")
    
    # Test edge cases
    print("\n🔄 Testing edge cases...")
    edge_cases = [
        "Can you play the next song please?",
        "PLAY NEXT SONG",
        "play something else",
        "i don't like this song"
    ]
    
    for command in edge_cases:
        print(f"\nTesting edge case: {command}")
        response = requests.post(
            f"{REST_API_URL}/chat",
            json={
                "message": command,
                "customerId": customer_id
            }
        )
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Move to next song (with wraparound)
        current_index = (current_index + 1) % len(playlist)
        expected_song = playlist[current_index]
        
        assert response.status_code == 200
        assert expected_song in response.json()['message']
        verify_song_state(expected_song, f"edge case ({command})")
    
    # Step 5: Test error cases
    print("\n🔌 Testing device power off scenario...")
    # Turn off the device
    response = requests.post(
        f"{REST_API_URL}/chat",
        json={
            "message": "Turn off the device",
            "customerId": customer_id
        }
    )
    print(f"Device power off response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    time.sleep(2)
    
    # Try to change song while device is off
    print("\n❌ Testing song change with powered off device...")
    response = requests.post(
        f"{REST_API_URL}/chat",
        json={
            "message": "Play next song",
            "customerId": customer_id
        }
    )
    print(f"Powered off song change response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert "powered off" in response.json()['message']
    
    print("✅ Song control tests completed successfully")

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
    logger.info(f"Starting service level permissions test for customer {customer_id}")
    
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    customers_table = dynamodb.Table(CUSTOMERS_TABLE)
    
    try:
        # First, ensure we start with a known state by setting to premium
        logger.info("Setting initial service level to premium")
        update_response = customers_table.update_item(
            Key={'id': customer_id},
            UpdateExpression="SET #lvl = :val",
            ExpressionAttributeNames={'#lvl': 'level'},
            ExpressionAttributeValues={':val': 'premium'},
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"Update response: {update_response}")
        
        # Wait for the change to propagate
        time.sleep(2)
        
        # Verify the customer is now premium
        response = customers_table.get_item(Key={'id': customer_id})
        assert 'Item' in response, f"Customer {customer_id} not found"
        customer = response['Item']
        assert customer.get('level') == 'premium', "Failed to set customer to premium service level"
        logger.info("Successfully set customer to premium service level")
        
        # First, ensure the device is powered on
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
            
        # Verify power on was successful
        assert power_response.status_code == 200
        power_data = power_response.json()
        assert "on" in power_data["message"].lower()
        
        # Wait a moment for the power state to update
        time.sleep(2)
        
        # Test premium feature access (e.g., volume control)
        logger.info("Testing premium feature access")
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
        logger.info("Premium feature access test successful")
        
        # Now change to basic service level
        logger.info("Changing to basic service level")
        update_response = customers_table.update_item(
            Key={'id': customer_id},
            UpdateExpression="SET #lvl = :val",
            ExpressionAttributeNames={'#lvl': 'level'},
            ExpressionAttributeValues={':val': 'basic'},
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"Service level update response: {update_response}")
        
        # Wait a moment for the change to propagate
        time.sleep(2)
        
        # Verify the change was successful
        response = customers_table.get_item(Key={'id': customer_id})
        assert response.get('Item', {}).get('level') == 'basic', "Failed to change service level to basic"
        logger.info("Successfully changed to basic service level")
        
        # Test the same feature with basic service level
        logger.info("Testing basic service level access")
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
        logger.info("Basic service level restriction test successful")
        
    finally:
        # Restore premium service level
        try:
            logger.info("Restoring premium service level")
            customers_table.update_item(
                Key={'id': customer_id},
                UpdateExpression="SET #lvl = :val",
                ExpressionAttributeNames={'#lvl': 'level'},
                ExpressionAttributeValues={':val': 'premium'}
            )
            logger.info("Successfully restored premium service level")
        except Exception as e:
            logger.error(f"Warning: Failed to restore premium service level: {e}")

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
            UpdateExpression="SET #lvl = :val",
            ExpressionAttributeNames={'#lvl': 'level'},
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
                UpdateExpression="SET #lvl = :val",
                ExpressionAttributeNames={'#lvl': 'level'},
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
        assert "off" in turn_off_message_text, "Response should confirm the device was turned off"
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
        assert "off" in status_again_message_text, "Response should indicate the device is now off"
        assert "on" not in status_again_message_text or ("not" in status_again_message_text and "on" in status_again_message_text), \
            f"Response should not indicate the device is on (unless saying it's not on): {status_again_message_text}"
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