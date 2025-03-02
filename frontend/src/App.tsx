import { ChakraProvider, Box } from '@chakra-ui/react'
import { Chat } from './components/Chat'

function App() {
  return (
    <ChakraProvider>
      <Box bg="gray.50" minH="100vh" py="8">
        <Chat />
      </Box>
    </ChakraProvider>
  )
}

export default App
