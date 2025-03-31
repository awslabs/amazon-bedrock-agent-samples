from InlineAgent.agent import InlineAgent
from rich.console import Console
from rich.markdown import Markdown
import argparse


def invoke_agent(modelId):

    InlineAgent(
        foundationModel=modelId,
        instruction="You are a friendly assistant that is supposed to say hello to everything.",
        userInput=True,
        agentName="hello-world-agent",
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
    foundationModel="MOCK_ID",
    instruction="You are a friendly assistant that is supposed to say hello to everything.",
    userInput=True,
    agentName="hello-world-agent",
).invoke("Hi how are you? What can you do for me?")
"""
    console = Console()
    console.print(Markdown(f"**Running Hellow world agent:**\n```python{code}```"))
    invoke_agent(modelId=args.modelId)
