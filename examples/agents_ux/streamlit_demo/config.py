import datetime

# Bot configurations
bot_configs = [
    {
        "bot_name": "Restaurant Bookings React",
        "agent_name": "restaurant-a-react",
        "start_prompt": "Can you make a reservation for 2 people, at 7pm tonight?"
    }, 
    {
        "bot_name": "Restaurant Bookings Rewoo",
        "agent_name": "restaurant-a-rewoo",
        "start_prompt": "Can you make a reservation for 2 people, at 7pm tonight?"
    },        
    {
        "bot_name": "Portfolio Assistant",
        "agent_name": "portfolio_assistant",
        "start_prompt": "What stock ticker would you like to analyze?"
    },
    {
        "bot_name": "Sports Team Poet",
        "agent_name": "sports_team_poet",
        "start_prompt": "Name a sports team and I'll give you a cool poem."
    },
    {
        "bot_name": "Trip Planner",
        "agent_name": "trip_planner",
        "start_prompt": "Tell me where you are going and for how long. I'll give you a great itinerary."
    },
    {
        "bot_name": "Voyage Virtuoso",
        "agent_name": "voyage_virtuoso",
        "start_prompt": "Describe the exotic and elite trip you want and I'll give you some top options."
    },
    {
        "bot_name": "Mortgages Assistant",
        "agent_name": "mortgages_assistant",
        "start_prompt": "I'm your mortgages assistant. How can I help today?",
        "session_attributes": {
            "sessionAttributes": {
                "customer_id": "123456",
                "todays_date": datetime.datetime.now().strftime("%Y-%m-%d")
            },
            "promptSessionAttributes": {
                "customer_id": "123456",
                "customer_preferred_name": "Mark",
                "todays_date": datetime.datetime.now().strftime("%Y-%m-%d")
            }
        }
    }
]
