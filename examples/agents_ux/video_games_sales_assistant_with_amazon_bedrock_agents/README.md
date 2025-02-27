# A Tutorial on Deploying the Data Analyst Assistant for Video Game Sales Using Amazon Bedrock Agents

This solution provides a Generative AI Application reference that is able to access structured data stored in a PostgreSQL database based on a question-answering assistant that generates SQL queries to obtain the necessary data to provide an answer in natural language.

**Also, you can change the data source to connect to your preferred database engine by adapting the Agent's instructions and the Lambda function logic.**

![Video Games Sales Assistant](./images/preview.png)

> [!IMPORTANT]
> This sample application is meant for demo purposes and is not production ready. Please make sure to validate the code with your organizations security best practices.
> 
> Clean up resources after you test the demo to avoid unnecessary costs. Follow the clean-up steps provided.

> [!TIP]
> Enhance AI safety and compliance by implementing [Amazon Bedrock Guardrails](https://aws.amazon.com/bedrock/guardrails/) for your AI applications.

## Deploying the Sample Generative AI Application

To deploy the application, please follow these two steps:

1. [Getting Started with SAM Video Games Sales Assistant and Amazon Bedrock Agents](./sam-bedrock-video-games-sales-assistant/)
2. [Getting Started with Amplify Video Games Sales Assistant](./amplify-video-games-sales-assistant-sample/)

> [!NOTE]
> *It is recommended to use the Oregon (us-west-2) or N. Virginia (us-east-1) regions to deploy the application.*

## AWS Diagram Architecture

![Video Games Sales Assistant](./images/gen-ai-assistant-diagram.png)

> [!NOTE]
> This solution references the use of AWS IAM Credentials to connect to Amazon Bedrock and Amazon DynamoDB. **For the production environment, you can implement user authentication and authorization through Amazon Cognito or your own Identity Provider to ensure secure access to the generative AI assistant and data.**

## Application Preview

The following images are part of a conversation analysis that includes the natural language answer, the rationale used by the LLM to generate the SQL query, the records resulting from the SQL query used to answer the question, and chart generation.

**Agent answers**

![Video Games Sales Assistant](./images/preview1.png)

**Answer details including the rationale to generate the SQL**

![Video Games Sales Assistant](./images/preview2.png)

**The record results from the SQL used to answer the question**

![Video Games Sales Assistant](./images/preview3.png)

**The chart generated using the agent's answer and the record results from the SQL Query (charts created using [Apexcharts](https://apexcharts.com/))**

![Video Games Sales Assistant](./images/preview4.png)

## License

This project is licensed under the Apache-2.0 License.