from typing import Dict, Optional, Tuple, List

class RequestAnalyzer:
    """Analyzes and categorizes user requests"""
    
    # Mapping of request types to required actions
    REQUEST_TYPES = {
        "device_relocation": ["device_relocation"],
        "volume_change": ["volume_control"],
        "device_status": ["status_check"],
        "play_music": ["music_services"],
        "device_info": ["device_info"],
        "multi_room_setup": ["multi_room_audio"],
        "custom_routine": ["custom_actions"]
    }
    
    # Keywords that help identify request types
    KEYWORDS = {
        "device_relocation": ["move", "relocate", "place", "put", "position", "bedroom", "kitchen", "office", "living room"],
        "volume_change": ["volume", "louder", "quieter", "turn up", "turn down", "mute"],
        "device_status": ["status", "working", "broken", "online", "offline", "connected"],
        "play_music": ["play", "music", "song", "artist", "album", "playlist"],
        "device_info": ["what is", "information", "details", "specs", "tell me about"],
        "multi_room_setup": ["multi-room", "whole home", "multiple devices", "sync", "all devices"],
        "custom_routine": ["routine", "automation", "automate", "sequence", "schedule", "when I"]
    }
    
    @classmethod
    def identify_request_type(cls, text: str) -> Optional[str]:
        """Identifies the type of request from user text"""
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
        """Extract source and destination locations from text"""
        # This is a simplified version - in a real implementation, you might use NLP
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
        """Get the list of actions required for a request type"""
        if request_type in cls.REQUEST_TYPES:
            return cls.REQUEST_TYPES[request_type]
        return []
