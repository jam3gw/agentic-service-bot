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
  "location": "living_room",
  "state": "off",
  "volume": 50
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
      "location": "living_room",
      "state": "off",
      "volume": 50
    }
  ]
}
```

### Service Levels Table

**Table Name**: `{environment}-service-levels`

**Purpose**: Defines the permissions and limitations for each service tier.

**Schema**:
- `level` (Partition Key): String - Service tier name (basic, premium, enterprise)
- `allowed_actions`: List - Array of action names allowed for this tier
- `max_devices`: Number - Maximum number of devices allowed for this tier
- `description`: String - Human-readable description of the tier

**Example Record**:
```json
{
  "level": "basic",
  "allowed_actions": [
    "device_status",
    "volume_control",
    "device_power"
  ],
  "max_devices": 1,
  "description": "Basic tier with limited functionality"
}
```

### Messages Table

**Table Name**: `{environment}-messages`

**Purpose**: Stores chat message history.

**Schema**:
- `id` (Partition Key): String - Unique identifier for the message
- `conversationId`: String - ID of the conversation this message belongs to
- `userId`: String - ID of the customer associated with this message
- `text`: String - Content of the message
- `sender`: String - Who sent the message ('user' or 'bot')
- `timestamp`: String - ISO format timestamp of when the message was sent

**GSI**: `conversationId-index`
- Partition Key: `conversationId`
- Sort Key: `timestamp`

**GSI**: `userId-index`
- Partition Key: `userId`
- Sort Key: `timestamp`

**Example Record**:
```json
{
  "id": "msg_001",
  "conversationId": "conv_001",
  "userId": "cust_001",
  "text": "Turn on my living room speaker",
  "sender": "user",
  "timestamp": "2023-03-01T12:00:00Z"
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

## Data Models

### Customer Model

The Customer model represents a customer in the system with their associated data and devices.

**Attributes**:
- `id`: String - Unique identifier for the customer
- `name`: String - Full name of the customer
- `service_level`: String - Service tier level (basic, premium, enterprise)
- `device`: Dict - The customer's smart device

**Methods**:
- `__init__(customer_id, name, service_level, device)`: Initialize a Customer instance
- `__str__()`: Return a string representation of the Customer
- `get_device()`: Get the customer's device
- `to_dict()`: Convert the Customer instance to a dictionary

**Example Usage**:
```python
customer = Customer(
    customer_id="cust_001",
    name="Jane Smith",
    service_level="basic",
    device={
        "id": "dev_001",
        "type": "SmartSpeaker",
        "location": "living_room",
        "state": "off",
        "volume": 50
    }
)
```

### Message Model

The Message model represents a chat message in the system.

**Attributes**:
- `id`: String - Unique identifier for the message
- `conversation_id`: String - ID of the conversation this message belongs to
- `user_id`: String - ID of the user who sent or received the message
- `text`: String - Content of the message
- `sender`: String - Who sent the message ('user' or 'bot')
- `timestamp`: String - When the message was sent

**Methods**:
- `__init__(id, conversation_id, user_id, text, sender, timestamp=None)`: Initialize a Message instance
- `__str__()`: Return a string representation of the Message
- `to_dict()`: Convert the Message to a dictionary for storage in DynamoDB
- `from_dict(data)`: Create a Message instance from a dictionary (class method)

**Example Usage**:
```python
message = Message(
    id="msg_001",
    conversation_id="conv_001",
    user_id="cust_001",
    text="Turn on my living room speaker",
    sender="user"
)
```

## Data Access Patterns

### Customer Access Patterns

1. **Get customer by ID**:
   - Used when processing a chat message to retrieve customer information
   - Query the Customers table using the customer ID as the partition key

2. **Update customer device state**:
   - Used when a device state change is requested
   - Update the Customers table using the customer ID as the partition key
   - Modify the specific device in the devices array

### Service Level Access Patterns

1. **Get service level permissions**:
   - Used when checking if a customer can perform a specific action
   - Query the Service Levels table using the service level as the partition key

### Message Access Patterns

1. **Save new message**:
   - Used when a new message is sent or received
   - Put item in the Messages table

2. **Get conversation history**:
   - Used when retrieving chat history for a specific conversation
   - Query the Messages table using the GSI with conversationId as the partition key
   - Sort by timestamp to get messages in chronological order

3. **Get all messages for a customer**:
   - Used when retrieving all chat history for a customer
   - Query the Messages table using the GSI with userId as the partition key
   - Sort by timestamp to get messages in chronological order

## Data Consistency

The system uses DynamoDB's strong consistency for read operations where immediate consistency is required, such as:
- Checking service level permissions before executing an action
- Retrieving customer information for processing a request

For other operations where eventual consistency is acceptable, such as retrieving chat history, the system uses DynamoDB's default eventually consistent reads for better performance and lower cost.

## Data Validation

Data validation is performed at multiple levels:

1. **API Layer**:
   - Validates request parameters
   - Ensures required fields are present
   - Checks data types and formats

2. **Service Layer**:
   - Validates business rules
   - Ensures data consistency
   - Checks permissions and limits

3. **Model Layer**:
   - Validates data structure
   - Provides type hints for better code quality
   - Ensures proper formatting before storage

## Error Handling

The system handles data-related errors in the following ways:

1. **Item Not Found**:
   - Returns appropriate error messages
   - Logs the error for monitoring
   - Provides helpful context in the response

2. **Validation Errors**:
   - Returns detailed error messages
   - Indicates which fields failed validation
   - Suggests correct formats or values

3. **Permission Errors**:
   - Explains why an action is not allowed
   - Suggests upgrading service level if applicable
   - Provides alternative actions that are allowed

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