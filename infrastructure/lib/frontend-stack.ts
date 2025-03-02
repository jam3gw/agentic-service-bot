import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { Construct } from 'constructs';
import { BaseStack } from './base-stack';
import { EnvironmentConfig } from './config';
import * as path from 'path';

export class FrontendStack extends BaseStack {
    constructor(scope: Construct, id: string, config: EnvironmentConfig, props?: cdk.StackProps) {
        super(scope, id, config, props);

        // Create S3 bucket for website hosting
        const websiteBucket = new s3.Bucket(this, 'WebsiteBucket', {
            bucketName: `${config.subdomain}-website`,
            removalPolicy: config.environment === 'prod'
                ? cdk.RemovalPolicy.RETAIN
                : cdk.RemovalPolicy.DESTROY,
            autoDeleteObjects: config.environment !== 'prod',
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL
        });

        // Get reference to hosted zone
        const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
            domainName: config.hostedZoneName,
        });

        // Create certificate for CloudFront
        const certificate = new acm.DnsValidatedCertificate(this, 'Certificate', {
            domainName: config.domainName,
            hostedZone,
            region: 'us-east-1', // CloudFront requires certificates in us-east-1
        });

        // Create CloudFront distribution
        const distribution = new cloudfront.Distribution(this, 'Distribution', {
            defaultBehavior: {
                origin: new origins.S3Origin(websiteBucket),
                viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
            },
            domainNames: [config.domainName],
            certificate,
            defaultRootObject: 'index.html',
            errorResponses: [
                {
                    httpStatus: 404,
                    responseHttpStatus: 200,
                    responsePagePath: '/index.html'
                }
            ]
        });

        // Create DNS record
        new route53.ARecord(this, 'AliasRecord', {
            zone: hostedZone,
            target: route53.RecordTarget.fromAlias(
                new targets.CloudFrontTarget(distribution)
            ),
            recordName: config.subdomain,
        });

        // Deploy website contents
        new s3deploy.BucketDeployment(this, 'DeployWebsite', {
            sources: [s3deploy.Source.asset(path.join(__dirname, '../../frontend/dist'))],
            destinationBucket: websiteBucket,
            distribution,
            distributionPaths: ['/*'],
        });

        // Output the CloudFront URL
        new cdk.CfnOutput(this, 'DistributionUrl', {
            value: distribution.distributionDomainName,
            description: 'CloudFront Distribution URL',
        });

        // Output the website URL
        new cdk.CfnOutput(this, 'WebsiteUrl', {
            value: `https://${config.domainName}`,
            description: 'Website URL',
        });
    }
} 