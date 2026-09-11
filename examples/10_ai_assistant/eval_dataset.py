"""
eval_dataset.py

Ground-truth evaluation dataset for the vulnerability applicability
and contextual prioritization pipeline (handoff items 26-27).

Two kinds of cases:

- mode="real": a real, published CVE. The expected values reflect
  actual, human-verified real-world facts (confirmed against live
  NVD data and the demo inventory in prior manual test runs), not
  just "whatever the code currently does." These cases require a
  live NVD API call to run.

- mode="synthetic": a fully-specified, made-up vulnerability record
  (same shape as apis.vulnerabilities.get_vulnerability()'s return
  value) fed directly into investigation_engine.build_investigation()
  with no network call. This makes the dataset reproducible offline,
  and lets it exercise specific code paths (each distinct reason for
  an UNKNOWN result, version-range matching, vendor-precision
  normalization) that are hard or slow to find real CVEs for.

  For synthetic cases, "expected" values were established by running
  the case once against a known-correct implementation and recording
  the result -- this is standard regression-test ground truth: it
  documents the system's INTENDED behavior for a deliberately
  constructed scenario, not independently-sourced real-world fact.
  If a future code change shifts these outputs, that is a signal
  worth investigating, not necessarily a "real" ground truth
  violation the way a real-CVE mismatch would be.

Categories covered (per handoff item 26):
- RELEVANT (positive): exact-version match, version-range match,
  a case matching only a CRITICAL/INTERNAL asset (for later exposure/
  criticality ablation contrast against an INTERNET/HIGH case)
- NOT_RELEVANT (negative): software present, version doesn't match
- UNKNOWN (uncertainty), covering each distinct reason:
  - product not found in inventory at all
  - no affected software identified by NVD
  - software identified but no version information at all
  - version range present but unparseable
  - vendor mismatch (same product name, different vendor)

This dataset is consumed by:
- this file's own run_eval() (validates current behavior against it)
- batch.py-style baseline/metric code in later steps (8-10)
"""

from apis.vulnerabilities import get_vulnerability
from apis.exceptions import (
    InvalidCVEError,
    VulnerabilityAPIError,
    VulnerabilityNotFoundError,
)

from database import initialize_database
from inventory import get_demo_inventory
from memory import get_organization_context

from investigation_engine import build_investigation


# ==========================================================
# Dataset
# ==========================================================

DATASET = [

    # ----------------------------------------------------
    # REAL CASE (anchor): xz-utils backdoor
    # Ground truth: verified against live NVD + manual
    # end-to-end test runs of this system.
    # ----------------------------------------------------
    {
        "id": "real-xz-backdoor",
        "mode": "real",
        "cve_id": "CVE-2024-3094",
        "description": (
            "Real CVE: xz-utils supply-chain backdoor. "
            "Affects web-server-01 (xz-utils 5.6.0)."
        ),
        "expected": {
            "status": "retrieved",
            "organizational_relevance": "RELEVANT",
            "applicability_confidence": 0.95,
            "matched_asset_ids": ["web-server-01"],
            "priority_label": "CRITICAL",
            "priority_score": 90,
        },
    },

    # ----------------------------------------------------
    # SYNTHETIC: RELEVANT via version range, matching two assets
    # ----------------------------------------------------
    {
        "id": "synthetic-range-match-two-assets",
        "mode": "synthetic",
        "vulnerability": {
            "cve_id": "CVE-SYNTH-RANGEMATCH-001",
            "severity": "HIGH",
            "cvss_score": 7.5,
            "cvss_version": "3.1",
            "description": "Synthetic test case",
            "affected_software": ["xz"],
            "affected_versions": [],
            "affected_products": [{
                "product": "xz",
                "vendor": "tukaani",
                "versions": [],
                "version_ranges": [{
                    "start_including": "5.0.0",
                    "start_excluding": None,
                    "end_including": None,
                    "end_excluding": "5.6.2",
                }],
            }],
            "source": "NVD",
        },
        "description": (
            "Synthetic: version range [5.0.0, 5.6.2) covers both "
            "web-server-01 (5.6.0) and database-01 (5.4.1)."
        ),
        "expected": {
            "status": "retrieved",
            "organizational_relevance": "RELEVANT",
            "applicability_confidence": 0.95,
            "matched_asset_ids": ["web-server-01", "database-01"],
            "priority_label": "CRITICAL",
            "priority_score": 88,
        },
    },

    # ----------------------------------------------------
    # SYNTHETIC: RELEVANT, matches only the CRITICAL/INTERNAL asset
    # ----------------------------------------------------
    {
        "id": "synthetic-relevant-critical-internal-only",
        "mode": "synthetic",
        "vulnerability": {
            "cve_id": "CVE-SYNTH-DBONLY-001",
            "severity": "HIGH",
            "cvss_score": 7.5,
            "cvss_version": "3.1",
            "description": "Synthetic test case",
            "affected_software": ["xz"],
            "affected_versions": ["5.4.1"],
            "affected_products": [{
                "product": "xz",
                "vendor": "tukaani",
                "versions": ["5.4.1"],
                "version_ranges": [],
            }],
            "source": "NVD",
        },
        "description": (
            "Synthetic: matches only database-01 (CRITICAL "
            "criticality, INTERNAL exposure) -- contrast case for "
            "criticality/exposure weighting."
        ),
        "expected": {
            "status": "retrieved",
            "organizational_relevance": "RELEVANT",
            "applicability_confidence": 0.95,
            "matched_asset_ids": ["database-01"],
            "priority_label": "HIGH",
            "priority_score": 76,
        },
    },

    # ----------------------------------------------------
    # SYNTHETIC: NOT_RELEVANT (software present, version mismatch)
    # ----------------------------------------------------
    {
        "id": "synthetic-not-relevant-version-mismatch",
        "mode": "synthetic",
        "vulnerability": {
            "cve_id": "CVE-SYNTH-NOTREL-001",
            "severity": "HIGH",
            "cvss_score": 7.5,
            "cvss_version": "3.1",
            "description": "Synthetic test case",
            "affected_software": ["nginx"],
            "affected_versions": ["1.18.0"],
            "affected_products": [{
                "product": "nginx",
                "vendor": "nginx",
                "versions": ["1.18.0"],
                "version_ranges": [],
            }],
            "source": "NVD",
        },
        "description": (
            "Synthetic: nginx is installed (1.24.0) but the "
            "affected version (1.18.0) does not match."
        ),
        "expected": {
            "status": "retrieved",
            "organizational_relevance": "NOT_RELEVANT",
            "applicability_confidence": 0.90,
            "matched_asset_ids": [],
            "priority_label": "LOW",
            "priority_score": 8,
        },
    },

    # ----------------------------------------------------
    # SYNTHETIC: UNKNOWN -- product not in inventory at all
    # ----------------------------------------------------
    {
        "id": "synthetic-unknown-product-not-in-inventory",
        "mode": "synthetic",
        "vulnerability": {
            "cve_id": "CVE-SYNTH-UNKPROD-001",
            "severity": "CRITICAL",
            "cvss_score": 10.0,
            "cvss_version": "3.1",
            "description": "Synthetic test case",
            "affected_software": ["log4j"],
            "affected_versions": ["2.14.0", "2.14.1"],
            "affected_products": [{
                "product": "log4j",
                "vendor": "apache",
                "versions": ["2.14.0", "2.14.1"],
                "version_ranges": [],
            }],
            "source": "NVD",
        },
        "description": (
            "Synthetic: log4j is not in the demo inventory at all."
        ),
        "expected": {
            "status": "retrieved",
            "organizational_relevance": "UNKNOWN",
            "applicability_confidence": 0.50,
            "matched_asset_ids": [],
            "priority_label": "MEDIUM",
            "priority_score": 50,
        },
    },

    # ----------------------------------------------------
    # SYNTHETIC: UNKNOWN -- no affected software identified
    # ----------------------------------------------------
    {
        "id": "synthetic-unknown-no-affected-software",
        "mode": "synthetic",
        "vulnerability": {
            "cve_id": "CVE-SYNTH-NOSOFT-001",
            "severity": "HIGH",
            "cvss_score": 7.0,
            "cvss_version": "3.1",
            "description": "Synthetic test case",
            "affected_software": [],
            "affected_versions": [],
            "affected_products": [],
            "source": "NVD",
        },
        "description": (
            "Synthetic: NVD data did not identify any affected "
            "software product."
        ),
        "expected": {
            "status": "retrieved",
            "organizational_relevance": "UNKNOWN",
            "applicability_confidence": 0.20,
            "matched_asset_ids": [],
            "priority_label": "LOW",
            "priority_score": 20,
        },
    },

    # ----------------------------------------------------
    # SYNTHETIC: UNKNOWN -- software known, no version info
    # ----------------------------------------------------
    {
        "id": "synthetic-unknown-no-version-info",
        "mode": "synthetic",
        "vulnerability": {
            "cve_id": "CVE-SYNTH-NOVER-001",
            "severity": "MEDIUM",
            "cvss_score": 5.5,
            "cvss_version": "3.1",
            "description": "Synthetic test case",
            "affected_software": ["xz"],
            "affected_versions": [],
            "affected_products": [{
                "product": "xz",
                "vendor": "tukaani",
                "versions": [],
                "version_ranges": [],
            }],
            "source": "NVD",
        },
        "description": (
            "Synthetic: affected software is known (xz) but no "
            "version information (exact or range) is available."
        ),
        "expected": {
            "status": "retrieved",
            "organizational_relevance": "UNKNOWN",
            "applicability_confidence": 0.30,
            "matched_asset_ids": [],
            "priority_label": "LOW",
            "priority_score": 28,
        },
    },

    # ----------------------------------------------------
    # SYNTHETIC: UNKNOWN -- unparseable version range boundary
    # ----------------------------------------------------
    {
        "id": "synthetic-unknown-unparseable-range",
        "mode": "synthetic",
        "vulnerability": {
            "cve_id": "CVE-SYNTH-BADRANGE-001",
            "severity": "HIGH",
            "cvss_score": 8.0,
            "cvss_version": "3.1",
            "description": "Synthetic test case",
            "affected_software": ["xz"],
            "affected_versions": [],
            "affected_products": [{
                "product": "xz",
                "vendor": "tukaani",
                "versions": [],
                "version_ranges": [{
                    "start_including": "5.0.0-rc1",
                    "start_excluding": None,
                    "end_including": None,
                    "end_excluding": "5.6.2",
                }],
            }],
            "source": "NVD",
        },
        "description": (
            "Synthetic: xz-utils is installed, but the version "
            "range's start boundary (5.0.0-rc1) cannot be parsed "
            "as a simple dotted-numeric version. Per item 19, this "
            "must resolve to UNKNOWN, never a guessed NOT_RELEVANT "
            "or RELEVANT."
        ),
        "expected": {
            "status": "retrieved",
            "organizational_relevance": "UNKNOWN",
            "applicability_confidence": 0.40,
            "matched_asset_ids": [],
            "priority_label": "MEDIUM",
            "priority_score": 40,
        },
    },

    # ----------------------------------------------------
    # SYNTHETIC: UNKNOWN -- vendor mismatch (Step 3 precision test)
    # ----------------------------------------------------
    {
        "id": "synthetic-unknown-vendor-mismatch",
        "mode": "synthetic",
        "vulnerability": {
            "cve_id": "CVE-SYNTH-VENDORMISMATCH-001",
            "severity": "HIGH",
            "cvss_score": 8.0,
            "cvss_version": "3.1",
            "description": "Synthetic test case",
            "affected_software": ["xz"],
            "affected_versions": ["5.6.0"],
            "affected_products": [{
                "product": "xz",
                "vendor": "someothervendor",
                "versions": ["5.6.0"],
                "version_ranges": [],
            }],
            "source": "NVD",
        },
        "description": (
            "Synthetic: a product also named 'xz', but from a "
            "vendor other than tukaani. Must NOT be normalized to "
            "xz-utils (that would incorrectly borrow the tukaani "
            "alias for an unrelated vendor's product) -- this is "
            "the precision property added in Step 3."
        ),
        "expected": {
            "status": "retrieved",
            "organizational_relevance": "UNKNOWN",
            "applicability_confidence": 0.50,
            "matched_asset_ids": [],
            "priority_label": "MEDIUM",
            "priority_score": 40,
        },
    },
]


# ==========================================================
# Evaluation Runner
# ==========================================================

def _get_investigation_for_case(
    case,
    inventory,
    organization_context,
):
    """
    Produce the actual investigation record for one dataset case.

    Synthetic cases run entirely offline. Real cases require a
    live NVD call; network or lookup failures are reported as
    SKIPPED rather than FAILED, since they reflect an environment
    limitation, not a system defect.
    """

    if case["mode"] == "synthetic":

        return (
            build_investigation(
                vulnerability=case["vulnerability"],
                inventory=inventory,
                organization_context=organization_context,
            ),
            None,
        )

    # mode == "real"

    try:

        vulnerability = get_vulnerability(
            case["cve_id"]
        )

    except (
        InvalidCVEError,
        VulnerabilityNotFoundError,
        VulnerabilityAPIError,
    ) as exc:

        return (
            None,
            f"NVD lookup failed: {exc}",
        )

    return (
        build_investigation(
            vulnerability=vulnerability,
            inventory=inventory,
            organization_context=organization_context,
        ),
        None,
    )


def _check_case(case, investigation):
    """
    Compare an actual investigation against a case's expected
    values. Returns a list of mismatch descriptions (empty list
    means the case passed).
    """

    expected = case["expected"]
    mismatches = []

    if investigation.get("status") != expected["status"]:

        mismatches.append(
            f"status: expected {expected['status']!r}, "
            f"got {investigation.get('status')!r}"
        )

    if (
        investigation.get("organizational_relevance")
        != expected["organizational_relevance"]
    ):

        mismatches.append(
            "organizational_relevance: expected "
            f"{expected['organizational_relevance']!r}, got "
            f"{investigation.get('organizational_relevance')!r}"
        )

    actual_confidence = investigation.get(
        "applicability_confidence"
    )

    if actual_confidence != expected["applicability_confidence"]:

        mismatches.append(
            "applicability_confidence: expected "
            f"{expected['applicability_confidence']!r}, got "
            f"{actual_confidence!r}"
        )

    actual_asset_ids = sorted(
        asset.get("asset_id")
        for asset in investigation.get("matched_assets", [])
    )

    expected_asset_ids = sorted(
        expected["matched_asset_ids"]
    )

    if actual_asset_ids != expected_asset_ids:

        mismatches.append(
            f"matched_asset_ids: expected {expected_asset_ids}, "
            f"got {actual_asset_ids}"
        )

    contextual_priority = investigation.get(
        "contextual_priority",
        {}
    )

    if (
        contextual_priority.get("priority_label")
        != expected["priority_label"]
    ):

        mismatches.append(
            "priority_label: expected "
            f"{expected['priority_label']!r}, got "
            f"{contextual_priority.get('priority_label')!r}"
        )

    if (
        contextual_priority.get("priority_score")
        != expected["priority_score"]
    ):

        mismatches.append(
            "priority_score: expected "
            f"{expected['priority_score']!r}, got "
            f"{contextual_priority.get('priority_score')!r}"
        )

    return mismatches


def run_eval(
    dataset,
    inventory,
    organization_context,
):
    """
    Run every case in the dataset against the current
    build_investigation() implementation and report PASS / FAIL /
    SKIP per case, with a summary at the end.

    This validates that the dataset's frozen expected values still
    match the system's actual behavior -- a regression check for
    the dataset itself, not yet the P/R/F1 metrics computation
    that later steps will build on top of it.
    """

    results = []

    for case in dataset:

        investigation, skip_reason = _get_investigation_for_case(
            case,
            inventory,
            organization_context,
        )

        if skip_reason:

            print(
                f"SKIP  {case['id']}: {skip_reason}"
            )

            results.append(
                ("SKIP", case["id"])
            )

            continue

        mismatches = _check_case(
            case,
            investigation,
        )

        if mismatches:

            print(
                f"FAIL  {case['id']}"
            )

            for mismatch in mismatches:

                print(
                    f"      - {mismatch}"
                )

            results.append(
                ("FAIL", case["id"])
            )

        else:

            print(
                f"PASS  {case['id']}"
            )

            results.append(
                ("PASS", case["id"])
            )

    passed = sum(
        1 for status, _ in results if status == "PASS"
    )

    failed = sum(
        1 for status, _ in results if status == "FAIL"
    )

    skipped = sum(
        1 for status, _ in results if status == "SKIP"
    )

    print()

    print(
        f"{passed} passed, {failed} failed, "
        f"{skipped} skipped (of {len(results)} total)"
    )

    return results


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    initialize_database()

    inventory = get_demo_inventory()

    organization_context = (
        get_organization_context()
    )

    run_eval(
        DATASET,
        inventory,
        organization_context,
    )