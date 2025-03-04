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
                    Welcome to Your Smart Home Assistant
                </Heading>

                <Text>
                    This assistant helps you control your smart home devices, set up routines, and manage your smart home ecosystem.
                    Your available features depend on your service level.
                </Text>

                <Accordion allowToggle defaultIndex={[0]}>
                    <AccordionItem border="none">
                        <AccordionButton px={0}>
                            <Box flex="1" textAlign="left" fontWeight="semibold">
                                How to Use This Assistant
                            </Box>
                            <AccordionIcon />
                        </AccordionButton>
                        <AccordionPanel pb={4} pl={4}>
                            <List spacing={2}>
                                <ListItem>
                                    <ListIcon as={CheckCircleIcon} color="green.500" />
                                    <Text as="span" fontWeight="medium">Control devices:</Text> "Turn on the living room lights" or "Set thermostat to 72 degrees"
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={CheckCircleIcon} color="green.500" />
                                    <Text as="span" fontWeight="medium">Multi-room control:</Text> "Play music in all rooms" or "Turn off lights downstairs"
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={CheckCircleIcon} color="green.500" />
                                    <Text as="span" fontWeight="medium">Create routines:</Text> "Create a morning routine that turns on lights and plays news at 7am"
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={CheckCircleIcon} color="green.500" />
                                    <Text as="span" fontWeight="medium">Get information:</Text> "What's the temperature in the bedroom?" or "Is the front door locked?"
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