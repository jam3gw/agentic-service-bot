"""
Request analyzer for the Agentic Service Bot.

This module provides the RequestAnalyzer class for analyzing and categorizing
user requests based on keywords and patterns.
"""

import re
from typing import Dict, List, Optional, Any

class RequestAnalyzer:
    """
    Analyzes and categorizes user requests based on keywords and patterns.
    
    This class provides methods to identify the type of request from user text
    and determine the required actions for each request type.
    
    Supported request types:
    - device_power: Control device power (on/off) - Available to all service levels
    - volume_control: Control device volume - Available to Premium and Enterprise
    - song_changes: Control device song choice - Available to Enterprise only
    """
    
    # Mapping of request types to required actions
    REQUEST_TYPES: Dict[str, List[str]] = {
        "device_power": ["device_power"],
        "volume_control": ["volume_control"],
        "song_changes": ["song_changes"]
    }
    
    # Keywords that help identify request types
    KEYWORDS: Dict[str, List[str]] = {
        "device_power": [
            "turn on", "turn off", "switch on", "switch off", 
            "power on", "power off", "start", "stop", 
            "activate", "deactivate", "enable", "disable"
        ],
        "volume_control": [
            "volume", "louder", "quieter", "increase volume", 
            "decrease volume", "turn up", "turn down", 
            "set volume", "change volume", "adjust volume"
        ],
        "song_changes": [
            "next song", "previous song", "skip song", "change song",
            "different song", "another song", "skip track", "next track",
            "change track", "switch song", "play something else"
        ]
    }
    
    @classmethod
    def identify_request_type(cls, text: str) -> Optional[str]:
        """
        Identify the type of request from user text.
        
        Args:
            text: The user's request text
            
        Returns:
            The identified request type or None if no type is identified
        """
        if not text:
            return None
        
        text = text.lower()
        scores = {request_type: 0 for request_type in cls.REQUEST_TYPES}
        
        # Score each request type based on keyword matches
        for request_type, keywords in cls.KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[request_type] += 1
        
        # Special handling for volume-related queries
        if "volume" in text:
            # Check if this is a volume change request or just asking about volume
            if any(phrase in text for phrase in ["change", "increase", "decrease", "set", "turn up", "turn down"]):
                scores["volume_control"] += 2
        
        # Special handling for song-related queries
        if any(word in text for word in ["song", "track", "music"]):
            # Check if this is a song change request
            if any(phrase in text for phrase in ["next", "skip", "change", "switch", "another"]):
                scores["song_changes"] += 2
        
        # Get the request type with the highest score
        max_score = max(scores.values())
        if max_score > 0:
            # If there's a tie, prioritize in this order: device_power, volume_control, song_changes
            for request_type in ["device_power", "volume_control", "song_changes"]:
                if scores[request_type] == max_score:
                    return request_type
        
        return None
    
    @classmethod
    def get_required_actions(cls, request_type: str) -> List[str]:
        """
        Get the required actions for a request type.
        
        Args:
            request_type: The type of request
            
        Returns:
            A list of required actions for the request type
        """
        return cls.REQUEST_TYPES.get(request_type, [])
        
    @classmethod
    def analyze(cls, text: str) -> Dict[str, Any]:
        """
        Analyze a user request and extract all relevant information.
        
        This method provides a simplified analysis of the user's request,
        focusing on the core functionality needed for basic service levels.
        
        Args:
            text: The user's request text
            
        Returns:
            A dictionary containing the analysis results:
            - request_type: The identified type of request
            - required_actions: List of actions required for the request
        """
        # Initialize the result dictionary
        result = {
            "request_type": None,
            "required_actions": []
        }
        
        # Identify the request type
        request_type = cls.identify_request_type(text)
        result["request_type"] = request_type
        
        if request_type:
            # Get required actions
            result["required_actions"] = cls.get_required_actions(request_type)
        
        return result 