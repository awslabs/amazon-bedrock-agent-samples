# A basic lambda function that just privdes a hellow world response whn invoked
import requests
import os
import pandas as pd
import numpy as np
import json
import re
import datetime
import time

#Global
grafana_base_url = os.environ.get("grafana_url")

# Function to get the epoch time n minutes ago
def get_epoch_n_minutes_ago(n):
    # Get the current time
    current_time = datetime.datetime.now()
    
    # Calculate the time n minutes ago
    time_n_minutes_ago = current_time - datetime.timedelta(minutes=n)
    
    # Convert to epoch time (seconds since January 1, 1970)
    epoch_time = int(time_n_minutes_ago.timestamp() * 1000)
    
    return epoch_time

# The annotations API provides the Dimension details within a text column with some json like string and regular string. this function helps extract that into separate columns
def extract_kv(s):
    # Extract key-value pairs from the curly braces
    kv_pairs = re.findall(r'(\w+)=([^,}]+)', s)
    # Extract B and C values
    b_value = re.search(r'B=([\d.]+)', s)
    c_value = re.search(r'C=([\d.]+)', s)
    
    # Create a dictionary with all extracted values
    result = dict(kv_pairs)
    if b_value:
        result['B'] = float(b_value.group(1))
    if c_value:
        result['C'] = float(c_value.group(1))
    
    return result


def get_all_alerts_api():
    # All the alert rules are stored in this folder. This is an optional filter
    alert_rules_folder = 'devops-agent-demo'
    
    
    # Set up the headers for authentication
    grafana_token = os.environ.get("grafana_token")
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {grafana_token}"
    }
    print(f"grafana token is {grafana_token}")
    # Endpoint for listing user repositories
    
  

    # Prometheus Rules api gets all alert rules and their status
    rules_api_url = f"{grafana_base_url}/api/prometheus/grafana/api/v1/rules"

    # Ruler API is needed to fetch the alert id. Alert id will be required in case of fetching the history of an alert
    ruler_api_url = f"{grafana_base_url}/api/ruler/grafana/api/v1/rules"
    ruler_params = {"subtype": "cortex"}

    # Make the GET request Rules API and get the data in Dataframe
    rules_response = requests.get(rules_api_url, headers=headers)
    rules_json = rules_response.json()
    rules_df = pd.DataFrame([d for d in rules_json['data']['groups'] if d["file"] == alert_rules_folder][0]['rules'])

    #Make the get request to ruler api to fetch all alerts and convert to Dataframe
    ruler_response = requests.get(ruler_api_url, headers=headers, params=ruler_params)
    ruler_json = ruler_response.json()
    ruler_details = ruler_json[alert_rules_folder][0]['rules']
    rule_id_df =  pd.DataFrame([
    {
        'title': item['grafana_alert']['title'],
        'id': item['grafana_alert']['id'],
    }
    for item in ruler_details
    ])

    # join rules_df and alert_id_df to add the alert id column
    rules_df = rules_df.join(rule_id_df.set_index('title'), on='name')

    # There is only one row per alert rule and the the dimension details within a single column named alerts.
    # Eploding it to create one row per alert, app(Dimension) combination
    rules_dimensions_df_full = rules_df.explode('alerts')

    #rename state of rules_dimensions_df_full
    rules_dimensions_df_full = rules_dimensions_df_full.rename(columns={'state':'alertState'})

    # Even after explode the alerts collumn has the dimension and other addtional details. Extract the required information from each dictionary
    alerts_df = rules_dimensions_df_full['alerts'].apply(lambda x: pd.Series({
        'App': x['labels'].get('App', ''),
        'State': x.get('state', ''),
        'ActiveAt': x.get('activeAt', '')
    }))

    # Combine the extracted information of app(dimension) into the main Datafram
    # rules_dimensions_df = pd.concat([rules_dimensions_df_full[['id', 'name','alertState', 'lastEvaluation','evaluationTime']], alerts_df], axis=1)
    rules_dimensions_df = pd.concat([rules_dimensions_df_full[['id', 'name', 'lastEvaluation','evaluationTime']], alerts_df], axis=1)

    # Reset the index
    rules_dimensions_df = rules_dimensions_df.reset_index(drop=True)

    return rules_dimensions_df


def get_alert_history_api(alert_id,relativeTimeMin):

    grafana_token = os.environ.get("grafana_token")
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json", 
    "Authorization": f"Bearer {grafana_token}"
    }
    print(f"grafana token is {grafana_token}")
    
    # Endpoint for getting rule history
    annotations_api = f"{grafana_base_url}/api/annotations"
    
    api_params = {"alertId": alert_id}
    
    #Call the api and parse response into json
    alert_history_response = requests.get(annotations_api, headers=headers, params=api_params)
    alert_history_json = alert_history_response.json()
    alert_history_df = pd.DataFrame(alert_history_json)


    # Apply the function to fetch relevant data from the text string column that has json like string and a regular string.
    alert_history_df['extracted'] = alert_history_df['text'].apply(extract_kv)

    # Create new columns from the dictionary
    alert_history_df['App'] = alert_history_df['extracted'].apply(lambda x: x.get('App', ''))
    alert_history_df['alertname'] = alert_history_df['extracted'].apply(lambda x: x.get('alertname', ''))
    alert_history_df['B'] = alert_history_df['extracted'].apply(lambda x: x.get('B', None))
    alert_history_df['C'] = alert_history_df['extracted'].apply(lambda x: x.get('C', None))

    # Drop the temporary 'extracted' column
    alert_history_df = alert_history_df.drop('extracted', axis=1)

    # alert_history_df = alert_history_df[['alertId', 'alertname','App', 'newState', 'prevState', 'updated', 'B', 'C']]
    
    # Retain needed columns
    alert_history_df = alert_history_df[['alertname','App', 'newState', 'prevState', 'updated']]
    # alert_history_df.columns = ['alertId', 'alertName','App', 'newState', 'prevState', 'updatedTime', 'Rule B Value', 'Rule C value']

    #rename Columns
    alert_history_df.columns = [ 'alertName','App', 'newState', 'prevState', 'updatedTime']

    # Get the epoch time of relative time input and filter for greater time
    epoch_time_n_minutes_ago = get_epoch_n_minutes_ago(relativeTimeMin)
    alert_history_df = alert_history_df[alert_history_df['updatedTime'] >= epoch_time_n_minutes_ago]

    # alert_history_df = alert_history_df[['alertId', 'alertName','App', 'newState', 'prevState', 'updated', 'Alert Rule B value', 'Alert Rule C value']]


    # convert column updatedTime from epoch to datetime
    alert_history_df['updatedTime'] = pd.to_datetime(alert_history_df['updatedTime'], unit='ms').dt.strftime('%d-%b-%y %H:%M:%S')


    return alert_history_df


def lambda_handler(event, context):

    print(event)
    print(type(event))

    params = {}
    if 'parameters' in event:
        params = dict((param['name'], param['value']) for param in event['parameters'])
        print(f"params is {params}")
    
    # This is an API funcation for getting all alerts  and if provided filtered by app, state
    if event['apiPath'] == '/get-alerts':
        print("IN GET ALERTS")
        alerts = get_all_alerts_api()
        print(f" Alerts before filter is {alerts}")


        #Filter only alerts of a paricular app if the app is in input
        if 'App' in params:
            print("IN APP FILTER")
            
            #Bedrock input is read as  a string. converting it into a list to iterate
            app_input = params['App']
            app_input_string = app_input.replace('[','').replace(']','').replace('"','').replace(', ',',')
            app_input_string = app_input_string.replace("<value>", "").replace("</value>", "")
            app_list = app_input_string.split(",")
            print(f"app_list is {app_list}")
            print(f"type of app_list is {type(app_list)}")

            # Iterate and filter alerts only for given app
            for app in app_list:
                print(f"app is {app}")
                mask = alerts['App']==app
                alerts = alerts[mask]

        #Filter alerts in a particular sate if state given. Use the words active and firing synonymously. 
        if 'state' in params:
            if params['state'].lower() in ['active','firing','alerting']:
                mask = alerts['State'] == 'Alerting'
                alerts = alerts[mask]
            else:
                mask = alerts['State'] == event['state']
                alerts = alerts[mask]

        print(f" Alerts after filter is {alerts}")
        
        # Send response
        response_body = {
            'application/json': {
                'body': alerts.to_json(orient='records')
            }
        }

        action_response = {
            'actionGroup': event['actionGroup'],
            'apiPath': event['apiPath'],
            'httpMethod': event['httpMethod'],
            'httpStatusCode': 200,
            'responseBody': response_body
        }

        responses = []
        responses.append(action_response)

        api_response = {
            'messageVersion': '1.0',
            'response': action_response
            }



        print(f"Api response is {api_response}")
        return api_response
    
    #Another API to get alerts in the past n minutes or a given time slot. 
    # This will get all alerts and their id, get history for all these and filter for the time slot. 


    if event['apiPath'] == '/get-alert-history':
        print("IN GET ALERT HISTORY")


        # Alert id is a mandatory input
        if 'alertId' in params:
            alert_id = params['alertId']
            print(f" alert ids is {params['alertId']}")
            print(f" type of alert ids is {type(params['alertId'])}")

            if 'relativeTimeMin' in params:
                relativeTimeMin = params['relativeTimeMin']
            else:
                relativeTimeMin = 86400 # 24 hours

            #Call alert history
            alert_history = get_alert_history_api(alert_id,relativeTimeMin)

        else:
            print("missing mandatory param")

        
        print(f" alert_history is {alert_history}")

        # Send response
        response_body = {
            'application/json': {
                'body': alert_history.to_json(orient='records')
            }
        }

        print(f"response_body is {response_body}")

        action_response = {
            'actionGroup': event['actionGroup'],
            'apiPath': event['apiPath'],
            'httpMethod': event['httpMethod'],
            'httpStatusCode': 200,
            'responseBody': response_body
        }

        responses = []
        responses.append(action_response)

        api_response = {
            'messageVersion': '1.0',
            'response': action_response
            }



        print(f"Api response is {api_response}")
        return api_response

        
# Below for local testing
if __name__ == "__main__":
    # Test the lambda handler locally
    # result = lambda_handler({'apiPath':'/get-alert-history','parameters':{'alertIds':[19]}}, {})
    result = lambda_handler({'apiPath':'/get-alert-history','parameters':[{'name': 'alertId', 'type': 'array', 'value': '19'},{'name': 'relativeTimeMin', 'type': 'Number', 'value': 5}]}, {})
    # result = lambda_handler({'apiPath':'/get-alerts'}, {})
    print(result)

