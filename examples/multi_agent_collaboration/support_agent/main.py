#!/usr/bin/env python

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.bedrock_agent import Agent, SupervisorAgent, Task, region, account_id, agents_helper
from src.utils.bedrock_agent_helper import AgentsForAmazonBedrock

import argparse
from datetime import datetime, timedelta
import time
import os
import argparse
import boto3
from textwrap import dedent

from src.utils.knowledge_base_helper import KnowledgeBasesForAmazonBedrock
from knowledge_base_confluence_helper import ConfluenceKnowledgeBasesForAmazonBedrock
from knowledge_base_webcrawler_helper import WebCrawlerKnowledgeBasesForAmazonBedrock


import logging
import uuid
import uuid

kb_helper = ConfluenceKnowledgeBasesForAmazonBedrock()
kb_wc_helper = WebCrawlerKnowledgeBasesForAmazonBedrock()

s3_client = boto3.client('s3')
sts_client = boto3.client('sts')

logging.basicConfig(format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)



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
    

    bucket_name = None
    confluence_url = args.confluence_url
    username = args.username
    print(username)
    password = args.token
    print(password)
    auth_type = "BASIC"
 
    confluence_space_key = kb_helper.create_confluence_credentials_secret(secret_name="Bedrock-Confluence-Secret",username=args.username,password=args.token ,auth_type = "BASIC")
    print(confluence_space_key)
    secret_arn = confluence_space_key['ARN']
    print(secret_arn)


    print("creating Jira KB")
    kb_name = "jira-support-agent"
    
    kb_confluence_id, ds_confluence_id = kb_helper.create_or_retrieve_confluence_knowledge_base(
        kb_name,
        kb_description="Useful for answering questions about Jira tasks",
        confluence_url=confluence_url,
        secret_arn=secret_arn
        )
    print(f"KB name: {kb_name}, kb_confluence_id: {kb_confluence_id}, ds_id: {ds_confluence_id}\n")


    print("Creation Github KB")
    kb_name = "github-agent"
    Github_URL = "https://docs.github.com/en/actions"
    kb_github_id, ds_github_id = kb_wc_helper.create_or_retrieve_webcrawler_knowledge_base(
        kb_name,
        kb_description="Useful for answering questions about Github tasks",
        URL=Github_URL
        )
    print(f"KB name: {kb_name}, kb_github_id: {kb_github_id}, ds_id: {ds_github_id}\n")


    

    if args.recreate_agents == "true":

        # ensure that the kb is available
        time.sleep(30)
        # sync knowledge base
        kb_helper.synchronize_data(kb_confluence_id, ds_confluence_id)
        kb_wc_helper.synchronize_data(kb_github_id, ds_github_id)
        print('KB sync completed\n')

    if args.agent_greeting == "true":
        JIRA_questions = Agent.create(
                name="JIRA_questions",
                role="JIRA related questions",
                goal="Handle conversations about the Jira domain.",
                instructions=dedent("""
                    You are a support agent bot. You are should answer based on the ingested JIRA tasks. You can retrieve details about the existing tasks according to the questions and return back to the user.
                     if you already have it.
    never ask the user for information that you already can retrieve yourself through 
    available actions. for example, you have actions to retrieve details about a 
    JIRA task.
    do not engage with users about topics other than an JIRA tasks and greetings. 
    leave those other topics for other experts to handle. 
    for example, do not respond to general questions about coding. However, respond to the greeting by another greeting               """),
                kb_id=kb_confluence_id,
                kb_descr=dedent("""
            Use this knowledge base to answer general questions about JIRA tasks"""),
                llm="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

        Github_questions = Agent.create(
                name="Github_questions",
                role="Github related questions",
                goal="Handle conversations about the Github.",
                instructions=dedent("""
                    You are a support agent bot. You are should answer based on Github issues. You can retrieve details about the existing tasks according to the questions and return back to the user.
                     if you already have it.
    never ask the user for information that you already can retrieve yourself through 
    available actions. for example, you have actions to retrieve details about an
    issue from Github's documentation.
    do not engage with users about topics other than an Github issues and greetings. 
    leave those other topics for other experts to handle. 
    for example, do not respond to general questions about coding. However, respond to the greeting by another greeting               """),
                kb_id=kb_github_id,
                kb_descr=dedent("""
            Use this knowledge base to answer general questions about Github issues"""),
                llm="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

        
       
        support_greeting_agent = Agent.create(
                                name="support_greeting_agent",
                                role="Support Greeting Agent",
                                goal="Handle the start of the conversation by greeting customers.",
                                instructions=""" 
    you are a Support Agent bot for greeting customer at the beginning of the chat. Reply back to the customers first message by greetings in the below XML tags
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
                                llm="anthropic.claude-3-5-haiku-20241022-v1:0",
                                code_interpreter=True, # lets us do mortgage calcs accurately
                                verbose=False
                                )

        support_assistant = SupervisorAgent.create("support_assistant", 
                                    role="Support Assistant",
                                    goal="Provide a unified conversational experience for all things related to mortgages.",
                                    collaboration_type="SUPERVISOR_ROUTER",
                                    instructions=dedent(f"""
        Act as a helpful support assistant, allowing seamless conversations across a few
        different domains:  greeting agents and JIRA knowledge.
        For Jira  knowledge, you use the {kb_name} knowledge base.
        If asked for a complicated calculation, use your code interpreter to be sure it's done accurately."""),
                                    collaborator_agents=[ 
                                        {
                                            "agent": "JIRA_questions",
                                            "instructions": dedent("""
                        Do not pick this collaborator for general  knowledge like guidance about coding, 
                        or tradeoffs between code questions. """),
                                        },
                                        
                                        {
                                            "agent": "support_greeting_agent",
                                            "instructions": dedent("""
                        Use this collaborator for greeting customers at the start of the conversation."""),
                                        },
                                        {
                                            "agent": "Github_questions",
                                            "instructions": dedent("""
                        Use this collaborator to answer Github related questions."""),
                                        }
                                    ],
                                    collaborator_objects=[JIRA_questions, support_greeting_agent, Github_questions
                                                        ],
                                    llm="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                                    verbose=True)
    
   
    if args.recreate_agents == "false":
        print("\n\nInvoking supervisor agent...\n\n")

        session_id = str(uuid.uuid4())

        requests = ["How to create Github issue?",
        ]

        for request in requests:
            print(f"\n\nRequest: {request}\n\n")
            result = support_assistant.invoke(request, session_id=session_id, 
                                                enable_trace=True, trace_level=args.trace_level)
            print(result)

if __name__ == '__main__':
    print("in main")
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_greeting", required=False, default=False, help="Default does NOT create greeting Agent")
    parser.add_argument("--recreate_agents", required=False, default=True, help="False if reusing existing agents.")
    parser.add_argument("--clean_up", required=False, default=False, help="True if cleaning up agents resources.")
    parser.add_argument("--trace_level", required=False, default="core", help="The level of trace, 'core', 'outline', 'all'.")
    parser.add_argument("--confluence_url", required=True, default="None", help="Confluence URL to connect to")
    parser.add_argument("--username", required=True, default="None", help="Confluence username to connect to")
    parser.add_argument("--token", required=True, default="None", help="Confluence token to connect to")


    args = parser.parse_args()
    main(args)

