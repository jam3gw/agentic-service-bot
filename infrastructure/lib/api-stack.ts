import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { BaseStack } from './base-stack';
import { EnvironmentConfig } from './config';
import * as path from 'path';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

export class ApiStack extends BaseStack {
    constructor(scope: Construct, id: string, config: EnvironmentConfig, props?: cdk.StackProps) {
        super(scope, id, config, props);

        // Create DynamoDB table for messages
        const messagesTable = new dynamodb.Table(this, 'MessagesTable', {
            tableName: `${config.environment}-messages`,
            partitionKey: { name: 'conversationId', type: dynamodb.AttributeType.STRING },
            sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: config.environment === 'prod'
                ? cdk.RemovalPolicy.RETAIN
                : cdk.RemovalPolicy.DESTROY,
        });

        // Add GSI for userId
        messagesTable.addGlobalSecondaryIndex({
            indexName: 'UserIdIndex',
            partitionKey: { name: 'userId', type: dynamodb.AttributeType.STRING },
            sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
        });

        // Create DynamoDB table for customers
        const customersTable = new dynamodb.Table(this, 'CustomersTable', {
            tableName: `${config.environment}-customers`,
            partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: config.environment === 'prod'
                ? cdk.RemovalPolicy.RETAIN
                : cdk.RemovalPolicy.DESTROY,
        });

        // Create DynamoDB table for service levels
        const serviceLevelsTable = new dynamodb.Table(this, 'ServiceLevelsTable', {
            tableName: `${config.environment}-service-levels`,
            partitionKey: { name: 'level', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: config.environment === 'prod'
                ? cdk.RemovalPolicy.RETAIN
                : cdk.RemovalPolicy.DESTROY,
        });

        // Create Lambda function for handling chat messages
        const chatFunction = new PythonFunction(this, 'ChatFunction', {
            functionName: `${config.environment}-chat-handler`,
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'handler',
            entry: path.join(__dirname, '../../lambda/chat'),
            timeout: cdk.Duration.minutes(10),
            memorySize: 1024,
            environment: {
                MESSAGES_TABLE: messagesTable.tableName,
                CUSTOMERS_TABLE: customersTable.tableName,
                SERVICE_LEVELS_TABLE: serviceLevelsTable.tableName,
                ANTHROPIC_API_KEY: config.environment === 'prod'
                    ? process.env.PROD_ANTHROPIC_API_KEY!!
                    : process.env.ANTHROPIC_API_KEY!!,
                ANTHROPIC_MODEL: 'claude-3-haiku-20240307',
                ENVIRONMENT: config.environment,
                ALLOWED_ORIGIN: config.environment === 'prod'
                    ? 'https://agentic-service-bot.jake-moses.com,http://localhost:5173'
                    : 'https://agentic-service-bot.dev.jake-moses.com,http://localhost:5173', // Add localhost for development
            },
            bundling: {
                assetExcludes: [
                    'venv',
                    '__pycache__'
                ]
            }
        });

        // Create Lambda function for handling API requests
        const apiFunction = new PythonFunction(this, 'ApiFunction', {
            functionName: `${config.environment}-api-handler`,
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'handler',
            entry: path.join(__dirname, '../../lambda/api'),
            timeout: cdk.Duration.minutes(5),
            memorySize: 512,
            environment: {
                CUSTOMERS_TABLE: customersTable.tableName,
                SERVICE_LEVELS_TABLE: serviceLevelsTable.tableName,
                ENVIRONMENT: config.environment,
                ALLOWED_ORIGIN: config.environment === 'prod'
                    ? 'https://agentic-service-bot.jake-moses.com,http://localhost:5173'
                    : 'https://agentic-service-bot.dev.jake-moses.com,http://localhost:5173', // Add localhost for development
            },
            bundling: {
                assetExcludes: [
                    'venv',
                    '__pycache__'
                ]
            }
        });

        // Grant Lambda permissions to access DynamoDB tables
        messagesTable.grantReadWriteData(chatFunction);
        customersTable.grantReadWriteData(chatFunction);
        serviceLevelsTable.grantReadWriteData(chatFunction);

        // Grant API Lambda permissions to access DynamoDB tables
        customersTable.grantReadWriteData(apiFunction);
        serviceLevelsTable.grantReadData(apiFunction);
        messagesTable.grantReadData(apiFunction);

        // Grant CloudWatch PutMetricData permissions to Lambda functions
        const cloudWatchPolicy = new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: ['cloudwatch:PutMetricData'],
            resources: ['*'],
        });

        chatFunction.addToRolePolicy(cloudWatchPolicy);
        apiFunction.addToRolePolicy(cloudWatchPolicy);

        // Create REST API for device, capability, and chat endpoints
        const restApi = new apigateway.RestApi(this, 'ServiceBotApi', {
            restApiName: `${config.environment}-service-bot-api`,
            description: 'API for device, capability, and chat management',
            defaultCorsPreflightOptions: {
                allowOrigins: config.environment === 'prod'
                    ? ['https://agentic-service-bot.jake-moses.com', 'http://localhost:5173']
                    : ['https://agentic-service-bot.dev.jake-moses.com', 'http://localhost:5173'], // Add localhost for development
                allowMethods: ['GET', 'POST', 'PATCH', 'OPTIONS'],
                allowHeaders: ['Content-Type', 'Authorization'],
                allowCredentials: true,
            },
            deployOptions: {
                stageName: config.environment,
            },
        });

        // Create API resources and methods
        const apiResource = restApi.root.addResource('api');

        // Capabilities endpoint
        const capabilitiesResource = apiResource.addResource('capabilities');
        capabilitiesResource.addMethod('GET', new apigateway.LambdaIntegration(apiFunction));

        // Customers endpoint
        const customersResource = apiResource.addResource('customers');
        customersResource.addMethod('GET', new apigateway.LambdaIntegration(apiFunction));

        const customerIdResource = customersResource.addResource('{customerId}');
        customerIdResource.addMethod('GET', new apigateway.LambdaIntegration(apiFunction));

        // Devices endpoints
        const devicesResource = customerIdResource.addResource('devices');
        devicesResource.addMethod('GET', new apigateway.LambdaIntegration(apiFunction));

        // Device ID endpoint for updating device state
        const deviceIdResource = devicesResource.addResource('{deviceId}');
        deviceIdResource.addMethod('PATCH', new apigateway.LambdaIntegration(apiFunction));

        // Chat endpoints
        const chatResource = apiResource.addResource('chat');

        // POST /api/chat - Send a message
        chatResource.addMethod('POST', new apigateway.LambdaIntegration(chatFunction));

        // GET /api/chat/history/{customerId} - Get chat history
        const chatHistoryResource = chatResource.addResource('history');
        const chatHistoryCustomerResource = chatHistoryResource.addResource('{customerId}');
        chatHistoryCustomerResource.addMethod('GET', new apigateway.LambdaIntegration(chatFunction));

        // Output the API URL
        new cdk.CfnOutput(this, 'ApiUrl', {
            value: restApi.url,
            description: 'URL of the REST API',
            exportName: `${config.environment}-api-url`,
        });
    }
} 