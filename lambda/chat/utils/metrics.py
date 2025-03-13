"""
Metrics utility for the Agentic Service Bot.

This module provides functions for emitting custom metrics to CloudWatch,
particularly for tracking Anthropic API calls.
"""

import os
import time
import logging
import boto3
import json
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG level for more verbose logging

# Constants
METRIC_NAMESPACE = "ServiceBot"

class MetricNames:
    """Constants for metric names."""
    ANTHROPIC_API_LATENCY = "AnthropicApiLatency"
    ANTHROPIC_API_TOKENS = "AnthropicApiTokens"
    ANTHROPIC_API_CALLS = "AnthropicApiCalls"


class MetricsClient:
    """Client for emitting metrics to CloudWatch."""
    
    def __init__(self):
        self._client = None
        self._environment = os.environ.get('ENVIRONMENT', 'dev')
        logger.debug(f"Initialized MetricsClient with environment: {self._environment}")
    
    @property
    def client(self):
        """Lazy initialization of CloudWatch client."""
        if self._client is None:
            try:
                logger.debug("Initializing CloudWatch client")
                self._client = boto3.client('cloudwatch')
                logger.debug("CloudWatch client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CloudWatch client: {e}")
                # Return a mock client that logs but doesn't fail
                return MockCloudWatchClient()
        return self._client
    
    def track_anthropic_api_call(self, 
                                api_name: str, 
                                duration_ms: float, 
                                tokens: int, 
                                success: bool = True) -> bool:
        """
        Track Anthropic API call metrics.
        
        Args:
            api_name: Name of the Anthropic API being called (e.g., 'messages.create')
            duration_ms: Duration of the API call in milliseconds
            tokens: Number of tokens used in the API call
            success: Whether the API call was successful
            
        Returns:
            bool: Whether the metrics were successfully emitted
        """
        logger.debug(f"Tracking Anthropic API call: api_name={api_name}, duration_ms={duration_ms}, tokens={tokens}, success={success}")
        
        # Emit metrics with both detailed and aggregated dimensions
        try:
            # First, emit metrics with detailed dimensions (including ApiName)
            self._emit_detailed_metrics(api_name, duration_ms, tokens, success)
            
            # Then, emit metrics with aggregated dimensions (without ApiName)
            self._emit_aggregated_metrics(duration_ms, tokens, success)
            
            logger.info(f"Emitted Anthropic API metrics for {api_name}: duration={duration_ms}ms, tokens={tokens}")
            return True
        except Exception as e:
            logger.error(f"Failed to emit Anthropic API metrics: {e}", exc_info=True)
            return False
    
    def _emit_detailed_metrics(self, api_name: str, duration_ms: float, tokens: int, success: bool) -> None:
        """Emit metrics with detailed dimensions including ApiName."""
        # Ensure success value is lowercase string
        success_str = str(success).lower()
        
        metric_data = [
            # Track API call count
            {
                'MetricName': MetricNames.ANTHROPIC_API_CALLS,
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': self._environment},
                    {'Name': 'ApiName', 'Value': api_name},
                    {'Name': 'Success', 'Value': success_str}
                ]
            },
            # Track API call latency
            {
                'MetricName': MetricNames.ANTHROPIC_API_LATENCY,
                'Value': duration_ms,
                'Unit': 'Milliseconds',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': self._environment},
                    {'Name': 'ApiName', 'Value': api_name}
                ]
            },
            # Track token usage
            {
                'MetricName': MetricNames.ANTHROPIC_API_TOKENS,
                'Value': tokens,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': self._environment},
                    {'Name': 'ApiName', 'Value': api_name}
                ]
            }
        ]
        
        logger.debug(f"Emitting detailed metrics: {json.dumps(metric_data, indent=2)}")
        response = self.client.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=metric_data
        )
        logger.debug(f"Detailed metrics response: {response}")
    
    def _emit_aggregated_metrics(self, duration_ms: float, tokens: int, success: bool) -> None:
        """Emit metrics with aggregated dimensions (without ApiName)."""
        # Ensure success value is lowercase string
        success_str = str(success).lower()
        
        metric_data = [
            # Track API call count - with Environment and Success dimensions
            {
                'MetricName': MetricNames.ANTHROPIC_API_CALLS,
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': self._environment},
                    {'Name': 'Success', 'Value': success_str}
                ]
            },
            # Also emit total API calls with just Environment dimension
            {
                'MetricName': MetricNames.ANTHROPIC_API_CALLS,
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': self._environment}
                ]
            },
            # Track API call latency - with just Environment dimension
            {
                'MetricName': MetricNames.ANTHROPIC_API_LATENCY,
                'Value': duration_ms,
                'Unit': 'Milliseconds',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': self._environment}
                ]
            },
            # Track token usage - with just Environment dimension
            {
                'MetricName': MetricNames.ANTHROPIC_API_TOKENS,
                'Value': tokens,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': self._environment}
                ]
            }
        ]
        
        logger.debug(f"Emitting aggregated metrics: {json.dumps(metric_data, indent=2)}")
        response = self.client.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=metric_data
        )
        logger.debug(f"Aggregated metrics response: {response}")


class MockCloudWatchClient:
    """Mock CloudWatch client for when the real client fails to initialize."""
    
    def put_metric_data(self, **kwargs):
        """Mock implementation that logs but doesn't actually send metrics."""
        logger.warning(f"MOCK: Would have sent metrics: {json.dumps(kwargs, indent=2)}")
        return {"ResponseMetadata": {"RequestId": "mock-request-id", "HTTPStatusCode": 200}}


# Create a singleton instance
metrics_client = MetricsClient()


def time_function(func):
    """
    Decorator to time a function execution.
    
    Args:
        func: The function to time
        
    Returns:
        The wrapped function
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        return result, duration_ms
    return wrapper