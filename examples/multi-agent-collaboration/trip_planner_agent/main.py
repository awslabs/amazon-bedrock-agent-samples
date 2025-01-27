#!/usr/bin/env python

# Copyright 2024 Amazon.com and its affiliates; all rights reserved.
# This file is AWS Content and may not be duplicated or distributed without permission
import sys
from pathlib import Path
import datetime
import traceback
import argparse
import yaml
import os
from textwrap import dedent
import uuid
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.utils.bedrock_agent import Agent, SupervisorAgent, Task, region, account_id

current_dir = os.path.dirname(os.path.abspath(__file__))
task_yaml_path = os.path.join(current_dir, "tasks.yaml")
agent_yaml_path = os.path.join(current_dir, "agents.yaml")


def create_agent(agent_name, agent_content, tools=None):
    agent = Agent(agent_name, agent_content, tools)
    print(f"Created agent: {agent_name}")
    return agent


def main(args):
    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
        if not Agent.exists("trip_planner"):
            print("'trip_planner' agent does not exist. Please rerun with --recreate_agents 'true'")
    else:
        Agent.set_force_recreate_default(True)
        Agent.delete_by_name("trip_planner", verbose=True)

    if args.clean_up == "true":        
        Agent.delete_by_name("trip_planner", verbose=True)
        Agent.delete_by_name("itinerary_compiler", verbose=True)
        Agent.delete_by_name("activity_finder", verbose=True)
        Agent.delete_by_name("restaurant_scout", verbose=True)
    else:
        inputs = {
            "origin": args.origin,
            "destination": args.destination,
            "age": args.age,
            "hotel_location": args.hotel_location,
            "arrival": args.arrival,
            "departure": args.departure,
            "interests": args.interests,
            "itinerary_hints": args.itinerary_hints,
            "food_preferences": args.food_preferences 
        }

        with open(task_yaml_path, "r") as file:
            yaml_task_content = yaml.safe_load(file)

        activity_planning_task = Task("activity_planning_task", yaml_task_content, inputs)
        restaurant_scout_task = Task("restaurant_scout_task", yaml_task_content, inputs)
        itinerary_compilation_task = Task(
            "itinerary_compilation_task", yaml_task_content, inputs
        )

        web_search_tool = {
            "code":f"arn:aws:lambda:{region}:{account_id}:function:web_search",
            "definition":{
                "name": "web_search",
                "description": "Searches the web for information",
                "parameters": {
                    "search_query": {
                        "description": "The query to search the web with",
                        "type": "string",
                        "required": True,
                    },
                    "target_website": {
                        "description": "The specific website to search including its domain name. If not provided, the most relevant website will be used",
                        "type": "string",
                        "required": False,
                    },
                    "topic": {
                        "description": "The topic being searched. 'news' or 'general'. Helps narrow the search when news is the focus.",
                        "type": "string",
                        "required": False,
                    },
                    "days": {
                        "description": "The number of days of history to search. Helps when looking for recent events or news.",
                        "type": "string",
                        "required": False,
                    },
                },
            },
        }
        set_value_for_key = {
            "code":f"arn:aws:lambda:{region}:{account_id}:function:working_memory",
            "definition":{
                "name": "set_value_for_key",
                "description": " Stores a key-value pair table. Creates the table if it doesn't exist.",
                "parameters": {
                    "key": {
                        "description": "The name of the key to store the value under.",
                        "type": "string",
                        "required": True,
                    },
                    "value": {
                        "description": "The value to store for that key name.",
                        "type": "string",
                        "required": True,
                    },
                    "table_name": {
                        "description": "The name of the table to use for storage.",
                        "type": "string",
                        "required": True,
                    }
                },
            },
        }

        get_key_value = {
            "code":f"arn:aws:lambda:{region}:{account_id}:function:working_memory",
            "definition":{
                "name": "get_key_value",
                "description": "Retrieves a value for a given key name from a table.",
                "parameters": {
                    "key": {
                        "description": "The name of the key to store the value under.",
                        "type": "string",
                        "required": True,
                    },
                    "table_name": {
                        "description": "The name of the table to use for storage.",
                        "type": "string",
                        "required": True,
                    }
                },
            },
        }

        delete_table = {
            "code":f"arn:aws:lambda:{region}:{account_id}:function:working_memory",
            "definition":{
                "name": "delete_table",
                "description": "Deletes a working memory table.",
                "parameters": {
                    "table_name": {
                        "description": "The name of the working memory table to delete.",
                        "type": "string",
                        "required": True
                    }
                },
            },
        }

        with open(agent_yaml_path, "r") as file:
            yaml_agent_content = yaml.safe_load(file)

        activity_finder = Agent(
            "activity_finder",
            yaml_agent_content,
            tools=[web_search_tool, set_value_for_key, get_key_value, delete_table])

        restaurant_scout = Agent(
            "restaurant_scout",
            yaml_agent_content,
            tools=[web_search_tool, set_value_for_key, get_key_value, delete_table])

        itinerary_compiler = Agent("itinerary_compiler", yaml_agent_content,
            tools=[set_value_for_key, get_key_value, delete_table])

        print("\n\nCreating supervisor agent...\n\n")
        trip_planner = SupervisorAgent(
            "trip_planner",
            yaml_agent_content,
            [activity_finder, restaurant_scout, itinerary_compiler],
        )

        if args.recreate_agents == "false":
            print("\n\nInvoking supervisor agent...\n\n")

            time_before_call = datetime.datetime.now()
            print(f"time before call: {time_before_call}\n")
            folder_name = "trip-planner-" + str(uuid.uuid4())
            try:
                print(
                    trip_planner.invoke_with_tasks(
                        [
                            activity_planning_task,
                            restaurant_scout_task,
                            itinerary_compilation_task,
                        ],
                        additional_instructions=dedent(f"""
                                Use a single project table in Working Memory for this entire set of tasks,
                                using table name: {folder_name}. When making requests to your collaborators,
                                tell them the working memory table name, and the named keys  they should 
                                use to retrieve their input or save their output.
                                The keys they use in that table will allow them to keep track of state.
                                As a final step, you MUST use one of your collaborators to delete the 
                                Working Memory table.
                                For the final response, please only return the final itinerary, 
                                returning the full text as is from your collaborator.
                                """),
                        processing_type="sequential",
                        enable_trace=True,
                        trace_level=args.trace_level,
                    )
                )
            except Exception as e:
                print(e)
                traceback.print_exc()
                pass

            duration = datetime.datetime.now() - time_before_call
            print(f"\nTime taken: {duration.total_seconds():,.1f} seconds")

        else:
            print("Recreated agents.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recreate_agents",
        required=False,
        default="false",
        help="False if reusing existing agents.",
    )
    parser.add_argument(
        "--trace_level",
        required=False,
        default="core",
        help="The level of trace, 'core', 'outline', 'all'.",
    )
    parser.add_argument(
        "--clean_up",
        required=False,
        default="false",
        help="Cleanup all infrastructure.",
    )
    parser.add_argument(
        "--origin",
        required=False,
        default="Boston, BOS",
        help="Origin of the trip.",
    )
    parser.add_argument(
        "--destination",
        required=False,
        default="Europe",
        help="Destination of the trip.",
    )
    parser.add_argument(
        "--age",
        required=False,
        default="25",
        help="Age of the traveler.",
    )
    parser.add_argument(
        "--hotel_location",
        required=False,
        default="Multiple across Europe",
        help="Preferred Hotel location.",
    )
    parser.add_argument(
        "--arrival",
        required=False,
        default="June 12, 11:00",
        help="Preferred arrival time.",
    )
    parser.add_argument(
        "--departure",
        required=False,
        default="June 20, 17:00",
        help="Preferred departure time.",
    )
    parser.add_argument(
        "--food_preferences",
        required=False,
        default="Unique to the destination, but with good gluten free options",
        help="Preferred food.",
    )
    parser.add_argument(
        "--interests",
        required=False,
        default="A few of the days on the beach, and some days with great historical museums",
        help="Additional hints about your interests for the trip.",
    )
    parser.add_argument(
        "--itinerary_hints",
        required=False,
        default="Spend the last day in Paris with friends",
        help="Specific hints about what to do on what days.",
    )
    args = parser.parse_args()

    main(args)
