# WebSocket Connection Analysis

This directory contains tools for analyzing WebSocket connection issues in the Agentic Service Bot application.

## WebSocket Analysis Script

The `analyze_websocket_logs.py` script helps you automatically analyze CloudWatch logs for WebSocket connection issues without requiring manual log pulls. It provides insights into:

1. **GoneException Errors**: Identifies patterns in GoneException errors, which occur when trying to send messages to closed connections.
2. **Connection Lifecycle**: Analyzes connection establishment, message exchange, and disconnection patterns.
3. **Welcome Message Delivery**: Tracks success rates and failures for welcome message delivery.

### Prerequisites

- AWS CLI installed and configured with appropriate permissions
- Python 3.6+
- AWS credentials with CloudWatch Logs read access

### Usage

```bash
# Basic usage (analyzes all aspects for the past 24 hours in dev environment)
python scripts/analyze_websocket_logs.py

# Analyze a specific environment
python scripts/analyze_websocket_logs.py --environment prod

# Analyze logs from the past 48 hours
python scripts/analyze_websocket_logs.py --hours 48

# Run only GoneException analysis
python scripts/analyze_websocket_logs.py --analysis gone

# Run only connection lifecycle analysis
python scripts/analyze_websocket_logs.py --analysis lifecycle

# Run only welcome message analysis
python scripts/analyze_websocket_logs.py --analysis welcome
```

### Command Line Options

- `--environment`, `-e`: Environment to analyze (dev, staging, prod). Default: dev
- `--hours`, `-t`: Hours of logs to analyze. Default: 24
- `--analysis`, `-a`: Type of analysis to run (all, gone, lifecycle, welcome). Default: all

### Example Output

```
Analyzing WebSocket logs for the past 24 hours in dev environment
Using log group: /aws/lambda/dev-chat-handler

Analyzing GoneException errors...
=== GoneException Analysis ===
Found 12 GoneException errors

Connection ID: AbCdEfGhIjK=
  Error count: 8
  First error: 2023-06-15T14:23:45Z
  Sample message: Error sending welcome message to connectionId: AbCdEfGhIjK=: GoneException: The connection with id...
  Welcome message errors: 8
  This suggests connection is closing before welcome message can be sent

Connection ID: LmNoPqRsTuV=
  Error count: 4
  First error: 2023-06-15T15:12:33Z
  Sample message: Error sending message to connectionId: LmNoPqRsTuV=: GoneException: The connection with id...

Analyzing connection lifecycle events...
=== Connection Lifecycle Analysis ===
Found 45 connection events
Complete connection lifecycles: 18
Incomplete connection lifecycles: 3
Short-lived connections (<5s): 7
This suggests connections are being closed prematurely

Analyzing welcome message events...
=== Welcome Message Analysis ===
Found 25 welcome message events
Successful welcome messages: 15
Failed welcome messages: 8
Welcome message retry attempts: 12
Welcome message failure rate: 34.8%
Average retries per message: 0.5

Analysis complete!
```

### Interpreting Results

#### GoneException Analysis
- **High welcome message error counts**: Indicates connections are closing before welcome messages can be sent
- **Multiple errors for the same connection ID**: Suggests retry attempts failing for the same connection

#### Connection Lifecycle Analysis
- **Incomplete lifecycles**: Connections that opened but didn't properly close
- **Short-lived connections**: Connections that lasted less than 5 seconds, suggesting premature closure

#### Welcome Message Analysis
- **High failure rate**: Indicates systematic issues with welcome message delivery
- **High retry counts**: Shows the system is attempting to recover but may need tuning

## Automated Monitoring

You can set up this script to run automatically using a cron job:

```bash
# Add to crontab to run daily at 6 AM
0 6 * * * cd /path/to/project && python scripts/analyze_websocket_logs.py > /path/to/logs/websocket_analysis_$(date +\%Y\%m\%d).log
```

## Additional Analysis Methods

### CloudWatch Metrics and Alarms

You can set up CloudWatch metrics and alarms to monitor WebSocket connection health:

```bash
# Create a CloudWatch alarm for high GoneException rates
aws cloudwatch put-metric-alarm \
  --alarm-name WebSocketGoneExceptionAlarm \
  --alarm-description "Alarm when GoneException rate is too high" \
  --metric-name GoneExceptionCount \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-west-2:123456789012:WebSocketAlerts
```

### AWS X-Ray Tracing

Enable X-Ray tracing for Lambda functions and API Gateway to gain insights into request flows:

1. Add X-Ray tracing to your Lambda function in the CDK stack:
   ```typescript
   const chatFunction = new PythonFunction(this, 'ChatFunction', {
     // ... existing configuration
     tracing: lambda.Tracing.ACTIVE,
   });
   ```

2. Enable X-Ray tracing for API Gateway in the CDK stack:
   ```typescript
   const webSocketStage = new websocketapi.WebSocketStage(this, 'ChatWebSocketStage', {
     // ... existing configuration
     tracingEnabled: true,
   });
   ```

### Custom Logging with Structured Data

Enhance Lambda function logging to include structured data for easier querying:

```python
import json
import logging

def log_connection_event(connection_id, event_type, details=None):
    """Log a structured connection event."""
    log_data = {
        "event_type": event_type,
        "connection_id": connection_id,
        "details": details or {}
    }
    logging.info(f"CONNECTION_EVENT: {json.dumps(log_data)}")
```

## Troubleshooting

If you encounter issues with the analysis script:

1. **Permission errors**: Ensure your AWS credentials have CloudWatch Logs read access
2. **No data found**: Verify the log group name is correct for your environment
3. **Script errors**: Check Python version (3.6+ required) and install any missing dependencies 