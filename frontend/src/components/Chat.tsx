import React, { useState, useEffect, useRef } from 'react';
import {
    Box,
    Input,
    Button,
    VStack,
    HStack,
    Text,
    Flex,
    useColorModeValue,
    Spinner,
    Alert,
    AlertIcon,
    AlertTitle,
    AlertDescription,
    CloseButton,
    Select,
} from '@chakra-ui/react';
import { Message, Customer } from '../types';
import config from '../config';
import * as apiService from '../utils/apiService';
import MessageList from './MessageList';

interface ChatProps {
    onCustomerChange: (customerId: string) => void;
}

export const Chat: React.FC<ChatProps> = ({ onCustomerChange }) => {
    // State
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [customerId, setCustomerId] = useState(config.defaultCustomerId);
    const [lastMessageTimestamp, setLastMessageTimestamp] = useState<string | null>(null);
    const [isPolling, setIsPolling] = useState(true);
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [isLoadingCustomers, setIsLoadingCustomers] = useState(false);

    // Refs
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // Colors
    const bgColor = useColorModeValue('gray.50', 'gray.700');
    const borderColor = useColorModeValue('gray.200', 'gray.600');

    // Scroll to bottom of messages
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    // Handle customer change
    const handleCustomerChange = (id: string) => {
        setCustomerId(id);
        onCustomerChange(id);
    };

    // Handle input change
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInput(e.target.value);
    };

    // Handle message submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!input.trim() || isLoading) return;

        // Create user message
        const userMessage: Message = {
            id: `user_${Date.now()}`,
            text: input,
            sender: 'user',
            timestamp: new Date().toISOString(),
        };

        // Add user message to state
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        setError(null);

        try {
            // Send message to API
            const response = await apiService.sendChatMessage(customerId, input);

            if (response.error) {
                setError(response.error);
            } else {
                // Create bot message
                const botMessage: Message = {
                    id: response.messageId || `bot_${Date.now()}`,
                    text: response.message,
                    sender: 'bot',
                    timestamp: response.timestamp || new Date().toISOString(),
                };

                // Add bot message to state
                setMessages(prev => [...prev, botMessage]);
                setLastMessageTimestamp(botMessage.timestamp);
            }
        } catch (err) {
            setError(`Failed to send message: ${err instanceof Error ? err.message : String(err)}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Load chat history
    const loadChatHistory = async () => {
        try {
            const history = await apiService.fetchChatHistory(customerId);

            if (history.length > 0) {
                setMessages(history);
                setLastMessageTimestamp(history[history.length - 1].timestamp);
            } else {
                // Add welcome message if no history
                const customer = customers.find(c => c.id === customerId);
                const welcomeMessage: Message = {
                    id: `welcome_${Date.now()}`,
                    text: `Welcome ${customer?.name?.split(' ')[0] || 'there'}! How can I help with your smart home today?`,
                    sender: 'bot',
                    timestamp: new Date().toISOString(),
                };
                setMessages([welcomeMessage]);
                setLastMessageTimestamp(welcomeMessage.timestamp);
            }
        } catch (err) {
            setError(`Failed to load chat history: ${err instanceof Error ? err.message : String(err)}`);
        }
    };

    // Load customers from API
    const loadCustomers = async () => {
        setIsLoadingCustomers(true);
        try {
            const fetchedCustomers = await apiService.fetchCustomers();
            setCustomers(fetchedCustomers);
        } catch (err) {
            setError(`Failed to load customers: ${err instanceof Error ? err.message : String(err)}`);
        } finally {
            setIsLoadingCustomers(false);
        }
    };

    // Poll for new messages
    const pollForNewMessages = async () => {
        if (!isPolling || !customerId) return;

        try {
            // Check if API is available
            const isAvailable = await apiService.checkApiAvailability();

            if (!isAvailable) {
                return;
            }

            const history = await apiService.fetchChatHistory(customerId);

            if (history.length > 0) {
                // Check if there are new messages
                const lastMessage = history[history.length - 1];

                if (!lastMessageTimestamp || lastMessage.timestamp > lastMessageTimestamp) {
                    setMessages(history);
                    setLastMessageTimestamp(lastMessage.timestamp);
                }
            }
        } catch (err) {
            console.error('Error polling for new messages:', err);
        }
    };

    // Set up polling interval
    useEffect(() => {
        // Clear any existing interval
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
        }

        // Set up new polling interval
        if (isPolling) {
            pollingIntervalRef.current = setInterval(pollForNewMessages, config.chatPollingInterval);
        }

        // Clean up on unmount
        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
            }
        };
    }, [isPolling, customerId, lastMessageTimestamp]);

    // Load customers when component mounts
    useEffect(() => {
        loadCustomers();
    }, []);

    // Load chat history when customer changes
    useEffect(() => {
        setMessages([]);
        setError(null);
        setIsLoading(false);
        setLastMessageTimestamp(null);

        if (customerId) {
            loadChatHistory();
        }
    }, [customerId]);

    // Scroll to bottom when messages change
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Focus input when component mounts
    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    // Render customer selector
    const renderCustomerSelector = () => (
        <Box mb={4}>
            <Text mb={2} fontWeight="bold">Select Customer:</Text>
            {isLoadingCustomers ? (
                <Spinner size="sm" />
            ) : (
                <Select
                    value={customerId}
                    onChange={(e) => handleCustomerChange(e.target.value)}
                    width="100%"
                    maxWidth="300px"
                >
                    {customers.map(customer => (
                        <option key={customer.id} value={customer.id}>
                            {customer.name} ({customer.level})
                        </option>
                    ))}
                </Select>
            )}
        </Box>
    );

    // Render error alert
    const renderError = () => (
        error ? (
            <Alert status="error" mb={4}>
                <AlertIcon />
                <AlertTitle mr={2}>Error!</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
                <CloseButton position="absolute" right="8px" top="8px" onClick={() => setError(null)} />
            </Alert>
        ) : null
    );

    return (
        <Box
            width="100%"
            height="100%"
            display="flex"
            flexDirection="column"
        >
            {renderCustomerSelector()}
            {renderError()}

            <Box
                flex="1"
                bg={bgColor}
                borderWidth="1px"
                borderColor={borderColor}
                borderRadius="md"
                p={4}
                mb={4}
                overflowY="auto"
                maxHeight="calc(100vh - 250px)"
            >
                <MessageList messages={messages} />
                <div ref={messagesEndRef} />
            </Box>

            <Box as="form" onSubmit={handleSubmit}>
                <Flex>
                    <Input
                        ref={inputRef}
                        value={input}
                        onChange={handleInputChange}
                        placeholder="Type your message..."
                        mr={2}
                        disabled={isLoading}
                    />
                    <Button
                        type="submit"
                        colorScheme="blue"
                        isLoading={isLoading}
                        loadingText="Sending"
                    >
                        Send
                    </Button>
                </Flex>
            </Box>
        </Box>
    );
}; 