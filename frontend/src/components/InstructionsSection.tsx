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
} from '@chakra-ui/react';
import { CheckCircleIcon, InfoIcon } from '@chakra-ui/icons';

const InstructionsSection: React.FC = () => {
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

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
            <VStack align="stretch" spacing={4}>
                <Heading size="md" mb={2}>
                    Welcome to the Agentic Service Bot
                </Heading>

                <Text>
                    This service bot helps you manage your devices and services based on your subscription tier.
                    Different service levels (Basic, Premium, Enterprise) provide access to different capabilities.
                </Text>

                <Accordion allowToggle defaultIndex={[0]}>
                    <AccordionItem border="none">
                        <AccordionButton px={0}>
                            <Box flex="1" textAlign="left" fontWeight="semibold">
                                How to Use This Service
                            </Box>
                            <AccordionIcon />
                        </AccordionButton>
                        <AccordionPanel pb={4} pl={4}>
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
                                <ListItem>
                                    <ListIcon as={InfoIcon} color="blue.500" />
                                    All service tiers are limited to 1 device maximum
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={InfoIcon} color="blue.500" />
                                    Try different user profiles to see how service levels affect available features
                                </ListItem>
                            </List>
                        </AccordionPanel>
                    </AccordionItem>
                </Accordion>
            </VStack>
        </Box>
    );
};

export default InstructionsSection; 