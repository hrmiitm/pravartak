"""
applicability.py

Evidence-based vulnerability applicability analysis.

This module determines whether a vulnerability applies to
organization assets by combining:

1. Vulnerability evidence
2. Software identity normalization
3. Installed software versions (exact matches and version ranges)
4. Organization asset inventory
"""

from inventory import Asset, get_demo_inventory, find_software


# ==========================================================
# Software Identity Normalization
# ==========================================================

SOFTWARE_ALIASES = {
    # (vendor, product) -> inventory software name
    #
    # Keying on the (vendor, product) pair, rather than product
    # alone, avoids a real ambiguity: two different vendors can
    # ship a product with the same name, and that name may not
    # mean the same inventory software for both. Requiring the
    # vendor to match makes an alias entry precise instead of a
    # coincidental string match.
    ("tukaani", "xz"): "xz-utils",
}


def normalize_software_identity(
    software_name: str,
    vendor: str = None,
) -> str:
    """
    Normalize a software/product name to the canonical
    inventory identity.

    Example:

        xz       -> xz-utils
        xz-utils -> xz-utils

    When a vendor is available, it is used to look up a
    precise (vendor, product) alias first. When no vendor is
    available, or no exact (vendor, product) entry exists, this
    falls back to matching on product name alone across all
    alias entries — preserving the original, vendor-agnostic
    behavior for callers that do not yet supply a vendor.

    The normalization layer is intentionally explicit and
    deterministic so that mappings can later be expanded
    using package metadata, CPE dictionaries, or a knowledge
    graph.
    """

    if not software_name:
        return ""

    product = (
        software_name
        .strip()
        .lower()
    )

    vendor_normalized = (
        vendor.strip().lower()
        if vendor
        else None
    )

    # ------------------------------------------------------
    # Precise (vendor, product) match
    # ------------------------------------------------------

    if vendor_normalized:

        exact_key = (
            vendor_normalized,
            product,
        )

        if exact_key in SOFTWARE_ALIASES:

            return SOFTWARE_ALIASES[
                exact_key
            ]

    # ------------------------------------------------------
    # Fallback: product-only match across all alias entries
    #
    # This fallback only applies when the vendor is genuinely
    # unknown (not supplied). If a vendor WAS supplied but did
    # not match any (vendor, product) entry, we deliberately do
    # not fall back to a product-only match here: doing so would
    # silently apply another vendor's alias to a same-named but
    # unrelated product, which is exactly the ambiguity that
    # keying on (vendor, product) is meant to avoid. In that
    # case normalization falls through to "no normalization
    # found" below, which is the conservative outcome.
    # ------------------------------------------------------

    if vendor_normalized is None:

        for (
            (alias_vendor, alias_product),
            inventory_name,
        ) in SOFTWARE_ALIASES.items():

            if alias_product == product:

                return inventory_name

    # ------------------------------------------------------
    # No normalization found
    # ------------------------------------------------------

    return product


# ==========================================================
# Version Parsing and Range Evaluation
# ==========================================================

def parse_version(version_str):
    """
    Parse a dotted-numeric version string into a tuple of
    integers.

    Example:

        "5.6.0" -> (5, 6, 0)

    Returns None if the string cannot be parsed as a simple
    dotted-numeric version (e.g. it contains letters, build
    metadata, or wildcards). This is intentionally strict:
    a version the parser cannot confidently interpret must
    never be silently treated as comparable.
    """

    if not version_str or version_str == "*":
        return None

    parts = version_str.strip().split(".")

    numeric_parts = []

    for part in parts:

        if not part.isdigit():
            return None

        numeric_parts.append(
            int(part)
        )

    if not numeric_parts:
        return None

    return tuple(numeric_parts)


def compare_versions(a: tuple, b: tuple) -> int:
    """
    Compare two version tuples of possibly different lengths.

    Returns:
        -1 if a < b
         0 if a == b
         1 if a > b
    """

    length = max(
        len(a),
        len(b),
    )

    a_padded = a + (0,) * (length - len(a))
    b_padded = b + (0,) * (length - len(b))

    if a_padded < b_padded:
        return -1

    if a_padded > b_padded:
        return 1

    return 0


def evaluate_version_range(
    installed_version: str,
    version_range: dict,
):
    """
    Determine whether an installed version falls within a
    single NVD version range.

    version_range may contain any of:
        start_including
        start_excluding
        end_including
        end_excluding

    Returns:

        True  - the installed version is confidently within
                the range
        False - the installed version is confidently outside
                the range (every boundary present was parsed
                successfully)
        None  - the range could not be reliably evaluated
                (the installed version, or a boundary that is
                present, could not be parsed as a simple
                dotted-numeric version)

    This function is deliberately conservative: it never
    returns False unless every boundary that is present could
    be parsed and compared. An unparseable boundary results in
    None, never a guess.
    """

    installed_parsed = parse_version(
        installed_version
    )

    if installed_parsed is None:
        return None

    start_including = version_range.get(
        "start_including"
    )
    start_excluding = version_range.get(
        "start_excluding"
    )
    end_including = version_range.get(
        "end_including"
    )
    end_excluding = version_range.get(
        "end_excluding"
    )

    boundaries = [
        start_including,
        start_excluding,
        end_including,
        end_excluding,
    ]

    # A range with no boundaries at all carries no information.
    if not any(boundaries):
        return None

    # Every boundary that is present must be parseable before
    # any conclusion can be drawn from this range.
    for boundary_value in boundaries:

        if boundary_value is not None:

            if parse_version(boundary_value) is None:
                return None

    if start_including is not None:

        boundary = parse_version(start_including)

        if compare_versions(
            installed_parsed,
            boundary,
        ) < 0:

            return False

    if start_excluding is not None:

        boundary = parse_version(start_excluding)

        if compare_versions(
            installed_parsed,
            boundary,
        ) <= 0:

            return False

    if end_including is not None:

        boundary = parse_version(end_including)

        if compare_versions(
            installed_parsed,
            boundary,
        ) > 0:

            return False

    if end_excluding is not None:

        boundary = parse_version(end_excluding)

        if compare_versions(
            installed_parsed,
            boundary,
        ) >= 0:

            return False

    return True


def evaluate_version_membership(
    installed_version: str,
    affected_versions: list,
    version_ranges: list,
):
    """
    Determine whether an installed version is affected, using
    both exact-match versions and version ranges.

    Returns a tuple:

        (status, detail)

    status is one of:

        "MATCH"   - the installed version is confidently affected
        "UNKNOWN" - at least one version range could not be
                    reliably evaluated, and no range or exact
                    match confidently applies
        "NO_MATCH" - every available exact version and range
                     was evaluated, and none apply

    detail is a short human-readable explanation suitable for
    use in evidence text.
    """

    # --------------------------------------------------
    # Exact version match (unchanged, existing behavior)
    # --------------------------------------------------

    if installed_version in affected_versions:

        return (
            "MATCH",
            "matches an affected version",
        )

    # --------------------------------------------------
    # Version range evaluation
    # --------------------------------------------------

    if version_ranges:

        range_results = [
            evaluate_version_range(
                installed_version,
                version_range,
            )
            for version_range in version_ranges
        ]

        if any(
            result is True
            for result in range_results
        ):

            return (
                "MATCH",
                "falls within a known affected version range",
            )

        if any(
            result is None
            for result in range_results
        ):

            return (
                "UNKNOWN",
                (
                    "the vulnerable version range could not be "
                    "reliably interpreted for this installed "
                    "version"
                ),
            )

        # All ranges were confidently evaluated and none matched.
        return (
            "NO_MATCH",
            "does not fall within any known affected version range",
        )

    # --------------------------------------------------
    # No ranges available, no exact match either
    # --------------------------------------------------

    return (
        "NO_MATCH",
        "does not match any known affected version",
    )


# ==========================================================
# Applicability Analysis
# ==========================================================

def analyze_applicability(
    cve_id: str,
    description: str,
    affected_software: str,
    affected_versions: list[str],
    inventory: list[Asset],
    organization_context: dict,
    version_ranges: list[dict] | None = None,
    vendor: str | None = None,
) -> dict:
    """
    Determine whether a vulnerability applies to organization assets.

    Applicability is based on:

    1. Affected software
    2. Software identity normalization (using vendor + product
       when a vendor is available, falling back to product alone)
    3. Installed software version (exact match or version range)
    4. Organization asset inventory

    version_ranges and vendor are both optional and additive.
    When omitted, this function behaves exactly as it did before
    they were added.

    The function is intentionally conservative.

    Possible results:

        RELEVANT
        NOT_RELEVANT
        UNKNOWN
    """

    if version_ranges is None:
        version_ranges = []

    evidence = []
    missing_evidence = []
    matched_assets = []
    unknown_assets = []

    # ------------------------------------------------------
    # Validate vulnerability information
    # ------------------------------------------------------

    if not affected_software:

        return {
            "cve_id": cve_id,
            "status": "UNKNOWN",
            "confidence": 0.20,
            "matched_assets": [],
            "evidence": [],
            "missing_evidence": [
                "Affected software could not be determined."
            ],
            "reason": (
                "The vulnerability evidence does not identify "
                "the affected software."
            ),
        }

    if not affected_versions and not version_ranges:

        return {
            "cve_id": cve_id,
            "status": "UNKNOWN",
            "confidence": 0.30,
            "matched_assets": [],
            "evidence": [],
            "missing_evidence": [
                "Affected software versions could not be determined."
            ],
            "reason": (
                "The affected software is known, but the vulnerable "
                "versions are not available."
            ),
        }

    # ------------------------------------------------------
    # Normalize software identity
    # ------------------------------------------------------

    original_software = affected_software

    canonical_software = normalize_software_identity(
        affected_software,
        vendor,
    )

    if not canonical_software:

        return {
            "cve_id": cve_id,
            "status": "UNKNOWN",
            "confidence": 0.20,
            "matched_assets": [],
            "evidence": [],
            "missing_evidence": [
                "Software identity could not be normalized."
            ],
            "reason": (
                "The affected software identifier could not "
                "be normalized to a usable inventory identity."
            ),
        }

    # ------------------------------------------------------
    # Record normalization evidence
    # ------------------------------------------------------

    if (
        original_software.strip().lower()
        != canonical_software
    ):

        evidence.append(
            f"NVD software identity '{original_software}' "
            f"was normalized to inventory identity "
            f"'{canonical_software}'."
        )

    # ------------------------------------------------------
    # Search organization inventory
    # ------------------------------------------------------

    software_matches = find_software(
        inventory,
        canonical_software,
    )

    # ------------------------------------------------------
    # No software found
    # ------------------------------------------------------

    if not software_matches:

        missing_evidence.append(
            f"Confirmation that {canonical_software} "
            "is deployed on organization assets."
        )

        return {
            "cve_id": cve_id,
            "status": "UNKNOWN",
            "confidence": 0.50,
            "matched_assets": [],
            "evidence": evidence,
            "missing_evidence": missing_evidence,
            "reason": (
                f"The affected software ({original_software}) "
                f"was normalized to ({canonical_software}), "
                "but it was not found in the available "
                "organization inventory. This does not prove "
                "that the organization is unaffected."
            ),
        }

    # ------------------------------------------------------
    # Compare installed versions (exact match and/or ranges)
    # ------------------------------------------------------

    for asset in software_matches:

        installed_version = asset["version"]

        status, detail = evaluate_version_membership(
            installed_version,
            affected_versions,
            version_ranges,
        )

        if status == "MATCH":

            matched_assets.append({
                "asset_id": asset["asset_id"],
                "software": asset["software"],
                "installed_version": installed_version,
                "affected_versions": affected_versions,
                "criticality": asset["criticality"],
                "exposure": asset["exposure"],
            })

            evidence.append(
                f"{asset['asset_id']} has "
                f"{asset['software']} {installed_version}, "
                f"which {detail}."
            )

        elif status == "UNKNOWN":

            unknown_assets.append({
                "asset_id": asset["asset_id"],
                "software": asset["software"],
                "installed_version": installed_version,
            })

            missing_evidence.append(
                f"Could not reliably determine whether "
                f"{asset['asset_id']}'s {asset['software']} "
                f"{installed_version} is affected: {detail}."
            )

        # status == "NO_MATCH" contributes to neither list and
        # is handled by the NOT_RELEVANT fallback below.

    # ------------------------------------------------------
    # Vulnerable asset found
    # ------------------------------------------------------

    if matched_assets:

        return {
            "cve_id": cve_id,
            "status": "RELEVANT",
            "confidence": 0.95,
            "matched_assets": matched_assets,
            "evidence": evidence,
            "missing_evidence": missing_evidence,
            "reason": (
                f"The NVD affected software ({original_software}) "
                f"was normalized to ({canonical_software}), "
                "which is present in the organization inventory "
                "at one or more versions confirmed to be affected "
                "(via exact match or version range)."
            ),
        }

    # ------------------------------------------------------
    # Software and version present, but version semantics
    # could not be reliably determined for at least one asset
    #
    # This mirrors the "UNKNOWN takes priority over
    # NOT_RELEVANT" principle used elsewhere in the pipeline:
    # an unparseable version range must not silently become
    # NOT_RELEVANT.
    # ------------------------------------------------------

    if unknown_assets:

        evidence.append(
            f"{canonical_software} is present in the organization "
            "inventory, but the vulnerable version range could not "
            "be reliably interpreted against one or more installed "
            "versions."
        )

        return {
            "cve_id": cve_id,
            "status": "UNKNOWN",
            "confidence": 0.40,
            "matched_assets": [],
            "evidence": evidence,
            "missing_evidence": missing_evidence,
            "reason": (
                f"The affected software ({original_software}) "
                f"was normalized to ({canonical_software}) and is "
                "present in the inventory, but the vulnerable "
                "version range semantics could not be reliably "
                "interpreted for the installed version(s). This "
                "does not prove the organization is unaffected."
            ),
        }

    # ------------------------------------------------------
    # Software exists but vulnerable version not found
    # ------------------------------------------------------

    evidence.append(
        f"{canonical_software} is present in the organization "
        "inventory, but no installed version matches the "
        "known affected versions or version ranges."
    )

    return {
        "cve_id": cve_id,
        "status": "NOT_RELEVANT",
        "confidence": 0.90,
        "matched_assets": [],
        "evidence": evidence,
        "missing_evidence": [],
        "reason": (
            f"The affected software ({original_software}) "
            f"was normalized to ({canonical_software}) and "
            "is present in the inventory, but the available "
            "installed versions do not match the known "
            "affected versions or version ranges."
        ),
    }


# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    inventory = get_demo_inventory()

    print("=" * 70)
    print("SOFTWARE NORMALIZATION TEST")
    print("=" * 70)

    print()
    print(
        "NVD identity : xz"
    )

    print(
        "Canonical (no vendor)    :",
        normalize_software_identity("xz")
    )

    print(
        "Canonical (vendor=tukaani):",
        normalize_software_identity("xz", "tukaani")
    )

    print(
        "Canonical (vendor=someothervendor):",
        normalize_software_identity("xz", "someothervendor")
    )

    print()
    print("=" * 70)
    print("APPLICABILITY TEST (exact match, unchanged)")
    print("=" * 70)

    result = analyze_applicability(
        cve_id="CVE-2024-3094",
        description=(
            "A vulnerability affecting xz-utils "
            "versions 5.6.0 and 5.6.1."
        ),
        affected_software="xz",
        affected_versions=[
            "5.6.0",
            "5.6.1",
        ],
        inventory=inventory,
        organization_context={},
    )

    print()
    print("Applicability Result:")
    print()

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )

    print()
    print("=" * 70)
    print("APPLICABILITY TEST (version range)")
    print("=" * 70)

    range_result = analyze_applicability(
        cve_id="CVE-TEST-RANGE",
        description="A vulnerability affecting xz-utils via a range.",
        affected_software="xz",
        affected_versions=[],
        version_ranges=[
            {
                "start_including": "5.0.0",
                "start_excluding": None,
                "end_including": None,
                "end_excluding": "5.6.2",
            }
        ],
        inventory=inventory,
        organization_context={},
    )

    print()
    print("Applicability Result:")
    print()

    for key, value in range_result.items():

        print(
            f"{key}: {value}"
        )

    print()
    print("=" * 70)
    print("APPLICABILITY TEST (unparseable range -> UNKNOWN)")
    print("=" * 70)

    unknown_result = analyze_applicability(
        cve_id="CVE-TEST-UNPARSEABLE",
        description="A vulnerability with an unparseable range boundary.",
        affected_software="xz",
        affected_versions=[],
        version_ranges=[
            {
                "start_including": "5.0.0-rc1",
                "start_excluding": None,
                "end_including": None,
                "end_excluding": "5.6.2",
            }
        ],
        inventory=inventory,
        organization_context={},
    )

    print()
    print("Applicability Result:")
    print()

    for key, value in unknown_result.items():

        print(
            f"{key}: {value}"
        )