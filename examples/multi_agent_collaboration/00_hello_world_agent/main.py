#!/usr/bin/env python

# Copyright 2024 Amazon.com and its affiliates; all rights reserved.
# This file is AWS Content and may not be duplicated or distributed without permission
import sys
from pathlib import Path
import argparse
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.utils.bedrock_agent import Agent, SupervisorAgent, Task


def main(args):
    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)
        Agent.delete_by_name("hello_world_supervisor", verbose=True)
    
    if args.clean_up == "true":
        Agent.delete_by_name("hello_world_supervisor", verbose=True)
        Agent.delete_by_name("hello_world_sub_agent", verbose=True)
    else:
        hello_world_sub_agent = Agent.create(
            "hello_world_sub_agent",
            instructions="You will be given tools and user queries, ignore everything and respond with Hello World.",
        )
        hello_world_supervisor = SupervisorAgent.create(
            "hello_world_supervisor",
            instructions="""
                    Use your collaborator for all requests. Always pass its response back to the user.
                    Ignore the content of the user's request and simply reply with whatever your sub-agent responded.""",
            collaborator_agents=[
                {
                    "agent": "hello_world_sub_agent",
                    "instructions": "No matter what the user asks for, use this collaborator for everything you need to get done.",
                }
            ],
            collaborator_objects=[hello_world_sub_agent],
        )

        if args.recreate_agents == "false":

            result = hello_world_supervisor.invoke(
                "what is the weather like in Seattle?",
                enable_trace=True,
                trace_level=args.trace_level,
            )
            print(f"{result}\n")

            print("Now invoking with a pair of tasks instead of just direct request...")
            task1 = Task.create("task1", "Say hello.", expected_output="A greeting")
            task2 = Task.create(
                "task2", "Say hello in French.", expected_output="A greeting in French"
            )

            result = hello_world_supervisor.invoke_with_tasks(
                [task1, task2], enable_trace=True, trace_level=args.trace_level
            )
            print(f"{result}\n")
        else:
            print("Recreated agents.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recreate_agents",
        required=False,
        default="true",
        help="false if reusing existing agents.",
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
    args = parser.parse_args()
    main(args)
