# Frontend

## Overview

The Agentic Service Bot frontend provides a user-friendly interface for customers to interact with the service bot. It is built using React with TypeScript and Chakra UI for styling.

## Technology Stack

- **Framework**: React with TypeScript
- **UI Library**: Chakra UI
- **State Management**: React Hooks (useState, useEffect)
- **Communication**: WebSocket API for real-time messaging
- **Build Tool**: Create React App

## Components

### App Component

The top-level component that provides the application structure and navigation.

**Features**:
- Tab-based navigation between Chat, Devices, and Capabilities views
- Shared customer context across all tabs
- Responsive layout using Chakra UI

**Props**: None (top-level component)

**State**:
- `customerId`: Currently selected customer ID

### Instructions Section Component

Provides an introduction and usage instructions for the smart home assistant.

**Features**:
- Welcome message and overview
- Collapsible instructions on how to use the assistant
- Example commands for different smart home functions

**Props**: None

### Chat Component

The main component that handles the chat interface and WebSocket communication.

**Features**:
- Real-time message display
- Message input and submission
- Customer selection
- Connection status indicator
- Error handling and display
- Automatic scrolling to latest messages
- Disconnect functionality

**Props**:
- `onCustomerChange`: Callback function when customer selection changes

**State**:
- `messages`: Array of message objects
- `input`: Current text input value
- `isLoading`: Boolean indicating if a response is being processed
- `error`: Error message if any
- `customerId`: Currently selected customer ID
- `isConnected`: Boolean indicating WebSocket connection status
- `isConnecting`: Boolean indicating if connection is in progress
- `isDisconnected`: Boolean indicating if user has manually disconnected

### User Devices Table Component

Displays a live-updated table of the user's smart home devices.

**Features**:
- Device listing with status indicators
- Filtering by device type and location
- Interactive controls for supported devices
- Automatic refresh of device status
- Responsive design for different screen sizes

**Props**:
- `customerId`: ID of the current customer

**State**:
- `devices`: Array of device objects
- `isLoading`: Boolean indicating if devices are being loaded
- `lastRefreshed`: Timestamp of last data refresh

### Capabilities Table Component

Provides a reference table for service level capabilities.

**Features**:
- Comparison of features across service levels
- Categorized capabilities for easy reference
- Visual indicators for available/unavailable features
- Highlighting of current user's service level

**Props**:
- `customerId`: ID of the current customer

**State**: None (static reference data)

### Message Component

Displays individual messages in the chat interface.

**Features**:
- Different styling for user and bot messages
- Timestamp display
- Message content formatting
- Message status indicators (sending, sent, delivered, error)

**Props**:
- `message`: Message object containing text, sender, timestamp, and status

### Connection Status Component

Displays the current WebSocket connection status.

**Features**:
- Visual indicators for different connection states
- Error message display
- Reconnect button for manual reconnection

**Props**:
- `isConnected`: Boolean indicating if connected
- `isConnecting`: Boolean indicating if connecting
- `error`: Error message if any
- `onReconnect`: Callback function for manual reconnection

### CustomerSelector Component

Allows selection of different customer profiles for testing.

**Features**:
- Dropdown of available customers
- Display of current service level

**Props**:
- `customers`: Array of customer objects
- `selectedId`: Currently selected customer ID
- `onChange`: Function to handle customer change

**State**: None (stateless component)

## Pages

### Main Chat Page

The primary page of the application, containing all the components.

**Layout**:
```
┌─────────────────────────────────────────────┐
│ Header                                       │
├─────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────┐ │
│ │ Customer        │ │ Connection Status    │ │
│ │ Selector        │ │                     │ │
│ └─────────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────┤
│                                             │
│                                             │
│                                             │
│                                             │
│                                             │
│             Message History                 │
│                                             │
│                                             │
│                                             │
│                                             │
│                                             │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────┐ ┌───────────┐   │
│ │ Message Input           │ │ Send      │   │
│ └─────────────────────────┘ └───────────┘   │
└─────────────────────────────────────────────┘
```

## WebSocket Communication

### Connection Establishment

1. When the Chat component mounts or when the customer changes:
   - Close any existing connection
   - Create a new WebSocket connection to `{wsUrl}?customerId={customerId}`
   - Set up event handlers for connection events

### Message Handling

1. **Sending Messages**:
   - When user submits a message:
     - Add message to local state
     - Send message through WebSocket
     - Display loading indicator

2. **Receiving Messages**:
   - When a message is received from the WebSocket:
     - Parse the JSON data
     - Add the bot's response to the message list
     - Clear loading indicator

### Error Handling

1. **Connection Errors**:
   - Display error message
   - Provide reconnection option
   - Automatically attempt to reconnect after delay

2. **Message Errors**:
   - Display error in the chat
   - Allow retry of failed messages

## User Experience

### Responsive Design

- Mobile-friendly layout
- Adapts to different screen sizes
- Touch-friendly controls

### Accessibility

- Semantic HTML
- ARIA attributes
- Keyboard navigation
- Screen reader support
- Color contrast compliance

### Performance

- Efficient rendering with React
- Optimized WebSocket communication
- Lazy loading of components
- Memoization of expensive calculations

## Implementation Details

### API Services

```typescript
// API Base URL configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

/**
 * Fetches user devices from the backend
 * @param customerId - The ID of the customer whose devices to fetch
 * @returns Promise containing array of Device objects
 */
export const fetchUserDevices = async (customerId: string): Promise<Device[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/customers/${customerId}/devices`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch devices: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.devices;
  } catch (error) {
    console.error('Error fetching user devices:', error);
    throw error;
  }
};

/**
 * Fetches service capabilities from the backend
 * @returns Promise containing array of Capability objects
 */
export const fetchServiceCapabilities = async (): Promise<Capability[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/capabilities`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch capabilities: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.capabilities;
  } catch (error) {
    console.error('Error fetching service capabilities:', error);
    throw error;
  }
};

/**
 * Updates the state of a device
 * @param deviceId - The ID of the device to update
 * @param newState - The new state to set for the device
 * @param customerId - The ID of the customer who owns the device
 * @returns Promise containing the updated Device object
 */
export const updateDeviceState = async (
  deviceId: string, 
  newState: string, 
  customerId: string
): Promise<Device> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/customers/${customerId}/devices/${deviceId}`, 
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ state: newState }),
      }
    );
    
    if (!response.ok) {
      throw new Error(`Failed to update device: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.device;
  } catch (error) {
    console.error('Error updating device state:', error);
    throw error;
  }
};
```

### WebSocket Connection

```typescript
const connectWebSocket = () => {
  // Close existing connection if any
  if (socketRef.current) {
    socketRef.current.close();
    socketRef.current = null;
  }

  setIsConnecting(true);
  setError(null);
  setMessages([]);

  // Create WebSocket URL with customerId as query parameter
  const wsUrl = `${config.wsUrl}?customerId=${customerId}`;
  const socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log('WebSocket connected');
    setIsConnected(true);
    setIsConnecting(false);
  };

  socket.onclose = (event) => {
    console.log('WebSocket disconnected', event);
    setIsConnected(false);
    setIsConnecting(false);

    // Attempt to reconnect after a delay if not intentionally closed
    if (!event.wasClean && socketRef.current === socket) {
      setTimeout(() => {
        connectWebSocket();
      }, 3000);
    }
  };

  socket.onerror = (error) => {
    console.error('WebSocket error', error);
    setError('Failed to connect to chat service');
    setIsConnecting(false);
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.message) {
        const botMessage = {
          id: Date.now().toString(),
          text: data.message,
          sender: 'bot',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error parsing message', error);
      setError('Failed to parse message from server');
      setIsLoading(false);
    }
  };

  socketRef.current = socket;
};
```

### Message Sending

```typescript
const sendMessage = () => {
  if (!input.trim() || !isConnected || isLoading) return;

  const userMessage = {
    id: Date.now().toString(),
    text: input,
    sender: 'user',
    timestamp: new Date().toISOString()
  };

  setMessages(prev => [...prev, userMessage]);
  setInput('');
  setIsLoading(true);
  setError(null);

  try {
    socketRef.current?.send(JSON.stringify({
      action: 'sendMessage',
      message: input
    }));
  } catch (error) {
    console.error('Error sending message', error);
    setError('Failed to send message');
    setIsLoading(false);
  }
};
```

## Deployment

The frontend is deployed to a static hosting service (e.g., AWS S3 with CloudFront) with environment-specific configurations:

- **Development**: https://agentic-service-bot.dev.jake-moses.com
- **Production**: https://agentic-service-bot.jake-moses.com

## Future Enhancements

1. **User Authentication**: Add login functionality for real customer accounts
2. **Message Attachments**: Support for sending images or files
3. **Voice Input/Output**: Add speech recognition and synthesis
4. **Typing Indicators**: Show when the bot is generating a response
5. **Message Templates**: Quick-access buttons for common requests
6. **Dark Mode**: Toggle between light and dark themes
7. **Offline Support**: Progressive Web App functionality

## User Interface

### Layout

The frontend uses a responsive layout with the following structure:

- **Header**: Contains the application title and global controls
- **Instructions Section**: Provides an introduction and usage instructions
- **Tab Navigation**: Allows switching between different views
  - **Chat Tab**: The main chat interface
  - **My Devices Tab**: Shows the user's smart home devices
  - **Capabilities Tab**: Displays service level capabilities
- **Footer**: Contains additional information and links

### Responsive Design

The UI is designed to work on various screen sizes:

- **Desktop**: Full layout with side-by-side elements
- **Tablet**: Adjusted spacing and sizing
- **Mobile**: Stacked layout with optimized controls for touch

### Theme

The application uses Chakra UI's theming system with:

- Light and dark mode support
- Consistent color scheme
- Accessible contrast ratios
- Responsive typography

## Interactions

### Chat Interaction

1. User selects a customer profile (Basic, Premium, or Enterprise)
2. User types a message in the input field
3. Message is sent to the backend via WebSocket
4. Response is received and displayed in the chat
5. Chat automatically scrolls to the latest message

### Device Management

1. User navigates to the My Devices tab
2. Devices are loaded based on the selected customer profile
3. User can view device status and control supported devices
4. Device status updates in real-time

### Capability Reference

1. User navigates to the Capabilities tab
2. Capabilities are displayed based on service levels
3. Current customer's service level is highlighted
4. User can expand categories to view detailed capabilities 