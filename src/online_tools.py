"""Free online information - no API key needed.

- Weather:   Open-Meteo (https://open-meteo.com), free for personal use.
- Knowledge: Wikipedia (English and Kiswahili).

Only the Python standard library is used.
"""

import json
from urllib.error import URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

USER_AGENT = "HighguyAI/1.0 (personal desktop assistant)"
TIMEOUT = 10

# WMO weather codes used by Open-Meteo -> (English, Kiswahili)
WEATHER_CODES = {
    0: ("clear sky", "anga safi"),
    1: ("mainly clear", "anga safi kiasi"),
    2: ("partly cloudy", "mawingu kiasi"),
    3: ("overcast", "mawingu mengi"),
    45: ("fog", "ukungu"), 48: ("fog", "ukungu"),
    51: ("light drizzle", "manyunyu"), 53: ("drizzle", "manyunyu"), 55: ("heavy drizzle", "manyunyu mengi"),
    56: ("freezing drizzle", "manyunyu ya baridi"), 57: ("freezing drizzle", "manyunyu ya baridi"),
    61: ("light rain", "mvua kidogo"), 63: ("rain", "mvua"), 65: ("heavy rain", "mvua kubwa"),
    66: ("freezing rain", "mvua ya baridi"), 67: ("freezing rain", "mvua ya baridi"),
    71: ("light snow", "theluji kidogo"), 73: ("snow", "theluji"), 75: ("heavy snow", "theluji nyingi"),
    77: ("snow grains", "theluji"),
    80: ("rain showers", "manyunyu ya mvua"), 81: ("rain showers", "mvua za rasharasha"),
    82: ("violent rain showers", "mvua kubwa za ghafla"),
    85: ("snow showers", "theluji"), 86: ("snow showers", "theluji"),
    95: ("thunderstorm", "radi na mvua"), 96: ("thunderstorm with hail", "radi na mvua ya mawe"),
    99: ("thunderstorm with hail", "radi na mvua ya mawe"),
}


class OnlineError(Exception):
    """Could not get the information (no internet, not found...)."""


def fetch_json(url):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError) as error:
        raise OnlineError(f"No internet connection or the service is down ({error}).") from error
    except json.JSONDecodeError as error:
        raise OnlineError("The service sent an unreadable answer.") from error


def describe(code, language="english"):
    english, swahili = WEATHER_CODES.get(code, ("unknown", "haijulikani"))
    return swahili if language == "swahili" else english


def get_weather(city, days=1):
    """Current weather and a short forecast for a city, as plain text."""
    days = max(1, min(int(days), 7))
    geo = fetch_json("https://geocoding-api.open-meteo.com/v1/search?"
                     + urlencode({"name": city, "count": 1, "format": "json"}))
    places = geo.get("results") or []
    if not places:
        raise OnlineError(f"I couldn't find a place called '{city}'.")
    place = places[0]

    data = fetch_json("https://api.open-meteo.com/v1/forecast?" + urlencode({
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": days,
    }))

    name = ", ".join(part for part in (place.get("name"), place.get("country")) if part)
    now = data["current"]
    lines = [
        f"Weather in {name} right now: {describe(now['weather_code'])}, "
        f"{now['temperature_2m']:.0f}°C, humidity {now['relative_humidity_2m']}%, "
        f"wind {now['wind_speed_10m']:.0f} km/h."
    ]
    daily = data["daily"]
    for index, day in enumerate(daily["time"]):
        rain = daily["precipitation_probability_max"][index]
        lines.append(
            f"{day}: {describe(daily['weather_code'][index])}, "
            f"{daily['temperature_2m_min'][index]:.0f}-{daily['temperature_2m_max'][index]:.0f}°C"
            + (f", {rain}% chance of rain" if rain is not None else "")
        )
    return "\n".join(lines)


def wikipedia_summary(topic, language="en"):
    """Short Wikipedia summary of a topic ('en' or 'sw' Wikipedia)."""
    language = "sw" if language.lower().startswith("sw") else "en"
    base = f"https://{language}.wikipedia.org"
    search = fetch_json(f"{base}/w/api.php?" + urlencode({
        "action": "query", "list": "search", "srsearch": topic,
        "srlimit": 1, "format": "json",
    }))
    hits = search.get("query", {}).get("search", [])
    if not hits:
        raise OnlineError(f"Wikipedia has no article about '{topic}'.")
    title = hits[0]["title"]
    page = fetch_json(f"{base}/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}")
    extract = page.get("extract") or "No summary available."
    return f"{title} (Wikipedia, {language}): {extract}"
