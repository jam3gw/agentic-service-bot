import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import { Construct } from 'constructs';
import { BaseStack } from './base-stack';
import { EnvironmentConfig } from './config';

export interface MonitoringStackProps extends cdk.StackProps {
    apiStackName: string;
    chatFunctionName: string;
    apiFunctionName: string;
    messagesTableName: string;
    customersTableName: string;
    serviceLevelsTableName: string;
    apiGatewayName: string;
    alarmEmail?: string;
}

export class MonitoringStack extends BaseStack {
    constructor(scope: Construct, id: string, config: EnvironmentConfig, props: MonitoringStackProps) {
        super(scope, id, config, props);

        // Create SNS topic for alarms
        const alarmTopic = new sns.Topic(this, 'AlarmTopic', {
            topicName: `${config.environment}-service-bot-alarms`,
            displayName: `${config.environment.charAt(0).toUpperCase() + config.environment.slice(1)} Service Bot Alarms`,
        });

        // Add email subscription
        alarmTopic.addSubscription(new subscriptions.EmailSubscription('mosesjake32@gmail.com'));

        // Create main dashboard
        const dashboard = new cloudwatch.Dashboard(this, 'ServiceBotDashboard', {
            dashboardName: `${config.environment}-service-bot-dashboard`,
        });

        // Create dedicated Anthropic API metrics dashboard
        const anthropicDashboard = new cloudwatch.Dashboard(this, 'AnthropicApiDashboard', {
            dashboardName: `${config.environment}-anthropic-api-dashboard`,
        });

        // Lambda metrics
        const chatFunctionMetrics = this.createLambdaMetricsWidget(
            props.chatFunctionName,
            'Chat Function'
        );

        const apiFunctionMetrics = this.createLambdaMetricsWidget(
            props.apiFunctionName,
            'API Function'
        );

        // API Gateway metrics
        const apiGatewayMetrics = this.createApiGatewayMetricsWidget(
            props.apiGatewayName,
            'service-bot-api'
        );

        // DynamoDB metrics
        const messagesTableMetrics = this.createDynamoDBMetricsWidget(
            props.messagesTableName,
            'Messages Table'
        );

        const customersTableMetrics = this.createDynamoDBMetricsWidget(
            props.customersTableName,
            'Customers Table'
        );

        const serviceLevelsTableMetrics = this.createDynamoDBMetricsWidget(
            props.serviceLevelsTableName,
            'Service Levels Table'
        );

        // Anthropic API metrics
        const anthropicApiMetrics = this.createAnthropicApiMetricsWidget();

        // Create detailed Anthropic API metrics widgets for the dedicated dashboard
        const anthropicApiCallsMetrics = this.createAnthropicApiCallsWidget();
        const anthropicApiLatencyMetrics = this.createAnthropicApiLatencyWidget();
        const anthropicApiTokensMetrics = this.createAnthropicApiTokensWidget();
        const anthropicApiByEndpointMetrics = this.createAnthropicApiByEndpointWidget();

        // Add widgets to main dashboard
        dashboard.addWidgets(
            // First row - most important metrics
            anthropicApiMetrics,

            // Second row - Lambda and API Gateway
            chatFunctionMetrics,
            apiFunctionMetrics,
            apiGatewayMetrics,

            // Third row - DynamoDB
            messagesTableMetrics,
            customersTableMetrics,
            serviceLevelsTableMetrics
        );

        // Add widgets to Anthropic API dashboard
        anthropicDashboard.addWidgets(
            // Header with summary metrics
            this.createMarkdownWidget('# Anthropic API Metrics Dashboard', 24),
            anthropicApiMetrics,

            // Detailed metrics
            anthropicApiCallsMetrics,
            anthropicApiLatencyMetrics,
            anthropicApiTokensMetrics,
            anthropicApiByEndpointMetrics
        );

        // Create alarms
        this.createLambdaAlarms(props.chatFunctionName, 'Chat Function', alarmTopic);
        this.createLambdaAlarms(props.apiFunctionName, 'API Function', alarmTopic);
        this.createApiGatewayAlarms(props.apiGatewayName, alarmTopic);
        this.createDynamoDBAlarms(props.messagesTableName, 'Messages Table', alarmTopic);
        this.createDynamoDBAlarms(props.customersTableName, 'Customers Table', alarmTopic);

        // Create Anthropic API alarms
        this.createAnthropicApiAlarms(alarmTopic);

        // Output dashboard URLs
        new cdk.CfnOutput(this, 'DashboardUrl', {
            value: `https://${this.region}.console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=${config.environment}-service-bot-dashboard`,
            description: 'URL of the main CloudWatch dashboard',
        });

        new cdk.CfnOutput(this, 'AnthropicDashboardUrl', {
            value: `https://${this.region}.console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=${config.environment}-anthropic-api-dashboard`,
            description: 'URL of the Anthropic API CloudWatch dashboard',
        });
    }

    private createLambdaMetricsWidget(
        functionName: string,
        label: string
    ): cloudwatch.GraphWidget {
        return new cloudwatch.GraphWidget({
            title: `${label} Metrics`,
            left: [
                new cloudwatch.Metric({
                    namespace: 'AWS/Lambda',
                    metricName: 'Invocations',
                    dimensionsMap: { FunctionName: functionName },
                    statistic: 'Sum',
                    label: 'Invocations',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/Lambda',
                    metricName: 'Errors',
                    dimensionsMap: { FunctionName: functionName },
                    statistic: 'Sum',
                    label: 'Errors',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            right: [
                new cloudwatch.Metric({
                    namespace: 'AWS/Lambda',
                    metricName: 'Duration',
                    dimensionsMap: { FunctionName: functionName },
                    statistic: 'Average',
                    label: 'Duration (avg)',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/Lambda',
                    metricName: 'Duration',
                    dimensionsMap: { FunctionName: functionName },
                    statistic: 'Maximum',
                    label: 'Duration (max)',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/Lambda',
                    metricName: 'Throttles',
                    dimensionsMap: { FunctionName: functionName },
                    statistic: 'Sum',
                    label: 'Throttles',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            width: 12,
            height: 6,
        });
    }

    private createApiGatewayMetricsWidget(
        apiName: string,
        apiId: string
    ): cloudwatch.GraphWidget {
        return new cloudwatch.GraphWidget({
            title: 'API Gateway Metrics',
            left: [
                new cloudwatch.Metric({
                    namespace: 'AWS/ApiGateway',
                    metricName: 'Count',
                    dimensionsMap: { ApiName: apiName, Stage: this.config.environment },
                    statistic: 'Sum',
                    label: 'Request Count',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/ApiGateway',
                    metricName: '4XXError',
                    dimensionsMap: { ApiName: apiName, Stage: this.config.environment },
                    statistic: 'Sum',
                    label: '4XX Errors',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/ApiGateway',
                    metricName: '5XXError',
                    dimensionsMap: { ApiName: apiName, Stage: this.config.environment },
                    statistic: 'Sum',
                    label: '5XX Errors',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            right: [
                new cloudwatch.Metric({
                    namespace: 'AWS/ApiGateway',
                    metricName: 'Latency',
                    dimensionsMap: { ApiName: apiName, Stage: this.config.environment },
                    statistic: 'Average',
                    label: 'Latency (avg)',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/ApiGateway',
                    metricName: 'Latency',
                    dimensionsMap: { ApiName: apiName, Stage: this.config.environment },
                    statistic: 'Maximum',
                    label: 'Latency (max)',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/ApiGateway',
                    metricName: 'IntegrationLatency',
                    dimensionsMap: { ApiName: apiName, Stage: this.config.environment },
                    statistic: 'Average',
                    label: 'Integration Latency (avg)',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            width: 12,
            height: 6,
        });
    }

    private createDynamoDBMetricsWidget(
        tableName: string,
        label: string
    ): cloudwatch.GraphWidget {
        return new cloudwatch.GraphWidget({
            title: `${label} Metrics`,
            left: [
                new cloudwatch.Metric({
                    namespace: 'AWS/DynamoDB',
                    metricName: 'ConsumedReadCapacityUnits',
                    dimensionsMap: { TableName: tableName },
                    statistic: 'Sum',
                    label: 'Read Capacity Units',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/DynamoDB',
                    metricName: 'ConsumedWriteCapacityUnits',
                    dimensionsMap: { TableName: tableName },
                    statistic: 'Sum',
                    label: 'Write Capacity Units',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            right: [
                new cloudwatch.Metric({
                    namespace: 'AWS/DynamoDB',
                    metricName: 'SuccessfulRequestLatency',
                    dimensionsMap: { TableName: tableName, Operation: 'GetItem' },
                    statistic: 'Average',
                    label: 'GetItem Latency (avg)',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/DynamoDB',
                    metricName: 'SuccessfulRequestLatency',
                    dimensionsMap: { TableName: tableName, Operation: 'PutItem' },
                    statistic: 'Average',
                    label: 'PutItem Latency (avg)',
                    period: cdk.Duration.minutes(1),
                }),
                new cloudwatch.Metric({
                    namespace: 'AWS/DynamoDB',
                    metricName: 'SuccessfulRequestLatency',
                    dimensionsMap: { TableName: tableName, Operation: 'Query' },
                    statistic: 'Average',
                    label: 'Query Latency (avg)',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            width: 12,
            height: 6,
        });
    }

    private createLambdaAlarms(
        functionName: string,
        label: string,
        alarmTopic: sns.ITopic
    ): void {
        // Error rate alarm
        const errorAlarm = new cloudwatch.Alarm(this, `${label}ErrorAlarm`, {
            alarmName: `${this.config.environment}-${label}-ErrorRate`,
            alarmDescription: `${label} error rate exceeds threshold`,
            metric: new cloudwatch.Metric({
                namespace: 'AWS/Lambda',
                metricName: 'Errors',
                dimensionsMap: { FunctionName: functionName },
                statistic: 'Sum',
                period: cdk.Duration.minutes(1),
            }),
            threshold: 5,
            evaluationPeriods: 5,
            datapointsToAlarm: 3,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        errorAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));

        // Duration alarm
        const durationAlarm = new cloudwatch.Alarm(this, `${label}DurationAlarm`, {
            alarmName: `${this.config.environment}-${label}-Duration`,
            alarmDescription: `${label} duration exceeds threshold`,
            metric: new cloudwatch.Metric({
                namespace: 'AWS/Lambda',
                metricName: 'Duration',
                dimensionsMap: { FunctionName: functionName },
                statistic: 'Average',
                period: cdk.Duration.minutes(1),
            }),
            threshold: 5000, // 5 seconds
            evaluationPeriods: 5,
            datapointsToAlarm: 3,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        durationAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));

        // Throttles alarm
        const throttlesAlarm = new cloudwatch.Alarm(this, `${label}ThrottlesAlarm`, {
            alarmName: `${this.config.environment}-${label}-Throttles`,
            alarmDescription: `${label} throttles exceeds threshold`,
            metric: new cloudwatch.Metric({
                namespace: 'AWS/Lambda',
                metricName: 'Throttles',
                dimensionsMap: { FunctionName: functionName },
                statistic: 'Sum',
                period: cdk.Duration.minutes(1),
            }),
            threshold: 5,
            evaluationPeriods: 5,
            datapointsToAlarm: 3,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        throttlesAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));
    }

    private createApiGatewayAlarms(
        apiName: string,
        alarmTopic: sns.ITopic
    ): void {
        // 4XX error alarm
        const error4xxAlarm = new cloudwatch.Alarm(this, 'ApiGateway4xxErrorAlarm', {
            alarmName: `${this.config.environment}-ApiGateway-4xxError`,
            alarmDescription: 'API Gateway 4XX error rate exceeds threshold',
            metric: new cloudwatch.Metric({
                namespace: 'AWS/ApiGateway',
                metricName: '4XXError',
                dimensionsMap: { ApiName: apiName, Stage: this.config.environment },
                statistic: 'Sum',
                period: cdk.Duration.minutes(1),
            }),
            threshold: 10,
            evaluationPeriods: 5,
            datapointsToAlarm: 3,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        error4xxAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));

        // 5XX error alarm
        const error5xxAlarm = new cloudwatch.Alarm(this, 'ApiGateway5xxErrorAlarm', {
            alarmName: `${this.config.environment}-ApiGateway-5xxError`,
            alarmDescription: 'API Gateway 5XX error rate exceeds threshold',
            metric: new cloudwatch.Metric({
                namespace: 'AWS/ApiGateway',
                metricName: '5XXError',
                dimensionsMap: { ApiName: apiName, Stage: this.config.environment },
                statistic: 'Sum',
                period: cdk.Duration.minutes(1),
            }),
            threshold: 5,
            evaluationPeriods: 5,
            datapointsToAlarm: 3,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        error5xxAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));

        // Latency alarm
        const latencyAlarm = new cloudwatch.Alarm(this, 'ApiGatewayLatencyAlarm', {
            alarmName: `${this.config.environment}-ApiGateway-Latency`,
            alarmDescription: 'API Gateway latency exceeds threshold',
            metric: new cloudwatch.Metric({
                namespace: 'AWS/ApiGateway',
                metricName: 'Latency',
                dimensionsMap: { ApiName: apiName, Stage: this.config.environment },
                statistic: 'Average',
                period: cdk.Duration.minutes(1),
            }),
            threshold: 5000, // 5 seconds
            evaluationPeriods: 5,
            datapointsToAlarm: 3,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        latencyAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));
    }

    private createDynamoDBAlarms(
        tableName: string,
        label: string,
        alarmTopic: sns.ITopic
    ): void {
        // Read throttle alarm
        const readThrottleAlarm = new cloudwatch.Alarm(this, `${label}ReadThrottleAlarm`, {
            alarmName: `${this.config.environment}-${label}-ReadThrottle`,
            alarmDescription: `${label} read throttle events exceed threshold`,
            metric: new cloudwatch.Metric({
                namespace: 'AWS/DynamoDB',
                metricName: 'ReadThrottleEvents',
                dimensionsMap: { TableName: tableName },
                statistic: 'Sum',
                period: cdk.Duration.minutes(1),
            }),
            threshold: 5,
            evaluationPeriods: 5,
            datapointsToAlarm: 3,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        readThrottleAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));

        // Write throttle alarm
        const writeThrottleAlarm = new cloudwatch.Alarm(this, `${label}WriteThrottleAlarm`, {
            alarmName: `${this.config.environment}-${label}-WriteThrottle`,
            alarmDescription: `${label} write throttle events exceed threshold`,
            metric: new cloudwatch.Metric({
                namespace: 'AWS/DynamoDB',
                metricName: 'WriteThrottleEvents',
                dimensionsMap: { TableName: tableName },
                statistic: 'Sum',
                period: cdk.Duration.minutes(1),
            }),
            threshold: 5,
            evaluationPeriods: 5,
            datapointsToAlarm: 3,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        writeThrottleAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));
    }

    private createAnthropicApiMetricsWidget(): cloudwatch.GraphWidget {
        return new cloudwatch.GraphWidget({
            title: 'Anthropic API Metrics',
            left: [
                // Total API calls (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiCalls',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'Sum',
                    label: 'Total API Calls',
                    period: cdk.Duration.minutes(1),
                }),
                // Successful API calls
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiCalls',
                    dimensionsMap: {
                        Environment: this.config.environment,
                        Success: 'true'
                    },
                    statistic: 'Sum',
                    label: 'Successful API Calls',
                    period: cdk.Duration.minutes(1),
                }),
                // Failed API calls
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiCalls',
                    dimensionsMap: {
                        Environment: this.config.environment,
                        Success: 'false'
                    },
                    statistic: 'Sum',
                    label: 'Failed API Calls',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            right: [
                // Average latency (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiLatency',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'Average',
                    label: 'Latency (avg)',
                    period: cdk.Duration.minutes(1),
                }),
                // Maximum latency (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiLatency',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'Maximum',
                    label: 'Latency (max)',
                    period: cdk.Duration.minutes(1),
                }),
                // Total tokens (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiTokens',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'Sum',
                    label: 'Tokens Used',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            width: 24,
            height: 6,
        });
    }

    private createAnthropicApiCallsWidget(): cloudwatch.GraphWidget {
        return new cloudwatch.GraphWidget({
            title: 'Anthropic API Calls',
            left: [
                // Total API calls (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiCalls',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'Sum',
                    label: 'Total API Calls',
                    period: cdk.Duration.minutes(1),
                }),
                // Successful API calls (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiCalls',
                    dimensionsMap: {
                        Environment: this.config.environment,
                        Success: 'true'
                    },
                    statistic: 'Sum',
                    label: 'Successful API Calls',
                    period: cdk.Duration.minutes(1),
                }),
                // Failed API calls (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiCalls',
                    dimensionsMap: {
                        Environment: this.config.environment,
                        Success: 'false'
                    },
                    statistic: 'Sum',
                    label: 'Failed API Calls',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            width: 12,
            height: 6,
            period: cdk.Duration.minutes(5),
            statistic: 'Sum',
            stacked: true,
        });
    }

    private createAnthropicApiLatencyWidget(): cloudwatch.GraphWidget {
        return new cloudwatch.GraphWidget({
            title: 'Anthropic API Latency',
            left: [
                // Average latency (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiLatency',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'Average',
                    label: 'Average Latency',
                    period: cdk.Duration.minutes(1),
                }),
                // p90 latency (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiLatency',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'p90',
                    label: 'p90 Latency',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            right: [
                // Maximum latency (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiLatency',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'Maximum',
                    label: 'Maximum Latency',
                    period: cdk.Duration.minutes(1),
                }),
                // Minimum latency (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiLatency',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'Minimum',
                    label: 'Minimum Latency',
                    period: cdk.Duration.minutes(1),
                }),
            ],
            width: 12,
            height: 6,
        });
    }

    private createAnthropicApiTokensWidget(): cloudwatch.GraphWidget {
        return new cloudwatch.GraphWidget({
            title: 'Anthropic API Token Usage',
            left: [
                // Total tokens (aggregated across all API names)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiTokens',
                    dimensionsMap: { Environment: this.config.environment },
                    statistic: 'Sum',
                    label: 'Total Tokens',
                    period: cdk.Duration.minutes(5),
                }),
            ],
            right: [
                // Hourly token usage (aggregated across all API names)
                new cloudwatch.MathExpression({
                    expression: 'FILL(m1,0)',
                    usingMetrics: {
                        m1: new cloudwatch.Metric({
                            namespace: 'ServiceBot',
                            metricName: 'AnthropicApiTokens',
                            dimensionsMap: { Environment: this.config.environment },
                            statistic: 'Sum',
                            period: cdk.Duration.hours(1),
                        }),
                    },
                    label: 'Hourly Token Usage',
                    period: cdk.Duration.hours(1),
                }),
            ],
            width: 12,
            height: 6,
        });
    }

    private createAnthropicApiByEndpointWidget(): cloudwatch.GraphWidget {
        return new cloudwatch.GraphWidget({
            title: 'Anthropic API Calls by Endpoint',
            left: [
                // API calls by specific endpoints (using ApiName dimension)
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiCalls',
                    dimensionsMap: {
                        Environment: this.config.environment,
                        ApiName: 'messages.create.stage1',
                        Success: 'true'
                    },
                    statistic: 'Sum',
                    label: 'Stage 1 Analysis',
                    period: cdk.Duration.minutes(5),
                }),
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiCalls',
                    dimensionsMap: {
                        Environment: this.config.environment,
                        ApiName: 'messages.create.stage2',
                        Success: 'true'
                    },
                    statistic: 'Sum',
                    label: 'Stage 2 Analysis',
                    period: cdk.Duration.minutes(5),
                }),
                new cloudwatch.Metric({
                    namespace: 'ServiceBot',
                    metricName: 'AnthropicApiCalls',
                    dimensionsMap: {
                        Environment: this.config.environment,
                        ApiName: 'messages.create.response',
                        Success: 'true'
                    },
                    statistic: 'Sum',
                    label: 'Response Generation',
                    period: cdk.Duration.minutes(5),
                }),
            ],
            width: 24,
            height: 6,
            stacked: true,
        });
    }

    private createMarkdownWidget(markdown: string, width: number): cloudwatch.TextWidget {
        return new cloudwatch.TextWidget({
            markdown,
            width,
            height: 1,
        });
    }

    private createAnthropicApiAlarms(alarmTopic: sns.ITopic): void {
        // Latency alarm
        const latencyAlarm = new cloudwatch.Alarm(this, 'AnthropicApiLatencyAlarm', {
            alarmName: `${this.config.environment}-AnthropicApi-Latency`,
            alarmDescription: 'Anthropic API latency exceeds threshold',
            metric: new cloudwatch.Metric({
                namespace: 'ServiceBot',
                metricName: 'AnthropicApiLatency',
                dimensionsMap: { Environment: this.config.environment },
                statistic: 'Average',
                period: cdk.Duration.minutes(1),
            }),
            threshold: 5000, // 5 seconds
            evaluationPeriods: 3,
            datapointsToAlarm: 2,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        latencyAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));

        // Error rate alarm
        const errorRateAlarm = new cloudwatch.Alarm(this, 'AnthropicApiErrorRateAlarm', {
            alarmName: `${this.config.environment}-AnthropicApi-ErrorRate`,
            alarmDescription: 'Anthropic API error rate exceeds threshold',
            metric: new cloudwatch.MathExpression({
                expression: 'errors / total * 100',
                usingMetrics: {
                    errors: new cloudwatch.Metric({
                        namespace: 'ServiceBot',
                        metricName: 'AnthropicApiCalls',
                        dimensionsMap: {
                            Environment: this.config.environment,
                            Success: 'false'
                        },
                        statistic: 'Sum',
                        period: cdk.Duration.minutes(5),
                    }),
                    total: new cloudwatch.Metric({
                        namespace: 'ServiceBot',
                        metricName: 'AnthropicApiCalls',
                        dimensionsMap: { Environment: this.config.environment },
                        statistic: 'Sum',
                        period: cdk.Duration.minutes(5),
                    }),
                },
                label: 'Error Rate (%)',
            }),
            threshold: 10, // 10% error rate
            evaluationPeriods: 3,
            datapointsToAlarm: 2,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        errorRateAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));

        // Token usage alarm (for cost control)
        const tokenUsageAlarm = new cloudwatch.Alarm(this, 'AnthropicApiTokenUsageAlarm', {
            alarmName: `${this.config.environment}-AnthropicApi-TokenUsage`,
            alarmDescription: 'Anthropic API token usage exceeds threshold',
            metric: new cloudwatch.Metric({
                namespace: 'ServiceBot',
                metricName: 'AnthropicApiTokens',
                dimensionsMap: { Environment: this.config.environment },
                statistic: 'Sum',
                period: cdk.Duration.hours(1),
            }),
            threshold: 1000000, // 1 million tokens per hour
            evaluationPeriods: 1,
            datapointsToAlarm: 1,
            comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        });
        tokenUsageAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));
    }
} 