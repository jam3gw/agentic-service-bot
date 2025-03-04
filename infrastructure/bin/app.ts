#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { FrontendStack } from '../lib/frontend-stack';
import { ApiStack } from '../lib/api-stack';
import { environments } from '../lib/config';

const app = new cdk.App();

// Create Dev API Stack
new ApiStack(app, 'AgenticServiceBotDevApi', environments.dev, {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-west-2'
    },
    description: 'Development API stack for Agentic Service Bot'
});

// Create Prod API Stack
new ApiStack(app, 'AgenticServiceBotProdApi', environments.prod, {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-west-2'
    },
    description: 'Production API stack for Agentic Service Bot'
});

// Create Dev Frontend Stack
new FrontendStack(app, 'AgenticServiceBotDevFrontend', environments.dev, {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-east-1'
    },
    description: 'Development frontend stack for Agentic Service Bot'
});

// Create Prod Frontend Stack
new FrontendStack(app, 'AgenticServiceBotProdFrontend', environments.prod, {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-east-1'
    },
    description: 'Production frontend stack for Agentic Service Bot'
}); 