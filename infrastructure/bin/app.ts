#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { FrontendStack } from '../lib/frontend-stack';
import { ApiStack } from '../lib/api-stack';
import { MonitoringStack } from '../lib/monitoring-stack';
import { environments } from '../lib/config';

const app = new cdk.App();

// Create Dev API Stack
const devApiStack = new ApiStack(app, 'AgenticServiceBotDevApi', environments.dev, {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-west-2'
    },
    description: 'Development API stack for Agentic Service Bot'
});

// Create Prod API Stack
const prodApiStack = new ApiStack(app, 'AgenticServiceBotProdApi', environments.prod, {
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

// Create Dev Monitoring Stack
new MonitoringStack(app, 'AgenticServiceBotDevMonitoring', environments.dev, {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-west-2'
    },
    description: 'Development monitoring stack for Agentic Service Bot',
    apiStackName: devApiStack.stackName,
    chatFunctionName: `${environments.dev.environment}-chat-handler`,
    apiFunctionName: `${environments.dev.environment}-api-handler`,
    messagesTableName: `${environments.dev.environment}-messages`,
    customersTableName: `${environments.dev.environment}-customers`,
    serviceLevelsTableName: `${environments.dev.environment}-service-levels`,
    apiGatewayName: `${environments.dev.environment}-service-bot-api`,
    alarmEmail: 'mosesjake32@gmail.com'
});

// Create Prod Monitoring Stack
new MonitoringStack(app, 'AgenticServiceBotProdMonitoring', environments.prod, {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-west-2'
    },
    description: 'Production monitoring stack for Agentic Service Bot',
    apiStackName: prodApiStack.stackName,
    chatFunctionName: `${environments.prod.environment}-chat-handler`,
    apiFunctionName: `${environments.prod.environment}-api-handler`,
    messagesTableName: `${environments.prod.environment}-messages`,
    customersTableName: `${environments.prod.environment}-customers`,
    serviceLevelsTableName: `${environments.prod.environment}-service-levels`,
    apiGatewayName: `${environments.prod.environment}-service-bot-api`,
    alarmEmail: 'mosesjake32@gmail.com'
}); 