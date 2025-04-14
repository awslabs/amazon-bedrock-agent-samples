# Foursquare Location Agent
This agent is available as an open source agent to demonstrate how to use Foursquare Location Services with Amazon Bedrock Agents.


### Foursquare Service API Key
You will need a Foursquare Service API Key to allow your AI agent to access Foursquare API endpoints.
If you do not already have one, follow the instructions on
[Foursquare Doc - Manage Your Service API Keys](https://docs.foursquare.com/developer/docs/manage-service-api-keys)
to create one.

You will need to log in to your Foursquare developer account or create one if you do not have one. 
Creating a basic account is free and includes starter credit for your project. Be sure to copy the
Service API key upon creation as you will not be able to see it again

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

