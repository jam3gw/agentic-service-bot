# Service Levels and Permissions

## Overview

The Agentic Service Bot implements a tiered service level system that determines what actions customers can perform with their devices. Each service level grants access to a specific set of features and capabilities.

## Service Tiers

### Basic Tier

**Description**: Entry-level service for customers with basic needs.

**Features**:
- Device status check
- Device power control
- Limited to 1 device

**Limitations**:
- No volume control
- No song changes
- No advanced features

**Support Priority**: Standard

### Premium Tier

**Description**: Mid-level service for customers with additional control needs.

**Features**:
- All Basic tier features (device status check, device power)
- Volume control
- Limited to 1 device

**Limitations**:
- No song changes

**Support Priority**: Priority

### Enterprise Tier

**Description**: Top-level service for customers with advanced control needs.

**Features**:
- All Premium tier features (device status check, device power, volume control)
- Song changes
- Limited to 1 device

**Limitations**:
- None within the system's capabilities

**Support Priority**: Dedicated

## Permission Matrix

| Action | Basic | Premium | Enterprise |
|--------|-------|---------|------------|
| Device Status Check | ✅ | ✅ | ✅ |
| Device Power | ✅ | ✅ | ✅ |
| Volume Control | ❌ | ✅ | ✅ |
| Song Changes | ❌ | ❌ | ✅ |

## Action Definitions

### Device Status Check
- **Description**: Check the status of smart home devices
- **Example Request**: "What's the status of my living room speaker?"
- **Required Permission**: `device_status`

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
   - Improves support priority

2. **Premium to Enterprise**:
   - Gains song changes
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
  "max_devices": 1,
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
  "max_devices": 1,
  "support_priority": "dedicated"
}
```

The RequestAnalyzer class maps user requests to required actions, which are then checked against the customer's service level permissions. 