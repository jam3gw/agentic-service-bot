# Service Levels and Permissions

## Overview

The Agentic Service Bot implements a tiered service level system that determines what actions customers can perform with their smart home devices. Each service level grants access to a specific set of features and capabilities.

## Service Tiers

### Basic Tier

**Description**: Entry-level service for customers with basic needs and a single device.

**Features**:
- Device power control
- Limited to 1 device

**Limitations**:
- No volume control
- No song changes
- No advanced features

**Support Priority**: Standard

### Premium Tier

**Description**: Mid-level service for customers with multiple devices and additional needs.

**Features**:
- All Basic tier features
- Volume control
- Up to 3 devices

**Limitations**:
- No song changes

**Support Priority**: Priority

### Enterprise Tier

**Description**: Top-level service for customers with advanced needs and multiple devices.

**Features**:
- All Premium tier features
- Song changes
- Up to 10 devices

**Limitations**:
- None within the system's capabilities

**Support Priority**: Dedicated

## Permission Matrix

| Action | Basic | Premium | Enterprise |
|--------|-------|---------|------------|
| Device Power | ✅ | ✅ | ✅ |
| Volume Control | ❌ | ✅ | ✅ |
| Song Changes | ❌ | ❌ | ✅ |

## Action Definitions

### Device Power
- **Description**: Control device power (on/off)
- **Example Request**: "Turn on my living room speaker"
- **Required Permission**: `device_power`

### Volume Control
- **Description**: Adjust the volume of a device
- **Example Request**: "Turn up the volume on my kitchen speaker"
- **Required Permission**: `volume_control`

### Song Changes
- **Description**: Change songs on a speaker device
- **Example Request**: "Skip to the next song on my living room speaker"
- **Required Permission**: `song_changes`

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
   - Gains volume control
   - Increases device limit from 1 to 3
   - Improves support priority

2. **Premium to Enterprise**:
   - Gains song changes
   - Increases device limit from 3 to 10
   - Provides dedicated support

## Implementation Details

Service levels are stored in the `service_levels_table` in DynamoDB with the following structure:

```json
{
  "level": "basic",
  "allowed_actions": [
    "device_power"
  ],
  "max_devices": 1,
  "support_priority": "standard"
}
```

For the Premium tier:
```json
{
  "level": "premium",
  "allowed_actions": [
    "device_power",
    "volume_control"
  ],
  "max_devices": 3,
  "support_priority": "priority"
}
```

For the Enterprise tier:
```json
{
  "level": "enterprise",
  "allowed_actions": [
    "device_power",
    "volume_control",
    "song_changes"
  ],
  "max_devices": 10,
  "support_priority": "dedicated"
}
```

The RequestAnalyzer class maps user requests to required actions, which are then checked against the customer's service level permissions. 