# AWS Incident response system MCP

> [!IMPORTANT]
> Never expose AWS or JIRA keys publicly, use least privilege IAM roles, and rotate credentials every 90 days. Utilize AWS Secrets Manager, implement MFA, avoid hard-coding credentials, and continuously monitor access.

<p align="center">
  <a href="https://github.com/madhurprash/AWS_CloudGuardMCP/blob/main/server_scripts/monitoring_agent_server.py"><img src="https://img.shields.io/badge/Github-aws_monitoring_server-blue" /></a>
  <a href="https://github.com/madhurprash/AWS_CloudGuardMCP/blob/main/server_scripts/diagnosis_agent_server.py"><img src="https://img.shields.io/badge/Github-jira_ticket_creation_server-blue" /></a>
</p>

1. Follow setup instructions [here](../../../README.md#getting-started)
2. Create .env file with [.env.example](./.env.example)
3. Setup the `AWS CloudGuard` monitoring and JIRA MCP server

    ```python
    git clone https://github.com/madhurprash/AWS_CloudGuardMCP.git
    cd AWS_CloudGuardMCP/
    docker build -t aws-cloudguard-mcp .
    docker build -t aws-jira-mcp .
    ```

4. Run example `python main.py`

    ```bash
    python main.py
    ```