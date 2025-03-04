import { Device, Capability } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

/**
 * Fetches user devices from the backend
 * @param customerId - The ID of the customer whose devices to fetch
 * @returns Promise containing array of Device objects
 */
export const fetchUserDevices = async (customerId: string): Promise<Device[]> => {
    try {
        const response = await fetch(`${API_BASE_URL}/customers/${customerId}/devices`);

        if (!response.ok) {
            throw new Error(`Failed to fetch devices: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        return data.devices;
    } catch (error) {
        console.error('Error fetching user devices:', error);
        throw error;
    }
};

/**
 * Fetches service capabilities from the backend
 * @returns Promise containing array of Capability objects
 */
export const fetchServiceCapabilities = async (): Promise<Capability[]> => {
    try {
        const response = await fetch(`${API_BASE_URL}/capabilities`);

        if (!response.ok) {
            throw new Error(`Failed to fetch capabilities: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        return data.capabilities;
    } catch (error) {
        console.error('Error fetching service capabilities:', error);
        throw error;
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
            `${API_BASE_URL}/customers/${customerId}/devices/${deviceId}`,
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