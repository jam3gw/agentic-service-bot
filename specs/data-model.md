# Data Model

## Overview

The Agentic Service Bot uses DynamoDB as its primary data store. The data model is designed to support the core functionality of the system, including customer management, service level permissions, device tracking, and conversation history.

## Database Tables

### Customers Table

**Table Name**: `{environment}-customers`

**Purpose**: Stores customer information and their associated devices.

**Schema**:
- `id` (Partition Key): String - Unique identifier for the customer
- `name`: String - Customer's name
- `service_level`: String - Customer's service tier (basic, premium, enterprise)
- `devices`: List - Array of device objects associated with the customer

**Device Object Structure**:
```json
{
  "id": "dev_001",
  "type": "SmartSpeaker",
  "location": "living_room"
}
```

**Example Record**:
```json
{
  "id": "cust_001",
  "name": "Jane Smith",
  "service_level": "basic",
  "devices": [
    {
      "id": "dev_001",
      "type": "SmartSpeaker",
      "location": "living_room"
    }
  ]
}
```

### Service Levels Table

**Table Name**: `{environment}-service-levels`

**Purpose**: Defines the permissions and limitations for each service tier.

**Schema**:
- `level` (Partition Key): String - Service tier name (basic, premium, enterprise)
- `allowed_actions`: List - Array of action names allowed at this service level
- `max_devices`: Number - Maximum number of devices allowed at this service level
- `support_priority`: String - Support priority level (standard, priority, dedicated)

**Example Record**:
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

**Service Level Permissions**:
- `basic`: Allows `device_power` actions
- `premium`: Allows `device_power` and `volume_control` actions
- `enterprise`: Allows `device_power`, `volume_control`, and `song_changes` actions

### Messages Table

**Table Name**: `{environment}-messages`

**Purpose**: Stores conversation history between customers and the service bot.

**Schema**:
- `conversationId` (Partition Key): String - Unique identifier for the conversation
- `timestamp` (Sort Key): String - ISO timestamp of the message
- `userId`: String - Customer ID or "bot" for bot messages
- `text`: String - Message content
- `requestType`: String (Optional) - Type of request for customer messages
- `requiredActions`: List (Optional) - Actions required for the request
- `allowed`: Boolean (Optional) - Whether the request was allowed

**Indexes**:
- **UserIdIndex** (GSI):
  - Partition Key: `userId`
  - Sort Key: `timestamp`

**Example Record**:
```json
{
  "conversationId": "conv_123",
  "timestamp": "2023-03-01T14:30:45.123Z",
  "userId": "cust_001",
  "text": "Move my smart speaker to the bedroom",
  "requestType": "device_relocation",
  "requiredActions": ["device_relocation"],
  "allowed": false
}
```

### Connections Table

**Table Name**: `{environment}-connections`

**Purpose**: Manages WebSocket connections for real-time communication.

**Schema**:
- `connectionId` (Partition Key): String - Unique WebSocket connection ID
- `userId`: String - Customer ID associated with the connection
- `connectionTime`: String - ISO timestamp when the connection was established
- `ttl`: Number - Time-to-live for automatic expiration (24 hours)

**Example Record**:
```json
{
  "connectionId": "ABC123",
  "userId": "cust_001",
  "connectionTime": "2023-03-01T14:30:00.000Z",
  "ttl": 1677765000
}
```

## Data Relationships

1. **Customer to Service Level**:
   - Each customer has a `service_level` attribute that references a record in the Service Levels table
   - This relationship determines what actions the customer can perform

2. **Customer to Devices**:
   - Devices are embedded within the customer record as a list
   - Each device has a unique ID, type, and location

3. **Customer to Messages**:
   - Messages are linked to customers via the `userId` field
   - The UserIdIndex GSI allows efficient retrieval of a customer's message history

4. **Customer to Connection**:
   - WebSocket connections are linked to customers via the `userId` field
   - This allows sending real-time updates to the correct customer

## Data Access Patterns

1. **Get Customer by ID**:
   - Used when a customer connects or sends a message
   - Direct lookup by partition key on Customers table

2. **Get Service Level Permissions**:
   - Used to check if a customer can perform a requested action
   - Lookup by partition key on Service Levels table

3. **Get Conversation History**:
   - Used to provide context for AI responses
   - Query Messages table by conversationId and timestamp range

4. **Get Customer Message History**:
   - Used for analytics or customer support
   - Query UserIdIndex GSI by userId and timestamp range

5. **Get Active Connection**:
   - Used to send real-time updates to a customer
   - Lookup by userId on Connections table

## Data Validation

1. **Customer Data**:
   - Customer ID must be unique
   - Service level must be one of: basic, premium, enterprise
   - Device count must not exceed the maximum allowed for the service level

2. **Message Data**:
   - Timestamps must be in ISO format
   - Message text cannot be empty
   - Request type must be a valid type if provided

3. **Connection Data**:
   - Connection ID must be unique
   - TTL must be a valid future timestamp

## Data Lifecycle

1. **Customer Data**:
   - Created when a customer is onboarded
   - Updated when service level changes or devices are added/removed
   - No automatic deletion

2. **Message Data**:
   - Created when messages are sent
   - Never updated (immutable)
   - No automatic deletion (retained for history)

3. **Connection Data**:
   - Created when a WebSocket connection is established
   - Deleted automatically after TTL expires (24 hours)
   - Deleted manually when connection is closed

## API Endpoints

### Device Management

**Get Customer Devices**
- **Endpoint**: `GET /api/customers/{customerId}/devices`
- **Description**: Retrieves all devices associated with a specific customer
- **Response Format**:
```json
{
  "devices": [
    {
      "id": "dev_001",
      "type": "SmartSpeaker",
      "name": "Living Room Speaker",
      "location": "living_room",
      "state": "on",
      "capabilities": ["volume_control", "music_playback"],
      "lastUpdated": "2023-03-01T14:30:45.123Z"
    }
  ]
}
```

**Update Device State**
- **Endpoint**: `PATCH /api/customers/{customerId}/devices/{deviceId}`
- **Description**: Updates the state of a specific device
- **Request Body**:
```json
{
  "state": "off"
}
```
- **Response Format**:
```json
{
  "device": {
    "id": "dev_001",
    "type": "SmartSpeaker",
    "name": "Living Room Speaker",
    "location": "living_room",
    "state": "off",
    "capabilities": ["volume_control", "music_playback"],
    "lastUpdated": "2023-03-01T15:45:12.456Z"
  }
}
```

### Service Capabilities

**Get Service Capabilities**
- **Endpoint**: `GET /api/capabilities`
- **Description**: Retrieves all available service capabilities and their availability by service level
- **Response Format**:
```json
{
  "capabilities": [
    {
      "id": "cap_001",
      "name": "Volume Control",
      "description": "Adjust volume of audio devices",
      "basic": true,
      "premium": true,
      "enterprise": true,
      "category": "device-control"
    },
    {
      "id": "cap_002",
      "name": "Multi-room Audio",
      "description": "Play audio across multiple speakers",
      "basic": false,
      "premium": true,
      "enterprise": true,
      "category": "device-control"
    }
  ]
}
```

## Implementation Notes

- All tables use on-demand capacity for automatic scaling
- Production tables have a removal policy of RETAIN to prevent accidental deletion
- Development tables have a removal policy of DESTROY for easy cleanup
- All sensitive data should be encrypted at rest 