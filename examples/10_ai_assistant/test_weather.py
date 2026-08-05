from pprint import pprint

from apis.weather import get_weather

pprint(
    get_weather("Chennai")
)