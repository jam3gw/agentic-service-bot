import React, { useState, useEffect } from 'react';
import {
    Box,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Heading,
    Text,
    useColorModeValue,
    Badge,
    Accordion,
    AccordionItem,
    AccordionButton,
    AccordionPanel,
    AccordionIcon,
    Icon,
    Spinner,
    Alert,
    AlertIcon,
    Flex,
} from '@chakra-ui/react';
import { CheckIcon, CloseIcon, InfoIcon } from '@chakra-ui/icons';
import * as apiService from '../utils/apiService';
import { Capability } from '../types';

// Fallback capabilities in case API fails
const fallbackCapabilities: Capability[] = [
    {
        id: 'device-status',
        name: 'Device Status Check',
        description: 'Check the status of smart home devices',
        tiers: {
            basic: true,
            premium: true,
            enterprise: true
        },
        category: 'device-control'
    },
    {
        id: 'device-power',
        name: 'Device Power Control',
        description: 'Turn devices on and off',
        tiers: {
            basic: true,
            premium: true,
            enterprise: true
        },
        category: 'device-control'
    },
    {
        id: 'volume-control',
        name: 'Volume Control',
        description: 'Adjust volume levels of audio devices',
        tiers: {
            basic: false,
            premium: true,
            enterprise: true
        },
        category: 'device-control'
    },
    {
        id: 'song-changes',
        name: 'Song Changes',
        description: 'Change songs and manage playlists',
        tiers: {
            basic: false,
            premium: false,
            enterprise: true
        },
        category: 'device-control'
    },
    {
        id: 'max-devices',
        name: 'Device Limit',
        description: 'Maximum of 1 device allowed',
        tiers: {
            basic: true,
            premium: true,
            enterprise: true
        },
        category: 'capacity'
    },
    {
        id: 'standard-support',
        name: 'Standard Support',
        description: 'Email support with 48-hour response time',
        tiers: {
            basic: true,
            premium: false,
            enterprise: false
        },
        category: 'support'
    },
    {
        id: 'priority-support',
        name: 'Priority Support',
        description: 'Email and chat support with 24-hour response time',
        tiers: {
            basic: false,
            premium: true,
            enterprise: false
        },
        category: 'support'
    },
    {
        id: 'dedicated-support',
        name: 'Dedicated Support',
        description: 'Email, chat, and phone support with dedicated account manager',
        tiers: {
            basic: false,
            premium: false,
            enterprise: true
        },
        category: 'support'
    }
];

interface CapabilitiesTableProps {
    customerId: string;
}

const CapabilitiesTable: React.FC<CapabilitiesTableProps> = ({ customerId }) => {
    const [capabilities, setCapabilities] = useState<Capability[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [customerLevel, setCustomerLevel] = useState<string>('basic');

    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const headerBg = useColorModeValue('gray.50', 'gray.700');

    // Load capabilities from API
    useEffect(() => {
        const loadCapabilities = async () => {
            setIsLoading(true);
            setError(null);

            try {
                // Fetch capabilities from API
                const fetchedCapabilities = await apiService.fetchServiceCapabilities();

                // Validate and normalize capabilities data
                const validCapabilities = fetchedCapabilities.map(capability => {
                    // Ensure tiers object exists and has the correct structure
                    if (!capability.tiers) {
                        capability.tiers = {
                            basic: false,
                            premium: false,
                            enterprise: false
                        };
                    } else if (typeof capability.tiers !== 'object') {
                        // Handle case where tiers might be in a different format
                        capability.tiers = {
                            basic: false,
                            premium: false,
                            enterprise: false
                        };
                    }

                    // Ensure all tier properties exist
                    capability.tiers.basic = !!capability.tiers.basic;
                    capability.tiers.premium = !!capability.tiers.premium;
                    capability.tiers.enterprise = !!capability.tiers.enterprise;

                    return capability;
                });

                setCapabilities(validCapabilities.length > 0 ? validCapabilities : fallbackCapabilities);

                // Fetch customer to get service level
                const customers = await apiService.fetchCustomers();
                const customer = customers.find(c => c.id === customerId);
                if (customer) {
                    setCustomerLevel(customer.level);
                }
            } catch (err) {
                console.error('Error loading capabilities:', err);
                setError(`Failed to load capabilities: ${err instanceof Error ? err.message : String(err)}`);
                setCapabilities(fallbackCapabilities);
            } finally {
                setIsLoading(false);
            }
        };

        loadCapabilities();
    }, [customerId]);

    // Group capabilities by category
    const groupedCapabilities = capabilities.reduce((acc, capability) => {
        const category = capability.category;
        if (!acc[category]) {
            acc[category] = [];
        }
        acc[category].push(capability);
        return acc;
    }, {} as Record<string, Capability[]>);

    // Format category name
    const formatCategoryName = (category: string): string => {
        const categoryMap: Record<string, string> = {
            'device-control': 'Device Control',
            'capacity': 'Device Capacity',
            'support': 'Support Services',
        };

        return categoryMap[category] || category.split('-').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    };

    // Render availability icon
    const renderAvailability = (available: boolean | undefined) => {
        // Default to false if undefined
        return available === true ? (
            <Icon as={CheckIcon} color="green.500" />
        ) : (
            <Icon as={CloseIcon} color="red.500" />
        );
    };

    // Render table row for a capability
    const renderCapabilityRow = (capability: Capability) => {
        return (
            <Tr key={capability.id}>
                <Td>
                    <Box>
                        <Text fontWeight="medium">{capability.name}</Text>
                        <Text fontSize="sm" color="gray.500">{capability.description}</Text>
                    </Box>
                </Td>
                <Td>{renderAvailability(capability.tiers?.basic)}</Td>
                <Td>{renderAvailability(capability.tiers?.premium)}</Td>
                <Td>{renderAvailability(capability.tiers?.enterprise)}</Td>
            </Tr>
        );
    };

    if (isLoading) {
        return (
            <Flex justify="center" align="center" py={10} direction="column">
                <Spinner size="xl" mb={4} />
                <Text>Loading capabilities...</Text>
            </Flex>
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
            <Heading size="md" mb={4}>Service Capabilities</Heading>

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

            <Accordion allowMultiple defaultIndex={[0]}>
                {Object.entries(groupedCapabilities).map(([category, categoryCapabilities]) => (
                    <AccordionItem key={category}>
                        <h2>
                            <AccordionButton py={3}>
                                <Box flex="1" textAlign="left" fontWeight="bold">
                                    {formatCategoryName(category)}
                                </Box>
                                <AccordionIcon />
                            </AccordionButton>
                        </h2>
                        <AccordionPanel pb={4}>
                            <Box overflowX="auto">
                                <Table variant="simple" size="sm">
                                    <Thead bg={headerBg}>
                                        <Tr>
                                            <Th>Capability</Th>
                                            <Th>Basic</Th>
                                            <Th>Premium</Th>
                                            <Th>Enterprise</Th>
                                        </Tr>
                                    </Thead>
                                    <Tbody>
                                        {categoryCapabilities.map((capability) => renderCapabilityRow(capability))}
                                    </Tbody>
                                </Table>
                            </Box>
                        </AccordionPanel>
                    </AccordionItem>
                ))}
            </Accordion>
        </Box>
    );
};

export default CapabilitiesTable; 