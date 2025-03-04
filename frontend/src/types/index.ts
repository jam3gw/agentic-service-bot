export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: string;
    status?: 'sending' | 'sent' | 'delivered' | 'error' | 'queued';
} 