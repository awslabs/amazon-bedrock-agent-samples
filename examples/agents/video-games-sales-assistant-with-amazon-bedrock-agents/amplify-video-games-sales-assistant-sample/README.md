# Getting Started with Amplify Video Games Sales Assistant

This tutorial guides you through the process of setting up a React front-end application using AWS Amplify that integrates with Amazon Bedrock Agent project. The application leverages Amazon Cognito for user authentication and authorization. 

By the end of this tutorial, you'll have a fully functional web application that allows users to interact with a conversational AI agent for video game sales assistance.

## Prerequisites

- [Node.js > 18 version required](https://nodejs.org/en/download/package-manager)


[Install the Amplify CLI](https://docs.amplify.aws/gen1/react/tools/cli/start/set-up-cli/) with the following command:
```console
npm install -g @aws-amplify/cli 
```

## Amplify Deployment

Run the following commands in the React front-end application.

### Install React Application Dependencies

```console
npm install
```

### Initialize the Amplify Application using **Gen1**

```console
amplify init
```

- To initialize the project use the **suggested configuration**.
- Select your authentication method.

### Add Authentication

```console
amplify add auth
```
Use the following configuration:
 - Do you want to use the default authentication and security configuration? **Default configuration**
 - How do you want users to be able to sign in? **Email**
 - Do you want to configure advanced settings? **No, I am done.**


```console
amplify push
```

### Configure the Amazon Bedrock Agent

Rename the file **src/sample.env.js** to **src/env.js**, update the values with your **Agent**, **Agent Alias ID** and **Question Answers Table Name** that you can find in the CloudFormation Outputs from the SAM project **sam-bedrock-video-games-sales-assistant**.

### Update the Auth Role from Amazon Cognito Identity Pool

Go to the **Cognito** service, choose **Identity pools**, click on **amplifyvideogamessaXXXXXXXXX_identitypool_XXXXXXXXX__dev**, go to **User access**.

From the **Authenticated access** section, click on the **Authenticated role** to go to the configuration page.

In the **Permissions policies** section, click **Add permissions** and then click **Create inline policy** to add the following inline policy using the **JSON Policy editor**:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "InvokeBedrockAgent",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeAgent",
                "bedrock:InvokeModel",
                "dynamodb:Query"
            ],
            "Resource": "*"
        }
    ]
}
```

### Add Hosting and Testing

```console
amplify add hosting
```

Use the following configuration:
- Select the plugin module to execute · **Hosting with Amplify Console (Managed hosting with custom domains, Continuous deployment)**
- Choose a type **Manual deployment**

```console
amplify publish
```

Now you can test the application using the provided URL, create an account to access the assistant.

#### Sample Questions

- Hello
- How can you help me?
- What is the structure of the data?
- Which developers tend to get the best reviews?
- What were the best-selling games in the last 10 years?
- What are the best-selling video game genres?
- Give me the top 3 game publishers.
- Give me the top 3 video games with the best reviews and the best sales.
- Which is the year with the highest number of games released?
- Which are the most popular consoles and why?
- Give me a short summary and conclusion.