#!/usr/bin/env python

import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from utils.bedrock_agent import Agent, SupervisorAgent, Task, region, account_id, agents_helper
from utils.bedrock_agent_helper import AgentsForAmazonBedrock
import argparse
from datetime import datetime, timedelta
import time
import os
import argparse
import boto3
from textwrap import dedent

from utils.knowledge_base_helper import KnowledgeBasesForAmazonBedrock


import logging
import uuid
import re


kb_helper = KnowledgeBasesForAmazonBedrock()

s3_client = boto3.client('s3')
sts_client = boto3.client('sts')

logging.basicConfig(format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_directory(path, bucket_name):
        for root,dirs,files in os.walk(path):
            for file in files:
                file_to_upload = os.path.join(root,file)
                dest_key = f"{path}/{file}"
                print(f"uploading file {file_to_upload} to {bucket_name}")
                s3_client.upload_file(file_to_upload,bucket_name,dest_key)

def main(args):
    if args.clean_up == "true":
        Agent.set_force_recreate_default(True)
        agents_helper.delete_agent("mortgages_assistant", verbose=True)
        kb_helper.delete_kb("general-mortgage-kb", delete_s3_bucket=False)
        return
    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)
        agents_helper.delete_agent("mortgages_assistant", verbose=True)
        # kb_helper.delete_kb("general-mortgage-kb", delete_s3_bucket=False)

    uuid_nums = re.sub('[^0-9]', '', str(uuid.uuid4()))[:6]
    bucket_name = f"mortgages-assistant-{uuid_nums}"
    print("creating general KB")
    kb_name = "general-mortgage-kb"
    kb_id, ds_id = kb_helper.create_or_retrieve_knowledge_base(
        kb_name,
        kb_description="Useful for answering questions about mortgage refinancing and for questions comparing various mortgage types",
        data_bucket_name=bucket_name
        )
    print(f"KB name: {kb_name}, kb_id: {kb_id}, ds_id: {ds_id}\n")

    if args.recreate_agents == "true":
        print("uploading dir")
        upload_directory("mortgage_dataset", f"{bucket_name}")

        # ensure that the kb is available
        time.sleep(30)
        # sync knowledge base
        kb_helper.synchronize_data(kb_id, ds_id)
        print('KB sync completed\n')

    if args.agent_greeting == "true":
        general_mortgage_questions = Agent.direct_create(
                name="general_mortgage_questions",
                role="General Mortgage Questions",
                goal="Handle conversations about general mortgage questions, like high level concepts of refinincing or tradeoffs of 15-year vs 30-year terms.",
                instructions=dedent("""
                    You are a mortgage bot, and can answer questions about mortgage refinancing and tradeoffs of mortgage types. Greet the customer first. Respons to the greeting by another greeting """),
                kb_id=kb_id,
                kb_descr=dedent("""
            Use this knowledge base to answer general questions about mortgages, like how to refinnance, 
            or the difference between 15-year and 30-year mortgages."""),
                llm="mistral.mistral-large-2407-v1:0"
        )

        existing_mortgage_assistant = Agent.direct_create(
                                name="existing_mortgage_assistant",
                                role="Existing Mortgage Assistant",
                                goal="Handle conversations about existing mortgage accounts.",
                                instructions=dedent(""" 
    You are a mortgage bot,you greet the customer first and then you can retrieve the latest details about an existing mortgage on behalf of customers.
    When starting a new session, give them a friendly greeting using their preferred name 
    if you already have it.
    never ask the user for information that you already can retrieve yourself through 
    available actions. for example, you have actions to retrieve details about the 
    existing mortgage (interest rate, balance, number of payments, 
    mortgage maturity date, last payment date, next payment date, etc.). Always use your Code Interpreter to perform calculations on these details. Do not try any math without using code interpreter. Execute the code and give complete results
    
    do not engage with users about topics other than an existing mortgage and greetings. 
    leave those other topics for other experts to handle. 
    for example, do not respond to general questions about mortgages. However, respond to the greeting by another greeting
                                """),
                                tool_code="existing_mortgage_function.py",
                                tool_defs=[
                                        {
                                            "name": "get_mortgage_status",
                                            "description": dedent("""
    Retrieves the mortgage status for a given customer ID. Returns an object containing 
    details like the account number, 
    outstanding principal, interest rate, maturity date, number of payments remaining, due date of next payment, 
    and amount of next payment. If customer_id is not passed, function implementation
    can retrieve it from session state instead."""),
                                            "parameters": {
                                                "customer_id": {
                                                    "description": "[optional] The unique identifier for the customer whose mortgage status is being requested.",
                                                    "type": "string",
                                                    "required": False
                                                }
                                            }
                                        }
                                    ], 
                                llm="mistral.mistral-large-2407-v1:0"
                                )

        mortgage_application_agent = Agent.direct_create(
                                name="mortgage_application_agent",
                                role="Mortgage Application Agent",
                                goal="Handle conversations about applications for new mortgages.",
                                instructions=""" 
    you are a mortgage bot for creating, managing, and completing an application for a new mortgage. you greet the customer before your answer.
    you are also great at calculating mortgage payments using your built-in code interpreter to make 
    accurate calculations. You never try to do those calculations on your own, instead your code
    interpreter is there to generate the code to do the calculations.
    
    Use get_mortgage_rate_history
    Calculate averages and ranges programmatically using Python
    Never estimate rates manually
    
    you can help customers know what documentation they have already provided and which ones they still need to provide.
    Summarize all the document statuses when you get_app_doc_status and explain the status for each one
    
    never make up information that you are unable to retrieve from your available actions. 
    do not engage with users about topics other than an existing mortgage. leave those other topics for 
    other experts to handle. for example, do not respond to general questions about mortgages. However, respond to the greeting by another greeting
    """,
                                tool_code="mortgage_application_function.py",
                                tool_defs=[
                                    {
                                        "name": "get_mortgage_app_doc_status",
                                        "description": """
    Retrieves the list of required documents for a mortgage application in process, 
    along with their respective statuses (COMPLETED or MISSING). 
    The function takes a customer ID, but it is purely optional. The funciton
    implementation can retrieve it from session state instead.
    This function returns a list of objects, where each object represents 
    a required document type. 
    The required document types for a mortgage application are: proof of income, employment information, 
    proof of assets, and credit information. Each object in the returned list contains the type of the 
    required document and its corresponding status. """,
                                        "parameters": {
                                            "customer_id": {
                                                "description": """
                The unique identifier of the customer whose mortgage application document status is to be retrieved.""",
                                                "type": "string",
                                                "required": False
                                            }
                                        }
                                    },
                                    {
                                        "name": "get_application_details",
                                        "description": """
    Retrieves the details about an application for a new mortgage.
    The function takes a customer ID, but it is purely optional. The funciton
    implementation can retrieve it from session state instead. Details include
    the application ID, application date, application status, application type,
    application amount, application tentative rate, and application term in years. """,
                                        "parameters": {
                                            "customer_id": {
                                                "description": """
                The unique identifier of the customer whose mortgage application details is to be retrieved.""",
                                                "type": "string",
                                                "required": False
                                            }
                                        }
                                    },
                                    {
                                        "name": "get_mortgage_rate_history",
                                        "description": """
    Retrieves the history of mortgage interest rates going back a given number of days, defaults to 30.
    History is returned as a list of objects, where each object contains the date and the interest rate to 2 decimal places. """,
                                        "parameters": {
                                            "day_count": {
                                                "description": "The number of days of interest rate history, defaults to 30. Use 1 for latest rate.",
                                                "type": "string",
                                                "required": True
                                            },
                                            "type": {
                                                "description": "The type of mortgage, defaults to '30-year-fixed'. Can also be '15-year-fixed'",
                                                "type": "string",
                                                "required": False
                                            }
                                        }
                                    }
                                ],
                                llm="mistral.mistral-large-2407-v1:0",
                                code_interpreter=True, # lets us do mortgage calcs accurately
                                verbose=False
                                )
       
        mortgage_greeting_agent = Agent.direct_create(
                                name="mortgage_greeting_agent",
                                role="Mortgage Greeting Agent",
                                goal="Handle the start of the conversation by greeting customers.",
                                instructions=""" 
    you are a mortgage bot for greeting customer at the beginning of the chat. Reply back to the customers first message by greetings in the below XML tags
    <greetings>
    Hello!
    Hey!
    Good morning!
    Good Afternoon!
    Good  evening!
    </greetings>

    <greeting_instructions>
    <instruction_1>
    Make sure the greeting matches the time of the day
    </instruction_1>
    <instruction_2>
    Use the greeting followed by a simple question such as "How can I help you today>"
    </instruction_2>
    </greeting_instructions>
    """,
                                llm="mistral.mistral-large-2407-v1:0",
                                code_interpreter=True, # lets us do mortgage calcs accurately
                                verbose=False
                                )

        mortgages_assistant = SupervisorAgent.direct_create("mortgages_assistant", 
                                    role="Mortgages Assistant",
                                    goal="Provide a unified conversational experience for all things related to mortgages.",
                                    collaboration_type="SUPERVISOR_ROUTER",
                                    llm="mistral.mistral-large-2407-v1:0",
                                    instructions=dedent(f"""
        Act as a helpful mortgages assistant, allowing seamless conversations across a few
        different domains: current mortgages, new mortgage applications, and general mortgage knowledge.
        For general mortgage knowledge, you use the {kb_name} knowledge base.
        If asked for a complicated calculation, use your code interpreter to be sure it's done accurately."""),
                                    collaborator_agents=[ 
                                        {
                                            "agent": "existing_mortgage_assistant",
                                            "instructions": dedent("""
                        Do not pick this collaborator for general mortgage knowledge like guidance about refinancing, 
                        or tradeoffs between mortgage types. instead use the general-mortgage-kb knowledge base for those.
                        Use this collaborator for discussing existing mortgages."""),
                                        },
                                        {
                                            "agent": "mortgage_application_agent",
                                            "instructions": dedent("""
                        Do not pick this collaborator for general mortgage knowledge like guidance about refinancing, 
                        or tradeoffs between mortgage types. instead use the general-mortgage-kb knowledge base for those.
                        Do use this collaborator for discussing the application process for new mortgages
                        and for getting the most recent interest rates available for new mortgages."""),
                                        },
                                        {
                                            "agent": "mortgage_greeting_agent",
                                            "instructions": dedent("""
                        Use this collaborator for greeting customers at the start of the conversation."""),
                                        },
                                        {
                                            "agent": "general_mortgage_questions",
                                            "instructions": """
                                                Use this collaborator for discussing general mortgage questions."""
                                        }
                                    ],
                                    collaborator_objects=[mortgage_application_agent, existing_mortgage_assistant,
                                                        general_mortgage_questions,mortgage_greeting_agent],
                                    verbose=False)
    
    else:
        general_mortgage_questions = Agent.direct_create(
                name="general_mortgage_questions",
                role="General Mortgage Questions",
                goal="Handle conversations about general mortgage questions, like high level concepts of refinincing or tradeoffs of 15-year vs 30-year terms.",
                instructions=dedent("""
                    You are a mortgage bot, and can answer questions about mortgage refinancing and tradeoffs of mortgage types. Greet the customer first. Respons to the greeting by another greeting """),
                kb_id=kb_id,
                kb_descr=dedent("""
            Use this knowledge base to answer general questions about mortgages, like how to refinnance, 
            or the difference between 15-year and 30-year mortgages."""),
                llm="mistral.mistral-large-2407-v1:0"
        )

        existing_mortgage_assistant = Agent.direct_create(
                                name="existing_mortgage_assistant",
                                role="Existing Mortgage Assistant",
                                goal="Handle conversations about existing mortgage accounts.",
                                instructions=dedent(""" 
    You are a mortgage bot,you greet the customer first and then you can retrieve the latest details about an existing mortgage on behalf of customers.
    When starting a new session, give them a friendly greeting using their preferred name 
    if you already have it.
    never ask the user for information that you already can retrieve yourself through 
    available actions. for example, you have actions to retrieve details about the 
    existing mortgage (interest rate, balance, number of payments, 
    mortgage maturity date, last payment date, next payment date, etc.). Always use your Code Interpreter to perform calculations on these details. Do not try any math without using code interpreter. Execute the code and give complete results
    
    do not engage with users about topics other than an existing mortgage and greetings. 
    leave those other topics for other experts to handle. 
    for example, do not respond to general questions about mortgages. However, respond to the greeting by another greeting
                                """),
                                tool_code="existing_mortgage_function.py",
                                tool_defs=[
                                        {
                                            "name": "get_mortgage_status",
                                            "description": dedent("""
    Retrieves the mortgage status for a given customer ID. Returns an object containing 
    details like the account number, 
    outstanding principal, interest rate, maturity date, number of payments remaining, due date of next payment, 
    and amount of next payment. If customer_id is not passed, function implementation
    can retrieve it from session state instead."""),
                                            "parameters": {
                                                "customer_id": {
                                                    "description": "[optional] The unique identifier for the customer whose mortgage status is being requested.",
                                                    "type": "string",
                                                    "required": False
                                                }
                                            }
                                        }
                                    ], 
                                llm="mistral.mistral-large-2407-v1:0"
                                )

        mortgage_application_agent = Agent.direct_create(
                                name="mortgage_application_agent",
                                role="Mortgage Application Agent",
                                goal="Handle conversations about applications for new mortgages.",
                                instructions=""" 
    you are a mortgage bot for creating, managing, and completing an application for a new mortgage. you greet the customer before your answer.
    you are also great at calculating mortgage payments using your built-in code interpreter to make 
    accurate calculations. You never try to do those calculations on your own, instead your code
    interpreter is there to generate the code to do the calculations.
    
    Use get_mortgage_rate_history
    Calculate averages and ranges programmatically using Python
    Never estimate rates manually
    
    you can help customers know what documentation they have already provided and which ones they still need to provide.
    Summarize all the document statuses when you get_app_doc_status and explain the status for each one
    
    never make up information that you are unable to retrieve from your available actions. 
    do not engage with users about topics other than an existing mortgage. leave those other topics for 
    other experts to handle. for example, do not respond to general questions about mortgages. However, respond to the greeting by another greeting
    """,
                                tool_code="mortgage_application_function.py",
                                tool_defs=[
                                    {
                                        "name": "get_mortgage_app_doc_status",
                                        "description": """
    Retrieves the list of required documents for a mortgage application in process, 
    along with their respective statuses (COMPLETED or MISSING). 
    The function takes a customer ID, but it is purely optional. The funciton
    implementation can retrieve it from session state instead.
    This function returns a list of objects, where each object represents 
    a required document type. 
    The required document types for a mortgage application are: proof of income, employment information, 
    proof of assets, and credit information. Each object in the returned list contains the type of the 
    required document and its corresponding status. """,
                                        "parameters": {
                                            "customer_id": {
                                                "description": """
                The unique identifier of the customer whose mortgage application document status is to be retrieved.""",
                                                "type": "string",
                                                "required": False
                                            }
                                        }
                                    },
                                    {
                                        "name": "get_application_details",
                                        "description": """
    Retrieves the details about an application for a new mortgage.
    The function takes a customer ID, but it is purely optional. The funciton
    implementation can retrieve it from session state instead. Details include
    the application ID, application date, application status, application type,
    application amount, application tentative rate, and application term in years. """,
                                        "parameters": {
                                            "customer_id": {
                                                "description": """
                The unique identifier of the customer whose mortgage application details is to be retrieved.""",
                                                "type": "string",
                                                "required": False
                                            }
                                        }
                                    },
                                    {
                                        "name": "get_mortgage_rate_history",
                                        "description": """
    Retrieves the history of mortgage interest rates going back a given number of days, defaults to 30.
    History is returned as a list of objects, where each object contains the date and the interest rate to 2 decimal places. """,
                                        "parameters": {
                                            "day_count": {
                                                "description": "The number of days of interest rate history, defaults to 30. Use 1 for latest rate.",
                                                "type": "string",
                                                "required": True
                                            },
                                            "type": {
                                                "description": "The type of mortgage, defaults to '30-year-fixed'. Can also be '15-year-fixed'",
                                                "type": "string",
                                                "required": False
                                            }
                                        }
                                    }
                                ],
                                llm="mistral.mistral-large-2407-v1:0",
                                code_interpreter=True, # lets us do mortgage calcs accurately
                                verbose=False
                                )
       

        mortgages_assistant = SupervisorAgent.direct_create("mortgages_assistant", 
                                    role="Mortgages Assistant",
                                    goal="Provide a unified conversational experience for all things related to mortgages.",
                                    collaboration_type="SUPERVISOR_ROUTER",
                                    instructions=dedent(f"""
        Act as a helpful mortgages assistant, allowing seamless conversations across a few
        different domains: current mortgages, new mortgage applications, and general mortgage knowledge.
        For general mortgage knowledge, you use the {kb_name} knowledge base.
        If asked for a complicated calculation, use your code interpreter to be sure it's done accurately."""),
                                    collaborator_agents=[ 
                                        {
                                            "agent": "existing_mortgage_assistant",
                                            "instructions": dedent("""
                        Do not pick this collaborator for general mortgage knowledge like guidance about refinancing, 
                        or tradeoffs between mortgage types. instead use the general-mortgage-kb knowledge base for those.
                        Use this collaborator for discussing existing mortgages."""),
                                        },
                                        {
                                            "agent": "mortgage_application_agent",
                                            "instructions": dedent("""
                        Do not pick this collaborator for general mortgage knowledge like guidance about refinancing, 
                        or tradeoffs between mortgage types. instead use the general-mortgage-kb knowledge base for those.
                        Do use this collaborator for discussing the application process for new mortgages
                        and for getting the most recent interest rates available for new mortgages."""),
                                        },
                                        {
                                            "agent": "general_mortgage_questions",
                                            "instructions": """
                                                Use this collaborator for discussing general mortgage questions."""
                                        }
                                    ],
                                    collaborator_objects=[mortgage_application_agent, existing_mortgage_assistant,
                                                        general_mortgage_questions],
                                    llm="mistral.mistral-large-2407-v1:0",
                                    verbose=False)
        

    if args.recreate_agents == "false":
        print("\n\nInvoking supervisor agent...\n\n")

        session_id = str(uuid.uuid4())

        requests = ["when’s my next payment due?",
                    "what’s my balance after that payment, and what rate am I paying?",
                    "why do so many people choose a 30-year mortgage??",
                    "did you receive my employment verification doc yet? i sent it last week",
                    "i’m getting ready to lock in on a rate. what have the rates looked like in last couple weeks?",
                    # "great. if i use the highest of those rates for $500K for 15 years, what’s my payment?"
        ]


        for request in requests:
            print(f"\n\nRequest: {request}\n\n")
            result = mortgages_assistant.invoke(request, session_id=session_id, 
                                                enable_trace=True, trace_level=args.trace_level)
            print(result)

if __name__ == '__main__':
    print("in main")
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_greeting", required=False, default=False, help="False does NOT create greeting Agent")
    parser.add_argument("--recreate_agents", required=False, default=True, help="False if reusing existing agents.")
    parser.add_argument("--clean_up", required=False, default=False, help="True if cleaning up agents resources.")
    parser.add_argument("--trace_level", required=False, default="core", help="The level of trace, 'core', 'outline', 'all'.")

    args = parser.parse_args()
    main(args)

