# Agentic Service Bot Project Structure
#
# To use this project:
# 1. Create a folder called "agentic_service_bot"
# 2. Inside this folder, create these files with the contents below
# 3. Run "pip install anthropic" to install required dependencies
# 4. Update the ANTHROPIC_API_KEY in config.py with your actual API key
# 5. Run the project with "python main.py"

# File: agentic_service_bot/main.py
"""
Main application entry point for the Agentic Service Bot
"""
import os
import sys
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, DATA_PATH, DEFAULT_CUSTOMER_ID, DEBUG_MODE

from models.customer import CustomerDB
from utils.llm_client import LLMClient
from agents.service_agent import ServiceAgent

def main():
    """Main application entry point"""
    print("Initializing Smart Home Assistant...")
    
    # Initialize components
    try:
        customer_db = CustomerDB(DATA_PATH)
        llm_client = LLMClient(ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
        agent = ServiceAgent(llm_client, customer_db)
        
        # Get customer for this session
        customer_id = DEFAULT_CUSTOMER_ID
        customer = customer_db.get_customer(customer_id)
        
        if not customer:
            print(f"Error: Customer {customer_id} not found.")
            return
        
        if DEBUG_MODE:
            service_level = customer.service_level
            permissions = customer_db.get_service_level_permissions(service_level)
            allowed_actions = permissions["allowed_actions"]
            print(f"DEBUG: Customer: {customer.name}, Service Level: {service_level}")
            print(f"DEBUG: Allowed actions: {', '.join(allowed_actions)}")
        
        # Main interaction loop
        print(f"Hello, {customer.name}! How can I help you with your smart home devices today?")
        
        while True:
            user_input = input("> ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Thank you for using Smart Home Assistant. Goodbye!")
                break
            
            if DEBUG_MODE and user_input.lower() == "debug":
                summary = agent.get_conversation_summary()
                print(f"DEBUG: Conversation summary: {summary}")
                continue
            
            # Process the request
            response = agent.process_request(customer_id, user_input)
            print(response)
            
    except Exception as e:
        print(f"Error: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
