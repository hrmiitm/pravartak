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
# Affected Software Extraction
# ==========================================================

def extract_affected_software(cve: dict) -> dict:
    """
    Extract affected software and version information from
    NVD CPE configuration data.

    NVD configurations may contain nested logical nodes.
    This function recursively traverses those nodes.

    Returns:

        {
            "affected_software": [...],
            "affected_versions": [...],
            "affected_products": [
                {
                    "product": "xz",
                    "vendor": "xz_project",
                    "versions": ["5.6.0", "5.6.1"],
                    "version_ranges": [
                        {
                            "start_including": "5.0.0",
                            "start_excluding": None,
                            "end_including": None,
                            "end_excluding": "5.6.2",
                        },
                        ...
                    ],
                },
                ...
            ]
        }

    "affected_software" and "affected_versions" are preserved
    exactly as before for backward compatibility with existing
    callers (tools.py, applicability.py, state.py).

    "affected_products" is a new, additive field. It keeps
    exact versions and version-range boundaries separated and
    tied to the specific product they apply to, which flat
    "affected_versions" cannot represent. It is not yet
    consumed anywhere downstream — this function only
    produces it.

    The extraction is conservative and only uses information
    explicitly present in NVD configuration data.
    """

    affected_software = set()
    affected_versions = set()

    # product -> { "vendor": str, "versions": set(), "ranges": [ {...}, ... ] }
    products: dict = {}

    def get_product_entry(product: str, vendor: str = None) -> dict:

        if product not in products:

            products[product] = {
                "vendor": vendor,
                "versions": set(),
                "ranges": [],
            }

        elif vendor and not products[product].get("vendor"):

            # Fill in vendor if an earlier entry for this
            # product was created without one.
            products[product]["vendor"] = vendor

        return products[product]

    # ------------------------------------------------------
    # Recursive NVD node processor
    # ------------------------------------------------------

    def process_node(node: dict):
        """
        Recursively process an NVD configuration node.
        """

        # --------------------------------------------------
        # Process CPE matches at this node
        # --------------------------------------------------

        for cpe_match in node.get(
            "cpeMatch",
            []
        ):

            # Only use CPE entries explicitly marked
            # as vulnerable.
            if not cpe_match.get(
                "vulnerable",
                False
            ):
                continue

            cpe_uri = cpe_match.get(
                "criteria"
            )

            if not cpe_uri:
                continue

            # --------------------------------------------------
            # Parse CPE 2.3
            #
            # Example:
            #
            # cpe:2.3:a:xz:xz:5.6.0:*:*:*:*:*:*:*
            #
            # Index:
            # 0 = cpe
            # 1 = 2.3
            # 2 = part
            # 3 = vendor
            # 4 = product
            # 5 = version
            # --------------------------------------------------

            parts = cpe_uri.split(":")

            product = None
            version = None

            if len(parts) >= 6:

                vendor = parts[3]
                product = parts[4]
                version = parts[5]

                # Keep the product as the software identifier.
                if product and product != "*":

                    affected_software.add(
                        product
                    )

                # Add exact version when explicitly available.
                if version and version != "*":

                    affected_versions.add(
                        version
                    )

            # --------------------------------------------------
            # Version range boundaries (legacy flat set —
            # unchanged from previous behavior)
            # --------------------------------------------------

            start_including = cpe_match.get(
                "versionStartIncluding"
            )
            end_including = cpe_match.get(
                "versionEndIncluding"
            )
            start_excluding = cpe_match.get(
                "versionStartExcluding"
            )
            end_excluding = cpe_match.get(
                "versionEndExcluding"
            )

            version_constraints = [
                start_including,
                end_including,
                start_excluding,
                end_excluding,
            ]

            for constrained_version in version_constraints:

                if constrained_version:

                    affected_versions.add(
                        constrained_version
                    )

            # --------------------------------------------------
            # Structured per-product data (new, additive)
            # --------------------------------------------------

            if product and product != "*":

                entry = get_product_entry(
                    product,
                    vendor if vendor and vendor != "*" else None,
                )

                if version and version != "*":

                    entry["versions"].add(
                        version
                    )

                has_range = any(
                    version_constraints
                )

                if has_range:

                    entry["ranges"].append({
                        "start_including": start_including,
                        "start_excluding": start_excluding,
                        "end_including": end_including,
                        "end_excluding": end_excluding,
                    })

        # --------------------------------------------------
        # Recursively process nested children
        # --------------------------------------------------

        for child_node in node.get(
            "children",
            []
        ):

            process_node(
                child_node
            )

    # ------------------------------------------------------
    # Process every top-level configuration
    # ------------------------------------------------------

    configurations = cve.get(
        "configurations",
        []
    )

    for configuration in configurations:

        for node in configuration.get(
            "nodes",
            []
        ):

            process_node(
                node
            )

    # ------------------------------------------------------
    # Build structured affected_products list
    # ------------------------------------------------------

    affected_products = [
        {
            "product": product,
            "vendor": entry.get("vendor"),
            "versions": sorted(
                entry["versions"]
            ),
            "version_ranges": entry["ranges"],
        }
        for product, entry in products.items()
    ]

    return {
        "affected_software": sorted(
            affected_software
        ),
        "affected_versions": sorted(
            affected_versions
        ),
        "affected_products": affected_products,
    }


# ==========================================================
# CVE Lookup
# ==========================================================

def get_vulnerability(cve_id: str):
    """
    Retrieve vulnerability information for a CVE identifier.

    Returns a structured dictionary containing:

    - CVE identifier
    - description
    - CVSS score
    - CVSS version
    - severity
    - publication metadata
    - affected software
    - affected versions
    - affected products (structured, per-product, additive)
    """

    # ======================================================
    # Validate CVE
    # ======================================================

    cve_id = validate_cve_id(
        cve_id
    )

    if settings.LEARN_MODE:

        print(
            "\n🔐 Calling NVD vulnerability API..."
        )

    start = time.perf_counter()

    # ======================================================
    # NVD API Request
    # ======================================================

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

    # ======================================================
    # Parse API Response
    # ======================================================

    data = response.json()

    vulnerabilities = data.get(
        "vulnerabilities",
        []
    )

    if not vulnerabilities:

        raise VulnerabilityNotFoundError(
            f"No vulnerability found for {cve_id}."
        )

    cve = vulnerabilities[0].get(
        "cve",
        {}
    )

    # ======================================================
    # Description
    # ======================================================

    descriptions = cve.get(
        "descriptions",
        []
    )

    description = next(
        (
            item.get("value")
            for item in descriptions
            if item.get("lang") == "en"
        ),
        "No English description available.",
    )

    # ======================================================
    # CVSS Metrics
    # ======================================================

    metrics = cve.get(
        "metrics",
        {}
    )

    cvss_score = None
    severity = None
    cvss_version = None

    if settings.LEARN_MODE:

        print()
        print("🔎 DEBUG: NVD Metrics Keys")
        print(
            list(
                metrics.keys()
            )
        )

    # ------------------------------------------------------
    # Prefer CVSS v3.1
    # ------------------------------------------------------

    if metrics.get(
        "cvssMetricV31"
    ):

        metric = metrics[
            "cvssMetricV31"
        ][0]

        cvss_data = metric.get(
            "cvssData",
            {}
        )

        cvss_score = cvss_data.get(
            "baseScore"
        )

        severity = (
            cvss_data.get(
                "baseSeverity"
            )
            or metric.get(
                "baseSeverity"
            )
        )

        cvss_version = (
            cvss_data.get(
                "version"
            )
            or "3.1"
        )

    # ------------------------------------------------------
    # Fall back to CVSS v3.0
    # ------------------------------------------------------

    elif metrics.get(
        "cvssMetricV30"
    ):

        metric = metrics[
            "cvssMetricV30"
        ][0]

        cvss_data = metric.get(
            "cvssData",
            {}
        )

        cvss_score = cvss_data.get(
            "baseScore"
        )

        severity = (
            cvss_data.get(
                "baseSeverity"
            )
            or metric.get(
                "baseSeverity"
            )
        )

        cvss_version = (
            cvss_data.get(
                "version"
            )
            or "3.0"
        )

    # ------------------------------------------------------
    # Fall back to CVSS v2
    # ------------------------------------------------------

    elif metrics.get(
        "cvssMetricV2"
    ):

        metric = metrics[
            "cvssMetricV2"
        ][0]

        cvss_data = metric.get(
            "cvssData",
            {}
        )

        cvss_score = cvss_data.get(
            "baseScore"
        )

        severity = (
            metric.get(
                "baseSeverity"
            )
            or cvss_data.get(
                "baseSeverity"
            )
        )

        cvss_version = (
            cvss_data.get(
                "version"
            )
            or "2.0"
        )

    # ======================================================
    # Affected Software
    # ======================================================

    affected = extract_affected_software(
        cve
    )

    if settings.LEARN_MODE:

        print()

        print(
            "🔎 DEBUG: NVD Configuration Count"
        )

        print(
            len(
                cve.get(
                    "configurations",
                    []
                )
            )
        )

        print()

        print(
            "🔎 Extracted Affected Software:"
        )

        print(
            affected[
                "affected_software"
            ]
        )

        print()

        print(
            "🔎 Extracted Affected Versions:"
        )

        print(
            affected[
                "affected_versions"
            ]
        )

        print()

        print(
            "🔎 Extracted Affected Products (structured):"
        )

        print(
            affected[
                "affected_products"
            ]
        )

    # ======================================================
    # Final Structured Result
    # ======================================================

    return {

        "cve_id": cve.get(
            "id",
            cve_id
        ),

        "description": description,

        "cvss_score": cvss_score,

        "cvss_version": cvss_version,

        "severity": severity,

        "published": cve.get(
            "published"
        ),

        "last_modified": cve.get(
            "lastModified"
        ),

        "affected_software": (
            affected[
                "affected_software"
            ]
        ),

        "affected_versions": (
            affected[
                "affected_versions"
            ]
        ),

        "affected_products": (
            affected[
                "affected_products"
            ]
        ),
    }


# ==========================================================
# Local Test
# ==========================================================

if __name__ == "__main__":

    result = get_vulnerability(
        "CVE-2024-3094"
    )

    print()
    print(
        "Vulnerability Result:"
    )
    print()

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )