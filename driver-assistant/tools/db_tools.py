"""DB tool functions for agent persistence."""

from ..utils.db import (
    save_agent_data,
    load_agent_data,
    save_session_data,
    load_session_data,
)


def agent_save_data(key: str, value: dict) -> dict:
    """Save data to the agent DB."""
    success = save_agent_data(key, value)
    return {"status": "success" if success else "error"}


def agent_load_data(key: str) -> dict:
    """Load data from the agent DB."""
    value = load_agent_data(key)
    if value is not None:
        return {"status": "success", "value": value}
    else:
        return {"status": "not_found"}


def agent_save_session_data(
    user_id: str, session_id: str, key: str, value: dict
) -> dict:
    """Save data to the agent DB for a session."""
    success = save_session_data(user_id, session_id, key, value)
    return {"status": "success" if success else "error"}


def agent_load_session_data(user_id: str, session_id: str, key: str) -> dict:
    """Load data from the agent DB for a session."""
    value = load_session_data(user_id, session_id, key)
    if value is not None:
        return {"status": "success", "value": value}
    else:
        return {"status": "not_found"}
