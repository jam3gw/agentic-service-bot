# Deployment

## Overview

The Agentic Service Bot uses AWS CDK (Cloud Development Kit) for infrastructure as code, enabling consistent and repeatable deployments across environments. The deployment process is designed to be automated, secure, and maintainable.

## Environments

### Development Environment

- **Purpose**: Testing new features and changes
- **URL**: https://agentic-service-bot.dev.jake-moses.com
- **Characteristics**:
  - Reduced capacity and scaling
  - More permissive CORS settings
  - DynamoDB tables with DESTROY removal policy
  - Debug logging enabled
  - Shorter TTLs for resources

### Production Environment

- **Purpose**: Serving end users
- **URL**: https://agentic-service-bot.jake-moses.com
- **Characteristics**:
  - Full capacity and scaling
  - Strict CORS settings
  - DynamoDB tables with RETAIN removal policy
  - Production-level logging
  - Standard TTLs for resources

## Infrastructure Components

### Frontend

- **Hosting**: AWS S3 bucket with CloudFront distribution
- **Deployment**: Static files uploaded to S3
- **Configuration**: Environment-specific config.ts file

### Backend

- **API Gateway**: WebSocket API for real-time communication
- **Lambda Functions**: Python functions for request processing
- **DynamoDB**: Tables for data storage
- **IAM Roles**: Permissions for services

## Deployment Process

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. Node.js and npm installed
3. AWS CDK installed globally
4. Python 3.9 or higher installed

### Backend Deployment

1. **Install Dependencies**:
   ```bash
   cd infrastructure
   npm install
   ```

2. **Bootstrap CDK** (first time only):
   ```bash
   cdk bootstrap aws://ACCOUNT-NUMBER/REGION
   ```

3. **Deploy to Development**:
   ```bash
   cdk deploy --context environment=dev
   ```

4. **Deploy to Production**:
   ```bash
   cdk deploy --context environment=prod
   ```

### Frontend Deployment

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Build for Development**:
   ```bash
   REACT_APP_ENV=dev npm run build
   ```

3. **Build for Production**:
   ```bash
   REACT_APP_ENV=prod npm run build
   ```

4. **Deploy to S3**:
   ```bash
   aws s3 sync build/ s3://agentic-service-bot-ENVIRONMENT-frontend
   ```

5. **Invalidate CloudFront Cache**:
   ```bash
   aws cloudfront create-invalidation --distribution-id DISTRIBUTION_ID --paths "/*"
   ```

## CI/CD Pipeline

A CI/CD pipeline automates the deployment process using GitHub Actions:

### Workflow Stages

1. **Build**: Compile and build the application
2. **Test**: Run automated tests
3. **Deploy to Development**: On merge to develop branch
4. **Deploy to Production**: On merge to main branch

### Example GitHub Actions Workflow

```yaml
name: Deploy Agentic Service Bot

on:
  push:
    branches:
      - main
      - develop

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '16'

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          npm install -g aws-cdk
          cd infrastructure
          npm install
          cd ../frontend
          npm install

      - name: Determine environment
        id: env
        run: |
          if [ "${{ github.ref }}" = "refs/heads/main" ]; then
            echo "::set-output name=environment::prod"
          else
            echo "::set-output name=environment::dev"
          fi

      - name: Deploy infrastructure
        run: |
          cd infrastructure
          cdk deploy --context environment=${{ steps.env.outputs.environment }} --require-approval never
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: us-east-1

      - name: Build frontend
        run: |
          cd frontend
          REACT_APP_ENV=${{ steps.env.outputs.environment }} npm run build

      - name: Deploy frontend
        run: |
          aws s3 sync frontend/build/ s3://agentic-service-bot-${{ steps.env.outputs.environment }}-frontend
          aws cloudfront create-invalidation --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} --paths "/*"
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: us-east-1
```

## Rollback Strategy

In case of deployment issues:

1. **Infrastructure Rollback**:
   - Use CDK to deploy the previous version:
     ```bash
     cdk deploy --context environment=ENVIRONMENT --app "npx ts-node bin/app.ts@PREVIOUS_COMMIT"
     ```

2. **Frontend Rollback**:
   - Deploy the previous build from artifact storage:
     ```bash
     aws s3 sync s3://artifacts/agentic-service-bot/PREVIOUS_VERSION/ s3://agentic-service-bot-ENVIRONMENT-frontend
     aws cloudfront create-invalidation --distribution-id DISTRIBUTION_ID --paths "/*"
     ```

## Monitoring and Alerts

1. **CloudWatch Alarms**:
   - Lambda error rates
   - API Gateway 4xx/5xx errors
   - DynamoDB throttling events

2. **CloudWatch Dashboards**:
   - Request volume
   - Response times
   - Error rates by endpoint

3. **SNS Notifications**:
   - Alert on critical errors
   - Daily summary reports

## Security Considerations

1. **IAM Roles**:
   - Least privilege principle
   - Service-specific roles

2. **Secrets Management**:
   - API keys stored in AWS Secrets Manager
   - No hardcoded secrets in code

3. **Network Security**:
   - CloudFront with WAF for frontend
   - API Gateway authorization for backend

## Disaster Recovery

1. **Backup Strategy**:
   - DynamoDB point-in-time recovery enabled
   - S3 versioning for frontend assets

2. **Recovery Procedure**:
   - Restore DynamoDB tables from backup
   - Redeploy infrastructure if needed
   - Restore frontend from S3 versions

## Compliance and Auditing

1. **Deployment Logs**:
   - All deployments logged to CloudTrail
   - Change history maintained in Git

2. **Access Logs**:
   - S3 access logging
   - CloudFront access logging
   - API Gateway execution logging 