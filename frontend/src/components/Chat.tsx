import { useState, useRef, useEffect, KeyboardEvent, ChangeEvent } from 'react';
import {
    Box,
    Button,
    Input,
    Flex,
    Text,
    Select,
    Badge,
} from '@chakra-ui/react';
import { Message } from '../types';
import config from '../config';

// Default customer IDs
const CUSTOMER_IDS = [
    { id: 'cust_001', name: 'Jane Smith (Basic)' },
    { id: 'cust_002', name: 'John Doe (Premium)' },
    { id: 'cust_003', name: 'Alice Johnson (Enterprise)' },
];

export const Chat = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [customerId, setCustomerId] = useState(CUSTOMER_IDS[0].id);
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const socketRef = useRef<WebSocket | null>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Connect to WebSocket when component mounts or customerId changes
    useEffect(() => {
        connectWebSocket();

        return () => {
            // Disconnect when component unmounts
            if (socketRef.current) {
                socketRef.current.close();
                socketRef.current = null;
            }
        };
    }, [customerId]);

    const connectWebSocket = () => {
        // Close existing connection if any
        if (socketRef.current) {
            socketRef.current.close();
            socketRef.current = null;
        }

        setIsConnecting(true);
        setError(null);
        setMessages([]);

        // Create WebSocket URL with customerId as query parameter
        const wsUrl = `${config.wsUrl}?customerId=${customerId}`;
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('WebSocket connected');
            setIsConnected(true);
            setIsConnecting(false);
        };

        socket.onclose = (event) => {
            console.log('WebSocket disconnected', event);
            setIsConnected(false);
            setIsConnecting(false);

            // Attempt to reconnect after a delay if not intentionally closed
            if (!event.wasClean && socketRef.current === socket) {
                setTimeout(() => {
                    connectWebSocket();
                }, 3000);
            }
        };

        socket.onerror = (error) => {
            console.error('WebSocket error', error);
            setError('Failed to connect to chat service');
            setIsConnecting(false);
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.message) {
                    const botMessage: Message = {
                        id: Date.now().toString(),
                        text: data.message,
                        sender: 'bot',
                        timestamp: new Date().toISOString(),
                    };
                    setMessages((prev) => [...prev, botMessage]);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message', error);
            }
        };

        socketRef.current = socket;
    };

    const handleSend = () => {
        if (!input.trim() || !isConnected) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            text: input,
            sender: 'user',
            timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        setError(null);

        try {
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({ message: input }));
            } else {
                setError('Not connected to chat service');
            }
        } catch (err) {
            console.error('Error sending message:', err);
            setError('Failed to send message. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCustomerChange = (e: ChangeEvent<HTMLSelectElement>) => {
        setCustomerId(e.target.value);
        // WebSocket reconnection will happen in the useEffect
    };

    return (
        <Box
            height="calc(100vh - 200px)"
            maxW="800px"
            mx="auto"
            display="flex"
            flexDirection="column"
        >
            <Flex mb={4} justifyContent="space-between" alignItems="center">
                <Badge
                    colorScheme={isConnected ? 'green' : isConnecting ? 'yellow' : 'red'}
                    variant="subtle"
                    p={2}
                >
                    {isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}
                </Badge>
                <Select
                    value={customerId}
                    onChange={handleCustomerChange}
                    width="250px"
                    bg="white"
                    isDisabled={isConnecting}
                >
                    {CUSTOMER_IDS.map(customer => (
                        <option key={customer.id} value={customer.id}>
                            {customer.name}
                        </option>
                    ))}
                </Select>
            </Flex>
            <Flex direction="column" flex="1" w="100%" gap={4}>
                <Box
                    flex="1"
                    w="100%"
                    overflowY="auto"
                    p={4}
                    borderRadius="lg"
                    bg="white"
                    boxShadow="base"
                >
                    {messages.length === 0 ? (
                        <Flex
                            height="100%"
                            align="center"
                            justify="center"
                        >
                            <Text color="gray.500">
                                {isConnecting
                                    ? 'Connecting to chat service...'
                                    : isConnected
                                        ? 'Send a message to start the conversation'
                                        : 'Not connected to chat service'}
                            </Text>
                        </Flex>
                    ) : (
                        messages.map((message: Message) => (
                            <Flex
                                key={message.id}
                                justify={message.sender === 'user' ? 'flex-end' : 'flex-start'}
                                mb={4}
                            >
                                <Box
                                    maxW="70%"
                                    bg={message.sender === 'user' ? 'blue.500' : 'gray.100'}
                                    color={message.sender === 'user' ? 'white' : 'black'}
                                    p={3}
                                    borderRadius="lg"
                                    boxShadow="md"
                                >
                                    <Text>{message.text}</Text>
                                    <Text
                                        fontSize="xs"
                                        color={message.sender === 'user' ? 'white' : 'gray.500'}
                                        mt={1}
                                    >
                                        {new Date(message.timestamp).toLocaleTimeString()}
                                    </Text>
                                </Box>
                            </Flex>
                        ))
                    )}
                    <div ref={messagesEndRef} />
                </Box>
                {error && (
                    <Text color="red.500" textAlign="center">
                        {error}
                    </Text>
                )}
                <Flex w="100%">
                    <Input
                        flex={1}
                        value={input}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
                        onKeyPress={(e: KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleSend()}
                        placeholder="Type your message..."
                        disabled={isLoading || !isConnected}
                        bg="white"
                        _focus={{ boxShadow: 'outline' }}
                    />
                    <Button
                        ml={2}
                        colorScheme="blue"
                        onClick={handleSend}
                        disabled={isLoading || !isConnected}
                    >
                        {isLoading ? 'Sending...' : 'Send'}
                    </Button>
                </Flex>
            </Flex>
        </Box>
    );
}; 