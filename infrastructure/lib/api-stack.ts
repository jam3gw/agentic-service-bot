import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { BaseStack } from './base-stack';
import { EnvironmentConfig } from './config';
import * as path from 'path';

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

        // Create Lambda function for handling chat messages
        const chatFunction = new lambda.Function(this, 'ChatFunction', {
            functionName: `${config.environment}-chat-handler`,
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'index.handler',
            code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/chat'), {
                exclude: [
                    '**/__pycache__/**',
                    '**/venv/**',
                    '**/.venv/**',
                    '**/.pytest_cache/**',
                    '**/.coverage',
                    '**/.mypy_cache/**'
                ]
            }),
            timeout: cdk.Duration.minutes(5),
            memorySize: 1024,
            environment: {
                MESSAGES_TABLE: messagesTable.tableName,
                ENVIRONMENT: config.environment,
            },
        });

        // Grant Lambda permissions to access DynamoDB
        messagesTable.grantReadWriteData(chatFunction);

        // Create REST API
        const api = new apigateway.RestApi(this, 'ChatApi', {
            restApiName: `${config.environment}-chat-api`,
            description: `Chat API for ${config.environment} environment`,
            defaultCorsPreflightOptions: {
                allowOrigins: apigateway.Cors.ALL_ORIGINS, // Allow all origins for now, can be restricted later
                allowMethods: ['GET', 'POST', 'OPTIONS'],
                allowHeaders: ['Content-Type', 'Authorization'],
                allowCredentials: true,
            },
        });

        // Create chat resource and method
        const chatResource = api.root.addResource('chat');
        chatResource.addMethod('POST', new apigateway.LambdaIntegration(chatFunction));

        // Output the API URL
        new cdk.CfnOutput(this, 'ApiUrl', {
            value: api.url,
            description: 'API URL',
        });
    }
} 