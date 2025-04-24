import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

import boto3
import json
import time
import os
import argparse
from botocore.exceptions import ClientError
from src.utils.knowledge_base_helper import KnowledgeBasesForAmazonBedrock

class BedrockAgentCleanup:
    def __init__(self, bucket_name, account_id,delete_bucket):
        boto3_session = boto3.session.Session()
        self.region = boto3_session.region_name
        print(f"the region we're working in is {self.region}")
        self.bucket_name = bucket_name
        self.account_id = account_id 
        self.delete_bucket = delete_bucket
        self.bedrock = boto3.client('bedrock')
        self.bedrock_agent = boto3.client('bedrock-agent',self.region)
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime',self.region)
        self.lambda_client = boto3.client('lambda',self.region)
        self.iam = boto3.client('iam',self.region)
        self.kb_helper = KnowledgeBasesForAmazonBedrock()
    
    def find_any_orchestrator_agent(self):
        """Find any agent that's using Agent1 or Agent2 as collaborators"""
        print("Looking for any agent using Agent1 or Agent2 as collaborators...")
        try:
            # Get a list of all agents
            response = self.bedrock_agent.list_agents(maxResults=1000)
        
            
            # Look for agents that might be orchestrators
            for agent in response.get('agentSummaries', []):
                agent_id = agent['agentId']
                agent_name = agent['agentName']
                print(f"Agent name is {agent_name}")
                print(f"Agent ID is {agent_id}")
                print("*******************")
                
                # Skip our known sub-agents
                if agent_name == 'Agent1' or agent_name == 'Agent2':
                    continue
                    
                print(f"Checking agent: {agent_name} ({agent_id})...")
                
                # Check all versions
                versions = self.find_all_versions(agent_id)
                
                has_collaborators = False
                
                # Check each version for collaborators
                for version in versions:
                    try:
                        collab_response = self.bedrock_agent.list_agent_collaborators(
                            agentId=agent_id,
                            agentVersion=version
                        )
                        
                        for collab in collab_response.get('collaboratorSummaries', []):
                            if collab['collaboratorName'] == 'Agent1' or collab['collaboratorName'] == 'Agent2':
                                has_collaborators = True
                                print(f"Found orchestrator: {agent_name} ({agent_id}) - using {collab['collaboratorName']} as collaborator")
                    except Exception as e:
                        print(f"Error checking collaborators for {agent_name}: {str(e)}")
                
                if has_collaborators:
                    return {
                        'id': agent_id,
                        'name': agent_name
                    }
                    
            print("No orchestrator agents found using Agent1 or Agent2 as collaborators.")
            return None
        
        except Exception as e:
            print(f"Error finding orchestrator agent: {str(e)}")
            return None
    
    def find_specific_agents(self):
        """Find the three specific agents we want to delete"""
        orchestrator_agent = None
        sub_agents = []
        
        try:
            # Find all agents to search through
            response = self.bedrock_agent.list_agents()
            
            # Identify our specific agents by name
            for agent in response.get('agentSummaries', []):
                print(f"Checking agent: {agent['agentName']} ({agent['agentId']})")
                if agent['agentName'] == 'OrchestratorAgent2':
                    # This is our orchestrator
                    orchestrator_agent = {
                        'id': agent['agentId'],
                        'name': agent['agentName']
                    }
                    print(f"Found orchestrator agent: {agent['agentName']} ({agent['agentId']})")
                elif agent['agentName'] == 'Agent1' or agent['agentName'] == 'Agent2':
                    # These are our sub-agents
                    sub_agents.append({
                        'id': agent['agentId'],
                        'name': agent['agentName']
                    })
                    print(f"Found sub-agent: {agent['agentName']} ({agent['agentId']})")
            
            return orchestrator_agent, sub_agents
            
        except Exception as e:
            print(f"Error finding agents: {str(e)}")
            return None, []
            
    def find_all_versions(self, agent_id):
        """Find all versions of an agent"""
        try:
            response = self.bedrock_agent.list_agent_versions(
                agentId=agent_id,
                maxResults=100
            )
            
            versions = ['DRAFT']  # DRAFT is always included
            for version in response.get('agentVersionSummaries', []):
                versions.append(version['agentVersion'])
                
            print(f"Agent {agent_id} versions: {versions}")
            return versions
        except Exception as e:
            print(f"Error finding agent versions: {str(e)}")
            return ['DRAFT']  # Return at least DRAFT version

    def find_all_aliases_for_agent(self, agent_id):
        """Find all aliases for a given agent"""
        aliases = []
        try:
            response = self.bedrock_agent.list_agent_aliases(
                agentId=agent_id,
                maxResults=100
            )
            
            for alias in response.get('agentAliasSummaries', []):
                aliases.append({
                    'id': alias['agentAliasId'],
                    'name': alias['agentAliasName'],
                    'arn': alias['agentAliasArn'] if 'agentAliasArn' in alias else None
                })
                
            return aliases
        except Exception as e:
            print(f"Error finding aliases for agent {agent_id}: {str(e)}")
            return []

    def find_all_collaborations(self, orchestrator_id):
        """Attempt to find all collaborations for all versions of an orchestrator"""
        collaborations = []
        
        # Check all versions including DRAFT
        versions = self.find_all_versions(orchestrator_id)
        
        for version in versions:
            try:
                response = self.bedrock_agent.list_agent_collaborators(
                    agentId=orchestrator_id,
                    agentVersion=version
                )
                
                for collab in response.get('collaboratorSummaries', []):
                    collaborations.append({
                        'id': collab['collaboratorId'],
                        'name': collab['collaboratorName'],
                        'version': version,
                        'arn': collab.get('agentDescriptor', {}).get('aliasArn', None)
                    })
                    print(f"Found collaborator: {collab['collaboratorName']} (ID: {collab['collaboratorId']}) for version {version}")
            except Exception as e:
                print(f"Error finding collaborators for agent {orchestrator_id} version {version}: {str(e)}")
        
        return collaborations

    def find_alias_from_arn(self, alias_arn):
        """Extract agent ID and alias ID from an alias ARN"""
        if not alias_arn:
            return None, None
            
        try:
            # Expected format: arn:aws:bedrock:region:account:agent/agent-id/alias/alias-id
            parts = alias_arn.split('/')
            if len(parts) >= 4:
                agent_id = parts[1]
                alias_id = parts[3]
                return agent_id, alias_id
        except Exception as e:
            print(f"Error parsing alias ARN {alias_arn}: {str(e)}")
            
        return None, None

    def disassociate_collaborators(self, orchestrator_id, collaborations):
        """Disassociate all collaborators from all versions of an orchestrator"""
        for collab in collaborations:
            try:
                print(f"Disassociating collaborator {collab['name']} (ID: {collab['id']}) from version {collab['version']}")
                self.bedrock_agent.disassociate_agent_collaborator(
                    agentId=orchestrator_id,
                    agentVersion=collab['version'],
                    collaboratorId=collab['id']
                )
            except Exception as e:
                print(f"Error disassociating collaborator: {str(e)}")
    
    def delete_agent_alias(self, agent_id, alias_id, alias_name):
        """Delete a specific agent alias"""
        try:
            print(f"Deleting agent alias: {alias_name} ({alias_id})")
            self.bedrock_agent.delete_agent_alias(
                agentId=agent_id,
                agentAliasId=alias_id
            )
            return True
        except Exception as e:
            print(f"Error deleting agent alias {alias_name} ({alias_id}): {str(e)}")
            return False
    
    def delete_all_agent_aliases(self, agent_id):
        """Delete all aliases for an agent"""
        aliases = self.find_all_aliases_for_agent(agent_id)
        success = True
        
        for alias in aliases:
            if not self.delete_agent_alias(agent_id, alias['id'], alias['name']):
                success = False
        
        if aliases:
            # Wait to ensure aliases are deleted
            print(f"Waiting for aliases deletion to complete for agent {agent_id}...")
            time.sleep(15)
            
        return success
    
    def delete_agent_action_groups(self, agent_id):
        """Delete all action groups for an agent"""
        try:
            # List action groups
            response = self.bedrock_agent.list_agent_action_groups(
                agentId=agent_id,
                agentVersion='DRAFT'
            )
            
            action_groups = response.get('agentActionGroupSummaries', [])
            print(f"Found {len(action_groups)} action groups for agent {agent_id}")
            
            # Delete each action group
            for action_group in action_groups:
                try:
                    print(f"Deleting action group: {action_group['actionGroupName']}")
                    self.bedrock_agent.delete_agent_action_group(
                        agentId=agent_id,
                        agentVersion='DRAFT',
                        actionGroupId=action_group['actionGroupId']
                    )
                except Exception as e:
                    print(f"Error deleting action group {action_group['actionGroupName']}: {str(e)}")
            
            return True
        except Exception as e:
            print(f"Error listing action groups for agent {agent_id}: {str(e)}")
            return False
    
    def delete_agent(self, agent_id, agent_name):
        """Delete a Bedrock agent"""
        try:
            print(f"Deleting agent: {agent_name} ({agent_id})")
            self.bedrock_agent.delete_agent(agentId=agent_id)
            
            # Wait for agent deletion to complete
            start_time = time.time()
            max_wait_time = 300  # 5 minutes
            
            while time.time() - start_time < max_wait_time:
                try:
                    response = self.bedrock_agent.get_agent(agentId=agent_id)
                    status = response["agent"]["agentStatus"]
                    print(f"Agent {agent_name} ({agent_id}) status: {status}")
                    
                    if status == "DELETING":
                        print(f"Waiting for agent deletion to complete...")
                        time.sleep(10)
                        continue
                except self.bedrock_agent.exceptions.ResourceNotFoundException:
                    print(f"Agent {agent_name} ({agent_id}) has been successfully deleted")
                    return True
                except Exception as check_e:
                    print(f"Error checking agent status: {str(check_e)}")
                    break
                    
            print(f"Timed out or encountered error while waiting for agent {agent_name} ({agent_id}) deletion")
            return False
            
        except Exception as e:
            print(f"Error deleting agent {agent_name} ({agent_id}): {str(e)}")
            return False
    
    def delete_lambda_function(self, function_name="BedrockAgentHandler"):
        """Delete the Lambda function used by the agents"""
        try:
            print(f"Deleting Lambda function: {function_name}")
            self.lambda_client.delete_function(FunctionName=function_name)
            return True
        except Exception as e:
            print(f"Error deleting Lambda function: {str(e)}")
            return False
            
    def delete_iam_roles(self):
        """Delete IAM roles created for the Bedrock agents and Lambda functions"""
        roles_to_delete = ['BedrockAgentRole', 'BedrockAgentLambdaRole']
        
        for role_name in roles_to_delete:
            try:
                # List and detach all policies attached to the role
                attached_policies = self.iam.list_attached_role_policies(RoleName=role_name)
                
                for policy in attached_policies.get('AttachedPolicies', []):
                    print(f"Detaching policy {policy['PolicyName']} from role {role_name}")
                    self.iam.detach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy['PolicyArn']
                    )
                
                # Delete inline policies
                inline_policies = self.iam.list_role_policies(RoleName=role_name)
                
                for policy_name in inline_policies.get('PolicyNames', []):
                    print(f"Deleting inline policy {policy_name} from role {role_name}")
                    self.iam.delete_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name
                    )
                
                # Delete the role
                print(f"Deleting IAM role: {role_name}")
                self.iam.delete_role(RoleName=role_name)
                
            except Exception as e:
                print(f"Error deleting IAM role {role_name}: {str(e)}")
    
    def delete_knowledge_base(self, kb_name="kb-metadatafiltering"):
        """Delete the Knowledge Base and its associated resources"""
        try:
            # First check if the KB exists
            exists = False
            try:
                kbs_available = self.bedrock_agent.list_knowledge_bases(maxResults=100)
                for kb in kbs_available.get("knowledgeBaseSummaries", []):
                    if kb["name"] == kb_name:
                        exists = True
                        break
            except Exception:
                print(f"Could not list knowledge bases")
                
            if not exists:
                print(f"Knowledge base {kb_name} not found, skipping deletion")
                return True
                
            print(f"Deleting knowledge base: {kb_name}")
            print(f"Deleting Bucket is set to {self.delete_bucket}")
            self.kb_helper.delete_kb(
                kb_name=kb_name,
                delete_s3_bucket=self.delete_bucket,  # Keep the bucket as it might contain other data
                delete_iam_roles_and_policies=True,
                delete_aoss=True
            )
            return True
        except Exception as e:
            print(f"Error deleting knowledge base: {str(e)}")
            return False
    
    def cleanup_specific_agents(self):
        """Clean up only the three specific agents and related resources"""
        # Find our specific agents
        orchestrator_agent, sub_agents = self.find_specific_agents()
        if not orchestrator_agent:
            print("Orchestrator 'OrchestratorAgent2' not found. Looking for any orchestrator...")
            orchestrator_agent = self.find_any_orchestrator_agent()
        
       
        if orchestrator_agent:
        # Find all collaborations for this orchestrator across all versions
            all_collaborations = self.find_all_collaborations(orchestrator_agent['id'])
            
            if all_collaborations:
                # Disassociate all collaborators
                print(f"Disassociating all collaborators from orchestrator {orchestrator_agent['name']}")
                self.disassociate_collaborators(orchestrator_agent['id'], all_collaborations)
                
                # Wait for disassociations to propagate
                print("Waiting for collaborator disassociations to complete...")
                time.sleep(30)
        
        # Now handle the orchestrator's aliases
        if orchestrator_agent:
            print(f"Deleting aliases for orchestrator: {orchestrator_agent['name']}")
            self.delete_all_agent_aliases(orchestrator_agent['id'])
        
        # Try to delete sub-agent aliases now that they should be disconnected
        for sub_agent in sub_agents:
            print(f"Deleting aliases for sub-agent: {sub_agent['name']}")
            self.delete_all_agent_aliases(sub_agent['id'])
        
        # Delete action groups for sub-agents
        for sub_agent in sub_agents:
            self.delete_agent_action_groups(sub_agent['id'])
        
        # Delete sub-agents
        for sub_agent in sub_agents:
            self.delete_agent(sub_agent['id'], sub_agent['name'])
        
        # Delete orchestrator agent
        if orchestrator_agent:
            self.delete_agent(orchestrator_agent['id'], orchestrator_agent['name'])
        
        # Cleanup other resources
        self.delete_lambda_function()
        self.delete_knowledge_base()
        self.delete_iam_roles()
        
        print("Cleanup completed!")

def main():
    parser = argparse.ArgumentParser(description='Cleanup specific Bedrock Agents and associated resources')
    parser.add_argument('--delete-bucket',required=True, help='Delete the S3 bucket')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--account-id', required=True, help='AWS account ID')
    
    args = parser.parse_args()
    
    cleanup = BedrockAgentCleanup(args.bucket, args.account_id, args.delete_bucket)
    cleanup.cleanup_specific_agents()
    print("Making sure that the sub agents are deleted")
    cleanup.cleanup_specific_agents()

if __name__ == '__main__':
    main()