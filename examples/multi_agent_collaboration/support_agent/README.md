# Support Assistant Agent

This is a good powering example to utilize the tickets, open git hub issues and public documentation effictevly. With support Agent you will be able to connect to JIRA and Guthub documentation to fetch any information needed regarding the opened/closed JIRA tasks or ask github related questions that can be of help to your developers.

Try sample prompts:

- "What are the current JIRA tasks?"
- "How to create a github API token?"

Each of these gets routed quickly to the right sub-agent for subsequent processing.
Conversation switching is seamless.

## Architecture
![Architecture](./Support-Agent.png)


## Prerequisites

1. Clone and install repository

```bash
git clone https://github.com/awslabs/amazon-bedrock-agent-samples

cd amazon-bedrock-agent-samples

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r src/requirements.txt
```

## Usage & Sample Prompts

1. Deploy Amazon Bedrock Agents

```bash
cd examples/multi_agent_collaboration/support_agent/
python3 main.py --recreate_agents "true" --confluence_url "<your confluence url>" --username "<your confluence username>" --token "<your confluence API access token>"
```
To add a greeting agent for handling users greeting, you can use the below command:
```bash
cd examples/multi_agent_collaboration/support_agent/
python3 main.py --recreate_agents "true" --agent_greeting "true" --confluence_url "<your confluence url>" --username "<your confluence username>" --token "<your confluence API access token>"
```

2. Invoke

```bash
python3 main.py --recreate_agents "false"
```

3. Cleanup

```bash
python3 main.py --clean_up "true"
```

## License

This project is licensed under the Apache-2.0 License.