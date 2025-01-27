import streamlit as st
import os
import uuid
import yaml
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.bedrock_agent import agents_helper
from config import bot_configs
from ui_utils import invoke_agent

def initialize_session():
    """Initialize session state and bot configuration."""
    if 'count' not in st.session_state:
        st.session_state['count'] = 1

        # Refresh agent IDs and aliases
        for idx, config in enumerate(bot_configs):
            try:
                agent_id = agents_helper.get_agent_id_by_name(config['agent_name'])
                agent_alias_id = agents_helper.get_agent_latest_alias_id(agent_id)
                bot_configs[idx]['agent_id'] = agent_id
                bot_configs[idx]['agent_alias_id'] = agent_alias_id
            except Exception as e:
                print(f"Could not find agent named:{config['agent_name']}, skipping...")
                continue

        # Get bot configuration
        bot_name = os.environ.get('BOT_NAME', 'Mortgages Assistant')
        bot_config = next((config for config in bot_configs if config['bot_name'] == bot_name), None)
        
        if bot_config:
            st.session_state['bot_config'] = bot_config
            
            # Load tasks if any
            task_yaml_content = {}
            if 'tasks' in bot_config:
                with open(bot_config['tasks'], 'r') as file:
                    task_yaml_content = yaml.safe_load(file)
            st.session_state['task_yaml_content'] = task_yaml_content

            # Initialize session ID and message history
            st.session_state['session_id'] = str(uuid.uuid4())
            st.session_state.messages = []

def main():
    """Main application flow."""
    initialize_session()

    # Display chat interface
    st.title(st.session_state['bot_config']['bot_name'])

    # Show message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if 'user_input' not in st.session_state:
        next_prompt = st.session_state['bot_config']['start_prompt']
        user_query = st.chat_input(placeholder=next_prompt, key="user_input")
        st.session_state['bot_config']['start_prompt'] = " "
    elif st.session_state.count > 1:
        user_query = st.session_state['user_input']
        
        if user_query:
            # Display user message
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Get and display assistant response
            response = ""
            with st.chat_message("assistant"):
                try:
                    session_id = st.session_state['session_id']
                    response = st.write_stream(invoke_agent(
                        user_query, 
                        session_id, 
                        st.session_state['task_yaml_content']
                    ))
                except Exception as e:
                    print(f"Error: {e}")  # Keep logging for debugging
                    st.error(f"An error occurred: {str(e)}")  # Show error in UI
                    response = "I encountered an error processing your request. Please try again."

            # Update chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Reset input
        user_query = st.chat_input(placeholder=" ", key="user_input")

    # Update session count
    st.session_state['count'] = st.session_state.get('count', 1) + 1

if __name__ == "__main__":
    main()
