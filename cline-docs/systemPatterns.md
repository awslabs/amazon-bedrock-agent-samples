# System Patterns

## Architecture Patterns

### 1. Multi-Agent Collaboration Modes
- **Supervisor Mode**: For complex task orchestration and workflow management
- **Supervisor with Routing**: For unified customer experiences with automatic intent classification
- **Direct Agent Communication**: For simpler, point-to-point interactions

### 2. Code Organization
```
├── examples/
│   ├── multi-agent-collaboration/    # Multi-agent examples
│   │   ├── 00_hello_world_agent/    # Basic example
│   │   ├── mortgage_assistant/      # Routing example
│   │   ├── portfolio_assistant/     # Financial analysis
│   │   └── other specialized agents...
│   └── agents_ux/                   # User interface components
│       ├── config.py               # Bot configurations
│       ├── demo_ui.py             # Main UI implementation
│       └── ui_utils.py            # UI helper functions
├── src/
    ├── shared/                        # Reusable components
    │   ├── working_memory/           # State management
    │   ├── web_search/              # Web search capability
    │   └── stock_data/              # Financial data access
    └── utils/                        # Core utilities
        ├── bedrock_agent.py         # High-level agent classes
        └── bedrock_agent_helper.py  # Lower-level helper functions
```

## Key Technical Decisions

### 1. Agent Implementation Approaches
- **Direct boto3**: Raw API access for maximum flexibility
- **Helper Class**: Simplified wrapper with additional capabilities
- **Object-Oriented SDK**: Clean, Pythonic interface for agent creation

### 2. Configuration Management
- YAML-based definitions for agents and tasks
- Environment-based AWS credentials
- Standardized project structure

### 3. Development Patterns
- Task-based workflow definitions
- Modular agent composition
- Reusable shared tools and utilities

## Best Practices

### 1. Agent Design
- Clear separation of concerns between agents
- Well-defined collaboration patterns
- Specific instructions for each agent role

### 2. Code Structure
- Modular and reusable components
- Clear separation between agent logic and utilities
- Consistent error handling and logging

### 3. Development Workflow
- Use virtual environments
- Follow AWS security best practices
- Maintain clear documentation
