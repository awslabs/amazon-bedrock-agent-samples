# Foursquare Location Agent
This agent is available as an open source agent to demonstrate how to use Foursquare Location Services with Amazon Bedrock Agents.

## Setup
Set environment variables for your Foursquare API tokens. 
```
export FOURSQUARE_SERVICE_TOKEN=xxxxx
```

Set environment variables for your AWS credentials.

```
export AWS_ACCESS_KEY_ID=xxxxx
export AWS_SECRET_ACCESS_KEY=xxxxx
```

Install requirements.
```
pip install requirements.txt
```

Start the streamlit UI
```
streamlit run agent_ui.py
```

