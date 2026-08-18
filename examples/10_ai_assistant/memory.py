"""
memory.py

Persistent organization memory using SQLite.

This module provides:
1. Generic key-value memory
2. Organization-specific memory helpers
"""

from database import (
    save_memory,
    load_memory,
)


# ==========================================================
# Generic Memory
# ==========================================================

def remember(key: str, value: str):
    """
    Store a key-value pair in persistent memory.
    """

    save_memory(
        key,
        value,
    )


def recall(key: str):
    """
    Retrieve a value from persistent memory.

    Returns:
        Stored value if present, otherwise None.
    """

    return load_memory(key)


# ==========================================================
# Organization Memory
# ==========================================================

def remember_firewall(vendor: str):
    """
    Store the organization's firewall vendor.
    """

    remember(
        "firewall_vendor",
        vendor,
    )


def get_firewall():
    """
    Retrieve the organization's firewall vendor.
    """

    return recall(
        "firewall_vendor"
    )


def remember_siem(platform: str):
    """
    Store the organization's SIEM platform.
    """

    remember(
        "siem_platform",
        platform,
    )


def get_siem():
    """
    Retrieve the organization's SIEM platform.
    """

    return recall(
        "siem_platform"
    )


def remember_company(company: str):
    """
    Store the organization name.
    """

    remember(
        "organization",
        company,
    )


def get_company():
    """
    Retrieve the organization name.
    """

    return recall(
        "organization"
    )


def remember_policy(policy: str):
    """
    Store the organization's incident-response policy.
    """

    remember(
        "incident_policy",
        policy,
    )


def get_policy():
    """
    Retrieve the organization's incident-response policy.
    """

    return recall(
        "incident_policy"
    )


# ==========================================================
# Complete Organization Context
# ==========================================================

def get_organization_context():
    """
    Retrieve all known organization context.

    Missing values are returned as None rather than
    being invented.
    """

    return {
        "organization": get_company(),
        "firewall_vendor": get_firewall(),
        "siem_platform": get_siem(),
        "incident_policy": get_policy(),
    }