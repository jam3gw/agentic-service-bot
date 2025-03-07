"""
Request analyzer for the Agentic Service Bot.

This module provides the RequestAnalyzer class for analyzing and categorizing
user requests based on keywords and patterns.
"""

import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class RequestAnalyzer:
    """
    Analyzes and categorizes user requests based on keywords and patterns.
    
    This class provides methods to identify the type of request from user text
    and determine the required actions for each request type.
    
    Supported request types:
    - device_status: Check device status - Available to all service levels
    - device_power: Control device power (on/off) - Available to all service levels
    - volume_control: Control device volume - Available to Premium and Enterprise
    - song_changes: Control device song choice - Available to Enterprise only
    """
    
    # Mapping of request types to required actions
    REQUEST_TYPES: Dict[str, List[str]] = {
        "device_status": ["device_status"],
        "device_power": ["device_power"],
        "volume_control": ["volume_control"],
        "song_changes": ["song_changes"]
    }
    
    # Keywords that help identify request types
    KEYWORDS: Dict[str, List[str]] = {
        "device_status": [
            "status", "state", "how is", "what's the status", 
            "is it on", "is it off", "is it working", "check",
            "what is", "what's", "how's", "tell me about",
            "working", "functioning", "how are", "can you check",
            "doing", "condition", "current state", "what state",
            "current status", "what is the state", "what is the current state",
            "what's the state", "what's the current state"
        ],
        "device_power": [
            "turn on", "turn off", "switch on", "switch off", 
            "power on", "power off", "start", "stop", 
            "activate", "deactivate", "enable", "disable",
            "turned on", "turned off", "can you turn", "please turn",
            "want it on", "want it off", "want the", "would you",
            "disable it", "enable it", "disable the", "enable the",
            "change the power", "change power"
        ],
        "volume_control": [
            "volume", "louder", "quieter", "increase volume", 
            "decrease volume", "turn up", "turn down", 
            "set volume", "change volume", "adjust volume",
            "barely hear", "too loud", "too quiet",
            "make it louder", "make it quieter", "bit louder",
            "bit quieter", "raise volume", "lower volume"
        ],
        "song_changes": [
            "next song", "previous song", "skip song", "change song",
            "different song", "another song", "skip track", "next track",
            "change track", "switch song", "play something else",
            "skip", "next", "previous", "forward", "backward", "back",
            "play another", "different track", "don't like this song",
            "hate this song", "something else", "skip this", "this track",
            "skip this one", "this song", "don't like", "not like",
            "skip it", "change the song", "switch track", "switch to another",
            "another track", "change to another", "change to different",
            "switch to different", "skip this track", "skip this song",
            "skip that", "skip to next", "don't want this", "change it"
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
        
        text = text.lower().strip()
        scores = {request_type: 0 for request_type in cls.REQUEST_TYPES}
        
        # Score each request type based on keyword matches
        for request_type, keywords in cls.KEYWORDS.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in text:
                    # Give higher score for exact matches or longer phrases
                    if keyword_lower == text or len(keyword_lower.split()) > 1:
                        scores[request_type] += 2
                    else:
                        scores[request_type] += 1
        
        # Special handling for status queries
        if any(q in text for q in ["what", "how", "is", "check"]):
            # Only increment score if there's device-related context
            if any(w in text for w in ["device", "speaker", "it", "system"]):
                if any(w in text for w in ["status", "state", "working", "doing", "condition", "on", "off"]):
                    scores["device_status"] += 2
                    scores["device_power"] = 0
                
                if "is" in text and any(state in text for state in ["on", "off", "turned on", "turned off"]):
                    scores["device_status"] += 2
                    scores["device_power"] = 0
        
        # Special handling for song-related queries
        if "skip" in text:
            scores["song_changes"] += 2  # Base score for skip command
            
            # Check for skip targets
            skip_targets = ["track", "song", "one", "this", "that", "it"]
            matching_targets = [target for target in skip_targets if target in text]
            
            # Add points for each matching target
            if matching_targets:
                scores["song_changes"] += len(matching_targets)
                
            # Extra points for complete skip phrases
            skip_phrases = ["skip this track", "skip this song", "skip this one", "skip that"]
            if any(phrase in text for phrase in skip_phrases):
                scores["song_changes"] += 2
        
        # Handle negative sentiment about current song
        negative_phrases = ["don't like", "not like", "hate", "don't want"]
        if any(phrase in text for phrase in negative_phrases):
            scores["song_changes"] += 2  # Base score for negative sentiment
            
            # Check for song/track references
            song_targets = ["song", "track", "this", "it"]
            matching_targets = [target for target in song_targets if target in text]
            if matching_targets:
                scores["song_changes"] += len(matching_targets)
                
            # Extra points for complete negative phrases
            if any(f"{phrase} this song" in text or f"{phrase} this track" in text for phrase in negative_phrases):
                scores["song_changes"] += 2
        
        # Special handling for volume-related queries
        if "volume" in text:
            scores["volume_control"] += 2
            if any(phrase in text for phrase in ["change volume", "set volume", "adjust volume"]):
                scores["volume_control"] += 1
        
        # Special handling for power-related queries
        if "power" in text:
            scores["device_power"] += 2
            if any(phrase in text for phrase in ["change power", "change the power"]):
                scores["device_power"] += 1
                scores["volume_control"] = max(0, scores["volume_control"] - 1)
        
        # Get the request type with the highest score
        max_score = max(scores.values())
        if max_score == 0:  # Only require non-zero score
            return None
            
        # Get all types with the max score
        top_types = [t for t, s in scores.items() if s == max_score]
        
        # If there's only one top type, return it
        if len(top_types) == 1:
            return top_types[0]
        
        # If there's a tie, prioritize based on context
        if any(w in text for w in ["turn", "switch", "power", "start", "stop", "enable", "disable"]) and "device_power" in top_types:
            return "device_power"
        if any(w in text for w in ["status", "state", "how is", "is it", "what is"]) and "device_status" in top_types:
            return "device_status"
        if any(w in text for w in ["volume", "loud", "quiet", "hear"]) and "volume_control" in top_types:
            return "volume_control"
        if any(w in text for w in ["skip", "track", "song", "change", "switch", "don't like", "next", "previous"]) and "song_changes" in top_types:
            return "song_changes"
        
        # Default priority if no context-based decision
        priority_order = ["device_status", "device_power", "volume_control", "song_changes"]
        for request_type in priority_order:
            if request_type in top_types:
                return request_type
        
        return None
    
    @classmethod
    def get_required_actions(cls, request_type: str) -> List[str]:
        """
        Get the required actions for a request type.
        
        Args:
            request_type: The request type
            
        Returns:
            List of required actions for the request type
        """
        return cls.REQUEST_TYPES.get(request_type, [])
    
    @classmethod
    def analyze(cls, text: str) -> Dict[str, Any]:
        """
        Analyze a user request and extract relevant information.
        
        Args:
            text: The user's request text
            
        Returns:
            A dictionary containing the analysis results
        """
        logger.info(f"Analyzing request: '{text}'")
        
        result = {
            "request_type": None,
            "required_actions": [],
            "context": {}
        }
        
        # Identify the request type
        request_type = cls.identify_request_type(text)
        
        if request_type:
            logger.info(f"Identified request type: {request_type}")
            result["request_type"] = request_type
            
            # Get the required actions for this request type
            required_actions = cls.get_required_actions(request_type)
            logger.info(f"Required actions for {request_type}: {required_actions}")
            result["required_actions"] = required_actions
            
            # Extract additional context based on the request type
            if request_type == "device_power":
                # Determine if the user wants to turn the device on or off
                text_lower = text.lower()
                on_indicators = ["on", "start", "activate", "enable"]
                off_indicators = ["off", "stop", "deactivate", "disable"]
                
                # Check for explicit off indicators first
                if any(phrase in text_lower for phrase in off_indicators):
                    power_state = "off"
                elif any(phrase in text_lower for phrase in on_indicators):
                    power_state = "on"
                else:
                    # Default to off if unclear
                    power_state = "off"
                    
                logger.info(f"Extracted power state: {power_state}")
                result["context"]["power_state"] = power_state
            
            elif request_type == "volume_control":
                text_lower = text.lower()
                # First check for specific volume level
                volume_match = re.search(r"(?:to|at)\s+(\d+)(?:\s+percent)?", text_lower)
                if volume_match:
                    volume_level = int(volume_match.group(1))
                    logger.info(f"Extracted specific volume level: {volume_level}")
                    result["context"]["volume_level"] = volume_level
                    result["context"]["volume_direction"] = "set"
                else:
                    # Check for numeric words
                    if "hundred" in text_lower or "100" in text_lower:
                        logger.info("Extracted specific volume level: 100")
                        result["context"]["volume_level"] = 100
                        result["context"]["volume_direction"] = "set"
                    else:
                        # Determine if the user wants to increase or decrease the volume
                        up_indicators = ["up", "increase", "louder", "higher", "raise"]
                        down_indicators = ["down", "decrease", "lower", "quieter", "reduce"]
                        
                        volume_direction = "up" if any(phrase in text_lower for phrase in up_indicators) else "down"
                        logger.info(f"Extracted volume direction: {volume_direction}")
                        result["context"]["volume_direction"] = volume_direction
                        
                        # Add default volume increment
                        result["context"]["volume_change"] = {
                            "direction": volume_direction,
                            "amount": 10  # Default increment of 10
                        }
            
            elif request_type == "song_changes":
                # Determine if the user wants to play the next or previous song
                song_action = "next" if any(phrase in text.lower() for phrase in ["next", "skip", "forward"]) else "previous"
                logger.info(f"Extracted song action: {song_action}")
                result["context"]["song_action"] = song_action
        else:
            logger.info("No request type identified")
        
        return result 