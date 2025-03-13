# Frontend

## Overview

The Agentic Service Bot frontend provides a user-friendly interface for customers to interact with the service bot. It is built using React with TypeScript and Chakra UI for styling.

## Technology Stack

- **Framework**: React with TypeScript
- **UI Library**: Chakra UI
- **State Management**: React Hooks (useState, useEffect, custom hooks)
- **Communication**: REST API for messaging
- **Build Tool**: Vite

## Components

### App Component

The top-level component that provides the application structure and navigation.

**Features**:
- Grid-based layout with main content and sidebar
- Shared customer context across all components
- Responsive layout using Chakra UI
- State management for customer selection and message updates

**Props**: None (top-level component)

**State**:
- `customerId`: Currently selected customer ID
- `lastMessageTimestamp`: Timestamp of the last message sent (for triggering updates)

### Instructions Section Component

Provides an introduction, system architecture visualization, and usage instructions for the smart home assistant.

**Features**:
- Welcome message and overview
- System architecture diagram with zoom functionality
- Technical highlights and key components
- Quick demo guide with step-by-step instructions
- Responsive design with color mode support

**Props**: None

**State**:
- Modal state for diagram zoom functionality

**Visual Elements**:
- System architecture sequence diagram
- Component lists with icons
- Styled sections with consistent theming
- Interactive zoom modal for detailed diagram viewing

### Chat Component

The main component that handles the chat interface and API communication.

**Features**:
- Message display
- Message input and submission
- Customer selection
- Loading state indicator
- Error handling with alerts
- New conversation functionality
- Auto-scrolling message list

**Props**:
- `onCustomerChange`: Callback function when customer changes
- `onMessageSent`: Callback function when a message is sent

**State**:
- Managed by custom `useChat` hook

### UserDevicesTable Component

Displays the devices associated with the selected customer.

**Features**:
- Tabular display of device information
- Real-time updates when device state changes
- Visual indicators for device status
- Responsive design for different screen sizes

**Props**:
- `customerId`: ID of the selected customer
- `lastUpdate`: Timestamp to trigger refreshes

### CapabilitiesTable Component

Displays the capabilities and permissions available to the selected customer based on their service level.

**Features**:
- Service level display
- Allowed and disallowed actions
- Visual indicators for permission status
- Upgrade suggestions for disallowed actions

**Props**:
- `customerId`: ID of the selected customer

### MessageList Component

Renders the list of messages in the chat.

**Features**:
- Alternating message styles for user and bot
- Timestamp display
- Auto-scrolling to latest message
- Visual differentiation between message types

**Props**:
- `messages`: Array of message objects
- `isLoading`: Boolean indicating if a message is being processed

### ErrorBoundary Component

Catches and displays errors that occur during rendering.

**Features**:
- Error state display
- Recovery options
- Detailed error information for debugging

**Props**:
- `children`: React nodes to render

## Custom Hooks

### useChat Hook

Custom hook that encapsulates chat functionality.

**Features**:
- Message state management
- API communication
- Error handling
- Customer data fetching
- Input handling

**Returns**:
- `messages`: Array of message objects
- `input`: Current input value
- `isLoading`: Boolean indicating if a message is being processed
- `error`: Error object if an error occurred
- `customers`: Array of customer objects
- `isLoadingCustomers`: Boolean indicating if customers are being loaded
- `customerId`: ID of the selected customer
- `setInput`: Function to update input value
- `sendMessage`: Function to send a message
- `startNewConversation`: Function to start a new conversation
- `setCustomerId`: Function to update the selected customer
- `clearError`: Function to clear the error state

## API Communication

### Chat API

**Endpoints**:
- `GET /api/customers`: Fetch list of customers
- `POST /api/chat`: Send a message to the chat service
- `GET /api/chat/history/{customerId}`: Fetch chat history for a customer
- `GET /api/customers/{customerId}/devices`: Fetch devices for a customer
- `GET /api/service-levels/{serviceLevel}`: Fetch service level permissions

**Request Format**:
```json
{
  "customerId": "string",
  "message": "string",
  "conversationId": "string (optional)"
}
```

**Response Format**:
```json
{
  "message": "string",
  "timestamp": "string (ISO date)",
  "messageId": "string",
  "id": "string",
  "conversationId": "string",
  "customerId": "string",
  "request_type": "string",
  "action_executed": "boolean"
}
```

## Styling

The application uses Chakra UI for styling with the following features:
- Responsive design for different screen sizes
- Light and dark mode support
- Consistent color scheme
- Accessible UI components
- Grid and flex layouts for organization

## User Experience

The frontend is designed to provide a seamless user experience with:
- Clear instructions and guidance
- Visual feedback for actions
- Error handling and recovery
- Responsive design for different devices
- Intuitive interface for chat interactions
- Real-time updates for device state changes

## Pages

### Main Chat Page

The primary page of the application, containing all the components.

**Layout**:
```
┌─────────────────────────────────────────────┐
│ Header                                       │
├─────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────┐ │
│ │ Customer        │ │ Status Indicator     │ │
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

## API Communication

### Message Handling

1. **Sending Messages**:
   - When user submits a message:
     - Add message to local state
     - Send POST request to `/api/chat` endpoint
     - Display loading indicator
     - Handle response when received

2. **Receiving Messages**:
   - When a response is received from the API:
     - Parse the JSON data
     - Add the bot's response to the message list
     - Clear loading indicator
     - Update last message timestamp

3. **Message History**:
   - On component mount or customer change:
     - Fetch message history from `/api/chat/history/{customerId}` endpoint
     - Display messages in chronological order

### Error Handling

1. **Request Errors**:
   - Display error message
   - Provide retry option
   - Implement exponential backoff for retries

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
- Optimized API communication
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
      throw new Error(`Failed to fetch devices: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching devices:', error);
    throw error;
  }
};

/**
 * Sends a chat message to the backend
 * @param customerId - The ID of the customer sending the message
 * @param message - The message text to send
 * @returns Promise containing the response from the bot
 */
export const sendChatMessage = async (customerId: string, message: string): Promise<ChatResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customerId,
        message,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to send message: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

/**
 * Fetches chat history for a customer
 * @param customerId - The ID of the customer whose chat history to fetch
 * @returns Promise containing array of Message objects
 */
export const fetchChatHistory = async (customerId: string): Promise<Message[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/history/${customerId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch chat history: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching chat history:', error);
    throw error;
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
3. Message is sent to the backend via REST API
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

## API Integration

### Backend Communication

The frontend communicates with the backend through REST API endpoints. The following integration points are implemented:

#### REST API Endpoints

- **GET /api/customers/{customerId}/devices**: Retrieve a customer's devices
- **POST /api/chat**: Send a chat message to the backend
- **GET /api/chat/history/{customerId}**: Retrieve chat history for a customer

### Integration Requirements

To ensure proper communication between the frontend and backend, the following requirements must be met:

1. **Environment Configuration**
   - The frontend must use the `REACT_APP_API_URL` environment variable to determine the API endpoint
   - Different environments (dev, staging, prod) should have different API endpoints
   - The `.env` files should be configured for each environment

2. **CORS Configuration**
   - The API Gateway must allow requests from the frontend domain
   - The Lambda functions must return the appropriate CORS headers
   - The frontend must include the necessary credentials in requests

3. **Authentication**
   - API requests must include authentication tokens
   - The frontend must handle token acquisition and renewal
   - Unauthorized requests must be redirected to the login page

4. **Error Handling**
   - The frontend must handle API errors gracefully
   - Network errors should trigger retry logic
   - User-friendly error messages should be displayed

5. **Message Handling**
   - The frontend must handle message sending and receiving
   - Message history should be fetched and displayed

### Implementation Steps

1. **Configure Environment Variables**
   - Create `.env.development`, `.env.staging`, and `.env.production` files
   - Set `REACT_APP_API_URL` in each environment file
   - Update the build pipeline to use the correct environment file

2. **Update API Service**
   - Enhance the `apiService.ts` to handle authentication
   - Add retry logic for failed requests
   - Implement proper error handling

3. **Testing**
   - Test API integration with mock endpoints
   - Perform end-to-end testing with the actual backend 