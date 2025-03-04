const WebSocket = require('ws');
const readline = require('readline');

// Replace with your actual WebSocket URL from the CDK output
const WS_URL = process.argv[2] || 'wss://your-websocket-api-id.execute-api.us-west-2.amazonaws.com/dev';
// Customer ID to use for testing
const CUSTOMER_ID = process.argv[3] || 'cust_001';

console.log(`Connecting to: ${WS_URL}?customerId=${CUSTOMER_ID}`);

// Create WebSocket connection with customer ID as query parameter
const ws = new WebSocket(`${WS_URL}?customerId=${CUSTOMER_ID}`);

// Set up readline interface for user input
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

// Flag to track if we're waiting for a response
let waitingForResponse = false;

// Connection opened
ws.on('open', () => {
    console.log('Connected to WebSocket API');
    console.log(`Using customer ID: ${CUSTOMER_ID}`);
    console.log('Type a message and press Enter to send. Type "exit" to quit.');

    // Prompt for user input
    promptUser();
});

// Listen for messages
ws.on('message', (data) => {
    try {
        const message = JSON.parse(data.toString());
        console.log('\nReceived message:');
        console.log(message.message || message);

        // If we received a "Processing your request..." message, don't prompt yet
        if (message.message === "Processing your request...") {
            console.log('Waiting for full response...');
            waitingForResponse = true;
        } else {
            waitingForResponse = false;
            promptUser();
        }
    } catch (error) {
        console.log('\nReceived raw message:');
        console.log(data.toString());
        waitingForResponse = false;
        promptUser();
    }
});

// Handle errors
ws.on('error', (error) => {
    console.error('WebSocket error:', error);
    waitingForResponse = false;
});

// Connection closed
ws.on('close', (code, reason) => {
    console.log(`Connection closed: ${code} - ${reason}`);
    rl.close();
    process.exit(0);
});

// Prompt for user input
function promptUser() {
    // Don't prompt if we're waiting for a response
    if (waitingForResponse) return;

    rl.question('> ', (input) => {
        if (input.toLowerCase() === 'exit') {
            console.log('Closing connection...');
            ws.close();
            rl.close();
            return;
        }

        // Send message
        try {
            const message = {
                action: 'message',
                message: input
            };
            ws.send(JSON.stringify(message));
            waitingForResponse = true;
            console.log('Message sent, waiting for response...');
        } catch (error) {
            console.error('Error sending message:', error);
            waitingForResponse = false;
        }
    });
}

// Handle process termination
process.on('SIGINT', () => {
    console.log('\nClosing connection...');
    ws.close();
    rl.close();
    process.exit(0);
}); 