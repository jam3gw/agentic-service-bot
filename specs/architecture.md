# System Architecture

## Overview

The Agentic Service Bot uses a serverless architecture on AWS, with a React frontend and WebSocket communication for real-time interactions. The system is designed to be scalable, cost-effective, and maintainable.

## Architecture Diagram

```
┌─────────────┐     ┌───────────────┐     ┌──────────────┐
│             │     │               │     │              │
│   Frontend  │◄────┤  WebSocket    │◄────┤  Lambda      │
│   (React)   │     │  API Gateway  │     │  Functions   │
│             │     │               │     │              │
└─────────────┘     └───────────────┘     └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐     ┌──────────────┐
                                          │              │     │              │
                                          │  DynamoDB    │     │  Anthropic   │
                                          │  Tables      │     │  Claude API  │
                                          │              │     │              │
                                          └──────────────┘     └──────────────┘
```

## Components

### Frontend

- **Technology**: React with TypeScript
- **UI Framework**: Chakra UI
- **Key Components**:
  - Chat interface
  - Customer selection
  - Message history display
  - Real-time status indicators

### Backend

#### API Gateway

- WebSocket API for real-time bidirectional communication
- Routes for connect, disconnect, and message events
- Custom authorizers for authentication

#### Lambda Functions

- **Chat Handler**: Processes incoming messages, interacts with Claude API, and sends responses
- **Connection Handler**: Manages WebSocket connections
- **Seed Function**: Initializes database with sample data

#### DynamoDB Tables

- **Messages Table**: Stores conversation history
  - Partition Key: `conversationId`
  - Sort Key: `timestamp`
  - GSI: `userId` for user-specific queries
- **Customers Table**: Stores customer information
  - Partition Key: `id`
  - Contains customer details and device information
- **Service Levels Table**: Defines permission tiers
  - Partition Key: `level`
  - Contains allowed actions and limits
- **Connections Table**: Manages WebSocket connections
  - Partition Key: `connectionId`
  - TTL attribute for automatic cleanup

### External Services

- **Anthropic Claude API**: Provides natural language understanding and generation
  - Model: claude-3-opus-20240229
  - Used for request analysis and response generation

## Data Flow

1. **User Request**:
   - User sends message via WebSocket
   - Message includes customer ID and request text

2. **Request Processing**:
   - Lambda receives message from WebSocket API
   - Retrieves customer data and service level
   - Analyzes request using RequestAnalyzer
   - Checks permissions based on service level

3. **AI Processing**:
   - Sends request to Claude API with context
   - Receives AI-generated response

4. **Response Delivery**:
   - Stores message in DynamoDB
   - Sends response back through WebSocket
   - Updates conversation history

## Deployment

- AWS CDK for infrastructure as code
- Environment-specific configurations (dev, prod)
- Automated deployment pipeline

## Security Considerations

- API Gateway authorization
- IAM roles with least privilege
- Environment variables for sensitive information
- CORS configuration for frontend access
- DynamoDB encryption at rest

## Scalability

- Serverless architecture scales automatically
- DynamoDB on-demand capacity
- Stateless Lambda functions
- Connection management with TTL

## Monitoring and Logging

- CloudWatch Logs for Lambda functions
- CloudWatch Metrics for API Gateway
- Custom logging in application code
- Error tracking and reporting 