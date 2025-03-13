# Agentic Service Bot Diagrams

This directory contains PlantUML diagrams that visualize the architecture and flow of the Agentic Service Bot application.

## Diagrams Overview

1. **System Architecture** (`system_architecture.puml`): High-level overview of the system components and their interactions.
2. **Chat Sequence** (`chat_sequence.puml`): Sequence diagram showing the flow of a chat message through the system.
3. **Anthropic API Flow** (`anthropic_api_flow.puml`): Detailed diagram of the Anthropic API interaction flow.
4. **Class Diagram** (`class_diagram.puml`): Class diagram showing the key components and their relationships.
5. **Service Level Permissions** (`service_level_permissions.puml`): Activity diagram showing the service level permissions flow.
6. **Metrics Flow** (`metrics_flow.puml`): Diagram showing the metrics collection and display flow.

## Viewing the Diagrams

### Option 1: Online PlantUML Server

1. Go to [PlantUML Online Server](https://www.plantuml.com/plantuml/uml/)
2. Copy the content of any `.puml` file and paste it into the editor
3. The diagram will be rendered automatically

### Option 2: VS Code Extension

1. Install the [PlantUML extension](https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml) for VS Code
2. Open any `.puml` file in VS Code
3. Use Alt+D to preview the diagram

### Option 3: Generate PNG/SVG Files

You can generate PNG or SVG files from the PlantUML diagrams using the PlantUML command-line tool:

```bash
java -jar plantuml.jar *.puml
```

This will generate PNG files for all the diagrams in the current directory.

## Understanding the Diagrams

### System Architecture

This diagram shows the high-level components of the system, including:
- Frontend
- API Gateway (REST and WebSocket)
- Lambda functions
- DynamoDB tables
- Anthropic Claude API
- CloudWatch monitoring

### Chat Sequence

This sequence diagram shows the detailed flow of a chat message through the system, from the user sending a message to receiving a response.

### Anthropic API Flow

This diagram focuses on the interaction with the Anthropic Claude API, showing:
- Stage 1: Request Type Identification
- Stage 2: Context Extraction
- Response Generation
- Metrics emission

### Class Diagram

This diagram shows the key classes and their relationships in the application, organized by packages:
- Models
- Services
- Handlers
- Utils

### Service Level Permissions

This activity diagram shows how service level permissions are checked and enforced, including:
- Basic, Premium, and Enterprise service levels
- Different actions allowed for each service level
- Device state checks
- Response generation based on permissions

### Metrics Flow

This diagram shows how metrics are collected, stored, and displayed, including:
- Metrics emission from the Lambda function
- CloudWatch metrics storage
- Dashboard display
- Alarm configuration
- Notification flow

## Updating the Diagrams

When making changes to the application, please update these diagrams to keep them in sync with the code. This will help maintain accurate documentation of the system architecture and flow. 