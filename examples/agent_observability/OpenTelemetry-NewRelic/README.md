# Amazon Bedrock Agent Observability with OpenTelemetry on Dynatrace

An OpenTelemetry example to provide observability to AWS Bedrock Agents.

## Setup

Create a [Free Dynatrace Trial](https://www.dynatrace.com/signup/) for 15 days.
After a few minutes, you will get redirected to your tenant. The URL will look like `https://wkf10640.apps.dynatrace.com/`.
The value `wkf10640` is your environment id which will be needed later.


### Prerequisites
1. AWS account with appropriate IAM permissions for Amazon Bedrock Agents
2. An existing Amazon Bedrock Agent (or follow [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-create.html) to create one)
3. A Dynatrace Token, to create one:

   1. In Dynatrace, go to **Access Tokens**. To find **Access Tokens**, press **Ctrl/Cmd+K** to search for and select **Access Tokens**.
   2. In **Access Tokens**, select **Generate new token**.
   3. Enter a **Token name** for your new token.
   4. Give your new token the following permissions:
   5. Search for and select all of the following scopes.
       * **Ingest OpenTelemetry traces** (`openTelemetryTrace.ingest`)
   6. Select **Generate token**.
   7. Copy the generated token to the clipboard. Store the token in a password manager for future use.


### Installation

```bash
pip install -r requirements.txt
```

## Quick Start

Configure the following env var

- `DT_TOKEN`
- `OTLP_ENDPOINT`

| EnvVar | Description                    | Example                                         |
|--------|--------------------------------|-------------------------------------------------|
| `DT_TOKEN` | Dynatrace Access token         | `dt0c01.VFGZLKTQ...`                            |
| `OTLP_ENDPOINT` | OpenTelemetry Protocol Endpoint | `https://{your-environment-id}.live.dynatrace.com/api/v2/otlp` <br> `http://0.0.0.0:4318` |

Run the main script to test your agent integration:

```bash
python main.py
```

![Example](./img/example_trace.png)
