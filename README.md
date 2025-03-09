# Agentic Service Bot

An agentic service bot that handles customer interactions using AI. The bot processes customer requests, manages device operations, and provides responses based on the customer's service level permissions (Basic, Premium, or Enterprise).

## Features

- Natural language processing of customer requests
- Three-tiered service level system:
  - Basic: Device status and power control
  - Premium: Basic features plus volume control
  - Enterprise: All features including song control
- Device management with tier-based capabilities
- Conversation history tracking
- Intelligent request analysis and response generation
- Modern React frontend with Chakra UI
- REST API for communication between frontend and backend
- DynamoDB for data persistence

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- AWS CLI configured with appropriate credentials
- An Anthropic API key (for Claude LLM integration)
- AWS DynamoDB tables set up for your environment

## Project Structure

```
agentic-service-bot/
├── frontend/                # React frontend application
│   ├── src/                 # Source code
│   │   ├── components/      # React components including CapabilitiesTable
│   │   ├── utils/          # Utility functions and API service
│   │   └── types.ts        # TypeScript type definitions
├── infrastructure/         # AWS CDK infrastructure code
│   ├── lib/               # CDK stack definitions
│   └── deploy.sh          # Deployment script
├── lambda/                # Lambda function code
│   ├── chat/             # Chat service Lambda
│   │   ├── handlers/     # Request handlers
│   │   ├── models/       # Data models
│   │   └── services/     # Service implementations
├── tests/                # Test scripts
│   ├── e2e/             # End-to-end tests
│   └── run_api_tests.py # API test runner
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

4. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your configuration
```

Your `.env` file should include:
```
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229
AWS_REGION=us-west-2
CUSTOMERS_TABLE=dev-customers
SERVICE_LEVELS_TABLE=dev-service-levels
```

## Deployment

### Deploy the Backend

Deploy the backend infrastructure:

```bash
cd infrastructure
./deploy.sh --env=dev
```

This will deploy:
- Lambda functions for the API
- DynamoDB tables (customers and service levels)
- REST API Gateway
- Required IAM roles and policies

### Deploy the Frontend

Deploy the frontend:

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

## Service Levels and Capabilities

The application supports three service levels:

1. **Basic**
   - Device status checking
   - Power control (on/off)

2. **Premium**
   - All Basic features
   - Volume control
   - Device location information

3. **Enterprise**
   - All Premium features
   - Song control (play, pause, skip)
   - Playlist management

## API Endpoints

The application provides the following REST endpoints:

- **POST /api/chat**
  ```typescript
  Request: {
    customerId: string;
    message: string;
  }
  Response: {
    message: string;
    timestamp: string;
    messageId: string;
    conversationId: string;
  }
  ```

- **GET /api/customers/{customerId}/devices**
  ```typescript
  Response: {
    devices: Array<{
      id: string;
      name: string;
      type: string;
      power: string;
      status: string;
      volume?: number;
      currentSong?: string;
      playlist?: string[];
    }>;
  }
  ```

- **GET /api/service/capabilities**
  ```typescript
  Response: {
    capabilities: Array<{
      id: string;
      name: string;
      description: string;
      tiers: {
        basic: boolean;
        premium: boolean;
        enterprise: boolean;
      };
    }>;
  }
  ```

## Testing

Run the test suite:

```bash
# Set up test data
python seed_test_data.py

# Run API tests
python tests/run_api_tests.py

# Run specific test categories
python tests/run_api_tests.py --test=capabilities
python tests/run_api_tests.py --test=chat
```

The test suite includes:
- API endpoint testing
- Service level permission verification
- Device control testing
- Chat functionality testing

## Development Tools

- **Debug Mode**: Enable in browser console with `localStorage.setItem('debug', 'true')`
- **Test Data Generation**: Use `seed_test_data.py` to create test customers
- **API Testing**: Use the provided test scripts in the `tests` directory

## Documentation

- [API Documentation](docs/README.md): Detailed API specifications
- [Testing Guidelines](tests/README.md): Testing procedures and guidelines

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes using conventional commits
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here] 