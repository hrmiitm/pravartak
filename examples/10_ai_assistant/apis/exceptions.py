class WeatherAPIError(Exception):
    """Base weather exception."""


class CityNotFoundError(WeatherAPIError):
    """City could not be found."""