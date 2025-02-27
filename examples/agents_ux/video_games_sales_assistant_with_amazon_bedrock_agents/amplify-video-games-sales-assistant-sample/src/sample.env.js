// AWS Credentials

const ACCESS_KEY_ID = "";
const SECRET_ACCESS_KEY = "";
const AWS_REGION = "";

// Amazon Bedrock Agent and DynamoDB Table

const AGENT_ID = "";
const AGENT_ALIAS_ID = "";
const QUESTION_ANSWERS_TABLE_NAME = "";

// Application Information

const APP_NAME = "Data Analyst Assistant";
const APP_SUBJECT = "Video Games Sales";
const WELCOME_MESSAGE = "I'm your Video Games Sales Data Analyst, crunching data for insights.";

// --------------------------------

const MAX_LENGTH_INPUT_SEARCH = 140;
const MODEL_ID_FOR_CHART_AND_DASHBOARD = "us.anthropic.claude-3-5-sonnet-20241022-v2:0";
const CHART_PROMPT = "Help me to create chart configuartion in React.js for \"ApexCharts\" using the following information:\n\
\n\
<information>\n\
    <data_sources>\n\
        <<data_sources>>\n\
    </data_sources>\n\
    <summary>\n\
        <<answer>>\n\
    </summary>\n\
</information>\n\
\n\
For your answer include:\n\
- Provide the series and options for the React ApexCharts.\n\
- Use the appropriate chart type based on the data saources.\n\
- A caption in an summary executive-style format based on the information provided (The minimum length is 140 characters, and the maximum length is 50 words).\n\
\n\
Strict Rules:\n\
- Provide a chart configuration only if the data is enough and suitable for being presented as a chart.\n\
- If needed provide the formatter attribute in string format, always using a function.\n\
- For datetime values, use an ascending order.\n\
- Use the data sources to create the chart configuration, use the values as is.\n\
- Provide titles, subtitles or descriptions in the same language as the <summary> provided.\n\
\n\
Those are some examples of series and options depending of the chart type:\n\
<ChartExamples>\n\
  <Chart description=\"Line Basic\">\n\
    <type>line</type>\n\
    <configuartion>\n\
{\n\
   \"series\":[\n\
      {\n\
         \"name\":\"Desktops\",\n\
         \"data\":[\n\
            10,\n\
            41,\n\
            35,\n\
            51,\n\
            49,\n\
            62,\n\
            69,\n\
            91,\n\
            148\n\
         ]\n\
      }\n\
   ],\n\
   \"options\":{\n\
      \"chart\":{\n\
         \"height\":350,\n\
         \"type\":\"line\",\n\
         \"zoom\":{\n\
            \"enabled\":false\n\
         }\n\
      },\n\
      \"dataLabels\":{\n\
         \"enabled\":false\n\
      },\n\
      \"stroke\":{\n\
         \"curve\":\"straight\"\n\
      },\n\
      \"title\":{\n\
         \"text\":\"Product Trends by Month\",\n\
         \"align\":\"left\"\n\
      },\n\
      \"grid\":{\n\
         \"row\":{\n\
            \"colors\":[\n\
               \"#f3f3f3\",\n\
               \"transparent\"\n\
            ],\n\
            :0.5\n\
         }\n\
      },\n\
      \"xaxis\":{\n\
         \"categories\":[\n\
            \"Jan\",\n\
            \"Feb\",\n\
            \"Mar\",\n\
            \"Apr\",\n\
            \"May\",\n\
            \"Jun\",\n\
            \"Jul\",\n\
            \"Aug\",\n\
            \"Sep\"\n\
         ]\n\
      }\n\
   }\n\
}\n\
    </configuartion>\n\
  </Chart>\n\
\n\
  <Chart description=\"Bar Funnel\">\n\
    <type>bar</type>\n\
    <configuartion>\n\
{\n\
   \"series\":[\n\
      {\n\
         \"name\":\"Funnel Series\",\n\
         \"data\":[\n\
            1380,\n\
            1100,\n\
            990,\n\
            880,\n\
            740,\n\
            548,\n\
            330,\n\
            200\n\
         ]\n\
      }\n\
   ],\n\
   \"options\":{\n\
      \"chart\":{\n\
         \"type\":\"bar\",\n\
         \"height\":350,\n\
         \"dropShadow\":{\n\
            \"enabled\":true\n\
         }\n\
      },\n\
      \"plotOptions\":{\n\
         \"bar\":{\n\
            \"borderRadius\":0,\n\
            \"horizontal\":true,\n\
            \"barHeight\":\"80%\",\n\
            \"isFunnel\":true\n\
         }\n\
      },\n\
      \"dataLabels\":{\n\
         \"enabled\":true,\n\
         \"formatter\":\"function (val, opt) { return opt.w.globals.labels[opt.dataPointIndex] + ':  ' + val }\",\n\
         \"dropShadow\":{\n\
            \"enabled\":true\n\
         }\n\
      },\n\
      \"title\":{\n\
         \"text\":\"Recruitment Funnel\",\n\
         \"align\":\"middle\"\n\
      },\n\
      \"xaxis\":{\n\
         \"categories\":[\n\
            \"Sourced\",\n\
            \"Screened\",\n\
            \"Assessed\",\n\
            \"HR Interview\",\n\
            \"Technical\",\n\
            \"Verify\",\n\
            \"Offered\",\n\
            \"Hired\"\n\
         ]\n\
      },\n\
      \"legend\":{\n\
         \"show\":false\n\
      }\n\
   }\n\
}\n\
    <configuartion>\n\
  </Chart>\n\
\n\
  <Chart description=\"Bar Basic\">\n\
    <type>bar</type>\n\
    <configuartion>\n\
{\n\
   \"series\":[\n\
      {\n\
         \"data\":[\n\
            400,\n\
            430,\n\
            448,\n\
            470,\n\
            540,\n\
            580,\n\
            690,\n\
            1100,\n\
            1200,\n\
            1380\n\
         ]\n\
      }\n\
   ],\n\
   \"options\":{\n\
      \"chart\":{\n\
         \"type\":\"bar\",\n\
         \"height\":350\n\
      },\n\
      \"plotOptions\":{\n\
         \"bar\":{\n\
            \"borderRadius\":4,\n\
            \"borderRadiusApplication\":\"end\",\n\
            \"horizontal\":true\n\
         }\n\
      },\n\
      \"dataLabels\":{\n\
         \"enabled\":false\n\
      },\n\
      \"xaxis\":{\n\
         \"categories\":[\n\
            \"South Korea\",\n\
            \"Canada\",\n\
            \"United Kingdom\",\n\
            \"Netherlands\",\n\
            \"Italy\",\n\
            \"France\",\n\
            \"Japan\",\n\
            \"United States\",\n\
            \"China\",\n\
            \"Germany\"\n\
         ]\n\
      }\n\
   }\n\
}\n\
    <configuartion>\n\
  </Chart>\n\
\n\
  <Chart description=\"Simple Pie\">\n\
    <type>pie</type>\n\
    <configuartion>\n\
{\n\
  \"series\": [2077, 1036.75, 384.99, 277.49],\n\
  \"options\": {\n\
    \"chart\": {\n\
      \"type\": \"pie\",\n\
      \"height\": 380\n\
    },\n\
    \"labels\": [\"North America\", \"Europe\", \"Other Regions\", \"Japan\"],\n\
    \"title\": {\n\
      \"text\": \"Video Game Sales Distribution by Region (2000-2010)\",\n\
      \"align\": \"center\"\n\
    },\n\
    \"subtitle\": {\n\
      \"text\": \"Total Global Sales: 3,779.72 million units\",\n\
      \"align\": \"center\"\n\
    },\n\
    \"dataLabels\": {\n\
      \"enabled\": true,\n\
      \"formatter\": \"function (val, opt) { return opt.w.config.labels[opt.seriesIndex] + ': ' + val.toFixed(2) + '%' }\"\n\
    },\n\
    \"legend\": {\n\
      \"position\": \"bottom\"\n\
    },\n\
    \"colors\": [\"#008FFB\", \"#00E396\", \"#FEB019\", \"#FF4560\"]\n\
  }\n\
}\n\
    <configuartion>\n\
  </Chart>\n\
\n\
</ChartExamples>\n\
\n\
Use the following format for your answer if you have a chart configuration:\n\
\n\
- If you have a chart configuration use this format:\n\
<has_chart>1</has_chart>\n\
<chart_type></chart_type>\n\
<chart_configuration>(Attributes and string values should be enclosed between double quotes for the JavaScript array/object format.)</chart_configuration>\n\
<caption></caption>\n\
\n\
- If you do not have a chart configuration use this format:\n\
<has_chart>0</has_chart>\n\
<rationale>The reason to do not generate a chart configuration, max 12 words</rationale>";

export { AGENT_ID, 
    AGENT_ALIAS_ID, 
    CHART_PROMPT, 
    QUESTION_ANSWERS_TABLE_NAME, 
    APP_NAME, APP_SUBJECT, 
    WELCOME_MESSAGE, 
    MODEL_ID_FOR_CHART_AND_DASHBOARD, 
    MAX_LENGTH_INPUT_SEARCH,
    ACCESS_KEY_ID,
    SECRET_ACCESS_KEY,
    AWS_REGION
};