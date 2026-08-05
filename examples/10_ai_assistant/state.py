"""
state.py

Shared state.
"""

from typing import TypedDict

from langgraph.graph import MessagesState


class AssistantState(MessagesState):
    """
    Shared graph state.
    """

    route: str

    profile: dict