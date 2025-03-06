#!/usr/bin/env python3
"""
Automated WebSocket testing using Playwright and the test-websocket.html page.

This script launches a headless browser, loads the WebSocket test page,
and automates interactions to test WebSocket functionality.
"""

import os
import sys
import time
import json
import asyncio
import logging
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, TimeoutError
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("websocket-test")

# Test configuration
WEBSOCKET_URL = os.environ.get('WEBSOCKET_URL', 'wss://ig3bth930d.execute-api.us-west-2.amazonaws.com/dev')
CUSTOMER_ID = os.environ.get('CUSTOMER_ID', 'cust_002')
TEST_DURATION_SECONDS = int(os.environ.get('TEST_DURATION_SECONDS', '30'))
ENABLE_HEARTBEAT = os.environ.get('ENABLE_HEARTBEAT', 'true').lower() == 'true'
HEARTBEAT_INTERVAL_SECONDS = int(os.environ.get('HEARTBEAT_INTERVAL_SECONDS', '15'))
HTML_TEST_PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_websocket.html')
CONNECTION_TIMEOUT = int(os.environ.get('CONNECTION_TIMEOUT', '20000'))  # 20 seconds timeout

async def capture_console_logs(page: Page):
    """Capture and log browser console messages."""
    page.on("console", lambda msg: logger.info(f"Browser console: {msg.text}"))

async def run_websocket_test():
    """Run the WebSocket test using Playwright to automate the browser interaction."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set up console log capture
        await capture_console_logs(page)
        
        # Load the HTML test page
        logger.info(f"Loading test page: {HTML_TEST_PAGE}")
        await page.goto(f"file://{HTML_TEST_PAGE}")
        
        # Verify the page loaded correctly
        title = await page.title()
        logger.info(f"Page loaded with title: {title}")
        
        # Fill in the WebSocket URL and customer ID
        await page.fill('#wsUrl', WEBSOCKET_URL)
        await page.fill('#customerId', CUSTOMER_ID)
        
        # Set up event listeners to capture WebSocket events
        await page.evaluate("""
        window.testEvents = {
            messages: [],
            errors: [],
            connectionEstablished: false,
            welcomeReceived: false,
            connectionTime: null,
            welcomeTime: null,
            messagesSent: 0,
            messagesReceived: 0,
            heartbeatCount: 0
        };
        
        // Override the addMessage function to capture events
        const originalAddMessage = window.addMessage;
        window.addMessage = function(message, type) {
            // Call the original function
            originalAddMessage(message, type);
            
            // Capture the event
            window.testEvents.messages.push({
                timestamp: new Date().toISOString(),
                type: type,
                message: message
            });
            
            // Update stats based on message type
            if (type === 'sent') {
                window.testEvents.messagesSent++;
            } else if (type === 'received') {
                window.testEvents.messagesReceived++;
            } else if (type === 'welcome') {
                window.testEvents.welcomeReceived = true;
                window.testEvents.welcomeTime = new Date();
            } else if (type === 'error') {
                window.testEvents.errors.push({
                    timestamp: new Date().toISOString(),
                    message: message
                });
            }
        };
        """)
        
        # Connect to the WebSocket
        logger.info(f"Connecting to WebSocket: {WEBSOCKET_URL} with customer ID: {CUSTOMER_ID}")
        await page.click('#connectBtn')
        
        # Wait for connection to establish with increased timeout
        try:
            logger.info(f"Waiting up to {CONNECTION_TIMEOUT/1000} seconds for connection to establish...")
            await page.wait_for_function("""
            document.querySelector('#connectionStatus').textContent === 'Connected'
            """, timeout=CONNECTION_TIMEOUT)
            logger.info("WebSocket connection established successfully")
            
            # Get connection details
            connection_details = await page.evaluate("""
            (() => {
                return {
                    "status": document.querySelector('#connectionStatus').textContent,
                    "startTime": document.querySelector('#connectionStart').textContent,
                    "establishedTime": document.querySelector('#connectionEstablished').textContent,
                    "connectionTime": document.querySelector('#connectionTime').textContent
                };
            })()
            """)
            logger.info(f"Connection details: Status={connection_details['status']}, " +
                       f"Start={connection_details['startTime']}, " +
                       f"Established={connection_details['establishedTime']}, " +
                       f"Time={connection_details['connectionTime']}")
            
            # Configure and enable heartbeat if requested
            if ENABLE_HEARTBEAT:
                logger.info(f"Enabling heartbeat with interval: {HEARTBEAT_INTERVAL_SECONDS} seconds")
                await page.fill('#heartbeatInterval', str(HEARTBEAT_INTERVAL_SECONDS * 1000))  # Convert to milliseconds
                
                # Check if the button is enabled before clicking
                is_enabled = await page.evaluate("!document.querySelector('#enableHeartbeat').disabled")
                if is_enabled:
                    await page.click('#enableHeartbeat')
                    logger.info("Heartbeat enabled successfully")
                else:
                    logger.warning("Cannot enable heartbeat - button is disabled")
            
            # Wait for welcome message (max 5 seconds)
            try:
                await page.wait_for_function("""
                Array.from(document.querySelectorAll('.message')).some(el => 
                    el.textContent && (
                        el.textContent.toLowerCase().includes('welcome') ||
                        el.textContent.toLowerCase().includes('connected to agentic')
                    )
                )
                """, timeout=5000)
                logger.info("Welcome message received")
                
                # Send a test message
                test_message = json.dumps({"message": f"Test message at {datetime.now().isoformat()}"})
                await page.fill('#message', test_message)
                await page.click('#sendBtn')
                logger.info(f"Sent test message: {test_message}")
                
                # Wait for the specified test duration
                logger.info(f"Running test for {TEST_DURATION_SECONDS} seconds")
                for i in range(TEST_DURATION_SECONDS):
                    # Get current stats every 5 seconds
                    if i % 5 == 0:
                        stats = await page.evaluate("""
                        (() => {
                            return {
                                "messagesSent": document.querySelector('#messagesSent').textContent,
                                "messagesReceived": document.querySelector('#messagesReceived').textContent,
                                "connectionDuration": document.querySelector('#connectionDuration').textContent,
                                "heartbeatCount": document.querySelector('#heartbeatCount') ? document.querySelector('#heartbeatCount').textContent : '0',
                                "lastHeartbeat": document.querySelector('#lastHeartbeat') ? document.querySelector('#lastHeartbeat').textContent : 'N/A',
                                "errorsCount": document.querySelector('#errorsCount') ? document.querySelector('#errorsCount').textContent : '0'
                            };
                        })()
                        """)
                        logger.info(f"Stats - Messages Sent: {stats['messagesSent']}, " +
                                   f"Messages Received: {stats['messagesReceived']}, " +
                                   f"Connection Duration: {stats['connectionDuration']}, " +
                                   f"Heartbeat Count: {stats['heartbeatCount']}, " +
                                   f"Last Heartbeat: {stats['lastHeartbeat']}, " +
                                   f"Errors: {stats['errorsCount']}")
                    
                    # Check if connection is still active
                    connection_status = await page.evaluate("document.querySelector('#connectionStatus').textContent")
                    if connection_status != 'Connected':
                        logger.error(f"Connection lost! Status: {connection_status}")
                        
                        # Get any error messages
                        errors = await page.evaluate("""
                        Array.from(document.querySelectorAll('.message.error')).map(el => el.textContent)
                        """)
                        for error in errors:
                            logger.error(f"Error message: {error}")
                        
                        break
                    
                    await asyncio.sleep(1)
                
                # Send another test message at the end
                test_message = json.dumps({"message": f"Final test message at {datetime.now().isoformat()}"})
                await page.fill('#message', test_message)
                await page.click('#sendBtn')
                logger.info(f"Sent final test message: {test_message}")
                
                # Wait a moment for the message to be processed
                await asyncio.sleep(2)
                
            except TimeoutError:
                logger.error("Failed to receive welcome message within timeout")
                # Capture any errors
                errors = await page.evaluate("""
                Array.from(document.querySelectorAll('.message.error')).map(el => el.textContent)
                """)
                for error in errors:
                    logger.error(f"Error message: {error}")
                
                # Capture all messages for debugging
                messages = await page.evaluate("""
                Array.from(document.querySelectorAll('.message')).map(el => {
                    return {
                        "type": Array.from(el.classList).find(c => c !== 'message'),
                        "text": el.textContent
                    };
                })
                """)
                logger.info(f"All messages received ({len(messages)}):")
                for msg in messages:
                    logger.info(f"[{msg['type']}] {msg['text']}")
        
        except TimeoutError:
            logger.error(f"Failed to establish connection within {CONNECTION_TIMEOUT/1000} seconds")
            
            # Get connection status
            try:
                status = await page.evaluate("document.querySelector('#connectionStatus').textContent")
                logger.error(f"Connection status: {status}")
            except Exception as e:
                logger.error(f"Could not get connection status: {str(e)}")
            
            # Get any error messages that might have been logged
            try:
                messages = await page.evaluate("""
                Array.from(document.querySelectorAll('.message')).map(el => {
                    return {
                        "type": Array.from(el.classList).find(c => c !== 'message'),
                        "text": el.textContent
                    };
                })
                """)
                logger.info(f"All messages received ({len(messages)}):")
                for msg in messages:
                    logger.info(f"[{msg['type']}] {msg['text']}")
            except Exception as e:
                logger.error(f"Could not get messages: {str(e)}")
                
            # Take a screenshot for debugging
            try:
                screenshot_path = f"websocket_connection_error_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
            except Exception as e:
                logger.error(f"Could not take screenshot: {str(e)}")
        
        # Disable heartbeat before disconnecting
        if ENABLE_HEARTBEAT:
            try:
                # Check if the button is enabled before clicking
                is_enabled = await page.evaluate("!document.querySelector('#disableHeartbeat').disabled")
                if is_enabled:
                    await page.click('#disableHeartbeat')
                    logger.info("Heartbeat disabled successfully")
                else:
                    logger.warning("Cannot disable heartbeat - button is disabled")
            except Exception as e:
                logger.warning(f"Failed to disable heartbeat: {str(e)}")
        
        # Disconnect from the WebSocket
        logger.info("Disconnecting from WebSocket")
        try:
            # Check if the button is enabled before clicking
            is_enabled = await page.evaluate("!document.querySelector('#disconnectBtn').disabled")
            if is_enabled:
                await page.click('#disconnectBtn')
                logger.info("Disconnect button clicked")
            else:
                logger.warning("Cannot disconnect - button is disabled")
        except Exception as e:
            logger.warning(f"Failed to click disconnect button: {str(e)}")
        
        # Wait for disconnection
        try:
            await page.wait_for_function("""
            document.querySelector('#connectionStatus').textContent === 'Disconnected'
            """, timeout=5000)
            logger.info("WebSocket disconnected successfully")
        except Exception as e:
            logger.error(f"Failed to disconnect: {str(e)}")
        
        # Get final stats
        try:
            final_stats = await page.evaluate("""
            (() => {
                return {
                    "messagesSent": document.querySelector('#messagesSent').textContent,
                    "messagesReceived": document.querySelector('#messagesReceived').textContent,
                    "errorsCount": document.querySelector('#errorsCount').textContent,
                    "connectionDuration": document.querySelector('#connectionDuration').textContent,
                    "heartbeatCount": document.querySelector('#heartbeatCount') ? document.querySelector('#heartbeatCount').textContent : '0'
                };
            })()
            """)
            
            logger.info("Test completed")
            logger.info(f"Final Stats - Messages Sent: {final_stats['messagesSent']}, " +
                       f"Messages Received: {final_stats['messagesReceived']}, " +
                       f"Errors: {final_stats['errorsCount']}, " +
                       f"Connection Duration: {final_stats['connectionDuration']}, " +
                       f"Heartbeat Count: {final_stats['heartbeatCount']}")
        except Exception as e:
            logger.error(f"Failed to get final stats: {str(e)}")
        
        # Close the browser
        await browser.close()

async def main():
    """Main function to run the WebSocket test."""
    logger.info("Starting WebSocket test")
    logger.info(f"WebSocket URL: {WEBSOCKET_URL}")
    logger.info(f"Customer ID: {CUSTOMER_ID}")
    logger.info(f"Test Duration: {TEST_DURATION_SECONDS} seconds")
    logger.info(f"Heartbeat Enabled: {ENABLE_HEARTBEAT}")
    logger.info(f"Heartbeat Interval: {HEARTBEAT_INTERVAL_SECONDS} seconds")
    logger.info(f"Connection Timeout: {CONNECTION_TIMEOUT/1000} seconds")
    
    try:
        await run_websocket_test()
        logger.info("Test completed successfully")
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 