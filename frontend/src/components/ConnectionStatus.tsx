import React from 'react';
import { Box, Text, Flex, Badge, useColorModeValue, HStack, Icon } from '@chakra-ui/react';
import * as websocketClient from '../utils/websocketClient';

const ConnectionStatus: React.FC = () => {
    const isConnected = websocketClient.isConnected;
    const isConnecting = websocketClient.isConnecting;
    const connectionError = websocketClient.connectionError;

    // Theme colors
    const errorBg = useColorModeValue('red.50', 'rgba(254, 178, 178, 0.16)');
    const errorBorder = useColorModeValue('red.200', 'red.500');
    const errorText = useColorModeValue('red.800', 'red.200');

    const warningBg = useColorModeValue('yellow.50', 'rgba(250, 240, 137, 0.16)');
    const warningBorder = useColorModeValue('yellow.200', 'yellow.500');
    const warningText = useColorModeValue('yellow.800', 'yellow.200');

    const infoBg = useColorModeValue('gray.50', 'rgba(160, 174, 192, 0.16)');
    const infoBorder = useColorModeValue('gray.200', 'gray.500');
    const infoText = useColorModeValue('gray.800', 'gray.200');

    // Don't show anything if connected
    if (isConnected.value && !connectionError.value) {
        return null;
    }

    let statusText = '';
    let statusBg = infoBg;
    let statusBorder = infoBorder;
    let statusTextColor = infoText;
    let indicatorColor = 'gray.500';

    if (isConnecting.value) {
        statusText = 'Connecting to server...';
        statusBg = warningBg;
        statusBorder = warningBorder;
        statusTextColor = warningText;
        indicatorColor = 'yellow.500';
    } else if (connectionError.value) {
        statusText = connectionError.value;
        statusBg = errorBg;
        statusBorder = errorBorder;
        statusTextColor = errorText;
        indicatorColor = 'red.500';
    } else if (!isConnected.value) {
        statusText = 'Disconnected from server';
        indicatorColor = 'red.500';
    }

    if (!statusText) return null;

    return (
        <Box
            px={4}
            py={3}
            bg={statusBg}
            borderWidth="1px"
            borderColor={statusBorder}
            borderRadius="md"
            mb={4}
            width="full"
        >
            <HStack spacing={2} align="center">
                <Box
                    w={3}
                    h={3}
                    borderRadius="full"
                    bg={indicatorColor}
                    animation={isConnecting.value ? "pulse 1.5s infinite" : "none"}
                />
                <Text fontSize="sm" fontWeight="medium" color={statusTextColor}>
                    {statusText}
                </Text>
            </HStack>
        </Box>
    );
};

export default ConnectionStatus; 