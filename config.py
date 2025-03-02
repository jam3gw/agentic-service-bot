"""
Configuration settings for the Agentic Service Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Anthropic API settings
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set. Please set it in your .env file.")

ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', "claude-3-opus-20240229")  # Or any other appropriate model

# Service settings
DATA_PATH = "data/customers.json"
DEFAULT_CUSTOMER_ID = "cust_001"  # For demo purposes

# Agent settings
MAX_CONVERSATION_TURNS = 10
DEBUG_MODE = True