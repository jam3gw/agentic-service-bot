import React, { useState, useEffect, useRef } from 'react';
import {
    Box,
    Input,
    Button,
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
    FormControl,
    FormLabel,
    HStack,
} from '@chakra-ui/react';
import { Message, Customer } from '../types';
import config from '../config';
import * as apiService from '../utils/apiService';
import MessageList from './MessageList';

interface ChatProps {
    onCustomerChange: (customerId: string) => void;
}

export const Chat: React.FC<ChatProps> = ({ onCustomerChange }) => {
    // Component state
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [isLoadingCustomers, setIsLoadingCustomers] = useState<boolean>(false);
    const [customerId, setCustomerId] = useState<string>('');
    const [conversationId, setConversationId] = useState<string>('');

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

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
        setConversationId('');
        onCustomerChange(id);
    };

    // Handle input change
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInput(e.target.value);
    };

    // Handle message submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Enhanced validation to prevent empty messages
        const trimmedInput = input.trim();
        if (!trimmedInput || isLoading) return;

        // Create user message
        const userMessage: Message = {
            id: `user_${Date.now()}`,
            text: trimmedInput,
            sender: 'user',
            timestamp: new Date().toISOString(),
        };

        // Add user message to state
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            // Send message to API
            const response = await apiService.sendChatMessage(customerId, trimmedInput, conversationId);

            if (response.error) {
                setError(response.error);
            } else {
                // Create bot message
                const botMessage: Message = {
                    id: response.messageId || `bot_${Date.now()}`,
                    text: response.message,
                    sender: 'bot',
                    timestamp: response.timestamp || new Date().toISOString(),
                    conversationId: response.conversationId
                };

                // Store the conversation ID if this is a new conversation
                if (response.conversationId && !conversationId) {
                    setConversationId(response.conversationId);
                }

                // Add bot message to state
                setMessages(prev => [...prev, botMessage]);
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
            setIsLoading(true);
            const history = await apiService.fetchChatHistory(customerId, conversationId);

            // Filter out any empty messages
            const validMessages = history.filter(msg => msg.text && msg.text.trim());

            if (validMessages.length > 0) {
                setMessages(validMessages);

                // If we have messages and no conversationId set, use the conversationId from the first message
                if (!conversationId && validMessages[0].conversationId) {
                    setConversationId(validMessages[0].conversationId);
                }
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
            }
        } catch (err) {
            setError(`Failed to load chat history: ${err instanceof Error ? err.message : String(err)}`);
        } finally {
            setIsLoading(false);
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

    // Load customers when component mounts
    useEffect(() => {
        loadCustomers();
    }, []);

    // Load chat history when customer changes
    useEffect(() => {
        setMessages([]);
        setError(null);
        setIsLoading(false);

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

    // Start a new conversation
    const startNewConversation = () => {
        setMessages([]);
        setConversationId('');

        // Add welcome message for new conversation
        const customer = customers.find(c => c.id === customerId);
        const welcomeMessage: Message = {
            id: `welcome_${Date.now()}`,
            text: `Welcome ${customer?.name?.split(' ')[0] || 'there'}! How can I help with your smart home today?`,
            sender: 'bot',
            timestamp: new Date().toISOString(),
        };
        setMessages([welcomeMessage]);
    };

    // Render customer selector
    const renderCustomerSelector = () => {
        return null; // We've replaced this with the HStack above
    };

    // Render error message
    const renderError = () => {
        if (!error) return null;

        return (
            <Alert status="error" mb={4}>
                <AlertIcon />
                <Box flex="1">
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Box>
                <CloseButton
                    position="absolute"
                    right="8px"
                    top="8px"
                    onClick={() => setError(null)}
                />
            </Alert>
        );
    };

    return (
        <Box
            width="100%"
            height="100%"
            display="flex"
            flexDirection="column"
        >
            <HStack mb={4} spacing={4}>
                <FormControl>
                    <FormLabel>Customer</FormLabel>
                    <Select
                        value={customerId}
                        onChange={(e) => {
                            const newCustomerId = e.target.value;
                            setCustomerId(newCustomerId);
                            setConversationId(''); // Reset conversation ID when customer changes
                            onCustomerChange(newCustomerId);
                        }}
                        placeholder="Select customer"
                        isDisabled={isLoadingCustomers}
                    >
                        {customers.map(customer => (
                            <option key={customer.id} value={customer.id}>
                                {customer.name} ({customer.service_level})
                            </option>
                        ))}
                    </Select>
                </FormControl>

                <Button
                    colorScheme="blue"
                    onClick={startNewConversation}
                    isDisabled={!customerId || isLoading}
                    mt="auto"
                >
                    New Conversation
                </Button>
            </HStack>

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
                {messages.length === 0 && isLoading ? (
                    <Flex justify="center" align="center" height="100%" direction="column">
                        <Spinner size="xl" mb={4} />
                        <Text>Loading conversation...</Text>
                    </Flex>
                ) : messages.length === 0 ? (
                    <Flex justify="center" align="center" height="100%">
                        <Text color="gray.500">No messages yet. Start a conversation!</Text>
                    </Flex>
                ) : (
                    <MessageList messages={messages} />
                )}
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