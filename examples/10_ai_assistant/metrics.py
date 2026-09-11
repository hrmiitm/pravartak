"""
metrics.py

Compute classification metrics for each approach (the three
baselines plus the proposed system) against eval_dataset.DATASET's
ground truth (handoff items 26-27).

Two separate metrics are computed, deliberately kept apart rather
than folded into one number, because they measure different
things:

1. BINARY RELEVANCE METRICS (precision, recall, F1, false positive
   rate, false negative rate)

   Computed only over dataset cases whose ground truth is
   confidently RELEVANT or NOT_RELEVANT (i.e., excluding cases
   where the correct answer is genuine uncertainty -- see below
   for why). A prediction is "positive" if the approach reports
   RELEVANT/MATCH, and "negative" otherwise (NOT_RELEVANT,
   NO_MATCH, or UNKNOWN -- an abstention is treated as not
   claiming relevance, so it can still count as a true negative,
   but never as a true positive).

2. FALSE CONFIDENCE RATE (on cases where ground truth is UNKNOWN)

   The fraction of genuinely-uncertain cases where an approach
   nonetheless produced a confident RELEVANT/MATCH or
   NOT_RELEVANT/NO_MATCH answer instead of expressing
   uncertainty. This is scored separately from (1) because mixing
   it into standard binary metrics would hide the single most
   important property this whole project is built around (item
   12): whether a system can tell the difference between "we
   checked and it's not relevant" and "we don't have enough
   evidence to say." A system that always guesses will look fine
   on binary accuracy while being unsafe in exactly the cases that
   matter most.

   The three baselines have no "UNKNOWN" output option at all --
   they always produce a definite match/no-match. Their false
   confidence rate on this axis is therefore 100% by construction,
   which is itself the finding: only the proposed system can
   express calibrated uncertainty.

CAVEAT: eval_dataset.DATASET has 9 cases (4 RELEVANT/NOT_RELEVANT,
5 UNKNOWN). This is far too small for statistically meaningful
confidence intervals -- these numbers are illustrative of the
METHODOLOGY, not a publishable accuracy claim. A real evaluation
needs a much larger real-CVE dataset (handoff item 26/31
acknowledges this is future work). Ranking-quality metrics (e.g.
rank correlation) are not computed here for the same reason: with
only 9 cases and several sharing predicted labels, a correlation
coefficient here would not be meaningful.
"""

from baselines import compare_all
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


APPROACHES = (
    "cvss_only",
    "cvss_keyword",
    "cvss_context",
    "proposed",
)

# Values that count as a confident "this applies" claim, per
# approach's own vocabulary.
_POSITIVE_VALUES = {"RELEVANT", "MATCH"}

# Values that count as a confident "this does not apply" claim.
_NEGATIVE_VALUES = {"NOT_RELEVANT", "NO_MATCH"}

# Values that count as an abstention / expression of uncertainty.
_UNCERTAIN_VALUES = {"UNKNOWN", "N/A (not modeled)"}


def _collect_predictions(dataset):
    """
    Run every approach against every dataset case, pairing each
    prediction with its ground truth. Cases requiring a live NVD
    call that fails are skipped (not scored as wrong).
    """

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

        results = compare_all(
            vulnerability,
            inventory,
            organization_context,
        )

        records.append({
            "case_id": case["id"],
            "ground_truth": (
                case["expected"]["organizational_relevance"]
            ),
            "predictions": {
                approach: results[approach]["relevance"]
                for approach in APPROACHES
            },
        })

    return records


def _classify(prediction_value):
    """
    Map an approach-specific relevance string to one of
    "positive", "negative", "uncertain".
    """

    if prediction_value in _POSITIVE_VALUES:
        return "positive"

    if prediction_value in _NEGATIVE_VALUES:
        return "negative"

    return "uncertain"


def compute_binary_metrics(records, approach):
    """
    Precision, recall, F1, FPR, FNR for one approach, over only
    the cases whose ground truth is RELEVANT or NOT_RELEVANT.
    """

    tp = fp = fn = tn = 0

    for record in records:

        ground_truth = record["ground_truth"]

        if ground_truth not in (
            "RELEVANT",
            "NOT_RELEVANT",
        ):

            continue

        predicted_class = _classify(
            record["predictions"][approach]
        )

        predicted_positive = (
            predicted_class == "positive"
        )

        if ground_truth == "RELEVANT":

            if predicted_positive:
                tp += 1
            else:
                fn += 1

        else:

            if predicted_positive:
                fp += 1
            else:
                tn += 1

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else None
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else None
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None
        and recall is not None
        and (precision + recall) > 0
        else None
    )

    fpr = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else None
    )

    fnr = (
        fn / (fn + tp)
        if (fn + tp) > 0
        else None
    )

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "fnr": fnr,
    }


def compute_false_confidence_rate(records, approach):
    """
    Fraction of ground-truth-UNKNOWN cases where the approach
    gave a confident positive or negative answer instead of
    expressing uncertainty.
    """

    uncertain_cases = [
        record
        for record in records
        if record["ground_truth"] == "UNKNOWN"
    ]

    if not uncertain_cases:
        return None

    falsely_confident = sum(
        1
        for record in uncertain_cases
        if _classify(
            record["predictions"][approach]
        ) != "uncertain"
    )

    return falsely_confident / len(uncertain_cases)


def _fmt(value):

    if value is None:
        return "N/A"

    return f"{value:.2f}"


def print_metrics_report(records):

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
        f"{n_binary} with RELEVANT/NOT_RELEVANT ground truth, "
        f"{n_uncertain} with UNKNOWN ground truth."
    )

    print(
        "\nBinary relevance metrics "
        f"(over the {n_binary} RELEVANT/NOT_RELEVANT cases):"
    )

    print(
        f"\n{'Approach':<15}{'Precision':<11}{'Recall':<9}"
        f"{'F1':<7}{'FPR':<7}{'FNR':<7}"
    )
    print("-" * 56)

    for approach in APPROACHES:

        metrics = compute_binary_metrics(
            records,
            approach,
        )

        print(
            f"{approach:<15}"
            f"{_fmt(metrics['precision']):<11}"
            f"{_fmt(metrics['recall']):<9}"
            f"{_fmt(metrics['f1']):<7}"
            f"{_fmt(metrics['fpr']):<7}"
            f"{_fmt(metrics['fnr']):<7}"
        )

    print(
        f"\nFalse confidence rate "
        f"(over the {n_uncertain} UNKNOWN-ground-truth cases -- "
        f"lower is better; this measures how often an approach "
        f"guesses instead of expressing uncertainty):"
    )

    print(
        f"\n{'Approach':<15}{'False Confidence Rate':<25}"
    )
    print("-" * 40)

    for approach in APPROACHES:

        rate = compute_false_confidence_rate(
            records,
            approach,
        )

        print(
            f"{approach:<15}{_fmt(rate):<25}"
        )


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    initialize_database()

    records = _collect_predictions(
        DATASET
    )

    print_metrics_report(
        records
    )