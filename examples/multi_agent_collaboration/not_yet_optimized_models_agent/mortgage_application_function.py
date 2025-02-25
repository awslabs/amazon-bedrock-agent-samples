import json
from datetime import datetime, timedelta
import random

BASE_RATE=6.00

RATE_MIN_15=38
RATE_MAX_15=48

RATE_MIN_30=RATE_MIN_15 + 80
RATE_MAX_30=RATE_MAX_15 + 80

NO_CUSTOMER_MESSAGE = "Invalid function call, since no customer ID was provided as a parameter, and it was not passed in session state."

def get_named_parameter(event, name):
    if 'parameters' in event:
        if event['parameters']:
            for item in event['parameters']:
                if item['name'] == name:
                    return item['value']
        return None
    else:
        return None
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def get_mortgage_app_doc_status(customer_id):
    # TODO: Implement the actual logic to retrieve the document status for the given customer ID
    return [
        {
            "type": "proof_of_income",
            "status": "COMPLETED"
        },
        {
            "type": "employment_information",
            "status": "MISSING"
        },
        {
            "type": "proof_of_assets",
            "status": "COMPLETED"
        },
        {
            "type": "credit_information",
            "status": "COMPLETED"
        }
    ]

def get_mortgage_rate_history(day_count: int=30, type: str="15-year-fixed"):
    print(f"getting rate history for: {day_count} days, for type: {type}...")
    # generate the last 7 working day dates starting with yesterday
    today = datetime.today()
    history_count = 0
    rate_history = []

    if type == "30-year-fixed":
        RATE_MIN = RATE_MIN_30
        RATE_MAX = RATE_MAX_30
    else:
        RATE_MIN = RATE_MIN_15
        RATE_MAX = RATE_MAX_15

    for i in range(int(day_count*1.4)):
        if history_count >= day_count:
            break
        else:
            day = today - timedelta(days=i+1)
            which_day_of_week = day.weekday()
            if which_day_of_week < 5:
                history_count += 1
                _date = str(day.strftime("%Y-%m-%d"))
                _rate = f"{BASE_RATE + ((random.randrange(RATE_MIN, RATE_MAX))/100):.2f}"
                rate_history.append({"date": _date, "rate": _rate})

    return rate_history

def get_application_details(customer_id):
    return {
        "customer_id": customer_id,
        "application_id": "998776",
        "application_date": datetime.today() - timedelta(days=35), # simulate app started 35 days ago
        "application_status": "IN_PROGRESS",
        "application_type": "NEW_MORTGAGE",
        "application_amount": 750000,
        "application_tentative_rate": 5.5,
        "application_term_years": 30,
        "application_rate_type": "fixed",
    }

def lambda_handler(event, context):
    print(event)
    function = event['function']

    if function == 'get_mortgage_rate_history':
        day_count = get_named_parameter(event, 'day_count')
        if day_count is not None:
            day_count = int(day_count)
        result = get_mortgage_rate_history(day_count)
        print(f"get_mortgage_rate_history({day_count}) = {result}")

    elif function == 'get_mortgage_app_doc_status':
        customer_id = get_named_parameter(event, 'customer_id')
        if not customer_id:
            # pull customer_id from session state variables if it was not supplied
            session_state = event['sessionAttributes']
            if session_state is None:
                return NO_CUSTOMER_MESSAGE
            else:
                if 'customer_id' in session_state:
                    customer_id = session_state['customer_id']
                else:
                    # return NO_CUSTOMER_MESSAGE
                    # for now, graceully just default, since this is just a toy example
                    customer_id = "123456"
            print(f"customer_id was pulled from session state variable = {customer_id}")
        result = get_mortgage_app_doc_status(customer_id)

    elif function == 'get_application_details':
        customer_id = get_named_parameter(event, 'customer_id')
        if not customer_id:
            # pull customer_id from session state variables if it was not supplied
            session_state = event['sessionAttributes']
            if session_state is None:
                return NO_CUSTOMER_MESSAGE
            else:
                if 'customer_id' in session_state:
                    customer_id = session_state['customer_id']
                else:
                    # return NO_CUSTOMER_MESSAGE
                    # for now, graceully just default, since this is just a toy example
                    customer_id = "123456"
            print(f"customer_id was pulled from session state variable = {customer_id}")
        result = get_application_details(customer_id)

    else:
        raise Exception(f"Unrecognized function: {function}")


    response = populate_function_response(event, result)
    print(response)
    return response