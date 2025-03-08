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
            "what's the state", "what's the current state",
            "is my", "is the", "check if", "check my", "check the"
        ],
        "device_power": [
            "turn on", "turn off", "switch on", "switch off", 
            "power on", "power off", "start", "stop", 
            "activate", "deactivate", "enable", "disable",
            "turned on", "turned off", "can you turn", "please turn",
            "want it on", "want it off", "want the", "would you",
            "disable it", "enable it", "disable the", "enable the",
            "change the power", "change power", "start the", "stop the",
            "start my", "stop my", "turn it on", "turn it off",
            "can you start", "can you stop", "please start", "please stop"
        ],
        "volume_control": [
            "volume", "louder", "quieter", "increase volume", 
            "decrease volume", "turn up", "turn down", 
            "set volume", "change volume", "adjust volume",
            "barely hear", "too loud", "too quiet",
            "make it louder", "make it quieter", "bit louder",
            "bit quieter", "raise volume", "lower volume",
            "can't hear", "hard to hear", "increase the volume",
            "decrease the volume", "adjust the volume"
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
            "skip that", "skip to next", "don't want this", "change it",
            "play next", "play previous", "play the next", "play the previous",
            "play next song", "play previous song", "play the next song",
            "play the previous song", "play", "can you play", "please play",
            "put on", "switch to", "change to", "forward", "put on", "switch to"
        ]
    }
    
    @classmethod
    def identify_request_type(cls, text: str) -> Optional[str]:
        """
        Identify the type of request based on the text.
        
        Args:
            text: The user's request text
            
        Returns:
            The identified request type or None if unknown
        """
        if not text:
            return None
            
        text_lower = text.lower().strip()
        
        # Score each request type based on keyword matches
        scores = {request_type: 0 for request_type in cls.REQUEST_TYPES}
        
        for request_type, keywords in cls.KEYWORDS.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in text_lower:
                    # Give higher score for exact matches or longer phrases
                    if keyword_lower == text_lower or len(keyword_lower.split()) > 1:
                        scores[request_type] += 2
                    else:
                        scores[request_type] += 1
        
        # Special handling for device status queries
        if any(q in text_lower for q in ["what", "how", "is", "check"]):
            # Only increment score if there's device-related context
            if any(w in text_lower for w in ["device", "speaker", "it", "system", "my"]):
                if any(w in text_lower for w in ["status", "state", "working", "doing", "condition", "on", "off"]):
                    scores["device_status"] += 2
                    scores["device_power"] = 0  # Clear power score for status checks
                
                if "is" in text_lower and any(state in text_lower for state in ["on", "off", "turned on", "turned off"]):
                    scores["device_status"] += 2
                    scores["device_power"] = 0  # Clear power score for status checks
        
        # Special handling for power commands
        if any(cmd in text_lower for cmd in ["start", "stop", "turn", "switch"]):
            if any(w in text_lower for w in ["device", "speaker", "it", "system", "my"]):
                scores["device_power"] += 2
                # If this is about power, reduce volume score to avoid confusion
                if "power" in text_lower:
                    scores["volume_control"] = 0
        
        # Special handling for volume-related queries
        if "volume" in text_lower:
            scores["volume_control"] += 2
            # If explicitly about changing volume, prioritize over other actions
            if any(phrase in text_lower for phrase in ["change volume", "set volume", "adjust volume"]):
                scores["volume_control"] += 2
                scores["device_power"] = 0  # Clear power score for explicit volume commands
                scores["song_changes"] = 0  # Clear song score for explicit volume commands
        
        # Special handling for song-related queries
        if any(word in text_lower for word in ["song", "music", "track"]):
            scores["song_changes"] += 2
            # If explicitly about changing songs, prioritize
            if any(word in text_lower for word in ["next", "previous", "skip", "change", "different", "another"]):
                scores["song_changes"] += 2
                scores["volume_control"] = 0  # Clear volume score for explicit song commands

        # Additional song change indicators with more variations
        if any(phrase in text_lower for phrase in [
            "different song", "another song", "something else", "change the music",
            "different music", "another track", "change track", "change song",
            "switch song", "switch track", "switch music", "change the song",
            "change the track", "don't like this", "hate this", "not this one"
        ]):
            scores["song_changes"] += 3  # Higher score for explicit song change requests
            
        # Handle implicit song change requests
        if any(phrase in text_lower for phrase in [
            "something different", "play something", "put something else",
            "change it", "switch it", "skip it", "different one"
        ]):
            scores["song_changes"] += 2
        
        # Get the request type with the highest score
        max_score = max(scores.values())
        if max_score == 0:
            return None
            
        # Get all types with the max score
        top_types = [t for t, s in scores.items() if s == max_score]
        
        # If there's only one top type, return it
        if len(top_types) == 1:
            return top_types[0]
        
        # If there's a tie, use context to break it
        if "power" in text_lower:
            if "device_power" in top_types:
                return "device_power"
        elif "volume" in text_lower:
            if "volume_control" in top_types:
                return "volume_control"
        elif any(word in text_lower for word in ["song", "track", "music"]):
            if "song_changes" in top_types:
                return "song_changes"
        
        # If still tied, use the priority order
        priority_order = ["device_power", "volume_control", "song_changes", "device_status"]
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
                text_lower = text.lower()
                song_action = None
                
                # Check for next/previous commands first (including with "play")
                if any(phrase in text_lower for phrase in [
                    "next song", "next track", "skip", "forward",
                    "play next", "play the next", "play next song",
                    "play the next song", "skip to next"
                ]):
                    song_action = "next"
                elif any(phrase in text_lower for phrase in [
                    "previous song", "previous track", "back", "backward",
                    "play previous", "play the previous", "play previous song",
                    "play the previous song", "go back"
                ]):
                    song_action = "previous"
                # Check for specific song requests before generic change requests
                elif any(phrase in text_lower for phrase in ["play", "put on", "switch to"]):
                    # Find which phrase was used
                    phrases = ["play", "put on", "switch to"]
                    used_phrase = next(phrase for phrase in phrases if phrase in text_lower)
                    phrase_index = text_lower.index(used_phrase)
                    requested_song = text[phrase_index + len(used_phrase):].strip()
                    
                    # Don't treat next/previous commands as song names
                    if requested_song and not any(word in requested_song.lower() for word in ["next", "previous"]):
                        if not any(phrase in requested_song.lower() for phrase in ["next song", "previous song"]):
                            song_action = "specific"
                            result["context"]["requested_song"] = requested_song
                # Check for generic change requests
                elif any(phrase in text_lower for phrase in [
                    "change", "different", "another", "something else",
                    "don't like this", "hate this", "not this one",
                    "play something different", "play another song"
                ]):
                    song_action = "next"  # Default to next for generic change requests
                
                # Only set song_action if we have a valid action
                if song_action:
                    logger.info(f"Extracted song action: {song_action}")
                    result["context"]["song_action"] = song_action
                else:
                    # If we can't determine a valid action, remove the song_changes request type
                    result["request_type"] = None
                    result["required_actions"] = []
        else:
            logger.info("No request type identified")
        
        return result 