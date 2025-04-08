# Startup Advisor Agent - CloudFormation Deployment

A CloudFormation-based deployment solution for setting up a Startup Advisor Agent using Amazon Bedrock Agents, including web search capabilities and working memory components.

## Architecture Overview

The deployment uses a nested stack architecture:

- Main stack (parent) orchestrates the overall deployment
- Bedrock Agents stack configures the agent and permissions
- Web search stack enables search capabilities
- Working memory stack manages agent memory
