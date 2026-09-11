"""
investigation_engine.py

Pure, LangChain/LangGraph-independent vulnerability investigation
logic: applicability analysis, deterministic recommendations, and
contextual risk prioritization.

This module has no dependency on LLMs, LangGraph state, or chat
messages. It operates on plain dicts (a parsed vulnerability record,
an inventory, an organization context) and returns a plain dict (a
structured investigation record).

It is the single source of truth for "given vulnerability evidence
and organization context, what is the investigation result" — used
by both:

- agents.py's security_investigation_node (the interactive,
  LangGraph-driven single-CVE path)
- batch.py (the non-interactive, multi-CVE batch path)

Keeping this logic in one place means the two paths cannot silently
drift apart, which matters for research reproducibility: a batch
evaluation run and a live chat investigation of the same CVE must
produce the same structured result.
"""

from applicability import analyze_applicability


# ==========================================================
# Security Recommendation Engine
# ==========================================================

def generate_security_recommendation(
    severity,
    cvss_score,
    organizational_relevance,
):
    """
    Generate deterministic security actions based on:
    - vulnerability severity
    - CVSS score
    - organizational relevance
    """

    recommendations = []

    # ------------------------------------------------------
    # Critical vulnerabilities
    # ------------------------------------------------------

    if (
        severity
        and severity.upper() == "CRITICAL"
    ) or (
        cvss_score is not None
        and cvss_score >= 9.0
    ):

        recommendations.extend([
            "Identify systems running the affected software.",
            "Verify whether vulnerable versions exist in the environment.",
            "Apply vendor patches or upgrade to a fixed version.",
            "Review security logs for possible exploitation attempts.",
        ])

    # ------------------------------------------------------
    # High vulnerabilities
    # ------------------------------------------------------

    elif (
        severity
        and severity.upper() == "HIGH"
    ) or (
        cvss_score is not None
        and cvss_score >= 7.0
    ):

        recommendations.extend([
            "Identify affected assets.",
            "Schedule remediation based on risk priority.",
            "Monitor affected systems.",
        ])

    # ------------------------------------------------------
    # Medium / Low / Unknown
    # ------------------------------------------------------

    else:

        recommendations.extend([
            "Review vulnerability details.",
            "Monitor vendor updates.",
        ])

    # ------------------------------------------------------
    # Organization relevance adjustment
    # ------------------------------------------------------

    if organizational_relevance == "RELEVANT":

        recommendations.append(
            "Prioritize investigation because "
            "the vulnerability appears related "
            "to known organizational assets."
        )

    elif organizational_relevance == "UNKNOWN":

        recommendations.append(
            "Verify whether affected technology "
            "exists within the organization."
        )

    return recommendations


# ==========================================================
# Contextual Risk Prioritization
# ==========================================================

CVSS_COMPONENT_MAX = 50
CRITICALITY_COMPONENT_MAX = 30
EXPOSURE_COMPONENT_MAX = 20

_SEVERITY_FALLBACK_SCORE = {
    "CRITICAL": 9.5,
    "HIGH": 7.5,
    "MEDIUM": 5.0,
    "LOW": 2.0,
}

_CRITICALITY_POINTS = {
    "CRITICAL": 30,
    "HIGH": 20,
    "MEDIUM": 10,
    "LOW": 5,
}

_EXPOSURE_POINTS = {
    "INTERNET": 20,
    "INTERNAL": 8,
}


def _cvss_component(severity, cvss_score):
    """
    0-50 points, derived from CVSS score when available, or a
    conservative severity-label fallback when it is not.
    """

    if cvss_score is not None:

        return (
            cvss_score / 10.0
        ) * CVSS_COMPONENT_MAX

    if severity:

        fallback = _SEVERITY_FALLBACK_SCORE.get(
            severity.upper()
        )

        if fallback is not None:

            return (
                fallback / 10.0
            ) * CVSS_COMPONENT_MAX

    return 0.0


def _criticality_component(matched_assets):
    """
    0-30 points, using the highest asset criticality among
    matched assets.
    """

    best = 0

    for asset in matched_assets:

        points = _CRITICALITY_POINTS.get(
            (asset.get("criticality") or "").upper(),
            0,
        )

        if points > best:
            best = points

    return best


def _exposure_component(matched_assets):
    """
    0-20 points, using the highest exposure level among
    matched assets.
    """

    best = 0

    for asset in matched_assets:

        points = _EXPOSURE_POINTS.get(
            (asset.get("exposure") or "").upper(),
            0,
        )

        if points > best:
            best = points

    return best


def calculate_contextual_priority(
    severity,
    cvss_score,
    organizational_relevance,
    applicability_confidence,
    matched_assets,
):
    """
    Compute a contextual risk priority score (0-100) and label,
    combining:

    - CVSS / severity (up to 50 points)
    - asset criticality, when the vulnerability is confirmed
      RELEVANT to specific assets (up to 30 points)
    - asset exposure, same condition (up to 20 points)

    Organizational relevance gates which components apply:

    - RELEVANT   : full CVSS + criticality + exposure scoring,
                   since specific affected assets are known.
    - UNKNOWN    : CVSS component only. No asset-specific
                   scoring is applied, because no asset is
                   confirmed affected.
    - NOT_RELEVANT: CVSS component heavily discounted (x0.2),
                   since the vulnerability is confidently
                   assessed as not applicable to known assets.

    Applicability confidence then caps the final score:

        final_score = min(raw_score, confidence * 100)

    This ensures low-confidence or UNKNOWN cases can never
    reach a CRITICAL priority, even when the underlying CVSS
    score is maximal — priority reflects not just how bad a
    vulnerability could be, but how confident the system is
    that it applies to this organization's assets.

    Returns a dict with the numeric score, a derived label, and
    a short explanation of which formula branch was used, so
    the result remains traceable to its inputs.
    """

    cvss_points = _cvss_component(
        severity,
        cvss_score,
    )

    if organizational_relevance == "RELEVANT":

        criticality_points = _criticality_component(
            matched_assets
        )

        exposure_points = _exposure_component(
            matched_assets
        )

        raw_score = (
            cvss_points
            + criticality_points
            + exposure_points
        )

        basis = (
            "CVSS + asset criticality + exposure "
            "(organization confirmed affected)"
        )

    elif organizational_relevance == "UNKNOWN":

        raw_score = cvss_points

        basis = (
            "CVSS only "
            "(organizational applicability could not be confirmed)"
        )

    else:

        raw_score = cvss_points * 0.2

        basis = (
            "CVSS heavily discounted "
            "(vulnerability confirmed not applicable "
            "to known assets)"
        )

    confidence = (
        applicability_confidence
        if applicability_confidence is not None
        else 0.0
    )

    confidence_cap = confidence * 100

    final_score = max(
        0,
        round(
            min(
                raw_score,
                confidence_cap,
            )
        ),
    )

    if final_score >= 80:
        label = "CRITICAL"
    elif final_score >= 60:
        label = "HIGH"
    elif final_score >= 35:
        label = "MEDIUM"
    else:
        label = "LOW"

    return {
        "priority_score": final_score,
        "priority_label": label,
        "priority_basis": basis,
        "raw_score": round(raw_score, 1),
        "confidence_cap": round(confidence_cap, 1),
    }


# ==========================================================
# Build Investigation
# ==========================================================

def build_investigation(
    vulnerability: dict,
    inventory: list,
    organization_context: dict,
) -> dict:
    """
    Build a structured investigation record from a parsed
    vulnerability record (the same shape returned by
    apis.vulnerabilities.get_vulnerability / tools.vulnerability_lookup),
    an organization asset inventory, and organization context.

    This function is pure: it performs no I/O (no NVD calls, no
    LLM calls, no database access) and has no side effects. It is
    the single source of truth for turning vulnerability evidence
    into an investigation result, shared by both the interactive
    LangGraph path and the batch path.

    Callers are responsible for:
    - retrieving the vulnerability record (from NVD or a tool)
    - loading the inventory and organization context
    - any logging/printing around this call

    Returns a dict matching the shape of InvestigationState
    (state.py), with "status": "retrieved".
    """

    # ------------------------------------------------------
    # Extract vulnerability evidence
    # ------------------------------------------------------

    cve_id = vulnerability.get(
        "cve_id"
    )

    severity = vulnerability.get(
        "severity"
    )

    cvss_score = vulnerability.get(
        "cvss_score"
    )

    cvss_version = vulnerability.get(
        "cvss_version"
    )

    description = vulnerability.get(
        "description"
    )

    affected_software = vulnerability.get(
        "affected_software",
        []
    )

    affected_versions = vulnerability.get(
        "affected_versions",
        []
    )

    affected_products = vulnerability.get(
        "affected_products",
        []
    )

    # ------------------------------------------------------
    # Index structured per-product data by product name so
    # each software's version_ranges/vendor can be looked up
    # when analyzing applicability below.
    # ------------------------------------------------------

    affected_products_by_name = {
        product.get("product"): product
        for product in affected_products
    }

    # ------------------------------------------------------
    # Analyze organizational applicability
    # ------------------------------------------------------

    applicability_results = []

    for software in affected_software:

        product_entry = affected_products_by_name.get(
            software,
            {}
        )

        version_ranges = product_entry.get(
            "version_ranges",
            []
        )

        vendor = product_entry.get(
            "vendor"
        )

        result = analyze_applicability(
            cve_id=cve_id,
            description=description or "",
            affected_software=software,
            affected_versions=affected_versions,
            version_ranges=version_ranges,
            vendor=vendor,
            inventory=inventory,
            organization_context=organization_context,
        )

        applicability_results.append(
            result
        )

    # ------------------------------------------------------
    # No identifiable affected software
    # ------------------------------------------------------

    if not applicability_results:

        applicability = {
            "cve_id": cve_id,
            "status": "UNKNOWN",
            "confidence": 0.20,
            "matched_assets": [],
            "evidence": [],
            "missing_evidence": [
                "NVD did not provide identifiable "
                "affected software."
            ],
            "reason": (
                "The vulnerability evidence does not identify "
                "affected software that can be compared against "
                "the organization inventory."
            ),
        }

    else:

        # --------------------------------------------------
        # Separate results by applicability status
        # --------------------------------------------------

        relevant_results = [
            result
            for result in applicability_results
            if result.get("status") == "RELEVANT"
        ]

        unknown_results = [
            result
            for result in applicability_results
            if result.get("status") == "UNKNOWN"
        ]

        not_relevant_results = [
            result
            for result in applicability_results
            if result.get("status") == "NOT_RELEVANT"
        ]

        # --------------------------------------------------
        # RELEVANT takes priority
        # --------------------------------------------------

        if relevant_results:

            applicability = {
                "cve_id": cve_id,
                "status": "RELEVANT",
                "confidence": max(
                    result.get(
                        "confidence",
                        0.0
                    )
                    for result in relevant_results
                ),
                "matched_assets": [
                    asset
                    for result in relevant_results
                    for asset in result.get(
                        "matched_assets",
                        []
                    )
                ],
                "evidence": [
                    evidence
                    for result in relevant_results
                    for evidence in result.get(
                        "evidence",
                        []
                    )
                ],
                "missing_evidence": [
                    evidence
                    for result in relevant_results
                    for evidence in result.get(
                        "missing_evidence",
                        []
                    )
                ],
                "reason": (
                    "At least one affected software product "
                    "identified by NVD matches a vulnerable "
                    "software version in the organization inventory."
                ),
            }

        # --------------------------------------------------
        # UNKNOWN takes priority over NOT_RELEVANT
        #
        # This is important:
        #
        # Absence of evidence must not automatically become
        # evidence of absence.
        # --------------------------------------------------

        elif unknown_results:

            applicability = {
                "cve_id": cve_id,
                "status": "UNKNOWN",
                "confidence": max(
                    result.get(
                        "confidence",
                        0.0
                    )
                    for result in unknown_results
                ),
                "matched_assets": [],
                "evidence": [
                    evidence
                    for result in unknown_results
                    for evidence in result.get(
                        "evidence",
                        []
                    )
                ],
                "missing_evidence": [
                    evidence
                    for result in unknown_results
                    for evidence in result.get(
                        "missing_evidence",
                        []
                    )
                ],
                "reason": (
                    "The available organization inventory does not "
                    "provide sufficient evidence to determine whether "
                    "the vulnerability applies."
                ),
            }

        # --------------------------------------------------
        # All known products are NOT_RELEVANT
        # --------------------------------------------------

        else:

            applicability = {
                "cve_id": cve_id,
                "status": "NOT_RELEVANT",
                "confidence": max(
                    result.get(
                        "confidence",
                        0.0
                    )
                    for result in not_relevant_results
                ),
                "matched_assets": [],
                "evidence": [
                    evidence
                    for result in not_relevant_results
                    for evidence in result.get(
                        "evidence",
                        []
                    )
                ],
                "missing_evidence": [],
                "reason": (
                    "Affected software identified by NVD is present "
                    "in the inventory, but none of the available "
                    "installed versions match the known affected "
                    "versions."
                ),
            }

    # ------------------------------------------------------
    # Extract final applicability values
    # ------------------------------------------------------

    organizational_relevance = (
        applicability["status"]
    )

    relevance_reason = (
        applicability["reason"]
    )

    matched_assets = (
        applicability["matched_assets"]
    )

    # ------------------------------------------------------
    # Generate security recommendations
    # ------------------------------------------------------

    recommendations = (
        generate_security_recommendation(
            severity,
            cvss_score,
            organizational_relevance,
        )
    )

    # ------------------------------------------------------
    # Calculate contextual risk priority
    # ------------------------------------------------------

    contextual_priority = (
        calculate_contextual_priority(
            severity=severity,
            cvss_score=cvss_score,
            organizational_relevance=organizational_relevance,
            applicability_confidence=applicability["confidence"],
            matched_assets=matched_assets,
        )
    )

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

        # --------------------------------------------------
        # Vulnerability evidence
        # --------------------------------------------------

        "cve_id": cve_id,

        "severity": severity,

        "cvss_score": cvss_score,

        "cvss_version": cvss_version,

        "description": description,

        "affected_software": affected_software,

        "affected_versions": affected_versions,

        "affected_products": affected_products,

        # --------------------------------------------------
        # Evidence provenance
        # --------------------------------------------------

        "evidence": {

            "vulnerability_source": vulnerability.get(
                "source",
                "NVD"
            ),

            "organizational_relevance": (
                applicability["status"]
            ),

            "relevance_reason": (
                applicability["reason"]
            ),

            "matched_assets": (
                applicability["matched_assets"]
            ),

            "applicability_confidence": (
                applicability["confidence"]
            ),

            "applicability_evidence": (
                applicability["evidence"]
            ),

            "missing_evidence": (
                applicability["missing_evidence"]
            ),

        },

        # --------------------------------------------------
        # Investigation status
        # --------------------------------------------------

        "status": "retrieved",

        # --------------------------------------------------
        # Deterministic risk assessment
        # --------------------------------------------------

        "risk_assessment": risk_assessment,

        # --------------------------------------------------
        # Organization context
        # --------------------------------------------------

        "organization_context": (
            organization_context
        ),

        # --------------------------------------------------
        # Contextual applicability
        # --------------------------------------------------

        "organizational_relevance": (
            organizational_relevance
        ),

        "relevance_reason": (
            relevance_reason
        ),

        "matched_assets": (
            matched_assets
        ),

        "applicability_confidence": (
            applicability["confidence"]
        ),

        "applicability_evidence": (
            applicability["evidence"]
        ),

        "missing_evidence": (
            applicability["missing_evidence"]
        ),

        # --------------------------------------------------
        # Security recommendations
        # --------------------------------------------------

        "recommendations": recommendations,

        # --------------------------------------------------
        # Contextual risk prioritization
        # --------------------------------------------------

        "contextual_priority": contextual_priority,

        # --------------------------------------------------
        # Analysis
        # --------------------------------------------------

        "analysis": (
            f"The vulnerability is classified as "
            f"{severity or 'UNKNOWN'} with a CVSS score of "
            f"{cvss_score if cvss_score is not None else 'N/A'}. "
            f"The resulting risk assessment is "
            f"{risk_assessment}. "
            f"Organizational relevance is "
            f"{organizational_relevance}. "
            f"Reason: {relevance_reason}"
        ),
    }

    return investigation