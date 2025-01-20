# Multi-Agent Collaboration Demo UI

A Streamlit-based user interface for multi agent collaboration demos. Each demo showcases different specialized agents working together to accomplish complex tasks.

## Available Demos

The following demos are supported and can be found in their respective folders:

- **Portfolio Assistant** (`/examples/multi-agent-collaboration/portfolio_assistant_agent/`): Analyzes stock tickers
- **Sports Team Poet** (`/examples/multi-agent-collaboration/team_poems_agent/`): Creates poems about sports teams
- **Trip Planner** (`/examples/multi-agent-collaboration/trip_planner_agent/`): Generates travel itineraries
- **Voyage Virtuoso** (`/examples/multi-agent-collaboration/voyage_virtuoso_agent/`): Provides exotic travel recommendations
- **Mortgages Assistant** (`/examples/multi-agent-collaboration/mortgage_assistant/`): Handles mortgage-related queries
- **Custom Orchestration** (`/examples/agents/custom_orchestration_agent/`): Demonstrates ReWoo (Reasoning without Observation) orchestration for a restaurant assistant agent

## Prerequisites

1. Follow the setup instructions in each agent's respective folder before using them in the demo UI:
   - `/examples/multi-agent-collaboration/mortgage_assistant/README.md`
   - `/examples/multi-agent-collaboration/voyage_virtuoso_agent/README.md`
   - `/examples/multi-agent-collaboration/trip_planner_agent/README.md`
   - `/examples/agents/custom_orchestration_agent/README.md`
   - etc.

2. Ensure you have:
   - Python 3.x
   - AWS credentials configured with appropriate permissions

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Demo

1. Configure your AWS credentials with appropriate permissions

2. Run the Streamlit application:
   ```bash
   streamlit run demo-ui.py
   ```

3. Optionally, specify a specific bot using the BOT_NAME environment variable:
   ```bash
   BOT_NAME="<bot-name>" streamlit run demo-ui.py
   ```

   Supported BOT_NAME values:
   - "Portfolio Assistant" 
   - "Sports Team Poet"
   - "Trip Planner"
   - "Voyage Virtuoso"
   - "Mortgages Assistant" (default)
   - "Custom Orchestration"

## Usage

1. The UI will display the selected bot's interface (defaults to Mortgages Assistant if not specified)
2. Enter your query in the chat input field
3. The agent will:
   - Process your request
   - Show the collaboration between different agents
   - Display thought processes and tool usage
   - Provide a detailed response

## Using with Other Bedrock Agents Examples

While this UI has been tested with the examples mentioned above, you can use it with any other simple Bedrock agent by updating the `config.py` file. To add your own agent:

1. Add a new configuration to the `bot_configs` list in `config.py`:
```python
{
    "bot_name": "Your Bot Name",  # Display name in the UI
    "agent_name": "your_agent_id", # Your Bedrock agent ID
    "start_prompt": "Initial message to show users",
    "session_attributes": {        # Optional: Include if your agent needs specific session attributes
        "sessionAttributes": {},
        "promptSessionAttributes": {}
    }
}
```

## Architecture

The demo UI integrates with Amazon Bedrock Agent Runtime for agent execution and showcases multi-agent collaboration features including:

- Dynamic routing between specialized agents
- Knowledge base lookups
- Tool invocations
- Code interpretation capabilities

Below is an example of the demo UI in action, showing the Mortgages Assistant interface:

![Demo UI Screenshot](demo-ui.png)