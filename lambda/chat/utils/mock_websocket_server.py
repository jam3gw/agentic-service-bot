"""
Mock WebSocket server for testing.

This module provides a simple WebSocket server implementation for testing
WebSocket connections in the Agentic Service Bot.
"""

import asyncio
import json
import logging
import threading
import websockets
from typing import Dict, Any, List, Set, Optional, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockWebSocketServer:
    """
    A mock WebSocket server for testing WebSocket connections.
    
    This server can be used to simulate WebSocket connections in tests,
    allowing for verification of connection handling, message processing,
    and disconnection behavior.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8765):
        """
        Initialize the mock WebSocket server.
        
        Args:
            host: The host to bind to
            port: The port to listen on
        """
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.received_messages: List[Dict[str, Any]] = []
        self.server = None
        self.loop = None
        self.thread = None
        self.running = False
        self.message_handler: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    
    async def _handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """
        Handle a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            path: The connection path
        """
        # Register the client
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected from {websocket.remote_address}")
        
        try:
            # Send a welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Welcome to the mock WebSocket server!"
            }))
            
            # Process messages
            async for message in websocket:
                try:
                    # Parse the message
                    data = json.loads(message)
                    logger.info(f"Received message from client {client_id}: {data}")
                    
                    # Store the message
                    self.received_messages.append(data)
                    
                    # Process the message if a handler is set
                    if self.message_handler:
                        response = self.message_handler(data)
                        await websocket.send(json.dumps(response))
                    else:
                        # Default response
                        await websocket.send(json.dumps({
                            "type": "response",
                            "status": "ok",
                            "message": "Message received"
                        }))
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from client {client_id}: {message}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON"
                    }))
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client {client_id} disconnected: {e}")
        finally:
            # Unregister the client
            self.clients.remove(websocket)
    
    def start(self):
        """Start the WebSocket server in a separate thread."""
        if self.running:
            logger.warning("Server is already running")
            return
        
        def run_server():
            """Run the server in a separate thread."""
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Create the server
            start_server = websockets.serve(
                self._handler, self.host, self.port, loop=self.loop
            )
            
            # Start the server
            self.server = self.loop.run_until_complete(start_server)
            logger.info(f"Mock WebSocket server started on ws://{self.host}:{self.port}")
            
            # Run the event loop
            self.loop.run_forever()
        
        # Start the server in a separate thread
        self.thread = threading.Thread(target=run_server)
        self.thread.daemon = True
        self.thread.start()
        self.running = True
    
    def stop(self):
        """Stop the WebSocket server."""
        if not self.running:
            logger.warning("Server is not running")
            return
        
        # Close all client connections
        if self.clients:
            close_tasks = [
                asyncio.run_coroutine_threadsafe(client.close(), self.loop)
                for client in self.clients
            ]
            for task in close_tasks:
                task.result()
        
        # Stop the server
        if self.server:
            self.server.close()
            stop_task = asyncio.run_coroutine_threadsafe(
                self.server.wait_closed(), self.loop
            )
            stop_task.result()
        
        # Stop the event loop
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # Wait for the thread to finish
        if self.thread:
            self.thread.join(timeout=5)
        
        self.running = False
        logger.info("Mock WebSocket server stopped")
    
    def get_received_messages(self) -> List[Dict[str, Any]]:
        """
        Get the messages received by the server.
        
        Returns:
            A list of received messages
        """
        return self.received_messages
    
    def clear_received_messages(self):
        """Clear the list of received messages."""
        self.received_messages = []
    
    def set_message_handler(self, handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Set a custom message handler.
        
        Args:
            handler: A function that takes a message and returns a response
        """
        self.message_handler = handler
    
    def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast
        """
        if not self.running:
            logger.warning("Server is not running")
            return
        
        # Convert the message to JSON
        message_json = json.dumps(message)
        
        # Send the message to all clients
        for client in self.clients:
            asyncio.run_coroutine_threadsafe(
                client.send(message_json), self.loop
            ) 