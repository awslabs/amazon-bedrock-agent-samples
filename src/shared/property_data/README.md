# Property Data Tool

This tool provides real estate property data through the RentCast API, enabling agents to retrieve comprehensive property information, valuation estimates, and rental projections. It's designed to support real estate investment analysis with reliable market data.

The tool supports three main functions:
1. **Property Lookup**: Get detailed property information, value estimates, or rent estimates
2. **Market Data Lookup**: Retrieve market statistics for specific zip codes
3. **Investment Analysis**: Calculate ROI, cash flow, and mortgage scenarios for investment properties

![architecture](./architecture.png)

## Prerequisites

1. Get your RentCast API key by [registering](https://rentcast.io/api). Developer plan gives you 50 free API requests a month.

## Deploy [property_data_stack.yaml](/src/shared/property_data/cfn_stacks/property_data_stack.yaml)

|   Region   | property_data_stack.yaml |
| ---------- | ----------------- |
| us-east-1  | [![launch-stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=PropertyData&templateURL=...property_data_stack.yaml)|
| us-west-2  | [![launch-stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=PropertyData&templateURL=...property_data_stack.yaml)|

## Tool Functions

### 1. Property Lookup
Retrieves detailed property information, value estimates, or rent estimates for a given address.

**Key Parameters:**
- `address`: The property address in the format "Street, City, State, Zip"
- `data_type`: Type of data to retrieve ("property_data", "value_estimate", or "rent_estimate")
- `propertyType`: Required for value/rent estimates (e.g., "Single Family", "Condo", etc.)
- `bedrooms`: Required for value/rent estimates (number of bedrooms)
- `squareFootage`: Required for value/rent estimates (living area in square feet)

**Usage Pattern:**
1. Call with `data_type=property_data` to get basic property details with just `address` provided.
2. Call with `data_type=value_estimate` or `data_type=rent_estimate`, providing the property attributes `propertyType`, `bedrooms`, `squareFootage` to get a more accurate value/rent estimate with comparable properties.

### 2. Market Data Lookup
Retrieves aggregate market statistics for a specific zip code.

**Key Parameters:**
- `zip_code`: The 5-digit zip code to look up
- `data_type`: Type of market data to retrieve ("Sale", "Rental", or "All")
- `history_range`: Number of months of historical data to retrieve (default: 1)

### 3. Investment Analysis
Performs comprehensive investment calculations for a property.

**Key Parameters:**
1. `investment_data`: JSON string containing investment parameters: 
    - `purchase_price`
    - `down_payment_percentage` 
    - `interest_rate` 
    - `term_years`
    - `rental_income` 
    - `property_taxes` 
    - `insurance`
    - `maintenance`
2. `analysis_type`: Type of analysis to perform ("mortgage_calc", "cash_flow", "roi", or "all")

## Usage Examples

### Example 1: Retrieve Property Data

```python
from src.utils.bedrock_agent import (
    Agent,
    region,
    account_id,
)
import uuid

property_data_agent = Agent.create(
    name="property_data_agent",
    role="Real Estate Data Specialist",
    goal="Provide accurate property information and valuation data.",
    instructions="Specialist in real estate data analysis.",
    tool_code=f"arn:aws:lambda:{region}:{account_id}:function:property_data",
    tool_defs=[
        {
            "name": "property_lookup",
            "description": "Retrieves property information, valuation, or rent estimates",
            "parameters": {
                "address": {
                    "description": "The property address to look up",
                    "type": "string",
                    "required": True
                },
                "data_type": {
                    "description": "Type of data to retrieve (property_data, value_estimate, rent_estimate)",
                    "type": "string",
                    "required": True
                },
                "propertyType": {
                    "description": "Needed for value/rent estimates. Property type from property_data",
                    "type": "string",
                    "required": False
                },
                "bedrooms": {
                    "description": "Needed for value/rent estimates. Bedrooms from property_data",
                    "type": "string",
                    "required": False
                },
                "squareFootage": {
                    "description": "Needed for value/rent estimates. Square footage from property_data",
                    "type": "string",
                    "required": False
                }
            }
        }
    ],
)

# Get basic property information
response = property_data_agent.invoke(
    input_text="Get property data for 123 Main St, Austin, TX 78701",
    session_id=str(uuid.uuid4()),
)
print(response)

# Get property valuation
response = property_data_agent.invoke(
    input_text="Get value estimate for 123 Main St, Austin, TX 78701. It's a Single Family home with 3 bedrooms and 2000 square feet.",
    session_id=str(uuid.uuid4()),
)
print(response)
```

### Example 2: Market Data and Investment Analysis

```python
from src.utils.bedrock_agent import (
    Agent,
    region,
    account_id,
)
import uuid

market_analyst = Agent.create(
    name="market_analyst",
    role="Real Estate Market Analyst",
    goal="Analyze market conditions and investment opportunities.",
    instructions="Expert in real estate market trends and investment calculations.",
    tool_code=f"arn:aws:lambda:{region}:{account_id}:function:property_data",
    tool_defs=[
        {
            "name": "market_data_lookup",
            "description": "Retrieves market statistics for a specific area",
            "parameters": {
                "zip_code": {
                    "description": "The 5-digit zip code to look up",
                    "type": "string",
                    "required": True
                },
                "data_type": {
                    "description": "Type of data to retrieve (Sale, Rental, All)",
                    "type": "string",
                    "required": False
                },
                "history_range": {
                    "description": "Number of months of historical data to retrieve",
                    "type": "string",
                    "required": False
                }
            }
        },
        {
            "name": "investment_analysis",
            "description": "Performs real estate investment calculations",
            "parameters": {
                "investment_data": {
                    "description": "JSON string with investment parameters",
                    "type": "string",
                    "required": True
                },
                "analysis_type": {
                    "description": "Type of analysis to perform",
                    "type": "string",
                    "required": False
                }
            }
        }
    ],
)

# Get market data for zip code
response = market_analyst.invoke(
    input_text="What's the market data for zip code 78701?",
    session_id=str(uuid.uuid4()),
)
print(response)

# Calculate investment metrics
response = market_analyst.invoke(
    input_text="""Analyze this investment opportunity:
    - Purchase price: $350,000
    - Down payment: 20%
    - Interest rate: 4.5%
    - Expected rental income: $2,000/month
    - Property taxes: $5,000/year
    - Insurance: $1,200/year
    """,
    session_id=str(uuid.uuid4()),
)
print(response)
```

## Data Flow Pattern

For property value or rent estimates, follow this sequence:
1. First call `property_lookup` with `data_type=property_data` to get basic property info
2. Extract key attributes: `propertyType`, `bedrooms`, and `squareFootage`
3. Then call `property_lookup` again with `data_type=value_estimate` or `data_type=rent_estimate`, providing those attributes as parameters

This pattern ensures you get accurate valuation and rental estimates based on the property's actual attributes.

## Clean Up

- Open the CloudFormation console.
- Select the stack `PropertyData` you created, then click **Delete**. Wait for the stack to be deleted.
- Make sure to manually delete `RENTCAST_API_KEY-*` secret key.

## References

- [RentCast API Documentation](https://developers.rentcast.io/reference/overview)
- [Property Data Schema](https://developers.rentcast.io/reference/property-data-schema)
- [Market Data Schema](https://developers.rentcast.io/reference/market-data-schema)

## Security

See [CONTRIBUTING](/CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
