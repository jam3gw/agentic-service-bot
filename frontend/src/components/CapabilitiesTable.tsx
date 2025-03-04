import React from 'react';
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
} from '@chakra-ui/react';
import { CheckIcon, CloseIcon, InfoIcon } from '@chakra-ui/icons';

interface Capability {
    name: string;
    description: string;
    basic: boolean;
    premium: boolean;
    enterprise: boolean;
    category: 'device-control' | 'automation' | 'security' | 'integration' | 'analytics';
}

const capabilities: Capability[] = [
    {
        name: 'Basic Device Control',
        description: 'Control lights, thermostats, and other basic smart home devices',
        basic: true,
        premium: true,
        enterprise: true,
        category: 'device-control'
    },
    {
        name: 'Multi-Room Audio',
        description: 'Control audio playback across multiple rooms simultaneously',
        basic: false,
        premium: true,
        enterprise: true,
        category: 'device-control'
    },
    {
        name: 'Security Devices',
        description: 'Control locks, cameras, and security systems',
        basic: false,
        premium: true,
        enterprise: true,
        category: 'security'
    },
    {
        name: 'Basic Routines',
        description: 'Create simple routines with limited actions and triggers',
        basic: true,
        premium: true,
        enterprise: true,
        category: 'automation'
    },
    {
        name: 'Advanced Routines',
        description: 'Create complex routines with multiple conditions and actions',
        basic: false,
        premium: true,
        enterprise: true,
        category: 'automation'
    },
    {
        name: 'Scheduled Routines',
        description: 'Schedule routines to run at specific times or intervals',
        basic: false,
        premium: true,
        enterprise: true,
        category: 'automation'
    },
    {
        name: 'Third-Party Integrations',
        description: 'Connect with third-party services and devices',
        basic: false,
        premium: false,
        enterprise: true,
        category: 'integration'
    },
    {
        name: 'Energy Usage Analytics',
        description: 'View and analyze energy usage patterns',
        basic: false,
        premium: false,
        enterprise: true,
        category: 'analytics'
    },
    {
        name: 'Security Monitoring',
        description: 'Advanced security monitoring and alerts',
        basic: false,
        premium: false,
        enterprise: true,
        category: 'security'
    },
    {
        name: 'Guest Access',
        description: 'Create and manage guest access to your smart home',
        basic: false,
        premium: true,
        enterprise: true,
        category: 'security'
    },
];

interface CapabilitiesTableProps {
    customerId: string;
}

const CapabilitiesTable: React.FC<CapabilitiesTableProps> = ({ customerId }) => {
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const headerBgColor = useColorModeValue('gray.50', 'gray.700');

    // Determine which service level to highlight based on customer ID
    const serviceLevel =
        customerId === 'cust_001' ? 'basic' :
            customerId === 'cust_002' ? 'premium' : 'enterprise';

    // Group capabilities by category
    const categorizedCapabilities = capabilities.reduce((acc, capability) => {
        if (!acc[capability.category]) {
            acc[capability.category] = [];
        }
        acc[capability.category].push(capability);
        return acc;
    }, {} as Record<string, Capability[]>);

    const categoryNames = {
        'device-control': 'Device Control',
        'automation': 'Automation',
        'security': 'Security',
        'integration': 'Integrations',
        'analytics': 'Analytics'
    };

    const renderAvailability = (available: boolean) => {
        return available ? (
            <Icon as={CheckIcon} color="green.500" />
        ) : (
            <Icon as={CloseIcon} color="red.500" />
        );
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
            <Heading size="md" mb={4}>Service Level Capabilities</Heading>

            <Text mb={4}>
                This table shows the capabilities available at each service level. Your current service level is{' '}
                <Badge colorScheme={
                    serviceLevel === 'basic' ? 'gray' :
                        serviceLevel === 'premium' ? 'blue' : 'purple'
                }>
                    {serviceLevel.charAt(0).toUpperCase() + serviceLevel.slice(1)}
                </Badge>
            </Text>

            <Accordion allowMultiple defaultIndex={[0]}>
                {Object.entries(categorizedCapabilities).map(([category, categoryCapabilities]) => (
                    <AccordionItem key={category}>
                        <AccordionButton py={3}>
                            <Box flex="1" textAlign="left" fontWeight="semibold">
                                {categoryNames[category as keyof typeof categoryNames]}
                            </Box>
                            <AccordionIcon />
                        </AccordionButton>
                        <AccordionPanel pb={4} px={0}>
                            <Box overflowX="auto">
                                <Table variant="simple" size="sm">
                                    <Thead bg={headerBgColor}>
                                        <Tr>
                                            <Th>Capability</Th>
                                            <Th width="100px" textAlign="center">Basic</Th>
                                            <Th width="100px" textAlign="center">Premium</Th>
                                            <Th width="100px" textAlign="center">Enterprise</Th>
                                        </Tr>
                                    </Thead>
                                    <Tbody>
                                        {categoryCapabilities.map((capability) => (
                                            <Tr key={capability.name}>
                                                <Td>
                                                    <Text fontWeight="medium">{capability.name}</Text>
                                                    <Text fontSize="xs" color="gray.500">{capability.description}</Text>
                                                </Td>
                                                <Td textAlign="center">{renderAvailability(capability.basic)}</Td>
                                                <Td textAlign="center">{renderAvailability(capability.premium)}</Td>
                                                <Td textAlign="center">{renderAvailability(capability.enterprise)}</Td>
                                            </Tr>
                                        ))}
                                    </Tbody>
                                </Table>
                            </Box>
                        </AccordionPanel>
                    </AccordionItem>
                ))}
            </Accordion>

            <Box mt={4} p={3} bg={useColorModeValue('blue.50', 'blue.900')} borderRadius="md">
                <Text fontSize="sm" display="flex" alignItems="center">
                    <Icon as={InfoIcon} mr={2} color="blue.500" />
                    Want to upgrade your service level? Contact our sales team for more information.
                </Text>
            </Box>
        </Box>
    );
};

export default CapabilitiesTable; 