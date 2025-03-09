# API Documentation

This document provides the API specification for the Agentic Service Bot.

## API Endpoints

### Chat API

#### POST /api/chat
Send a chat message to the bot.

**Request:**
```typescript
{
  customerId: string;  // Required: The ID of the customer sending the message
  message: string;     // Required: The message text
}
```

**Response:**
```typescript
{
  message: string;        // The bot's response message
  timestamp: string;      // ISO 8601 timestamp
  messageId: string;      // Unique message identifier
  conversationId: string; // Conversation thread identifier
}
```

### Device API

#### GET /api/customers/{customerId}/devices
Get all devices for a customer.

**Response:**
```typescript
{
  devices: Array<{
    id: string;           // Device identifier
    name: string;         // Display name
    type: string;         // Device type (e.g., "speaker")
    power: string;        // "on" or "off"
    status: string;       // "online" or "offline"
    volume?: number;      // 0-100 (for audio devices)
    currentSong?: string; // Currently playing song
    playlist?: string[];  // List of songs in playlist
  }>;
}
```

### Service Level API

#### GET /api/service/capabilities
Get available service capabilities.

**Response:**
```typescript
{
  capabilities: Array<{
    id: string;           // Capability identifier
    name: string;         // Display name
    description: string;  // Detailed description
    tiers: {
      basic: boolean;     // Available in basic tier
      premium: boolean;   // Available in premium tier
      enterprise: boolean;// Available in enterprise tier
    };
  }>;
}
```

## Service Levels

The API enforces the following service level permissions:

### Basic Level
- View device status
- Control device power (on/off)

### Premium Level
- All Basic level capabilities
- Control device volume
- View and set device location

### Enterprise Level
- All Premium level capabilities
- Control music playback
- Manage playlists

## Error Handling

All API endpoints follow this error response format:

```typescript
{
  error: {
    code: string;      // Error code
    message: string;   // Human-readable error message
    details?: any;     // Additional error details
  }
}
```

Common error codes:
- `UNAUTHORIZED`: Invalid or missing authentication
- `FORBIDDEN`: Action not allowed for customer's service level
- `NOT_FOUND`: Requested resource not found
- `BAD_REQUEST`: Invalid request parameters
- `INTERNAL_ERROR`: Server-side error

## Rate Limiting

API endpoints are rate limited to:
- 10 requests per second per customer
- 1000 requests per hour per customer

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1234567890
```

## Data Types

### Customer Service Levels
```typescript
type ServiceLevel = 'basic' | 'premium' | 'enterprise';
```

### Device Types
```typescript
type DeviceType = 'speaker' | 'audio';
```

### Device Status
```typescript
type DeviceStatus = 'online' | 'offline';
```

### Power State
```typescript
type PowerState = 'on' | 'off';
```

## Testing

Use the provided test data generation script to create test customers:

```bash
python seed_test_data.py
```

This will create test customers with different service levels for API testing.

## Versioning

The current API version is v1. The version is included in the response headers:
```
X-API-Version: 1.0
```

Future versions will be available at `/api/v2/`, etc. 