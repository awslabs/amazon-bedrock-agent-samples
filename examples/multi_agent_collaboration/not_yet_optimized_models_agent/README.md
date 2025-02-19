# Yet to be Optimized Models for Multi-agents - Mortgage Assistant Agent

Amazon Bedrock Agents now supports all models from Amazon Bedrock so that you can create agents with any foundation model. Currently, some of the offered models are optimized with prompts/parsers fine-tuned for integrating with the agents architecture. Over time, we plan to offer optimization for all of the offered models.

If you’ve selected a model for which optimization is not yet available, you can override the prompts to extract better responses, and if needed, override the parsers. See [Modify parser Lambda function in Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/lambda-parser.html) for more information.

In this example the Mortgage Assistant Agent example is refactored and prompts are updated for Llama and Mistral in the main-llama.py and main-mistral.py files. Utils contains the utility files from the base directory refactored for the responses expected from mistral and llama instead of Claude

This example demonstrates the use of Amazon Bedrock Agents multi-agent collaboration with its built-in Routing Classifier feature. By simply enabling that mode for your supervisor, Bedrock automatically routes to the correct collaborating sub-agent using LLM intent classification optimized to route with sub-second latency. Contrast that with a traditional supervisor that must go through its own orchestration loop, a more expensive proposition that can take 3-6 seconds depending on which LLM you are using. This feature is most valuable when trying to build a unified customer experience across a set of sub-agents. In our example, we have 3 collaborators: one for general mortgage questions, one for handling conversations about Existing mortgages, and another for dealing with New mortgages.

Try sample prompts:

- "what's my balance?"
- "what are rates looking like over the past 2 weeks for new mortgages?"
- "what's your general guidance about refinancing mortgages?"

Each of these gets routed quickly to the right sub-agent for subsequent processing.
Conversation switching is seamless.

Routing also reverts automatically to full Supervisor mode if the request is truly
not mapping cleanly to a single collaborator. For example:

- "what interest rate do i have on my existing mortgage, and how does it compare to rates for new mortgages"

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
cd examples/multi_agent_collaboration/unoptimized_models_example/
python3 main-llama.py --recreate_agents "true"
```
or
```bash
cd examples/multi_agent_collaboration/unoptimized_models_example/
python3 main-mistral.py --recreate_agents "true"
```

2. Invoke

```bash
python3 main-llama.py --recreate_agents "false"
```
or
```bash
python3 main-mistral.py --recreate_agents "false"
```

3. Cleanup

```bash
python3 main-llama.py --clean_up "true"
```

## License

This project is licensed under the Apache-2.0 License.