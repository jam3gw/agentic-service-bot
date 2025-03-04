import { useState, useRef, useEffect, KeyboardEvent, ChangeEvent } from 'react';
import {
    Box,
    Button,
    Input,
    Flex,
    Text,
    Select,
    Badge,
    VStack,
    HStack,
    Heading,
    Container,
    useColorModeValue,
    Icon,
    Spinner,
    Alert,
    AlertIcon,
    Tooltip,
    Avatar,
    IconButton,
    useToast,
} from '@chakra-ui/react';
import { Message } from '../types';
import config from '../config';
import * as websocketClient from '../utils/websocketClient';
import ConnectionStatus from './ConnectionStatus';
import MessageList from './MessageList';

// Default customer IDs
const CUSTOMER_IDS = [
    { id: 'cust_001', name: 'Jane Smith (Basic)', avatar: '👩‍💼' },
    { id: 'cust_002', name: 'John Doe (Premium)', avatar: '👨‍💼' },
    { id: 'cust_003', name: 'Alice Johnson (Enterprise)', avatar: '👩‍🔧' },
];

interface ChatProps {
    onCustomerChange?: (customerId: string) => void;
}

export const Chat: React.FC<ChatProps> = ({ onCustomerChange }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [customerId, setCustomerId] = useState(CUSTOMER_IDS[0].id);
    const [reconnecting, setReconnecting] = useState(false);
    const [isDisconnected, setIsDisconnected] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const toast = useToast();

    // Theme colors
    const bgColor = useColorModeValue('gray.50', 'gray.900');
    const headerBg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const userBubbleBg = useColorModeValue('blue.500', 'blue.400');
    const botBubbleBg = useColorModeValue('gray.100', 'gray.700');
    const inputBg = useColorModeValue('white', 'gray.800');

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Focus input when component mounts
    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    // Handle incoming WebSocket messages
    const handleWebSocketMessage = (data: any) => {
        console.log('Received WebSocket message:', data);

        if (data.message) {
            const botMessage: Message = {
                id: Date.now().toString(),
                text: data.message,
                sender: 'bot',
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, botMessage]);
            setIsLoading(false);
        }

        if (data.error) {
            setError(data.error);
            setIsLoading(false);

            // Auto-reconnect after error
            if (data.error.includes('timed out')) {
                handleReconnect();
            }
        }

        if (data.status === 'processing') {
            // Optional: Show a typing indicator or processing state
            console.log('Bot is processing the message...');
        }
    };

    // Connect to WebSocket when component mounts or customerId changes
    useEffect(() => {
        // Connect to WebSocket
        console.log(`Connecting to WebSocket for customer: ${customerId}`);

        // Clear messages when customer changes
        setMessages([]);
        setError(null);
        setIsLoading(false);

        connectToWebSocket();

        // Set up connection status monitoring
        const connectionMonitor = setInterval(() => {
            // Update UI based on connection status
            if (websocketClient.connectionError.value && !error) {
                setError(websocketClient.connectionError.value);
            } else if (!websocketClient.connectionError.value && error) {
                // Clear error if connection is restored
                if (websocketClient.isConnected.value) {
                    setError(null);
                }
            }
        }, 1000);

        return () => {
            // Disconnect when component unmounts
            websocketClient.disconnect();
            clearInterval(connectionMonitor);
        };
    }, [customerId]);

    const connectToWebSocket = () => {
        setReconnecting(true);
        setIsDisconnected(false);
        websocketClient.connect(config.wsUrl, customerId, handleWebSocketMessage, {
            pingIntervalMs: 30000,
            reconnectDelayMs: 3000,
            maxReconnectAttempts: 5,
            connectionTimeoutMs: 10000 // Increased timeout
        }).then(() => {
            setReconnecting(false);
            setError(null);
            // Add welcome message
            if (messages.length === 0) {
                const welcomeMessage: Message = {
                    id: `welcome_${Date.now()}`,
                    text: `Welcome ${CUSTOMER_IDS.find(c => c.id === customerId)?.name.split(' ')[0]}! How can I help with your smart home today?`,
                    sender: 'bot',
                    timestamp: new Date().toISOString(),
                };
                setMessages([welcomeMessage]);
            }
        }).catch(err => {
            console.error('Failed to connect to WebSocket:', err);
            setError('Failed to connect to chat service. Please try again later.');
            setReconnecting(false);
        });
    };

    const handleReconnect = () => {
        websocketClient.disconnect();
        connectToWebSocket();
    };

    const handleSend = async () => {
        if (!input.trim()) return;

        const messageText = input.trim();
        const messageId = `msg_${Date.now()}`;

        // Create user message
        const userMessage: Message = {
            id: messageId,
            text: messageText,
            sender: 'user',
            timestamp: new Date().toISOString(),
            status: 'sending'
        };

        // Optimistic UI update
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        inputRef.current?.focus();

        try {
            // Check connection before sending
            if (!websocketClient.isSocketConnected()) {
                // Update message status to indicate it's queued
                setMessages((prev) =>
                    prev.map(msg =>
                        msg.id === messageId
                            ? { ...msg, status: 'queued' }
                            : msg
                    )
                );

                // Try to reconnect
                handleReconnect();
                throw new Error('Message queued - reconnecting to server');
            }

            // Send message
            await websocketClient.sendMessage(messageText, customerId);

            // Update message status to sent
            setMessages((prev) =>
                prev.map(msg =>
                    msg.id === messageId
                        ? { ...msg, status: 'sent' }
                        : msg
                )
            );
        } catch (err) {
            console.error('Error sending message:', err);

            // Don't show error for queued messages
            if (err.message && !err.message.includes('queued')) {
                setError(`Failed to send message: ${err.message}`);
            }

            // Keep the message in the UI with error status if not queued
            if (err.message && !err.message.includes('queued')) {
                setMessages((prev) =>
                    prev.map(msg =>
                        msg.id === messageId
                            ? { ...msg, status: 'error' }
                            : msg
                    )
                );
            }
        }
    };

    const handleCustomerChange = (e: ChangeEvent<HTMLSelectElement>) => {
        const newCustomerId = e.target.value;
        setCustomerId(newCustomerId);
        // Call the onCustomerChange prop if provided
        if (onCustomerChange) {
            onCustomerChange(newCustomerId);
        }
        // WebSocket reconnection will happen in the useEffect
    };

    const currentCustomer = CUSTOMER_IDS.find(c => c.id === customerId);

    // Handle manual disconnect
    const handleDisconnect = () => {
        websocketClient.disconnect();
        setIsDisconnected(true);
        setError("Disconnected from server. Click 'Reconnect' to resume.");

        toast({
            title: "Disconnected",
            description: "You've been disconnected from the chat server.",
            status: "info",
            duration: 3000,
            isClosable: true,
            position: "top"
        });
    };

    return (
        <Container maxW="container.md" p={0} h="100vh">
            <VStack h="full" spacing={0} borderRadius="lg" overflow="hidden" boxShadow="lg">
                {/* Header */}
                <Box
                    w="full"
                    bg={headerBg}
                    p={4}
                    borderBottom="1px"
                    borderColor={borderColor}
                >
                    <HStack justify="space-between">
                        <HStack>
                            <Avatar
                                bg="blue.500"
                                color="white"
                                name="Smart Home"
                                size="sm"
                                src="/logo.png"
                                fallback={<Text fontSize="lg">🏠</Text>}
                            />
                            <VStack align="start" spacing={0}>
                                <Heading size="md">Smart Home Assistant</Heading>
                                <HStack>
                                    <Text fontSize="xs" color="gray.500">Connected as:</Text>
                                    <Select
                                        size="xs"
                                        variant="unstyled"
                                        value={customerId}
                                        onChange={handleCustomerChange}
                                        fontWeight="bold"
                                        width="auto"
                                    >
                                        {CUSTOMER_IDS.map(customer => (
                                            <option key={customer.id} value={customer.id}>
                                                {customer.name}
                                            </option>
                                        ))}
                                    </Select>
                                </HStack>
                            </VStack>
                        </HStack>
                        <HStack>
                            {reconnecting ? (
                                <Badge colorScheme="yellow" variant="subtle" px={2} py={1}>
                                    <HStack>
                                        <Spinner size="xs" />
                                        <Text>Reconnecting...</Text>
                                    </HStack>
                                </Badge>
                            ) : isDisconnected ? (
                                <Badge colorScheme="red" variant="subtle" px={2} py={1}>Manually Disconnected</Badge>
                            ) : websocketClient.isConnected.value ? (
                                <Badge colorScheme="green" variant="subtle" px={2} py={1}>Connected</Badge>
                            ) : (
                                <Badge colorScheme="red" variant="subtle" px={2} py={1}>Disconnected</Badge>
                            )}
                            <Tooltip label="Reconnect">
                                <IconButton
                                    aria-label="Reconnect"
                                    icon={<span>🔄</span>}
                                    size="sm"
                                    variant="ghost"
                                    onClick={handleReconnect}
                                    isLoading={reconnecting}
                                />
                            </Tooltip>
                            <Tooltip label={websocketClient.isConnected.value ? "Disconnect" : "Already disconnected"}>
                                <IconButton
                                    aria-label="Disconnect"
                                    icon={<span>🔌</span>}
                                    size="sm"
                                    variant="ghost"
                                    onClick={handleDisconnect}
                                    isDisabled={!websocketClient.isConnected.value || isDisconnected}
                                    colorScheme="red"
                                />
                            </Tooltip>
                        </HStack>
                    </HStack>
                </Box>

                {/* Connection Status */}
                {error && (
                    <Alert status="error" variant="left-accent">
                        <AlertIcon />
                        {error}
                    </Alert>
                )}

                {/* Messages */}
                <Box
                    w="full"
                    flex="1"
                    overflowY="auto"
                    p={4}
                    bg={bgColor}
                    css={{
                        '&::-webkit-scrollbar': {
                            width: '8px',
                        },
                        '&::-webkit-scrollbar-track': {
                            width: '10px',
                        },
                        '&::-webkit-scrollbar-thumb': {
                            background: 'rgba(0,0,0,0.2)',
                            borderRadius: '24px',
                        },
                    }}
                >
                    <MessageList messages={messages} />

                    {isLoading && (
                        <HStack justify="flex-start" mt={4} mb={2}>
                            <Avatar
                                size="xs"
                                bg="blue.500"
                                name="Smart Home"
                                src="/logo.png"
                                fallback={<Text fontSize="xs">🏠</Text>}
                            />
                            <Box
                                bg={botBubbleBg}
                                px={3}
                                py={2}
                                borderRadius="lg"
                                maxW="75%"
                            >
                                <HStack spacing={1}>
                                    <Box w={2} h={2} borderRadius="full" bg="blue.500" animation="pulse 1s infinite" />
                                    <Box w={2} h={2} borderRadius="full" bg="blue.500" animation="pulse 1s infinite 0.2s" />
                                    <Box w={2} h={2} borderRadius="full" bg="blue.500" animation="pulse 1s infinite 0.4s" />
                                </HStack>
                            </Box>
                        </HStack>
                    )}

                    <div ref={messagesEndRef} />
                </Box>

                {/* Input */}
                <Box
                    w="full"
                    p={4}
                    borderTop="1px"
                    borderColor={borderColor}
                    bg={headerBg}
                >
                    <HStack>
                        <Input
                            ref={inputRef}
                            flex={1}
                            value={input}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
                            onKeyPress={(e: KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleSend()}
                            placeholder="Type your message..."
                            disabled={isLoading || !websocketClient.isConnected.value}
                            bg={inputBg}
                            borderRadius="full"
                            size="md"
                            _focus={{
                                boxShadow: "none",
                                borderColor: "blue.500"
                            }}
                        />
                        <Button
                            colorScheme="blue"
                            onClick={handleSend}
                            disabled={isLoading || !websocketClient.isConnected.value || !input.trim()}
                            isLoading={isLoading}
                            borderRadius="full"
                            px={6}
                        >
                            Send
                        </Button>
                    </HStack>
                </Box>
            </VStack>
        </Container>
    );
}; 