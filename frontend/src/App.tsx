import { useState } from 'react';
import { ChakraProvider, Box, Container, Tabs, TabList, TabPanels, Tab, TabPanel } from '@chakra-ui/react';
import { Chat } from './components/Chat';
import InstructionsSection from './components/InstructionsSection';
import UserDevicesTable from './components/UserDevicesTable';
import CapabilitiesTable from './components/CapabilitiesTable';

// Default customer ID
const DEFAULT_CUSTOMER_ID = 'cust_001';

function App() {
  const [customerId, setCustomerId] = useState(DEFAULT_CUSTOMER_ID);

  // This function will be passed to the Chat component to update the customer ID
  const handleCustomerChange = (newCustomerId: string) => {
    setCustomerId(newCustomerId);
  };

  return (
    <ChakraProvider>
      <Box bg="gray.50" minH="100vh" py="8">
        <Container maxW="container.xl">
          <InstructionsSection />

          <Tabs variant="enclosed" colorScheme="blue" mb={6}>
            <TabList>
              <Tab>Chat</Tab>
              <Tab>My Devices</Tab>
              <Tab>Capabilities</Tab>
            </TabList>

            <TabPanels>
              <TabPanel p={0} pt={5}>
                <Chat onCustomerChange={handleCustomerChange} />
              </TabPanel>

              <TabPanel p={0} pt={5}>
                <UserDevicesTable customerId={customerId} />
              </TabPanel>

              <TabPanel p={0} pt={5}>
                <CapabilitiesTable customerId={customerId} />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Container>
      </Box>
    </ChakraProvider>
  );
}

export default App;
