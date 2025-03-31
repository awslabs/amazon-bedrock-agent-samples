from datetime import datetime, timedelta

today = datetime.today().strftime("%Y-%m-%d")
print(f"Today's date is: {today}")


def get_named_parameter(event, name):
    if "parameters" in event:
        return next(item for item in event["parameters"] if item["name"] == name)[
            "value"
        ]
    else:
        return None


def populate_function_response(event, response_body):
    return {
        "response": {
            "actionGroup": event["actionGroup"],
            "function": event["function"],
            "functionResponse": {
                "responseBody": {"TEXT": {"body": str(response_body)}}
            },
        }
    }


def get_contract_status(contract_id):
    # TODO: Implement real business logic to retrieve contract status
    return {
        "contract_id": contract_id,
        "status": "Active",
        "compliance_status": "Compliant",
        "last_reviewed_date": str(datetime.today() - timedelta(days=30)).split(" ")[0],
        "next_review_date": str(datetime.today() + timedelta(days=60)).split(" ")[0],
        "days_until_expiration": 180,
        "renewal_status": "Auto-renewal enabled",
    }


def get_contract_details(contract_id):
    # TODO: Implement real business logic to retrieve contract details
    return {
        "contract_id": contract_id,
        "contract_type": "Service Agreement",
        "start_date": "2024-01-01",
        "end_date": "2025-12-31",
        "contract_value": 75000.00,
        "payment_terms": "Net 30",
        "billing_frequency": "Monthly",
        "parties": {"customer": "ABC Corporation", "provider": "XYZ Services Ltd"},
        "key_terms": ["24/7 Support", "99.9% Uptime SLA", "Monthly reporting"],
    }


def lambda_handler(event, context):
    print(event)
    function = event["function"]

    if function in ["get_contract_status", "get_contract_details"]:
        contract_id = get_named_parameter(event, "contract_id")
        if not contract_id:
            # pull contract_id from session state variables if it was not supplied
            session_state = event["sessionAttributes"]
            if session_state is None:
                result = "I'm sorry, but I can't get the contract information without a contract ID"
            else:
                if "contract_id" in session_state:
                    contract_id = session_state["contract_id"]
                else:
                    result = "I'm sorry, but I can't get the contract information without a contract ID"
            print(f"contract_id was pulled from session state variable = {contract_id}")

        if function == "get_contract_status":
            result = get_contract_status(contract_id)
        else:  # get_contract_details
            result = get_contract_details(contract_id)
    else:
        result = f"Error, function '{function}' not recognized"

    response = populate_function_response(event, result)
    print(response)
    return response
