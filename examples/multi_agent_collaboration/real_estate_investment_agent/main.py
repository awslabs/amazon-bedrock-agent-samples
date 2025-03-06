#!/usr/bin/env python

# Copyright 2025 Amazon.com and its affiliates; all rights reserved.
# This file is AWS Content and may not be duplicated or distributed without permission
import sys
from pathlib import Path
import argparse
import yaml
import os
import datetime
import uuid
import json
import traceback
from textwrap import dedent

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.bedrock_agent import Agent, SupervisorAgent, Task, region, account_id

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
task_yaml_path = os.path.join(current_dir, "tasks.yaml")
agent_yaml_path = os.path.join(current_dir, "agents.yaml")


def main(args):
    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
        if not Agent.exists("investment_advisor"):
            print(
                "'investment_advisor' agent does not exist. Please rerun with --recreate_agents 'true'"
            )
            return
    else:
        Agent.set_force_recreate_default(True)
        Agent.delete_by_name("investment_advisor", verbose=True)

    if args.clean_up == "true":
        Agent.delete_by_name("investment_advisor", verbose=True)
        Agent.delete_by_name("property_researcher", verbose=True)
        Agent.delete_by_name("financial_analyst", verbose=True)
        Agent.delete_by_name("market_intelligence", verbose=True)
    else:
        # Define input parameters for the analysis
        inputs = {
            "address": args.address,
            "property_type": args.property_type,
            "investment_goal": args.investment_goal,
            "budget_range": args.budget_range,
            "purchase_price": args.purchase_price,
            "down_payment": args.down_payment,
            "target_roi": args.target_roi,
            "investment_timeline": args.investment_timeline,
            "expected_rental": args.expected_rental,
            "market_area": args.market_area,
        }

        # Load tasks from YAML
        with open(task_yaml_path, "r") as file:
            yaml_task_content = yaml.safe_load(file)

        # Create task objects
        property_research_task = Task(
            "property_research_task", yaml_task_content, inputs
        )
        market_intelligence_task = Task(
            "market_intelligence_task", yaml_task_content, inputs
        )
        financial_analysis_task = Task(
            "financial_analysis_task", yaml_task_content, inputs
        )
        investment_recommendation_task = Task(
            "investment_recommendation_task", yaml_task_content, inputs
        )

        # Define tool definitions
        property_data_tools = [
            {
                "name": "property_lookup",
                "description": "Retrieves property information, valuation, or rent estimates",
                "parameters": {
                    "address": {
                        "description": "The property address to look up in the format Street, City, State, Zip",
                        "type": "string",
                        "required": True,
                    },
                    "data_type": {
                        "description": "Type of data to retrieve (property_data, value_estimate, rent_estimate)",
                        "type": "string",
                        "required": True,
                    },
                    "propertyType": {
                        "description": "Needed when data_type=value_estimate or rent_estimate. The type of property obtained with data_type=property_data",
                        "type": "string",
                        "required": False,
                    },
                    "bedrooms": {
                        "description": "Needed when data_type=value_estimate or rent_estimate. The number of bedrooms in the property obtained with data_type=property_data",
                        "type": "string",
                        "required": False,
                    },
                    "squareFootage": {
                        "description": "Needed when data_type=value_estimate or rent_estimate. The total living area size of the property, in square feet obtained with data_type=property_data",
                        "type": "string",
                        "required": False,
                    },
                },
            },
            {
                "name": "market_data_lookup",
                "description": "Retrieves market statistics for a specific area",
                "parameters": {
                    "zip_code": {
                        "description": "The 5-digit zip code to look up",
                        "type": "string",
                        "required": True,
                    },
                    "data_type": {
                        "description": "Type of data to retrieve (Sale, Rental)",
                        "type": "string",
                        "required": True,
                    },
                },
            },
            {
                "name": "investment_analysis",
                "description": "Performs real estate investment calculations",
                "parameters": {
                    "investment_data": {
                        "description": "JSON string containing investment parameters (purchase_price, down_payment_percent, interest_rate, term_years, rental_income, property_taxes, insurance, maintenance, vacancy_rate, property_management, hoa)",
                        "type": "string",
                        "required": True,
                    },
                    "analysis_type": {
                        "description": "Type of analysis to perform: 'mortgage_calc' (mortgage payment details), 'cash_flow' (monthly income/expenses), 'roi' (return on investment metrics), or 'all' (default: all analyses)",
                        "type": "string",
                        "required": False,
                    },
                },
            },
        ]

        economic_data_tools = [
            {
                "name": "series_observations",
                "description": "Gets observations or data values for an economic data series",
                "parameters": {
                    "series_id": {
                        "description": "The FRED series ID for the economic indicator",
                        "type": "string",
                        "required": True,
                    },
                    "units": {
                        "description": "Data value transformation (lin=no transformation, pch=percent change, ph1=percent change from year ago)",
                        "type": "string",
                        "required": False,
                    },
                },
            },
            {
                "name": "series_search",
                "description": "Search for economic data series that match keywords",
                "parameters": {
                    "search_text": {
                        "description": "Keywords to match against economic data series",
                        "type": "string",
                        "required": True,
                    },
                    "limit": {
                        "description": "Maximum number of series to return (default: 10)",
                        "type": "string",
                        "required": False,
                    },
                },
            },
        ]

        # Define web search tool
        web_search_tool = {
            "code": f"arn:aws:lambda:{region}:{account_id}:function:web_search",
            "definition": {
                "name": "web_search",
                "description": "Searches the web for information",
                "parameters": {
                    "search_query": {
                        "description": "The query to search the web with",
                        "type": "string",
                        "required": True,
                    },
                    "target_website": {
                        "description": "The specific website to search including its domain name. If not provided, the most relevant website will be used",
                        "type": "string",
                        "required": False,
                    },
                    "topic": {
                        "description": "The topic being searched. 'news' or 'general'. Helps narrow the search when news is the focus.",
                        "type": "string",
                        "required": False,
                    },
                    "days": {
                        "description": "The number of days of history to search. Helps when looking for recent events or news.",
                        "type": "string",
                        "required": False,
                    },
                },
            },
        }

        # Define working memory tools
        set_value_for_key = {
            "code": f"arn:aws:lambda:{region}:{account_id}:function:working_memory",
            "definition": {
                "name": "set_value_for_key",
                "description": "Stores a key-value pair table. Creates the table if it doesn't exist.",
                "parameters": {
                    "key": {
                        "description": "The name of the key to store the value under.",
                        "type": "string",
                        "required": True,
                    },
                    "value": {
                        "description": "The value to store for that key name.",
                        "type": "string",
                        "required": True,
                    },
                    "table_name": {
                        "description": "The name of the table to use for storage.",
                        "type": "string",
                        "required": True,
                    },
                },
            },
        }

        get_key_value = {
            "code": f"arn:aws:lambda:{region}:{account_id}:function:working_memory",
            "definition": {
                "name": "get_key_value",
                "description": "Retrieves a value for a given key name from a table.",
                "parameters": {
                    "key": {
                        "description": "The name of the key to store the value under.",
                        "type": "string",
                        "required": True,
                    },
                    "table_name": {
                        "description": "The name of the table to use for storage.",
                        "type": "string",
                        "required": True,
                    },
                },
            },
        }

        delete_table = {
            "code": f"arn:aws:lambda:{region}:{account_id}:function:working_memory",
            "definition": {
                "name": "delete_table",
                "description": "Deletes a working memory table.",
                "parameters": {
                    "table_name": {
                        "description": "The name of the working memory table to delete.",
                        "type": "string",
                        "required": True,
                    }
                },
            },
        }

        # Load agent definitions from YAML
        with open(agent_yaml_path, "r") as file:
            yaml_agent_content = yaml.safe_load(file)

        # Property data function ARN (would be created separately)
        property_data_lambda = (
            f"arn:aws:lambda:{region}:{account_id}:function:property_data"
        )

        # Economic data function ARN (would be created separately)
        economic_data_lambda = (
            f"arn:aws:lambda:{region}:{account_id}:function:economic_data"
        )

        # Create the specialized agents
        property_researcher = Agent(
            "property_researcher",
            yaml_agent_content,
            tools=[
                {
                    "code": property_data_lambda,
                    "definition": property_data_tools[0],  # property_lookup
                },
                {
                    "code": property_data_lambda,
                    "definition": property_data_tools[1],  # market_data_lookup
                },
                web_search_tool,
                set_value_for_key,
                get_key_value,
            ],
        )

        financial_analyst = Agent(
            "financial_analyst",
            yaml_agent_content,
            tools=[
                {
                    "code": property_data_lambda,
                    "definition": property_data_tools[2],  # investment_analysis
                },
                web_search_tool,
                set_value_for_key,
                get_key_value,
            ],
        )

        market_intelligence = Agent(
            "market_intelligence",
            yaml_agent_content,
            tools=[
                web_search_tool,
                {
                    "code": property_data_lambda,
                    "definition": property_data_tools[1],  # market_data_lookup
                },
                {
                    "code": economic_data_lambda,
                    "definition": economic_data_tools[0],  # series_observations
                },
                {
                    "code": economic_data_lambda,
                    "definition": economic_data_tools[1],  # series_search
                },
                set_value_for_key,
                get_key_value,
            ],
        )

        # Create the supervisor agent
        print("\n\nCreating supervisor agent...\n\n")
        investment_advisor = SupervisorAgent(
            "investment_advisor",
            yaml_agent_content,
            [property_researcher, financial_analyst, market_intelligence],
        )

        if args.recreate_agents == "false":
            print("\n\nInvoking supervisor agent...\n\n")

            time_before_call = datetime.datetime.now()
            print(f"Time before call: {time_before_call}\n")

            # Generate unique working memory table name
            folder_name = "investment-analysis-" + str(uuid.uuid4())

            try:
                result = investment_advisor.invoke_with_tasks(
                    [
                        property_research_task,
                        market_intelligence_task,
                        financial_analysis_task,
                        investment_recommendation_task,
                    ],
                    additional_instructions=dedent(
                        f"""
                            Use a single project table in Working Memory for this entire set of tasks,
                            using table name: {folder_name}. When making requests to your collaborators,
                            tell them the working memory table name, and the named keys they should 
                            use to retrieve their input or save their output.
                            The keys they use in that table will allow them to keep track of state.
                            As a final step, you MUST use one of your collaborators to delete the 
                            Working Memory table.
                            
                            For the market_intelligence specialist, note that:
                            1. For the economic data tool (FRED), use these key indicators:
                                - Current 30-year fixed mortgage rates (series_id: MORTGAGE30US)
                                - Regional house price index (series_id format: [state code]STHPI, e.g., TXSTHPI for Texas)
                                - Regional rental vacancy rates (series_id format: [state code]RVAC, e.g., TXRVAC for Texas)
                                - Consumer Price Index for rent (series_id: CUSR0000SEHA)
                                - Regional unemployment rate (series_id format: [state code]UR, e.g., TXUR for Texas)
                            
                            2. Extract the 2-letter state code from the address to use in the series_id parameters for state-specific data
                            
                            3. IMPORTANT: Save all retrieved economic indicators to the working memory table

                            For the financial_analyst, note that:
                            1. The investment_analysis tool expects:
                                - A JSON string parameter called 'investment_data' containing financial parameters
                                - A separate 'analysis_type' parameter ('mortgage_calc', 'cash_flow', 'roi', or 'all')
                            
                            2. Before performing financial analysis, check the working memory table for both:
                            a) Property data retrieved by the property_researcher (like HOA fees, property taxes)
                            b) Economic indicators retrieved by the market_intelligence agent
                            
                            3. Use the actual economic data from the working memory when available:
                            - Use the current mortgage rate from FRED data rather than web searching for rates
                            - Use actual regional vacancy rates from FRED data for more accurate cash flow projections
                            - Use inflation data (CPI) to inform projected rental increases
                            
                            4. Use the RentCast API data when available instead of estimates. Important data 
                            to look for includes:
                                - HOA fees (typically found in property_data as hoa.fee)
                                - Property tax history (typically found in property_data as taxAssessments or propertyTaxes)
                                - Last sale price (if different from the specified purchase price)
                                - Year built (to estimate maintenance costs based on property age)
                            
                            For the final response, provide a comprehensive investment recommendation 
                            that includes property analysis, financial projections, and market insights.
                            """
                    ),
                    processing_type="sequential",
                    enable_trace=True,
                    trace_level=args.trace_level,
                )

                print(result)
            except Exception as e:
                print(f"Error invoking agent: {e}")
                traceback.print_exc()

            duration = datetime.datetime.now() - time_before_call
            print(f"\nTime taken: {duration.total_seconds():,.1f} seconds")
        else:
            print("Recreated agents.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real Estate Investment Advisor")
    parser.add_argument(
        "--recreate_agents",
        required=False,
        default="false",
        help="False if reusing existing agents.",
    )
    parser.add_argument(
        "--trace_level",
        required=False,
        default="core",
        help="The level of trace, 'core', 'outline', 'all'.",
    )
    parser.add_argument(
        "--clean_up",
        required=False,
        default="false",
        help="Cleanup all infrastructure.",
    )

    # Property research parameters
    parser.add_argument(
        "--address",
        required=False,
        default="5500 Grand Lake Dr, San Antonio, TX 78244",
        help="Address of the property to analyze.",
    )
    parser.add_argument(
        "--property_type",
        required=False,
        default="Single Family",
        help="Type of property (Single Family, Condo, Multi-Family, etc.).",
    )
    parser.add_argument(
        "--investment_goal",
        required=False,
        default="Long-term rental income with moderate appreciation",
        help="Investment goal (cash flow, appreciation, etc.).",
    )
    parser.add_argument(
        "--budget_range",
        required=False,
        default="$350,000 - $450,000",
        help="Budget range for the investment.",
    )

    # Financial analysis parameters
    parser.add_argument(
        "--purchase_price",
        required=False,
        default="399000",
        help="Purchase price of the property.",
    )
    parser.add_argument(
        "--down_payment",
        required=False,
        default="20",
        help="Down payment amount as percentage.",
    )
    parser.add_argument(
        "--target_roi",
        required=False,
        default="6",
        help="Target return on investment percentage.",
    )
    parser.add_argument(
        "--investment_timeline",
        required=False,
        default="10 years",
        help="Investment timeline.",
    )
    parser.add_argument(
        "--expected_rental",
        required=False,
        default="2500",
        help="Expected monthly rental income.",
    )

    # Market intelligence parameters
    parser.add_argument(
        "--market_area",
        required=False,
        default="San Antonio, TX",
        help="Market area for analysis.",
    )

    args = parser.parse_args()
    main(args)
