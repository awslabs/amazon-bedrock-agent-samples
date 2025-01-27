# Getting Started with SAM Video Games Sales Assistant and Amazon Bedrock Agents

This tutorial guides you through the process of setting up the back-end using AWS Serverless Application Model (SAM) and the Amazon Bedrock Agent. The services to be deployed are: Virtual Private Cloud (VPC), Lambda Function, Aurora Serverless PostgreSQL Cluster Database, AWS Secrets Manager, and Amazon DynamoDB Table within the SAM Project. Using Python scripts, you will create an Amazon S3 Bucket to upload the sales data source and create the Amazon Bedrock Agent.

By the end of this tutorial, you'll have the Amazon Bedrock Agent working in the AWS Console for testing purposes.

> IMPORTANT: This example is meant for demo purposes and is not production ready. Please make sure to validate the code with your organizations security best practices.

## Prerequisites

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3.9 or a later major version installed](https://www.python.org/downloads/) 
* Anthropic Claude 3.5 Haiku and Sonnet enabled in Amazon Bedrock.

## SAM Deployment

Under this SAM project folder execute the following commands to deploy the backend services for the Assistant:

```bash
sam build
```

Note: By default, the Python version used for the Lambda Function is 3.9. If you receive a **Build Failed** error, change to the Python version (>3.9) that you have in **template.yaml** file in line **56**.

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

After uploading the SAM project and changeset created:

- Deploy this changeset? [y/N]: **Y**

> If you prefer, you can continue creating the following resources manually [here](./manual_database_data_load_and_agent_creation.md).

After completing the SAM deployment, execute the following commands to save the environment variables for use in subsequent configurations.

``` bash
# Set the stack name environment variable
export STACK_NAME=sam-bedrock-video-games-sales-assistant

# Retrieve the output values and store them in environment variables
export DATABASE_CLUSTER_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='DatabaseClusterName'].OutputValue" --output text)
export QUESTION_ANSWERS_TABLE_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='QuestionAnswersTableName'].OutputValue" --output text)
export QUESTION_ANSWERS_TABLE_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='QuestionAnswersTableArn'].OutputValue" --output text)
export SECRET_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='SecretARN'].OutputValue" --output text)
export LAMBDA_FUNCTION_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionArn'].OutputValue" --output text)
export LAMBDA_FUNCTION_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" --output text)
export DATA_SOURCE_BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='DataSourceBucketName'].OutputValue" --output text)
export AURORA_SERVERLESS_DB_CLUSTER_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='AuroraServerlessDBClusterArn'].OutputValue" --output text)
cat << EOF
STACK_NAME: ${STACK_NAME}
QUESTION_ANSWERS_TABLE_NAME: ${QUESTION_ANSWERS_TABLE_NAME}
QUESTION_ANSWERS_TABLE_ARN: ${QUESTION_ANSWERS_TABLE_ARN}
DATABASE_CLUSTER_NAME: ${DATABASE_CLUSTER_NAME}
SECRET_ARN: ${SECRET_ARN}
LAMBDA_FUNCTION_ARN: ${LAMBDA_FUNCTION_ARN}
LAMBDA_FUNCTION_NAME: ${LAMBDA_FUNCTION_NAME}
DATA_SOURCE_BUCKET_NAME: ${DATA_SOURCE_BUCKET_NAME}
AURORA_SERVERLESS_DB_CLUSTER_ARN: ${AURORA_SERVERLESS_DB_CLUSTER_ARN}
EOF

```

## Loading Data Sample to the PostgreSQL Databae

> Execute the following command to create the database and load the data source.

``` bash
pip install boto3
python3 resources/create-sales-database.py
```

## Amazon Bedrock Agent Creation

Execute the following command to create the Amazon Bedrock Agent. This step will take about 30 seconds.

``` bash
python3 resources/create-amazon-bedrock-agent.py
```

The Agent was configured with the following information:
- [Agent Instruction](./resources/agent-instructions.txt)
- [Agent Orchestration Strategy](./resources/agent-orchestration-strategy.txt)
- [Agent API Schema for the Action Group](./resources/agent-api-schema.json)

## Testing the Agent

Now you can go back to your Amazon Bedrock Agen called **video-games-sales-assistant**, click on **Edit Agent Builder**, in the **Agent builder** section click on **Save**, **Prepare** and **Test**, use the **Test Agent** with the following sample questions:

- Hello
- How can you help me?
- What is the structure of the data?
- Which developers tend to get the best reviews?
- What were the best-selling games in the last 10 years?
- What are the best-selling video game genres?
- Give me the top 3 game publishers.
- Give me the top 3 video games with the best reviews and the best sales.
- Which is the year with the highest number of games released?
- Which are the most popular consoles and why?
- Give me a short summary and conclusion.

## Create Alias Agent Application

To use the Agent application, once you have a **Prepared** version for testing, go to your **Agent overview** and click on **Create Alias** to use it from your front-end application.

## Cleaning-up Resources (optional)

The next steps are optional and demonstrate how to delete the resources that we've created.
Update the following exports with the values of the services you created before, and then execute."

``` bash
# Set the stack name environment variable
export AGENT_ID=<you_agent_id>
export AGENT_ARN=<you_agent_arn>
export ACTION_GROUP_ID=<you_action_group_id>
export LAMBDA_FUNCTION_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionArn'].OutputValue" --output text)
export LAMBDA_FUNCTION_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" --output text)
export DATA_SOURCE_BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='DataSourceBucketName'].OutputValue" --output text)

```

Execute the following command to delete Amazon Bedrock Agent.

``` bash
python3 resources/delete-amazon-bedrock-agent.py
```

Remove the data source file uploaded to the Amazon S3 bucket.

``` bash
aws s3api delete-object --bucket $DATA_SOURCE_BUCKET_NAME --key video_games_sales_no_headers.csv
```

Delete the AWS SAM application by deleting the AWS CloudFormation stack.

``` bash
sam delete
```

## Thank You