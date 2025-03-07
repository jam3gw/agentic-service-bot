export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: string;
    status?: 'sending' | 'sent' | 'delivered' | 'error' | 'queued';
}

export interface Device {
    id: string;
    name: string;
    type: string;
    location: string;
    status: 'online' | 'offline' | 'standby';
    power: string;
    lastUpdated: string;
}

export interface Capability {
    id: string;
    name: string;
    description: string;
    category: string;
    serviceTier: 'basic' | 'premium' | 'enterprise';
    available: boolean;
} 