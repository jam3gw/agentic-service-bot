import React from 'react';
import {
    Box,
    Heading,
    Text,
    VStack,
    Accordion,
    AccordionItem,
    AccordionButton,
    AccordionPanel,
    AccordionIcon,
    List,
    ListItem,
    ListIcon,
    useColorModeValue,
    Link,
    Code,
    Flex,
    Badge,
    SimpleGrid,
} from '@chakra-ui/react';
import { CheckCircleIcon, InfoIcon } from '@chakra-ui/icons';

const InstructionsSection: React.FC = () => {
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const accentColor = useColorModeValue('blue.500', 'blue.300');
    const diagramBg = useColorModeValue('gray.50', 'gray.700');

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
            <VStack align="stretch" spacing={6}>
                <Flex direction={{ base: "column", md: "row" }} align="center" justify="space-between">
                    <Box>
                        <Heading size="lg" mb={2} color={accentColor}>
                            Agentic Service Bot Demo
                        </Heading>
                        <Text fontSize="md" lineHeight="tall" maxW="600px">
                            A demonstration of autonomous agent architecture for smart home device control,
                            showcasing service level permissions, state management, and AI-powered natural language understanding.
                        </Text>
                    </Box>
                    <Box mt={{ base: 4, md: 0 }}>
                        <Badge colorScheme="green" fontSize="0.8em" p={1} borderRadius="md">
                            Interview Demo
                        </Badge>
                    </Box>
                </Flex>

                {/* Technical Architecture Highlight Section */}
                <Box
                    p={5}
                    bg={diagramBg}
                    borderRadius="md"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <VStack spacing={4} align="stretch">
                        <Heading size="md" color={accentColor}>
                            System Architecture & Message Flow
                        </Heading>

                        <Text>
                            This application demonstrates a complete serverless architecture with AI integration.
                            The sequence diagram below shows how a user message flows through the system:
                        </Text>

                        <Box
                            borderWidth="1px"
                            borderColor={borderColor}
                            borderRadius="md"
                            overflow="hidden"
                            bg={bgColor}
                        >
                            <img
                                src="/images/ui/chat_bot_sequence_diagram.png"
                                alt="Chat Bot Sequence Diagram"
                                style={{ width: '100%', height: 'auto' }}
                            />
                        </Box>

                        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mt={2}>
                            <Box>
                                <Text fontWeight="medium" fontSize="sm" mb={1}>
                                    Key Components:
                                </Text>
                                <List spacing={1} fontSize="sm">
                                    <ListItem>
                                        <ListIcon as={InfoIcon} color={accentColor} />
                                        React Frontend with Chakra UI
                                    </ListItem>
                                    <ListItem>
                                        <ListIcon as={InfoIcon} color={accentColor} />
                                        AWS API Gateway + Lambda Backend
                                    </ListItem>
                                    <ListItem>
                                        <ListIcon as={InfoIcon} color={accentColor} />
                                        DynamoDB for Data Persistence
                                    </ListItem>
                                    <ListItem>
                                        <ListIcon as={InfoIcon} color={accentColor} />
                                        Anthropic Claude API for NLU
                                    </ListItem>
                                </List>
                            </Box>
                            <Box>
                                <Text fontWeight="medium" fontSize="sm" mb={1}>
                                    Technical Highlights:
                                </Text>
                                <List spacing={1} fontSize="sm">
                                    <ListItem>
                                        <ListIcon as={InfoIcon} color={accentColor} />
                                        Service Level Permission Management
                                    </ListItem>
                                    <ListItem>
                                        <ListIcon as={InfoIcon} color={accentColor} />
                                        Two-Stage AI Request Analysis
                                    </ListItem>
                                    <ListItem>
                                        <ListIcon as={InfoIcon} color={accentColor} />
                                        Real-time State Synchronization
                                    </ListItem>
                                    <ListItem>
                                        <ListIcon as={InfoIcon} color={accentColor} />
                                        Contextual Response Generation
                                    </ListItem>
                                </List>
                            </Box>
                        </SimpleGrid>
                    </VStack>
                </Box>

                {/* Quick Start Guide */}
                <Box p={4} bg={useColorModeValue('blue.50', 'blue.900')} borderRadius="md">
                    <Text fontWeight="medium" fontSize="md" mb={2}>
                        🚀 Quick Demo Guide:
                    </Text>
                    <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                        <Box>
                            <Text fontWeight="bold" fontSize="sm">1. Select a Customer</Text>
                            <Text fontSize="sm">Choose different service tiers to demonstrate permission boundaries</Text>
                        </Box>
                        <Box>
                            <Text fontWeight="bold" fontSize="sm">2. Try These Commands</Text>
                            <Text fontSize="sm">"Turn on my speaker", "Set volume to 80", "Play jazz music"</Text>
                        </Box>
                        <Box>
                            <Text fontWeight="bold" fontSize="sm">3. Observe the Response</Text>
                            <Text fontSize="sm">Note how responses adapt based on service level permissions</Text>
                        </Box>
                    </SimpleGrid>
                </Box>

                {/* Detailed Information in Accordions */}
                <Accordion allowMultiple>
                    <AccordionItem>
                        <AccordionButton>
                            <Box flex="1" textAlign="left" fontWeight="semibold">
                                Service Tiers & Features
                            </Box>
                            <AccordionIcon />
                        </AccordionButton>
                        <AccordionPanel pb={4}>
                            <List spacing={2}>
                                <ListItem>
                                    <ListIcon as={CheckCircleIcon} color="green.500" />
                                    <Text as="span" fontWeight="medium">Basic tier:</Text> Control basic device power functions
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={CheckCircleIcon} color="green.500" />
                                    <Text as="span" fontWeight="medium">Premium tier:</Text> Additional volume control capabilities
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={CheckCircleIcon} color="green.500" />
                                    <Text as="span" fontWeight="medium">Enterprise tier:</Text> Full control including song changes
                                </ListItem>
                            </List>
                        </AccordionPanel>
                    </AccordionItem>

                    <AccordionItem>
                        <AccordionButton>
                            <Box flex="1" textAlign="left" fontWeight="semibold">
                                System Architecture Details
                            </Box>
                            <AccordionIcon />
                        </AccordionButton>
                        <AccordionPanel pb={4}>
                            <VStack align="stretch" spacing={3}>
                                <Text>
                                    Our service bot is built on a modern, scalable architecture:
                                </Text>
                                <Box
                                    bg={useColorModeValue('gray.50', 'gray.900')}
                                    p={4}
                                    borderRadius="md"
                                    fontFamily="mono"
                                >
                                    <Code display="block" whiteSpace="pre" p={4}>
                                        {`┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   React UI   │     │ API Gateway  │     │   DynamoDB   │
│  (Frontend)  │────▶│   + Lambda   │────▶│  (Database)  │
└──────────────┘     └──────────────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Claude API  │
                    │    (LLM)     │
                    └──────────────┘`}
                                    </Code>
                                </Box>

                                <List spacing={2}>
                                    <ListItem>
                                        <ListIcon as={CheckCircleIcon} color="green.500" />
                                        <Text as="span" fontWeight="medium">Frontend:</Text> React + Chakra UI for a responsive interface
                                    </ListItem>
                                    <ListItem>
                                        <ListIcon as={CheckCircleIcon} color="green.500" />
                                        <Text as="span" fontWeight="medium">Backend:</Text> AWS Lambda + API Gateway for serverless operations
                                    </ListItem>
                                    <ListItem>
                                        <ListIcon as={CheckCircleIcon} color="green.500" />
                                        <Text as="span" fontWeight="medium">Database:</Text> DynamoDB for device and customer data
                                    </ListItem>
                                    <ListItem>
                                        <ListIcon as={CheckCircleIcon} color="green.500" />
                                        <Text as="span" fontWeight="medium">AI Integration:</Text> Claude API for natural language understanding
                                    </ListItem>
                                </List>
                            </VStack>
                        </AccordionPanel>
                    </AccordionItem>

                    <AccordionItem>
                        <AccordionButton>
                            <Box flex="1" textAlign="left" fontWeight="semibold">
                                Autonomous Agent Implementation
                            </Box>
                            <AccordionIcon />
                        </AccordionButton>
                        <AccordionPanel pb={4}>
                            <VStack align="stretch" spacing={3}>
                                <Text>
                                    This service bot implements the principles outlined in Anthropic's{' '}
                                    <Link
                                        href="https://www.anthropic.com/engineering/building-effective-agents"
                                        color={accentColor}
                                        isExternal
                                    >
                                        Building Effective Agents
                                    </Link> guide, demonstrating autonomous decision-making in a real-world application:
                                </Text>
                                <List spacing={3}>
                                    <ListItem>
                                        <ListIcon as={CheckCircleIcon} color="green.500" />
                                        <Text as="span" fontWeight="medium">Service Level Management:</Text>
                                        <Text mt={1} ml={6}>
                                            The agent checks DynamoDB for the customer's service level (Basic, Premium, or Enterprise)
                                            before processing each request. This determines which actions are permitted:
                                        </Text>
                                        <List spacing={2} ml={8} mt={2}>
                                            <ListItem fontSize="sm">
                                                • Basic: Power control only
                                            </ListItem>
                                            <ListItem fontSize="sm">
                                                • Premium: Adds volume control
                                            </ListItem>
                                            <ListItem fontSize="sm">
                                                • Enterprise: Full functionality including music control
                                            </ListItem>
                                        </List>
                                    </ListItem>

                                    <ListItem>
                                        <ListIcon as={CheckCircleIcon} color="green.500" />
                                        <Text as="span" fontWeight="medium">Request Analysis & Routing:</Text>
                                        <Text mt={1} ml={6}>
                                            The agent analyzes natural language requests using pattern matching and semantic
                                            understanding to identify the intended action. It then:
                                        </Text>
                                        <List spacing={2} ml={8} mt={2}>
                                            <ListItem fontSize="sm">
                                                • Categorizes requests (power, volume, music control)
                                            </ListItem>
                                            <ListItem fontSize="sm">
                                                • Validates against service level permissions
                                            </ListItem>
                                            <ListItem fontSize="sm">
                                                • Routes to appropriate DynamoDB update operations
                                            </ListItem>
                                        </List>
                                    </ListItem>

                                    <ListItem>
                                        <ListIcon as={CheckCircleIcon} color="green.500" />
                                        <Text as="span" fontWeight="medium">State Management:</Text>
                                        <Text mt={1} ml={6}>
                                            Device states are maintained in DynamoDB, with the agent handling:
                                        </Text>
                                        <List spacing={2} ml={8} mt={2}>
                                            <ListItem fontSize="sm">
                                                • Atomic updates to device attributes
                                            </ListItem>
                                            <ListItem fontSize="sm">
                                                • Real-time state synchronization
                                            </ListItem>
                                        </List>
                                    </ListItem>

                                    <ListItem>
                                        <ListIcon as={CheckCircleIcon} color="green.500" />
                                        <Text as="span" fontWeight="medium">Intelligent Response Generation:</Text>
                                        <Text mt={1} ml={6}>
                                            When requests exceed service level permissions, the agent:
                                        </Text>
                                        <List spacing={2} ml={8} mt={2}>
                                            <ListItem fontSize="sm">
                                                • Explains the limitation clearly
                                            </ListItem>
                                            <ListItem fontSize="sm">
                                                • Suggests available alternatives
                                            </ListItem>
                                            <ListItem fontSize="sm">
                                                • Provides upgrade information when relevant
                                            </ListItem>
                                        </List>
                                    </ListItem>
                                </List>
                                <Text fontSize="sm" color="gray.500" mt={2}>
                                    This implementation showcases how autonomous agents can handle complex business logic
                                    while maintaining a natural conversation flow and respecting system constraints.
                                </Text>
                            </VStack>
                        </AccordionPanel>
                    </AccordionItem>
                </Accordion>
            </VStack>
        </Box>
    );
};

export default InstructionsSection; 