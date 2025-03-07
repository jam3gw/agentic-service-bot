/**
 * Type definitions for the Agentic Service Bot frontend.
 */

// Message type for chat
export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: string;
    conversationId?: string;
    status?: 'sending' | 'sent' | 'delivered' | 'queued' | 'error';
}

// Device type for smart home devices
export interface Device {
    id: string;
    name: string;
    type: string;
    location: string;
    status: string;
    capabilities: string[];
    power?: string;
}

// Capability type for service level capabilities
export interface Capability {
    id: string;
    name: string;
    description: string;
    tiers: {
        basic: boolean;
        premium: boolean;
        enterprise: boolean;
    };
    category: string;
}

// Customer type
export interface Customer {
    id: string;
    name: string;
    level: 'basic' | 'premium' | 'enterprise';
    avatar?: string;
}

// Chat response from the API
export interface ChatResponse {
    message: string;
    timestamp: string;
    messageId: string;
    conversationId: string;
    error?: string;
} 