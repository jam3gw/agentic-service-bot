export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: string;
    status?: 'sending' | 'sent' | 'queued' | 'error' | 'delivered';
}

export interface Device {
    id: string;
    type: string;
    name: string;
    location: string;
    state: string;
    capabilities: string[];
    lastUpdated: string;
}

export interface Capability {
    id: string;
    name: string;
    description: string;
    basic: boolean;
    premium: boolean;
    enterprise: boolean;
    category: 'device-control' | 'automation' | 'security' | 'integration' | 'analytics';
} 