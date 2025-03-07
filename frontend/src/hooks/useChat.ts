import { useState, useEffect, useCallback } from 'react';
import { Message, Customer } from '../types';
import * as apiService from '../utils/apiService';

interface UseChatReturn {
    messages: Message[];
    input: string;
    isLoading: boolean;
    error: string | null;
    customers: Customer[];
    isLoadingCustomers: boolean;
    customerId: string;
    conversationId: string;
    setInput: (input: string) => void;
    sendMessage: (message: string) => Promise<void>;
    startNewConversation: () => void;
    setCustomerId: (id: string) => void;
    clearError: () => void;
}

export const useChat = (initialCustomerId: string = ''): UseChatReturn => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [isLoadingCustomers, setIsLoadingCustomers] = useState<boolean>(false);
    const [customerId, setCustomerId] = useState<string>(initialCustomerId);
    const [conversationId, setConversationId] = useState<string>('');

    // Load chat history
    const loadChatHistory = useCallback(async () => {
        if (!customerId) return;

        try {
            const history = await apiService.fetchChatHistory(customerId, conversationId);
            if (history && history.length > 0) {
                setMessages(history);
            } else if (!conversationId) {
                // Only show welcome message if there's no conversation and no history
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
            // Don't clear messages on error
        }
    }, [customerId, conversationId, customers]);

    // Send message
    const sendMessage = async (message: string) => {
        if (!message.trim() || isLoading) return;

        const userMessage: Message = {
            id: `user_${Date.now()}`,
            text: message.trim(),
            sender: 'user',
            timestamp: new Date().toISOString(),
        };

        // Keep track of previous messages in case we need to rollback
        const previousMessages = [...messages];

        // Optimistically add user message
        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);
        setError(null);

        try {
            const response = await apiService.sendChatMessage(customerId, message, conversationId);

            if (response.error) {
                setError(response.error);
                // Rollback to previous messages if there's an error
                setMessages(previousMessages);
            } else {
                const botMessage: Message = {
                    id: response.messageId || `bot_${Date.now()}`,
                    text: response.message,
                    sender: 'bot',
                    timestamp: response.timestamp || new Date().toISOString(),
                    conversationId: response.conversationId
                };

                if (response.conversationId && !conversationId) {
                    setConversationId(response.conversationId);
                }

                // Update messages with both user message and bot response
                setMessages(prev => {
                    // Check if the user message is already in the list
                    const hasUserMessage = prev.some(m => m.id === userMessage.id);

                    if (hasUserMessage) {
                        return [...prev, botMessage];
                    } else {
                        // If user message was somehow lost, add both messages
                        return [...prev, userMessage, botMessage];
                    }
                });
            }
        } catch (err) {
            setError(`Failed to send message: ${err instanceof Error ? err.message : String(err)}`);
            // Rollback to previous messages on error
            setMessages(previousMessages);
        } finally {
            setIsLoading(false);
        }
    };

    // Start new conversation
    const startNewConversation = useCallback(() => {
        // Clear messages and conversation ID
        setMessages([]);
        setConversationId('');

        // Show welcome message for new conversation
        const customer = customers.find(c => c.id === customerId);
        const welcomeMessage: Message = {
            id: `welcome_${Date.now()}`,
            text: `Welcome ${customer?.name?.split(' ')[0] || 'there'}! How can I help with your smart home today?`,
            sender: 'bot',
            timestamp: new Date().toISOString(),
        };
        setMessages([welcomeMessage]);
    }, [customerId, customers]);

    // Load customers
    useEffect(() => {
        const loadCustomers = async () => {
            setIsLoadingCustomers(true);
            try {
                const data = await apiService.fetchCustomers();
                setCustomers(data);
            } catch (err) {
                setError(`Failed to load customers: ${err instanceof Error ? err.message : String(err)}`);
            } finally {
                setIsLoadingCustomers(false);
            }
        };

        loadCustomers();
    }, []);

    // Load chat history when customer changes
    useEffect(() => {
        if (customerId) {
            // Start a new conversation when customer changes
            startNewConversation();
        } else {
            setMessages([]);
        }
    }, [customerId, startNewConversation]);

    return {
        messages,
        input,
        isLoading,
        error,
        customers,
        isLoadingCustomers,
        customerId,
        conversationId,
        setInput,
        sendMessage,
        startNewConversation,
        setCustomerId,
        clearError: () => setError(null)
    };
}; 