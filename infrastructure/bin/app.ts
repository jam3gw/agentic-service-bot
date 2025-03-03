#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { FrontendStack } from '../lib/frontend-stack';
import { environments } from '../lib/config';

const app = new cdk.App();

// Create Dev Stack
new FrontendStack(app, 'AgenticServiceBotDevFrontend', environments.dev, {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-east-1'
    },
    description: 'Development frontend stack for Agentic Service Bot'
});

// Create Prod Stack
new FrontendStack(app, 'AgenticServiceBotProdFrontend', environments.prod, {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-east-1'
    },
    description: 'Production frontend stack for Agentic Service Bot'
}); 