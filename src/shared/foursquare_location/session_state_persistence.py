import streamlit as st
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


class StatePersistence:
    def __init__(self, file_path: str = ".streamlit/global_state.json"):
        """
        Initialize the global state persistence manager.

        Args:
            file_path: Path to the global state file
        """
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Create file if it doesn't exist
        if not os.path.exists(file_path):
            self.save_state({})

    def save_state(self, state_dict: Dict[str, Any]) -> None:
        """
        Save state to disk.

        Args:
            state_dict: Dictionary of state to save
        """
        # Add metadata
        state_dict['_metadata'] = {
            'last_saved': datetime.now().isoformat()
        }

        try:
            with open(self.file_path, 'w') as f:
                json.dump(state_dict, f, indent=2)
        except Exception as e:
            st.error(f"Failed to save global state: {str(e)}")

    def load_state(self) -> Dict[str, Any]:
        """
        Load state from disk.

        Returns:
            Dictionary containing the saved state
        """
        try:
            with open(self.file_path, 'r') as f:
                state_dict = json.load(f)

            # Remove metadata before returning
            state_dict.pop('_metadata', None)
            return state_dict

        except Exception as e:
            st.error(f"Failed to load global state: {str(e)}")
            return {}

    def save_current_state(self, keys_to_save: Optional[list] = None) -> None:
        """
        Save current Streamlit session state to disk.

        Args:
            keys_to_save: List of keys to save. If None, saves all serializable keys.
        """
        state_dict = {}

        # If no keys specified, get all serializable keys
        if keys_to_save is None:
            for key, value in st.session_state.items():
                try:
                    # Test JSON serialization
                    json.dumps(value)
                    state_dict[key] = value
                except (TypeError, OverflowError):
                    continue
        else:
            # Only save specified keys
            for key in keys_to_save:
                if key in st.session_state:
                    try:
                        json.dumps(st.session_state[key])
                        state_dict[key] = st.session_state[key]
                    except (TypeError, OverflowError):
                        continue

        self.save_state(state_dict)

    def restore_state(self) -> None:
        """Restore saved state to current session."""
        saved_state = self.load_state()

        # Update session state with saved values
        for key, value in saved_state.items():
            st.session_state[key] = value


def initialize_persistent_state(keys_to_persist: Optional[list] = None):
    """
    Initialize global state persistence.

    Args:
        keys_to_persist: List of keys to persist. If None, persists all serializable keys.
    """
    state_manager = StatePersistence()

    # Restore previous state if exists
    if not hasattr(st.session_state, '_state_restored'):
        state_manager.restore_state()
        st.session_state._state_restored = True

    # Auto-save on script rerun
    if not hasattr(st.session_state, '_state_saved'):
        state_manager.save_current_state(keys_to_persist)
        st.session_state._state_saved = True

    return state_manager