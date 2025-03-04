"""
Request analyzer for the Agentic Service Bot.

This module defines the RequestAnalyzer class which analyzes and categorizes
user requests based on keywords and patterns.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Any

# Add the parent directory to sys.path to enable absolute imports if needed
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class RequestAnalyzer:
    """
    Analyzes and categorizes user requests based on keywords and patterns.
    
    This class provides methods to identify the type of request from user text,
    extract location information, and determine the required actions for each
    request type.
    """
    
    # Mapping of request types to required actions
    REQUEST_TYPES: Dict[str, List[str]] = {
        "device_relocation": ["device_relocation"],
        "volume_change": ["volume_control"],
        "device_status": ["status_check"],
        "play_music": ["music_services"],
        "device_info": ["device_info"],
        "multi_room_setup": ["multi_room_audio"],
        "custom_routine": ["custom_actions"]
    }
    
    # Keywords that help identify request types
    KEYWORDS: Dict[str, List[str]] = {
        "device_relocation": ["move", "relocate", "place", "put", "position", "bedroom", "kitchen", "office", "living room"],
        "volume_change": ["volume", "louder", "quieter", "turn up", "turn down", "mute"],
        "device_status": ["status", "working", "broken", "online", "offline", "connected"],
        "play_music": ["play", "music", "song", "artist", "album", "playlist"],
        "device_info": ["what is", "information", "details", "specs", "tell me about"],
        "multi_room_setup": ["multi-room", "whole home", "multiple devices", "sync", "all devices", "all speakers", "every room", "same music", "synchronize", "play everywhere", "all rooms"],
        "custom_routine": ["routine", "automation", "automate", "sequence", "schedule", "when I"]
    }
    
    @classmethod
    def identify_request_type(cls, text: str) -> Optional[str]:
        """
        Identifies the type of request from user text.
        
        Args:
            text: The user's request text
            
        Returns:
            The identified request type, or None if no type could be determined
        """
        text = text.lower()
        scores = {req_type: 0 for req_type in cls.REQUEST_TYPES}
        
        # Score each request type based on keyword matches
        for req_type, keywords in cls.KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    scores[req_type] += 1
        
        # Get the request type with the highest score, if any score > 0
        if max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    @classmethod
    def extract_locations(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract source and destination locations from text.
        
        Args:
            text: The user's request text
            
        Returns:
            A tuple containing (source_location, destination_location),
            where either may be None if not found in the text
        """
        locations = ["living room", "bedroom", "kitchen", "office", "bathroom", "dining room", 
                    "conference room", "reception"]
        
        source = None
        destination = None
        
        # Look for "from X to Y" pattern
        text = text.lower()
        for loc in locations:
            if f"from {loc}" in text:
                source = loc.replace(" ", "_")
            if f"to {loc}" in text:
                destination = loc.replace(" ", "_")
        
        # If only destination found, look for simple placement
        if not destination:
            for loc in locations:
                if loc in text and not source:
                    destination = loc.replace(" ", "_")
                    break
        
        return source, destination
    
    @classmethod
    def get_required_actions(cls, request_type: str) -> List[str]:
        """
        Get the list of actions required for a request type.
        
        Args:
            request_type: The type of request
            
        Returns:
            A list of action names required for the request type,
            or an empty list if the request type is unknown
        """
        if request_type in cls.REQUEST_TYPES:
            return cls.REQUEST_TYPES[request_type]
        return []

    @classmethod
    def extract_device_groups(cls, text: str) -> List[str]:
        """
        Extract device groups for multi-room audio requests.
        
        Args:
            text: The user's request text
            
        Returns:
            A list of device locations or groups mentioned in the request
        """
        text = text.lower()
        locations = ["living room", "bedroom", "kitchen", "office", "bathroom", "dining room", 
                    "conference room", "reception"]
        
        # Check for "all" or "every" keywords
        if any(keyword in text for keyword in ["all", "every", "everywhere"]):
            return ["all"]
        
        # Extract specific locations
        mentioned_locations = []
        for loc in locations:
            if loc in text:
                mentioned_locations.append(loc.replace(" ", "_"))
        
        return mentioned_locations

    @classmethod
    def extract_routine_details(cls, text: str) -> Dict[str, Any]:
        """
        Extract routine details for custom action requests.
        
        Args:
            text: The user's request text
            
        Returns:
            A dictionary containing routine details such as:
            - name: The name of the routine
            - trigger: What triggers the routine (time, event)
            - actions: List of actions to perform
            - devices: List of devices involved
        """
        text = text.lower()
        
        # Initialize routine details
        routine = {
            "name": None,
            "trigger": None,
            "trigger_value": None,
            "actions": [],
            "devices": []
        }
        
        # Extract routine name
        name_patterns = [
            r"call(?:ed)? (?:it |the routine )?([\w\s]+)",
            r"name(?:d)? (?:it |the routine )?([\w\s]+)",
            r"create (?:a |the )routine ([\w\s]+)"
        ]
        
        import re
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                routine["name"] = match.group(1).strip()
                break
        
        # Extract trigger type and value
        if "when" in text:
            routine["trigger"] = "event"
            if "at" in text and re.search(r"\d{1,2}(?::\d{2})?\s*(?:am|pm)?", text):
                routine["trigger"] = "time"
                time_match = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", text)
                if time_match:
                    routine["trigger_value"] = time_match.group(1)
        
        # Extract actions
        action_keywords = {
            "play": "play_music",
            "turn on": "power_on",
            "turn off": "power_off",
            "volume": "volume_change",
            "mute": "mute",
            "unmute": "unmute"
        }
        
        for keyword, action in action_keywords.items():
            if keyword in text:
                routine["actions"].append(action)
        
        # Extract devices
        device_types = ["speaker", "display", "hub"]
        locations = ["living room", "bedroom", "kitchen", "office", "bathroom", "dining room", 
                    "conference room", "reception"]
        
        for device in device_types:
            if device in text:
                for loc in locations:
                    if loc in text:
                        routine["devices"].append({"type": device, "location": loc.replace(" ", "_")})
        
        return routine 