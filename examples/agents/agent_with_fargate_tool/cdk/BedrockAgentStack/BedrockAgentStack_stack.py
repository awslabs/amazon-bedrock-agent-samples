import os
import json
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    Aspects,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    aws_bedrock as bedrock,
    aws_s3 as s3,
)
from constructs import Construct
from cdk_nag import AwsSolutionsChecks, NagSuppressions


class BedrockAgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Aspects.of(self).add(AwsSolutionsChecks())

        # Load configuration
        with open("./BedrockAgentStack/config.json", "r") as config_file:
            config = json.load(config_file)

        agent_name = config["agentName"]
        agent_alias_name = config["agentAliasName"]
        agent_model_id = config["agentModelId"]
        agent_description = config["agentDescription"]
        agent_instruction = config["agentInstruction"]

        # --- VPC ---
        vpc = ec2.Vpc(
            self,
            "TikaVpc",
            max_azs=2,
            nat_gateways=1,
        )

        # AwsSolutions-VPC7: Enable VPC Flow Logs
        vpc_flow_log_group = logs.LogGroup(
            self,
            "VpcFlowLogGroup",
            retention=logs.RetentionDays.ONE_WEEK,
        )
        vpc.add_flow_log(
            "FlowLog",
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(vpc_flow_log_group),
        )

        # S3 gateway endpoint — free, avoids NAT for S3 traffic
        vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        # --- ECS Cluster + Fargate Service ---
        # AwsSolutions-ECS4: Enable Container Insights
        cluster = ecs.Cluster(
            self,
            "TikaCluster",
            vpc=vpc,
            container_insights=True,
        )

        task_def = ecs.FargateTaskDefinition(
            self,
            "TikaTaskDef",
            memory_limit_mib=config["fargateMemoryMiB"],
            cpu=config["fargateCpu"],
        )

        task_def.add_container(
            "tika",
            image=ecs.ContainerImage.from_registry(
                f"apache/tika:{config['tikaImageTag']}"
            ),
            port_mappings=[ecs.PortMapping(container_port=9998)],
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="tika",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
        )

        fargate_service = ecs.FargateService(
            self,
            "TikaService",
            cluster=cluster,
            task_definition=task_def,
            desired_count=config["desiredCount"],
            assign_public_ip=False,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        # AwsSolutions-S1: Access logs bucket for ALB and S3
        access_logs_bucket = s3.Bucket(
            self,
            "AccessLogsBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        # Internal ALB so Lambda can reach Tika without public exposure
        # AwsSolutions-ELB2: Enable access logs
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "TikaAlb",
            vpc=vpc,
            internet_facing=False,
        )
        alb.log_access_logs(access_logs_bucket, prefix="alb-logs")

        # AwsSolutions-EC23: Restrict ALB security group to VPC CIDR only
        alb_sg = alb.connections.security_groups[0]
        # Remove the default 0.0.0.0/0 rule by overriding ingress
        cfn_sg = alb_sg.node.default_child
        cfn_sg.add_property_override(
            "SecurityGroupIngress",
            [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 80,
                    "ToPort": 80,
                    "CidrIp": vpc.vpc_cidr_block,
                    "Description": "Allow HTTP from within VPC only",
                }
            ],
        )

        listener = alb.add_listener("TikaListener", port=80, open=False)
        listener.add_targets(
            "TikaTarget",
            port=9998,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[fargate_service],
            health_check=elbv2.HealthCheck(
                path="/tika",
                interval=Duration.seconds(30),
            ),
        )

        # --- S3 Bucket for document uploads ---
        # AwsSolutions-S1: Enable server access logs
        docs_bucket = s3.Bucket(
            self,
            "TikaDocsBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            server_access_logs_bucket=access_logs_bucket,
            server_access_logs_prefix="s3-access-logs/",
        )

        # --- Lambda log group ---
        log_group = logs.LogGroup(
            self,
            "TikaActionLambdaLogGroup",
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
            self,
            "TikaActionLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                base_lambda_policy,
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
            ],
        )

        # --- Lambda bridge between Bedrock Agent and Tika ---
        tika_lambda = lambda_.Function(
            self,
            "TikaActionLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("../backend/"),
            handler="lambda.handler",
            timeout=Duration.seconds(120),
            memory_size=256,
            role=lambda_role,
            log_group=log_group,
            log_format="JSON",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            environment={
                "TIKA_URL": f"http://{alb.load_balancer_dns_name}",
                "DOCS_BUCKET": docs_bucket.bucket_name,
            },
        )

        # Allow Lambda to read from the S3 bucket
        docs_bucket.grant_read(tika_lambda)

        # Allow Lambda to reach the ALB
        alb.connections.allow_from(tika_lambda, ec2.Port.tcp(80))

        # --- Bedrock Agent Role ---
        agent_model_arn = Stack.of(self).format_arn(
            service="bedrock",
            resource="foundation-model",
            resource_name=agent_model_id,
            account="",
        )

        agent_role = iam.Role(
            self,
            "AgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        )

        agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="InvokeBedrockModel",
                effect=iam.Effect.ALLOW,
                resources=[agent_model_arn],
                actions=["bedrock:InvokeModel"],
            )
        )

        # Allow Bedrock to invoke the Lambda
        tika_lambda.grant_invoke(agent_role)
        tika_lambda.add_permission(
            "BedrockInvoke",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            source_arn=Stack.of(self).format_arn(
                service="bedrock",
                resource="agent",
                resource_name="*",
            ),
        )

        # Load the OpenAPI schema for the action group
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "schemas", "tika-openapi.json"
        )
        with open(schema_path, "r") as f:
            api_schema = f.read()

        # --- Bedrock Agent with Action Group ---
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
                bedrock.CfnAgent.AgentActionGroupProperty(
                    action_group_name=config["actionGroupName"],
                    description=config["actionGroupDescription"],
                    action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                        lambda_=tika_lambda.function_arn
                    ),
                    api_schema=bedrock.CfnAgent.APISchemaProperty(payload=api_schema),
                ),
            ],
        )

        # --- Agent Alias ---
        cfn_agent_alias = bedrock.CfnAgentAlias(
            self,
            "CfnAgentAlias",
            agent_alias_name=agent_alias_name,
            agent_id=cfn_agent.attr_agent_id,
        )
        cfn_agent_alias.add_dependency(cfn_agent)

        # --- Outputs ---
        CfnOutput(self, "AgentId", value=cfn_agent.attr_agent_id)
        CfnOutput(self, "AgentAliasId", value=cfn_agent_alias.attr_agent_alias_id)
        CfnOutput(self, "TikaAlbDns", value=alb.load_balancer_dns_name)
        CfnOutput(self, "DocsBucketName", value=docs_bucket.bucket_name)

        # --- cdk-nag suppressions for CDK-generated wildcard policies ---
        # grant_read() generates s3:GetObject*, s3:GetBucket*, s3:List* and
        # a resource wildcard on bucket_arn/* — all scoped to this bucket.
        NagSuppressions.add_resource_suppressions(
            lambda_role,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Wildcard actions (s3:GetObject*, s3:GetBucket*, s3:List*) "
                    "and resource ARN/* are generated by CDK grant_read() and "
                    "scoped to the TikaDocsBucket only.",
                },
            ],
            apply_to_children=True,
        )

        # grant_invoke() generates a resource wildcard on function_arn:*
        # for Lambda versioning — scoped to the TikaActionLambda only.
        NagSuppressions.add_resource_suppressions(
            agent_role,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Wildcard resource (function_arn:*) is generated by CDK "
                    "grant_invoke() for Lambda version/alias invocation and "
                    "scoped to TikaActionLambda only.",
                },
            ],
            apply_to_children=True,
        )

        # Suppress AwsSolutions-IAM4/IAM5 on the auto-delete custom resource
        # and VPC flow log role — both are CDK-managed.
        NagSuppressions.add_stack_suppressions(
            self,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "CDK-managed custom resource and VPC flow log roles use "
                    "AWS managed policies by design.",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "CDK-managed custom resource Lambda for auto-delete "
                    "objects requires broad S3 permissions.",
                    "applies_to": ["Resource::*"],
                },
                {
                    "id": "AwsSolutions-L1",
                    "reason": "CDK-managed custom resource Lambda runtime is controlled "
                    "by the CDK framework.",
                },
                {
                    "id": "AwsSolutions-S1",
                    "reason": "The access logs bucket itself does not need server access "
                    "logs to avoid infinite recursion.",
                },
            ],
        )
