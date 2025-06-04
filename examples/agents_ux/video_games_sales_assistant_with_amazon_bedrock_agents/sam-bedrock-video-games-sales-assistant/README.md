# Generative AI Application - Data Source and Amazon Bedrock Agent Deployment with AWS SAM

This tutorial guides you through setting up the back-end infrastructure and Amazon Bedrock Agent to create a Data Analyst Assistant for Video Game Sales using AWS Serverless Application Model (SAM).

## Overview

You will deploy the following AWS services:

- **Amazon Bedrock Agent**: Powers the ***Data Analyst Assistant*** that answers questions by generating SQL queries using Claude 3.5 Haiku
- **AWS Lambda**: Processes agent requests through various tools including:
    - /runSQLQuery: Executes queries against the database
    - /getCurrentDate: Retrieves the current date
    - /getTablesInformation: Provides database tables information for agent context
- **Aurora Serverless PostgreSQL**: Stores the video game sales data
- **Amazon DynamoDB**: Tracks questions and query results
- **AWS Secrets Manager**: Securely stores database credentials
- **Amazon VPC**: Provides network isolation for the database

By completing this tutorial, you'll have a fully functional Amazon Bedrock Agent for testing in the AWS Console.

> [!IMPORTANT]
> This sample application is meant for demo purposes and is not production ready. Please make sure to validate the code with your organizations security best practices.
>
> Remember to clean up resources after testing to avoid unnecessary costs by following the clean-up steps provided.

## Prerequisites

Before you begin, ensure you have:

* [SAM CLI Installed](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3.9 or later](https://www.python.org/downloads/) 
* [Boto3 1.36 or later](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html)
* Anthropic Claude 3.5 Haiku and Sonnet models enabled in Amazon Bedrock
* Run this command to create a service-linked role for RDS:

```bash
aws iam create-service-linked-role --aws-service-name rds.amazonaws.com
```

## Deploy the Back-End Services with AWS SAM

Navigate to the SAM project folder (sam-bedrock-video-games-sales-assistant/) and execute::

```bash
sam build
```

> [!CAUTION]
> If you encounter a **Build Failed error**, you might need to change the Python version in the [template.yaml](./template.yaml) file. By default, the Lambda function uses **Python 3.9**. You can modify this setting on **line 84** of the **[template.yaml](./template.yaml)** file to use a Python version higher than 3.9 that you have installed.

Now deploy the SAM application:

```bash
sam deploy --guided
```

Use the following value arguments for the deployment configuration:

- Stack Name : **sam-bedrock-video-games-sales-assistant**
- AWS Region : **<use_your_own_code_region>**
- Parameter PostgreSQLDatabaseName : **video_games_sales**
- Parameter AuroraMaxCapacity : **2**
- Parameter AuroraMinCapacity : **1**
- Confirm changes before deploy : **Y**
- Allow SAM CLI IAM role creation : **Y**
- Disable rollback : **N**
- Save arguments to configuration file : **Y**
- SAM configuration file : **samconfig.toml**
- SAM configuration environment : **default**

After the SAM project preparation and changeset created, confirm the following to start the deployment:

- Deploy this changeset? [y/N]: **Y**

After deployment completes, the following services will be created:

- Amazon Bedrock Agent configured with:
    - **[Agent Instructions](./resources/agent-instructions.txt)**
    - **[Agent API Schema that provides the tools for the Agent (Action Group)](./resources/agent-api-schema.json)**
- Lambda Function API for the agent to use
    - **[Provide the tools for the agent: runSQLQuery, getCurrentDate, and getTablesInformation](./functions/assistant-api-postgresql-haiku-35/tables_information.txt)**
- The Aurora Serverless PostgreSQL Cluster Database
- A DynamoDB Table for tracking questions and query details

> [!TIP]
> You can also change the data source to connect to your preferred database engine by adapting both the Agent's instructions and the AWS Lambda API function logic.

> [!IMPORTANT] 
> Enhance AI safety and compliance by implementing **[Amazon Bedrock Guardrails](https://aws.amazon.com/bedrock/guardrails/)** for your AI applications.

> [!NOTE]
> To learn about agent creation configuration, please refer to [this tutorial](./manual_database_data_load_and_agent_creation.md), which provides step-by-step guidance for setting up an Amazon Bedrock Agent in the AWS Console.

## Load Sample Data into PostgreSQL Database

Set up the required environment variables:

``` bash
# Set the stack name environment variable
export STACK_NAME=sam-bedrock-video-games-sales-assistant

# Retrieve the output values and store them in environment variables
export SECRET_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='SecretARN'].OutputValue" --output text)
export DATA_SOURCE_BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='DataSourceBucketName'].OutputValue" --output text)
export AURORA_SERVERLESS_DB_CLUSTER_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='AuroraServerlessDBClusterArn'].OutputValue" --output text)
cat << EOF
STACK_NAME: ${STACK_NAME}
SECRET_ARN: ${SECRET_ARN}
DATA_SOURCE_BUCKET_NAME: ${DATA_SOURCE_BUCKET_NAME}
AURORA_SERVERLESS_DB_CLUSTER_ARN: ${AURORA_SERVERLESS_DB_CLUSTER_ARN}
EOF

```

Execute the following command to create the database and load the sample data:

``` bash
python3 resources/create-sales-database.py
```

The script uses the **[video_games_sales_no_headers.csv](./resources/database/video_games_sales_no_headers.csv)** as the data source.

> [!NOTE]
> The data source provided contains information from [Video Game Sales](https://www.kaggle.com/datasets/asaniczka/video-game-sales-2024) which is made available under the [ODC Attribution License](https://opendatacommons.org/licenses/odbl/1-0/).

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

You can now proceed to the [Front-End Implementation - Integrating Amazon Bedrock Agent with a Ready-to-Use Data Analyst Assistant Application](../amplify-video-games-sales-assistant-bedrock-agent/). The tutorial will ask you for your **Agent Alias** along with the other services that you have created so far.

## Cleaning-up Resources (Optional)

To avoid unnecessary charges, delete the AWS SAM application:

``` bash
sam delete
```

## Thank You

## License

This project is licensed under the Apache-2.0 License.