import { useState } from 'react';
import { ChakraProvider, Box, Container, Grid, GridItem } from '@chakra-ui/react';
import { Chat } from './components/Chat';
import InstructionsSection from './components/InstructionsSection';
import UserDevicesTable from './components/UserDevicesTable';
import CapabilitiesTable from './components/CapabilitiesTable';

// Default customer ID
const DEFAULT_CUSTOMER_ID = 'cust_001';

function App() {
  const [customerId, setCustomerId] = useState(DEFAULT_CUSTOMER_ID);
  const [lastMessageTimestamp, setLastMessageTimestamp] = useState<number>(Date.now());

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
          <InstructionsSection />

          <Grid
            templateColumns={{ base: "1fr", lg: "1fr 400px" }}
            gap={6}
          >
            {/* Main Chat Section */}
            <GridItem>
              <Chat onCustomerChange={handleCustomerChange} onMessageSent={handleMessageSent} />
            </GridItem>

            {/* Sidebar with Devices and Capabilities */}
            <GridItem>
              <UserDevicesTable customerId={customerId} lastUpdate={lastMessageTimestamp} />
              <CapabilitiesTable customerId={customerId} />
            </GridItem>
          </Grid>
        </Container>
      </Box>
    </ChakraProvider>
  );
}

export default App;
