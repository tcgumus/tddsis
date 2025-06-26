import requests
from datetime import datetime, timedelta

def get_weather(city, day_offset=0):
    """Belirli bir sehir ve gun icin hava durumunu getirir."""
   
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=tr&format=json"
    geo_response = requests.get(geo_url).json()

    if "results" not in geo_response or len(geo_response["results"]) == 0:
        return f"{city} icin konum bulunamadi."

    lat = geo_response["results"][0]["latitude"]
    lon = geo_response["results"][0]["longitude"]

   
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,"
        f"temperature_2m_min,weathercode&timezone=auto"
    )
    weather_response = requests.get(weather_url).json()

    if "daily" not in weather_response:
        return f"{city} icin hava durumu verisi alinamadi."

 
    try:
        date = datetime.today().date() + timedelta(days=day_offset)
        date_str = date.isoformat()
        index = weather_response["daily"]["time"].index(date_str)

        max_temp = weather_response["daily"]["temperature_2m_max"][index]
        min_temp = weather_response["daily"]["temperature_2m_min"][index]

        return f"{city.title()} icin {date.strftime('%d %B %Y')} tarihinde hava: {min_temp} - {max_temp} °C"
    except (ValueError, IndexError):
        return f"{city} icin {day_offset} gun sonrasina ait hava durumu bulunamadi."

