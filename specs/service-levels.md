# Service Levels and Permissions

## Overview

The Agentic Service Bot implements a tiered service level system that determines what actions customers can perform with their devices. Each service level grants access to a specific set of features and capabilities.

## Service Tiers

### Basic Tier

**Description**: Basic service level with device status and power control.

**Features**:
- Device status check
- Device power control
- Limited to 1 device

**Allowed Actions**:
- `device_status`
- `device_power`

**Price**: Free

### Premium Tier

**Description**: Premium service level with volume control.

**Features**:
- All Basic tier features (device status check, device power)
- Volume control
- Limited to 1 device

**Allowed Actions**:
- `device_status`
- `device_power`
- `volume_control`

**Price**: $9.99/month

### Enterprise Tier

**Description**: Enterprise service level with full device control.

**Features**:
- All Premium tier features (device status check, device power, volume control)
- Song changes
- Limited to 1 device

**Allowed Actions**:
- `device_status`
- `device_power`
- `volume_control`
- `song_changes`

**Price**: $29.99/month

## Action Definitions

### device_status

**Description**: Check the status of a device.

**Examples**:
- "Is my speaker on?"
- "What's the volume of my speaker?"
- "Check the status of my living room speaker"

**Required Parameters**:
- Device ID or location (optional, defaults to the customer's device)

**Response**:
- Current device state (on/off)
- Current volume level (if applicable)
- Current location

### device_power

**Description**: Turn a device on or off.

**Examples**:
- "Turn on my speaker"
- "Turn off my living room speaker"
- "Power on my device"

**Required Parameters**:
- Device ID or location (optional, defaults to the customer's device)
- Desired state (on/off)

**Response**:
- Confirmation of the action
- New device state

### volume_control

**Description**: Adjust the volume of a device.

**Examples**:
- "Turn up the volume"
- "Set volume to 50%"
- "Lower the volume"

**Required Parameters**:
- Device ID or location (optional, defaults to the customer's device)
- Volume level or adjustment direction

**Response**:
- Confirmation of the action
- New volume level

### song_changes

**Description**: Change the currently playing song.

**Examples**:
- "Play the next song"
- "Skip this track"
- "Play the previous song"

**Required Parameters**:
- Device ID or location (optional, defaults to the customer's device)
- Direction (next, previous) or specific song

**Response**:
- Confirmation of the action
- Information about the new song (if available)

## Permission Enforcement

The system enforces permissions at multiple levels:

1. **API Layer**:
   - Validates the customer's service level before processing requests
   - Returns appropriate error messages for unauthorized actions

2. **Service Layer**:
   - Checks permissions before executing device actions
   - Logs permission denials for monitoring

3. **Response Generation**:
   - Provides helpful responses explaining permission limitations
   - Suggests upgrading to a higher service tier when appropriate

## Implementation

Permissions are stored in the `{environment}-service-levels` DynamoDB table with the following structure:

```json
{
  "level": "premium",
  "name": "Premium",
  "description": "Premium service level with volume control",
  "price": 9.99,
  "allowed_actions": [
    "device_status",
    "device_power",
    "volume_control"
  ]
}
```

The system retrieves these permissions when processing customer requests and uses them to determine if the requested action is allowed.

## Upgrading Service Levels

When a customer attempts an action that is not allowed at their current service level, the system:

1. Identifies the required service level for the action
2. Explains the limitation to the customer
3. Suggests upgrading to the appropriate service level
4. Provides information about the benefits of upgrading

Example response:
```
I'm sorry, but changing songs requires the Enterprise service level. You're currently on the Premium plan. Would you like to upgrade to Enterprise for $29.99/month to access this feature?
```

## Future Enhancements

Planned enhancements to the service level system include:

1. **Custom Service Levels**: Allow creating custom service levels with specific permissions
2. **Temporary Upgrades**: Enable temporary access to higher-tier features
3. **Usage-Based Pricing**: Implement pay-per-use options for certain actions
4. **Family Plans**: Support multiple users with shared devices and permissions 