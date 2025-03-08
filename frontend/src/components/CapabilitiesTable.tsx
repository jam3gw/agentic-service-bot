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
    Alert,
    AlertIcon,
    useColorModeValue,
    Spinner,
} from '@chakra-ui/react';
import * as apiService from '../utils/apiService';
import { Capability, Customer } from '../types';

interface CapabilitiesTableProps {
    customerId?: string;  // Make customerId optional
}

const CapabilitiesTable: React.FC<CapabilitiesTableProps> = ({ customerId }) => {
    const [capabilities, setCapabilities] = useState<Capability[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [customerLevel, setCustomerLevel] = useState<'basic' | 'premium' | 'enterprise'>('basic');
    const [selectedCustomerId, setSelectedCustomerId] = useState<string | undefined>(customerId);

    // Colors
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    // Load capabilities from API
    useEffect(() => {
        const loadCapabilities = async () => {
            setIsLoading(true);
            setError(null);

            try {
                // Fetch capabilities from API
                const fetchedCapabilities = await apiService.fetchServiceCapabilities();
                setCapabilities(fetchedCapabilities);

                // Fetch customers and use first one if no customerId provided
                const customers = await apiService.fetchCustomers();
                let targetCustomer: Customer | undefined;

                if (selectedCustomerId) {
                    targetCustomer = customers.find(c => c.id === selectedCustomerId);
                }

                if (!targetCustomer && customers.length > 0) {
                    targetCustomer = customers[0];
                    setSelectedCustomerId(targetCustomer.id);
                }

                if (targetCustomer) {
                    setCustomerLevel(targetCustomer.level as 'basic' | 'premium' | 'enterprise');
                } else {
                    setError('No customers found');
                }
            } catch (err) {
                setError(`Failed to load capabilities: ${err instanceof Error ? err.message : String(err)}`);
            } finally {
                setIsLoading(false);
            }
        };

        loadCapabilities();
    }, [selectedCustomerId]);

    if (isLoading) {
        return (
            <Box textAlign="center" py={10}>
                <Spinner size="xl" />
                <Text mt={4}>Loading capabilities...</Text>
            </Box>
        );
    }

    return (
        <Box
            bg={bgColor}
            p={5}
            borderRadius="md"
            boxShadow="md"
            borderWidth="1px"
            borderColor={borderColor}
        >
            <Heading size="md" mb={4}>Your Service Capabilities</Heading>

            {error && (
                <Alert status="error" mb={4}>
                    <AlertIcon />
                    <Text>{error}</Text>
                </Alert>
            )}

            <Text mb={4}>
                Your current service level: <Badge colorScheme={
                    customerLevel === 'enterprise' ? 'purple' :
                        customerLevel === 'premium' ? 'blue' : 'gray'
                }>{customerLevel.toUpperCase()}</Badge>
            </Text>

            <Table variant="simple">
                <Thead>
                    <Tr>
                        <Th>Capability</Th>
                        <Th>Description</Th>
                        <Th>Available</Th>
                    </Tr>
                </Thead>
                <Tbody>
                    {capabilities.map(capability => (
                        <Tr key={capability.id}>
                            <Td>
                                <Text fontWeight="medium">{capability.name}</Text>
                            </Td>
                            <Td>{capability.description}</Td>
                            <Td>
                                <Badge colorScheme={capability.tiers[customerLevel] ? 'green' : 'red'}>
                                    {capability.tiers[customerLevel] ? 'Yes' : 'No'}
                                </Badge>
                            </Td>
                        </Tr>
                    ))}
                </Tbody>
            </Table>
        </Box>
    );
};

export default CapabilitiesTable; 