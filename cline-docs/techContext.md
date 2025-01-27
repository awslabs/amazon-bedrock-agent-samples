# Technical Context

## Technologies Used

### Core Services
- **Amazon Bedrock**: Foundation model service for AI capabilities
- **Amazon Bedrock Agents**: Service for creating and managing AI agents
- **AWS Lambda**: For executing agent tools and actions
- **AWS IAM**: For security and access control

### Development Stack
- **Python 3.8+**: Primary development language
- **boto3**: AWS SDK for Python
- **YAML**: For agent and task configuration
- **Virtual Environment**: For dependency isolation

## Development Setup

### Prerequisites
1. AWS Account with Bedrock access
2. Python 3.8 or later installed
3. AWS credentials configured

### Environment Setup
```bash
# Clone repository
git clone https://github.com/awslabs/amazon-bedrock-agent-samples

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

or just use pyenv

# Install dependencies
pip3 install -r src/requirements.txt
```

### AWS Configuration
- Region: us-west-2 (default)
- Required AWS Profile: jlanger+ml-demo-Admin
- Environment Variables:
  ```bash
  AWS_DEFAULT_REGION=us-west-2
  AWS_PROFILE=jlanger+ml-demo-Admin
  ```

## Technical Constraints

### Development Constraints
1. Must follow AWS security best practices
2. Code must be compatible with Python 3.8+
3. All AWS interactions through boto3 SDK
4. Must maintain backward compatibility

### System Constraints
1. Agent operations limited by Bedrock service quotas
2. Lambda function timeouts and memory limits
3. API rate limits for external services
4. Network latency considerations

### Security Constraints
1. IAM roles must follow least privilege principle
2. Sensitive data must be properly encrypted
3. No hardcoded credentials
4. Must use secure communication channels

## Integration Points

### Internal Integrations
1. Between supervisor and collaborator agents
2. With shared tools (web search, working memory)
3. With AWS services (Lambda, IAM)

### External Integrations
1. Web search capabilities
2. Stock data providers
3. Third-party APIs when needed
