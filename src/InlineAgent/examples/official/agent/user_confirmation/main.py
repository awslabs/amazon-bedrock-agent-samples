import asyncio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent, require_confirmation


@require_confirmation
def get_current_weather(location: str, state: str, unit: str = "fahrenheit") -> dict:
    """
    Get the current weather in a given location.

    Parameters:
        location: The city, e.g., San Francisco
        state: The state eg CA
        unit: The unit to use, e.g., fahrenheit or celsius. Defaults to "fahrenheit"
    """
    return "Weather is 70 fahrenheit"


weather_action_group = ActionGroup(
    name="WeatherActionGroup",
    description="This is action group to get weather",
    tools=[get_current_weather],
)

agent = InlineAgent(
    foundation_model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    instruction="You are a friendly assistant that is responsible for getting the current weather.",
    action_groups=[weather_action_group],
    agent_name="MockAgent",
)


asyncio.run(agent.invoke(input_text="What is the weather of New York City, NY?"))
