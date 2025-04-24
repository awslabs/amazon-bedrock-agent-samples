# Cost Explorer Agent

> [!IMPORTANT]
> Never expose AWS keys publicly, use least privilege IAM roles, and rotate credentials every 90 days. Utilize AWS Secrets Manager, implement MFA, avoid hard-coding credentials, and continuously monitor access.

<p align="center">
  <a href="https://github.com/aws-samples/sample-cloud-spend-mcp-server"><img src="https://img.shields.io/badge/Github-aws_cost_explorer_mcp_server-blue" /></a>
  <a href="https://hub.docker.com/r/mcp/perplexity-ask"><img src="https://img.shields.io/badge/Docker-perplexity_ask-blue" /></a>
  <a href="https://github.com/jsonallen/perplexity-mcp"><img src="https://img.shields.io/badge/Github-perplexity_mcp-blue" /></a>
</p>

1. Follow setup instructions [here](../../../README.md#getting-started)
2. Create .env file with [.env.example](./.env.example)
3. Setup `aws-cost-explorer-mcp-server` MCP server

```python
git clone https://github.com/aws-samples/sample-cloud-spend-mcp-server.git
cd sample-cloud-spend-mcp-server/
docker build -t aws-cost-explorer-mcp .
```

4. Run example `python main.py`

## Output

<p align="center">
  <a href="https://www.youtube.com/watch?v=sLCcbyCZoHU"><img src="https://markdown-videos-api.jorgenkh.no/youtube/sLCcbyCZoHU?width=640&height=360&filetype=jpeg" /></a>
</p>
