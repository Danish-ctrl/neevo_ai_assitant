import requests
from config import WEATHER_API_KEY

def get_weather_data(city):
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    data = response.json()

    return {
        "city": data.get("name"),
        "temp": data.get("main", {}).get("temp"),
        "condition": data.get("weather", [{}])[0].get("description")
    }