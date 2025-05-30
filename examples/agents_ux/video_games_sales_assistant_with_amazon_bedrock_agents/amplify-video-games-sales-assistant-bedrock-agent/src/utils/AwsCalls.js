import { DynamoDBClient, QueryCommand } from "@aws-sdk/client-dynamodb";
import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";
import {
  BedrockAgentRuntimeClient,
  InvokeAgentCommand,
} from "@aws-sdk/client-bedrock-agent-runtime";
import { createAwsClient } from "./AwsAuth";
import { extractBetweenTags, removeCharFromStartAndEnd, handleFormatter } from "./Utils.js";
import {
  AGENT_ID,
  AGENT_ALIAS_ID,
  QUESTION_ANSWERS_TABLE_NAME,
  MODEL_ID_FOR_CHART,
  CHART_PROMPT
} from "../env.js";

/**
 * Query data from DynamoDB
 *
 * @param {string} id - The ID to query
 * @returns {Promise<Object>} - The query response
 */
export const getQueryResults = async (queryUuid = "") => {
  let queryResults = [];
  try {
    const dynamodb = await createAwsClient(DynamoDBClient);

    const input = {
      TableName: QUESTION_ANSWERS_TABLE_NAME,
      KeyConditionExpression: "id = :queryUuid",
      ExpressionAttributeValues: {
        ":queryUuid": {
          S: queryUuid,
        },
      },
      ConsistentRead: true,
    };

    console.log("------- Get Query Results -------");
    console.log(input);

    const command = new QueryCommand(input);
    const response = await dynamodb.send(command);

    if (response.hasOwnProperty("Items")) {
      for (let i = 0; i < response.Items.length; i++) {
        queryResults.push({
          query: response.Items[i].query.S,
          query_results: JSON.parse(response.Items[i].data.S).result,
        });
      }
    }

    return queryResults;
  } catch (error) {
    console.error("Error querying DynamoDB:", error);
    throw error;
  }
};

/**
 * Invoke an AWS Bedrock agent
 *
 * @param {string} sessionId - The session ID
 * @param {string} inputText - The text to send to the agent
 * @returns {Promise<Object>} - The agent response with comprehensive data
 */
export const invokeBedrockAgent = async (
  sessionId,
  inputText = "",
  setAnswers,
  setControlAnswers,
  userName = "",
  queryUuid = ""
) => {
  try {
    const bedrock = await createAwsClient(BedrockAgentRuntimeClient);

    const input = {
      agentId: AGENT_ID,
      agentAliasId: AGENT_ALIAS_ID,
      sessionId,
      inputText,
      sessionState: {
        promptSessionAttributes: {
          userName: userName,
          queryUuid: queryUuid,
        },
      },
      enableTrace: true,
    };

    const command = new InvokeAgentCommand(input);
    console.log("------- Invoke Agent -------");
    console.log(command);

    let completion = "";
    let runningTraces = [];
    let countRationals = 0;

    const response = await bedrock.send(command);
    if (response.completion === undefined) {
      throw new Error("Completion is undefined");
    }

    for await (let chunkEvent of response.completion) {
      //console.log("------- Invoke Agent - Chunk Response -------");
      //console.log("Full chunk event structure:", JSON.stringify(chunkEvent));
      if (chunkEvent.chunk) {
        const chunk = chunkEvent.chunk;
        const decodedResponse = new TextDecoder("utf-8").decode(chunk.bytes);
        completion += decodedResponse;
      }

      if (chunkEvent.trace) {
        runningTraces = [...runningTraces, chunkEvent.trace.trace];

        if (chunkEvent.trace.trace.orchestrationTrace?.rationale?.text) {
          console.log("-----rationale------");
          console.log(
            chunkEvent.trace.trace.orchestrationTrace?.rationale?.text
          );
          countRationals++;
          setAnswers((prevState) => [
            ...prevState,
            {
              rationaleText:
                chunkEvent.trace.trace.orchestrationTrace?.rationale?.text,
            },
          ]);
          setControlAnswers((prevState) => [...prevState, {}]);
        }
      }
    }

    // Calculate token usage
    let usage = [];
    let totalInputTokens = 0;
    let totalOutputTokens = 0;

    for (const trace of runningTraces) {
      if (trace.orchestrationTrace?.modelInvocationOutput?.metadata?.usage) {
        usage.push(
          trace.orchestrationTrace?.modelInvocationOutput?.metadata?.usage
        );
        totalInputTokens +=
          trace.orchestrationTrace?.modelInvocationOutput?.metadata?.usage
            .inputTokens;
        totalOutputTokens +=
          trace.orchestrationTrace?.modelInvocationOutput?.metadata?.usage
            .outputTokens;
      }
    }

    console.log("------- Invoke Agent - Traces -------");
    console.log(runningTraces);
    console.log("------- Invoke Agent - Completion -------");
    console.log(completion);
    return {
      sessionId,
      completion,
      usage,
      totalInputTokens,
      totalOutputTokens,
      runningTraces,
      countRationals
    };
  } catch (error) {
    console.error("Error invoking Bedrock agent:", error);
    throw error;
  }
};


/**
 * Generates a chart based on answer and data
 * @param {Object} answer - Answer object containing text
 * @returns {Object} Chart configuration or rationale for no chart
 */
export const generateChart = async (
  answer
) => {
  const bedrock = await createAwsClient(BedrockRuntimeClient);
  let query_results = "";
  for (let i = 0; i < answer.queryResults.length; i++) {
    query_results += JSON.stringify(answer.queryResults[i].query_results) + "\n";
  }

  // Prepare the prompt
  let new_chart_prompt = CHART_PROMPT.replace(
    /<<answer>>/i,
    answer.text
  ).replace(/<<data_sources>>/i, query_results);

  const payload = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 2000,
    temperature: 1,
    messages: [
      {
        role: "user",
        content: [{ type: "text", text: new_chart_prompt }],
      },
    ],
  };

  try {
    // Send the request to Bedrock
    console.log("------- Request chart -------");
    console.log(payload);

    const command = new InvokeModelCommand({
      contentType: "application/json",
      body: JSON.stringify(payload),
      modelId: MODEL_ID_FOR_CHART,
    });

    const apiResponse = await bedrock.send(command);
    const decodedResponseBody = new TextDecoder().decode(apiResponse.body);
    const responseBody = JSON.parse(decodedResponseBody).content[0].text;

    console.log("------- Response chart generation -------");
    console.log(responseBody);

    // Process the response
    const has_chart = parseInt(extractBetweenTags(responseBody, "has_chart"));

    if (has_chart) {
      const chartConfig = JSON.parse(
        extractBetweenTags(responseBody, "chart_configuration")
      );
      const chart = {
        chart_type: removeCharFromStartAndEnd(
          extractBetweenTags(responseBody, "chart_type"),
          "\n"
        ),
        chart_configuration: handleFormatter(chartConfig),
        caption: removeCharFromStartAndEnd(
          extractBetweenTags(responseBody, "caption"),
          "\n"
        ),
      };

      console.log("------- Final chart generation -------");
      console.log(chart);
      
      return chart;
    } else {
      return {
        rationale: removeCharFromStartAndEnd(
          extractBetweenTags(responseBody, "rationale"),
          "\n"
        ),
      };
    }
  } catch (error) {
    console.error("Chart generation failed:", error);
    return {
      rationale: "Error generating or parsing chart data.",
    };
  }
};


