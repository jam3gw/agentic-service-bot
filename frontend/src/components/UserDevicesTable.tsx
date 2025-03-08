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
    IconButton,
    Tooltip,
    Alert,
    AlertIcon,
    Flex,
} from '@chakra-ui/react';
import { RepeatIcon } from '@chakra-ui/icons';
import * as apiService from '../utils/apiService';
import { Device } from '../types';

interface UserDevicesTableProps {
    customerId: string;
    lastUpdate: number;
}

const UserDevicesTable: React.FC<UserDevicesTableProps> = ({ customerId, lastUpdate }) => {
    const [devices, setDevices] = useState<Device[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [lastRefreshed, setLastRefreshed] = useState(new Date());

    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    // Load devices from API
    const loadDevices = async () => {
        if (!customerId) {
            setDevices([]);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const fetchedDevices = await apiService.fetchUserDevices(customerId);
            setDevices(fetchedDevices);
            setLastRefreshed(new Date());
        } catch (err) {
            setError(`Failed to load devices: ${err instanceof Error ? err.message : String(err)}`);
            setDevices([]);
        } finally {
            setIsLoading(false);
        }
    };

    // Load devices when customer changes or lastUpdate changes
    useEffect(() => {
        if (customerId) {
            loadDevices();
        }
    }, [customerId, lastUpdate]);

    // Refresh devices
    const refreshDevices = () => {
        loadDevices();
    };

    return (
        <Box
            bg={bgColor}
            p={4}
            borderRadius="md"
            boxShadow="sm"
            borderWidth="1px"
            borderColor={borderColor}
            mb={4}
            maxH="400px"
            overflowY="auto"
        >
            <HStack justifyContent="space-between" mb={3}>
                <Box>
                    <Heading size="md" mb={0}>Your Smart Devices</Heading>
                    <Text fontSize="xs" color="gray.500">
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
                <Table variant="simple" size="sm">
                    <Thead>
                        <Tr>
                            <Th>Device</Th>
                            <Th>Power</Th>
                            <Th>Volume</Th>
                            <Th>Song</Th>
                        </Tr>
                    </Thead>
                    <Tbody>
                        {devices.map(device => (
                            <Tr key={device.id}>
                                <Td>
                                    <Box>
                                        <Text fontWeight="medium">{device.name}</Text>
                                        <HStack spacing={1} mt={1}>
                                            <Tag size="sm" colorScheme={
                                                device.type === 'security' ? 'red' :
                                                    device.type === 'light' ? 'yellow' :
                                                        device.type === 'climate' ? 'blue' :
                                                            device.type === 'audio' ? 'purple' : 'gray'
                                            }>
                                                <Text fontSize="md" fontWeight="medium">{device.type}</Text>
                                            </Tag>
                                        </HStack>
                                    </Box>
                                </Td>
                                <Td>
                                    <Badge colorScheme={device.power?.toLowerCase() === 'on' ? 'green' : 'gray'}>
                                        {device.power || 'Unknown'}
                                    </Badge>
                                </Td>
                                <Td>
                                    {(device.type === 'audio' || device.type === 'speaker') && (
                                        <Text fontSize="sm">
                                            {device.power === 'off' ? '0' : device.volume || 0}%
                                        </Text>
                                    )}
                                </Td>
                                <Td>
                                    {(device.type === 'audio' || device.type === 'speaker') && (
                                        <Text fontSize="sm" noOfLines={1}>
                                            {device.power === 'off' ? 'None' : device.currentSong || 'No song playing'}
                                        </Text>
                                    )}
                                </Td>
                            </Tr>
                        ))}
                    </Tbody>
                </Table>
            )}
        </Box>
    );
};

export default UserDevicesTable; 