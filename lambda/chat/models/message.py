"""
Message model for the Agentic Service Bot.

This module defines the Message class which represents a chat message in the system.
"""

# Standard library imports
from datetime import datetime
from typing import Dict, Any, Optional

class Message:
    """
    Represents a chat message in the system.
    
    Attributes:
        id: Unique identifier for the message
        conversation_id: ID of the conversation this message belongs to
        user_id: ID of the user who sent or received the message
        text: Content of the message
        sender: Who sent the message ('user' or 'bot')
        timestamp: When the message was sent
    """
    
    # Class-level attribute declarations
    id: str = None
    conversation_id: str = None
    user_id: str = None
    text: str = None
    sender: str = None
    timestamp: str = None
    
    def __init__(self, id: str, conversation_id: str, user_id: str, text: str, 
                 sender: str, timestamp: Optional[str] = None):
        """
        Initialize a Message instance.
        
        Args:
            id: Unique identifier for the message
            conversation_id: ID of the conversation this message belongs to
            user_id: ID of the user who sent or received the message
            text: Content of the message
            sender: Who sent the message ('user' or 'bot')
            timestamp: When the message was sent (defaults to current time if not provided)
        """
        self.id = id
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.text = text
        self.sender = sender
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def __str__(self) -> str:
        """Return a string representation of the Message."""
        return f"Message(id={self.id}, sender={self.sender}, timestamp={self.timestamp})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Message to a dictionary for storage in DynamoDB.
        
        Returns:
            Dictionary representation of the Message
        """
        return {
            'id': self.id,
            'conversationId': self.conversation_id,
            'userId': self.user_id,
            'text': self.text,
            'sender': self.sender,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a Message instance from a dictionary.
        
        Args:
            data: Dictionary containing message data
            
        Returns:
            A new Message instance
        """
        return cls(
            id=data.get('id'),
            conversation_id=data.get('conversationId'),
            user_id=data.get('userId'),
            text=data.get('text'),
            sender=data.get('sender'),
            timestamp=data.get('timestamp')
        ) 