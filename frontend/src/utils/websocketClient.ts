import { ref } from 'vue';

// WebSocket connection status
export const isConnected = ref(false);
export const isConnecting = ref(false);
export const connectionError = ref<string | null>(null);

// WebSocket instance
let socket: WebSocket | null = null;

// Message callback
type MessageCallback = (message: string) => void;
let messageCallback: MessageCallback | null = null;

// Connect to the WebSocket server
export const connect = (url: string, customerId: string, onMessage: MessageCallback): Promise<void> => {
    return new Promise((resolve, reject) => {
        if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
            console.log('WebSocket already connected or connecting');
            if (socket.readyState === WebSocket.OPEN) {
                resolve();
            }
            return;
        }

        isConnecting.value = true;
        connectionError.value = null;
        messageCallback = onMessage;

        // Add customerId as a query parameter
        const wsUrl = `${url}?customerId=${customerId}`;
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('WebSocket connected');
            isConnected.value = true;
            isConnecting.value = false;
            resolve();
        };

        socket.onclose = (event) => {
            console.log('WebSocket disconnected', event);
            isConnected.value = false;
            isConnecting.value = false;

            // Attempt to reconnect after a delay if not intentionally closed
            if (!event.wasClean) {
                setTimeout(() => {
                    connect(url, customerId, onMessage);
                }, 3000);
            }
        };

        socket.onerror = (error) => {
            console.error('WebSocket error', error);
            connectionError.value = 'Failed to connect to chat service';
            isConnecting.value = false;
            reject(error);
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.message && messageCallback) {
                    messageCallback(data.message);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message', error);
            }
        };
    });
};

// Send a message through the WebSocket
export const sendMessage = (message: string): boolean => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        connectionError.value = 'Not connected to chat service';
        return false;
    }

    try {
        socket.send(JSON.stringify({ message }));
        return true;
    } catch (error) {
        console.error('Error sending message', error);
        return false;
    }
};

// Disconnect from the WebSocket server
export const disconnect = (): void => {
    if (socket) {
        socket.close();
        socket = null;
    }
    isConnected.value = false;
    isConnecting.value = false;
}; 