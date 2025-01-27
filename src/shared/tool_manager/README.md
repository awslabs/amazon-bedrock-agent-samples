# Tool Manager

Tool Manager is a utility for managing Bedrock Agent tools in AWS DynamoDB. It provides a simple interface to register, unregister, list, and get details about tools that can be used with Amazon Bedrock Agents.

## Features

- Register tools from a JSON definition file
- Unregister existing tools
- List all registered tools
- Get detailed information about specific tools
- Configurable DynamoDB table name and AWS region

## Prerequisites

- Python 3.7 or higher
- AWS credentials configured

## Installation

Clone the repository and ensure you have the required dependencies installed:

```bash
git clone https://github.com/awslabs/amazon-bedrock-agent-samples

cd amazon-bedrock-agent-samples/src/shared/tool_manager

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r requirements.txt

# On Unix/Linux, set the script to be executable
chmod ug+x tool_manager.py 

# You should first create the tool management table
./tool_manager.py create_table
```
  
## Usage 
The Tool Manager supports the following commands:

```shell
# Display usage help
./tool_manager.py
./tool_manager.py --help

# Create the tool management table. 
# You can supply optional --region and --table-name arguments if needed
./tool_manager.py create-table

# Register tools from a JSON file (see file format)
./tool_manager.py register tools.json

# List all registered tools
./tool_manager.py list-tools

# Get details about a specific tool
./tool_manager.py get mytool

# Unregister a tool. This leaves the lambda in place.
./tool_manager.py unregister mytool

# Delete the tool management table if needed (unregisters all tools)
./tool_manager.py delete-table
```

## Optional Parameters
* --table-name: Specify a custom DynamoDB table name (default: "agent-tools")

* --region: Specify AWS region (default: "us-west-2")

## Tool Definition File Format
Tools are defined in JSON format. Here's an example structure:
```JSON
{
    "code": "arn:aws:lambda:region:account:function:stock_data_lookup",
    "definition": [
        {
            "name": "stock_data_lookup",
            "description": "Gets stock price history for a given ticker",
            "parameters": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol",
                    "required": true
                }
            }
        }
    ]
}
```
See example_tool_definition.py.

## DynamoDB Schema
The tool definitions are stored in DynamoDB with the following attributes:

* **tool_name** : The unique identifier for the tool (Partition Key)

* **description** : A description of the tool's functionality

* **tool_code** : The ARN of the Lambda function implementing the tool

* **tool_definition** : JSON object describing the tool's parameters

## License
This project is licensed under the Apache-2.0 License.