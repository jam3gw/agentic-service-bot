import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { EnvironmentConfig } from './config';

export class BaseStack extends cdk.Stack {
    protected readonly config: EnvironmentConfig;

    constructor(scope: Construct, id: string, config: EnvironmentConfig, props?: cdk.StackProps) {
        super(scope, id, props);
        this.config = config;

        // Add tags to all resources in this stack
        cdk.Tags.of(this).add('Environment', config.environment);
        cdk.Tags.of(this).add('Project', 'agentic-service-bot');
        cdk.Tags.of(this).add('ManagedBy', 'CDK');
    }
} 