"""
inventory.py

Organization asset inventory for vulnerability applicability analysis.
"""

from typing import TypedDict


class SoftwareInstallation(TypedDict):
    name: str
    version: str


class Asset(TypedDict):
    asset_id: str
    os: str
    software: list[SoftwareInstallation]
    criticality: str
    exposure: str


def get_demo_inventory() -> list[Asset]:
    """
    Return a small demo organization inventory.

    This is intentionally local and deterministic for development
    and evaluation. Later this can be replaced with a real CMDB,
    EDR, vulnerability scanner, or asset-management source.
    """

    return [
        {
            "asset_id": "web-server-01",
            "os": "Ubuntu 24.04",
            "software": [
                {
                    "name": "xz-utils",
                    "version": "5.6.0",
                },
                {
                    "name": "nginx",
                    "version": "1.24.0",
                },
            ],
            "criticality": "HIGH",
            "exposure": "INTERNET",
        },
        {
            "asset_id": "database-01",
            "os": "Ubuntu 22.04",
            "software": [
                {
                    "name": "xz-utils",
                    "version": "5.4.1",
                },
                {
                    "name": "postgresql",
                    "version": "14.11",
                },
            ],
            "criticality": "CRITICAL",
            "exposure": "INTERNAL",
        },
        {
            "asset_id": "firewall-01",
            "os": "PAN-OS",
            "software": [],
            "criticality": "CRITICAL",
            "exposure": "INTERNET",
        },
    ]


def find_software(
    inventory: list[Asset],
    software_name: str,
) -> list[dict]:
    """
    Find all assets containing a given software package.
    """

    matches = []

    target = software_name.lower()

    for asset in inventory:

        for software in asset["software"]:

            if software["name"].lower() == target:

                matches.append(
                    {
                        "asset_id": asset["asset_id"],
                        "software": software["name"],
                        "version": software["version"],
                        "criticality": asset["criticality"],
                        "exposure": asset["exposure"],
                    }
                )

    return matches