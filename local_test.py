#!/usr/bin/env python3
"""
Local test script for the Agentic Service Bot
This script simulates the Lambda function locally for testing purposes
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, Any

# Set environment variables for local testing
os.environ['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', 'your-api-key-here')
os.environ['ANTHROPIC_MODEL'] = 'claude-3-opus-20240229'
os.environ['MESSAGES_TABLE'] = 'messages'
os.environ['CUSTOMERS_TABLE'] = 'customers'
os.environ['SERVICE_LEVELS_TABLE'] = 'service-levels'
os.environ['CONNECTIONS_TABLE'] = 'connections'

# Import the lambda function
import importlib.util
lambda_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'lambda/chat/index.py'))
spec = importlib.util.spec_from_file_location("lambda_chat", lambda_path)
lambda_chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lambda_chat)

# Mock DynamoDB tables
class MockDynamoDBTable:
    """Mock DynamoDB table for local testing"""
    
    def __init__(self, name: str, data_file: str = None):
        self.name = name
        self.items = {}
        
        # Load data from file if provided
        if data_file and os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = json.load(f)
                if name == 'customers':
                    for item in data['customers']:
                        self.items[item['id']] = item
                elif name == 'service-levels':
                    for level, item in data['service_levels'].items():
                        self.items[level] = item
    
    def get_item(self, Key: Dict[str, Any]) -> Dict[str, Any]:
        """Mock get_item operation"""
        key_name = list(Key.keys())[0]
        key_value = Key[key_name]
        
        if key_value in self.items:
            return {'Item': self.items[key_value]}
        return {}
    
    def put_item(self, Item: Dict[str, Any]) -> Dict[str, Any]:
        """Mock put_item operation"""
        if 'id' in Item:
            self.items[Item['id']] = Item
        elif 'level' in Item:
            self.items[Item['level']] = Item
        elif 'connectionId' in Item:
            self.items[Item['connectionId']] = Item
        elif 'conversationId' in Item and 'timestamp' in Item:
            key = f"{Item['conversationId']}#{Item['timestamp']}"
            self.items[key] = Item
        
        return {}

def main():
    """Main function to test the Lambda function locally"""
    print("Starting local test of Agentic Service Bot...")
    
    # Load sample data
    sample_data_file = os.path.join(os.path.dirname(__file__), 'data/sample_data.json')
    
    # Create mock DynamoDB tables
    customers_table = MockDynamoDBTable('customers', sample_data_file)
    service_levels_table = MockDynamoDBTable('service-levels', sample_data_file)
    messages_table = MockDynamoDBTable('messages')
    connections_table = MockDynamoDBTable('connections')
    
    # Patch the Lambda function to use mock tables
    lambda_chat.customers_table = customers_table
    lambda_chat.service_levels_table = service_levels_table
    lambda_chat.messages_table = messages_table
    lambda_chat.connections_table = connections_table
    
    # Test customer selection
    print("\nAvailable customers:")
    for customer_id, customer in customers_table.items.items():
        print(f"  {customer_id}: {customer['name']} ({customer['service_level']} tier)")
    
    # Main interaction loop
    while True:
        # Get customer ID
        customer_id = input("\nEnter customer ID (or 'quit' to exit): ")
        if customer_id.lower() in ['quit', 'exit', 'q']:
            break
        
        # Validate customer ID
        customer_data = customers_table.get_item({'id': customer_id})
        if 'Item' not in customer_data:
            print(f"Error: Customer {customer_id} not found.")
            continue
        
        customer = customer_data['Item']
        print(f"\nConnected as {customer['name']} ({customer['service_level']} tier)")
        
        # Get service level permissions
        service_level = customer['service_level']
        permissions = service_levels_table.get_item({'level': service_level})['Item']
        print(f"Allowed actions: {', '.join(permissions['allowed_actions'])}")
        
        # Chat loop for this customer
        while True:
            # Get user input
            user_input = input("\nYou: ")
            if user_input.lower() in ['back', 'b', 'change customer']:
                break
            if user_input.lower() in ['quit', 'exit', 'q']:
                return
            
            # Process the request
            print("Bot: ", end="", flush=True)
            start_time = time.time()
            response = lambda_chat.process_request(customer_id, user_input)
            end_time = time.time()
            
            print(response)
            print(f"[Response time: {end_time - start_time:.2f}s]")

if __name__ == "__main__":
    main()
    print("\ndone") 