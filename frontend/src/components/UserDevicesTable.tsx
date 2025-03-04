import React, { useState, useEffect } from 'react';
import {
    Box,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Badge,
    Heading,
    Text,
    Spinner,
    useColorModeValue,
    Tag,
    HStack,
    Switch,
    IconButton,
    Tooltip,
} from '@chakra-ui/react';
import { RepeatIcon, SettingsIcon } from '@chakra-ui/icons';

// Mock data for devices - in a real app, this would come from an API
interface Device {
    id: string;
    name: string;
    type: string;
    location: string;
    status: 'online' | 'offline' | 'standby';
    state: string;
    lastUpdated: string;
}

interface UserDevicesTableProps {
    customerId: string;
}

const UserDevicesTable: React.FC<UserDevicesTableProps> = ({ customerId }) => {
    const [devices, setDevices] = useState<Device[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [lastRefreshed, setLastRefreshed] = useState(new Date());

    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    // Mock device data based on customer ID
    useEffect(() => {
        setIsLoading(true);

        // Simulate API call delay
        const timer = setTimeout(() => {
            // Different devices for different customers
            const mockDevices: Record<string, Device[]> = {
                'cust_001': [
                    { id: 'd001', name: 'Living Room Light', type: 'Light', location: 'Living Room', status: 'online', state: 'Off', lastUpdated: '2 mins ago' },
                    { id: 'd002', name: 'Kitchen Light', type: 'Light', location: 'Kitchen', status: 'online', state: 'On', lastUpdated: '5 mins ago' },
                    { id: 'd003', name: 'Thermostat', type: 'Climate', location: 'Hallway', status: 'online', state: '72°F', lastUpdated: '1 min ago' },
                ],
                'cust_002': [
                    { id: 'd001', name: 'Living Room Light', type: 'Light', location: 'Living Room', status: 'online', state: 'Off', lastUpdated: '2 mins ago' },
                    { id: 'd002', name: 'Kitchen Light', type: 'Light', location: 'Kitchen', status: 'online', state: 'On', lastUpdated: '5 mins ago' },
                    { id: 'd003', name: 'Thermostat', type: 'Climate', location: 'Hallway', status: 'online', state: '72°F', lastUpdated: '1 min ago' },
                    { id: 'd004', name: 'Front Door Lock', type: 'Security', location: 'Front Door', status: 'online', state: 'Locked', lastUpdated: '10 mins ago' },
                    { id: 'd005', name: 'Bedroom Speaker', type: 'Audio', location: 'Bedroom', status: 'standby', state: 'Idle', lastUpdated: '30 mins ago' },
                ],
                'cust_003': [
                    { id: 'd001', name: 'Living Room Light', type: 'Light', location: 'Living Room', status: 'online', state: 'Off', lastUpdated: '2 mins ago' },
                    { id: 'd002', name: 'Kitchen Light', type: 'Light', location: 'Kitchen', status: 'online', state: 'On', lastUpdated: '5 mins ago' },
                    { id: 'd003', name: 'Thermostat', type: 'Climate', location: 'Hallway', status: 'online', state: '72°F', lastUpdated: '1 min ago' },
                    { id: 'd004', name: 'Front Door Lock', type: 'Security', location: 'Front Door', status: 'online', state: 'Locked', lastUpdated: '10 mins ago' },
                    { id: 'd005', name: 'Bedroom Speaker', type: 'Audio', location: 'Bedroom', status: 'standby', state: 'Idle', lastUpdated: '30 mins ago' },
                    { id: 'd006', name: 'Garage Door', type: 'Security', location: 'Garage', status: 'online', state: 'Closed', lastUpdated: '15 mins ago' },
                    { id: 'd007', name: 'Basement Motion Sensor', type: 'Security', location: 'Basement', status: 'online', state: 'No Motion', lastUpdated: '3 mins ago' },
                    { id: 'd008', name: 'Outdoor Camera', type: 'Security', location: 'Front Yard', status: 'online', state: 'Recording', lastUpdated: 'Just now' },
                ],
            };

            setDevices(mockDevices[customerId] || []);
            setIsLoading(false);
        }, 1000);

        return () => clearTimeout(timer);
    }, [customerId]);

    const refreshDevices = () => {
        setIsLoading(true);
        // In a real app, this would fetch the latest device data
        setTimeout(() => {
            setLastRefreshed(new Date());
            setIsLoading(false);
        }, 1000);
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'online':
                return <Badge colorScheme="green">Online</Badge>;
            case 'offline':
                return <Badge colorScheme="red">Offline</Badge>;
            case 'standby':
                return <Badge colorScheme="yellow">Standby</Badge>;
            default:
                return <Badge>Unknown</Badge>;
        }
    };

    const toggleDeviceState = (deviceId: string) => {
        setDevices(devices.map(device => {
            if (device.id === deviceId) {
                if (device.type === 'Light') {
                    const newState = device.state === 'On' ? 'Off' : 'On';
                    return { ...device, state: newState, lastUpdated: 'Just now' };
                }
            }
            return device;
        }));
    };

    return (
        <Box
            bg={bgColor}
            p={5}
            borderRadius="md"
            boxShadow="md"
            borderWidth="1px"
            borderColor={borderColor}
            mb={6}
        >
            <HStack justifyContent="space-between" mb={4}>
                <Box>
                    <Heading size="md" mb={1}>Your Smart Devices</Heading>
                    <Text fontSize="sm" color="gray.500">
                        Last updated: {lastRefreshed.toLocaleTimeString()}
                    </Text>
                </Box>
                <Tooltip label="Refresh devices">
                    <IconButton
                        aria-label="Refresh devices"
                        icon={<RepeatIcon />}
                        onClick={refreshDevices}
                        isLoading={isLoading}
                        size="sm"
                    />
                </Tooltip>
            </HStack>

            {isLoading ? (
                <Box textAlign="center" py={10}>
                    <Spinner size="xl" />
                    <Text mt={4}>Loading devices...</Text>
                </Box>
            ) : devices.length === 0 ? (
                <Box textAlign="center" py={10}>
                    <Text>No devices found for this user.</Text>
                </Box>
            ) : (
                <Box overflowX="auto">
                    <Table variant="simple" size="sm">
                        <Thead>
                            <Tr>
                                <Th>Name</Th>
                                <Th>Type</Th>
                                <Th>Location</Th>
                                <Th>Status</Th>
                                <Th>State</Th>
                                <Th>Last Updated</Th>
                                <Th>Actions</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {devices.map((device) => (
                                <Tr key={device.id}>
                                    <Td fontWeight="medium">{device.name}</Td>
                                    <Td>
                                        <Tag size="sm" colorScheme={
                                            device.type === 'Security' ? 'red' :
                                                device.type === 'Light' ? 'yellow' :
                                                    device.type === 'Climate' ? 'blue' :
                                                        device.type === 'Audio' ? 'purple' : 'gray'
                                        }>
                                            {device.type}
                                        </Tag>
                                    </Td>
                                    <Td>{device.location}</Td>
                                    <Td>{getStatusBadge(device.status)}</Td>
                                    <Td>{device.state}</Td>
                                    <Td>{device.lastUpdated}</Td>
                                    <Td>
                                        <HStack spacing={2}>
                                            {device.type === 'Light' && (
                                                <Switch
                                                    size="sm"
                                                    isChecked={device.state === 'On'}
                                                    onChange={() => toggleDeviceState(device.id)}
                                                    isDisabled={device.status !== 'online'}
                                                />
                                            )}
                                            <Tooltip label="Device settings">
                                                <IconButton
                                                    aria-label="Device settings"
                                                    icon={<SettingsIcon />}
                                                    size="xs"
                                                    variant="ghost"
                                                />
                                            </Tooltip>
                                        </HStack>
                                    </Td>
                                </Tr>
                            ))}
                        </Tbody>
                    </Table>
                </Box>
            )}
        </Box>
    );
};

export default UserDevicesTable; 