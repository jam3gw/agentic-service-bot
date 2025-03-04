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

### Chat Component

The main component that handles the chat interface and WebSocket communication.

**Features**:
- Real-time message display
- Message input and submission
- Customer selection
- Connection status indicator
- Error handling and display
- Automatic scrolling to latest messages

**Props**: None (top-level component)

**State**:
- `messages`: Array of message objects
- `input`: Current text input value
- `isLoading`: Boolean indicating if a response is being processed
- `error`: Error message if any
- `customerId`: Currently selected customer ID
- `isConnected`: Boolean indicating WebSocket connection status
- `isConnecting`: Boolean indicating if connection is in progress

### Message Component

Displays individual messages in the chat interface.

**Features**:
- Different styling for user and bot messages
- Timestamp display
- Message content formatting

**Props**:
- `message`: Message object containing text, sender, and timestamp
- `isLast`: Boolean indicating if this is the most recent message

**State**: None (stateless component)

### ConnectionStatus Component

Displays the current connection status.

**Features**:
- Visual indicator of connection state
- Status text

**Props**:
- `isConnected`: Boolean indicating if connected
- `isConnecting`: Boolean indicating if connecting
- `error`: Error message if any

**State**: None (stateless component)

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