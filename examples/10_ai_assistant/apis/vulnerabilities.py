"""
vulnerabilities.py

Cybersecurity vulnerability intelligence service.

This module is responsible only for communicating with the
external vulnerability database. No LangChain code belongs here.
"""

import re
import time

import httpx
import settings

from apis.exceptions import (
    InvalidCVEError,
    VulnerabilityAPIError,
    VulnerabilityNotFoundError,
)


# ==========================================================
# API Configuration
# ==========================================================

NVD_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

CVE_PATTERN = re.compile(
    r"^CVE-\d{4}-\d{4,}$",
    re.IGNORECASE,
)


# ==========================================================
# HTTP Client
# ==========================================================

client = httpx.Client(
    timeout=10,
    headers={
        "User-Agent": "LangGraph-Cybersecurity-Assistant/1.0"
    },
)


# ==========================================================
# CVE Validation
# ==========================================================

def validate_cve_id(cve_id: str) -> str:
    """
    Validate and normalize a CVE identifier.

    Example:
        cve-2024-3094 → CVE-2024-3094
    """

    cve_id = cve_id.strip().upper()

    if not CVE_PATTERN.fullmatch(cve_id):
        raise InvalidCVEError(
            f"Invalid CVE identifier: {cve_id}"
        )

    return cve_id


# ==========================================================
# CVE Lookup
# ==========================================================

def get_vulnerability(cve_id: str):
    """
    Retrieve vulnerability information for a CVE identifier.

    Returns a structured dictionary containing the most
    useful information for the agent.
    """

    cve_id = validate_cve_id(cve_id)

    if settings.LEARN_MODE:
        print("\n🔐 Calling NVD vulnerability API...")

    start = time.perf_counter()

    try:

        response = client.get(
            NVD_CVE_URL,
            params={
                "cveId": cve_id,
            },
        )

        response.raise_for_status()

    except httpx.HTTPError as exc:

        raise VulnerabilityAPIError(
            f"Unable to query vulnerability database: {exc}"
        ) from exc

    end = time.perf_counter()

    if settings.LEARN_MODE:
        print(
            f"⏱ NVD API Time : "
            f"{end - start:.3f} sec"
        )

    data = response.json()

    vulnerabilities = data.get("vulnerabilities", [])

    if not vulnerabilities:
        raise VulnerabilityNotFoundError(
            f"No vulnerability found for {cve_id}."
        )

    cve = vulnerabilities[0].get("cve", {})

    descriptions = cve.get("descriptions", [])

    description = next(
        (
            item["value"]
            for item in descriptions
            if item.get("lang") == "en"
        ),
        "No English description available.",
    )

    metrics = cve.get("metrics", {})

    cvss_score = None
    severity = None

    # Prefer CVSS v3.1
    if metrics.get("cvssMetricV31"):

        metric = metrics["cvssMetricV31"][0]

        cvss_data = metric.get("cvssData", {})

        cvss_score = cvss_data.get("baseScore")
        severity = cvss_data.get("baseSeverity")

    # Fall back to CVSS v3.0
    elif metrics.get("cvssMetricV30"):

        metric = metrics["cvssMetricV30"][0]

        cvss_data = metric.get("cvssData", {})

        cvss_score = cvss_data.get("baseScore")
        severity = cvss_data.get("baseSeverity")

    return {
        "cve_id": cve.get("id", cve_id),
        "description": description,
        "cvss_score": cvss_score,
        "severity": severity,
        "published": cve.get("published"),
        "last_modified": cve.get("lastModified"),
    }