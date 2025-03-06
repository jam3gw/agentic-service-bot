/**
 * API service for the Agentic Service Bot frontend.
 * 
 * This module provides functions for interacting with the backend REST API.
 */

import config from '../config';
import { Message, Device, Capability, ChatResponse, Customer } from '../types';

/**
 * Sends a chat message to the backend
 * @param customerId - The ID of the customer sending the message
 * @param message - The message text to send
 * @returns Promise containing the response from the bot
 */
export const sendChatMessage = async (customerId: string, message: string): Promise<ChatResponse> => {
    try {
        if (config.debug) {
            console.log(`Sending message to ${config.apiUrl}/chat for customer ${customerId}: ${message}`);
        }

        const response = await fetch(`${config.apiUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                customerId,
                message,
            }),
        });

        if (!response.ok) {
            throw new Error(`Failed to send message: ${response.statusText}`);
        }

        const data = await response.json();

        if (config.debug) {
            console.log('Received response:', data);
        }

        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
};

/**
 * Fetches chat history for a customer
 * @param customerId - The ID of the customer whose chat history to fetch
 * @returns Promise containing array of Message objects
 */
export const fetchChatHistory = async (customerId: string): Promise<Message[]> => {
    try {
        if (config.debug) {
            console.log(`Fetching chat history for customer ${customerId}`);
        }

        const response = await fetch(`${config.apiUrl}/chat/history/${customerId}`);

        if (!response.ok) {
            throw new Error(`Failed to fetch chat history: ${response.statusText}`);
        }

        const data = await response.json();

        if (config.debug) {
            console.log('Received chat history:', data);
        }

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
        if (config.debug) {
            console.log(`Fetching devices for customer ${customerId}`);
        }

        const response = await fetch(`${config.apiUrl}/customers/${customerId}/devices`);

        if (!response.ok) {
            throw new Error(`Failed to fetch devices: ${response.statusText}`);
        }

        const data = await response.json();

        if (config.debug) {
            console.log('Received devices:', data);
        }

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
        if (config.debug) {
            console.log('Fetching service capabilities');
        }

        const response = await fetch(`${config.apiUrl}/capabilities`);

        if (!response.ok) {
            throw new Error(`Failed to fetch capabilities: ${response.statusText}`);
        }

        const data = await response.json();

        if (config.debug) {
            console.log('Received capabilities:', data);
        }

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
    try {
        const response = await fetch(`${config.apiUrl}/ping`);
        return response.ok;
    } catch (error) {
        console.error('API availability check failed:', error);
        return false;
    }
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
        const response = await fetch(
            `${config.apiUrl}/customers/${customerId}/devices/${deviceId}`,
            {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ state: newState }),
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to update device: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
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
        if (config.debug) {
            console.log('Fetching customers');
        }

        const response = await fetch(`${config.apiUrl}/customers`);

        if (!response.ok) {
            throw new Error(`Failed to fetch customers: ${response.statusText}`);
        }

        const data = await response.json();

        if (config.debug) {
            console.log('Received customers:', data);
        }

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