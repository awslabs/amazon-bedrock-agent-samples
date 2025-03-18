# cdk

## Prerequisites

Please refer to the [main project prerequisites](../README.md) for initial setup requirements.

Additionally, ensure you have:
- AWS CLI installed and configured with appropriate credentials
- AWS region set to `us-west-2` (required for access to latest models like Claude 3.5 Haiku)

To verify your AWS CLI setup is working correctly, run:
```bash
$ aws s3 ls
2025-01-15 10:30:25 my-bucket-name
2025-02-20 15:45:12 another-bucket-name
2025-03-10 09:15:33 deployment-artifacts
```
If you see your S3 buckets listed, your AWS CLI is properly to execute commands on your account.

#### Setting up Virtual Environment

In order to use the cdk, you must first set up a virtual environment and install dependencies. First, navigate to the CDK folder in the repo:
```
$ cd <path-to-repo>
bedrock-hr-assistant-roc $ cd ./cdk
```

Then create a virtual environment and install dependencies. This will install the aws-cdk in the virtual environment.
```
bedrock-hr-assistant-roc/cdk $ python3 -m venv .venv
... # should see (.venv) before terminal prompt afterwards
(.venv) bedrock-hr-assistant-roc/cdk $ pip3 install -r requirements.txt
```

## Deployment

It should take approximately one minute to deploy the entire stack. Make sure to set up your virtual environment first.

### Confirm region is us-west-2
Ensure infrastructure is being deployed to `us-west-2`.
```
(.venv) bedrock-hr-assistant-roc/frontend $ env | grep AWS_DEFAULT
AWS_DEFAULT_REGION=us-west-2
```

### Deploy the infrastructure
```
(.venv) bedrock-hr-assistant-roc/cdk $ cdk bootstrap
(.venv) bedrock-hr-assistant-roc/cdk $ cdk synth 
... # you may see some node EOL messages
(.venv) bedrock-hr-assistant-roc/cdk $ cdk deploy 
... # should see 5 resources pop up
Do you wish to deploy these changes (y/n)? y
```

### Viewing the infrastructure in AWS Console

1. Log into your AWS account
2. Navigate to Amazon Bedrock service
3. Under "Builder Tools" select "Agents"
4. You should have an Agent called "hr-assistant-cdk". Click on the Agent.
5. Under aliases, you should see an alias named "hr-assistant-no-roc" representing an Agent without any return of control capabilities.
6. You can test your agent by following [these instructions](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-test.html).

## Updating Agent to use human_in_the_loop capabilities

### Adding confirmation to agent

1. Click on the "Edit" button in the agent configuration page.
![Edit agent configuration](../images/console-edit-agent.png)

2. Navigate to the action groups section and select the action group you want to modify.
![Select action group](../images/console-click-on-action-group.png)

3. Enable the confirmation dialog by selecting the "Add confirmation" option.
![Enable confirmation](../images/console-add-confirmation.png)

4. Click on "Prepare agent" to apply the changes.
![Prepare the agent](../images/console-prepare-agent.png)

5. Create a new alias by clicking the "Create alias" button.
![Create new alias](../images/console-create-new-alias.png)

6. Configure the alias settings in the modal dialog and create the alias.
![Configure alias settings](../images/console-create-alias-modal.png)

### Adding return of control

1. Click on the "Edit" button in the agent configuration page.
![Edit agent configuration](../images/console-edit-agent.png)

2. Navigate to the action groups section and select the action group you want to modify.
![Select action group](../images/console-click-on-action-group.png)

3. Enable return of control by selecting the "Add ROC" option.
![Enable ROC](../images/console-add-roc.png)

4. Click on "Prepare agent" to apply the changes.
![Prepare the agent](../images/console-prepare-agent.png)

5. Create a new alias by clicking the "Create alias" button.
![Create new alias](../images/console-create-new-alias.png)

6. Configure the alias settings in the modal dialog and create the alias.
![Configure alias settings](../images/console-create-alias-modal.png)

## Clean Up
To clean up the infrastructure, simply run the `cdk destroy` command.
```
(.venv) bedrock-hr-assistant-roc/cdk $ cdk destroy
Are you sure you want to delete: BedrockAgentStack (y/n)? y
```