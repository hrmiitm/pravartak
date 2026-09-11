"""
state.py

Shared state for the cybersecurity AI assistant.
"""

from typing import TypedDict

from langgraph.graph import MessagesState


class InvestigationState(TypedDict, total=False):
    """
    Structured state for a cybersecurity investigation.
    """

    # ------------------------------------------------------
    # Vulnerability evidence
    # ------------------------------------------------------

    cve_id: str
    severity: str
    cvss_score: float
    cvss_version: str
    description: str
    source: str
    status: str

    # ------------------------------------------------------
    # Affected software and versions
    # ------------------------------------------------------

    affected_software: list[str]
    affected_versions: list[str]

    # Structured per-product affected data, additive to the
    # two flat fields above. Each entry keeps exact versions
    # and version-range boundaries (versionStart/EndIncluding,
    # versionStart/EndExcluding) tied to the specific product
    # they apply to, which the flat fields cannot represent.
    #
    # Example:
    #
    #   [
    #       {
    #           "product": "xz",
    #           "versions": ["5.6.0", "5.6.1"],
    #           "version_ranges": [
    #               {
    #                   "start_including": "5.0.0",
    #                   "start_excluding": None,
    #                   "end_including": None,
    #                   "end_excluding": "5.6.2",
    #               },
    #           ],
    #       },
    #   ]
    affected_products: list[dict]

    # ------------------------------------------------------
    # Risk assessment
    # ------------------------------------------------------

    risk_assessment: str
    analysis: str

    # Contextual risk prioritization (additive to risk_assessment).
    # risk_assessment reflects how severe the CVE is globally;
    # contextual_priority reflects how urgently THIS organization
    # should act, combining CVSS, asset criticality, exposure, and
    # applicability confidence.
    #
    # Shape:
    #   {
    #       "priority_score": int (0-100),
    #       "priority_label": str (CRITICAL/HIGH/MEDIUM/LOW),
    #       "priority_basis": str,
    #       "raw_score": float,
    #       "confidence_cap": float,
    #   }
    contextual_priority: dict

    # ------------------------------------------------------
    # Organizational context
    # ------------------------------------------------------

    organization_context: dict

    # ------------------------------------------------------
    # Organizational applicability
    # ------------------------------------------------------

    organizational_relevance: str
    relevance_reason: str
    matched_assets: list[dict]

    applicability_confidence: float
    applicability_evidence: list[str]
    missing_evidence: list[str]

    # ------------------------------------------------------
    # Security recommendations
    # ------------------------------------------------------

    recommendations: list[str]

    # ------------------------------------------------------
    # Evidence provenance
    # ------------------------------------------------------

    evidence: dict


class AssistantState(MessagesState):
    """
    Shared LangGraph state.
    """

    route: str
    investigation: InvestigationState