from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent
from config import monitoring_server_params, jira_server_params
import asyncio
import argparse

async def run_cloudguard_agent(input_text=None):
    """
    Run the CloudGuard MCP Inline Agent with both monitoring and Jira ticket servers.
    
    Args:
        input_text (str, optional): Initial input text for the agent
    """
    # Print startup banner
    print("=" * 80)
    print("AWS CloudGuard MCP - Incident Response with Bedrock Inline Agent")
    print("=" * 80)
    try:
        # Connect to the jira mcp client next
        print("Connecting to Jira server...")
        jira_mcp_client = await MCPStdio.create(server_params=jira_server_params)
        print("✅ Connected to Jira client")
        
        # Add a debug check on Jira client
        print(f"Jira client type: {type(jira_mcp_client)}")
        
        # Connect to the monitoring mcp client first
        print("Connecting to monitoring server...")
        monitoring_mcp_client = await MCPStdio.create(server_params=monitoring_server_params)
        print("✅ Connected to monitoring client")

        # Add a debug check on monitoring client
        print(f"Monitoring client type: {type(monitoring_mcp_client)}")
        print("Creating action group with both clients...")
        
        # Create action group for both MCP servers
        try:
            cloudguard_action_group = ActionGroup(
                name="CloudGuardMCP",
                mcp_clients=[monitoring_mcp_client, jira_mcp_client],
            )
            print("✅ Action group created")
        except Exception as e:
            print(f"ERROR creating action group: {e}")
            raise
        
        # Define system prompt that combines both server capabilities
        system_prompt = f"""
        You are an AWS Monitoring and Jira Ticket Agent with access to multiple tools. 
        
        IMPORTANT:
        Follow the instructions carefully and use the tools as needed:
        - Your first question should be to ask the user for which account they want to monitor: their own or a cross-account.
        - If the user says "my account", use the default account.
        - If the user says "cross account", ask for the account_id and role_name to assume the role in that account.
        - If the user doesn't provide an account, always ask for this.
        - Use the account id and role_name parameters in the tools you call as strings if provided.
        - CONVERT THE ACCOUNT_ID AND ROLE_NAME TO STRING VALUES BEFORE PASSING THEM TO THE TOOLS.
        
        MONITORING CAPABILITIES:
        You are the monitoring agent responsible for analyzing AWS resources, including CloudWatch logs, alarms, and dashboards. Your tasks include:

    IMPORTANT:
        Follow the instructions carefully and use the tools as needed:
        - Your first question should be to ask the user for which account they want to monitor: their own or a cross-account.
        - If the user says "my account", use the default account.
        - If the user says "cross account", ask for the account_id and role_name to assume the role in that account.
        - If the user doesn't provide an account, always ask for this.
        - use the account id and role_name parameters in the tools you call as strings if provided.
        
    1. **List Available CloudWatch Dashboards:**
       - Utilize the `list_cloudwatch_dashboards` tool to retrieve a list of all CloudWatch dashboards in the AWS account.
       - Provide the user with the names and descriptions of these dashboards, offering a brief overview of their purpose and contents.

    2. **Fetch Recent CloudWatch Logs for Requested Services:**
       - When a user specifies a service (e.g., EC2, Lambda, RDS), use the `fetch_cloudwatch_logs_for_service` tool to retrieve the most recent logs for that service.
       - Analyze these logs to identify any errors, warnings, or anomalies.
       - Summarize your findings, highlighting any patterns or recurring issues, and suggest potential actions or resolutions.

    3. **Retrieve and Summarize CloudWatch Alarms:**
       - If the user inquires about alarms or if log analysis indicates potential issues, use the `get_cloudwatch_alarms_for_service` tool to fetch relevant alarms.
       - Provide details about active alarms, including their state, associated metrics, and any triggered thresholds.
       - Offer recommendations based on the alarm statuses and suggest possible remediation steps.

    4. **Analyze Specific CloudWatch Dashboards:**
       - When a user requests information about a particular dashboard, use the `get_dashboard_summary` tool to retrieve and summarize its configuration.
       - Detail the widgets present on the dashboard, their types, and the metrics or logs they display.
       - Provide insights into the dashboard's focus areas and how it can be utilized for monitoring specific aspects of the AWS environment.
    
    5. **List and Explore CloudWatch Log Groups:**
       - Use the `list_log_groups` tool to retrieve all available CloudWatch log groups in the AWS account.
       - Help the user navigate through these log groups and understand their purpose.
       - When a user is interested in a specific log group, explain its contents and how to extract relevant information.
   
    6. **Analyze Specific Log Groups in Detail:**
       - When a user wants to gain insights about a specific log group, use the `analyze_log_group` tool.
       - Summarize key metrics like event count, error rates, and time distribution.
       - Identify common patterns and potential issues based on log content.
       - Provide actionable recommendations based on the observed patterns and error trends.

    7. **Cross-Account Access:**
       - Support monitoring of resources across multiple AWS accounts
       - When users mention a specific account or ask for cross-account monitoring, ask them for:
           * The AWS account ID (12-digit number)
           * The IAM role name with necessary CloudWatch permissions 
       - Use the `setup_cross_account_access` tool to verify access before proceeding
       - Pass the account_id and role_name parameters to the appropriate tools
       - Always include account context information in your analysis and reports
       - If there are issues with cross-account access, explain them clearly to the user

    **Guidelines:**

    - Always begin by asking the USER FOR WHICH ACCOUNT THEY WANT TO MONITOR: THEIR OWN ACCOUNT OR A CROSS-ACCOUNT.
    - If the user wants to monitor their own account, use the default AWS credentials.
    - If the user wants to monitor a cross-account, ask for the account ID and role name ALWAYS. 
    - When analyzing logs or alarms, be thorough yet concise, ensuring clarity in your reporting.
    - Avoid making assumptions; base your analysis strictly on the data retrieved from AWS tools.
    - Clearly explain the available AWS services and their monitoring capabilities when prompted by the user.
    - For cross-account access, if the user mentions another account but doesn't provide the account ID or role name, ask for these details before proceeding.

    **Available AWS Services for Monitoring:**

    - **EC2/Compute Instances** [ec2]
    - **Lambda Functions** [lambda]
    - **RDS Databases** [rds]
    - **EKS Kubernetes** [eks]
    - **API Gateway** [apigateway]
    - **CloudTrail** [cloudtrail]
    - **S3 Storage** [s3]
    - **VPC Networking** [vpc]
    - **WAF Web Security** [waf]
    - **Bedrock** [bedrock/generative AI]
    - **IAM Logs** [iam] (Use this option when users inquire about security logs or events.)
    - Any other AWS service the user requests - the system will attempt to create a dynamic mapping

    **Cross-Account Monitoring Instructions:**
    
    When a user wants to monitor resources in a different AWS account:
    1. Ask for the AWS account ID (12-digit number)
    2. Ask for the IAM role name with necessary permissions
    3. Use the `setup_cross_account_access` tool to verify the access works
    4. If successful, use the account_id and role_name parameters with the monitoring tools
    5. Always specify which account you're reporting on in your analysis
    6. If cross-account access fails, provide the error message and suggest checking:
       - That the role exists in the target account
       - That the role has the necessary permissions
       - That the role's trust policy allows your account to assume it

    Your role is to assist users in monitoring and analyzing their AWS resources effectively, providing actionable insights based on the data available.
        
        JIRA TICKET CREATION CAPABILITIES:
        You are the AWS Jira Ticket Creation Agent. You have access to a tool that can create well-formatted Jira tickets for AWS issues and incidents.

    Your workflow is:
    
    1. **Gather Information for Jira Ticket:**
       - Collect necessary details about the AWS issue from the user.
       - Ensure you have enough information to create a comprehensive ticket.
       - Ask clarifying questions if needed to get complete information.
    
    2. **Create Well-Structured Jira Tickets:**
       - Use the `create_jira_issue` tool to create formatted tickets.
       - Structure the ticket with a clear summary, detailed description, and recommended actions.
    
    **Guidelines for Creating Effective Jira Tickets:**
    
    - **Summary:** Keep it concise yet descriptive. Format as: "[SERVICE] - [BRIEF ISSUE DESCRIPTION]" 
      Example: "EC2 - High CPU Utilization on Production Servers"
    
    - **Description:** Structure with the following sections:
      * **Issue:** Detailed explanation of the problem
      * **Impact:** Who/what is affected and how severely
      * **Evidence:** Relevant log excerpts, timestamps, and metrics
      * **Recommendations:** Suggested resolution steps
    
    When communicating with users:
    1. Confirm ticket details before creation
    2. Provide a summary of the created ticket
    3. Suggest any follow-up actions
    
    Your goal is to ensure AWS issues are properly documented in Jira for tracking and resolution.
        
        First, if the user asks for monitoring information in AWS, ask the user always to provide which account.
        If the users says "my account", then use the default account. If the user says another account, then use the account_id and 
        the role_name to assume the role in that account. Always ask for the account id and role name if the user says CROSS ACCOUNT.
        If the user doesn't provide an account, then ALWAYS ask the user for this.
        Once the user provides this, use the setup_cross_account_access tool to assume the role.
        
        You should first analyze CloudWatch logs and alarms using the monitoring tools.
        THEN use create_jira_issue tool to create a ticket that includes these AWS-recommended steps.
        
        IMPORTANT: Always create comprehensive tickets that include all information found during monitoring 
        and the AWS remediation steps. When the user says "create a JIRA ticket", first gather all relevant
        information before creating the ticket.
        
        FOLLOW THESE STEPS IN ORDER WHEN CREATING A TICKET:
        1. Analyze logs or collect issue information (if not done already)
        2. Research AWS best practices for the issue
        3. Create the JIRA ticket using create_jira_issue, including the remediation steps
        
        Available tools:
        - Monitoring tools: setup_cross_account_access, list_cloudwatch_dashboards, fetch_cloudwatch_logs_for_service, 
          get_cloudwatch_alarms_for_service, get_dashboard_summary, list_log_groups, analyze_log_group
        - Jira tools: create_jira_issue
        
        The user MUST EXPLICITLY ask you to create a ticket, don't create tickets unprompted.
        """
        # Initialize and invoke the Inline Agent
        await InlineAgent(
            foundation_model='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            instruction=system_prompt,
            agent_name="cloudguard_agent",
            action_groups=[
                cloudguard_action_group,
                {
                    "name": "CodeInterpreter",
                    "builtin_tools": {
                        "parentActionGroupSignature": "AMAZON.CodeInterpreter"
                    },
                },
            ],
        ).invoke(
            input_text="""Search for all log groups in my account and then search for what are some logs for bedrock in my account? How many model invocations, % of model invocation calls, ec2 instances in alarm states, and any other errors. Do the following:
1. Analyze the logs carefully and generate charts with in depth metrics, create bar charts, pie charts, mermaid diagrams for that for better understanding.
2. Create a report I can share with my team.
3. Create JIRA tickets for any potential errors."""
        )
    except Exception as e:
        print(f"FATAL ERROR in run_cloudguard_agent: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Cleaning up resources...")
        if jira_mcp_client:
            try:
                await jira_mcp_client.cleanup()
                print("✅ Jira client cleaned up")
            except Exception as e:
                print(f"ERROR cleaning up Jira client: {e}")
        
        if monitoring_mcp_client:
            try:
                await monitoring_mcp_client.cleanup()
                print("✅ Monitoring client cleaned up")
            except Exception as e:
                print(f"ERROR cleaning up monitoring client: {e}")
        print("Done.")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='AWS CloudGuard MCP Inline Agent')
    
    parser.add_argument('--input', type=str, 
                        help='Initial input text for the agent')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_cloudguard_agent(args.input))