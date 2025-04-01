import asyncio
from InlineAgent.agent import InlineAgent
from rich.console import Console
from rich.markdown import Markdown
import argparse


async def invoke_agent(modelId):

    await InlineAgent(
        foundation_model=modelId,
        instruction="You are a friendly assistant that is supposed to say hello to everything.",
        user_input=True,
        agent_name="hello-world-agent",
    ).invoke("Hi how are you? What can you do for me?")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "modelId", help="Amazon Bedrock Foundational Model Id", type=str
    )
    args = parser.parse_args()

    code = """
from bedrock_agents.agent import InlineAgent

InlineAgent(
    foundationModel="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    instruction="You are a friendly assistant that is supposed to say hello to everything.",
    userInput=True,
    agentName="hello-world-agent",
).invoke("Hi how are you? What can you do for me?")
"""
    console = Console()
    console.print(Markdown(f"**Running Hellow world agent:**\n```python{code}```"))
    asyncio.run(invoke_agent(modelId=args.modelId))
