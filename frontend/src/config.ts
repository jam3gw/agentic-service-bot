// Configuration for different environments
interface Config {
    apiUrl: string;
}

// Hardcoded API URL - replace this with your actual API Gateway URL after deployment
const config: Config = {
    // For development, use a placeholder URL
    // After deploying the API stack, replace this with the actual API Gateway URL
    // Dev
    apiUrl: 'https://xi2dz3sln6.execute-api.us-west-2.amazonaws.com/prod/',
};

export default config; 