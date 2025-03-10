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
    UnorderedList,
    ListItem,
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
            maxH="800px"
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

            <Box
                bg={useColorModeValue('purple.50', 'purple.900')}
                p={4}
                borderRadius="md"
                mb={4}
            >
                <Text fontSize="sm" fontWeight="medium" mb={2}>
                    🎵 Welcome to Your Smart Home Control Center!
                </Text>
                <Text fontSize="sm" mb={2}>
                    Here you can monitor and control all your smart devices. For audio devices and speakers:
                </Text>
                <Box pl={4}>
                    <UnorderedList fontSize="sm" spacing={2}>
                        <ListItem>View device power status (on/off) and current volume level</ListItem>
                        <ListItem>See what's currently playing on each device</ListItem>
                        <ListItem>Browse the full playlist when a device is powered on</ListItem>
                        <ListItem>Use the chat interface below to control your devices with natural language</ListItem>
                        <ListItem>For music control, you can only play songs from the device's existing playlist</ListItem>
                    </UnorderedList>
                </Box>
                <Text fontSize="sm" mt={2}>
                    Try saying: <Text as="span" fontWeight="medium">"Turn on the living room speaker"</Text>,{' '}
                    <Text as="span" fontWeight="medium">"Set the volume to 50%"</Text>, or{' '}
                    <Text as="span" fontWeight="medium">"Play the next song"</Text>
                </Text>
            </Box>

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
                            <React.Fragment key={device.id}>
                                <Tr>
                                    <Td>
                                        <Box>
                                            <HStack spacing={1}>
                                                <Tag size="sm" colorScheme={
                                                    device.type === 'security' ? 'red' :
                                                        device.type === 'light' ? 'yellow' :
                                                            device.type === 'climate' ? 'blue' :
                                                                device.type === 'audio' || device.type === 'speaker' ? 'purple' : 'gray'
                                                }>
                                                    <Text fontSize="md" fontWeight="medium" textTransform="capitalize">{device.type}</Text>
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
                                {(device.type === 'audio' || device.type === 'speaker') && device.playlist && device.power === 'on' && (
                                    <Tr>
                                        <Td colSpan={4}>
                                            <Box pl={4} py={2} borderLeft="2px" borderColor="purple.200">
                                                <Text fontSize="sm" fontWeight="medium" mb={2}>Playlist:</Text>
                                                <Box maxH="300px" overflowY="auto">
                                                    {device.playlist.map((song, index) => (
                                                        <HStack
                                                            key={index}
                                                            spacing={2}
                                                            mb={1}
                                                            bg={index === device.currentSongIndex ? "purple.50" : "transparent"}
                                                            p={1}
                                                            borderRadius="md"
                                                        >
                                                            <Text fontSize="xs" color="gray.500" w="20px">{index + 1}.</Text>
                                                            <Text fontSize="sm" noOfLines={1}>{song}</Text>
                                                            {index === device.currentSongIndex && (
                                                                <Badge colorScheme="purple" fontSize="xs">Now Playing</Badge>
                                                            )}
                                                        </HStack>
                                                    ))}
                                                </Box>
                                            </Box>
                                        </Td>
                                    </Tr>
                                )}
                            </React.Fragment>
                        ))}
                    </Tbody>
                </Table>
            )}
        </Box>
    );
};

export default UserDevicesTable; 