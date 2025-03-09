# Agentic Service Bot

A sophisticated AI-powered smart home assistant that processes natural language requests, manages device operations, and provides responses based on customer service level permissions.

## Overview
The Agentic Service Bot is an intelligent system that uses Claude AI (via Anthropic's API) to create a service-level aware approach to handling smart home device requests. Instead of treating all requests the same way, the system:

- Analyzes the complexity and type of each request
- Validates permissions based on service level
- Manages device operations within allowed capabilities
- Provides natural language responses
- Tracks conversation history
- Offers upgrade suggestions when needed

## Deep Dive: Under the Hood
The Agentic Service Bot uses a sophisticated service-oriented architecture:

### How It Works
1. **Request Analysis**: When a request is submitted, the system first analyzes its type and required permissions
2. **Service Level Validation**: Checks if the customer's service tier allows the requested actions
3. **Device Management**: Executes allowed device operations and tracks state changes
4. **Response Generation**: Uses Claude AI to generate natural, context-aware responses
5. **History Tracking**: Maintains conversation history for context and analysis

### Technical Implementation
- **Recursive Request Processing**: The system breaks down complex requests into manageable operations
- **Permission Enforcement**: Strict validation of service level permissions before any action
- **Real-time Communication**: WebSocket API for instant responses
- **State Management**: DynamoDB for reliable data persistence
- **AI Integration**: Claude AI for natural language understanding and generation

## Service Tiers
The system implements a three-tiered service model:

### Basic Tier
- Device status checks
- Power control (on/off)
- Limited to 1 device
- Standard support priority

### Premium Tier
- All Basic tier features
- Volume control
- Limited to 1 device
- Priority support

### Enterprise Tier
- All Premium tier features
- Song control
- Limited to 1 device
- Dedicated support

## Architecture
The application consists of:

- **Frontend**: React-based web interface with Chakra UI
- **Backend**: AWS Lambda functions for request processing
- **Database**: DynamoDB tables for data persistence
- **AI Integration**: Anthropic Claude for natural language processing
- **API Layer**: REST and WebSocket APIs for communication

### Key Components
1. **Frontend Application**
   - Modern React interface
   - Real-time updates via WebSocket
   - Service level-aware UI components

2. **Backend Services**
   - Lambda functions for request handling
   - DynamoDB for data storage
   - Claude AI integration
   - WebSocket management

3. **Data Storage**
   - Customers table
   - Service levels table
   - Messages table
   - Connections table

## Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- AWS CLI configured with appropriate credentials
- Anthropic API key
- AWS DynamoDB tables set up

## Project Structure
```
agentic-service-bot/
├── frontend/                # React frontend application
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── utils/          # Utility functions
│   │   └── types.ts        # TypeScript definitions
├── infrastructure/         # AWS CDK infrastructure code
│   ├── lib/               # CDK stack definitions
│   └── deploy.sh          # Deployment script
├── lambda/                # Lambda function code
│   ├── chat/             # Chat service Lambda
│   │   ├── handlers/     # Request handlers
│   │   ├── models/       # Data models
│   │   └── services/     # Service implementations
├── tests/                # Test scripts
└── README.md            # This file
```

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-service-bot
```

2. Set up the frontend:
```bash
cd frontend
npm install
```

3. Set up the infrastructure:
```bash
cd infrastructure
npm install
```

4. Configure environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration:
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229
AWS_REGION=us-west-2
CUSTOMERS_TABLE=dev-customers
SERVICE_LEVELS_TABLE=dev-service-levels
```

## Deployment

### Deploy Backend
```bash
cd infrastructure
./deploy.sh --env=dev
```

### Deploy Frontend
```bash
cd frontend
npm run build
# Deploy build directory to your hosting service
```

## Example Requests
The system excels at handling various smart home device requests:

- "What's the status of my living room speaker?"
- "Turn up the volume in the kitchen"
- "Skip to the next song on my bedroom speaker"
- "Turn off all devices in the living room"
- "Move my speaker from the kitchen to the living room"

## Architecture Diagram
[Include an architecture diagram showing the interaction between components]

## Contributing
[Include contribution guidelines]

## License
[Include license information] 