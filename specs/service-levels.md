# Service Levels and Permissions

## Overview

The Agentic Service Bot implements a tiered service level system that determines what actions customers can perform with their smart home devices. Each service level grants access to a specific set of features and capabilities.

## Service Tiers

### Basic Tier

**Description**: Entry-level service for customers with basic needs and a single device.

**Features**:
- Status checks for devices
- Volume control
- Device information retrieval

**Limitations**:
- Maximum of 1 device
- No device relocation
- No music services
- No multi-room audio
- No custom actions

**Support Priority**: Standard

### Premium Tier

**Description**: Mid-level service for customers with multiple devices and additional needs.

**Features**:
- All Basic tier features
- Device relocation
- Music services
- Up to 3 devices

**Limitations**:
- No multi-room audio
- No custom actions

**Support Priority**: Priority

### Enterprise Tier

**Description**: Top-level service for customers with advanced needs and multiple devices.

**Features**:
- All Premium tier features
- Multi-room audio
- Custom actions
- Up to 10 devices

**Limitations**:
- None within the system's capabilities

**Support Priority**: Dedicated

## Permission Matrix

| Action | Basic | Premium | Enterprise |
|--------|-------|---------|------------|
| Status Check | ✅ | ✅ | ✅ |
| Volume Control | ✅ | ✅ | ✅ |
| Device Info | ✅ | ✅ | ✅ |
| Device Relocation | ❌ | ✅ | ✅ |
| Music Services | ❌ | ✅ | ✅ |
| Multi-Room Audio | ❌ | ❌ | ✅ |
| Custom Actions | ❌ | ❌ | ✅ |

## Action Definitions

### Status Check
- **Description**: Check if a device is online, offline, or experiencing issues
- **Example Request**: "Is my smart speaker working?"
- **Required Permission**: `status_check`

### Volume Control
- **Description**: Adjust the volume of a device
- **Example Request**: "Turn up the volume on my kitchen speaker"
- **Required Permission**: `volume_control`

### Device Info
- **Description**: Retrieve information about a device
- **Example Request**: "What is my smart display?"
- **Required Permission**: `device_info`

### Device Relocation
- **Description**: Move a device from one location to another
- **Example Request**: "Move my smart speaker to the bedroom"
- **Required Permission**: `device_relocation`

### Music Services
- **Description**: Play music on a device
- **Example Request**: "Play jazz music on my living room speaker"
- **Required Permission**: `music_services`

### Multi-Room Audio
- **Description**: Synchronize audio across multiple devices
- **Example Request**: "Play the same music on all my speakers"
- **Required Permission**: `multi_room_audio`

### Custom Actions
- **Description**: Create and execute custom routines or automations
- **Example Request**: "Create a routine to turn on my speaker at 7 AM"
- **Required Permission**: `custom_actions`

## Permission Enforcement

1. When a customer sends a request, the system:
   - Identifies the customer
   - Retrieves their service level
   - Analyzes the request to determine required actions
   - Checks if the service level allows those actions
   - Processes the request if allowed, or returns a permission error if not

2. Permission errors include:
   - Clear explanation of why the request was denied
   - Information about upgrading to a higher service tier
   - Alternative actions that are available at the current tier

## Service Level Upgrade Path

Customers can upgrade their service level to gain access to additional features:

1. **Basic to Premium**:
   - Gains device relocation and music services
   - Increases device limit from 1 to 3
   - Improves support priority

2. **Premium to Enterprise**:
   - Gains multi-room audio and custom actions
   - Increases device limit from 3 to 10
   - Provides dedicated support

## Implementation Details

Service levels are stored in the `service_levels_table` in DynamoDB with the following structure:

```json
{
  "level": "basic",
  "allowed_actions": [
    "status_check",
    "volume_control",
    "device_info"
  ],
  "max_devices": 1,
  "support_priority": "standard"
}
```

The RequestAnalyzer class maps user requests to required actions, which are then checked against the customer's service level permissions. 