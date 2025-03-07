import React, { useRef, useEffect } from 'react';
import {
    Box,
    Input,
    Button,
    Flex,
    useColorModeValue,
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
import MessageList from './MessageList';
import { ErrorBoundary } from './ErrorBoundary';
import { useChat } from '../hooks/useChat';

interface ChatProps {
    onCustomerChange: (customerId: string) => void;
    onMessageSent: () => void;
}

export const Chat: React.FC<ChatProps> = ({ onCustomerChange, onMessageSent }) => {
    const {
        messages,
        input,
        isLoading,
        error,
        customers,
        isLoadingCustomers,
        customerId,
        setInput,
        sendMessage,
        startNewConversation,
        setCustomerId,
        clearError
    } = useChat();

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Colors
    const bgColor = useColorModeValue('gray.50', 'gray.700');
    const borderColor = useColorModeValue('gray.200', 'gray.600');

    // Scroll to bottom of messages
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    // Handle input change
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInput(e.target.value);
    };

    // Handle message submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim()) {
            await sendMessage(input.trim());
            setInput('');
            onMessageSent();
        }
    };

    // Scroll to bottom when messages change
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Focus input when component mounts
    useEffect(() => {
        inputRef.current?.focus();
    }, []);

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
                    onClick={clearError}
                />
            </Alert>
        );
    };

    return (
        <ErrorBoundary>
            <Box
                width="100%"
                height="calc(100vh - 300px)"
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
                                onCustomerChange(newCustomerId);
                            }}
                            placeholder="Select customer"
                            isDisabled={isLoadingCustomers}
                        >
                            {customers.map(customer => (
                                <option key={customer.id} value={customer.id}>
                                    {customer.name} ({customer.level})
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

                {renderError()}

                <Box
                    flex="1"
                    bg={bgColor}
                    borderRadius="md"
                    borderWidth="1px"
                    borderColor={borderColor}
                    p={4}
                    mb={4}
                    overflowY="auto"
                    minH="0"
                >
                    <MessageList messages={messages} />
                    <div ref={messagesEndRef} />
                </Box>

                <form onSubmit={handleSubmit}>
                    <Flex>
                        <Input
                            ref={inputRef}
                            value={input}
                            onChange={handleInputChange}
                            placeholder="Type your message..."
                            mr={2}
                            isDisabled={isLoading || !customerId}
                        />
                        <Button
                            type="submit"
                            colorScheme="blue"
                            isLoading={isLoading}
                            loadingText="Sending..."
                            isDisabled={!input.trim() || !customerId}
                        >
                            Send
                        </Button>
                    </Flex>
                </form>
            </Box>
        </ErrorBoundary>
    );
}; 