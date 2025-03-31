import asyncio
import os
from crewai_tools import SpiderTool
from dotenv import load_dotenv

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

load_dotenv()
# To enable scraping any website it finds during its execution
spider_tool = SpiderTool(api_key=os.environ.get("SPIDER_API_KEY"))

tools = [spider_tool._run]

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
