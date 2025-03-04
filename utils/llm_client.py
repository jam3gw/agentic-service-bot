"""
Utility class for interacting with the Anthropic Claude API
"""
import os
import anthropic
from typing import List, Dict, Any, Optional

class LLMClient:
    """Client for interacting with the Anthropic Claude API"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        """
        Initialize the LLM client
        
        Args:
            api_key: Anthropic API key
            model: Model to use for generation
        """
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response using Anthropic's Claude API
        
        Args:
            prompt: The user prompt to respond to
            context: Additional context for the system prompt
            
        Returns:
            The generated response text
        """
        system_prompt = self._build_system_prompt(context)
        
        try:
            message = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            return message.content[0].text
        except Exception as e:
            print(f"Error calling Anthropic API: {e}")
            return "I apologize, but I'm having trouble processing your request right now."
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build a system prompt based on context
        
        Args:
            context: Additional context for the system prompt
            
        Returns:
            The system prompt
        """
        if not context:
            return "You are a helpful AI assistant for a smart home device company."
        
        # Start with base prompt
        system_prompt = "You are an AI assistant for a smart home device company. "
        
        # Add customer info if available
        if "customer" in context:
            customer = context["customer"]
            system_prompt += f"You are speaking with {customer.name}, who has a {customer.service_level} service level. "
        
        # Add device info if available
        if "devices" in context and context["devices"]:
            devices_desc = ", ".join([f"{d['type']} in the {d['location'].replace('_', ' ')}" for d in context["devices"]])
            system_prompt += f"They have the following devices: {devices_desc}. "
        
        # Add service level permissions
        if "permissions" in context:
            allowed = ", ".join(context["permissions"]["allowed_actions"])
            system_prompt += f"Their service level permits these actions: {allowed}. "
        
        # Add specific instructions based on context
        if "action_allowed" in context:
            if context["action_allowed"]:
                system_prompt += "The requested action IS permitted for this customer's service level. Respond helpfully and proceed with the request. "
            else:
                system_prompt += (
                    "The requested action is NOT permitted for this customer's service level. "
                    "Politely explain this limitation and offer to connect them with customer support to upgrade their service. "
                    "Do not explain specific pricing or offer workarounds."
                )
        
        return system_prompt