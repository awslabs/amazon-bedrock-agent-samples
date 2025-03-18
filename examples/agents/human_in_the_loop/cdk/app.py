#!/usr/bin/env python3
import os
import json
import aws_cdk as cdk
# from cdk_nag import AwsSolutionsChecks, NagSuppressions

from BedrockAgentStack.BedrockAgentStack_stack import BedrockAgentStack


app = cdk.App()

stack = BedrockAgentStack(app, "BedrockAgentStack")
# cdk.Aspects.of(app).add(AwsSolutionsChecks())
# NagSuppressions.add_stack_suppressions(
#     stack,
#     [
#         {
#             "id": "AwsSolutions-IAM4",
#             "reason": "The role is a requirement for Bedrock"
#         },
#         {
#             "id": "AwsSolutions-IAM5",
#             "reason": "The role is a requirement for Bedrock"
#         },
#     ],
# )

app.synth()
