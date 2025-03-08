import { useState } from 'react';
import {
  ChakraProvider,
  Box,
  Container,
  Grid,
  GridItem,
  VStack,
  Text,
  useColorModeValue,
} from '@chakra-ui/react';
import { Chat } from './components/Chat';
import InstructionsSection from './components/InstructionsSection';
import UserDevicesTable from './components/UserDevicesTable';
import CapabilitiesTable from './components/CapabilitiesTable';

function App() {
  const [customerId, setCustomerId] = useState<string>('');
  const [lastMessageTimestamp, setLastMessageTimestamp] = useState<number>(Date.now());
  const textColor = useColorModeValue('gray.600', 'gray.400');

  // This function will be passed to the Chat component to update the customer ID
  const handleCustomerChange = (newCustomerId: string) => {
    setCustomerId(newCustomerId);
  };

  // This function will be called when a message is sent
  const handleMessageSent = () => {
    setLastMessageTimestamp(Date.now());
  };

  return (
    <ChakraProvider>
      <Box bg="gray.50" minH="100vh" py="8">
        <Container maxW="container.xl">
          <Text fontSize="sm" color={textColor} mb={4} textAlign="center">
            For the best experience, please view this application on a desktop browser.
          </Text>
          <InstructionsSection />

          <Grid
            templateColumns={{ base: "1fr", lg: "1fr 400px" }}
            gap={6}
          >
            {/* Main Section */}
            <GridItem>
              <VStack spacing={4} align="stretch">
                <Chat onCustomerChange={handleCustomerChange} onMessageSent={handleMessageSent} />
                {customerId && (
                  <UserDevicesTable customerId={customerId} lastUpdate={lastMessageTimestamp} />
                )}
              </VStack>
            </GridItem>

            {/* Sidebar with Capabilities */}
            <GridItem>
              {customerId && (
                <CapabilitiesTable customerId={customerId} />
              )}
            </GridItem>
          </Grid>
        </Container>
      </Box>
    </ChakraProvider>
  );
}

export default App;
