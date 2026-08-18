"""
state.py

Shared state for the cybersecurity AI assistant.
"""

from typing import TypedDict, Optional

from langgraph.graph import MessagesState


class InvestigationState(TypedDict, total=False):
    """
    Structured state for a cybersecurity investigation.
    """

    cve_id: str
    severity: str
    cvss_score: float
    description: str
    source: str
    status: str

    risk_assessment: str
    analysis: str


class AssistantState(MessagesState):
    """
    Shared LangGraph state.
    """

    route: str

    profile: dict

    investigation: InvestigationState