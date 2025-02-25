from datetime import datetime, timedelta

today = datetime.today().strftime('%Y-%m-%d')
print(f"Today's date is: {today}")

def get_named_parameter(event, name):
    if 'parameters' in event:
        return next(item for item in event['parameters'] if item['name'] == name)['value']
    else:
        return None
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def get_mortgage_status(customer_id):
    # TODO: Implement real business logic to retrieve mortgage status
    return {
        "account_number": customer_id,
        "outstanding_principal": 150599.25,
        "interest_rate": 8.5,
        "maturity_date": "2030-06-30",
        "original_issue_date": "2021-05-30",
        "payments_remaining": 72,
        "last_payment_date": str(datetime.today() - timedelta(days=14)).split(' ')[0],
        "next_payment_due": str(datetime.today() + timedelta(days=14)).split(' ')[0],
        "next_payment_amount": 1579.63
    }

def lambda_handler(event, context):
    print(event)
    function = event['function']
    if function == 'get_mortgage_status':
        customer_id = get_named_parameter(event, 'customer_id')
        if not customer_id:
            # pull customer_id from session state variables if it was not supplied
            session_state = event['sessionAttributes']
            if session_state is None:
                result = "I'm sorry, but I can't get the status of your mortgage without your customer ID"
            else:
                if 'customer_id' in session_state:
                    customer_id = session_state['customer_id']
                else:
                    result = "I'm sorry, but I can't get the status of your mortgage without your customer ID"
            print(f"customer_id was pulled from session state variable = {customer_id}")
        result = get_mortgage_status(customer_id)
    else:
        result = f"Error, function '{function}' not recognized"

    response = populate_function_response(event, result)
    print(response)
    return response
