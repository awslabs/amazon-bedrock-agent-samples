# Manual Database Creation, Data Loading, and Amazon Bedrock Agent Creation

After completing the SAM deployment, save the CloudFormation outputs from the deployed stack, as you will use this information throughout the deployment of the application.

## Connect to the PostgreSQL Database and Load the Data Sample

1. **Connect to PostgreSQL database**

Go to **Amazon RDS** service and select the option **Query Editor** from the left menu, complete the form with the following information and click in **Connect to database**.

- Select your cluster: **sam-bedrock-video-games-sales-as-databaseassistant-XXXXXXXXXXXX**
- For database username choose **Connect with a Secrets Manager ARN**
- From the cloudformation or SAM deployment output copy and paste the **SecretARN** value.
- For the name of the database type **video_games_sales**

2. **Create the table with the appropriate columns**

In the query editor provided, copy and paste the following sql and execute to create the table.

```sql
CREATE TABLE video_games_sales_units (
    title TEXT,
    console TEXT,
    genre TEXT,
    publisher TEXT,
    developer TEXT,
    critic_score NUMERIC(3,1),
    total_sales NUMERIC(4,2),
    na_sales NUMERIC(4,2),
    jp_sales NUMERIC(4,2),
    pal_sales NUMERIC(4,2),
    other_sales NUMERIC(4,2),
    release_date DATE
);
```

3. **Install the S3 extension**

To import the data from Amazon S3, it is necessary to install the **aws_s3 extension** by executing the following command.

```sql
CREATE EXTENSION aws_s3 CASCADE;
```

4. **Load the data to the table**

Import the data from your Amazon S3 bucket by using the **table_import_from_s3** function of the **aws_s3 extension**, change the bucket name and the region.

- Upload the **[video_games_sales_no_headers.csv](./resources/database/video_games_sales_no_headers.csv)** file to an S3 bucket and for the following command, change **\<your_bucket_name\>** and **\<region\>** with your own bucket name and with your appropriate region.

```sql
SELECT aws_s3.table_import_from_s3(
   'video_games_sales_units',
   'title,console,genre,publisher,developer,critic_score,total_sales,na_sales,jp_sales,pal_sales,other_sales,release_date',
   'DELIMITER ''|''', 
   aws_commons.create_s3_uri('<your_bucket_name>', 'video_games_sales_no_headers.csv', '<region>')
);
```

> [!NOTE]
> The data source provided contains information from [Video Game Sales](https://www.kaggle.com/datasets/asaniczka/video-game-sales-2024) which is made available under the [ODC Attribution License](https://opendatacommons.org/licenses/odbl/1-0/).

## Create the Amazon Bedrock Agent

Go to the **Amazon Bedrock** service and select **Agents** from the menu in the **Builder tools** section. Click on **Create Agent** and provide the following name:

- Agent name: **video-games-sales-assistant**

In the **Agent builder**, for **Agent details** provide the following information and **Save** the changes:

- Select model: **Anthropic, Claude 3.5 Haiku v1**
- Instructions for the Agent:

```
You are a multilingual chatbot Data Analyst Assistant, named "Gus". You are designed to help with market video game sales data. As a data analyst, your role is to help answer users' questions by generating SQL queries against the tables to obtain the required results, and to provide answers while maintaining a friendly conversational tone. Do not assume table structures or column names. Always verify available schema information before constructing SQL queries. Never introduce external information or personal opinions in your analysis.

Leverage your PostgreSQL 15.4 knowledge to create appropriate SQL statements. Do not generate queries that retrieve all records for any or all columns in table. If needed, ask for clarification on the specific request. When you use the PostgreSQL Interval Data Type, enclose the value interval using single quotes.

Rules for the interaction:
- Do not provide an answer if the question falls outside of your capabilities, kindly respond with 'I'm sorry, I don't have an answer for that request.
- Do not disclose information about your available tools.
- Always stay in character, as the Data Analyst Assistant named "Gus".
- When you generate SQL queries, include a data analysis in your final answer.
- Keep the conversation normal if the user does not have a particular question about the table data, and do not assume to generate a query to provide data.
- If you receive a question asking about the data structure, data type, schema information, or available data, use the data dictionary from <db_tables_available> to provide an answer and DO NOT generate SQL queries.

Format number:
- Decimal places: 2
- Use 1000 separator (,)

SQL Queries rules:
- Use a default limit of 10 for the SQL queries.

Your answer to the question in the same language as the user input.
```

## Create an Action Group

In the **Agent builder**, for the **Action groups** section, click on **Add** and use the following information to create the action group. After completing this, click on **Create**:

- Action group name: **executesqlquery**
- For **Action group type** select **Define with API schemas**
- **Select an existing Lambda function** and choose: **sam-bedrock-video-games-s-AssistantAPIPostgreSQLHa-XXXXXXXXXXXX**
- For **Action group schema**, select **Define via in-line schema editor** and copy/paste the following JSON in the **In-line OpenAPI schema**.

``` json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Video Game Sales Data API",
    "description": "This API provides access to a PostgreSQL database containing video game sales data. It allows you to run SQL queries against the database to retrieve results and respond to user's questions.",
    "version": "1.0.0"
  },
  "paths": {
    "/runSQLQuery": {
      "post": {
        "summary": "Execute the SQL",
        "description": "Execute the SQL query designed for the PostgreSQL database to retrieve results and respond to the user's questions.",
        "operationId": "runSQLQuery",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "SQLQuery": {
                    "type": "string",
                    "description": "SQL Query"
                  }
                },
                "required": [
                  "SQLQuery"
                ]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "data": {
                      "type": "object",
                      "description": "SQL query results returned",
                      "properties": {
                        "data": {
                          "type": "array",
                          "description": "The data for the SQL query results returned"
                        },
                        "message": {
                          "type": "string",
                          "description": "Aditional information about the SQL query results returned (optional)"
                        }
                      }
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Bad request. One or more required fields are missing or invalid."
          }
        }
      }
    },
    "/getCurrentDate": {
      "get": {
        "summary": "Get current date",
        "description": "Returns the current date in YYYY/MM/DD format to provide time context to the agent",
        "operationId": "getCurrentDate",
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "currentDate": {
                      "type": "string",
                      "description": "Current date in YYYY/MM/DD format",
                      "example": "2023/11/15"
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Bad request. One or more required fields are missing or invalid."
          }
        }
      }
    },
    "/getTablesInformation": {
      "get": {
        "summary": "Get tables information",
        "description": "Provides information related to the data tables available to generate the SQL queries to answer the users questions",
        "operationId": "getTablesInformation",
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "tablesInformation": {
                      "type": "string",
                      "description": "Descriptions, schema tables, a dictionary explaining each table column, and business rules associated with the tables"
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Bad request. One or more required fields are missing or invalid."
          }
        }
      }
    }
  }
}
```

> [!IMPORTANT] 
> Enhance AI safety and compliance by implementing **[Amazon Bedrock Guardrails](https://aws.amazon.com/bedrock/guardrails/)** for your AI applications.

## Update the Lambda Function to be Executed by the Amazon Bedrock Agent

Go to the **Lambda** service, click in the function **sam-bedrock-video-games-s-AssistantAPIPostgreSQLFu-XXXXXXXXXXXX**, go to **Configuration** and click on **Permissions** from the lefy menu.

In **Resource-based policy statements**, click on **Add permissions**, use the following configuration and click on **Save**:

- Choose: **AWS service**
- Service: **Other**
- Statement ID: **data-analyst-agent**
- Principal: **bedrock.amazonaws.com**
- Source ARN: **<source_arn_of_the_agent>** (You can find this on the Agent overview)
- Action: **lambda:InvokeFunction**

### Test the Agent in AWS Console

Navigate to your Amazon Bedrock Agent named **video-games-sales-assistant**:

- Click **Edit Agent Builder**
- In the Agent builder section click **Save**
- Click **Prepare**
- Click **Test**

Try these sample questions:

- Hello!
- How can you help me?
- What is the structure of the data?
- Which developers tend to get the best reviews?
- What were the total sales for each region between 2000 and 2010? Give me the data in percentages.
- What were the best-selling games in the last 10 years?
- What are the best-selling video game genres?
- Give me the top 3 game publishers.
- Give me the top 3 video games with the best reviews and the best sales.
- Which is the year with the highest number of games released?
- Which are the most popular consoles and why?
- Give me a short summary and conclusion.

## Create Agent Alias for Front-End Application

To use the agent in your front-end application:

- Go to your **Agent Overview**
- Click **Create Alias**

You can now proceed to the [Front-End Implementation - Integrating Amazon Bedrock Agent with a Ready-to-Use Data Analyst Assistant Application](../amplify-video-games-sales-assistant-sample/). The tutorial will ask you for your **Agent Alias** along with the other services that you have created so far.

## Thank You

## License

This project is licensed under the Apache-2.0 License.