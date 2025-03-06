#!/usr/bin/env python3
"""
WebSocket Connection Analysis Script

This script analyzes CloudWatch logs for WebSocket connection issues,
focusing on GoneException errors, connection lifecycle events, and
message delivery failures.
"""

import argparse
import json
import subprocess
import time
import sys
import re
from datetime import datetime, timedelta
import os
from typing import Dict, List, Any, Optional, Tuple

# ANSI color codes for terminal output
COLORS = {
    "RED": "\033[91m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m"
}

def color_text(text: str, color: str) -> str:
    """Add color to terminal text."""
    return f"{COLORS.get(color, '')}{text}{COLORS['RESET']}"

def run_command(command: List[str]) -> Tuple[str, int]:
    """Run a shell command and return the output and exit code."""
    try:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return result.stdout, result.returncode
    except Exception as e:
        return str(e), 1

def get_log_group_name(environment: str = "dev") -> str:
    """Get the correct log group name for the chat handler Lambda."""
    # First, try to list log groups to find the correct one
    command = ["aws", "logs", "describe-log-groups", "--log-group-name-prefix", f"/aws/lambda/{environment}"]
    output, exit_code = run_command(command)
    
    if exit_code != 0:
        print(color_text(f"Error listing log groups: {output}", "RED"))
        return f"/aws/lambda/{environment}-chat-handler"  # Default fallback
    
    try:
        log_groups = json.loads(output)
        for group in log_groups.get("logGroups", []):
            group_name = group.get("logGroupName", "")
            if "chat" in group_name.lower() and environment in group_name.lower():
                return group_name
    except json.JSONDecodeError:
        pass
    
    # Fallback to default naming pattern
    return f"/aws/lambda/{environment}-chat-handler"

def start_query(log_group_name: str, query_string: str, start_time: int, end_time: int) -> Optional[str]:
    """Start a CloudWatch Logs Insights query and return the query ID."""
    command = [
        "aws", "logs", "start-query",
        "--log-group-name", log_group_name,
        "--start-time", str(start_time),
        "--end-time", str(end_time),
        "--query-string", query_string
    ]
    
    output, exit_code = run_command(command)
    
    if exit_code != 0:
        print(color_text(f"Error starting query: {output}", "RED"))
        return None
    
    try:
        result = json.loads(output)
        return result.get("queryId")
    except json.JSONDecodeError:
        print(color_text(f"Error parsing query result: {output}", "RED"))
        return None

def get_query_results(query_id: str, max_attempts: int = 10) -> List[Dict[str, Any]]:
    """Get the results of a CloudWatch Logs Insights query."""
    if not query_id:
        return []
    
    for attempt in range(max_attempts):
        command = ["aws", "logs", "get-query-results", "--query-id", query_id]
        output, exit_code = run_command(command)
        
        if exit_code != 0:
            print(color_text(f"Error getting query results: {output}", "RED"))
            return []
        
        try:
            result = json.loads(output)
            status = result.get("status")
            
            if status == "Complete":
                return result.get("results", [])
            elif status in ["Failed", "Cancelled"]:
                print(color_text(f"Query {status}: {result.get('statistics', {})}", "RED"))
                return []
            
            # Query still running, wait before trying again
            print(f"Query in progress... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(2)
        except json.JSONDecodeError:
            print(color_text(f"Error parsing query results: {output}", "RED"))
            return []
    
    print(color_text("Query timed out", "YELLOW"))
    return []

def format_results(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Format the query results into a more usable structure."""
    formatted_results = []
    
    for result in results:
        item = {}
        for field in result:
            field_name = field.get("field", "")
            field_value = field.get("value", "")
            item[field_name] = field_value
        
        formatted_results.append(item)
    
    return formatted_results

def analyze_gone_exceptions(results: List[Dict[str, str]]) -> None:
    """Analyze GoneException errors in the logs."""
    if not results:
        print(color_text("No GoneException errors found.", "GREEN"))
        return
    
    print(color_text("\n=== GoneException Analysis ===", "BOLD"))
    print(f"Found {len(results)} GoneException errors")
    
    # Group by connection ID if available
    connection_groups = {}
    for result in results:
        message = result.get("@message", "")
        timestamp = result.get("@timestamp", "")
        
        # Try to extract connection ID
        connection_match = re.search(r"connectionId: ([a-zA-Z0-9_-]+)", message)
        connection_id = connection_match.group(1) if connection_match else "unknown"
        
        if connection_id not in connection_groups:
            connection_groups[connection_id] = []
        
        connection_groups[connection_id].append({
            "timestamp": timestamp,
            "message": message
        })
    
    # Print summary by connection ID
    for connection_id, messages in connection_groups.items():
        print(color_text(f"\nConnection ID: {connection_id}", "CYAN"))
        print(f"  Error count: {len(messages)}")
        
        if messages:
            first_msg = messages[0]["message"]
            print(f"  First error: {messages[0]['timestamp']}")
            print(f"  Sample message: {first_msg[:100]}..." if len(first_msg) > 100 else first_msg)
            
            # Look for patterns in the errors
            welcome_msg_count = sum(1 for m in messages if "welcome message" in m["message"].lower())
            if welcome_msg_count > 0:
                print(color_text(f"  Welcome message errors: {welcome_msg_count}", "YELLOW"))
                print("  This suggests connection is closing before welcome message can be sent")

def analyze_connection_lifecycle(results: List[Dict[str, str]]) -> None:
    """Analyze WebSocket connection lifecycle events."""
    if not results:
        print(color_text("No connection lifecycle events found.", "YELLOW"))
        return
    
    print(color_text("\n=== Connection Lifecycle Analysis ===", "BOLD"))
    print(f"Found {len(results)} connection events")
    
    # Group by connection ID
    connection_events = {}
    for result in results:
        message = result.get("@message", "")
        timestamp = result.get("@timestamp", "")
        
        # Try to extract connection ID
        connection_match = re.search(r"connectionId: ([a-zA-Z0-9_-]+)", message)
        connection_id = connection_match.group(1) if connection_match else "unknown"
        
        if connection_id not in connection_events:
            connection_events[connection_id] = []
        
        # Determine event type
        event_type = "unknown"
        if "$connect" in message:
            event_type = "connect"
        elif "$disconnect" in message:
            event_type = "disconnect"
        elif "message" in message.lower():
            event_type = "message"
        
        connection_events[connection_id].append({
            "timestamp": timestamp,
            "message": message,
            "event_type": event_type
        })
    
    # Analyze connection patterns
    complete_lifecycles = 0
    incomplete_lifecycles = 0
    short_lived_connections = 0
    
    for connection_id, events in connection_events.items():
        # Sort events by timestamp
        events.sort(key=lambda x: x["timestamp"])
        
        has_connect = any(e["event_type"] == "connect" for e in events)
        has_disconnect = any(e["event_type"] == "disconnect" for e in events)
        has_message = any(e["event_type"] == "message" for e in events)
        
        if has_connect and has_disconnect:
            complete_lifecycles += 1
            
            # Check for short-lived connections
            if len(events) >= 2:
                try:
                    connect_time = datetime.fromisoformat(events[0]["timestamp"].replace('Z', '+00:00'))
                    disconnect_time = datetime.fromisoformat(events[-1]["timestamp"].replace('Z', '+00:00'))
                    duration = (disconnect_time - connect_time).total_seconds()
                    
                    if duration < 5:  # Less than 5 seconds
                        short_lived_connections += 1
                except (ValueError, IndexError):
                    pass
        else:
            incomplete_lifecycles += 1
    
    # Print summary
    print(f"Complete connection lifecycles: {complete_lifecycles}")
    print(f"Incomplete connection lifecycles: {incomplete_lifecycles}")
    
    if short_lived_connections > 0:
        print(color_text(f"Short-lived connections (<5s): {short_lived_connections}", "YELLOW"))
        print("This suggests connections are being closed prematurely")

def analyze_welcome_messages(results: List[Dict[str, str]]) -> None:
    """Analyze welcome message attempts and successes."""
    if not results:
        print(color_text("No welcome message events found.", "YELLOW"))
        return
    
    print(color_text("\n=== Welcome Message Analysis ===", "BOLD"))
    print(f"Found {len(results)} welcome message events")
    
    # Count successes and failures
    success_count = 0
    failure_count = 0
    retry_count = 0
    
    for result in results:
        message = result.get("@message", "").lower()
        
        if "successfully sent welcome message" in message:
            success_count += 1
        elif "failed to send welcome message" in message:
            failure_count += 1
        elif "retrying" in message and "welcome message" in message:
            retry_count += 1
    
    # Print summary
    print(f"Successful welcome messages: {success_count}")
    print(f"Failed welcome messages: {failure_count}")
    print(f"Welcome message retry attempts: {retry_count}")
    
    if failure_count > 0:
        failure_rate = (failure_count / (success_count + failure_count)) * 100
        print(color_text(f"Welcome message failure rate: {failure_rate:.1f}%", 
                        "RED" if failure_rate > 20 else "YELLOW"))
    
    if retry_count > 0:
        print(color_text(f"Average retries per message: {retry_count / (success_count + failure_count):.1f}", 
                        "YELLOW"))

def main():
    parser = argparse.ArgumentParser(description="Analyze WebSocket connection logs")
    parser.add_argument("--environment", "-e", default="dev", help="Environment (dev, staging, prod)")
    parser.add_argument("--hours", "-t", type=int, default=24, help="Hours of logs to analyze")
    parser.add_argument("--analysis", "-a", choices=["all", "gone", "lifecycle", "welcome"], 
                        default="all", help="Type of analysis to run")
    args = parser.parse_args()
    
    # Calculate time range
    end_time = int(time.time())
    start_time = end_time - (args.hours * 3600)
    
    print(color_text(f"Analyzing WebSocket logs for the past {args.hours} hours in {args.environment} environment", "BOLD"))
    
    # Get the correct log group name
    log_group_name = get_log_group_name(args.environment)
    print(f"Using log group: {log_group_name}")
    
    # Run the appropriate analyses
    if args.analysis in ["all", "gone"]:
        print(color_text("\nAnalyzing GoneException errors...", "BLUE"))
        query_string = """
        fields @timestamp, @message
        | filter @message like 'GoneException'
        | sort @timestamp desc
        | limit 100
        """
        query_id = start_query(log_group_name, query_string, start_time, end_time)
        results = get_query_results(query_id)
        formatted_results = format_results(results)
        analyze_gone_exceptions(formatted_results)
    
    if args.analysis in ["all", "lifecycle"]:
        print(color_text("\nAnalyzing connection lifecycle events...", "BLUE"))
        query_string = """
        fields @timestamp, @message
        | filter @message like 'connectionId' and (@message like '$connect' or @message like '$disconnect' or @message like 'message')
        | sort @timestamp asc
        | limit 200
        """
        query_id = start_query(log_group_name, query_string, start_time, end_time)
        results = get_query_results(query_id)
        formatted_results = format_results(results)
        analyze_connection_lifecycle(formatted_results)
    
    if args.analysis in ["all", "welcome"]:
        print(color_text("\nAnalyzing welcome message events...", "BLUE"))
        query_string = """
        fields @timestamp, @message
        | filter @message like 'welcome message'
        | sort @timestamp desc
        | limit 100
        """
        query_id = start_query(log_group_name, query_string, start_time, end_time)
        results = get_query_results(query_id)
        formatted_results = format_results(results)
        analyze_welcome_messages(formatted_results)
    
    print(color_text("\nAnalysis complete!", "GREEN"))

if __name__ == "__main__":
    main() 