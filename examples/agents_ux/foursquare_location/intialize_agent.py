import json
from datetime import datetime
import uuid

from bedrock_agent_helper import BedrockAgent
from function_calls import get_bedrock_tools, convert_tools_to_function_schema
from location_tools import search_near
from weather_tools import get_weather


# Get the bedrock tools and convert to function schema
tools = get_bedrock_tools()
action_groups_schema = convert_tools_to_function_schema(tools)

#print(json.dumps(action_groups_schema, indent=4))

DEFAULT_INSTRUCTIONS = """
            You are a helpful location aware agent.
            You search for things to do based on the context provided through the input.  
            Always Use the tools provided along with the context to provide the best answers
            to the human's questions. Use the information from the tools to provide interesting
            answers in a conversational style!

            Format your response using HTML, but whenever you identify a retrieved location by name, tag it
            with the id, latitude and longitude: <place id="{{fsq_place_id}}" lat={{lat}} lng={{lng}}>{{name}}</place>

            For example: `<div>Check out <place id="42893400f964a52052231fe3" lat=40.66193827120861 lng=-73.96961688995361>Prospect Park</place>, people say it's got great playgrounds!</div>`
"""

DEFAULT_MODEL = "us.amazon.nova-pro-v1:0"

def initialize(session_id: str, instructions=None, model_id=None):
    # Initialize the agent
    agent = BedrockAgent(
        session_id=session_id,
        model_id=model_id if model_id is not None else DEFAULT_MODEL,
        action_groups=action_groups_schema,
        instructions=instructions if instructions is not None else DEFAULT_INSTRUCTIONS,
    )

    # Set up session attributes
    session_attributes = {
        'current_date': datetime.now().strftime("%m/%d/%Y"),
        'radius': '100',
    }

    return agent, session_attributes