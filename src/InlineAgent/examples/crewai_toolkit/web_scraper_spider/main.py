import asyncio
import json
import os
from typing import Any, Dict, Literal
from crewai_tools import SpiderTool
from dotenv import load_dotenv

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

from InlineAgent import AgentAppConfig

config = AgentAppConfig()

# To enable scraping any website it finds during its execution
spider_tool = SpiderTool(api_key=config.SPIDER_API_KEY)

def spider_tool_run(
    website_url: str,
    mode: Literal["scrape", "crawl"] = "scrape",) -> str:
    """Execute the spider tool to scrape or crawl the specified website.

    Args:
        website_url (str): The URL to process. Must be a valid HTTP(S) URL.
        mode (Literal["scrape", "crawl"]): Operation mode.
            - "scrape": Extract content from single page
            - "crawl": Follow links and extract content from multiple pages

    Returns:
        Optional[str]: Extracted content in markdown format, or None if extraction fails
                    and log_failures is True.

    Raises:
        ValueError: If URL is invalid or missing, or if mode is invalid.
        ImportError: If spider-client package is not properly installed.
        ConnectionError: If network connection fails while accessing the URL.
        Exception: For other runtime errors.
    """
    return json.dumps(spider_tool._run(website_url=website_url, mode=mode),default=str)


tools = [spider_tool_run]

spider_action_group = ActionGroup(
    name="spider_action_group", tools=tools, argument_key="Args:"
)
website_url = "https://en.wikipedia.org/wiki/Machine_learning"

github_agent = InlineAgent(
    foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    instruction=f"You're a researcher that is tasked with researching a website and it's content (use crawl mode). The website is to crawl is: {website_url}.",
    agent_name="cost_agent",
    action_groups=[spider_action_group],
)


asyncio.run(github_agent.invoke("What is the application of Machine Learning?"))
