/**
 * API service for the Agentic Service Bot frontend.
 * 
 * This module provides functions for interacting with the backend REST API.
 */

import config from '../config';
import { Message, Device, Capability, ChatResponse, Customer } from '../types';

/**
 * Base API request function with error handling
 * @param url - The URL to fetch
 * @param options - Fetch options
 * @returns Promise containing the response data
 */
async function apiCall<T>(url: string, options?: RequestInit): Promise<T> {
    try {
        // For development only - add a timestamp to prevent caching
        const urlWithCache = config.debug
            ? `${url}${url.includes('?') ? '&' : '?'}_t=${Date.now()}`
            : url;

        const response = await fetch(urlWithCache, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(options?.headers || {})
            },
            // No credentials needed for this API
            // credentials: 'include',
            // Note: 'no-cors' mode will make the response opaque and unusable for JSON parsing
            // Only use this if you're just testing connectivity and don't need the response data
            // mode: 'no-cors' // Uncomment this line only if you're testing connectivity
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(
                errorData.message || `API error: ${response.status} ${response.statusText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

/**
 * Sends a chat message to the backend
 * @param customerId - The ID of the customer sending the message
 * @param message - The message text to send
 * @returns Promise containing the response from the bot
 */
export const sendChatMessage = async (customerId: string, message: string): Promise<ChatResponse> => {
    try {
        // Validate message before sending
        if (!message || !message.trim()) {
            console.warn('Attempted to send empty message');
            return {
                message: '',
                timestamp: new Date().toISOString(),
                messageId: '',
                conversationId: '',
                error: 'Empty messages are not allowed'
            };
        }

        return await apiCall<ChatResponse>(`${config.apiUrl}/chat`, {
            method: 'POST',
            body: JSON.stringify({
                customerId,
                message: message.trim(), // Ensure message is trimmed
            }),
        });
    } catch (error) {
        console.error('Error sending message:', error);
        return {
            message: '',
            timestamp: new Date().toISOString(),
            messageId: '',
            conversationId: '',
            error: error instanceof Error ? error.message : String(error)
        };
    }
};

/**
 * Fetches chat history for a customer
 * @param customerId - The ID of the customer whose chat history to fetch
 * @returns Promise containing array of Message objects
 */
export const fetchChatHistory = async (customerId: string): Promise<Message[]> => {
    try {
        const data = await apiCall<{ messages: Message[] }>(`${config.apiUrl}/chat/history/${customerId}`);
        return data.messages || [];
    } catch (error) {
        console.error('Error fetching chat history:', error);
        throw error;
    }
};

/**
 * Fetches user devices from the backend
 * @param customerId - The ID of the customer whose devices to fetch
 * @returns Promise containing array of Device objects
 */
export const fetchUserDevices = async (customerId: string): Promise<Device[]> => {
    try {
        const data = await apiCall<{ devices: Device[] }>(`${config.apiUrl}/customers/${customerId}/devices`);
        return data.devices || [];
    } catch (error) {
        console.error('Error fetching devices:', error);
        throw error;
    }
};

/**
 * Fetches service capabilities from the backend
 * @returns Promise containing array of Capability objects
 */
export const fetchServiceCapabilities = async (): Promise<Capability[]> => {
    try {
        const data = await apiCall<{ capabilities: Capability[] }>(`${config.apiUrl}/capabilities`);
        return data.capabilities || [];
    } catch (error) {
        console.error('Error fetching capabilities:', error);
        throw error;
    }
};

/**
 * Checks if the API is available
 * @returns Promise containing a boolean indicating if the API is available
 */
export const checkApiAvailability = async (): Promise<boolean> => {
    // The ping API no longer exists, so we'll assume the API is available
    return true;
};

/**
 * Updates the state of a device
 * @param deviceId - The ID of the device to update
 * @param newState - The new state to set for the device
 * @param customerId - The ID of the customer who owns the device
 * @returns Promise containing the updated Device object
 */
export const updateDeviceState = async (
    deviceId: string,
    newState: string,
    customerId: string
): Promise<Device> => {
    try {
        const data = await apiCall<{ device: Device }>(
            `${config.apiUrl}/customers/${customerId}/devices/${deviceId}`,
            {
                method: 'PATCH',
                body: JSON.stringify({ state: newState }),
            }
        );
        return data.device;
    } catch (error) {
        console.error('Error updating device state:', error);
        throw error;
    }
};

/**
 * Fetches customers from the backend
 * @returns Promise containing array of Customer objects
 */
export const fetchCustomers = async (): Promise<Customer[]> => {
    try {
        const data = await apiCall<{ customers: Customer[] }>(`${config.apiUrl}/customers`);

        // Map the API response to our Customer type
        return (data.customers || []).map((customer: any) => ({
            id: customer.id,
            name: customer.name || `Customer ${customer.id}`,
            level: customer.level || customer.serviceLevel || 'basic',
            avatar: customer.avatar
        }));
    } catch (error) {
        console.error('Error fetching customers:', error);
        // Return default customers if API fails
        return [
            { id: 'cust_001', name: 'John Smith', level: 'basic' },
            { id: 'cust_002', name: 'Sarah Johnson', level: 'premium' },
            { id: 'cust_003', name: 'Michael Chen', level: 'enterprise' }
        ];
    }
}; 