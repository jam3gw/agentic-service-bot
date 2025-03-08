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

export const useChat = (): UseChatReturn => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [isLoadingCustomers, setIsLoadingCustomers] = useState<boolean>(true);
    const [customerId, setCustomerId] = useState<string>('');
    const [conversationId, setConversationId] = useState<string>('');

    // Load customers first
    useEffect(() => {
        const loadCustomers = async () => {
            setIsLoadingCustomers(true);
            try {
                const data = await apiService.fetchCustomers();
                setCustomers(data);
                if (data.length > 0) {
                    setCustomerId(data[0].id);
                }
            } catch (err) {
                setError(`Failed to load customers: ${err instanceof Error ? err.message : String(err)}`);
            } finally {
                setIsLoadingCustomers(false);
            }
        };

        loadCustomers();
    }, []); // Only run once on mount

    // Start new conversation
    const startNewConversation = useCallback(() => {
        if (!customerId) return;

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

    // When customerId changes, start a new conversation
    useEffect(() => {
        if (customerId) {
            startNewConversation();
        }
    }, [customerId, startNewConversation]);

    // Send a message
    const sendMessage = async (text: string) => {
        if (!customerId || !text.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await apiService.sendChatMessage(customerId, text, conversationId);

            if (response.conversationId && !conversationId) {
                setConversationId(response.conversationId);
            }

            setMessages(prev => [
                ...prev,
                {
                    id: `user_${Date.now()}`,
                    text,
                    sender: 'user',
                    timestamp: new Date().toISOString()
                },
                {
                    id: response.messageId || `bot_${Date.now()}`,
                    text: response.message,
                    sender: 'bot',
                    timestamp: new Date().toISOString()
                }
            ]);
        } catch (err) {
            setError(`Failed to send message: ${err instanceof Error ? err.message : String(err)}`);
        } finally {
            setIsLoading(false);
        }
    };

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