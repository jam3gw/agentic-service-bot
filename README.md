# Agentic Service Bot

A smart home assistant service bot that handles customer interactions using AI. The bot processes customer requests, manages device operations, and provides responses based on the customer's service level permissions.

## Features

- Natural language processing of customer requests
- Service level-based permission system
- Smart home device management
- Conversation history tracking
- Intelligent request analysis and response generation
- Support for device relocation requests
- REST API for communication between frontend and backend

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- AWS CLI configured with appropriate credentials
- An Anthropic API key (for Claude LLM integration)

## Project Structure

```
agentic-service-bot/
├── frontend/                # React frontend application
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── utils/           # Utility functions
│   │   └── types.ts         # TypeScript type definitions
├── infrastructure/          # AWS CDK infrastructure code
│   ├── lib/                 # CDK stack definitions
│   └── deploy.sh            # Deployment script
├── lambda/                  # Lambda function code
│   ├── chat/                # Chat service Lambda
│   │   ├── handlers/        # Request handlers
│   │   ├── models/          # Data models
│   │   └── services/        # Service implementations
├── tests/                   # Test scripts
│   ├── e2e/                 # End-to-end tests
│   └── run_api_tests.py     # API test runner
├── docs/                    # Documentation
│   └── websocket-to-rest-migration.md  # Migration guide
└── README.md                # This file
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

4. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and add your Anthropic API key
# Replace 'your-api-key-here' with your actual API key
```

Your `.env` file should look like this:
```
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229
```

## Deployment

### Deploy the Backend

Use the deployment script to deploy the backend infrastructure:

```bash
cd infrastructure
./deploy.sh --env=dev
```

This will deploy the following resources:
- Lambda functions for handling API requests
- DynamoDB tables for storing data
- REST API Gateway for exposing endpoints
- IAM roles and policies for security

### Deploy the Frontend

Deploy the frontend to your hosting service:

```bash
cd frontend
npm run build
# Deploy the build directory to your hosting service
```

## Running the Application

1. Start the frontend development server:
```bash
cd frontend
npm start
```

2. Access the application at http://localhost:3000

## API Endpoints

The application uses REST API endpoints for communication:

- **POST /api/chat**: Send a chat message to the bot
  - Request: `{ "customerId": "string", "message": "string" }`
  - Response: `{ "message": "string", "timestamp": "string", "messageId": "string", "conversationId": "string" }`

- **GET /api/chat/history/{customerId}**: Get chat history for a customer
  - Response: `{ "messages": [{ "id": "string", "text": "string", "sender": "string", "timestamp": "string", "conversationId": "string" }], "customerId": "string" }`

- **GET /api/customers/{customerId}/devices**: Get devices for a customer
  - Response: `{ "devices": [{ "id": "string", "name": "string", "type": "string", "location": "string", "status": "string", "capabilities": ["string"] }] }`

- **GET /api/capabilities**: Get service capabilities
  - Response: `{ "capabilities": [{ "id": "string", "name": "string", "description": "string", "tiers": { "basic": boolean, "premium": boolean, "enterprise": boolean }, "category": "string" }] }`

## Testing

```bash
# Run all tests
./tests/run_api_tests.py

# Run a specific test
./tests/run_api_tests.py --test=capabilities

# Run tests with a specific customer ID
./tests/run_api_tests.py --customer=cust_002

# Run a conversation test for 2 minutes
./tests/run_api_tests.py --test=conversation --duration=120

# Enable verbose logging
./tests/run_api_tests.py --verbose
```

Available test types:
- `all`: Run all tests
- `capabilities`: Test the capabilities endpoint

## Debug Mode

The application includes a debug mode that can be enabled in the frontend:

1. Open the browser console
2. Set `localStorage.setItem('debug', 'true')`
3. Refresh the page

When debug mode is enabled:
- API requests and responses are logged to the console
- Additional debugging information is displayed
- Error details are shown

## Documentation

For more information about the project, refer to the following documentation:

- [WebSocket to REST Migration Guide](docs/websocket-to-rest-migration.md): Details about the migration from WebSocket to REST API
- [Architecture](specs/architecture.md): System architecture and components
- [Frontend](specs/frontend.md): Frontend components and design
- [API Documentation](docs/README.md): Detailed documentation of the API endpoints and contracts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here] 