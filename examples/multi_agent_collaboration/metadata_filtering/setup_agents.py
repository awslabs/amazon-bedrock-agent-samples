import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

import boto3
import json
import time
import os
from botocore.exceptions import ClientError
from src.utils.knowledge_base_helper import KnowledgeBasesForAmazonBedrock
import yaml

class BedrockAgentSetup:
    def __init__(self, bucket_name, account_id):
        boto3_session = boto3.session.Session()
        self.bucket_name = bucket_name
        self.account_id = account_id
        self.region = boto3_session.region_name
        self.bedrock = boto3.client('bedrock')
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.s3 = boto3.client('s3')
        self.lambda_client = boto3.client('lambda')
        self.iam = boto3.client('iam')
        self.kb_helper = KnowledgeBasesForAmazonBedrock()

    def create_knowledge_base(self):
        """Create a Knowledge Base using the specified S3 bucket"""
        try:
            kb_id, ds_id = self.kb_helper.create_or_retrieve_knowledge_base(
                kb_name='kb-metadatafiltering',
                kb_description='Knowledge base for shareholder letters',
                data_bucket_name=self.bucket_name,
                embedding_model='amazon.titan-embed-text-v2:0'
            )
            print(f"Knowledge Base created: {kb_id}")
            if kb_id and ds_id:
                print(f"Starting KB ingestion job")
                print(f"-----------------------------")
                response = self.kb_helper.synchronize_data(kb_id, ds_id)            
            print(f"Knowledge Base Synced: {kb_id}")
            return kb_id
                
        except Exception as e:
            print(f"Error creating knowledge base: {str(e)}")

            raise
     

    def wait_agent_status_update(self, agent_id):
        response = self.bedrockPagent.get_agent(agentId=agent_id)
        agent_status = response["agent"]["agentStatus"]
        _waited_at_least_once = False
        while agent_status.endswith("ING"):
            print(f"Waiting for agent status to change. Current status {agent_status}")
            time.sleep(5)
            _waited_at_least_once = True
            try:
                response = self.bedrockPagent.get_agent(agentId=agent_id)
                agent_status = response["agent"]["agentStatus"]
            except self.bedrockPagent.exceptions.ResourceNotFoundException:
                agent_status = "DELETED"
        if _waited_at_least_once:
            print(f"Agent id {agent_id} current status: {agent_status}")


    def _create_lambda_role(self):
        """Create IAM role for Lambda function"""
        try:
            role_name = 'BedrockAgentLambdaRole'
            
            # Check if role exists
            try:
                existing_role = self.iam.get_role(RoleName=role_name)
                print(f"Role {role_name} already exists, updating policies...")
                return existing_role['Role']['Arn']
            except self.iam.exceptions.NoSuchEntityException:
                # Create new role if it doesn't exist
                trust_policy = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }]
                }
                
                # Create the role
                role = self.iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy)
                )
                
                # Attach necessary policies
                policies = [
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                    'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
                    'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess'
                ]
                
                for policy_arn in policies:
                    self.iam.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy_arn
                    )
                
                # Add inline policy for Bedrock Agent access
                inline_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "bedrock:InvokeModel",
                                "bedrock-agent:*"
                            ],
                            "Resource": "*"
                        }
                    ]
                }
                
                self.iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName='BedrockAgentAccess',
                    PolicyDocument=json.dumps(inline_policy)
                )
                
                # Wait for role to be available
                print("Waiting for role to be available...")
                time.sleep(10)
                
                return role['Role']['Arn']
                
        except Exception as e:
            print(f"Error creating Lambda role: {str(e)}")
            raise
    
    def add_lambda_resource_policy(self, function_name):
        """Add resource-based policy to allow Bedrock agents to invoke the Lambda function"""
        try:
            # Create the policy statement
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowBedrockAgentInvoke",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "bedrock.amazonaws.com"
                        },
                        "Action": "lambda:InvokeFunction",
                        "Resource": f"arn:aws:lambda:{self.region}:{self.account_id}:function:{function_name}",
                        "Condition": {
                            "StringEquals": {
                                "AWS:SourceAccount": self.account_id
                            },
                            "ArnLike": {
                                "AWS:SourceArn": f"arn:aws:bedrock:{self.region}:{self.account_id}:agent/*"
                            }
                        }
                    }
                ]
            }

            # Add the resource-based policy to the Lambda function
            response = self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId="BedrockAgentInvoke",
                Action="lambda:InvokeFunction",
                Principal="bedrock.amazonaws.com",
                SourceAccount=self.account_id,
                SourceArn=f"arn:aws:bedrock:{self.region}:{self.account_id}:agent/*"
            )
            
            print(f"Added resource-based policy to Lambda function: {function_name}")
            return response

        except self.lambda_client.exceptions.ResourceConflictException:
            print(f"Resource-based policy already exists for function: {function_name}")
        except Exception as e:
            print(f"Error adding resource-based policy: {str(e)}")
            raise



    def create_lambda_function(self, kb_id):
        """Create Lambda function with dynamic document filtering"""
        import io
        import zipfile
        function_name = "BedrockAgentHandler"
        
        # Create Lambda role
        role_arn = self._create_lambda_role()
        
        # Create a ZIP file containing the Lambda function code
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the Lambda function code to the ZIP file
            zip_file.writestr('lambda_function.py', self._get_lambda_code().decode('utf-8'))
        
        zip_buffer.seek(0)
        
        try:
            # Try to get the function first
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                print("Lambda function already exists, updating code...")
                
                # Update the existing function
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_buffer.read()
                )
            except self.lambda_client.exceptions.ResourceNotFoundException:
                print("Creating new Lambda function...")
                # Create new function
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.11',
                    Role=role_arn,
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_buffer.read()},
                    Environment={
                        'Variables': {
                            'KNOWLEDGE_BASE_ID': kb_id,
                            'MODEL_ID': 'us.anthropic.claude-3-5-haiku-20241022-v1:0',
                            'S3_BUCKET': self.bucket_name,
                            'AWSREGION': self.region
                        }
                    },
                    Timeout=900,
                    MemorySize=256,
                    Publish=True
                )
                
                # Wait for the function to be active
                print("Waiting for function to be active...")
                waiter = self.lambda_client.get_waiter('function_active')
                waiter.wait(FunctionName='BedrockAgentHandler')
            
            ## Adding Lambda Resource Policy
            self.add_lambda_resource_policy(function_name)
            
            return response['FunctionArn']
            
        except Exception as e:
            print(f"Error creating Lambda function: {str(e)}")
            raise
    

    def _create_agent_role(self):
        """Create IAM role for Bedrock Agent"""
        try:
            role_name = 'BedrockAgentRole'
            
            # Check if role exists
            try:
                existing_role = self.iam.get_role(RoleName=role_name)
                print(f"Role {role_name} already exists, updating policies...")
                return existing_role['Role']['Arn']
            except self.iam.exceptions.NoSuchEntityException:
                # Create new role if it doesn't exist
                trust_policy = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "bedrock.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }]
                }
                
                # Create the role
                role = self.iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="Role for Bedrock Agent to access Lambda and Knowledge Base"
                )
                
                # Create inline policy for Lambda and Knowledge Base access
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "lambda:InvokeFunction"
                            ],
                            "Resource": [
                                f"arn:aws:lambda:{self.region}:{self.account_id}:function:BedrockAgentHandler"
                            ]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "bedrock:InvokeModel",
                                "bedrock-agent-runtime:*",
                                "bedrock:*"
                            ],
                            "Resource": "*"
                        }
                    ]
                }
                
                # Attach inline policy
                self.iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName='BedrockAgentPolicy',
                    PolicyDocument=json.dumps(policy)
                )
                
                # Wait for role to be available
                print("Waiting for agent role to be available...")
                time.sleep(10)
                
                return role['Role']['Arn']
                
        except Exception as e:
            print(f"Error creating agent role: {str(e)}")
            raise

    def associate_sub_agents(self, supervisor_agent_id, sub_agents_list):
        for sub_agent in sub_agents_list:
            association_response = (
                self.bedrock_agent.associate_agent_collaborator(
                    agentId=supervisor_agent_id,
                    agentVersion="DRAFT",
                    agentDescriptor={"aliasArn": sub_agent["sub_agent_alias_arn"]},
                    collaboratorName=sub_agent["sub_agent_association_name"],
                    collaborationInstruction=sub_agent["sub_agent_instruction"],
                    relayConversationHistory=sub_agent["relay_conversation_history"],
                )
            )
        # Waiting a minute to make sure the collaborators are attached to the supervisor agent
        time.sleep(60)    
        self.bedrock_agent.prepare_agent(agentId=supervisor_agent_id)   

        # Waiting a minute to make srue the supervisor agent is prepared
        time.sleep(60)
        supervisor_agent_alias = self.bedrock_agent.create_agent_alias(
            agentAliasName="multi-agent-metadatafilter", agentId=supervisor_agent_id
        )

        # Sleeping 10 seconds till the alias is created
        time.sleep(10)
        supervisor_agent_alias_id = supervisor_agent_alias["agentAlias"]["agentAliasId"]
        supervisor_agent_alias_arn = supervisor_agent_alias["agentAlias"][
            "agentAliasArn"
        ]
        return supervisor_agent_alias_id, supervisor_agent_alias_arn



    def create_agents(self, lambda_arn,kb_id):
        """Create orchestrator and sub-agents"""
        _sub_agent_list = []
        try:
            # Create sub-agents
            print(f"Creating Agent 1")
            agent1 = self._create_sub_agent('Agent1', 'You are an agent responsible for answering questions ONLY about the 2020 shareholder letter. If a question is not about 2020, respond with "I can only answer questions about the 2020 shareholder letter. Please rephrase your question to focus on 2020."', lambda_arn)  
            print(f"Agent 1 is created! {agent1['agent']['agentId']}") 
            print(f"----------------------------------------------")

            # Prepare Agent 1
            print(f"Preparing Agent1")
            agent1_resp = self.bedrock_agent.prepare_agent(agentId=agent1['agent']['agentId'])
            time.sleep(30)
            agent1_alias = self.bedrock_agent.create_agent_alias(agentAliasName="agent1-metadatafilter", agentId=agent1['agent']['agentId'])
            agent1_alias_id = agent1_alias["agentAlias"]["agentAliasId"]
            agent1_alias_arn = agent1_alias["agentAlias"]["agentAliasArn"]
            _sub_agent_list.append(
                {
                    "sub_agent_alias_arn": agent1_alias_arn,
                    "sub_agent_instruction": agent1["agent"]["instruction"],
                    "sub_agent_association_name": agent1["agent"]["agentName"],
                    "relay_conversation_history": "DISABLED",  #'TO_COLLABORATOR'
                }
            )      
            agent2 = self._create_sub_agent('Agent2', 'You are an agent responsible for answering questions ONLY about the 2023 shareholder letter. If a question is not about 2023, respond with "I can only answer questions about the 2023 shareholder letter. Please rephrase your question to focus on 2023."', lambda_arn)
            print(f"Preparing Agent2")
            agent2_resp = self.bedrock_agent.prepare_agent(agentId=agent2['agent']['agentId'])
            time.sleep(30)
            agent2_alias = self.bedrock_agent.create_agent_alias(agentAliasName="agent2-metadatafilter", agentId=agent2['agent']['agentId'])
            agent2_alias_id = agent2_alias["agentAlias"]["agentAliasId"]
            agent2_alias_arn = agent2_alias["agentAlias"]["agentAliasArn"]
            _sub_agent_list.append(
                {
                    "sub_agent_alias_arn": agent2_alias_arn,
                    "sub_agent_instruction": agent2["agent"]["instruction"],
                    "sub_agent_association_name": agent2["agent"]["agentName"],
                    "relay_conversation_history": "DISABLED",  #'TO_COLLABORATOR'
                }
            )
            
            modelId='us.anthropic.claude-3-5-haiku-20241022-v1:0'
            

            # Create orchestrator agent
            orchestrator = self.bedrock_agent.create_agent(
                agentName='OrchestratorAgent2',
                agentResourceRoleArn=self._create_agent_role(),
                instruction='''You are an orchestrator agent that routes queries to appropriate sub-agents.
                Route queries about 2020 documents to Agent1 and 2023 documents to Agent2.''',
                foundationModel=f"arn:aws:bedrock:{self.region}:166827918465:inference-profile/{modelId}",
                idleSessionTTLInSeconds=1800,
                agentCollaboration="SUPERVISOR_ROUTER"
            )
            time.sleep(60)
            print(f"Preparing Orchestrator")
            supervistor_info = self.associate_sub_agents(orchestrator['agent']['agentId'], _sub_agent_list)
            #orch_resp = self.bedrock_agent.prepare_agent(agentId=orchestrator['agent']['agentId'])
            time.sleep(45)

            self.lambda_client.update_function_configuration(
                FunctionName="BedrockAgentHandler",
                Environment={
                    'Variables': {
                        'KNOWLEDGE_BASE_ID': kb_id,
                        'MODEL_ID': 'us.anthropic.claude-3-5-haiku-20241022-v1:0',
                        'AGENT1_ID': agent1['agent']['agentId'],
                        'AGENT2_ID': agent2['agent']['agentId'],
                        'DOC_2020': 'AMZN-2020-Shareholder-Letter.pdf',
                        'DOC_2023': 'Amazon-com-Inc-2023-Shareholder-Letter.pdf',
                        'AWSREGION': self.region
                    }
                }
            )

            return {
                'orchestrator': orchestrator['agent']['agentId'],
                'orchestrator_alias': supervistor_info[0],
                'agent1': agent1['agent']['agentId'],
                'agent2': agent2['agent']['agentId']
            }
        except ClientError as e:
            print(f"Error creating agents: {str(e)}")
            raise

    def _create_sub_agent(self, name, description, lambda_arn):
        try:
            modelId='us.anthropic.claude-3-5-haiku-20241022-v1:0'
            # Create the agent first
            agent = self.bedrock_agent.create_agent(
                agentName=name,
                agentResourceRoleArn=self._create_agent_role(),
                instruction=description,
                foundationModel=f"arn:aws:bedrock:{self.region}:166827918465:inference-profile/{modelId}",
                idleSessionTTLInSeconds=1800
            )

            print(f"Created agent: {name}")
            
            # Wait for agent to be available
            print(f"Waiting for agent {name} to be available...")
            time.sleep(10)

            # Read the OpenAPI schema from file
            with open('openapi_schema.yaml', 'r') as file:
                schema = yaml.safe_load(file)

            # Create action group for the agent
            action_group = self.bedrock_agent.create_agent_action_group(
                agentId=agent['agent']['agentId'],
                agentVersion='DRAFT',
                actionGroupName='QueryKnowledgeBase',
                actionGroupExecutor={
                    'lambda': lambda_arn
                },
                apiSchema={
                    'payload': json.dumps(schema)
                },
                actionGroupState='ENABLED'
            )

            print(f"Created action group for agent: {name}")
            return agent

        except Exception as e:
            print(f"Error creating sub-agent {name}: {str(e)}")
            raise


    @staticmethod
    def _get_lambda_code():
        """Return the Lambda function code with dynamic document filtering"""
        return '''
import json
import boto3
import os
import logging
from botocore.exceptions import ClientError

# Configure proper logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler that processes queries from a Bedrock Agent and invokes 
    Bedrock Knowledge Base retrieveAndGenerate API with document filters.
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    try:
        # Extract action inputs based on Bedrock Agent structure
        request_body = event.get('requestBody', {})
        content = request_body.get('content', {}).get('application/json', {})
        agent = event.get('agent', {})
        logger.info(f"Agent data: {agent}")
        
        agent_id = agent.get('id')
        logger.info(f"Agent ID: {agent_id}")
        logger.info(f"Content: {content}")
        # Extract query from the request
        query = event.get('inputText')
        logger.info(f"Query: {query}")
        
        if agent_id == os.environ.get('AGENT1_ID'):
            # Hardcoded document filter (can be made dynamic)
            document_id = 'AMZN-2020-Shareholder-Letter.pdf'
        elif agent_id == os.environ.get('AGENT2_ID',):
            document_id = 'Amazon-com-Inc-2023-Shareholder-Letter.pdf'
        else:
            document_id = ''
        
        logger.info(f"Using document ID: {document_id}")
        
        # Optional session tracking
        session_id = content.get('session_id')
        
        if not query:
            logger.warning("Missing required parameter: query")
            return format_agent_response(
                event,
                400,
                {"error": "Missing required parameter: query"}
            )
        
        # Get configuration from environment variables
        knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID', "PHE22GQXYJ")
        model_id = os.environ.get('MODEL_ID', 'us.anthropic.claude-3-5-haiku-20241022-v1:0')
        region = os.environ.get('AWSREGION')
        
        # Initialize Bedrock Knowledge Bases client
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        
        # Prepare retrieval configuration
        retrieval_config = {
            'vectorSearchConfiguration': {
                'overrideSearchType': 'HYBRID'
            }
        }
        
        # Add document filter if specified
        if document_id:
            retrieval_config['vectorSearchConfiguration']['filter'] = {
                'equals': {
                    'key': 'DocumentId', 
                    'value': document_id
                }
            }
        
        # Call the retrieveAndGenerate API
        retrieve_args = {
            'input': {
                'text': query
            },
            'retrieveAndGenerateConfiguration': {
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': f"arn:aws:bedrock:{region}:166827918465:inference-profile/{model_id}",
                    'retrievalConfiguration': retrieval_config
                }
            }
        }
        
        # Add session ID if provided
        if session_id:
            retrieve_args['sessionId'] = session_id
            
        logger.info(f"Calling bedrock-agent-runtime with args: {json.dumps(retrieve_args, default=str)}")
        response = bedrock_agent_runtime.retrieve_and_generate(**retrieve_args)
        logger.info(f"Response from knowledge base: {json.dumps(response, default=str)}")
        
        # Safety check before accessing nested properties
        if 'output' not in response or 'text' not in response.get('output', {}):
            logger.error(f"Unexpected response structure: {response}")
            return format_agent_response(
                event, 
                500, 
                {"error": "Invalid response structure from knowledge base"}
            )
        
        # Extract the generated answer
        answer = response['output']['text']
        logger.info(f"Answer from knowledge base: {answer}")
        
        # Format response according to the OpenAPI schema
        result = {
            'answer': answer,
            'citations': []
        }
        
        # Process citations if available
        if 'citations' in response:
            for citation in response.get('citations', []):
                # Get first reference if available
                if citation.get('retrievedReferences'):
                    ref = citation['retrievedReferences'][0]
                    location = ref.get('location', {}).get('s3Location', {}).get('uri', '')
                    
                    # Format according to API schema
                    result['citations'].append({
                        'text': citation.get('generatedResponsePart', {}).get('text', ''),
                        'document_id': ref.get('documentAttributes', {}).get('DocumentID', ''),
                        'location': location
                    })
        
        # Return success response formatted for Bedrock Agent
        logger.info(f"Returning result: {json.dumps(result, default=str)}")
        return format_agent_response(event, 200, result)
        
    except ClientError as e:
        logger.error(f"Bedrock API error: {str(e)}", exc_info=True)
        return format_agent_response(
            event,
            500,
            {"error": str(e), "message": "Error in Bedrock Knowledge Base API call"}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return format_agent_response(
            event,
            500,
            {"error": str(e), "message": "Failed to process query or retrieve information"}
        )

def format_agent_response(event, status_code, body):
    """
    Format the response according to the Bedrock Agent Lambda function response structure
    """
    # FIX: Don't serialize body to JSON string - pass the object directly
    response_body = {
        'application/json': body
    }
    
    action_response = {
        'actionGroup': event.get('actionGroup'),
        'apiPath': event.get('apiPath'),
        'httpMethod': event.get('httpMethod'),
        'httpStatusCode': status_code,
        'responseBody': response_body
    }
    
    response = {
        'messageVersion': '1.0',
        'response': action_response,
        'sessionAttributes': event.get('sessionAttributes', {}),
        'promptSessionAttributes': event.get('promptSessionAttributes', {})
    }
    
    logger.info(f"Final response structure: {json.dumps(response, default=str)}")
    return response
    '''.encode('utf-8')

    @staticmethod
    def _get_openapi_schema():
        """Return the OpenAPI schema for the Knowledge Base Retrieval API"""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Knowledge Base Retrieval API",
                "version": "1.0.0",
                "description": "API for retrieving information from a knowledge base with document filtering"
            },
            "paths": {
                "/retrieveKnowledge": {
                    "post": {
                        "summary": "Retrieve and generate content from the knowledge base and return citations",
                        "description": "Retrieve and generate content from the knowledge base and return citations",
                        "operationId": "retrieveKnowledge",
                        "parameters": [
                            {
                                "name": "include_citations",
                                "in": "query",
                                "description": "Flag to include citations when generating responses",
                                "required": False,
                                "schema": {
                                    "type": "boolean",
                                    "default": True
                                }
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "description": "The user's query to search for in the knowledge base"
                                            },
                                            "document_id": {
                                                "type": "string",
                                                "description": "Optional filter to retrieve from a specific document"
                                            },
                                            "session_id": {
                                                "type": "string",
                                                "description": "Optional session ID for maintaining context across requests"
                                            }
                                        },
                                        "required": ["query"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Successful retrieval and generation",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "answer": {
                                                    "type": "string",
                                                    "description": "Generated answer based on retrieved content"
                                                },
                                                "citations": {
                                                    "type": "array",
                                                    "description": "Citations MUST be included in responses to the user",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "text": {
                                                                "type": "string"
                                                            },
                                                            "document_id": {
                                                                "type": "string"
                                                            },
                                                            "location": {
                                                                "type": "string"
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        "examples": {
                                            "response_with_citations": {
                                                "value": {
                                                    "answer": "The product launched in 2022.",
                                                    "citations": [
                                                        {
                                                            "text": "Our flagship product was launched in Q3 2022.",
                                                            "document_id": "annual-report-2022",
                                                            "location": "s3://company-docs/reports/annual-2022.pdf"
                                                        }
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    




def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Setup Bedrock Agents with Knowledge Base')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--account-id', required=True, help='AWS account ID')
    args = parser.parse_args()
   
    # Initialize setup
    setup = BedrockAgentSetup(args.bucket, args.account_id)
    
    # Create resources
    kb_id = setup.create_knowledge_base()
    lambda_arn = setup.create_lambda_function(kb_id)
    agents = setup.create_agents(lambda_arn,kb_id)

    # Print setup information
    print("\nSetup completed successfully!")
    print(f"Knowledge Base ID: {kb_id}")
    print(f"Lambda Function ARN: {lambda_arn}")
    print("Agent IDs:")
    print(f"  Orchestrator: {agents['orchestrator']}")
    print(f" Orchestrator Alias ID: {agents['orchestrator_alias']}")
    print(f"  Agent1: {agents['agent1']}")
    print(f"  Agent2: {agents['agent2']}")

if __name__ == '__main__':
    main()
