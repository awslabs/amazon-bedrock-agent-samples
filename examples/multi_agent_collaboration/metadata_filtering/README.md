# Amazon Bedrock Multi Agent with metadata filtering

In many cases, builders would like to refine the results returned by the agent group by providing [metadata to filter results from the knowledge base](https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-knowledge-bases-now-supports-metadata-filtering-to-improve-retrieval-accuracy/).

This sample shows how to create an Amazon Bedrock Multi-Agent setup that can answer questions from multiple documents using a Lambda Action group. Using a single knowledge based each agent retrieves only the documents that are pertinent to them. The architecture utilized action groups and the RetrieveAndGenerate API call with metadata filtering.

## Architecture Overview

## Architecture
![Architecture](./metadatafiltering.png)

The solution consists of:
- An Orchestrator Agent that routes queries to appropriate sub-agents
- Two sub-agents Agent1 (2020 specialist) and Agent2 (2023 specialist)
- A Lambda function acting as an Action Group in both sub-agents, that processes queries using the Bedrock Knowledge Base's RetrieveAndGenerate API call.
- A knowledge base containing the shareholder letters and the metadata json file for each letter.

## Prerequisites

- AWS Account with appropriate permissions 
- AWS CLI configured with appropriate credentials
- Python 3.11 or later
- The following AWS services enabled:
  - Amazon Bedrock
  - AWS Lambda
  - IAM
  - Amazon S3
    
For more details on how to enable Amazon Bedrock model access and how to configure credentials see [Getting started with Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html)


## Setup Instructions

1. Clone and install repository
```
git clone https://github.com/awslabs/amazon-bedrock-agent-samples

cd amazon-bedrock-agent-samples

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r src/requirements.txt

cd examples/multi_agent_collaboration/metadata_filtering/

pip3 install -r requirements.txt
```


2. Create a bucket
```aws s3 mb s3://<your bucket name>```

3. Download shareholder letters and copy them to the S3 bucket created and create the corresponding metadata file.

This step downloads the Amazon Letters to Shareholders for 2020 and 2023 from [aboutamazon.com](https://ir.aboutamazon.com/annual-reports-proxies-and-shareholder-letters/default.aspx):

- Amazon-Shareholder-Letter-2023.pdf
- Amazon-Shareholder-Letter-2020.pdf

```python data_source_creation.py```

```aws s3 cp ./data_sources/ s3://BUCKET_NAME/ --recursive```


4. Configure environment variables:
```
export AWS_PROFILE=your-profile
export AWS_REGION=your-region
export S3_BUCKET_NAME=your-bucket-name
```


5. Deploy the solution:
```
python setup_agents.py --bucket <your bucket name> --account-id <your account ID>
```
Keep note of the orchestrator's ID and alias ID since we will need to use it in the next step

6. Test the Solution:

```
python invoke_agent.py --agent-id <your agent ID> --agent-alias-id <your agent alias ID> --query "<your query>" 
```

Replace the agent Id and Agent Alias ID with the info returned in Step #3.

A sample query could be: 
- "What is the plan for 2023?"
- "What is the plan for 2020?"

7. Project Structure
```bash
.
├── README.md
├── requirements.txt
├── knowledge_base_helper.py
├── setup_agents.py
├── data_souoce_creation.py
├── openapi_schema.yaml
|── invoke_agent.py/
```

## Clean up:

To clean up ONLY the resources created, run the below command.
```
python cleanup.py --delete-bucket <True or False> --bucket <your bucket> --account-id <your account ID>
```

* Note --delete-bucket will be used to determine weather to delete the S3 bucket or not.
* Note that the regions is set to the region you configure, to check your region run ```aws configure```


## Contributers:
[x] Omar Elkharbotly
[x] Anna Gruebler
[x] Maira Ladeira Tanke