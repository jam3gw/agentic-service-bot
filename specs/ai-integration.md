# AI Integration

## Overview

The Agentic Service Bot integrates with Anthropic's Claude AI to provide natural language understanding and generation capabilities. This integration enables the system to process customer requests, analyze their intent, and generate appropriate responses.

## Claude AI Model

- **Model**: claude-3-haiku-20240307
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

## Metrics and Monitoring

The system tracks detailed metrics for Anthropic API calls to monitor performance, costs, and usage patterns:

### CloudWatch Metrics

The following metrics are emitted to CloudWatch under the `ServiceBot` namespace:

1. **AnthropicApiCalls**: Count of API calls made to Anthropic
   - Dimensions:
     - Environment (dev, prod)
     - ApiName (messages.create.stage1, messages.create.stage2, etc.)
     - Success (true, false)

2. **AnthropicApiLatency**: Duration of API calls in milliseconds
   - Dimensions:
     - Environment (dev, prod)
     - ApiName (messages.create.stage1, messages.create.stage2, etc.)

3. **AnthropicApiTokens**: Number of tokens consumed by API calls
   - Dimensions:
     - Environment (dev, prod)
     - ApiName (messages.create.stage1, messages.create.stage2, etc.)

### Metrics Implementation

The system uses a custom `MetricsClient` class to emit metrics to CloudWatch:

- Tracks both detailed metrics (with ApiName dimension) and aggregated metrics
- Handles failures gracefully with a mock client implementation
- Logs detailed information about each API call
- Supports environment-specific metrics

### Monitoring Dashboards

CloudWatch dashboards are set up to monitor:
- API call volume over time
- Average latency by API endpoint
- Token usage and associated costs
- Error rates and failure patterns
- Unusual spikes in usage or latency

## Implementation Details

The AI integration is implemented in the `lambda/chat/services/anthropic_service.py` file:

```python
# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')

# Example function for generating responses
def generate_response(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a response using the Anthropic Claude API.
    
    Args:
        prompt: The prompt to send to Claude
        context: Additional context for the prompt
        
    Returns:
        The generated response text
    """
    # Track API call latency and token usage
    start_time = time.time()
    
    # Call Claude API
    response = anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1000,
        system=build_system_prompt(context or {}),
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Calculate metrics
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    total_tokens = input_tokens + output_tokens
    
    # Emit metrics
    metrics_client.track_anthropic_api_call(
        api_name="messages.create",
        duration_ms=duration_ms,
        tokens=total_tokens,
        success=True
    )
    
    return response.content[0].text
```

## Future Enhancements

1. **Fine-tuning**: Potential to fine-tune the model on domain-specific data
2. **Multi-modal Support**: Adding image understanding for device troubleshooting
3. **Personalization**: Adapting responses based on customer history and preferences
4. **Proactive Suggestions**: Using AI to suggest helpful actions based on context
5. **Sentiment Analysis**: Detecting customer frustration and adapting responses accordingly
6. **Cost Optimization**: Implementing strategies to reduce token usage and API costs
7. **Metrics-driven Improvements**: Using collected metrics to identify and address performance bottlenecks
``` 