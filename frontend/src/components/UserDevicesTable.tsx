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
    Alert,
    AlertIcon,
    Flex,
} from '@chakra-ui/react';
import { RepeatIcon, SettingsIcon } from '@chakra-ui/icons';
import * as apiService from '../utils/apiService';
import { Device } from '../types';

interface UserDevicesTableProps {
    customerId: string;
}

const UserDevicesTable: React.FC<UserDevicesTableProps> = ({ customerId }) => {
    const [devices, setDevices] = useState<Device[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastRefreshed, setLastRefreshed] = useState(new Date());

    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    // Load devices from API
    const loadDevices = async () => {
        if (!customerId) return;

        setIsLoading(true);
        setError(null);

        try {
            const fetchedDevices = await apiService.fetchUserDevices(customerId);
            setDevices(fetchedDevices);
            setLastRefreshed(new Date());
        } catch (err) {
            setError(`Failed to load devices: ${err instanceof Error ? err.message : String(err)}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Load devices when customer changes
    useEffect(() => {
        loadDevices();
    }, [customerId]);

    // Refresh devices
    const refreshDevices = () => {
        loadDevices();
    };

    // Get status badge
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

    // Toggle device power
    const toggleDevicePower = async (deviceId: string, currentPower: string) => {
        try {
            const newPower = currentPower === 'on' ? 'off' : 'on';
            await apiService.updateDevicePower(deviceId, newPower, customerId);

            // Update local state
            setDevices(devices.map(device => {
                if (device.id === deviceId) {
                    return { ...device, power: newPower };
                }
                return device;
            }));
        } catch (err) {
            setError(`Failed to update device: ${err instanceof Error ? err.message : String(err)}`);
        }
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

            {error && (
                <Alert status="error" mb={4}>
                    <AlertIcon />
                    <Text>{error}</Text>
                </Alert>
            )}

            {isLoading ? (
                <Flex justify="center" align="center" py={10} direction="column">
                    <Spinner size="xl" mb={4} />
                    <Text>Loading devices...</Text>
                </Flex>
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
                                <Th>Actions</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {devices.map((device) => (
                                <Tr key={device.id}>
                                    <Td fontWeight="medium">{device.name}</Td>
                                    <Td>
                                        <Tag size="sm" colorScheme={
                                            device.type === 'security' ? 'red' :
                                                device.type === 'light' ? 'yellow' :
                                                    device.type === 'climate' ? 'blue' :
                                                        device.type === 'audio' ? 'purple' : 'gray'
                                        }>
                                            {device.type}
                                        </Tag>
                                    </Td>
                                    <Td>{device.location}</Td>
                                    <Td>{getStatusBadge(device.status || 'unknown')}</Td>
                                    <Td>{device.power || 'Unknown'}</Td>
                                    <Td>
                                        <HStack spacing={2}>
                                            {device.type === 'light' && (
                                                <Switch
                                                    size="sm"
                                                    isChecked={device.power?.toLowerCase() === 'on'}
                                                    onChange={() => toggleDevicePower(device.id, device.power || '')}
                                                    isDisabled={device.status?.toLowerCase() !== 'online'}
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