"""
baselines.py

Baseline vulnerability prioritization approaches, for comparison
against the proposed agentic system (handoff item 25).

Each baseline is a deliberately simpler, self-contained
implementation -- NOT a reuse of investigation_engine's logic --
because the point of a baseline is to represent a genuinely
different, less sophisticated level of capability:

1. CVSS-only
   Priority is derived purely from the CVE's own CVSS score /
   severity. No organization context of any kind. This is the
   "CVE -> CVSS" status quo the handoff explicitly frames the
   whole project as moving beyond (item 35).

2. CVSS + naive keyword matching
   Adds a check for whether the affected product's NAME appears
   anywhere in the organization's inventory -- a simple
   case-insensitive substring match in either direction, with NO
   vendor awareness, NO software-identity normalization, and NO
   version comparison at all. If the name matches anything,
   installed software is assumed affected regardless of version.

3. CVSS + organization context (criticality/exposure), same naive
   matching as (2)
   Adds asset criticality/exposure scoring on top of a keyword
   match, but still without proper applicability analysis. This
   isolates one question: does adding rich context scoring alone
   fix the false-positive problem, or does it just make wrong
   matches look more confidently wrong? (It's the latter -- see
   the NOT_RELEVANT comparison case.)

4. Proposed (this project's system)
   investigation_engine.build_investigation() -- normalization,
   version-range matching, RELEVANT/UNKNOWN/NOT_RELEVANT
   applicability, and confidence-capped contextual priority.

IMPORTANT CAVEAT about comparing against eval_dataset.DATASET:

For the dataset's SYNTHETIC cases, "expected" values were derived
by running the proposed system itself (see eval_dataset.py's
docstring) -- so "proposed" will trivially match ground truth on
those cases by construction. The synthetic comparisons here are
still useful to see EACH baseline's qualitative behavior and
failure modes, but they are not a fair accuracy measurement of
"proposed" specifically. The dataset's one REAL case
(CVE-2024-3094) is independently-verified real-world ground
truth, and is the only case in this dataset where comparing all
four approaches against ground truth is unbiased. A rigorous
accuracy comparison needs a larger real-CVE dataset -- that is
future work beyond this step, not something this file claims to
provide.
"""

from inventory import find_software


# ==========================================================
# Shared label thresholds (kept identical across baselines and
# the proposed system, so label comparisons are apples-to-apples
# and only the SCORE formula differs between approaches)
# ==========================================================

def _label_from_score(score):

    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 35:
        return "MEDIUM"
    else:
        return "LOW"


def _cvss_score_0_100(vulnerability):
    """
    Map CVSS score (0-10) to a 0-100 scale, falling back to a
    severity label when no numeric score is available. Used
    identically by all three baselines, since none of them
    differ in HOW they read the raw CVSS/severity fields --
    they differ in what else they add on top.
    """

    cvss_score = vulnerability.get(
        "cvss_score"
    )

    if cvss_score is not None:
        return (cvss_score / 10.0) * 100

    severity = vulnerability.get(
        "severity"
    )

    fallback = {
        "CRITICAL": 95,
        "HIGH": 75,
        "MEDIUM": 50,
        "LOW": 20,
    }

    if severity:
        return fallback.get(
            severity.upper(),
            0,
        )

    return 0


# ==========================================================
# Baseline 1: CVSS-only
# ==========================================================

def baseline_cvss_only(vulnerability):
    """
    Priority is the CVE's own severity, full stop. No concept
    of organizational relevance exists in this baseline -- every
    vulnerability is implicitly treated as if it applies.
    """

    score = round(
        _cvss_score_0_100(vulnerability)
    )

    return {
        "approach": "cvss_only",
        "relevance": "N/A (not modeled)",
        "matched_assets": [],
        "priority_score": score,
        "priority_label": _label_from_score(score),
    }


# ==========================================================
# Baseline 2: CVSS + naive keyword matching
# ==========================================================

def _naive_keyword_matches(vulnerability, inventory):
    """
    For each affected software name, find installed software
    whose name contains it (or is contained by it),
    case-insensitively. No vendor check, no version check.
    Deliberately naive.
    """

    affected_software = vulnerability.get(
        "affected_software",
        []
    )

    matches = []

    for product in affected_software:

        product_lower = (product or "").lower()

        if not product_lower:
            continue

        for asset in inventory:

            for software in asset["software"]:

                installed_lower = (
                    software["name"].lower()
                )

                if (
                    product_lower in installed_lower
                    or installed_lower in product_lower
                ):

                    matches.append({
                        "asset_id": asset["asset_id"],
                        "software": software["name"],
                        "installed_version": software["version"],
                        "criticality": asset["criticality"],
                        "exposure": asset["exposure"],
                    })

    return matches


def baseline_cvss_keyword(vulnerability, inventory):
    """
    CVSS score plus a binary "does the name appear anywhere in
    inventory" check. No version awareness: a name match is
    treated as a confirmed hit regardless of whether the
    installed version is actually affected.
    """

    matches = _naive_keyword_matches(
        vulnerability,
        inventory,
    )

    base_score = _cvss_score_0_100(
        vulnerability
    )

    if matches:

        score = round(base_score)
        relevance = "MATCH"

    else:

        score = 0
        relevance = "NO_MATCH"

    return {
        "approach": "cvss_keyword",
        "relevance": relevance,
        "matched_assets": matches,
        "priority_score": score,
        "priority_label": _label_from_score(score),
    }


# ==========================================================
# Baseline 3: CVSS + organization context, naive matching
# ==========================================================

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


def baseline_cvss_context(vulnerability, inventory):
    """
    Same naive keyword matching as baseline 2, but adds asset
    criticality/exposure scoring on top -- without any real
    applicability analysis (no normalization, no version check).

    This isolates one question: does adding rich context scoring
    alone fix the false-positive problem that naive matching
    creates? It does not -- it just makes a wrong match look more
    confidently wrong, since a keyword hit on the wrong version
    still receives full criticality/exposure points.
    """

    matches = _naive_keyword_matches(
        vulnerability,
        inventory,
    )

    cvss_points = (
        _cvss_score_0_100(vulnerability) / 100.0
    ) * 50

    if not matches:

        return {
            "approach": "cvss_context",
            "relevance": "NO_MATCH",
            "matched_assets": [],
            "priority_score": 0,
            "priority_label": _label_from_score(0),
        }

    best_criticality = max(
        (
            _CRITICALITY_POINTS.get(
                (m.get("criticality") or "").upper(),
                0,
            )
            for m in matches
        ),
        default=0,
    )

    best_exposure = max(
        (
            _EXPOSURE_POINTS.get(
                (m.get("exposure") or "").upper(),
                0,
            )
            for m in matches
        ),
        default=0,
    )

    score = round(
        cvss_points
        + best_criticality
        + best_exposure
    )

    return {
        "approach": "cvss_context",
        "relevance": "MATCH",
        "matched_assets": matches,
        "priority_score": score,
        "priority_label": _label_from_score(score),
    }


# ==========================================================
# Comparison Runner
# ==========================================================

def compare_all(
    vulnerability,
    inventory,
    organization_context,
):
    """
    Run all three baselines plus the proposed system on the same
    vulnerability record and inventory, returning a dict keyed by
    approach name.
    """

    from investigation_engine import build_investigation

    proposed = build_investigation(
        vulnerability=vulnerability,
        inventory=inventory,
        organization_context=organization_context,
    )

    proposed_summary = {
        "approach": "proposed",
        "relevance": proposed.get(
            "organizational_relevance"
        ),
        "matched_assets": proposed.get(
            "matched_assets",
            []
        ),
        "priority_score": proposed.get(
            "contextual_priority",
            {}
        ).get("priority_score"),
        "priority_label": proposed.get(
            "contextual_priority",
            {}
        ).get("priority_label"),
    }

    return {
        "cvss_only": baseline_cvss_only(
            vulnerability
        ),
        "cvss_keyword": baseline_cvss_keyword(
            vulnerability,
            inventory,
        ),
        "cvss_context": baseline_cvss_context(
            vulnerability,
            inventory,
        ),
        "proposed": proposed_summary,
    }


def print_comparison_table(case_id, results):

    print(f"\n=== {case_id} ===")

    print(
        f"{'Approach':<15}{'Relevance':<12}"
        f"{'Assets':<10}{'Priority':<20}"
    )
    print("-" * 60)

    for approach_key in (
        "cvss_only",
        "cvss_keyword",
        "cvss_context",
        "proposed",
    ):

        result = results[approach_key]

        priority_display = (
            f"{result['priority_label']} "
            f"({result['priority_score']}/100)"
        )

        print(
            f"{result['approach']:<15}"
            f"{str(result['relevance']):<12}"
            f"{len(result['matched_assets']):<10}"
            f"{priority_display:<20}"
        )


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    from database import initialize_database
    from inventory import get_demo_inventory
    from memory import get_organization_context
    from apis.vulnerabilities import get_vulnerability
    from apis.exceptions import (
        InvalidCVEError,
        VulnerabilityAPIError,
        VulnerabilityNotFoundError,
    )

    from eval_dataset import DATASET

    initialize_database()

    inventory = get_demo_inventory()
    organization_context = get_organization_context()

    print(
        "Comparing baselines against the proposed system "
        "across the evaluation dataset."
    )
    print(
        "NOTE: for synthetic cases, 'proposed' matches its own "
        "regression-test ground truth by construction -- see "
        "this file's module docstring. The real CVE case "
        "(CVE-2024-3094) is the only unbiased comparison point."
    )

    for case in DATASET:

        if case["mode"] == "synthetic":

            vulnerability = case["vulnerability"]

        else:

            try:

                vulnerability = get_vulnerability(
                    case["cve_id"]
                )

            except (
                InvalidCVEError,
                VulnerabilityNotFoundError,
                VulnerabilityAPIError,
            ) as exc:

                print(
                    f"\n=== {case['id']} ==="
                )

                print(
                    f"SKIPPED: NVD lookup failed: {exc}"
                )

                continue

        results = compare_all(
            vulnerability,
            inventory,
            organization_context,
        )

        print_comparison_table(
            case["id"],
            results,
        )