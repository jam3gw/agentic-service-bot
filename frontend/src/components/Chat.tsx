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
    VStack,
    ButtonGroup,
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

    const chatBoxRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Colors
    const bgColor = useColorModeValue('gray.50', 'gray.700');
    const borderColor = useColorModeValue('gray.200', 'gray.600');

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
        }
    }, [messages]);

    // Notify parent when customer changes
    useEffect(() => {
        if (customerId) {
            onCustomerChange(customerId);
        }
    }, [customerId, onCustomerChange]);

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
            // Focus the input after sending a message
            inputRef.current?.focus();
        }
    };

    // Focus input when component mounts or when customerId changes
    useEffect(() => {
        inputRef.current?.focus();
    }, [customerId]); // Also focus when customer changes

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
            <VStack
                width="100%"
                height="calc(100vh - 200px)"
                spacing={4}
                align="stretch"
            >
                {/* Customer Selection Section */}
                <Box>
                    <FormControl>
                        <FormLabel>Customer</FormLabel>
                        <Select
                            value={customerId}
                            onChange={(e) => {
                                setCustomerId(e.target.value);
                            }}
                            isDisabled={isLoadingCustomers}
                        >
                            {customers.map(customer => (
                                <option key={customer.id} value={customer.id}>
                                    {customer.name} ({customer.level})
                                </option>
                            ))}
                        </Select>
                    </FormControl>
                </Box>

                {/* Chat Interface Section */}
                <Box flex="1" display="flex" flexDirection="column">
                    {renderError()}

                    <Box
                        ref={chatBoxRef}
                        flex="1"
                        bg={bgColor}
                        p={4}
                        borderRadius="md"
                        boxShadow="sm"
                        borderWidth="1px"
                        borderColor={borderColor}
                        overflowY="auto"
                        mb={4}
                        maxH="calc(100vh - 500px)"
                        minH="400px"
                        sx={{
                            '&::-webkit-scrollbar': {
                                width: '4px',
                            },
                            '&::-webkit-scrollbar-track': {
                                width: '6px',
                            },
                            '&::-webkit-scrollbar-thumb': {
                                background: 'gray.300',
                                borderRadius: '24px',
                            },
                        }}
                    >
                        <MessageList messages={messages} />
                    </Box>

                    <form onSubmit={handleSubmit}>
                        <Flex gap={2}>
                            <Input
                                ref={inputRef}
                                value={input}
                                onChange={handleInputChange}
                                placeholder="Type your message..."
                                isDisabled={isLoading || !customerId}
                            />
                            <ButtonGroup>
                                <Button
                                    type="submit"
                                    colorScheme="blue"
                                    isLoading={isLoading}
                                    isDisabled={!input.trim() || !customerId}
                                >
                                    Send
                                </Button>
                                <Button
                                    colorScheme="gray"
                                    onClick={startNewConversation}
                                    isDisabled={!customerId || isLoading}
                                >
                                    New Conversation
                                </Button>
                            </ButtonGroup>
                        </Flex>
                    </form>
                </Box>
            </VStack>
        </ErrorBoundary>
    );
}; 