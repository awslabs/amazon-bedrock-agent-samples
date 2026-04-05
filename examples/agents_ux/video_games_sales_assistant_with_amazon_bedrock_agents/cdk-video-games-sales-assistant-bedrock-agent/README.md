# Generative AI Application - Data Source and Amazon Bedrock Agent Deployment with AWS CDK

This tutorial guides you through setting up the back-end infrastructure and **[Amazon Bedrock Agent](https://aws.amazon.com/bedrock/agents/)** to create a Data Analyst Assistant for Video Game Sales using **[AWS Cloud Development Kit (CDK)](https://docs.aws.amazon.com/cdk/v2/guide/home.html)** with TypeScript.

> [!NOTE]
> **Working Directory**: Make sure you are in the `cdk-video-games-sales-assistant-bedrock-agent/` folder before starting this tutorial. All commands in this guide should be executed from this directory.

## Overview

You will deploy the following AWS services:

- **Amazon Bedrock Agent**: Powers the ***Data Analyst Assistant*** that answers questions by generating SQL queries using Claude Haiku 4.5
- **AWS Lambda**: Processes agent requests through various tools including:
    - /runSQLQuery: Executes queries against the database via the RDS Data API
    - /getCurrentDate: Retrieves the current date
    - /getTablesInformation: Provides database tables information for agent context
- **Aurora Serverless v2 PostgreSQL**: Stores the video game sales data (with RDS Data API enabled)
- **Amazon DynamoDB**: Tracks questions and query results
- **AWS Secrets Manager**: Securely stores database credentials (admin and read-only user)
- **Amazon VPC**: Provides network isolation for the database

> [!NOTE]
> This CDK project uses the **RDS Data API** for database access. The Lambda function communicates with Aurora via the AWS API (using `boto3` `rds-data` client) rather than a direct database connection. This eliminates the need for VPC placement of the Lambda function and simplifies networking.

By completing this tutorial, you'll have a fully functional Amazon Bedrock Agent for testing in the AWS Console.

> [!IMPORTANT]
> This sample application is meant for demo purposes and is not production ready. Please make sure to validate the code with your organizations security best practices.
>
> Remember to clean up resources after testing to avoid unnecessary costs by following the clean-up steps provided.

## Prerequisites

Before you begin, ensure you have:

* [AWS CDK CLI Installed](https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html) (v2.222.0 or later)
* [Node.js](https://nodejs.org/) (v18 or later)
* [TypeScript](https://www.typescriptlang.org/) (v5 or later)
* [Python 3.9 or later](https://www.python.org/downloads/)
* [Boto3 1.36 or later](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html)
* Anthropic Claude Haiku 4.5 model enabled in Amazon Bedrock
* Run this command to create a service-linked role for RDS:

```bash
aws iam create-service-linked-role --aws-service-name rds.amazonaws.com
```

> [!NOTE]
> If the role already exists, you will see the message: `Service role name AWSServiceRoleForRDS has been taken in this account`. This is expected and you can proceed with the deployment.

## Deploy the Back-End Services with AWS CDK

Install the required npm dependencies:

```bash
npm install
```

Bootstrap your AWS environment (if you haven't already):

```bash
cdk bootstrap
```

Synthesize the CloudFormation template to verify the stack:

```bash
cdk synth
```

Deploy the CDK stack:

```bash
cdk deploy
```

The default values are:
- **PostgreSQLDatabaseName**: `video_games_sales`
- **PostgreSQLTableName**: `video_games_sales_units`
- **AuroraMaxCapacity**: `2`
- **AuroraMinCapacity**: `1`

After deployment completes, the following services will be created:

- Amazon Bedrock Agent configured as a Data Analyst Assistant
- Lambda Function API for the agent (using RDS Data API for database access)
- Aurora Serverless v2 PostgreSQL Cluster with RDS Data API enabled
- A DynamoDB Table for tracking questions and query details
- S3 Bucket for data source storage

> [!TIP]
> You can also change the data source to connect to your preferred database engine by adapting both the Agent's instructions and the AWS Lambda API function logic.

> [!IMPORTANT] 
> Enhance AI safety and compliance by implementing **[Amazon Bedrock Guardrails](https://aws.amazon.com/bedrock/guardrails/)** for your AI applications.

## Set Up the PostgreSQL Database

1. Install required Python dependencies:

```bash
pip install boto3
```

2. Set up the required environment variables:

```bash
# Set the stack name environment variable
export STACK_NAME=CdkVideoGamesSalesAssistantBedrockAgentStack

# Retrieve the output values from the CDK stack
export SECRET_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='SecretARN'].OutputValue" --output text)
export DATA_SOURCE_BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='DataSourceBucketName'].OutputValue" --output text)
export AURORA_SERVERLESS_DB_CLUSTER_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='AuroraServerlessDBClusterArn'].OutputValue" --output text)
export READONLY_SECRET_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='ReadOnlySecretARN'].OutputValue" --output text)

# Retrieve the parameter values from the CDK stack
export TABLE_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Parameters[?ParameterKey=='PostgreSQLTableName'].ParameterValue" --output text)
export DATABASE_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Parameters[?ParameterKey=='PostgreSQLDatabaseName'].ParameterValue" --output text)
cat << EOF
STACK_NAME: ${STACK_NAME}
SECRET_ARN: ${SECRET_ARN}
DATA_SOURCE_BUCKET_NAME: ${DATA_SOURCE_BUCKET_NAME}
AURORA_SERVERLESS_DB_CLUSTER_ARN: ${AURORA_SERVERLESS_DB_CLUSTER_ARN}
READONLY_SECRET_ARN: ${READONLY_SECRET_ARN}
TABLE_NAME: ${TABLE_NAME}
DATABASE_NAME: ${DATABASE_NAME}
EOF
```

### Load Sample Data

Execute the following command to create the database table and load the sample data:

```bash
python3 resources/create-sales-database.py
```

The script uses the **[video_games_sales_no_headers.csv](./resources/database/video_games_sales_no_headers.csv)** as the data source.

> [!NOTE]
> The data source provided contains information from [Video Game Sales](https://www.kaggle.com/datasets/asaniczka/video-game-sales-2024) which is made available under the [ODC Attribution License](https://opendatacommons.org/licenses/odbl/1-0/).

### Create Read-Only Database User

Execute the following command to create the read-only database user:

```bash
python3 resources/create-readonly-user.py
```

This script creates a `readonly_user` in PostgreSQL with SELECT-only privileges on the `video_games_sales_units` table. The Lambda function uses this user for least-privilege database access.

## Test the Agent in AWS Console

Navigate to your Amazon Bedrock Agent named **video-games-sales-assistant**:

- Click **Edit Agent Builder**
- In the Agent builder section click **Save**
- Click **Prepare**
- Click **Test**

Try these sample questions:

- Hello!
- How can you help me?
- What is the structure of the data?
- Which developers tend to get the best reviews?
- What were the total sales for each region between 2000 and 2010? Give me the data in percentages.
- What were the best-selling games in the last 10 years?
- What are the best-selling video game genres?
- Give me the top 3 game publishers.
- Give me the top 3 video games with the best reviews and the best sales.
- Which is the year with the highest number of games released?
- Which are the most popular consoles and why?
- Give me a short summary and conclusion of our conversation.

## Create Agent Alias for Front-End Application

To use the agent in your front-end application:

- Go to your **Agent Overview**
- Click **Create Alias**

You can now proceed to the [Front-End Implementation - Integrating Amazon Bedrock Agent with a Ready-to-Use Data Analyst Assistant Application](../amplify-video-games-sales-assistant-bedrock-agent/).

## Cleaning-up Resources (Optional)

To avoid unnecessary charges, delete the CDK stack:

```bash
cdk destroy
```

## Thank You

## License

This project is licensed under the Apache-2.0 License.
