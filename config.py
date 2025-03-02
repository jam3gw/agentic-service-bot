"""
Configuration settings for the Agentic Service Bot
"""
# Anthropic API settings
ANTHROPIC_API_KEY = "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"
ANTHROPIC_MODEL = "claude-3-opus-20240229"  # Or any other appropriate model

# Service settings
DATA_PATH = "data/customers.json"
DEFAULT_CUSTOMER_ID = "cust_001"  # For demo purposes

# Agent settings
MAX_CONVERSATION_TURNS = 10
DEBUG_MODE = True