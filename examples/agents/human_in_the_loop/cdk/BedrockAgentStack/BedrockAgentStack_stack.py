from typing_extensions import runtime
import os
from aws_cdk import (
    Duration,
    Stack,
    Aspects,
    aws_lambda as lambda_,
    aws_iam as iam,
    CfnOutput,
    aws_bedrock as bedrock,
    aws_logs as logs,
)
import json
from constructs import Construct
from cdk_nag import AwsSolutionsChecks, NagSuppressions


class BedrockAgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Aspects.of(self).add(AwsSolutionsChecks())

        # Load configuration
        with open("./BedrockAgentStack/config.json", "r") as config_file:
            config = json.load(config_file)

        # Define parameters
        agent_name = config["agentName"]
        agent_alias_name = config["agentAliasName"]
        agent_model_id = config["agentModelId"]
        agent_model_arn = bedrock.FoundationModel.from_foundation_model_id(
            scope=self,
            _id="AgentModel",
            foundation_model_id=bedrock.FoundationModelIdentifier(agent_model_id),
        ).model_arn

        agent_description = config["agentDescription"]
        agent_instruction = config["agentInstruction"]

        # The name for this role is a requirement for Bedrock
        agent_role = iam.Role(
            scope=self,
            id="AgentRole",
            role_name="AmazonBedrockExecutionRoleForAgents-HumanInTheLoop",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        )

        agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="InvokeBedrockLambda",
                effect=iam.Effect.ALLOW,
                resources=[agent_model_arn],
                actions=["bedrock:InvokeModel", "lambda:InvokeFunction"],
            )
        )

        log_group = logs.LogGroup(
            self,
            "BedrockActionGroup-HRAssistant",
            retention=logs.RetentionDays.ONE_WEEK,
        )

        base_lambda_policy = iam.ManagedPolicy(
            self,
            "LambdaBasicExecutionPolicy",
            description="Allows Lambda functions to write to CloudWatch Logs",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    resources=[log_group.log_group_arn],
                )
            ],
        )

        lambda_role = iam.Role(
            scope=self,
            id="HRAssistantLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[base_lambda_policy],
        )

        # Create the lambda function for the Agent Action Group
        action_group_function = lambda_.Function(
            self,
            "BedrockAgentActionGroupExecutor",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("../backend/"),
            handler="lambda.lambda_handler",
            timeout=Duration.seconds(300),
            role=lambda_role,
            function_name="BedrockActionGroup-HRAssistant",
            log_group=log_group,
            log_format="JSON",
        )

        # Create the Agent
        cfn_agent = bedrock.CfnAgent(
            self,
            "CfnAgent",
            agent_name=agent_name,
            agent_resource_role_arn=agent_role.role_arn,
            auto_prepare=True,
            description=agent_description,
            foundation_model=agent_model_id,
            instruction=agent_instruction,
            idle_session_ttl_in_seconds=1800,
            action_groups=[
                # get time off action group
                bedrock.CfnAgent.AgentActionGroupProperty(
                    action_group_name=config["getTimeOffActionGroupName"],
                    description=config["getTimeOffActionGroup"],
                    # the properties below are optional
                    action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                        lambda_=action_group_function.function_arn
                    ),
                    function_schema=bedrock.CfnAgent.FunctionSchemaProperty(
                        functions=[
                            bedrock.CfnAgent.FunctionProperty(
                                name=config["func_gettime_name"],
                                # the properties below are optional
                                description=config["func_gettime_description"],
                            )
                        ]
                    ),
                ),
                # request time off action group
                bedrock.CfnAgent.AgentActionGroupProperty(
                    action_group_name=config["requestTimeOffActionGroupName"],
                    description=config["requestTimeOffActionGroup"],
                    # the properties below are optional
                    action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                        lambda_=action_group_function.function_arn
                    ),
                    function_schema=bedrock.CfnAgent.FunctionSchemaProperty(
                        functions=[
                            # request_time_off
                            bedrock.CfnAgent.FunctionProperty(
                                name=config["func_createtimeoff_name"],
                                # the properties below are optional
                                description=config["func_createtimeoff_description"],
                                parameters={
                                    config[
                                        "func_createtimeoff_start_date"
                                    ]: bedrock.CfnAgent.ParameterDetailProperty(
                                        type="string",
                                        # the properties below are optional
                                        description="The date that time off starts",
                                        required=True,
                                    ),
                                    config[
                                        "func_createtimeoff_number_of_days"
                                    ]: bedrock.CfnAgent.ParameterDetailProperty(
                                        type="integer",
                                        # the properties below are optional
                                        description="The number of days user wants to request off",
                                        required=True,
                                    ),
                                },
                            )
                        ]
                    ),
                ),
            ],
        )

        cfn_agent_alias = bedrock.CfnAgentAlias(
            self,
            "MyCfnAgentAlias",
            agent_alias_name=agent_alias_name,
            agent_id=cfn_agent.attr_agent_id,
        )

        lambda_.CfnPermission(
            self,
            "BedrockInvocationPermission",
            action="lambda:InvokeFunction",
            function_name=action_group_function.function_name,
            principal="bedrock.amazonaws.com",
            source_arn=cfn_agent.attr_agent_arn,
        )

        # Agent is created with booking-agent-alias and prepared, so it shoudld be ready to test #

        # Declare the stack outputs
        CfnOutput(scope=self, id="Agent_name", value=cfn_agent.agent_name)
        CfnOutput(scope=self, id="Agent_id", value=cfn_agent.attr_agent_id)
        # CfnOutput(scope=self, id='Agent_alias', value=cfn_agent_alias.agentAliasName)
