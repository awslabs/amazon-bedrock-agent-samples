forecast_functions = [
    {
        "name": "get_forecasted_consumption",
        "description": """Gets the next 3 months energy usage forecast""",
        "parameters": {
            "customer_id": {
                "description": "Unique customer identifier",
                "required": True,
                "type": "string",
            }
        },
    },
    {
        "name": "get_historical_consumption",
        "description": """Gets energy usage history to date""",
        "parameters": {
            "customer_id": {
                "description": "Unique customer identifier",
                "required": True,
                "type": "string",
            }
        },
    },
    {
        "name": "get_consumption_statistics",
        "description": """Gets current month usage analytics""",
        "parameters": {
            "customer_id": {
                "description": "Unique customer identifier",
                "required": True,
                "type": "string",
            }
        },
    },
    {
        "name": "update_forecasting",
        "description": """Updates the energy forecast for a specific month""",
        "parameters": {
            "customer_id": {
                "description": "Unique customer identifier",
                "required": True,
                "type": "string",
            },
            "month": {
                "description": "Target update month. In the format MM",
                "required": True,
                "type": "integer",
            },
            "year": {
                "description": "Target update year. In the format YYYY",
                "required": True,
                "type": "integer",
            },
            "usage": {
                "description": "New consumption value",
                "required": True,
                "type": "integer",
            },
        },
    },
]

peak_functions = [
    {
        "name": "detect_peak",
        "description": """detect consumption peak during current month""",
        "parameters": {
            "customer_id": {
                "description": "The ID of the customer",
                "required": True,
                "type": "string",
            }
        },
    },
    {
        "name": "detect_non_essential_processes",
        "description": """detect non-essential processes that are causing the peaks""",
        "parameters": {
            "customer_id": {
                "description": "The ID of the customer",
                "required": True,
                "type": "string",
            }
        },
    },
    {
        "name": "redistribute_allocation",
        "description": """reduce/increase allocated quota for a specific 
                            item during current month""",
        "parameters": {
            "customer_id": {
                "description": "The ID of the customer",
                "required": True,
                "type": "string",
            },
            "item_id": {
                "description": "Item that will be updated",
                "required": True,
                "type": "string",
            },
            "quota": {"description": "new quota", "required": True, "type": "string"},
        },
    },
]
