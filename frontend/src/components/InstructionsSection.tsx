import React from 'react';
import {
    Box,
    Heading,
    Text,
    VStack,
    List,
    ListItem,
    ListIcon,
    useColorModeValue,
    SimpleGrid,
    Modal,
    ModalOverlay,
    ModalContent,
    ModalBody,
    ModalCloseButton,
    useDisclosure,
    Flex,
} from '@chakra-ui/react';
import { InfoIcon, SearchIcon } from '@chakra-ui/icons';

const InstructionsSection: React.FC = () => {
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const accentColor = useColorModeValue('blue.500', 'blue.300');
    const diagramBg = useColorModeValue('gray.50', 'gray.700');

    // Modal control for image zoom
    const { isOpen, onOpen, onClose } = useDisclosure();

    return (
        <Box
            bg={bgColor}
            p={4}
            borderRadius="md"
            boxShadow="md"
            borderWidth="1px"
            borderColor={borderColor}
            mb={3}
        >
            <VStack align="stretch" spacing={3}>
                <Box textAlign="center" mx="auto" maxW="800px">
                    <Heading size="lg" mb={2} color={accentColor}>
                        Agentic Service Bot Demo
                    </Heading>
                    <Text fontSize="md" lineHeight="tall">
                        A demonstration of autonomous agent architecture for smart home device control,
                        showcasing service level permissions, state management, and AI-powered natural language understanding.
                    </Text>
                </Box>

                {/* Technical Architecture Highlight Section */}
                <Box
                    p={4}
                    bg={diagramBg}
                    borderRadius="md"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <VStack spacing={3} align="stretch">
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
                            position="relative"
                            cursor="pointer"
                            onClick={onOpen}
                            _hover={{
                                boxShadow: "lg",
                                "& .zoom-icon": { opacity: 1 }
                            }}
                        >
                            <img
                                src="/images/ui/chat_bot_sequence_diagram.png"
                                alt="Chat Bot Sequence Diagram"
                                style={{ width: '100%', height: 'auto' }}
                            />
                            <Flex
                                position="absolute"
                                top="8px"
                                right="8px"
                                className="zoom-icon"
                                opacity="0.7"
                                transition="opacity 0.2s"
                                bg="rgba(0,0,0,0.1)"
                                borderRadius="md"
                                p={1}
                            >
                                <SearchIcon color={accentColor} boxSize={5} />
                                <Text fontSize="xs" ml={1} fontWeight="medium" color={accentColor}>Click to zoom</Text>
                            </Flex>
                        </Box>

                        {/* Image Zoom Modal */}
                        <Modal isOpen={isOpen} onClose={onClose} size="5xl" isCentered>
                            <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(10px)" />
                            <ModalContent bg={bgColor}>
                                <ModalCloseButton size="lg" />
                                <ModalBody p={4}>
                                    <img
                                        src="/images/ui/chat_bot_sequence_diagram.png"
                                        alt="Chat Bot Sequence Diagram (Enlarged)"
                                        style={{ width: '100%', height: 'auto', maxHeight: '80vh', objectFit: 'contain' }}
                                    />
                                </ModalBody>
                            </ModalContent>
                        </Modal>

                        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3} mt={1}>
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
                <Box p={3} bg={useColorModeValue('blue.50', 'blue.900')} borderRadius="md">
                    <Text fontWeight="medium" fontSize="md" mb={2}>
                        🚀 Quick Demo Guide:
                    </Text>
                    <SimpleGrid columns={{ base: 1, md: 3 }} spacing={3}>
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
            </VStack>
        </Box>
    );
};

export default InstructionsSection; 