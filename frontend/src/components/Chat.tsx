import { useState, useRef, useEffect, KeyboardEvent, ChangeEvent } from 'react';
import {
    Box,
    Button,
    Input,
    Flex,
    Text,
} from '@chakra-ui/react';
import { Message } from '../types';
import config from '../config';
import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
    baseURL: config.apiUrl,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

export const Chat = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            text: input,
            sender: 'user',
            timestamp: new Date().toISOString(),
        };

        setMessages((prev: Message[]) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        setError(null);

        try {
            const response = await api.post('/chat', {
                message: input,
                customerId: 'user_' + Date.now(), // Generate a simple user ID for now
            });

            const botMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: response.data.message,
                sender: 'bot',
                timestamp: new Date().toISOString(),
            };

            setMessages((prev: Message[]) => [...prev, botMessage]);
        } catch (err) {
            console.error('Error sending message:', err);
            setError('Failed to send message. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box
            height="calc(100vh - 200px)"
            maxW="800px"
            mx="auto"
            display="flex"
            flexDirection="column"
        >
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
                                Send a message to start the conversation
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
                        disabled={isLoading}
                        bg="white"
                        _focus={{ boxShadow: 'outline' }}
                    />
                    <Button
                        ml={2}
                        colorScheme="blue"
                        onClick={handleSend}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Sending...' : 'Send'}
                    </Button>
                </Flex>
            </Flex>
        </Box>
    );
}; 