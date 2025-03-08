export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: string;
    status?: 'sending' | 'sent' | 'delivered' | 'error' | 'queued';
}

export interface Device {
    id: string;
    type: string;
    power: string;
    volume: number;
    currentSong?: string;
    status?: string;
    capabilities?: string[];
}

export interface Capability {
    id: string;
    name: string;
    description: string;
    category: string;
    serviceTier: 'basic' | 'premium' | 'enterprise';
    available: boolean;
}

export interface ChatResponse {
    message: string;
    timestamp: string;
    messageId: string;
    conversationId: string;
    error?: string;
} 