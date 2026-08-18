"""
agents.py

All LangGraph nodes used by the AI Assistant.
"""
from router import detect_intent


import settings
from config import llm

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)


from memory import (
    remember,
    recall,
    get_organization_context,
)

# ==========================================================
# Organizational Relevance Analysis
# ==========================================================

def analyze_organizational_relevance(
    description: str,
    organization_context: dict,
):
    """
    Determine whether the vulnerability evidence appears
    relevant to the organization's known technologies.

    This is deliberately conservative.

    RELEVANT:
        A known organization technology is explicitly
        mentioned in the vulnerability description.

    NOT_RELEVANT:
        The description contains identifiable technology
        information, but none matches known organization
        technologies.

    UNKNOWN:
        There is not enough evidence to establish relevance.
    """

    if not description:
        return {
            "status": "UNKNOWN",
            "reason": "The vulnerability description is empty.",
            "matched_assets": [],
        }

    description_lower = description.lower()

    # ------------------------------------------------------
    # Known organization technologies
    # ------------------------------------------------------

    known_assets = []

    for key in [
        "firewall_vendor",
        "siem_platform",
    ]:

        value = organization_context.get(key)

        if value:
            known_assets.append(
                value.strip()
            )

    # ------------------------------------------------------
    # No known technologies
    # ------------------------------------------------------

    if not known_assets:

        return {
            "status": "UNKNOWN",
            "reason": (
                "No organization technologies are currently "
                "stored in memory."
            ),
            "matched_assets": [],
        }

    # ------------------------------------------------------
    # Match known technologies against CVE description
    # ------------------------------------------------------

    matched_assets = []

    for asset in known_assets:

        if asset.lower() in description_lower:

            matched_assets.append(asset)

    # ------------------------------------------------------
    # Relevant
    # ------------------------------------------------------

    if matched_assets:

        return {
            "status": "RELEVANT",
            "reason": (
                "The vulnerability description explicitly "
                "mentions technology used by the organization."
            ),
            "matched_assets": matched_assets,
        }

    # ------------------------------------------------------
    # No direct match
    #
    # We intentionally return UNKNOWN rather than
    # NOT_RELEVANT because absence of a keyword does not
    # prove that the organization is unaffected.
    # ------------------------------------------------------

    return {
        "status": "UNKNOWN",
        "reason": (
            "The available vulnerability evidence does not "
            "establish a connection to the organization's "
            "known technologies."
        ),
        "matched_assets": [],
    }

from prompts import (
    ASSISTANT_PROMPT,
)
from tools import TOOLS


# ==========================================================
# ReAct Assistant
# ==========================================================

assistant_llm = llm.bind_tools(TOOLS)


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
            print("✅ Decision     : Route → Memory Node")

        return {
            "route": "memory"
        }

    if settings.LEARN_MODE:
        print("✅ Decision     : Route → Assistant Node")

    return {
        "route": "assistant"
    }
  

def memory_node(state):

    if settings.LEARN_MODE:
        print("\n🧠 Current Node : Memory")

    last_message = state["messages"][-1].content.strip()
    text = last_message.lower()

    # ======================================================
    # Store organization information
    # Example:
    # Remember our firewall vendor is Palo Alto.
    # ======================================================

    if text.startswith("remember our ") and " is " in text:

        before, value = last_message.split(" is ", 1)

        key = before[len("Remember our "):].strip()
        key = (
            key
            .rstrip("?.!")
            .replace(" ", "_")
            .lower()
        )

        if key == "company":
            key = "organization"

        value = value.strip().rstrip("?.!")

        if settings.LEARN_MODE:
            print(f"💾 Action       : Store {key} = {value}")

        remember(key, value)

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
    # Examples:
    # What is our firewall vendor?
    # What's our SIEM platform?
    # ======================================================

    if text.startswith("what is our ") or text.startswith("what's our "):

        if text.startswith("what is our "):
            key = last_message[len("What is our "):]
        else:
            key = last_message[len("What's our "):]

        key = key.strip().rstrip("?.!").replace(" ", "_").lower()

        if settings.LEARN_MODE:
            print(f"🔍 Action       : Retrieve {key}")

        value = recall(key)

        if value:
            return {
                "messages": [
                    AIMessage(
                        content=(
                            f"Our {key.replace('_', ' ')} is {value}."
                        )
                    )
                ]
            }

        return {
            "messages": [
                AIMessage(
                    content=(
                        f"I don't have any information about our "
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

import time


def assistant_node(state):

    if settings.LEARN_MODE:
        print("\n🤖 Current Node : Assistant")
        print("🧠 Action       : Thinking...")

    start = time.perf_counter()

    # ------------------------------------------------------
    # Build investigation context
    # ------------------------------------------------------

    investigation = state.get("investigation")

    investigation_context = ""

    if investigation:

        investigation_context = f"""

CURRENT SECURITY INVESTIGATION STATE:

CVE ID:
{investigation.get("cve_id", "N/A")}

Severity:
{investigation.get("severity", "N/A")}

CVSS Score:
{investigation.get("cvss_score", "N/A")}

Risk Assessment:
{investigation.get("risk_assessment", "N/A")}

Evidence Source:
{investigation.get("source", "N/A")}

Status:
{investigation.get("status", "N/A")}

Description:
{investigation.get("description", "N/A")}

Analysis:
{investigation.get("analysis", "N/A")}

Use this structured investigation state when answering the user.
Do not invent information that is not present in the evidence.
"""

    # ------------------------------------------------------
    # Invoke Assistant
    # ------------------------------------------------------

    response = assistant_llm.invoke(
        [
            SystemMessage(
                content=ASSISTANT_PROMPT
                + investigation_context
            ),
            *state["messages"],
        ]
    )

    end = time.perf_counter()

    if settings.LEARN_MODE:

        print(
            f"⏱ Assistant Time: "
            f"{end-start:.3f} sec"
        )

        if response.tool_calls:
            print("🛠 Decision     : Tool Required")
        else:
            print("💬 Decision     : Respond Directly")

    return {
        "messages": [response]
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

    import json

    if settings.LEARN_MODE:
        print("\n🔐 Current Node : Security Investigation")

        # ------------------------------------------------------
    # Load persistent organization context
    # ------------------------------------------------------

    organization_context = get_organization_context()

    if settings.LEARN_MODE:

        print("🏢 Organization Context")

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
    # Find the most recent vulnerability tool response
    # ------------------------------------------------------

    tool_message = None

    for message in reversed(state["messages"]):

        if getattr(message, "type", None) == "tool":

            if (
                getattr(message, "name", None)
                == "vulnerability_lookup"
            ):
                tool_message = message
                break

    # ------------------------------------------------------
    # No evidence
    # ------------------------------------------------------

    if tool_message is None:

        if settings.LEARN_MODE:
            print("⚠ No vulnerability evidence found.")

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

    if vulnerability.get("status") == "error":

        if settings.LEARN_MODE:
            print(
                "❌ Vulnerability evidence "
                "contains an API error."
            )

        return {
            "investigation": {
                "cve_id": vulnerability.get("cve_id"),
                "source": "NVD",
                "status": "failed",
                "error": vulnerability.get("error"),
            }
        }

    # ------------------------------------------------------
    # Extract evidence
    # ------------------------------------------------------

    severity = vulnerability.get("severity")
    cvss_score = vulnerability.get("cvss_score")

    # ------------------------------------------------------
    # Determine risk assessment
    # ------------------------------------------------------

    if cvss_score is not None:

        if cvss_score >= 9.0:
            risk_assessment = "CRITICAL"

        elif cvss_score >= 7.0:
            risk_assessment = "HIGH"

        elif cvss_score >= 4.0:
            risk_assessment = "MEDIUM"

        else:
            risk_assessment = "LOW"

    else:

        risk_assessment = (
            severity.upper()
            if severity
            else "UNKNOWN"
        )

    # ------------------------------------------------------
    # Build structured investigation state
    # ------------------------------------------------------

    investigation = {
    # ------------------------------------------------------
    # Vulnerability evidence
    # ------------------------------------------------------

    "cve_id": vulnerability.get("cve_id"),
    "severity": severity,
    "cvss_score": cvss_score,
    "description": vulnerability.get("description"),

    # ------------------------------------------------------
    # Evidence provenance
    # ------------------------------------------------------

    "source": vulnerability.get("source", "NVD"),

    # ------------------------------------------------------
    # Investigation status
    # ------------------------------------------------------

    "status": "retrieved",

    # ------------------------------------------------------
    # Deterministic risk assessment
    # ------------------------------------------------------

    "risk_assessment": risk_assessment,

    # ------------------------------------------------------
    # Organization context
    # ------------------------------------------------------

    "organization_context": organization_context,

    # ------------------------------------------------------
    # Contextual relevance
    #
    # We do NOT claim the CVE affects the organization yet.
    # That requires evidence.
    # ------------------------------------------------------

    "organizational_relevance": "UNKNOWN",

    # ------------------------------------------------------
    # Analysis
    # ------------------------------------------------------

    "analysis": (
        f"The vulnerability is classified as "
        f"{severity or 'UNKNOWN'} with a CVSS score of "
        f"{cvss_score if cvss_score is not None else 'N/A'}. "
        f"The resulting risk assessment is "
        f"{risk_assessment}. "
        f"Organizational relevance has not yet been established."
    ),
}

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
            f"⚠ Risk Level    : "
            f"{investigation['risk_assessment']}"
        )

        print(
            f"📚 Evidence     : "
            f"{investigation['source']}"
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
# Router
# ==========================================================

def supervisor_router(state):

    route = state["route"]

    if route == "memory":
        return "memory"

    return "assistant"
