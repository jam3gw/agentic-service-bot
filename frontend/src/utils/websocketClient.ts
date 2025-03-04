import { ref } from 'vue';

// WebSocket connection status
export const isConnected = ref(false);
export const isConnecting = ref(false);
export const connectionError = ref<string | null>(null);

// WebSocket instance
let socket: WebSocket | null = null;
let reconnectTimer: number | null = null;
let pingInterval: number | null = null;
let connectionTimeout: number | null = null;

// Message callback
type MessageCallback = (message: any) => void;
let messageCallback: MessageCallback | null = null;

// Connection options
interface ConnectionOptions {
    pingIntervalMs?: number;
    reconnectDelayMs?: number;
    maxReconnectAttempts?: number;
    connectionTimeoutMs?: number;
}

const defaultOptions: ConnectionOptions = {
    pingIntervalMs: 30000, // 30 seconds
    reconnectDelayMs: 3000, // 3 seconds
    maxReconnectAttempts: 5,
    connectionTimeoutMs: 5000 // 5 seconds
};

let reconnectAttempts = 0;
let intentionalClose = false;

// Message queue for failed sends
const messageQueue: Array<{ message: string, customerId: string }> = [];

// Connect to the WebSocket server
export const connect = (url: string, customerId: string, onMessage: MessageCallback, options: ConnectionOptions = {}): Promise<void> => {
    return new Promise((resolve, reject) => {
        // Clear any existing reconnect timer and connection timeout
        if (reconnectTimer) {
            window.clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }

        if (connectionTimeout) {
            window.clearTimeout(connectionTimeout);
            connectionTimeout = null;
        }

        // Reset reconnect attempts if this is a fresh connection
        if (!isConnecting.value) {
            reconnectAttempts = 0;
            intentionalClose = false;
        }

        // Merge default options with provided options
        const opts = { ...defaultOptions, ...options };

        if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
            console.log('WebSocket already connected or connecting');
            if (socket.readyState === WebSocket.OPEN) {
                resolve();
            }
            return;
        }

        // Close existing socket if it exists
        if (socket) {
            try {
                intentionalClose = true;
                socket.close();
            } catch (err) {
                console.warn('Error closing existing socket:', err);
            }
            socket = null;
        }

        isConnecting.value = true;
        connectionError.value = null;
        messageCallback = onMessage;

        // Add customerId as a query parameter
        const wsUrl = `${url}?customerId=${customerId}`;
        console.log(`Connecting to WebSocket: ${wsUrl}`);

        // Set connection timeout
        connectionTimeout = window.setTimeout(() => {
            if (isConnecting.value) {
                console.error('WebSocket connection timeout');
                connectionError.value = 'Connection timeout';
                isConnecting.value = false;
                handleConnectionFailure(url, customerId, onMessage, opts, reject);
            }
        }, opts.connectionTimeoutMs);

        try {
            socket = new WebSocket(wsUrl);
        } catch (err) {
            console.error('Error creating WebSocket:', err);
            if (connectionTimeout) {
                window.clearTimeout(connectionTimeout);
                connectionTimeout = null;
            }
            handleConnectionFailure(url, customerId, onMessage, opts, reject);
            return;
        }

        socket.onopen = () => {
            console.log('WebSocket connected');
            if (connectionTimeout) {
                window.clearTimeout(connectionTimeout);
                connectionTimeout = null;
            }
            isConnected.value = true;
            isConnecting.value = false;
            reconnectAttempts = 0;

            // Set up ping interval to keep connection alive
            if (pingInterval) {
                window.clearInterval(pingInterval);
            }

            pingInterval = window.setInterval(() => {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    try {
                        // Send a ping message
                        socket.send(JSON.stringify({ action: 'ping' }));
                    } catch (err) {
                        console.warn('Error sending ping:', err);
                    }
                } else {
                    // Clear interval if socket is not open
                    if (pingInterval) {
                        window.clearInterval(pingInterval);
                        pingInterval = null;
                    }
                }
            }, opts.pingIntervalMs);

            // Process any queued messages
            processMessageQueue();

            resolve();
        };

        socket.onclose = (event) => {
            console.log('WebSocket disconnected', event);
            if (connectionTimeout) {
                window.clearTimeout(connectionTimeout);
                connectionTimeout = null;
            }
            isConnected.value = false;
            isConnecting.value = false;

            // Clear ping interval
            if (pingInterval) {
                window.clearInterval(pingInterval);
                pingInterval = null;
            }

            // Attempt to reconnect after a delay if not intentionally closed
            if (!intentionalClose) {
                handleConnectionFailure(url, customerId, onMessage, opts, reject);
            } else {
                console.log('WebSocket was intentionally closed, not reconnecting');
                intentionalClose = false;
            }
        };

        socket.onerror = (error) => {
            console.error('WebSocket error', error);
            connectionError.value = 'Failed to connect to chat service';
            isConnecting.value = false;

            // Don't reject here, let onclose handle reconnection
            // Only reject if we've exceeded max reconnect attempts
            if (reconnectAttempts >= (opts.maxReconnectAttempts || 5)) {
                reject(error);
            }
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (messageCallback) {
                    messageCallback(data);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message', error);
            }
        };
    });
};

// Handle connection failure with reconnect logic
const handleConnectionFailure = (
    url: string,
    customerId: string,
    onMessage: MessageCallback,
    options: ConnectionOptions,
    reject: (reason?: any) => void
) => {
    reconnectAttempts++;

    if (reconnectAttempts <= (options.maxReconnectAttempts || 5)) {
        console.log(`WebSocket reconnect attempt ${reconnectAttempts}/${options.maxReconnectAttempts}`);

        // Calculate backoff time with exponential backoff
        const backoffTime = Math.min(
            30000, // Max 30 seconds
            options.reconnectDelayMs! * Math.pow(1.5, reconnectAttempts - 1)
        );

        console.log(`Will attempt reconnect in ${backoffTime}ms`);

        // Schedule reconnect
        reconnectTimer = window.setTimeout(() => {
            console.log(`Attempting to reconnect...`);
            connect(url, customerId, onMessage, options)
                .catch(err => {
                    console.error('Reconnect attempt failed:', err);
                });
        }, backoffTime);
    } else {
        console.error(`Failed to connect after ${reconnectAttempts} attempts`);
        connectionError.value = `Failed to connect after ${reconnectAttempts} attempts`;
        reject(new Error(`Failed to connect after ${reconnectAttempts} attempts`));
    }
};

// Process queued messages
const processMessageQueue = () => {
    if (!isSocketConnected()) return;

    console.log(`Processing message queue (${messageQueue.length} messages)`);

    while (messageQueue.length > 0) {
        const queuedMessage = messageQueue.shift();
        if (!queuedMessage) continue;

        try {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    action: 'sendMessage',
                    message: queuedMessage.message,
                    customerId: queuedMessage.customerId
                }));
                console.log('Sent queued message');
            } else {
                // Put the message back in the queue if socket is not ready
                messageQueue.unshift(queuedMessage);
                break;
            }
        } catch (error) {
            console.error('Error sending queued message', error);
            // Put the message back in the queue
            messageQueue.unshift(queuedMessage);
            break;
        }
    }
};

// Send a message through the WebSocket
export const sendMessage = (message: string, customerId: string): Promise<boolean> => {
    return new Promise((resolve, reject) => {
        // Validate message
        if (!message || message.trim() === '') {
            reject(new Error('Message cannot be empty'));
            return;
        }

        if (!isSocketConnected()) {
            console.warn('Socket not connected, queueing message');
            // Queue message for later
            messageQueue.push({ message, customerId });

            // Try to reconnect if not already connecting
            if (!isConnecting.value) {
                // We need to reconnect but don't have the original parameters
                // This is a limitation of the current implementation
                connectionError.value = 'Not connected to chat service, message queued';
                reject(new Error('Not connected to chat service, message queued'));
            } else {
                connectionError.value = 'Connecting to chat service, message queued';
                reject(new Error('Connecting to chat service, message queued'));
            }
            return;
        }

        try {
            // Include customerId in the message payload
            socket!.send(JSON.stringify({
                action: 'sendMessage',
                message,
                customerId
            }));
            resolve(true);
        } catch (error) {
            console.error('Error sending message', error);
            // Queue message for retry
            messageQueue.push({ message, customerId });
            connectionError.value = `Error sending message: ${error}`;
            reject(error);
        }
    });
};

// Check if the WebSocket is connected
export const isSocketConnected = (): boolean => {
    return !!(socket && socket.readyState === WebSocket.OPEN);
};

// Disconnect from the WebSocket server
export const disconnect = (): void => {
    if (socket) {
        intentionalClose = true;
        socket.close();
        socket = null;
    }

    if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }

    if (pingInterval) {
        window.clearInterval(pingInterval);
        pingInterval = null;
    }

    if (connectionTimeout) {
        window.clearTimeout(connectionTimeout);
        connectionTimeout = null;
    }

    isConnected.value = false;
    isConnecting.value = false;
    reconnectAttempts = 0;
}; 