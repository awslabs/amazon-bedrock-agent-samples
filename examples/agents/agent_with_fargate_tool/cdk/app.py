#!/usr/bin/env python3
import os
import aws_cdk as cdk
from BedrockAgentStack.BedrockAgentStack_stack import BedrockAgentStack

app = cdk.App()

stack = BedrockAgentStack(
    app,
    "BedrockAgentStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
