"""
Runtime helpers for Streamlit deployment modes.
"""

import os
import streamlit as st


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def is_demo_mode() -> bool:
    """
    Demo mode is enabled via either:
    - Environment variable: DEMO_MODE=true
    - Streamlit secrets: DEMO_MODE = "true"
    """
    env_value = os.getenv("DEMO_MODE", "false")

    secret_value = "false"
    try:
        secret_value = str(st.secrets.get("DEMO_MODE", "false"))
    except Exception:
        pass

    return _to_bool(env_value) or _to_bool(secret_value)
