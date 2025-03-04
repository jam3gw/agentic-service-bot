# AI Integration

## Overview

The Agentic Service Bot integrates with Anthropic's Claude AI to provide natural language understanding and generation capabilities. This integration enables the system to process customer requests, analyze their intent, and generate appropriate responses.

## Claude AI Model

- **Model**: claude-3-opus-20240229
- **Provider**: Anthropic
- **Capabilities**:
  - Natural language understanding
  - Context-aware responses
  - Request classification
  - Structured output generation
  - Multi-turn conversation

## Integration Points

### Request Analysis

The system uses Claude AI to analyze customer requests and determine:
- Request type (device relocation, volume change, etc.)
- Required actions
- Entities mentioned (devices, locations, etc.)
- Customer intent

### Response Generation

Claude AI generates natural language responses based on:
- Request analysis results
- Customer service level
- Available actions
- Device status
- Conversation history

## System Prompts

The system uses carefully crafted prompts to guide Claude's behavior:

### Base System Prompt

```
You are a helpful smart home assistant service bot. Your job is to assist customers with their smart home devices.
You can help with device status, relocation, volume control, and other actions depending on the customer's service level.
Always be polite, concise, and helpful. If a customer requests an action that is not allowed at their service level,
explain the limitation and suggest upgrading their service.
```

### Request Analysis Prompt

```
Analyze the following customer request and determine:
1. The type of request (device_relocation, volume_change, device_status, etc.)
2. The specific device mentioned (if any)
3. The location mentioned (if any)
4. Any other relevant parameters

Customer request: "{customer_request}"

Provide your analysis in JSON format.
```

### Response Generation Prompt

```
Generate a response to the following customer request.

Customer: {customer_name}
Service Level: {service_level}
Devices: {devices}
Request: "{customer_request}"
Request Type: {request_type}
Required Actions: {required_actions}
Allowed Actions: {allowed_actions}

If the required actions are not allowed for this customer's service level, politely explain the limitation
and suggest upgrading their service. Otherwise, provide a helpful response that addresses their request.
```

## Error Handling

The AI integration includes robust error handling:

1. **API Failures**:
   - Retry logic with exponential backoff
   - Fallback responses for API outages
   - Error logging and monitoring

2. **Misunderstood Requests**:
   - Clarification responses when intent is unclear
   - Suggestions for alternative phrasings
   - Fallback to general help when request cannot be understood

3. **Content Filtering**:
   - Handling of inappropriate requests
   - Safe responses for edge cases
   - Redirection to human support when necessary

## Performance Considerations

- **Latency**: Responses should be generated within 5 seconds
- **Concurrency**: System handles multiple simultaneous requests
- **Token Usage**: Optimized prompts to minimize token consumption
- **Caching**: Common responses may be cached to improve performance

## Implementation Details

The AI integration is implemented in the `lambda/chat/index.py` file:

```python
# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(
    api_key=os.environ.get('ANTHROPIC_API_KEY')
)
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-opus-20240229')

# Example function for generating responses
def generate_response(customer, request, conversation_history):
    # Construct the prompt with customer context
    prompt = f"""
    You are a helpful smart home assistant service bot...
    
    Customer: {customer.name}
    Service Level: {customer.service_level}
    Devices: {json.dumps(customer.devices)}
    Request: "{request}"
    
    Previous conversation:
    {format_conversation_history(conversation_history)}
    """
    
    # Call Claude API
    response = anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1000,
        system=prompt,
        messages=[
            {"role": "user", "content": request}
        ]
    )
    
    return response.content[0].text
```

## Future Enhancements

1. **Fine-tuning**: Potential to fine-tune the model on domain-specific data
2. **Multi-modal Support**: Adding image understanding for device troubleshooting
3. **Personalization**: Adapting responses based on customer history and preferences
4. **Proactive Suggestions**: Using AI to suggest helpful actions based on context
5. **Sentiment Analysis**: Detecting customer frustration and adapting responses accordingly 