"""
batch.py

Batch vulnerability analysis: run the same deterministic
investigation pipeline used by the interactive assistant across
multiple CVEs, with no LLM and no LangGraph involved, and produce
a ranked, prioritized output.

This exists to support research evaluation (comparing results
across many CVEs, computing metrics, running ablations) rather
than one-off interactive lookups -- see handoff items 24-25.

Run:
    python batch.py [cve_list_file]

cve_list_file (optional): a plain text file with one CVE ID per
line. Blank lines and lines starting with "#" are ignored. If
omitted, or if the file cannot be read, a small built-in demo
list of well-known CVEs is used instead.

Output:
    - A ranked table printed to the console (highest contextual
      priority first).
    - A CSV file, batch_results.csv, written alongside this
      script, with one row per CVE.
"""

import csv
import sys
import time
from pathlib import Path

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
# Demo CVE list (used when no input file is given)
# ==========================================================

DEMO_CVE_IDS = [
    "CVE-2024-3094",   # xz-utils backdoor (matches demo inventory)
    "CVE-2021-44228",  # Log4Shell
    "CVE-2023-4863",   # WebP heap buffer overflow
]

OUTPUT_CSV_PATH = (
    Path(__file__).parent / "batch_results.csv"
)


# ==========================================================
# CVE List Loading
# ==========================================================

def load_cve_ids(path_arg):
    """
    Load CVE IDs from a plain text file (one per line, "#"
    comments and blank lines ignored). Falls back to
    DEMO_CVE_IDS when no path is given or the file cannot be
    read.
    """

    if not path_arg:

        print(
            "No input file given -- using the built-in demo "
            f"CVE list ({len(DEMO_CVE_IDS)} CVEs)."
        )

        return list(DEMO_CVE_IDS)

    path = Path(path_arg)

    if not path.is_file():

        print(
            f"Input file '{path_arg}' not found -- falling "
            f"back to the built-in demo CVE list "
            f"({len(DEMO_CVE_IDS)} CVEs)."
        )

        return list(DEMO_CVE_IDS)

    cve_ids = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:

        for line in f:

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            cve_ids.append(line)

    if not cve_ids:

        print(
            f"Input file '{path_arg}' contained no CVE IDs -- "
            f"falling back to the built-in demo CVE list "
            f"({len(DEMO_CVE_IDS)} CVEs)."
        )

        return list(DEMO_CVE_IDS)

    print(
        f"Loaded {len(cve_ids)} CVE ID(s) from '{path_arg}'."
    )

    return cve_ids


# ==========================================================
# Per-CVE Investigation (batch path)
# ==========================================================

def investigate_cve_batch(
    cve_id,
    inventory,
    organization_context,
):
    """
    Retrieve and analyze a single CVE for batch processing.

    Unlike the interactive path, this calls the NVD API
    directly -- there is no LLM, no tool call, and no
    LangGraph state involved. The resulting record is built
    by the same investigation_engine.build_investigation()
    used by the interactive path, so results are directly
    comparable between the two.

    On failure (invalid CVE ID, not found, or an API error),
    returns a minimal record carrying the error, in a shape
    consistent with the interactive path's error branches.
    """

    try:

        vulnerability = get_vulnerability(
            cve_id
        )

    except InvalidCVEError as exc:

        return {
            "cve_id": cve_id,
            "status": "invalid_cve",
            "error": str(exc),
        }

    except VulnerabilityNotFoundError as exc:

        return {
            "cve_id": cve_id,
            "status": "not_found",
            "error": str(exc),
        }

    except VulnerabilityAPIError as exc:

        return {
            "cve_id": cve_id,
            "status": "failed",
            "error": str(exc),
        }

    return build_investigation(
        vulnerability=vulnerability,
        inventory=inventory,
        organization_context=organization_context,
    )


def investigate_cves(
    cve_ids,
    inventory,
    organization_context,
):
    """
    Run investigate_cve_batch() across a list of CVE IDs,
    printing brief progress as it goes.
    """

    investigations = []

    for index, cve_id in enumerate(
        cve_ids,
        start=1,
    ):

        print(
            f"[{index}/{len(cve_ids)}] "
            f"Investigating {cve_id}..."
        )

        investigation = investigate_cve_batch(
            cve_id,
            inventory,
            organization_context,
        )

        investigations.append(
            investigation
        )

        # Be polite to the NVD API across a batch run.
        time.sleep(0.5)

    return investigations


# ==========================================================
# Ranked Table Output
# ==========================================================

def _matched_assets_summary(investigation):

    matched_assets = investigation.get(
        "matched_assets",
        []
    )

    if not matched_assets:
        return "-"

    first = matched_assets[0]

    summary = first.get(
        "asset_id",
        "?"
    )

    if len(matched_assets) > 1:

        summary += (
            f" (+{len(matched_assets) - 1} more)"
        )

    return summary


def build_ranked_rows(investigations):
    """
    Build display/CSV rows from a list of investigation
    records, sorted by contextual priority score (highest
    first). Failed/invalid/not_found records sort last.
    """

    rows = []

    for investigation in investigations:

        status = investigation.get(
            "status",
            "unknown"
        )

        if status != "retrieved":

            rows.append({
                "cve_id": investigation.get(
                    "cve_id",
                    "?"
                ),
                "severity": "N/A",
                "cvss_score": "N/A",
                "organizational_relevance": "N/A",
                "matched_assets": "-",
                "priority_score": -1,
                "priority_label": status.upper(),
                "status": status,
            })

            continue

        contextual_priority = investigation.get(
            "contextual_priority",
            {}
        )

        rows.append({
            "cve_id": investigation.get(
                "cve_id",
                "?"
            ),
            "severity": investigation.get(
                "severity"
            ) or "UNKNOWN",
            "cvss_score": investigation.get(
                "cvss_score"
            ),
            "organizational_relevance": investigation.get(
                "organizational_relevance",
                "UNKNOWN"
            ),
            "matched_assets": _matched_assets_summary(
                investigation
            ),
            "priority_score": contextual_priority.get(
                "priority_score",
                -1
            ),
            "priority_label": contextual_priority.get(
                "priority_label",
                "N/A"
            ),
            "status": status,
        })

    rows.sort(
        key=lambda row: row["priority_score"],
        reverse=True,
    )

    return rows


def print_ranked_table(rows):

    print()
    print(
        f"{'CVE':<18}{'Severity':<10}{'Relevant':<14}"
        f"{'Asset':<20}{'Priority':<18}"
    )
    print("-" * 80)

    for row in rows:

        priority_display = (
            f"{row['priority_label']} "
            f"({row['priority_score']}/100)"
            if row["priority_score"] >= 0
            else row["priority_label"]
        )

        print(
            f"{row['cve_id']:<18}"
            f"{str(row['severity']):<10}"
            f"{str(row['organizational_relevance']):<14}"
            f"{row['matched_assets']:<20}"
            f"{priority_display:<18}"
        )

    print("-" * 80)


def write_csv(rows, path):

    fieldnames = [
        "cve_id",
        "severity",
        "cvss_score",
        "organizational_relevance",
        "matched_assets",
        "priority_score",
        "priority_label",
        "status",
    ]

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:

            writer.writerow(
                {
                    key: row.get(key, "")
                    for key in fieldnames
                }
            )

    print(
        f"\nWrote {len(rows)} row(s) to {path}"
    )


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    initialize_database()

    input_arg = (
        sys.argv[1]
        if len(sys.argv) > 1
        else None
    )

    cve_ids = load_cve_ids(
        input_arg
    )

    inventory = get_demo_inventory()

    organization_context = (
        get_organization_context()
    )

    print()

    investigations = investigate_cves(
        cve_ids,
        inventory,
        organization_context,
    )

    rows = build_ranked_rows(
        investigations
    )

    print_ranked_table(
        rows
    )

    write_csv(
        rows,
        OUTPUT_CSV_PATH,
    )