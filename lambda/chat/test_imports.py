#!/usr/bin/env python3
"""
Test script to verify imports in the Agentic Service Bot.
"""

import os
import sys
import json

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path}")

try:
    print("\nTesting imports...")
    
    # Test importing handlers
    from handlers.websocket_handler import handle_connect, handle_message, CORS_HEADERS
    print("✅ Successfully imported from handlers.websocket_handler")
    
    # Test importing services
    from services.request_processor import process_request
    print("✅ Successfully imported from services.request_processor")
    
    # Test importing models
    from models.customer import Customer
    print("✅ Successfully imported from models.customer")
    
    # Test importing analyzers
    from analyzers.request_analyzer import RequestAnalyzer
    print("✅ Successfully imported from analyzers.request_analyzer")
    
    # Test importing index
    import index
    print("✅ Successfully imported index")
    
    print("\nAll imports successful! The modularization is working correctly.")
    
except ImportError as e:
    print(f"\n❌ Import error: {str(e)}")
    print(f"Module path that failed: {e.__traceback__.tb_frame.f_globals['__name__']}")
    print(f"Line number: {e.__traceback__.tb_lineno}")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}") 