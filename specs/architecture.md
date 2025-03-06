# System Architecture

## Overview

The Agentic Service Bot uses a serverless architecture on AWS, with a React frontend and REST API communication for interactions. The system is designed to be scalable, cost-effective, and maintainable.

## Architecture Diagram

```
┌─────────────┐     ┌───────────────┐     ┌──────────────┐
│             │     │               │     │              │
│   Frontend  │◄────┤  REST API     │◄────┤  Lambda      │
│   (React)   │     │  Gateway      │     │  Functions   │
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
  - Status indicators

### Backend

#### API Gateway

- REST API for communication
- Endpoints for chat, customers, devices, and capabilities
- CORS configuration for frontend access

#### Lambda Functions

- **Chat Handler**: Processes incoming messages, interacts with Claude API, and returns responses
- **API Handler**: Manages customer and device data
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

### External Services

- **Anthropic Claude API**: Provides natural language understanding and generation
  - Model: claude-3-opus-20240229
  - Used for request analysis and response generation

## Data Flow

1. **User Request**:
   - User sends message via REST API
   - Request includes customer ID and message text

2. **Request Processing**:
   - Lambda receives message from API Gateway
   - Retrieves customer data and service level
   - Analyzes request using RequestAnalyzer
   - Checks permissions based on service level

3. **AI Processing**:
   - Sends request to Anthropic API with context
   - Receives AI-generated response

4. **Response Delivery**:
   - Stores message in DynamoDB
   - Returns response through REST API
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

## Monitoring and Logging

- CloudWatch Logs for Lambda functions
- CloudWatch Metrics for API Gateway
- Custom logging in application code
- Error tracking and reporting 