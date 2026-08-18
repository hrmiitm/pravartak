"""
exceptions.py

Exceptions raised by external API services.
"""


class APIError(Exception):
    """Base exception for external API failures."""


# ==========================================================
# Weather
# ==========================================================

class WeatherAPIError(APIError):
    """Base weather exception."""


class CityNotFoundError(WeatherAPIError):
    """City could not be found."""


# ==========================================================
# Vulnerability Intelligence
# ==========================================================

class VulnerabilityAPIError(APIError):
    """Base vulnerability API exception."""


class VulnerabilityNotFoundError(VulnerabilityAPIError):
    """Requested vulnerability could not be found."""


class InvalidCVEError(VulnerabilityAPIError):
    """CVE identifier has an invalid format."""