# Bedrock Agent with Fargate Tool (Apache Tika)

## Purpose
This example deploys a Bedrock Agent that can extract text, metadata, and MIME types from documents using [Apache Tika](https://tika.apache.org/) running on ECS Fargate. A Lambda function bridges the Bedrock Agent action group calls to Tika's REST API, and an S3 bucket is provided for document uploads.

This repo is for demonstrative purposes only, and the application code is not meant for production use.

## Architecture

```
User → Bedrock Agent (Claude 3 Haiku)
         ↓
       Lambda (action group bridge)
         ↓
       Internal ALB → ECS Fargate (Apache Tika :9998)
         ↓
       S3 Bucket (document uploads)
```

- Apache Tika runs as a Docker container on Fargate in private subnets
- An internal ALB fronts the Fargate service (not internet-facing)
- A Python Lambda bridges Bedrock Agent action group calls to Tika's REST API
- An S3 bucket allows users to drop files for the agent to process
- The Bedrock Agent uses Claude 3 Haiku as its foundation model

## Prerequisites
Before getting started, ensure you have the following installed:
* [Python 3.10+](https://www.python.org/downloads/)
* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured with appropriate credentials and permissions
* [AWS CLI Environment Variable setup](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html). Credentials used need to have permissions to CloudFormation, IAM, Bedrock, Lambda, ECS, EC2, ELB, and S3. If you use PowerUser or Admin permissions, temporary credentials are recommended.
* [Bedrock Foundation model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html). Ensure that you have access to Claude 3 Haiku in your target region.

If you are new to Python, be sure to read through [venv documentation](https://docs.python.org/3/library/venv.html) as you will need to use this to deploy the agent using the CDK.

## Deployment

### Setting up Virtual Environment

```bash
git clone https://github.com/awslabs/amazon-bedrock-agent-samples

cd amazon-bedrock-agent-samples/examples/agents/agent_with_fargate_tool/cdk

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r requirements.txt
```

### Bootstrap and Deploy

```bash
export AWS_DEFAULT_REGION=us-east-1

cdk bootstrap

cdk synth

cdk deploy
```

You should get prompted to deploy the changes. The stack will create a VPC, ECS Fargate service running Apache Tika, an internal ALB, a Lambda function, an S3 bucket, and the Bedrock Agent.

### Stack Outputs

After deployment, the stack outputs:
- `AgentId` — Bedrock Agent ID
- `AgentAliasId` — Agent alias ID (use this to invoke the agent)
- `TikaAlbDns` — Internal ALB DNS name
- `DocsBucketName` — S3 bucket name for uploading documents

## Usage

### Process a file from S3

1. Upload a file to the S3 bucket:
   ```bash
   aws s3 cp my-report.pdf s3://<DocsBucketName>/my-report.pdf
   ```

2. Ask the agent:
   > "Extract text from my-report.pdf"

   The agent calls the `/process-s3-file` action with the object key and returns the extracted content.

### Available Actions

| Endpoint | Description |
|---|---|
| `/process-s3-file` | Fetch a file from S3 and extract text, metadata, or detect MIME type |
| `/extract-text` | Extract text from a base64-encoded document |
| `/detect-type` | Detect MIME type of a base64-encoded document |
| `/extract-metadata` | Extract metadata from a base64-encoded document |

## Sample Prompts
- Extract text from my-report.pdf
- What is the MIME type of data.xlsx?
- Get the metadata from presentation.pptx

## Project Structure

```
agent_with_fargate_tool/
├── backend/
│   └── lambda.py                          # Lambda handler bridging Bedrock → Tika
├── cdk/
│   ├── app.py                             # CDK app entry point
│   ├── cdk.json                           # CDK configuration
│   ├── requirements.txt                   # Python CDK dependencies
│   └── BedrockAgentStack/
│       ├── BedrockAgentStack_stack.py     # CDK stack (VPC, ECS, ALB, Lambda, Agent)
│       └── config.json                    # Agent and Fargate configuration
├── schemas/
│   └── tika-openapi.json                  # OpenAPI schema for the action group
└── README.md
```

## Next Steps
* Learn more about what other models are on [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/foundation-models-reference.html).
* Scale the Fargate service with target tracking auto-scaling for production workloads.
* Add a [Guardrail](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html) to the agent for responsible AI.
* Integrate with a Knowledge Base for RAG over extracted document content.

## Clean Up

```bash
cdk destroy
```

When prompted, indicate yes and the stack should delete.
```
Are you sure you want to delete: BedrockAgentStack (y/n)? y
```
