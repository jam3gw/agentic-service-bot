import React from 'react';
import { Box, Text, Flex, Avatar, useColorModeValue } from '@chakra-ui/react';
import { Message } from '../types';

interface MessageListProps {
    messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
    if (messages.length === 0) {
        return (
            <Flex
                justify="center"
                align="center"
                height="100%"
                color={useColorModeValue('gray.500', 'gray.400')}
            >
                <Text>No messages yet. Start a conversation!</Text>
            </Flex>
        );
    }

    return (
        <Box
            width="100%"
            display="flex"
            flexDirection="column"
            gap={2}
        >
            {messages.map((message) => (
                <MessageItem key={message.id} message={message} />
            ))}
        </Box>
    );
};

interface MessageItemProps {
    message: Message;
}

const MessageItem: React.FC<MessageItemProps> = React.memo(({ message }) => {
    const isBot = message.sender === 'bot';
    const bgColor = useColorModeValue(
        isBot ? 'blue.50' : 'gray.50',
        isBot ? 'blue.900' : 'gray.700'
    );
    const textColor = useColorModeValue('gray.800', 'white');

    return (
        <Flex
            direction={isBot ? 'row' : 'row-reverse'}
            align="start"
            maxW="100%"
            mb={2}
            flexShrink={0}
        >
            <Avatar
                size="sm"
                name={isBot ? 'Service Bot' : 'User'}
                bg={isBot ? 'blue.500' : 'gray.500'}
                mr={isBot ? 2 : 0}
                ml={isBot ? 0 : 2}
                flexShrink={0}
            />
            <Box
                bg={bgColor}
                color={textColor}
                px={4}
                py={2}
                borderRadius="lg"
                maxW="80%"
                position="relative"
                wordBreak="break-word"
            >
                <Text fontSize="md" whiteSpace="pre-wrap">
                    {message.text}
                </Text>
                <Text
                    fontSize="xs"
                    color="gray.500"
                    mt={1}
                    textAlign={isBot ? 'left' : 'right'}
                >
                    {new Date(message.timestamp).toLocaleTimeString()}
                </Text>
            </Box>
        </Flex>
    );
});

export default MessageList; 