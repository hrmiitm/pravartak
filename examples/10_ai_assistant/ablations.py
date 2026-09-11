"""
ablations.py

Ablation study: remove one component of the proposed system at a
time and re-measure against eval_dataset.DATASET, to show which
components actually matter (handoff items 28-31).

Each ablation reuses the REAL, unmodified production code as much
as possible -- either by temporarily disabling one mechanism
(software normalization) or by recomputing only the specific piece
being ablated (priority components) -- rather than maintaining a
second, parallel copy of the whole pipeline that could silently
drift from the real one. The exception is "remove uncertainty
handling", which changes the aggregation decision itself and
therefore needs its own variant of that logic (still calling the
real, unmodified analyze_applicability() underneath).

Two SEPARATE comparisons are reported, because different ablations
affect different things:

1. CLASSIFICATION metrics (precision/recall/F1/FPR/false confidence
   rate) -- affected by: no_organization_context, no_normalization,
   no_uncertainty. NOT affected by no_criticality/no_exposure,
   since those only change the priority SCORE for an already-
   RELEVANT case, never whether it's RELEVANT at all.

2. PRIORITY SCORE impact, over the RELEVANT-ground-truth cases only
   -- affected by: no_organization_context (no score concept
   survives at all), no_criticality, no_exposure. This table exists
   specifically so no_criticality/no_exposure are not misread as
   "having no effect" just because table 1 is blind to them.

Ablations covered:

1. no_organization_context -- reuses baselines.baseline_cvss_only
   directly: no inventory, no applicability analysis, no asset
   context at all.

2. no_normalization -- the real pipeline runs unmodified, except
   applicability.SOFTWARE_ALIASES is temporarily emptied, so
   normalize_software_identity() always falls through to "no
   normalization found" (returns the raw product name unchanged).

3. no_criticality -- real applicability result, but
   contextual_priority is recomputed with the asset-criticality
   component fixed at 0.

4. no_exposure -- same idea, with the exposure component fixed
   at 0 instead.

5. no_uncertainty -- the real per-product analyze_applicability()
   calls are reused unmodified, but the aggregation step that
   normally produces UNKNOWN when evidence is insufficient is
   changed to instead confidently report NOT_RELEVANT. This
   simulates a system with no third "I don't know" state.

6. no_evidence_provenance -- NOT quantitatively ablated. Evidence
   text does not feed into organizational_relevance, matched_assets,
   or contextual_priority at all -- removing it would not change a
   single number this file measures, only whether a human reading
   the output can audit WHY a conclusion was reached. This is
   demonstrated qualitatively instead of faked as a metric.
"""

import contextlib

import applicability
from applicability import analyze_applicability

from investigation_engine import (
    build_investigation,
    calculate_contextual_priority,
    _cvss_component,
    _criticality_component,
    _exposure_component,
)

from baselines import baseline_cvss_only

from metrics import (
    compute_binary_metrics,
    compute_false_confidence_rate,
    _fmt,
)

from eval_dataset import DATASET
from inventory import get_demo_inventory
from memory import get_organization_context
from database import initialize_database
from apis.vulnerabilities import get_vulnerability
from apis.exceptions import (
    InvalidCVEError,
    VulnerabilityAPIError,
    VulnerabilityNotFoundError,
)


VARIANTS = (
    "full",
    "no_organization_context",
    "no_normalization",
    "no_criticality",
    "no_exposure",
    "no_uncertainty",
)

# Ablations that plausibly change priority score for a RELEVANT
# case, worth showing in the priority-impact table.
PRIORITY_RELEVANT_VARIANTS = (
    "full",
    "no_organization_context",
    "no_criticality",
    "no_exposure",
)


# ==========================================================
# Ablation: no organization context
# ==========================================================

def variant_no_organization_context(
    vulnerability,
    inventory,
    organization_context,
):

    result = baseline_cvss_only(
        vulnerability
    )

    return {
        "relevance": result["relevance"],
        "priority_score": result["priority_score"],
        "priority_label": result["priority_label"],
    }


# ==========================================================
# Ablation: no software normalization
# ==========================================================

@contextlib.contextmanager
def _normalization_disabled():
    """
    Temporarily empties applicability.SOFTWARE_ALIASES, so
    normalize_software_identity() cannot map any product name to
    an inventory identity -- it always falls through to
    returning the raw name unchanged. Restores the real alias
    table afterward, regardless of exceptions.
    """

    original_aliases = applicability.SOFTWARE_ALIASES

    applicability.SOFTWARE_ALIASES = {}

    try:

        yield

    finally:

        applicability.SOFTWARE_ALIASES = original_aliases


def variant_no_normalization(
    vulnerability,
    inventory,
    organization_context,
):

    with _normalization_disabled():

        investigation = build_investigation(
            vulnerability=vulnerability,
            inventory=inventory,
            organization_context=organization_context,
        )

    contextual_priority = investigation.get(
        "contextual_priority",
        {}
    )

    return {
        "relevance": investigation[
            "organizational_relevance"
        ],
        "priority_score": contextual_priority.get(
            "priority_score"
        ),
        "priority_label": contextual_priority.get(
            "priority_label"
        ),
    }


# ==========================================================
# Ablations: no criticality / no exposure component
# ==========================================================

def _recompute_priority_ablated(
    investigation,
    skip_criticality=False,
    skip_exposure=False,
):
    """
    Recompute contextual priority from an existing (real)
    investigation result, with one scoring component fixed at 0.
    Relevance classification and matched assets are unchanged --
    only the priority formula is ablated.
    """

    severity = investigation.get("severity")
    cvss_score = investigation.get("cvss_score")
    organizational_relevance = investigation.get(
        "organizational_relevance"
    )
    applicability_confidence = investigation.get(
        "applicability_confidence"
    )
    matched_assets = investigation.get(
        "matched_assets",
        []
    )

    cvss_points = _cvss_component(
        severity,
        cvss_score,
    )

    if organizational_relevance == "RELEVANT":

        criticality_points = (
            0
            if skip_criticality
            else _criticality_component(matched_assets)
        )

        exposure_points = (
            0
            if skip_exposure
            else _exposure_component(matched_assets)
        )

        raw_score = (
            cvss_points
            + criticality_points
            + exposure_points
        )

    elif organizational_relevance == "UNKNOWN":

        raw_score = cvss_points

    else:

        raw_score = cvss_points * 0.2

    confidence = (
        applicability_confidence
        if applicability_confidence is not None
        else 0.0
    )

    final_score = max(
        0,
        round(
            min(
                raw_score,
                confidence * 100,
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

    return final_score, label


def variant_no_criticality(
    vulnerability,
    inventory,
    organization_context,
):

    investigation = build_investigation(
        vulnerability=vulnerability,
        inventory=inventory,
        organization_context=organization_context,
    )

    score, label = _recompute_priority_ablated(
        investigation,
        skip_criticality=True,
    )

    return {
        "relevance": investigation[
            "organizational_relevance"
        ],
        "priority_score": score,
        "priority_label": label,
    }


def variant_no_exposure(
    vulnerability,
    inventory,
    organization_context,
):

    investigation = build_investigation(
        vulnerability=vulnerability,
        inventory=inventory,
        organization_context=organization_context,
    )

    score, label = _recompute_priority_ablated(
        investigation,
        skip_exposure=True,
    )

    return {
        "relevance": investigation[
            "organizational_relevance"
        ],
        "priority_score": score,
        "priority_label": label,
    }


# ==========================================================
# Ablation: no uncertainty handling
# ==========================================================

def _build_no_uncertainty(
    vulnerability,
    inventory,
    organization_context,
):
    """
    Same per-product applicability analysis as the real pipeline
    (analyze_applicability is called exactly as in
    investigation_engine.build_investigation), but the
    aggregation step collapses UNKNOWN into NOT_RELEVANT: a
    system with no third "insufficient evidence" state has to
    force every non-RELEVANT case into a confident negative.
    """

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

    description = vulnerability.get(
        "description"
    )

    cve_id = vulnerability.get(
        "cve_id"
    )

    affected_products_by_name = {
        product.get("product"): product
        for product in affected_products
    }

    applicability_results = []

    for software in affected_software:

        product_entry = affected_products_by_name.get(
            software,
            {}
        )

        result = analyze_applicability(
            cve_id=cve_id,
            description=description or "",
            affected_software=software,
            affected_versions=affected_versions,
            version_ranges=product_entry.get(
                "version_ranges",
                []
            ),
            vendor=product_entry.get("vendor"),
            inventory=inventory,
            organization_context=organization_context,
        )

        applicability_results.append(result)

    relevant_results = [
        r for r in applicability_results
        if r.get("status") == "RELEVANT"
    ]

    if relevant_results:

        status = "RELEVANT"

        matched_assets = [
            asset
            for r in relevant_results
            for asset in r.get("matched_assets", [])
        ]

        confidence = max(
            r.get("confidence", 0.0)
            for r in relevant_results
        )

    else:

        # No third state: anything short of a confirmed match
        # is reported as confidently NOT_RELEVANT, whether the
        # real reason was "confirmed absent" or merely
        # "insufficient evidence."

        status = "NOT_RELEVANT"

        matched_assets = []

        confidence = max(
            (r.get("confidence", 0.0) for r in applicability_results),
            default=0.90,
        )

    return {
        "severity": vulnerability.get("severity"),
        "cvss_score": vulnerability.get("cvss_score"),
        "organizational_relevance": status,
        "applicability_confidence": confidence,
        "matched_assets": matched_assets,
    }


def variant_no_uncertainty(
    vulnerability,
    inventory,
    organization_context,
):

    ablated = _build_no_uncertainty(
        vulnerability,
        inventory,
        organization_context,
    )

    # Priority is computed with the REAL, unmodified formula,
    # fed the ablated (collapsed) relevance label -- isolating
    # the aggregation change from the priority formula itself.
    contextual_priority = calculate_contextual_priority(
        severity=ablated["severity"],
        cvss_score=ablated["cvss_score"],
        organizational_relevance=ablated[
            "organizational_relevance"
        ],
        applicability_confidence=ablated[
            "applicability_confidence"
        ],
        matched_assets=ablated["matched_assets"],
    )

    return {
        "relevance": ablated["organizational_relevance"],
        "priority_score": contextual_priority["priority_score"],
        "priority_label": contextual_priority["priority_label"],
    }


# ==========================================================
# "Full" variant (reference, not ablated)
# ==========================================================

def variant_full(
    vulnerability,
    inventory,
    organization_context,
):

    investigation = build_investigation(
        vulnerability=vulnerability,
        inventory=inventory,
        organization_context=organization_context,
    )

    contextual_priority = investigation.get(
        "contextual_priority",
        {}
    )

    return {
        "relevance": investigation[
            "organizational_relevance"
        ],
        "priority_score": contextual_priority.get(
            "priority_score"
        ),
        "priority_label": contextual_priority.get(
            "priority_label"
        ),
    }


VARIANT_FUNCTIONS = {
    "full": variant_full,
    "no_organization_context": variant_no_organization_context,
    "no_normalization": variant_no_normalization,
    "no_criticality": variant_no_criticality,
    "no_exposure": variant_no_exposure,
    "no_uncertainty": variant_no_uncertainty,
}


# ==========================================================
# Qualitative demonstration: no evidence provenance
# ==========================================================

def demonstrate_evidence_removal(
    vulnerability,
    inventory,
    organization_context,
):
    """
    Not a metric -- prints what the investigation looks like
    with evidence/provenance fields stripped, to demonstrate
    (qualitatively) that the CONCLUSION is unchanged but is no
    longer auditable.
    """

    investigation = build_investigation(
        vulnerability=vulnerability,
        inventory=inventory,
        organization_context=organization_context,
    )

    print(
        "With evidence provenance:  "
        f"{investigation['organizational_relevance']} -- "
        f"{investigation['relevance_reason']}"
    )

    print(
        "Without evidence provenance: "
        f"{investigation['organizational_relevance']} -- "
        "(no reason given; conclusion cannot be audited)"
    )


# ==========================================================
# Runner
# ==========================================================

def _collect_ablation_records(dataset):

    inventory = get_demo_inventory()
    organization_context = get_organization_context()

    records = []

    for case in dataset:

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
            ):

                continue

        outcomes = {
            variant_name: variant_fn(
                vulnerability,
                inventory,
                organization_context,
            )
            for variant_name, variant_fn in VARIANT_FUNCTIONS.items()
        }

        records.append({
            "case_id": case["id"],
            "ground_truth": (
                case["expected"]["organizational_relevance"]
            ),
            # Plain relevance strings, for reuse with
            # metrics.py's classification functions unchanged.
            "predictions": {
                variant_name: outcome["relevance"]
                for variant_name, outcome in outcomes.items()
            },
            # Full per-variant outcome (relevance + priority),
            # for the priority-impact table below.
            "outcomes": outcomes,
        })

    return records


def print_classification_table(records):

    n_binary = sum(
        1
        for r in records
        if r["ground_truth"] in ("RELEVANT", "NOT_RELEVANT")
    )

    n_uncertain = sum(
        1
        for r in records
        if r["ground_truth"] == "UNKNOWN"
    )

    print(
        f"Evaluated {len(records)} case(s): "
        f"{n_binary} RELEVANT/NOT_RELEVANT, "
        f"{n_uncertain} UNKNOWN ground truth.\n"
    )

    print("Classification metrics:\n")

    print(
        f"{'Variant':<28}{'Precision':<11}{'Recall':<9}"
        f"{'F1':<7}{'FPR':<7}{'FalseConf':<10}"
    )
    print("-" * 72)

    for variant in VARIANTS:

        binary = compute_binary_metrics(
            records,
            variant,
        )

        false_conf = compute_false_confidence_rate(
            records,
            variant,
        )

        print(
            f"{variant:<28}"
            f"{_fmt(binary['precision']):<11}"
            f"{_fmt(binary['recall']):<9}"
            f"{_fmt(binary['f1']):<7}"
            f"{_fmt(binary['fpr']):<7}"
            f"{_fmt(false_conf):<10}"
        )


def print_priority_impact_table(records):

    print(
        "\nPriority score impact (RELEVANT-ground-truth cases "
        "only -- this is where no_criticality/no_exposure "
        "actually show an effect, since they never change "
        "RELEVANT/NOT_RELEVANT classification, only the score):\n"
    )

    relevant_records = [
        r for r in records
        if r["ground_truth"] == "RELEVANT"
    ]

    if not relevant_records:

        print(
            "No RELEVANT-ground-truth cases available "
            "(likely running offline without the real CVE case)."
        )

        return

    header = f"{'Case':<32}"

    for variant in PRIORITY_RELEVANT_VARIANTS:
        header += f"{variant:<22}"

    print(header)
    print("-" * len(header))

    for record in relevant_records:

        row = f"{record['case_id']:<32}"

        for variant in PRIORITY_RELEVANT_VARIANTS:

            outcome = record["outcomes"][variant]

            score = outcome["priority_score"]
            label = outcome["priority_label"]

            cell = (
                f"{label} ({score})"
                if score is not None
                else "N/A"
            )

            row += f"{cell:<22}"

        print(row)


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    initialize_database()

    records = _collect_ablation_records(
        DATASET
    )

    print_classification_table(
        records
    )

    print_priority_impact_table(
        records
    )

    print(
        "\n(no_evidence_provenance is not included above -- it "
        "does not change any of these numbers. See "
        "demonstrate_evidence_removal() below.)"
    )

    print(
        "\n--- Evidence provenance demonstration "
        "(CVE-2024-3094) ---"
    )

    inventory = get_demo_inventory()
    organization_context = get_organization_context()

    try:

        vulnerability = get_vulnerability(
            "CVE-2024-3094"
        )

        demonstrate_evidence_removal(
            vulnerability,
            inventory,
            organization_context,
        )

    except (
        InvalidCVEError,
        VulnerabilityNotFoundError,
        VulnerabilityAPIError,
    ) as exc:

        print(
            f"SKIPPED: NVD lookup failed: {exc}"
        )