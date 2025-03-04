import React from 'react';
import { Box, Text, Flex, Avatar, VStack, useColorModeValue } from '@chakra-ui/react';
import { Message } from '../types';

interface MessageItemProps {
    message: Message;
}

const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
    const isUser = message.sender === 'user';

    // Theme colors
    const userBubbleBg = useColorModeValue('blue.500', 'blue.400');
    const userTextColor = useColorModeValue('white', 'white');
    const botBubbleBg = useColorModeValue('white', 'gray.700');
    const botTextColor = useColorModeValue('gray.800', 'gray.100');
    const botBubbleBorder = useColorModeValue('gray.200', 'gray.600');
    const timestampColor = useColorModeValue('gray.500', 'gray.400');

    // Format timestamp
    const formatTime = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Status indicator component
    const StatusIndicator = () => {
        if (!message.status || message.status === 'delivered') return null;

        let statusText = '';
        let statusColor = '';

        switch (message.status) {
            case 'sending':
                statusText = 'Sending...';
                statusColor = 'gray.400';
                break;
            case 'sent':
                statusText = 'Sent';
                statusColor = 'green.500';
                break;
            case 'queued':
                statusText = 'Queued';
                statusColor = 'yellow.500';
                break;
            case 'error':
                statusText = 'Failed to send';
                statusColor = 'red.500';
                break;
        }

        return (
            <Text fontSize="xs" color={statusColor} mt={1}>
                {statusText}
            </Text>
        );
    };

    return (
        <Flex
            justify={isUser ? 'flex-end' : 'flex-start'}
            mb={4}
            align="flex-start"
        >
            {!isUser && (
                <Avatar
                    size="xs"
                    bg="blue.500"
                    name="Smart Home"
                    src="/logo.png"
                    mr={2}
                    mt={1}
                    fallback={<Text fontSize="xs">🏠</Text>}
                />
            )}

            <VStack
                maxW="75%"
                align={isUser ? 'flex-end' : 'flex-start'}
                spacing={0}
            >
                <Box
                    px={4}
                    py={2}
                    borderRadius="lg"
                    bg={isUser ? userBubbleBg : botBubbleBg}
                    color={isUser ? userTextColor : botTextColor}
                    borderWidth={isUser ? 0 : '1px'}
                    borderColor={botBubbleBorder}
                    boxShadow="sm"
                    whiteSpace="pre-wrap"
                >
                    {message.text}
                </Box>

                <Flex
                    w="full"
                    justify={isUser ? 'flex-end' : 'flex-start'}
                    align="center"
                    mt={1}
                >
                    <Text fontSize="xs" color={timestampColor} mr={2}>
                        {formatTime(message.timestamp)}
                    </Text>
                    {isUser && <StatusIndicator />}
                </Flex>
            </VStack>

            {isUser && (
                <Avatar
                    size="xs"
                    bg="gray.400"
                    name="User"
                    ml={2}
                    mt={1}
                />
            )}
        </Flex>
    );
};

interface MessageListProps {
    messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
    return (
        <VStack spacing={4} align="stretch">
            {messages.map((message) => (
                <MessageItem key={message.id} message={message} />
            ))}
        </VStack>
    );
};

export default MessageList; 