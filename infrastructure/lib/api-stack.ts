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
import * as websocketapi from '@aws-cdk/aws-apigatewayv2-alpha';
import { WebSocketLambdaIntegration } from '@aws-cdk/aws-apigatewayv2-integrations-alpha';

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

        // Create DynamoDB table for WebSocket connections
        const connectionsTable = new dynamodb.Table(this, 'ConnectionsTable', {
            tableName: `${config.environment}-connections`,
            partitionKey: { name: 'connectionId', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            timeToLiveAttribute: 'ttl',
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
                CONNECTIONS_TABLE: connectionsTable.tableName,
                ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || 'your-api-key-here',
                ANTHROPIC_MODEL: 'claude-3-opus-20240229',
                ENVIRONMENT: config.environment,
                ALLOWED_ORIGIN: config.environment === 'prod'
                    ? 'https://agentic-service-bot.jake-moses.com'
                    : 'https://agentic-service-bot.dev.jake-moses.com',
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
        connectionsTable.grantReadWriteData(chatFunction);

        // Create WebSocket API
        const webSocketApi = new websocketapi.WebSocketApi(this, 'ChatWebSocketApi', {
            apiName: `${config.environment}-chat-websocket-api`,
            connectRouteOptions: {
                integration: new WebSocketLambdaIntegration('ConnectIntegration', chatFunction),
                returnResponse: true,
            },
            disconnectRouteOptions: {
                integration: new WebSocketLambdaIntegration('DisconnectIntegration', chatFunction),
                returnResponse: true,
            },
            defaultRouteOptions: {
                integration: new WebSocketLambdaIntegration('DefaultIntegration', chatFunction),
                returnResponse: true,
            },
        });

        // Add a route for message handling
        webSocketApi.addRoute('message', {
            integration: new WebSocketLambdaIntegration('MessageIntegration', chatFunction),
            returnResponse: true,
        });

        // Deploy the WebSocket API
        const webSocketStage = new websocketapi.WebSocketStage(this, 'ChatWebSocketStage', {
            webSocketApi,
            stageName: config.environment,
            autoDeploy: true,
        });

        // Grant permission for the Lambda to manage WebSocket connections
        chatFunction.addToRolePolicy(new iam.PolicyStatement({
            actions: ['execute-api:ManageConnections'],
            resources: [`arn:aws:execute-api:${this.region}:${this.account}:${webSocketApi.apiId}/${config.environment}/*`],
        }));

        // Output the WebSocket URL
        new cdk.CfnOutput(this, 'WebSocketURL', {
            value: webSocketStage.url,
            description: 'WebSocket API URL',
        });

        // Create a custom resource to seed the DynamoDB tables with initial data
        const seedFunction = new PythonFunction(this, 'SeedFunction', {
            functionName: `${config.environment}-seed-data`,
            runtime: lambda.Runtime.PYTHON_3_9,
            entry: path.join(__dirname, '../../lambda/seed'),
            index: 'app.py',
            handler: 'handler',
            timeout: cdk.Duration.minutes(5),
            environment: {
                CUSTOMERS_TABLE: customersTable.tableName,
                SERVICE_LEVELS_TABLE: serviceLevelsTable.tableName,
            },
            bundling: {
                assetExcludes: [
                    'venv',
                    '__pycache__'
                ]
            }
        });

        // Grant permissions to the seed function
        customersTable.grantReadWriteData(seedFunction);
        serviceLevelsTable.grantReadWriteData(seedFunction);

        // Create the custom resource
        const provider = new cdk.custom_resources.Provider(this, 'SeedProvider', {
            onEventHandler: seedFunction,
        });

        const seedResource = new cdk.CustomResource(this, 'SeedData', {
            serviceToken: provider.serviceToken,
        });

        // Output the API URL
        new cdk.CfnOutput(this, 'ApiUrl', {
            value: webSocketStage.url,
            description: 'WebSocket API URL',
        });
    }
} 