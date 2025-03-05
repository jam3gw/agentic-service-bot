"""
Consolidated API tests package.

This package contains integration tests for the API Lambda function,
focusing on testing with real dependencies where possible.
"""

from .test_api_integration import TestApiIntegration
from .test_capability_integration import TestCapabilityIntegration
from .test_device_integration import TestDeviceIntegration
from .test_dynamodb_integration import TestDynamoDBIntegration

__all__ = ['TestApiIntegration', 'TestCapabilityIntegration', 'TestDeviceIntegration', 'TestDynamoDBIntegration'] 