# API Documentation

This directory contains the API specification for the Agentic Service Bot.

## API Specification

The `api-specification.yaml` file is an OpenAPI 3.0 specification that documents the contract between the backend and frontend. It defines:

- Available endpoints
- Request and response formats
- Required and optional fields
- Data types and descriptions

## Field Definitions

### Chat Endpoint

The `/chat` POST endpoint returns a response with the following fields:

- `message`: The response message from the bot
- `timestamp`: Unix timestamp when the message was created
- `messageId`: Unique identifier for the message (legacy field)
- `id`: Unique identifier for the message
- `conversationId`: Identifier for the conversation this message belongs to
- `customerId`: Identifier for the customer who sent the message

Note: Both `messageId` and `id` are included for backward compatibility. New implementations should use the `id` field.

## Using the API Specification

This specification can be used to:

1. **Generate Client Code**: Use tools like OpenAPI Generator to create client libraries
2. **Validate API Responses**: Ensure responses conform to the defined schema
3. **Document API Changes**: Update this specification when making changes to the API
4. **API Testing**: Use as a reference for writing API tests

## Viewing the API Documentation

You can view this documentation using tools like:

- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [Redoc](https://github.com/Redocly/redoc)
- [Stoplight Studio](https://stoplight.io/studio)

Simply import the `api-specification.yaml` file into any of these tools to visualize the API documentation. 