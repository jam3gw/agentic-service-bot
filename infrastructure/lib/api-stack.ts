import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
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
            timeout: cdk.Duration.minutes(5),
            memorySize: 1024,
            environment: {
                MESSAGES_TABLE: messagesTable.tableName,
                CUSTOMERS_TABLE: customersTable.tableName,
                SERVICE_LEVELS_TABLE: serviceLevelsTable.tableName,
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

        // Create REST API
        const api = new apigateway.RestApi(this, 'ChatApi', {
            restApiName: `${config.environment}-chat-api`,
            description: `Chat API for ${config.environment} environment`,
            defaultCorsPreflightOptions: {
                allowOrigins: [
                    `https://agentic-service-bot.dev.jake-moses.com`,
                    `https://agentic-service-bot.jake-moses.com`,
                    'http://localhost:3000',
                    'http://localhost:5173'
                ],
                allowMethods: ['GET', 'POST', 'OPTIONS'],
                allowHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
                allowCredentials: true,
                maxAge: cdk.Duration.seconds(300)
            },
        });

        // Create chat resource and method
        const chatResource = api.root.addResource('chat');
        chatResource.addMethod('POST', new apigateway.LambdaIntegration(chatFunction, {
            integrationResponses: [{
                statusCode: '200',
                responseParameters: {
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization'",
                },
            }],
        }), {
            methodResponses: [{
                statusCode: '200',
                responseParameters: {
                    'method.response.header.Access-Control-Allow-Origin': true,
                    'method.response.header.Access-Control-Allow-Methods': true,
                    'method.response.header.Access-Control-Allow-Headers': true,
                },
            }],
        });

        // Create a custom resource to seed the DynamoDB tables with initial data
        const seedFunction = new lambda.Function(this, 'SeedFunction', {
            functionName: `${config.environment}-seed-data`,
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'index.handler',
            code: lambda.Code.fromInline(`
import boto3
import cfnresponse
import os

def handler(event, context):
    try:
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            # Initialize DynamoDB client
            dynamodb = boto3.resource('dynamodb')
            
            # Seed customers table
            customers_table = dynamodb.Table(os.environ['CUSTOMERS_TABLE'])
            customers = [
                {
                    "id": "cust_001",
                    "name": "Jane Smith",
                    "service_level": "basic",
                    "devices": [
                        {
                            "id": "dev_001",
                            "type": "SmartSpeaker",
                            "location": "living_room"
                        }
                    ]
                },
                {
                    "id": "cust_002",
                    "name": "John Doe",
                    "service_level": "premium",
                    "devices": [
                        {
                            "id": "dev_002",
                            "type": "SmartSpeaker",
                            "location": "bedroom"
                        },
                        {
                            "id": "dev_003",
                            "type": "SmartDisplay",
                            "location": "kitchen"
                        }
                    ]
                },
                {
                    "id": "cust_003",
                    "name": "Alice Johnson",
                    "service_level": "enterprise",
                    "devices": [
                        {
                            "id": "dev_004",
                            "type": "SmartSpeaker",
                            "location": "office"
                        },
                        {
                            "id": "dev_005",
                            "type": "SmartDisplay",
                            "location": "conference_room"
                        },
                        {
                            "id": "dev_006",
                            "type": "SmartHub",
                            "location": "reception"
                        }
                    ]
                }
            ]
            
            for customer in customers:
                customers_table.put_item(Item=customer)
            
            # Seed service levels table
            service_levels_table = dynamodb.Table(os.environ['SERVICE_LEVELS_TABLE'])
            service_levels = [
                {
                    "level": "basic",
                    "allowed_actions": [
                        "status_check",
                        "volume_control",
                        "device_info"
                    ],
                    "max_devices": 1,
                    "support_priority": "standard"
                },
                {
                    "level": "premium",
                    "allowed_actions": [
                        "status_check",
                        "volume_control",
                        "device_info",
                        "device_relocation",
                        "music_services"
                    ],
                    "max_devices": 3,
                    "support_priority": "priority"
                },
                {
                    "level": "enterprise",
                    "allowed_actions": [
                        "status_check",
                        "volume_control",
                        "device_info",
                        "device_relocation",
                        "music_services",
                        "multi_room_audio",
                        "custom_actions"
                    ],
                    "max_devices": 10,
                    "support_priority": "dedicated"
                }
            ]
            
            for service_level in service_levels:
                service_levels_table.put_item(Item=service_level)
                
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {})
            `),
            timeout: cdk.Duration.minutes(5),
            environment: {
                CUSTOMERS_TABLE: customersTable.tableName,
                SERVICE_LEVELS_TABLE: serviceLevelsTable.tableName,
            },
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
            value: api.url,
            description: 'API URL',
        });
    }
} 