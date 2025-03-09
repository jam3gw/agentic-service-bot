/**
 * Configuration for the Agentic Service Bot frontend.
 */

// API URLs
const DEV_API_URL = 'https://k4w64ym45e.execute-api.us-west-2.amazonaws.com/dev/api';
// const PROD_API_URL = 'https://api.agentic-service-bot.jake-moses.com/prod/api';

// Environment-specific configuration
const config = {
    // API URL based on environment
    apiUrl: DEV_API_URL,

    // Default customer ID
    defaultCustomerId: 'cust_001',

    // Polling interval for chat history (in milliseconds)
    chatPollingInterval: 5000,

    // Maximum number of messages to display
    maxMessages: 100,

    // Enable debug logging
    debug: true
};

export default config; 