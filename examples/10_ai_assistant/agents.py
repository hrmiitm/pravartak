"""
All LangGraph nodes used by the AI Assistant.
"""

import json
import re
import time

from router import detect_intent

import settings
from config import llm

from langchain_core.messages import (
    AIMessage,
    SystemMessage,
)

from memory import (
    remember,
    recall,
    get_organization_context,
)

from inventory import get_demo_inventory

from investigation_engine import (
    generate_security_recommendation,
    calculate_contextual_priority,
    build_investigation,
)

from prompts import ASSISTANT_PROMPT
from tools import TOOLS


# ==========================================================
# ReAct Assistant
# ==========================================================

assistant_llm = llm.bind_tools(TOOLS)


# Used by the grounding guard in assistant_node: detects a CVE
# identifier anywhere in text (unanchored, unlike the stricter
# full-match validator in apis/vulnerabilities.py, which is used
# to validate a CVE ID supplied as a tool argument).
CVE_MENTION_PATTERN = re.compile(
    r"\bCVE-\d{4}-\d{4,}\b",
    re.IGNORECASE,
)


# ==========================================================
# Supervisor Node
# ==========================================================

def supervisor(state):
    """
    Supervisor Node

    Fast deterministic intent router.
    """

    last_message = state["messages"][-1].content

    intent = detect_intent(last_message)

    if settings.LEARN_MODE:

        print("\n" + "=" * 70)
        print("🧭 LANGGRAPH EXECUTION")
        print("=" * 70)

        print("📍 Current Node : Supervisor")
        print(f"📨 User Query   : {last_message}")
        print(f"🎯 Intent       : {intent}")

    if intent == "memory":

        if settings.LEARN_MODE:
            print(
                "✅ Decision     : "
                "Route → Memory Node"
            )

        return {
            "route": "memory"
        }

    if settings.LEARN_MODE:
        print(
            "✅ Decision     : "
            "Route → Assistant Node"
        )

    return {
        "route": "assistant"
    }


# ==========================================================
# Memory Node
# ==========================================================

def memory_node(state):

    if settings.LEARN_MODE:
        print("\n🧠 Current Node : Memory")

    last_message = state["messages"][-1].content.strip()
    text = last_message.lower()

    # ======================================================
    # Store organization information
    # ======================================================

    if (
        text.startswith("remember our ")
        and " is " in text
    ):

        before, value = last_message.split(
            " is ",
            1,
        )

        key = before[
            len("Remember our "):
        ].strip()

        key = (
            key
            .rstrip("?.!")
            .replace(" ", "_")
            .lower()
        )

        if key == "company":
            key = "organization"

        value = value.strip().rstrip("? .!")

        if settings.LEARN_MODE:
            print(
                f"💾 Action       : "
                f"Store {key} = {value}"
            )

        remember(
            key,
            value,
        )

        return {
            "messages": [
                AIMessage(
                    content=(
                        f"Got it. I'll remember that our "
                        f"{key.replace('_', ' ')} is {value}."
                    )
                )
            ]
        }

    # ======================================================
    # Retrieve organization information
    # ======================================================

    if (
        text.startswith("what is our ")
        or text.startswith("what's our ")
    ):

        if text.startswith("what is our "):

            key = last_message[
                len("What is our "):
            ]

        else:

            key = last_message[
                len("What's our "):
            ]

        key = (
            key
            .strip()
            .rstrip("?.!")
            .replace(" ", "_")
            .lower()
        )

        if settings.LEARN_MODE:
            print(
                f"🔍 Action       : "
                f"Retrieve {key}"
            )

        value = recall(
            key
        )

        if value:

            return {
                "messages": [
                    AIMessage(
                        content=(
                            f"Our "
                            f"{key.replace('_', ' ')} "
                            f"is {value}."
                        )
                    )
                ]
            }

        return {
            "messages": [
                AIMessage(
                    content=(
                        f"I don't have any information "
                        f"about our "
                        f"{key.replace('_', ' ')} yet."
                    )
                )
            ]
        }

    # ======================================================
    # Unsupported memory request
    # ======================================================

    return {
        "messages": [
            AIMessage(
                content=(
                    "I couldn't identify a specific organization "
                    "fact to store or retrieve."
                )
            )
        ]
    }


# ==========================================================
# Assistant Node
# ==========================================================

def assistant_node(state):

    if settings.LEARN_MODE:
        print(
            "\n🤖 Current Node : Assistant"
        )
        print(
            "🧠 Action       : Thinking..."
        )

    start = time.perf_counter()

    # ------------------------------------------------------
    # Build investigation context
    # ------------------------------------------------------

    investigation = state.get(
        "investigation"
    )

    investigation_context = ""

    if investigation:

        recommendations = investigation.get(
            "recommendations",
            []
        )

        investigation_context = f"""

CURRENT SECURITY INVESTIGATION STATE:

CVE ID:
{investigation.get("cve_id", "N/A")}

Severity:
{investigation.get("severity", "N/A")}

CVSS Score:
{investigation.get("cvss_score", "N/A")}

CVSS Version:
{investigation.get("cvss_version", "N/A")}

Affected Software:
{investigation.get("affected_software", [])}

Affected Versions:
{investigation.get("affected_versions", [])}

Risk Assessment:
{investigation.get("risk_assessment", "N/A")}

Contextual Priority:
{investigation.get("contextual_priority", {}).get("priority_label", "N/A")} ({investigation.get("contextual_priority", {}).get("priority_score", "N/A")}/100)

Contextual Priority Basis:
{investigation.get("contextual_priority", {}).get("priority_basis", "N/A")}

Evidence Source:
{investigation.get("evidence", {}).get("vulnerability_source", "N/A")}

Evidence Provenance:
{investigation.get("evidence", {})}

Status:
{investigation.get("status", "N/A")}

Organizational Relevance:
{investigation.get("organizational_relevance", "UNKNOWN")}

Applicability Confidence:
{investigation.get("applicability_confidence", "N/A")}

Applicability Evidence:
{investigation.get("applicability_evidence", [])}

Missing Evidence:
{investigation.get("missing_evidence", [])}

Relevance Reason:
{investigation.get("relevance_reason", "N/A")}

Matched Assets:
{investigation.get("matched_assets", [])}

Description:
{investigation.get("description", "N/A")}

Analysis:
{investigation.get("analysis", "N/A")}

Recommended Actions:
{recommendations}

Use this structured investigation state when answering the user.

Do not invent information that is not present in the evidence.

When recommended actions are available, use them when answering
questions about what the organization should do.

When applicability is UNKNOWN, clearly communicate that this means
there is insufficient evidence to establish whether the organization
is affected. Do not interpret UNKNOWN as NOT_RELEVANT.

When explaining applicability, mention important missing evidence
when relevant.
"""

    # ------------------------------------------------------
    # Invoke Assistant
    # ------------------------------------------------------

    response = assistant_llm.invoke(
        [
            SystemMessage(
                content=(
                    ASSISTANT_PROMPT
                    + investigation_context
                )
            ),
            *state["messages"],
        ]
    )

    # --------------------------------------------------
    # Grounding guard
    #
    # If the user's message references a specific CVE, and the
    # assistant chose to respond directly (no tool call) without
    # any investigation evidence existing yet in this turn, that
    # response can only be based on the model's own training
    # knowledge rather than verified NVD evidence. This is the
    # exact failure mode item 23 of the handoff describes: the
    # model stating vulnerability facts (e.g. affected software)
    # that are not backed by structured evidence.
    #
    # Rather than trying to detect hallucinated facts in free
    # text (fragile), this checks something structural: was a
    # CVE mentioned, and does no grounding exist for it yet.
    # When both are true, retry once with an explicit reminder
    # forcing tool use. This adds one extra LLM call only in
    # this rare case — the normal working path (tool called on
    # the first try) is unaffected.
    # --------------------------------------------------

    if (
        not response.tool_calls
        and not investigation
        and state["messages"]
    ):

        last_user_text = (
            state["messages"][-1].content
            or ""
        )

        if CVE_MENTION_PATTERN.search(
            last_user_text
        ):

            if settings.LEARN_MODE:

                print(
                    "\n⚠ Grounding Guard : "
                    "CVE mentioned, no tool called, "
                    "no evidence yet. Forcing retrieval retry."
                )

            grounding_reminder = SystemMessage(
                content=(
                    ASSISTANT_PROMPT
                    + investigation_context
                    + "\n\nIMPORTANT: The user's message "
                    "references a specific CVE identifier. "
                    "You must call the vulnerability_lookup "
                    "tool for that CVE before answering. Do "
                    "not state any vulnerability facts "
                    "(severity, CVSS score, affected software, "
                    "or affected versions) from memory."
                )
            )

            response = assistant_llm.invoke(
                [
                    grounding_reminder,
                    *state["messages"],
                ]
            )

            if (
                settings.LEARN_MODE
                and not response.tool_calls
            ):

                print(
                    "⚠ Grounding Guard : "
                    "Retry still did not call the tool. "
                    "Response may be ungrounded — treat with "
                    "caution."
                )

    end = time.perf_counter()

    if settings.LEARN_MODE:

        print(
            f"⏱ Assistant Time: "
            f"{end - start:.3f} sec"
        )

        if response.tool_calls:

            print(
                "🛠 Decision     : "
                "Tool Required"
            )

        else:

            print(
                "💬 Decision     : "
                "Respond Directly"
            )

    return {
        "messages": [
            response
        ]
    }


# ==========================================================
# Security Investigation Node
# ==========================================================

def security_investigation_node(state):
    """
    Convert vulnerability tool evidence into structured
    LangGraph investigation state.

    IMPORTANT:
    This node does NOT call the NVD API.

    It reuses the evidence already retrieved by ToolNode.
    """

    if settings.LEARN_MODE:
        print(
            "\n🔐 Current Node : "
            "Security Investigation"
        )

    # ------------------------------------------------------
    # Load persistent organization context
    # ------------------------------------------------------

    organization_context = (
        get_organization_context()
    )

    if settings.LEARN_MODE:

        print(
            "🏢 Organization Context"
        )

        print(
            f"   Organization   : "
            f"{organization_context.get('organization') or 'Unknown'}"
        )

        print(
            f"   Firewall       : "
            f"{organization_context.get('firewall_vendor') or 'Unknown'}"
        )

        print(
            f"   SIEM           : "
            f"{organization_context.get('siem_platform') or 'Unknown'}"
        )

        print(
            f"   Incident Policy: "
            f"{organization_context.get('incident_policy') or 'Unknown'}"
        )

    # ------------------------------------------------------
    # Find most recent vulnerability tool response
    # ------------------------------------------------------

    tool_message = None

    for message in reversed(
        state["messages"]
    ):

        if getattr(
            message,
            "type",
            None,
        ) == "tool":

            if (
                getattr(
                    message,
                    "name",
                    None,
                )
                == "vulnerability_lookup"
            ):

                tool_message = message
                break

    # ------------------------------------------------------
    # No evidence
    # ------------------------------------------------------

    if tool_message is None:

        if settings.LEARN_MODE:
            print(
                "⚠ No vulnerability evidence found."
            )

        return {
            "investigation": {
                "status": "no_evidence"
            }
        }

    # ------------------------------------------------------
    # Parse structured tool output
    # ------------------------------------------------------

    try:

        vulnerability = json.loads(
            tool_message.content
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ) as exc:

        if settings.LEARN_MODE:

            print(
                f"❌ Could not parse "
                f"vulnerability evidence: {exc}"
            )

        return {
            "investigation": {
                "status": "invalid_evidence",
                "source": "NVD",
            }
        }

    # ------------------------------------------------------
    # Check for API error
    # ------------------------------------------------------

    if vulnerability.get(
        "status"
    ) == "error":

        if settings.LEARN_MODE:

            print(
                "❌ Vulnerability evidence "
                "contains an API error."
            )

        return {
            "investigation": {
                "cve_id": vulnerability.get(
                    "cve_id"
                ),
                "source": "NVD",
                "status": "failed",
                "error": vulnerability.get(
                    "error"
                ),
            }
        }

    # ------------------------------------------------------
    # Load organization asset inventory
    # ------------------------------------------------------

    inventory = get_demo_inventory()

    # ------------------------------------------------------
    # Build the structured investigation record
    #
    # All applicability analysis, recommendation generation,
    # and contextual risk prioritization logic lives in
    # investigation_engine.build_investigation() -- shared
    # with the batch (non-interactive) path in batch.py, so
    # the two cannot silently drift apart.
    # ------------------------------------------------------

    investigation = build_investigation(
        vulnerability=vulnerability,
        inventory=inventory,
        organization_context=organization_context,
    )

    # ------------------------------------------------------
    # Display applicability result
    # ------------------------------------------------------

    if settings.LEARN_MODE:

        print(
            f"\U0001f3e2 Organizational Relevance : "
            f"{investigation['organizational_relevance']}"
        )

        print(
            f"\U0001f4dd Reason                    : "
            f"{investigation['relevance_reason']}"
        )

        print(
            f"\U0001f3af Applicability Confidence  : "
            f"{investigation['applicability_confidence']}"
        )

        if investigation['matched_assets']:

            print(
                f"\U0001f517 Matched Assets            : "
                f"{investigation['matched_assets']}"
            )

        if investigation['applicability_evidence']:

            print(
                "\U0001f4da Applicability Evidence   :"
            )

            for item in investigation['applicability_evidence']:

                print(
                    f"   \u2022 {item}"
                )

        if investigation['missing_evidence']:

            print(
                "\U0001f50e Missing Evidence          :"
            )

            for item in investigation['missing_evidence']:

                print(
                    f"   \u2022 {item}"
                )

        print(
            "\U0001f6e0 Recommended Actions      :"
        )

        for recommendation in investigation['recommendations']:

            print(
                f"   \u2022 {recommendation}"
            )

        print(
            f"\U0001f3af Contextual Priority       : "
            f"{investigation['contextual_priority']['priority_label']} "
            f"({investigation['contextual_priority']['priority_score']}/100)"
        )

        print(
            f"\U0001f4d0 Priority Basis            : "
            f"{investigation['contextual_priority']['priority_basis']}"
        )

    # ------------------------------------------------------
    # Display investigation result
    # ------------------------------------------------------

    if settings.LEARN_MODE:

        print(
            f"🔐 CVE          : "
            f"{investigation['cve_id']}"
        )

        print(
            f"📊 Severity     : "
            f"{investigation['severity']}"
        )

        print(
            f"📈 CVSS         : "
            f"{investigation['cvss_score']}"
        )

        print(
            f"📋 CVSS Version : "
            f"{investigation['cvss_version']}"
        )

        print(
            f"💻 Affected Software : "
            f"{investigation['affected_software']}"
        )

        print(
            f"📦 Affected Versions : "
            f"{investigation['affected_versions']}"
        )

        print(
            f"⚠ Risk Level    : "
            f"{investigation['risk_assessment']}"
        )

        print(
            f"📚 Evidence     : "
            f"{investigation['evidence']['vulnerability_source']}"
        )

        print(
            "🔎 Provenance   : "
            f"{investigation['evidence']}"
        )

        print(
            "✅ Investigation state updated."
        )

    # ------------------------------------------------------
    # Return state to LangGraph
    # ------------------------------------------------------

    return {
        "investigation": investigation
    }


# ==========================================================
# Security Response Builder Node
# ==========================================================

def security_response_builder_node(state):
    """
    Build the final answer directly from the structured
    investigation state, without an additional LLM call.

    Only reached when the Security Investigation node has
    just produced a completed, evidence-backed result for
    the current turn (investigation["status"] == "retrieved").

    Every sentence in the generated response is traceable to
    a field in the structured investigation state. This node
    intentionally does not call the LLM, in order to:

    - eliminate the unnecessary second LLM call that was the
      dominant source of end-to-end latency
    - guarantee the response cannot contain security facts
      that are not backed by structured evidence
    """

    if settings.LEARN_MODE:
        print(
            "\n📝 Current Node : "
            "Security Response Builder"
        )
        print(
            "⚙ Action        : "
            "Deterministic response (no LLM call)"
        )

    start = time.perf_counter()

    investigation = state["investigation"]

    # ------------------------------------------------------
    # Pull structured fields
    # ------------------------------------------------------

    cve_id = investigation.get(
        "cve_id",
        "Unknown CVE"
    )

    severity = (
        investigation.get("severity")
        or "UNKNOWN"
    ).upper()

    cvss_score = investigation.get(
        "cvss_score"
    )

    cvss_version = investigation.get(
        "cvss_version"
    )

    affected_software = investigation.get(
        "affected_software",
        []
    )

    affected_versions = investigation.get(
        "affected_versions",
        []
    )

    risk_assessment = investigation.get(
        "risk_assessment",
        "UNKNOWN"
    )

    organizational_relevance = investigation.get(
        "organizational_relevance",
        "UNKNOWN"
    )

    relevance_reason = investigation.get(
        "relevance_reason",
        ""
    )

    matched_assets = investigation.get(
        "matched_assets",
        []
    )

    applicability_confidence = investigation.get(
        "applicability_confidence"
    )

    applicability_evidence = investigation.get(
        "applicability_evidence",
        []
    )

    missing_evidence = investigation.get(
        "missing_evidence",
        []
    )

    recommendations = investigation.get(
        "recommendations",
        []
    )

    evidence_source = investigation.get(
        "evidence",
        {}
    ).get(
        "vulnerability_source",
        "N/A"
    )

    contextual_priority = investigation.get(
        "contextual_priority"
    )

    # ------------------------------------------------------
    # "What it is" section
    # ------------------------------------------------------

    software_str = (
        ", ".join(affected_software)
        or "unspecified software"
    )

    versions_str = ", ".join(
        affected_versions
    )

    what_it_is = (
        f"{cve_id} is a {severity} severity vulnerability "
        f"affecting {software_str}"
        + (
            f" (versions {versions_str})"
            if versions_str
            else ""
        )
        + "."
    )

    # ------------------------------------------------------
    # "Security significance" section
    # ------------------------------------------------------

    if cvss_score is not None:

        significance = (
            f"{evidence_source} assigns this vulnerability a "
            f"CVSS {cvss_version or ''} score of {cvss_score}. "
            f"Deterministic risk assessment: {risk_assessment}."
        )

    else:

        significance = (
            f"No CVSS score is available; severity is reported "
            f"as {severity}. Deterministic risk assessment: "
            f"{risk_assessment}."
        )

    # ------------------------------------------------------
    # "Organizational relevance" section
    # ------------------------------------------------------

    org_lines = [
        f"**{organizational_relevance}** — {relevance_reason}"
    ]

    if organizational_relevance == "UNKNOWN":

        org_lines.append(
            "This does not mean the organization is unaffected — "
            "it means there is not enough evidence to determine "
            "applicability."
        )

    for asset in matched_assets:

        org_lines.append(
            f"- {asset.get('asset_id')}: "
            f"{asset.get('software')} "
            f"{asset.get('installed_version')} "
            f"(criticality: {asset.get('criticality')}, "
            f"exposure: {asset.get('exposure')})"
        )

    if applicability_confidence is not None:

        org_lines.append(
            f"Applicability confidence: "
            f"{applicability_confidence}"
        )

    # ------------------------------------------------------
    # "Evidence" section
    # ------------------------------------------------------

    evidence_lines = [
        f"- Vulnerability source: {evidence_source}"
    ]

    evidence_lines += [
        f"- {item}"
        for item in applicability_evidence
    ]

    if missing_evidence:

        evidence_lines.append("")
        evidence_lines.append("Missing evidence:")

        evidence_lines += [
            f"- {item}"
            for item in missing_evidence
        ]

    # ------------------------------------------------------
    # "Contextual priority" section
    # ------------------------------------------------------

    if contextual_priority:

        priority_section = (
            f"**{contextual_priority['priority_label']}** "
            f"({contextual_priority['priority_score']}/100)\n"
            f"Basis: {contextual_priority['priority_basis']}"
        )

    else:

        priority_section = "Not calculated."

    # ------------------------------------------------------
    # "Recommended actions" section
    # ------------------------------------------------------

    recommendations_section = (
        "\n".join(
            f"- {item}"
            for item in recommendations
        )
        if recommendations
        else "- No specific actions generated."
    )

    # ------------------------------------------------------
    # Assemble final response
    # ------------------------------------------------------

    content = f"""## {cve_id}

### What it is
{what_it_is}

### Security significance
{significance}

### Organizational relevance
{chr(10).join(org_lines)}

### Contextual priority
{priority_section}

### Evidence
{chr(10).join(evidence_lines)}

### Recommended actions
{recommendations_section}
"""

    end = time.perf_counter()

    if settings.LEARN_MODE:

        print(
            f"⏱ Response Builder Time: "
            f"{end - start:.4f} sec"
        )

        print(
            "✅ Deterministic response generated."
        )

    return {
        "messages": [
            AIMessage(
                content=content
            )
        ]
    }


# ==========================================================
# Router
# ==========================================================

def supervisor_router(state):

    route = state["route"]

    if route == "memory":

        return "memory"

    return "assistant"