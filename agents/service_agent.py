"""
Main service agent for handling customer interactions
"""
from typing import Dict, List, Any, Optional
from models.customer import Customer, CustomerDB
from models.request import RequestAnalyzer
from utils.llm_client import LLMClient

class ServiceAgent:
    """Main agent class that handles customer interactions and makes decisions"""
    
    def __init__(self, llm_client: LLMClient, customer_db: CustomerDB):
        self.llm_client = llm_client
        self.customer_db = customer_db
        self.conversation_history = []
    
    def process_request(self, customer_id: str, user_input: str) -> str:
        """Process a user request and generate a response"""
        # Get customer data
        customer = self.customer_db.get_customer(customer_id)
        if not customer:
            return "Error: Customer not found."
        
        # Identify request type
        request_type = RequestAnalyzer.identify_request_type(user_input)
        if not request_type:
            # If request type can't be determined, just have the LLM respond generically
            return self.llm_client.generate_response(user_input, {"customer": customer})
        
        # Determine required actions for this request
        required_actions = RequestAnalyzer.get_required_actions(request_type)
        
        # Check if all required actions are allowed for this customer's service level
        all_actions_allowed = all(
            self.customer_db.is_action_allowed(customer, action)
            for action in required_actions
        )
        
        # Extract source and destination locations if this is a relocation request
        source_location, destination_location = None, None
        if request_type == "device_relocation":
            source_location, destination_location = RequestAnalyzer.extract_locations(user_input)
        
        # Build context for the LLM
        context = {
            "customer": customer,
            "devices": customer.devices,
            "permissions": self.customer_db.get_service_level_permissions(customer.service_level),
            "action_allowed": all_actions_allowed,
            "request_type": request_type
        }
        
        # For relocation requests, add additional context
        if request_type == "device_relocation" and destination_location:
            context["destination"] = destination_location
            
            # Add specific explanation for relocation requests
            if all_actions_allowed:
                prompt = (
                    f"The customer wants to move their device to the {destination_location.replace('_', ' ')}. "
                    f"They are allowed to do this with their {customer.service_level} service level. "
                    f"Please confirm the relocation and provide any helpful information."
                )
            else:
                prompt = (
                    f"The customer wants to move their device to the {destination_location.replace('_', ' ')}, "
                    f"but their {customer.service_level} service level doesn't allow device relocation. "
                    f"Politely explain this limitation and offer to connect them with customer support to upgrade."
                )
        else:
            # Generic prompt for other request types
            prompt = user_input
        
        # Generate and return the response
        response = self.llm_client.generate_response(prompt, context)
        
        # Store the interaction in conversation history
        self.conversation_history.append({
            "user_input": user_input,
            "request_type": request_type,
            "actions_allowed": all_actions_allowed,
            "response": response
        })
        
        return response
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation for debugging/analysis"""
        return {
            "turns": len(self.conversation_history),
            "requests_denied": sum(1 for turn in self.conversation_history if "actions_allowed" in turn and not turn["actions_allowed"]),
            "requests_allowed": sum(1 for turn in self.conversation_history if "actions_allowed" in turn and turn["actions_allowed"]),
            "request_types": {turn["request_type"] for turn in self.conversation_history if "request_type" in turn and turn["request_type"]}
        }