"""
End-to-end tests for the Agentic Service Bot Capabilities API endpoint.

This module tests the capabilities API endpoint:
- GET /api/capabilities
"""

import os
import sys
import json
import pytest
import requests
from pathlib import Path

# Add the project root to the Python path so that imports work correctly
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "test"

# API URLs for testing
REST_API_URL = "https://k4w64ym45e.execute-api.us-west-2.amazonaws.com/dev/api"


def test_get_capabilities():
    """
    Test the GET /capabilities endpoint.
    
    This test verifies that the endpoint returns the service capabilities
    with the correct structure.
    """
    # Make the API request
    response = requests.get(f"{REST_API_URL}/capabilities")
    
    # Verify response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.text}"
    
    # Parse response body
    data = response.json()
    
    # Verify response structure
    assert "capabilities" in data, "Response should contain 'capabilities' key"
    assert isinstance(data["capabilities"], list), "'capabilities' should be a list"
    
    # If there are capabilities, verify their structure
    if data["capabilities"]:
        capability = data["capabilities"][0]
        assert "id" in capability, "Capability should have an 'id'"
        assert "name" in capability, "Capability should have a 'name'"
        assert "description" in capability, "Capability should have a 'description'"
        
        # Check for service levels in different formats
        has_service_levels = False
        if "basic" in capability and "premium" in capability and "enterprise" in capability:
            has_service_levels = True
        elif "serviceLevels" in capability:
            has_service_levels = True
            assert isinstance(capability["serviceLevels"], list), "'serviceLevels' should be a list"
        elif "tiers" in capability:
            has_service_levels = True
            assert isinstance(capability["tiers"], dict), "'tiers' should be a dictionary"
        
        assert has_service_levels, "Capability should have service level information" 